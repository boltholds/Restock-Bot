from decimal import Decimal
from restock_bot.db import pool
from restock_bot.common.dto import Product


class ProductsRepo:
    async def get_products(self, ids: list[int]) -> dict[int, Product]:
        if not ids:
            return {}

        sql = """
        SELECT id, name, price
        FROM bot2_products
        WHERE id = ANY($1::int[])
        """
        rows = await pool().fetch(sql, ids)

        return {
            r["id"]: Product(
                id=r["id"],
                name=r["name"],
                price=Decimal(r["price"]),
            )
            for r in rows
        }
