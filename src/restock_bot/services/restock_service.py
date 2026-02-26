from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from restock_bot.common.dto import ItemCount, RestockMissing, RestockResult
from restock_bot.common.errors import NoTransactions, RoomNotFound
from restock_bot.repositories.rooms_repo import RoomsRepo
from restock_bot.repositories.planogram_repo import PlanogramRepo
from restock_bot.repositories.minibar_repo import MinibarRepo
from restock_bot.repositories.products_repo import ProductsRepo


class RestockService:
    """
    Port of Ruby restock_items + restock_room.

    Current behavior (1:1 with Ruby MVP):
    - get_missing: planogram(category) - stock(last_transaction)
    - mark_restocked: set last_transaction.event_type='restock'

    Later improvement:
    - create a dedicated restock transaction instead of mutating last one.
    """

    def __init__(
        self,
        rooms: RoomsRepo,
        planogram: PlanogramRepo,
        minibar: MinibarRepo,
        products: ProductsRepo,
    ):
        self._rooms = rooms
        self._planogram = planogram
        self._minibar = minibar
        self._products = products

    async def get_missing(self, room_id: int) -> RestockMissing:
        room = await self._rooms.get_room(room_id)
        if room is None:
            raise RoomNotFound(f"Room {room_id} not found")

        planned_pairs = await self._planogram.get_default_items(room.category)
        planned = Counter({pid: qty for pid, qty in planned_pairs})

        last_tx = await self._minibar.get_last_transaction(room_id)
        if last_tx is None:
            # No snapshots => cannot compute current stock
            raise NoTransactions(f"No transactions for room {room_id}")

        product_ids = await self._minibar.list_transaction_items(int(last_tx["id"]))
        current = Counter(product_ids)

        missing: Counter[int] = Counter()
        for pid, planned_qty in planned.items():
            diff = planned_qty - current.get(pid, 0)
            if diff > 0:
                missing[pid] = diff

        # hydrate product info
        products = await self._products.get_products(list(missing.keys()))

        items: list[ItemCount] = []
        for pid, qty in missing.items():
            p = products.get(pid)
            if p is None:
                name = f"product:{pid}"
                price = 0
            else:
                name = p.name
                price = p.price

            items.append(ItemCount(product_id=pid, name=name, quantity=int(qty), unit_price=price))

        items.sort(key=lambda x: (x.name.lower(), x.product_id))
        return RestockMissing(room_id=room_id, items=items)

    async def mark_restocked(self, room_id: int) -> RestockResult:
        last_tx = await self._minibar.get_last_transaction(room_id)
        if last_tx is None:
            raise NoTransactions(f"No transactions for room {room_id}")

        tx_id = int(last_tx["id"])
        await self._minibar.mark_transaction_event(tx_id, "restock")

        return RestockResult(
            room_id=room_id,
            transaction_id=tx_id,
            marked_at=datetime.now(timezone.utc),
        )


    async def get_current_stock(self, room_id: int) -> list[ItemCount]:
        """
        Current stock == items in the last minibar transaction snapshot.
        """
        last_tx = await self._minibar.get_last_transaction(room_id)
        if last_tx is None:
            raise NoTransactions(f"No transactions for room {room_id}")

        tx_id = int(last_tx["id"])
        product_ids = await self._minibar.list_transaction_items(tx_id)
        counts = Counter(product_ids)

        products = await self._products.get_products(list(counts.keys()))

        items: list[ItemCount] = []
        for pid, qty in counts.items():
            p = products.get(pid)
            if p is None:
                name = f"product:{pid}"
                price = 0
            else:
                name = p.name
                price = p.price
            items.append(ItemCount(product_id=pid, name=name, quantity=int(qty), unit_price=price))

        items.sort(key=lambda x: (x.name.lower(), x.product_id))
        return items