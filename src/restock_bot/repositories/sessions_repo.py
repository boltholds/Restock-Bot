from __future__ import annotations

from datetime import datetime
from restock_bot.db import pool


class SessionsRepo:
    async def create_session(
        self,
        room_id: int,
        check_in: datetime,
        transfer_id: int | None = None,
    ) -> int:
        sql = """
        INSERT INTO guest_sessions (room_id, check_in, transfer_id)
        VALUES ($1, $2, $3)
        RETURNING id
        """
        row = await pool().fetchrow(sql, room_id, check_in, transfer_id)
        return int(row["id"])

    async def get_active_session_by_room(self, room_id: int) -> dict | None:
        sql = """
        SELECT *
        FROM guest_sessions
        WHERE room_id = $1 AND check_out IS NULL
        ORDER BY id DESC
        LIMIT 1
        """
        r = await pool().fetchrow(sql, room_id)
        return dict(r) if r else None

    async def close_session(self, session_id: int, check_out: datetime) -> None:
        sql = """
        UPDATE guest_sessions
        SET check_out = $2
        WHERE id = $1
        """
        await pool().execute(sql, session_id, check_out)

    async def get_session(self, session_id: int) -> dict | None:
        sql = "SELECT * FROM guest_sessions WHERE id=$1"
        r = await pool().fetchrow(sql, session_id)
        return dict(r) if r else None

    async def get_linked_sessions(self, root_session_id: int) -> list[dict]:
        """
        Port of Ruby get_all_linked_sessions:
        Walks "transfer_id" chain forward: new_session.transfer_id = previous_session.id
        """
        out: list[dict] = []
        current_id = root_session_id

        while True:
            current = await self.get_session(current_id)
            if not current:
                break

            out.append(current)

            nxt = await pool().fetchrow(
                """
                SELECT *
                FROM guest_sessions
                WHERE transfer_id = $1
                ORDER BY id ASC
                LIMIT 1
                """,
                current_id,
            )
            if not nxt:
                break
            current_id = int(nxt["id"])

        return out
