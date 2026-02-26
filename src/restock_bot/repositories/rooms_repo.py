from __future__ import annotations

from restock_bot.db import pool
from restock_bot.common.dto import Room


class RoomsRepo:
    
    # ---- Restock bot
    
    async def list_rooms(self) -> list[Room]:
        sql = """
        SELECT id, room_num, category, id_hotel, guest_id, id_minibar
        FROM bot2_hotel_rooms
        ORDER BY room_num ASC
        """
        rows = await pool().fetch(sql)
        return [
            Room(
                id=r["id"],
                room_num=r["room_num"],
                category=r["category"],
                hotel_id=r.get("id_hotel"),
                guest_session_id=r.get("guest_id"),
                id_minibar=r["id_minibar"]
            )
            for r in rows
        ]

    async def list_rooms_with_status(self) -> list[tuple[Room, str]]:
        """
        Returns [(room, status_icon)]
        status_icon:
          🟢 = free (no guest session bound)
          🔴 = occupied
        """
        rooms = await self.list_rooms()
        out: list[tuple[Room, str]] = []
        for r in rooms:
            icon = "🔴" if r.guest_session_id else "🟢"
            out.append((r, icon))
        return out

    async def get_room(self, room_id: int) -> Room | None:
        sql = """
        SELECT id, room_num, category, id_hotel, guest_id, id_minibar
        FROM bot2_hotel_rooms
        WHERE id = $1
        """
        r = await pool().fetchrow(sql, room_id)
        if r is None:
            return None
        return Room(
            id=r["id"],
            room_num=r["room_num"],
            category=r["category"],
            hotel_id=r.get("id_hotel"),
            guest_session_id=r.get("guest_id"),
            id_minibar=r["id_minibar"]
            )
        
    
    # ---- Receptions bot
    
    async def set_guest_session(self, room_id: int, session_id: int | None) -> None:
        sql = """
        UPDATE bot2_hotel_rooms
        SET guest_id = $2
        WHERE id = $1
        """
        await pool().execute(sql, room_id, session_id)
