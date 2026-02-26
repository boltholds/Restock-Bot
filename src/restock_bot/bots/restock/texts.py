from restock_bot.common.dto import RestockMissing, ItemCount


def rooms_title() -> str:
    return "Выбери комнату (🟢 свободно / 🔴 занято):"


def stock_text(items: list[ItemCount]) -> str:
    if not items:
        return "(пусто)"
    lines = ["Текущий запас:"]
    for it in items:
        lines.append(f"• {it.name}: {it.quantity}")
    return "\n".join(lines)


def room_title(room_num: int, room_id: int) -> str:
    return f"Комната {room_num} (id={room_id})"


def missing_text(m: RestockMissing) -> str:
    if not m.items:
        return "✅ По планограмме всё на месте. Ничего докладывать не нужно."
    lines = [" Недостающее по планограмме:"]
    for it in m.items:
        lines.append(f"• {it.name}: {it.quantity}")
    return "\n".join(lines)
