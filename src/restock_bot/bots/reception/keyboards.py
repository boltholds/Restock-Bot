from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def rooms_kb(rooms: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"room:{room_id}")]
            for room_id, label in rooms
        ]
    )


def room_actions_kb(room_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Check-in", callback_data=f"checkin:{room_id}"),
                InlineKeyboardButton(text="🔴 Check-out", callback_data=f"checkout:{room_id}"),
            ],
            [InlineKeyboardButton(text="Transfer", callback_data=f"transfer_from:{room_id}")],
            [InlineKeyboardButton(text="↩ Назад", callback_data="back:rooms")],
        ]
    )


def transfer_targets_kb(from_room_id: int, targets: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"transfer_to:{from_room_id}:{room_id}")]
            for room_id, label in targets
        ] + [[InlineKeyboardButton(text="↩ Назад", callback_data=f"room:{from_room_id}")]]
    )
