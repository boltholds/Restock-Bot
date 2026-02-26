from __future__ import annotations

from datetime import datetime, timezone

from restock_bot.common.errors import NoActiveSession, RoomNotFound
from restock_bot.common.dto import CheckoutReport
from restock_bot.repositories.rooms_repo import RoomsRepo
from restock_bot.repositories.sessions_repo import SessionsRepo
from restock_bot.services.checkout_service import CheckoutService


class OccupancyService:
    def __init__(self, rooms: RoomsRepo, sessions: SessionsRepo, checkout: CheckoutService):
        self._rooms = rooms
        self._sessions = sessions
        self._checkout = checkout

    async def check_in(self, room_id: int) -> int:
        room = await self._rooms.get_room(room_id)
        if room is None:
            raise RoomNotFound(f"Room {room_id} not found")

        now = datetime.now(timezone.utc)
        session_id = await self._sessions.create_session(room_id=room_id, check_in=now, transfer_id=None)
        await self._rooms.set_guest_session(room_id, session_id)
        return session_id

    async def check_out(self, room_id: int) -> CheckoutReport:
        room = await self._rooms.get_room(room_id)
        if room is None:
            raise RoomNotFound(f"Room {room_id} not found")

        active = await self._sessions.get_active_session_by_room(room_id)
        if not active:
            raise NoActiveSession(f"No active session for room {room_id}")

        now = datetime.now(timezone.utc)
        session_id = int(active["id"])

        # Close this session
        await self._sessions.close_session(session_id, now)
        await self._rooms.set_guest_session(room_id, None)

        # Include transfers chain in the bill:
        linked = await self._sessions.get_linked_sessions(session_id)

        # Sum bills across linked sessions
        # (каждая сессия имеет свой room_id и окно check_in..check_out)
        merged = await self._merge_checkout_reports(linked, now)

        return merged

    async def transfer(self, from_room_id: int, to_room_id: int) -> int:
        from_room = await self._rooms.get_room(from_room_id)
        to_room = await self._rooms.get_room(to_room_id)
        if from_room is None or to_room is None:
            raise RoomNotFound("Room not found")

        active = await self._sessions.get_active_session_by_room(from_room_id)
        if not active:
            raise NoActiveSession(f"No active session for room {from_room_id}")

        now = datetime.now(timezone.utc)
        old_session_id = int(active["id"])

        # close old
        await self._sessions.close_session(old_session_id, now)
        await self._rooms.set_guest_session(from_room_id, None)

        # create new with transfer_id = old_session_id
        new_session_id = await self._sessions.create_session(
            room_id=to_room_id,
            check_in=now,
            transfer_id=old_session_id,
        )
        await self._rooms.set_guest_session(to_room_id, new_session_id)
        return new_session_id

    async def _merge_checkout_reports(self, linked_sessions: list[dict], default_end: datetime) -> CheckoutReport:
        """
        linked_sessions: list of dict rows from guest_sessions
        """
        from collections import Counter
        from decimal import Decimal

        net = Counter()  # product_id -> qty
        names = {}
        prices = {}

        period_start = None
        period_end = default_end
        room_id_for_report = int(linked_sessions[0]["room_id"]) if linked_sessions else 0

        for s in linked_sessions:
            start = s["check_in"]
            end = s["check_out"] or default_end
            rid = int(s["room_id"])
            if period_start is None or start < period_start:
                period_start = start
            if end > period_end:
                period_end = end

            rep = await self._checkout.calculate_for_period(rid, start, end)

            for it in rep.items:
                net[it.product_id] += it.quantity
                names[it.product_id] = it.name
                prices[it.product_id] = it.unit_price

        items = []
        total = Decimal("0")
        for pid, qty in net.items():
            if qty <= 0:
                continue
            name = names.get(pid, f"product:{pid}")
            price = prices.get(pid, Decimal("0"))
            items.append((name.lower(), pid, name, qty, price))
            total += price * qty

        items.sort(key=lambda x: (x[0], x[1]))

        from restock_bot.common.dto import ItemCount, CheckoutReport
        return CheckoutReport(
            room_id=room_id_for_report,
            period_start=period_start or default_end,
            period_end=period_end,
            items=[ItemCount(product_id=pid, name=name, quantity=qty, unit_price=price) for _, pid, name, qty, price in items],
            total=total,
        )
