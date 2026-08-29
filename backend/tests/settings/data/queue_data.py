"""Test data for the session queue and the reverse-proxy address chain."""


class FakeRedisData:
    """An in-memory stand-in for the redis commands the queue service uses."""

    def __init__(self):
        self.lists: dict[str, list[str]] = {}
        self.strings: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def eval(self, script: str, numkeys: int, *args):
        """Dispatches on the script's shape, which is what the queue relies on."""
        keys = list(args[:numkeys])
        argv = list(args[numkeys:])
        if "RPUSH" in script:
            return self._enqueue(keys[0], str(argv[0]), int(argv[1]))
        if "INCR" in script:
            return self._try_acquire(keys[0], keys[1], int(argv[0]), int(argv[1]), int(argv[2]))
        if "DECR" in script:
            return self._release(keys[0], keys[1])
        raise AssertionError("unknown script")

    def _enqueue(self, key: str, user: str, ttl: int) -> int:
        """Appends the user only when absent, mirroring LUA_ENQUEUE."""
        items = self.lists.setdefault(key, [])
        self.ttls[key] = ttl
        if user in items:
            return items.index(user) + 1
        items.append(user)
        return len(items)

    def _try_acquire(self, lab_key: str, total_key: str, lab_cap, global_cap, ttl) -> int:
        """Increments both counters when neither cap is reached."""
        lab = int(self.strings.get(lab_key, "0"))
        total = int(self.strings.get(total_key, "0"))
        if lab >= lab_cap or total >= global_cap:
            return 0
        self.strings[lab_key] = str(lab + 1)
        self.strings[total_key] = str(total + 1)
        self.ttls[lab_key] = ttl
        self.ttls[total_key] = ttl
        return 1

    def _release(self, lab_key: str, total_key: str) -> int:
        """Decrements both counters, never below zero."""
        for key in (lab_key, total_key):
            current = int(self.strings.get(key, "0"))
            if current > 0:
                self.strings[key] = str(current - 1)
        return 1

    async def lrem(self, key: str, count: int, value: str) -> int:
        """Removes every matching entry."""
        items = self.lists.get(key, [])
        removed = items.count(value)
        self.lists[key] = [entry for entry in items if entry != value]
        return removed

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        """Returns the slice redis would."""
        items = self.lists.get(key, [])
        return items[start:] if stop == -1 else items[start : stop + 1]

    async def llen(self, key: str) -> int:
        """Length of the list."""
        return len(self.lists.get(key, []))

    def pipeline(self) -> "FakeRedisPipelineData":
        """A pipeline that applies its queued commands on execute."""
        return FakeRedisPipelineData(self)


class FakeRedisPipelineData:
    """Collects commands and applies them together, like a redis pipeline."""

    def __init__(self, redis: FakeRedisData):
        self.redis = redis
        self.calls: list[tuple] = []

    def lpush(self, key: str, value) -> "FakeRedisPipelineData":
        """Queues a left push."""
        self.calls.append(("lpush", key, value))
        return self

    def ltrim(self, key: str, start: int, stop: int) -> "FakeRedisPipelineData":
        """Queues a trim."""
        self.calls.append(("ltrim", key, start, stop))
        return self

    def expire(self, key: str, ttl: int) -> "FakeRedisPipelineData":
        """Queues an expiry."""
        self.calls.append(("expire", key, ttl))
        return self

    async def execute(self) -> list:
        """Applies every queued command in order."""
        for call in self.calls:
            if call[0] == "lpush":
                self.redis.lists.setdefault(call[1], []).insert(0, str(call[2]))
            elif call[0] == "ltrim":
                items = self.redis.lists.get(call[1], [])
                self.redis.lists[call[1]] = items[call[2] : call[3] + 1]
            elif call[0] == "expire":
                self.redis.ttls[call[1]] = call[2]
        self.calls = []
        return []


class ForwardedHeaderData:
    """Generates X-Forwarded-For chains as a single trusted proxy would leave them."""

    def __init__(self, header: str, expected: str):
        self.header = header
        self.expected = expected

    @classmethod
    def spoofed(cls) -> "ForwardedHeaderData":
        """A client that supplied its own value before the proxy appended the real one."""
        return cls("203.0.113.9, 198.51.100.4", "198.51.100.4")

    @classmethod
    def two_callers(cls) -> tuple["ForwardedHeaderData", "ForwardedHeaderData"]:
        """Two different callers arriving through the same proxy."""
        return cls("198.51.100.4", "198.51.100.4"), cls("198.51.100.5", "198.51.100.5")


class FixedPositionQueueData:
    """A queue service that always reports the same place in line."""

    def __init__(self, position: int | None, depth: int = 4, provision_seconds: float = 30.0):
        self.expected_position = position
        self.expected_depth = depth
        self.provision_seconds = provision_seconds

    async def position(self, user_id: str, lab_slug: str) -> int | None:
        """The caller's place in line, or None when not queued."""
        return self.expected_position

    async def queue_depth(self, lab_slug: str) -> int:
        """How many learners are waiting for the lab."""
        return self.expected_depth

    async def avg_provision_seconds(self) -> float:
        """How long one provisioning run takes on average."""
        return self.provision_seconds


class TicketRedisData:
    """The two redis commands the ticket store uses."""

    def __init__(self):
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """Stores a value with its expiry."""
        self.values[key] = value
        if ex is not None:
            self.ttls[key] = ex

    async def getdel(self, key: str) -> str | None:
        """Reads and removes in one step, which is what makes a ticket single-use."""
        return self.values.pop(key, None)
