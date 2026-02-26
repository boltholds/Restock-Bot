from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from restock_bot.repositories.rooms_repo import RoomsRepo
from restock_bot.repositories.planogram_repo import PlanogramRepo
from restock_bot.repositories.minibar_repo import MinibarRepo
from restock_bot.repositories.products_repo import ProductsRepo
from restock_bot.services.restock_service import RestockService
from restock_bot.common.errors import DomainError

from restock_bot.bots.restock.keyboards import rooms_kb, room_actions_kb, confirm_restock_kb
from restock_bot.bots.restock.texts import rooms_title, room_title, missing_text, stock_text



router = Router()

# Poor-man DI (пока без контейнера)
rooms_repo = RoomsRepo()
planogram_repo = PlanogramRepo()
minibar_repo = MinibarRepo()
products_repo = ProductsRepo()
restock_service = RestockService(
    rooms=rooms_repo,
    planogram=planogram_repo,
    minibar=minibar_repo,
    products=products_repo,
)


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

    await c.message.edit_text(
        room_title(room.room_num, room.id),
        reply_markup=room_actions_kb(room.id),
    )
    await c.answer()


@router.callback_query(F.data.startswith("missing:"))
async def show_missing(c: CallbackQuery):
    room_id = int(c.data.split(":", 1)[1])
    try:
        m = await restock_service.get_missing(room_id)
        await c.message.edit_text(
            missing_text(m) + "\n\n(Выберите действие ниже)",
            reply_markup=room_actions_kb(room_id),
        )
        await c.answer()
    except DomainError as e:
        await c.answer(str(e), show_alert=True)


@router.callback_query(F.data.startswith("restock_confirm:"))
async def restock_confirm(c: CallbackQuery):
    room_id = int(c.data.split(":", 1)[1])
    await c.message.edit_text(
        "Подтвердите: минибар действительно пополнен?",
        reply_markup=confirm_restock_kb(room_id),
    )
    await c.answer()


@router.callback_query(F.data.startswith("restock:"))
async def restock_apply(c: CallbackQuery):
    room_id = int(c.data.split(":", 1)[1])
    try:
        res = await restock_service.mark_restocked(room_id)
        room = await rooms_repo.get_room(room_id)
        label = f"{room.room_num}" if room else str(room_id)
        await c.message.edit_text(
            f"Пополнение подтверждено для комнаты {label}.\n"
            f"Транзакция помечена restock: {res.transaction_id}",
            reply_markup=room_actions_kb(room_id),
        )
        await c.answer()
    except DomainError as e:
        await c.answer(str(e), show_alert=True)


@router.callback_query(F.data.startswith("stock:"))
async def show_stock(c: CallbackQuery):
    room_id = int(c.data.split(":", 1)[1])
    try:
        items = await restock_service.get_current_stock(room_id)
        await c.message.edit_text(
            stock_text(items) + "\n\n(Выбери действие ниже)",
            reply_markup=room_actions_kb(room_id),
        )
        await c.answer()
    except DomainError as e:
        await c.answer(str(e), show_alert=True)
