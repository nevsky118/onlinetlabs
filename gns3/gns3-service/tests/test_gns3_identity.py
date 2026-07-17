"""Unit-тесты gns3_username_for: имя GNS3-пользователя не должно коллидировать.

Регрессия: имя строилось как `student-{user_id[:8]}`. Два студента с общим
8-символьным префиксом id получали ОДНО имя, и orphan-cleanup при провижне второго
удалял GNS3-пользователя первого посреди его сессии → ACL падал с
`FOREIGN KEY constraint failed`, сессия — с 500. Студенты рушили лабы друг другу.
"""

from src.gns3_identity import gns3_username_for


class TestGns3UsernameFor:
    def test_distinct_users_with_shared_prefix_get_distinct_names(self):
        """Общий 8-символьный префикс id больше не даёт одинаковых имён."""
        a = gns3_username_for("sim-12000-1")
        b = gns3_username_for("sim-12000-2")
        c = gns3_username_for("sim-12000-49")

        assert a != b != c
        assert len({a, b, c}) == 3, "имена должны различаться при общем префиксе"

    def test_is_deterministic(self):
        """Тот же студент → то же имя (иначе уборка его залётных аккаунтов сломается)."""
        assert gns3_username_for("user-abc") == gns3_username_for("user-abc")

    def test_name_is_prefixed_and_bounded(self):
        """Имя опознаваемо и не длиннее лимитов GNS3."""
        name = gns3_username_for("0d1903e5-d38a-41ff-bcfb-03554cddba20")

        assert name.startswith("student-")
        assert len(name) == len("student-") + 16
        assert name[len("student-"):].isalnum()

    def test_uuid_users_do_not_collide(self):
        """Массовая проверка: 500 разных id → 500 разных имён."""
        names = {gns3_username_for(f"student-{i}-0d1903e5") for i in range(500)}

        assert len(names) == 500
