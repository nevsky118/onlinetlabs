import httpx
import pytest
import respx
from httpx import Response
from tests.report import autotests

pytestmark = [pytest.mark.unit]

class TestGNS3AdminClient:
    @pytest.fixture
    def base_url(self):
        return "http://gns3-test:3080"

    @autotests.num("430")
    @autotests.external_id("e1f2a3b4-0001-4eee-ffff-430000000001")
    @autotests.name("GNS3 Admin Client: authenticate возвращает token")
    @respx.mock
    async def test_authenticate(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt-123"})
        )
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        assert client.token == "jwt-123"
        await client.close()

    @autotests.num("431")
    @autotests.external_id("e1f2a3b4-0002-4eee-ffff-431000000001")
    @autotests.name("GNS3 Admin Client: create_user создаёт пользователя")
    @respx.mock
    async def test_create_user(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.post(f"{base_url}/v3/access/users").mock(
            return_value=Response(201, json={"user_id": "u1", "username": "student-abc"})
        )
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        result = await client.create_user("student-abc", "pass123")
        assert result["user_id"] == "u1"
        await client.close()

    @autotests.num("432")
    @autotests.external_id("e1f2a3b4-0003-4eee-ffff-432000000001")
    @autotests.name("GNS3 Admin Client: delete_user удаляет пользователя")
    @respx.mock
    async def test_delete_user(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.delete(f"{base_url}/v3/access/users/u1").mock(return_value=Response(204))
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        await client.delete_user("u1")
        await client.close()

    @autotests.num("433")
    @autotests.external_id("e1f2a3b4-0004-4eee-ffff-433000000001")
    @autotests.name("GNS3 Admin Client: duplicate_project дублирует проект")
    @respx.mock
    async def test_duplicate_project(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.post(f"{base_url}/v3/projects/p1/duplicate").mock(
            return_value=Response(201, json={"project_id": "p2", "name": "Copy"})
        )
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        result = await client.duplicate_project("p1")
        assert result["project_id"] == "p2"
        await client.close()

    @autotests.num("434")
    @autotests.external_id("e1f2a3b4-0005-4eee-ffff-434000000001")
    @autotests.name("GNS3 Admin Client: get_user_token получает JWT для студента")
    @respx.mock
    async def test_get_user_token(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            side_effect=[
                Response(200, json={"access_token": "admin-jwt"}),
                Response(200, json={"access_token": "student-jwt"}),
            ]
        )
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        token = await client.get_user_token("student-abc", "pass123")
        assert token == "student-jwt"
        await client.close()

    @autotests.num("435")
    @autotests.external_id("e1f2a3b4-0006-4eee-ffff-435000000001")
    @autotests.name("GNS3 Admin Client: duplicate_project передаёт name в теле запроса")
    @respx.mock
    async def test_duplicate_project_sends_name(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        route = respx.post(f"{base_url}/v3/projects/p1/duplicate").mock(
            return_value=Response(201, json={"project_id": "p2", "name": "my-copy"})
        )
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        result = await client.duplicate_project("p1", name="my-copy")
        assert result["name"] == "my-copy"
        import json
        assert json.loads(route.calls.last.request.content) == {"name": "my-copy"}
        await client.close()

    @autotests.num("436")
    @autotests.external_id("e1f2a3b4-0007-4eee-ffff-436000000001")
    @autotests.name("GNS3 Admin Client: create_role создаёт роль")
    @respx.mock
    async def test_create_role(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.post(f"{base_url}/v3/access/roles").mock(
            return_value=Response(201, json={"role_id": "r1", "name": "student-role"})
        )
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        result = await client.create_role("student-role")
        assert result["role_id"] == "r1"
        assert result["name"] == "student-role"
        await client.close()

    @autotests.num("437")
    @autotests.external_id("e1f2a3b4-0008-4eee-ffff-437000000001")
    @autotests.name("GNS3 Admin Client: create_acl отправляет ace_type, user_id, role_id")
    @respx.mock
    async def test_create_acl(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        route = respx.post(f"{base_url}/v3/access/acl").mock(
            return_value=Response(201, json={"acl_id": "a1"})
        )
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        result = await client.create_acl("/projects/p1", role_id="r1", user_id="u1")
        assert result["acl_id"] == "a1"
        import json
        sent = json.loads(route.calls.last.request.content)
        assert sent["ace_type"] == "user"
        assert sent["user_id"] == "u1"
        assert sent["role_id"] == "r1"
        assert sent["allowed"] is True
        await client.close()

    @autotests.num("438")
    @autotests.external_id("e1f2a3b4-0009-4eee-ffff-438000000001")
    @autotests.name("GNS3 Admin Client: assign_role_to_user отправляет PUT с role_id")
    @respx.mock
    async def test_assign_role_to_user(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        route = respx.put(f"{base_url}/v3/access/users/u1").mock(
            return_value=Response(200, json={})
        )
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        await client.assign_role_to_user("u1", "r1")
        import json
        sent = json.loads(route.calls.last.request.content)
        assert sent["role_id"] == "r1"
        await client.close()

    @autotests.num("439")
    @autotests.external_id("e1f2a3b4-0010-4eee-ffff-439000000001")
    @autotests.name("GNS3 Admin Client: delete_project отправляет DELETE")
    @respx.mock
    async def test_delete_project(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.delete(f"{base_url}/v3/projects/p1").mock(return_value=Response(204))
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        await client.delete_project("p1")
        await client.close()

    @autotests.num("440")
    @autotests.external_id("e1f2a3b4-0011-4eee-ffff-440000000001")
    @autotests.name("GNS3 Admin Client: delete_role отправляет DELETE")
    @respx.mock
    async def test_delete_role(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.delete(f"{base_url}/v3/access/roles/r1").mock(return_value=Response(204))
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        await client.delete_role("r1")
        await client.close()

    @autotests.num("4401")
    @autotests.external_id("e1f2a3b4-0015-4eee-ffff-440100000001")
    @autotests.name("GNS3 Admin Client: update_user_password отправляет PUT с новым паролем")
    @respx.mock
    async def test_update_user_password(self, base_url):
        import json

        from src.gns3_admin_client import GNS3AdminClient

        with autotests.step("Подготовка — mock GNS3 API"):
            respx.post(f"{base_url}/v3/access/users/authenticate").mock(
                return_value=Response(200, json={"access_token": "jwt"})
            )
            route = respx.put(f"{base_url}/v3/access/users/u1").mock(
                return_value=Response(200, json={})
            )

        with autotests.step("Вызываем update_user_password"):
            client = GNS3AdminClient(base_url, "admin", "admin")
            await client.authenticate()
            await client.update_user_password("u1", "new-secret")

        with autotests.step("Проверяем тело запроса"):
            sent = json.loads(route.calls.last.request.content)
            assert sent["password"] == "new-secret"

        await client.close()

    @autotests.num("441")
    @autotests.external_id("e1f2a3b4-0012-4eee-ffff-441000000001")
    @autotests.name("GNS3 Admin Client: create_user 409 вызывает HTTPStatusError")
    @respx.mock
    async def test_create_user_conflict_409(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.post(f"{base_url}/v3/access/users").mock(return_value=Response(409))
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        with pytest.raises(httpx.HTTPStatusError):
            await client.create_user("dup-user", "pass")
        await client.close()

    @autotests.num("442")
    @autotests.external_id("e1f2a3b4-0013-4eee-ffff-442000000001")
    @autotests.name("GNS3 Admin Client: create_role 400 вызывает HTTPStatusError")
    @respx.mock
    async def test_create_role_conflict_400(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.post(f"{base_url}/v3/access/roles").mock(return_value=Response(400))
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        with pytest.raises(httpx.HTTPStatusError):
            await client.create_role("bad-role")
        await client.close()

    @autotests.num("443")
    @autotests.external_id("e1f2a3b4-0014-4eee-ffff-443000000001")
    @autotests.name("GNS3 Admin Client: duplicate_project 422 вызывает HTTPStatusError")
    @respx.mock
    async def test_duplicate_project_422(self, base_url):
        from src.gns3_admin_client import GNS3AdminClient
        respx.post(f"{base_url}/v3/access/users/authenticate").mock(
            return_value=Response(200, json={"access_token": "jwt"})
        )
        respx.post(f"{base_url}/v3/projects/p1/duplicate").mock(return_value=Response(422))
        client = GNS3AdminClient(base_url, "admin", "admin")
        await client.authenticate()
        with pytest.raises(httpx.HTTPStatusError):
            await client.duplicate_project("p1")
        await client.close()
