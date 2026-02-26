from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def rooms_kb(rooms: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    # rooms: [(room_id, label)]
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"room:{room_id}")]
        for room_id, label in rooms
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def room_actions_kb(room_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Недостающее", callback_data=f"missing:{room_id}")],
            [InlineKeyboardButton(text="Минибар пополнен", callback_data=f"restock_confirm:{room_id}")],
            [InlineKeyboardButton(text="↩ Назад", callback_data="back:rooms")],
        ]
    )


def confirm_restock_kb(room_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data=f"restock:{room_id}"),
                InlineKeyboardButton(text="Отмена", callback_data=f"room:{room_id}"),
            ]
        ]
    )




def room_actions_kb(room_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Текущий запас", callback_data=f"stock:{room_id}")],
            [InlineKeyboardButton(text="Недостающее", callback_data=f"missing:{room_id}")],
            [InlineKeyboardButton(text="Минибар пополнен!", callback_data=f"restock_confirm:{room_id}")],
            [InlineKeyboardButton(text="↩ Назад", callback_data="back:rooms")],
        ]
    )