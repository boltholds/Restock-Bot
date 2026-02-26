from datetime import datetime
from typing import Iterable
from restock_bot.db import pool


class MinibarRepo:
    async def get_last_transaction(self, room_id: int) -> dict | None:
        sql = """
        SELECT *
        FROM bot2_minibar_transactions
        WHERE id_minibar = $1
        ORDER BY id DESC
        LIMIT 1
        """
        r = await pool().fetchrow(sql, room_id)
        return dict(r) if r else None

    async def list_transaction_items(self, transaction_id: int) -> list[int]:
        sql = """
        SELECT id_product
        FROM bot2_minibar_transactions_details
        WHERE id_transaction = $1
        """
        rows = await pool().fetch(sql, transaction_id)
        return [r["id_product"] for r in rows]

    async def mark_transaction_event(self, transaction_id: int, event_type: str) -> None:
        sql = """
        UPDATE bot2_minibar_transactions
        SET event_type = $2
        WHERE id = $1
        """
        await pool().execute(sql, transaction_id, event_type)
