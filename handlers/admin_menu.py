"""Админ-меню с кнопками."""
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
import logging

from config import is_admin
from states import AdminSearchStates
from database import search_by_plot_number, search_by_phone, search_by_full_name
from security import sanitize_search_query


def format_user_info(user: dict) -> str:
    """Форматировать информацию о пользователе для вывода."""
    status_emoji = {
        "pending": "⏳",
        "approved": "✅",
        "rejected": "❌"
    }
    status_text = {
        "pending": "На рассмотрении",
        "approved": "Одобрен",
        "rejected": "Отклонен"
    }
    
    emoji = status_emoji.get(user["status"], "❓")
    status = status_text.get(user["status"], user["status"])
    
    return (
        f"{emoji} <b>Статус:</b> {status}\n"
        f"<b>ФИО:</b> {user['full_name']}\n"
        f"<b>Телефон:</b> {user['phone']}\n"
        f"<b>Участок:</b> {user['plot_number']}\n"
        f"<b>Telegram ID:</b> {user['telegram_id']}\n"
        f"<b>Username:</b> @{user['username'] or 'не указан'}\n"
        f"<b>ID заявки:</b> {user['id']}\n"
        f"<b>Дата регистрации:</b> {user.get('created_at', 'не указана')}"
    )

logger = logging.getLogger(__name__)
router = Router()


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Создать админ-меню с кнопками."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔍 Поиск по участку"),
                KeyboardButton(text="📱 Поиск по телефону")
            ],
            [
                KeyboardButton(text="👤 Поиск по ФИО"),
                KeyboardButton(text="🔎 Универсальный поиск")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return keyboard


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Команда для открытия админ-меню."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    menu = get_admin_menu()
    await message.answer(
        "👨‍💼 <b>Админ-панель</b>\n\n"
        "Выберите действие из меню ниже или используйте команды:\n\n"
        "🔍 <b>Поиск:</b>\n"
        "/search_plot [номер участка]\n"
        "/search_phone [номер телефона]\n"
        "/search_name [ФИО]\n"
        "/search - универсальный поиск",
        reply_markup=menu,
        parse_mode="HTML"
    )
    logger.info(f"Админ {message.from_user.id} открыл админ-меню")


@router.message(lambda m: m.text == "🔍 Поиск по участку")
async def search_by_plot_button(message: Message, state: FSMContext):
    """Обработка кнопки поиска по участку."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.set_state(AdminSearchStates.waiting_for_plot)
    await message.answer(
        "🔍 <b>Поиск по номеру участка</b>\n\n"
        "Введите номер участка для поиска.\n"
        "Пример: 50:28:0090247",
        parse_mode="HTML"
    )


@router.message(lambda m: m.text == "📱 Поиск по телефону")
async def search_by_phone_button(message: Message, state: FSMContext):
    """Обработка кнопки поиска по телефону."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.set_state(AdminSearchStates.waiting_for_phone)
    await message.answer(
        "📱 <b>Поиск по номеру телефона</b>\n\n"
        "Введите номер телефона для поиска.\n"
        "Пример: +79001234567",
        parse_mode="HTML"
    )


@router.message(lambda m: m.text == "👤 Поиск по ФИО")
async def search_by_name_button(message: Message, state: FSMContext):
    """Обработка кнопки поиска по ФИО."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.set_state(AdminSearchStates.waiting_for_name)
    await message.answer(
        "👤 <b>Поиск по ФИО</b>\n\n"
        "Введите ФИО для поиска.\n"
        "Пример: Иванов Иван Иванович",
        parse_mode="HTML"
    )


@router.message(lambda m: m.text == "🔎 Универсальный поиск")
async def universal_search_button(message: Message, state: FSMContext):
    """Обработка кнопки универсального поиска."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.set_state(AdminSearchStates.waiting_for_universal)
    await message.answer(
        "🔎 <b>Универсальный поиск</b>\n\n"
        "Введите данные для поиска (номер участка, телефон или ФИО).\n"
        "Поиск будет выполнен по всем полям.",
        parse_mode="HTML"
    )


@router.message(StateFilter(AdminSearchStates.waiting_for_plot))
async def process_plot_search(message: Message, state: FSMContext):
    """Обработка поиска по участку из меню."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        await state.clear()
        return
    
    query = message.text.strip()
    is_valid, error_msg, sanitized = sanitize_search_query(query)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    users = await search_by_plot_number(sanitized)
    
    if not users:
        await message.answer(f"❌ Пользователи с номером участка '{sanitized}' не найдены.")
        await state.clear()
        return
    
    await message.answer(f"📋 <b>Найдено пользователей: {len(users)}</b>\n\n", parse_mode="HTML")
    
    for user in users:
        user_text = format_user_info(user)
        await message.answer(user_text, parse_mode="HTML")
    
    await state.clear()


@router.message(StateFilter(AdminSearchStates.waiting_for_phone))
async def process_phone_search(message: Message, state: FSMContext):
    """Обработка поиска по телефону из меню."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        await state.clear()
        return
    
    query = message.text.strip()
    is_valid, error_msg, sanitized = sanitize_search_query(query)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    users = await search_by_phone(sanitized)
    
    if not users:
        await message.answer(f"❌ Пользователи с номером телефона '{sanitized}' не найдены.")
        await state.clear()
        return
    
    await message.answer(f"📋 <b>Найдено пользователей: {len(users)}</b>\n\n", parse_mode="HTML")
    
    for user in users:
        user_text = format_user_info(user)
        await message.answer(user_text, parse_mode="HTML")
    
    await state.clear()


@router.message(StateFilter(AdminSearchStates.waiting_for_name))
async def process_name_search(message: Message, state: FSMContext):
    """Обработка поиска по ФИО из меню."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        await state.clear()
        return
    
    query = message.text.strip()
    is_valid, error_msg, sanitized = sanitize_search_query(query)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    users = await search_by_full_name(sanitized)
    
    if not users:
        await message.answer(f"❌ Пользователи с ФИО '{sanitized}' не найдены.")
        await state.clear()
        return
    
    await message.answer(f"📋 <b>Найдено пользователей: {len(users)}</b>\n\n", parse_mode="HTML")
    
    for user in users:
        user_text = format_user_info(user)
        await message.answer(user_text, parse_mode="HTML")
    
    await state.clear()


@router.message(StateFilter(AdminSearchStates.waiting_for_universal))
async def process_universal_search(message: Message, state: FSMContext):
    """Обработка универсального поиска из меню."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        await state.clear()
        return
    
    query = message.text.strip()
    is_valid, error_msg, sanitized = sanitize_search_query(query)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        await state.clear()
        return
    
    # Поиск по всем критериям
    results_plot = await search_by_plot_number(sanitized)
    results_phone = await search_by_phone(sanitized)
    results_name = await search_by_full_name(sanitized)
    
    # Объединяем результаты, убирая дубликаты
    all_results = {}
    for user in results_plot + results_phone + results_name:
        all_results[user["id"]] = user
    
    users = list(all_results.values())
    
    if not users:
        await message.answer(f"❌ По запросу '{sanitized}' ничего не найдено.")
        await state.clear()
        return
    
    await message.answer(f"📋 <b>Найдено пользователей: {len(users)}</b>\n\n", parse_mode="HTML")
    
    for user in users:
        user_text = format_user_info(user)
        await message.answer(user_text, parse_mode="HTML")
    
    await state.clear()

