"""Locust scenarios — Plan E Phase 1 backend load characterization.

Single seeded test user (verify-live@test.com) is used by all simulated VUs
since per-user rate limit (3/min) and per-user cap (2 concurrent) will gate
true 50-concurrent behavior. This file exercises:
- /auth/exchange (30/min limit)
- /users/me/sessions launch (3/min, 2/user cap)
- /users/me/sessions/{id}/state polling
- /users/me/sessions/{id}/end

Run:
  locust -f locust/locustfile.py --headless -u 50 -r 5 --run-time 5m \
    --csv /tmp/locust-phase1 --host http://localhost:8000
"""

import os
import random
import time

from locust import HttpUser, between, task

# Select scenario via env var so a single locustfile drives both phases without
# spawning the off-phase user (locust --tags filters tasks, not classes, so the
# off-phase user still runs on_start and hits /auth/exchange).
SCENARIO = os.environ.get("LOCUST_SCENARIO", "baseline")

USER_EMAIL = "verify-live@test.com"
USER_ID = "38118539-5584-4a60-845d-7468199db31d"


class PlatformUser(HttpUser):
    abstract = SCENARIO != "baseline"
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self) -> None:
        r = self.client.post(
            "/auth/exchange",
            json={"email": USER_EMAIL, "user_id": USER_ID},
            name="/auth/exchange",
        )
        self.token = None
        if r.status_code == 200:
            self.token = r.json()["access_token"]
        self.session_id: str | None = None

    def _h(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    @task(3)
    def launch_lab(self) -> None:
        if not self.token:
            return
        with self.client.post(
            "/users/me/sessions",
            json={"lab_slug": "ospf-vlan-lab"},
            headers=self._h(),
            name="POST /users/me/sessions",
            catch_response=True,
        ) as r:
            # 201 = new active. 200 = existing active. 429 = rate-limited. 400 = cap.
            if r.status_code in (200, 201):
                try:
                    self.session_id = r.json().get("session_id")
                except Exception:
                    pass
                r.success()
            elif r.status_code in (400, 429):
                r.success()  # expected throttling
            else:
                r.failure(f"unexpected {r.status_code}: {r.text[:120]}")

    @task(10)
    def poll_state(self) -> None:
        if not self.token or not self.session_id:
            return
        self.client.get(
            f"/users/me/sessions/{self.session_id}/state",
            headers=self._h(),
            name="GET /users/me/sessions/{id}/state",
        )

    @task(1)
    def end_session(self) -> None:
        if not self.token or not self.session_id:
            return
        self.client.post(
            f"/users/me/sessions/{self.session_id}/end",
            headers=self._h(),
            name="POST /users/me/sessions/{id}/end",
        )
        self.session_id = None


class BurstUser(HttpUser):
    """Phase 2 — aggressive launch attempts to exercise queueing.

    Biases lab choice toward FRR (cap 50) over dynamips (cap 15) to maximize
    queue depth without instant 400/cap rejections. Target this class only:
      LOCUST_SCENARIO=burst locust ... -u 70 -r 10 -t 15m
    """

    abstract = SCENARIO != "burst"
    wait_time = between(0.1, 0.5)
    host = "http://localhost:8000"

    def on_start(self) -> None:
        r = self.client.post(
            "/auth/exchange",
            json={"email": USER_EMAIL, "user_id": USER_ID},
            name="/auth/exchange (burst)",
        )
        self.token = r.json()["access_token"] if r.status_code == 200 else None
        self.queued_lab: str | None = None

    def _h(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    @task(5)
    def burst_launch(self) -> None:
        if not self.token:
            return
        lab = random.choices(
            ["ospf-vlan-lab-frr", "ospf-vlan-lab"],
            weights=[3, 1],
        )[0]
        with self.client.post(
            "/users/me/sessions",
            json={"lab_slug": lab},
            headers=self._h(),
            name="POST /sessions (burst)",
            catch_response=True,
        ) as r:
            if r.status_code in (200, 201):
                r.success()
            elif r.status_code == 202:
                try:
                    self.queued_lab = r.json().get("lab_slug") or lab
                except Exception:
                    self.queued_lab = lab
                r.success()
            elif r.status_code in (400, 429):
                r.success()  # throttled / capped — expected under burst
            else:
                r.failure(f"unexpected {r.status_code}: {r.text[:120]}")

    @task(2)
    def poll_queue_status(self) -> None:
        if not self.token or not self.queued_lab:
            return
        self.client.get(
            f"/users/me/sessions/queue-status?lab_slug={self.queued_lab}",
            headers=self._h(),
            name="GET /sessions/queue-status (burst)",
        )
