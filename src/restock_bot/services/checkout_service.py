from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from restock_bot.common.dto import CheckoutReport, ItemCount
from restock_bot.repositories.minibar_repo import MinibarRepo
from restock_bot.repositories.products_repo import ProductsRepo


@dataclass(frozen=True)
class _TxStock:
    tx_id: int
    ts: datetime
    event_type: str | None
    stock: Counter[int]  # product_id -> count


class CheckoutService:
    """
    Calculates "items taken" by comparing stock snapshots between transactions.

    Important domain assumptions:
    - bot2_minibar_transactions_details: one row = one unit.
    - bot2_minibar_transactions.id_minibar == bot2_hotel_rooms.id (room_id).
    - event_type == 'restock' acts like a reset point.
    """

    def __init__(self, minibar: MinibarRepo, products: ProductsRepo):
        self._minibar = minibar
        self._products = products

    async def calculate_for_period(
        self,
        room_id: int,
        start: datetime,
        end: datetime,
    ) -> CheckoutReport:
        txs = await self._minibar.list_transactions(room_id=room_id, start=start, end=end)

        if not txs:
            return CheckoutReport(
                room_id=room_id,
                period_start=start,
                period_end=end,
                items=[],
                total=Decimal("0"),
            )

        # Build stock snapshots per transaction
        snapshots: list[_TxStock] = []
        for tx in txs:
            tx_id = int(tx["id"])
            ts = tx["transaction_timestamp"]
            event_type = tx.get("event_type")
            product_ids = await self._minibar.list_transaction_items(tx_id)
            stock = Counter(product_ids)
            snapshots.append(_TxStock(tx_id=tx_id, ts=ts, event_type=event_type, stock=stock))

        # Compute net items taken across period
        net_taken: Counter[int] = Counter()

        # We interpret consumption as decreases of stock between consecutive snapshots:
        # taken = max(prev_count - curr_count, 0) per product.
        # Restock resets the baseline (i.e. do not compute delta across restock boundary).
        prev: _TxStock | None = None
        for cur in snapshots:
            if prev is None:
                prev = cur
                continue

            # If current transaction is marked as restock (or previous is restock),
            # we treat it as a reset boundary: baseline becomes current snapshot.
            if (cur.event_type == "restock") or (prev.event_type == "restock"):
                prev = cur
                continue

            net_taken += self._compute_taken(prev.stock, cur.stock)
            prev = cur

        # Fetch product info for all taken items
        product_ids = list(net_taken.keys())
        products = await self._products.get_products(product_ids)

        # Build report items
        items: list[ItemCount] = []
        total = Decimal("0")
        for pid, qty in net_taken.items():
            if qty <= 0:
                continue
            p = products.get(pid)
            if p is None:
                # Unknown product id (data integrity issue) — still show it
                name = f"product:{pid}"
                price = Decimal("0")
            else:
                name = p.name
                price = p.price

            items.append(ItemCount(product_id=pid, name=name, quantity=int(qty), unit_price=price))
            total += price * int(qty)

        # Stable order: by name then id
        items.sort(key=lambda x: (x.name.lower(), x.product_id))

        return CheckoutReport(
            room_id=room_id,
            period_start=start,
            period_end=end,
            items=items,
            total=total,
        )

    @staticmethod
    def _compute_taken(prev: Counter[int], cur: Counter[int]) -> Counter[int]:
        taken: Counter[int] = Counter()
        # union of keys
        keys = set(prev.keys()) | set(cur.keys())
        for k in keys:
            d = prev.get(k, 0) - cur.get(k, 0)
            if d > 0:
                taken[k] = d
        return taken
