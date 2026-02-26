from restock_bot.common.dto import CheckoutReport


def rooms_title() -> str:
    return "Ресепшн: выбери комнату (🟢 свободно / 🔴 занято):"


def room_title(room_num: int, room_id: int, status_icon: str) -> str:
    return f"{status_icon} Комната {room_num} (id={room_id})"


def checkout_text(rep: CheckoutReport) -> str:
    lines = [
        "Чек:",
        f"Период: {rep.period_start} → {rep.period_end}",
        "",
    ]
    if not rep.items:
        lines.append("Нет списаний по минибару.")
    else:
        for it in rep.items:
            lines.append(f"• {it.name}: {it.quantity} × {it.unit_price} = {it.unit_price * it.quantity}")
    lines.append("")
    lines.append(f"Итого: {rep.total}")
    return "\n".join(lines)
