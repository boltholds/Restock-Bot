from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from restock_bot.common.errors import DomainError
from restock_bot.repositories.rooms_repo import RoomsRepo
from restock_bot.repositories.sessions_repo import SessionsRepo
from restock_bot.repositories.minibar_repo import MinibarRepo
from restock_bot.repositories.products_repo import ProductsRepo
from restock_bot.services.checkout_service import CheckoutService
from restock_bot.services.occupancy_service import OccupancyService

from restock_bot.bots.reception.keyboards import rooms_kb, room_actions_kb, transfer_targets_kb
from restock_bot.bots.reception.texts import rooms_title, room_title, checkout_text


router = Router()

rooms_repo = RoomsRepo()
sessions_repo = SessionsRepo()
minibar_repo = MinibarRepo()
products_repo = ProductsRepo()

checkout_service = CheckoutService(minibar=minibar_repo, products=products_repo)
occupancy_service = OccupancyService(rooms=rooms_repo, sessions=sessions_repo, checkout=checkout_service)


@router.message(CommandStart())
async def start(m: Message):
    rooms_with = await rooms_repo.list_rooms_with_status()
    pairs = [(r.id, f"{icon} {r.room_num}") for r, icon in rooms_with]
    await m.answer(rooms_title(), reply_markup=rooms_kb(pairs))


@router.callback_query(F.data == "back:rooms")
async def back_rooms(c: CallbackQuery):
    rooms_with = await rooms_repo.list_rooms_with_status()
    pairs = [(r.id, f"{icon} {r.room_num}") for r, icon in rooms_with]
    await c.message.edit_text(rooms_title(), reply_markup=rooms_kb(pairs))
    await c.answer()


@router.callback_query(F.data.startswith("room:"))
async def open_room(c: CallbackQuery):
    room_id = int(c.data.split(":", 1)[1])
    room = await rooms_repo.get_room(room_id)
    if room is None:
        await c.answer("Комната не найдена", show_alert=True)
        return
    icon = "🔴" if room.guest_session_id else "🟢"
    await c.message.edit_text(
        room_title(room.room_num, room.id, icon),
        reply_markup=room_actions_kb(room.id),
    )
    await c.answer()


@router.callback_query(F.data.startswith("checkin:"))
async def check_in(c: CallbackQuery):
    room_id = int(c.data.split(":", 1)[1])
    try:
        sid = await occupancy_service.check_in(room_id)
        await c.answer("Заселение выполнено")
        await open_room(c)  # обновим карточку комнаты
    except DomainError as e:
        await c.answer(str(e), show_alert=True)


@router.callback_query(F.data.startswith("checkout:"))
async def check_out(c: CallbackQuery):
    room_id = int(c.data.split(":", 1)[1])
    try:
        rep = await occupancy_service.check_out(room_id)
        await c.message.edit_text(checkout_text(rep), reply_markup=room_actions_kb(room_id))
        await c.answer("Выселение выполнено")
    except DomainError as e:
        await c.answer(str(e), show_alert=True)


@router.callback_query(F.data.startswith("transfer_from:"))
async def transfer_from(c: CallbackQuery):
    from_room_id = int(c.data.split(":", 1)[1])

    # таргеты — только свободные комнаты
    rooms_with = await rooms_repo.list_rooms_with_status()
    targets = [(r.id, f"{icon} {r.room_num}") for r, icon in rooms_with if (not r.guest_session_id and r.id != from_room_id)]

    if not targets:
        await c.answer("Нет свободных комнат для переселения", show_alert=True)
        return

    await c.message.edit_text(
        "Выбери комнату, куда переселить гостя:",
        reply_markup=transfer_targets_kb(from_room_id, targets),
    )
    await c.answer()


@router.callback_query(F.data.startswith("transfer_to:"))
async def transfer_to(c: CallbackQuery):
    _, from_room_id, to_room_id = c.data.split(":")
    from_room_id = int(from_room_id)
    to_room_id = int(to_room_id)

    try:
        await occupancy_service.transfer(from_room_id, to_room_id)
        await c.answer("Переселение выполнено")
        # после transfer логичнее показать новую комнату
        c.data = f"room:{to_room_id}"
        await open_room(c)
    except DomainError as e:
        await c.answer(str(e), show_alert=True)
