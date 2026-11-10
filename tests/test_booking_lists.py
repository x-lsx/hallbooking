import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from sqlalchemy.dialects import postgresql

from app.core.dependencies import get_current_user
from app.db.postgres import get_db
from app.domains.booking.models import Booking, BookingStatus
from app.domains.booking.repository import BookingRepository
from app.domains.booking.schemas import BookingListFilter
from app.domains.booking.services import BookingService
from app.domains.moderators.repository import RoomModeratorRepository
from app.domains.rooms.repository import RoomRepository
from app.domains.rooms.schemas import RoomFilter
from app.main import app
from test_regressions import request


def booking(status=BookingStatus.PENDING):
    now = datetime.now(UTC)
    return Booking(
        id=8, title="Встреча", requester_first_name="Имя", requester_last_name="Фамилия",
        requester_middle_name=None, requester_phone="12345678", created_by_id=17,
        room_id=3, event_id=1, department_id=1, decided_by_id=None, source="online",
        status=status, attendees_count=10, is_public=False, start_at=now,
        end_at=now + timedelta(hours=1), reject_reason=None, created_at=now,
    )


class ListApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.saved = dict(app.dependency_overrides)
        self.actor = SimpleNamespace(id=17, is_superuser=False)
        app.dependency_overrides[get_current_user] = lambda: self.actor

        async def database():
            yield AsyncMock()

        app.dependency_overrides[get_db] = database

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.saved)

    async def test_my_route_uses_actor_and_paginates_all_statuses(self):
        with patch.object(BookingRepository, "list_by_user", new_callable=AsyncMock,
                          return_value=([booking(BookingStatus.CANCELLED)], 21)) as load:
            status, body, _ = await request(app, "GET", "/api/bookings/my?page=2&size=10&statuses=canselled")
        self.assertEqual(status, 200)
        self.assertEqual((body["total"], body["page"], body["pages"]), (21, 2, 3))
        self.assertEqual(body["items"][0]["status"], "canselled")
        self.assertEqual(load.await_args.args[0], 17)
        self.assertEqual(load.await_args.args[1].statuses, [BookingStatus.CANCELLED])

    async def test_my_does_not_accept_other_user_id(self):
        status, _, _ = await request(app, "GET", "/api/bookings/my?user_id=99")
        self.assertEqual(status, 422)

    async def test_offline_creation_uses_room_permission_and_guest_data(self):
        start = datetime.now(UTC) + timedelta(days=1)
        payload = dict(title="Личное обращение", event_format_id=1, department_id=2,
                       attendees_count=5, start_at=start.isoformat(),
                       end_at=(start + timedelta(hours=1)).isoformat(),
                       requester_first_name="Гость", requester_last_name="Посетитель",
                       requester_phone="+79990000001")
        result = booking(BookingStatus.APPROVED)
        result.source = "offline"
        result.decided_by_id = 17
        result.requester_first_name = "Гость"
        for allowed in (False, True):
            with self.subTest(allowed=allowed), patch.object(RoomModeratorRepository, "has_active_assignment", new_callable=AsyncMock, return_value=allowed), patch.object(BookingService, "create_offline", new_callable=AsyncMock, return_value=result) as create:
                status, body, _ = await request(app, "POST", "/api/rooms/3/bookings", payload)
                if not allowed:
                    self.assertEqual(status, 403)
                    create.assert_not_awaited()
                else:
                    self.assertEqual(status, 200)
                    self.assertEqual((body["source"], body["status"]), ("offline", "approved"))
                    room_id, actor, data = create.await_args.args
                    self.assertEqual((room_id, actor.id), (3, 17))
                    self.assertEqual(data.requester_first_name, "Гость")
                    self.assertIsNone(data.requester_middle_name)

    async def test_lists_require_authentication(self):
        app.dependency_overrides.pop(get_current_user)
        for path in ("/api/bookings/my", "/api/rooms/my", "/api/rooms/3/booking-requests"):
            with self.subTest(path=path):
                status, _, _ = await request(app, "GET", path)
                self.assertEqual(status, 401)

    async def test_room_requests_check_permission_before_reading_private_data(self):
        with patch.object(RoomModeratorRepository, "has_active_assignment", new_callable=AsyncMock, return_value=False), patch.object(BookingRepository, "list_requests_for_room", new_callable=AsyncMock) as load:
            status, _, _ = await request(app, "GET", "/api/rooms/3/booking-requests")
        self.assertEqual(status, 403)
        load.assert_not_awaited()

    async def test_room_moderator_can_read_archive(self):
        with patch.object(RoomModeratorRepository, "has_active_assignment", new_callable=AsyncMock, return_value=True), patch.object(RoomRepository, "get_by_id", new_callable=AsyncMock, return_value=SimpleNamespace(id=3)), patch.object(BookingRepository, "list_requests_for_room", new_callable=AsyncMock, return_value=([booking(BookingStatus.REJECTED)], 1)) as load:
            status, body, _ = await request(app, "GET", "/api/rooms/3/booking-requests?statuses=rejected&statuses=canselled")
        self.assertEqual(status, 200)
        self.assertEqual(body["items"][0]["status"], "rejected")
        self.assertEqual(load.await_args.args[0], 3)
        self.assertEqual(load.await_args.args[1].statuses, [BookingStatus.REJECTED, BookingStatus.CANCELLED])

    async def test_superuser_can_read_room_requests_without_assignment(self):
        self.actor.is_superuser = True
        with patch.object(RoomModeratorRepository, "has_active_assignment", new_callable=AsyncMock) as check, patch.object(RoomRepository, "get_by_id", new_callable=AsyncMock, return_value=SimpleNamespace(id=3)), patch.object(BookingRepository, "list_requests_for_room", new_callable=AsyncMock, return_value=([], 0)):
            status, body, _ = await request(app, "GET", "/api/rooms/3/booking-requests")
        self.assertEqual(status, 200)
        self.assertEqual(body["items"], [])
        check.assert_not_awaited()

    async def test_my_rooms_with_no_assignments_remain_empty(self):
        with patch.object(RoomModeratorRepository, "get_by_user", new_callable=AsyncMock, return_value=[]) as assignments, patch.object(RoomRepository, "list", new_callable=AsyncMock, return_value=([], 0)) as load:
            status, body, _ = await request(app, "GET", "/api/rooms/my")
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 0)
        self.assertEqual(load.await_args.kwargs["room_ids"], [])
        assignments.assert_awaited_once_with(17)

    async def test_my_rooms_only_passes_assigned_ids(self):
        with patch.object(RoomModeratorRepository, "get_by_user", new_callable=AsyncMock, return_value=[SimpleNamespace(room_id=3)]), patch.object(RoomRepository, "list", new_callable=AsyncMock, return_value=([], 0)) as load:
            status, _, _ = await request(app, "GET", "/api/rooms/my?page=2&size=5")
        self.assertEqual(status, 200)
        self.assertEqual(load.await_args.kwargs["room_ids"], [3])
        self.assertEqual(load.await_args.args[0].page, 2)

    async def test_superuser_my_rooms_does_not_require_assignment(self):
        self.actor.is_superuser = True
        with patch.object(RoomModeratorRepository, "get_by_user", new_callable=AsyncMock) as assignments, patch.object(RoomRepository, "list", new_callable=AsyncMock, return_value=([], 0)) as load:
            status, _, _ = await request(app, "GET", "/api/rooms/my")
        self.assertEqual(status, 200)
        self.assertIsNone(load.await_args.kwargs["room_ids"])
        assignments.assert_not_awaited()

    async def test_invalid_filters_return_422(self):
        for query in ("size=101", "page=0", "statuses=unknown", "room_id=-1",
                      "start_at=2030-01-02T00:00:00Z&end_at=2030-01-01T00:00:00Z",
                      "start_at=2030-01-01T00:00:00"):
            with self.subTest(query=query):
                status, _, _ = await request(app, "GET", f"/api/bookings/my?{query}")
                self.assertEqual(status, 422)

    async def test_calendar_still_omits_archive_and_masks_private_title(self):
        with patch.object(RoomModeratorRepository, "has_active_assignment", new_callable=AsyncMock, return_value=False), patch.object(RoomRepository, "get_by_id", new_callable=AsyncMock, return_value=SimpleNamespace(id=3)), patch.object(BookingRepository, "list_for_room", new_callable=AsyncMock, return_value=[booking(BookingStatus.APPROVED)]) as load:
            status, body, _ = await request(app, "GET", "/api/rooms/3/bookings?start_at=2030-01-01T00:00:00Z&end_at=2030-01-02T00:00:00Z")
        self.assertEqual(status, 200)
        self.assertEqual(body[0]["title"], "Занято")
        self.assertEqual(load.await_args.args[2], [BookingStatus.APPROVED])


class RepositoryListTests(unittest.IsolatedAsyncioTestCase):
    async def test_personal_count_and_items_share_scope_filters_and_boundaries(self):
        db = AsyncMock()
        db.scalar.return_value = 22
        db.scalars.return_value = Mock(all=Mock(return_value=[]))
        filters = BookingListFilter(statuses=[BookingStatus.REJECTED], room_id=3,
                                    start_at=datetime(2030, 1, 1, tzinfo=UTC),
                                    end_at=datetime(2030, 2, 1, tzinfo=UTC), page=3, size=2)
        _, total = await BookingRepository(db).list_by_user(17, filters)
        count = db.scalar.await_args.args[0]
        items = db.scalars.await_args.args[0]
        self.assertEqual(str(count.whereclause), str(items.whereclause))
        sql = str(items.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        for fragment in ("bookings.created_by_id = 17", "bookings.room_id = 3", "bookings.status IN ('rejected')", "bookings.end_at >", "bookings.start_at <", "bookings.created_at DESC, bookings.id DESC", "LIMIT 2 OFFSET 4"):
            self.assertIn(fragment, sql)
        self.assertEqual(total, 22)

    async def test_room_requests_cannot_escape_room_scope(self):
        db = AsyncMock()
        db.scalar.return_value = 0
        db.scalars.return_value = Mock(all=Mock(return_value=[]))
        await BookingRepository(db).list_requests_for_room(3, BookingListFilter(room_id=99))
        sql = str(db.scalars.await_args.args[0].compile(compile_kwargs={"literal_binds": True}))
        self.assertIn("bookings.room_id = 3", sql)
        self.assertIn("bookings.room_id = 99", sql)

    async def test_empty_room_scope_is_present_in_count_and_items(self):
        db = AsyncMock()
        db.scalar.return_value = 0
        db.scalars.return_value = Mock(all=Mock(return_value=[]))
        await RoomRepository(db).list(RoomFilter(), room_ids=[])
        for call in (db.scalar.await_args, db.scalars.await_args):
            sql = str(call.args[0].compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
            self.assertIn("1 != 1", sql)

    async def test_assignments_exclude_future_expired_and_revoked(self):
        db = AsyncMock()
        result = Mock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result
        await RoomModeratorRepository(db).get_by_user(17)
        sql = str(db.execute.await_args.args[0].compile(compile_kwargs={"literal_binds": True}))
        for condition in ("user_id = 17", "revoked_at IS NULL", "valid_from <= now()", "valid_until > now()"):
            self.assertIn(condition, sql)
