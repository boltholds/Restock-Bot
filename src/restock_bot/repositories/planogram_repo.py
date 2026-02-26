from __future__ import annotations

from restock_bot.db import pool


class PlanogramRepo:
    async def get_default_items(self, category_id: int) -> list[tuple[int, int]]:
        """
        Returns list of (product_id, planned_qty)
        """
        sql = """
        SELECT id_product, planned_quantity
        FROM bot2_planogram
        WHERE room_category_id = $1
        """
        rows = await pool().fetch(sql, category_id)
        return [(r["id_product"], r["planned_quantity"]) for r in rows]
