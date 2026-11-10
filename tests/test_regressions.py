import asyncio
import json
import unittest
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.core.dependencies import get_current_user
from app.core.error_handlers import register_exception_handlers
from app.db.postgres import get_db
from app.domains.booking.exceptions import BookingConflict, BookingInvalid
from app.domains.booking.models import Booking
from app.domains.booking.schemas import BookingOfflineCreate, BookingOnlineCreate
from app.domains.booking.services import BookingService
from app.domains.departments.services import DepartmentService
from app.domains.departments.models import Department
from app.domains.event_format.services import EventFormatService
from app.domains.rooms.models import Room
from app.domains.rooms.repository import RoomRepository
from app.domains.rooms.schemas import RoomFilter
from app.domains.users.models import User
from app.domains.users.schemas import UserUpdate
from app.main import app


async def request(application, method, path, body=None):
    """ASGI-запрос без сервера, сети и дополнительных зависимостей."""
    sent = []
    received = False

    async def receive():
        nonlocal received
        if received:
            await asyncio.Future()
        received = True
        return {"type": "http.request", "body": json.dumps(body).encode() if body is not None else b""}

    async def send(message):
        sent.append(message)

    url = urlsplit(path)
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": method, "scheme": "http", "path": url.path, "raw_path": url.path.encode(),
        "root_path": "", "query_string": url.query.encode(), "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1234), "server": ("test", 80),
    }
    try:
        await asyncio.wait_for(application(scope, receive, send), timeout=5)
    except RuntimeError:
        # ServerErrorMiddleware повторно выбрасывает ошибку после отправки ответа 500.
        if not any(m.get("status") == 500 for m in sent):
            raise
    start = next(m for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return start["status"], json.loads(payload), dict(start["headers"])


class ApiRegressionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.overrides = dict(app.dependency_overrides)

        async def database():
            yield AsyncMock()

        app.dependency_overrides[get_db] = database

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.overrides)

    async def test_dictionary_writes_require_superuser(self):
        cases = [
            ("/api/buildings", {"number": "1", "address": "Адрес"}, "app.domains.rooms.services.BuildingService.create_building", {"id": 1, "number": "1", "name": None, "address": "Адрес"}),
            ("/api/departments", {"name": "Подразделение"}, "app.domains.departments.services.DepartmentService.create", {"id": 1, "name": "Подразделение"}),
            ("/api/event-formats", {"name": "Лекция"}, "app.domains.event_format.services.EventFormatService.create_event_format", {"id": 1, "name": "Лекция", "description": None}),
        ]
        for path, body, method, response in cases:
            with self.subTest(path=path), patch(method, new_callable=AsyncMock, return_value=response) as create:
                app.dependency_overrides.pop(get_current_user, None)
                status, error, _ = await request(app, "POST", path, body)
                self.assertEqual(status, 401)
                self.assertEqual(set(error), {"detail"})
                app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, is_superuser=False)
                status, _, _ = await request(app, "POST", path, body)
                self.assertEqual(status, 403)
                create.assert_not_awaited()
                app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, is_superuser=True)
                status, result, _ = await request(app, "POST", path, body)
                self.assertEqual(status, 201)
                self.assertEqual(result, response)
                create.assert_awaited_once()

    async def test_profile_with_and_without_department(self):
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
        for department in (None, Department(id=2, name="Кафедра")):
            user = User(
                id=1, email="review@example.com", phone_number="12345678", first_name="Имя",
                last_name="Фамилия", middle_name=None, department=department,
                is_active=True, is_superuser=False, is_verified=False,
                created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
            )
            with patch("app.domains.users.repository.UserRepository.get_with_department", new_callable=AsyncMock, return_value=user) as load:
                status, result, _ = await request(app, "GET", "/api/user/profile")
                self.assertEqual(status, 200)
                self.assertEqual(result["department"], None if department is None else {"id": 2, "name": "Кафедра"})
                self.assertIsNone(result["middle_name"])
                load.assert_awaited_once_with(1)

    async def test_error_contract(self):
        application = FastAPI()
        register_exception_handlers(application)

        @application.get("/conflict")
        async def conflict():
            raise BookingConflict()

        @application.get("/auth")
        async def auth():
            raise HTTPException(401, "Требуется вход", headers={"WWW-Authenticate": "Bearer"})

        @application.get("/broken")
        async def broken():
            raise RuntimeError("private database information")

        class Payload(BaseModel):
            count: int

        @application.post("/validate")
        async def validate(data: Payload):
            return data

        cases = [("GET", "/conflict", None, 409), ("GET", "/auth", None, 401),
                 ("GET", "/missing", None, 404), ("POST", "/conflict", None, 405),
                 ("POST", "/validate", {"count": "private-input"}, 422), ("GET", "/broken", None, 500)]
        for method, path, body, expected in cases:
            with self.subTest(path=path), self.assertLogs("app.core.error_handlers", level="ERROR") if expected == 500 else nullcontext():
                status, result, headers = await request(application, method, path, body)
                self.assertEqual(status, expected)
                self.assertEqual(set(result), {"detail"})
                self.assertIsInstance(result["detail"], str)
                self.assertNotIn("private", result["detail"])
                if expected == 401:
                    self.assertEqual(headers[b"www-authenticate"], b"Bearer")
                if expected == 409:
                    self.assertEqual(result["detail"], "Зал уже занят в это время")

    async def test_missing_dictionary_entries_are_404(self):
        for service, repository, method in [
            (DepartmentService, "dep_repo", "get_by_id"),
            (EventFormatService, "event_format_repository", "get_event_format_by_id"),
        ]:
            instance = service(AsyncMock())
            getattr(instance, repository).get_by_id = AsyncMock(return_value=None)
            with self.assertRaises(Exception) as caught:
                await getattr(instance, method)(999)
            self.assertEqual(caught.exception.status_code, 404)

    async def test_online_booking_rejects_incomplete_profile_before_writing(self):
        service = BookingService(AsyncMock())
        service.booking_repo.create = AsyncMock()
        data = BookingOnlineCreate(room_id=1, department_id=1, title="Лекция", event_format_id=1,
                                   attendees_count=1, start_at=datetime.now(UTC) + timedelta(days=1),
                                   end_at=datetime.now(UTC) + timedelta(days=1, hours=1))
        with self.assertRaises(BookingInvalid):
            await service.create_online(SimpleNamespace(first_name=None, last_name="Фамилия", phone_number="123456"), data)
        service.booking_repo.create.assert_not_awaited()

    async def test_online_and_offline_booking_without_middle_name(self):
        start = (datetime.now(UTC) + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
        from datetime import time
        room = SimpleNamespace(id=1, is_active=True, capacity=30, event_formats=[],
                               building=SimpleNamespace(timezone="Asia/Yekaterinburg"),
                               open_from=time(8), open_until=time(20))
        actor = SimpleNamespace(id=2, first_name="Имя", last_name="Фамилия",
                                middle_name=None, phone_number="12345678", department_id=1)
        common = dict(title="Лекция", event_format_id=1, department_id=1,
                      attendees_count=10, start_at=start, end_at=start + timedelta(hours=1))
        for online in (True, False):
            with self.subTest(online=online):
                service = BookingService(AsyncMock())
                service._get_room = AsyncMock(return_value=room)
                service.booking_repo.find_conflicts = AsyncMock(return_value=[])

                async def create(booking):
                    booking.id = 1
                    booking.created_at = datetime.now(UTC)
                    service.booking_repo.get_by_id = AsyncMock(return_value=booking)
                    return booking

                service.booking_repo.create = AsyncMock(side_effect=create)
                if online:
                    result = await service.create_online(actor, BookingOnlineCreate(room_id=1, **common))
                else:
                    data = BookingOfflineCreate(requester_first_name="Гость", requester_last_name="Посетитель",
                                                requester_phone="87654321", **common)
                    result = await service.create_offline(1, actor, data)
                    self.assertEqual((result.source, result.status), ("offline", "approved"))
                    self.assertEqual((result.created_by_id, result.decided_by_id), (actor.id, actor.id))
                    self.assertEqual((result.requester_first_name, result.requester_phone), ("Гость", "87654321"))
                self.assertIsNone(result.requester_middle_name)
                self.assertEqual(result.id, 1)
                service.db.commit.assert_awaited_once()


class SchemaRegressionTests(unittest.TestCase):
    def test_optional_middle_name(self):
        self.assertTrue(Booking.__table__.c.requester_middle_name.nullable)
        for value in (None, "", "   "):
            data = BookingOfflineCreate(title="Лекция", event_format_id=1, department_id=1,
                                        attendees_count=1, start_at=datetime.now(UTC) + timedelta(days=1),
                                        end_at=datetime.now(UTC) + timedelta(days=1, hours=1),
                                        requester_first_name="Имя", requester_last_name="Фамилия",
                                        requester_phone="123456", requester_middle_name=value)
            self.assertIsNone(data.requester_middle_name)
            self.assertIsNone(UserUpdate(middle_name=value).middle_name)
        self.assertEqual(UserUpdate(first_name="Имя").model_dump(exclude_unset=True), {"first_name": "Имя"})

    def test_capacity_filter_compiles(self):
        statement = RoomRepository._apply_filter(select(Room), RoomFilter(capacity_min=25))
        compiled = statement.compile(dialect=postgresql.dialect())
        self.assertIn("rooms.capacity >=", str(compiled))
        self.assertIn(25, compiled.params.values())

    def test_openapi_documents_error_contract(self):
        schema = app.openapi()
        error = schema["paths"]["/api/bookings"]["post"]["responses"]["422"]["content"]["application/json"]["schema"]
        self.assertEqual(error, {"$ref": "#/components/schemas/ErrorResponse"})


if __name__ == "__main__":
    unittest.main()
