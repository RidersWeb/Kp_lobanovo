"""Обработчики поиска для администраторов."""
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
import logging

from config import is_admin
from database import search_by_plot_number, search_by_phone, search_by_full_name
from security import sanitize_search_query

logger = logging.getLogger(__name__)
router = Router()


class SearchStates(StatesGroup):
    """Состояния для поиска."""
    waiting_for_query = State()


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


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    """Команда для начала поиска."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    await state.set_state(SearchStates.waiting_for_query)
    await message.answer(
        "🔍 <b>Поиск пользователей</b>\n\n"
        "Введите данные для поиска:\n"
        "• Номер участка\n"
        "• Номер телефона\n"
        "• ФИО\n\n"
        "Или используйте команды:\n"
        "/search_plot [номер участка]\n"
        "/search_phone [номер телефона]\n"
        "/search_name [ФИО]",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("search_plot"))
async def cmd_search_plot(message: Message):
    """Поиск по номеру участка."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Укажите номер участка для поиска.\n"
            "Пример: /search_plot 50:28:0090247"
        )
        return
    
    plot_number = args[1].strip()
    
    # Санитизация запроса
    is_valid, error_msg, sanitized = sanitize_search_query(plot_number)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    users = await search_by_plot_number(sanitized)
    
    if not users:
        await message.answer(f"❌ Пользователи с номером участка '{plot_number}' не найдены.")
        return
    
    await message.answer(
        f"📋 <b>Найдено пользователей: {len(users)}</b>\n\n",
        parse_mode=ParseMode.HTML
    )
    
    for user in users:
        user_text = format_user_info(user)
        await message.answer(user_text, parse_mode=ParseMode.HTML)
        
        # Отправляем документ, если есть
        if user.get("document_file_id"):
            try:
                await message.answer_photo(
                    user["document_file_id"],
                    caption=f"Документ пользователя: {user['full_name']}"
                )
            except:
                try:
                    await message.answer_document(
                        user["document_file_id"],
                        caption=f"Документ пользователя: {user['full_name']}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке документа: {e}")


@router.message(Command("search_phone"))
async def cmd_search_phone(message: Message):
    """Поиск по номеру телефона."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Укажите номер телефона для поиска.\n"
            "Пример: /search_phone +79001234567"
        )
        return
    
    phone = args[1].strip()
    
    # Санитизация запроса
    is_valid, error_msg, sanitized = sanitize_search_query(phone)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    users = await search_by_phone(sanitized)
    
    if not users:
        await message.answer(f"❌ Пользователи с номером телефона '{phone}' не найдены.")
        return
    
    await message.answer(
        f"📋 <b>Найдено пользователей: {len(users)}</b>\n\n",
        parse_mode=ParseMode.HTML
    )
    
    for user in users:
        user_text = format_user_info(user)
        await message.answer(user_text, parse_mode=ParseMode.HTML)
        
        # Отправляем документ, если есть
        if user.get("document_file_id"):
            try:
                await message.answer_photo(
                    user["document_file_id"],
                    caption=f"Документ пользователя: {user['full_name']}"
                )
            except:
                try:
                    await message.answer_document(
                        user["document_file_id"],
                        caption=f"Документ пользователя: {user['full_name']}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке документа: {e}")


@router.message(Command("search_name"))
async def cmd_search_name(message: Message):
    """Поиск по ФИО."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Укажите ФИО для поиска.\n"
            "Пример: /search_name Иванов Иван Иванович"
        )
        return
    
    full_name = args[1].strip()
    
    # Санитизация запроса
    is_valid, error_msg, sanitized = sanitize_search_query(full_name)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    users = await search_by_full_name(sanitized)
    
    if not users:
        await message.answer(f"❌ Пользователи с ФИО '{full_name}' не найдены.")
        return
    
    await message.answer(
        f"📋 <b>Найдено пользователей: {len(users)}</b>\n\n",
        parse_mode=ParseMode.HTML
    )
    
    for user in users:
        user_text = format_user_info(user)
        await message.answer(user_text, parse_mode=ParseMode.HTML)
        
        # Отправляем документ, если есть
        if user.get("document_file_id"):
            try:
                await message.answer_photo(
                    user["document_file_id"],
                    caption=f"Документ пользователя: {user['full_name']}"
                )
            except:
                try:
                    await message.answer_document(
                        user["document_file_id"],
                        caption=f"Документ пользователя: {user['full_name']}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке документа: {e}")


@router.message(StateFilter(SearchStates.waiting_for_query))
async def process_search_query(message: Message, state: FSMContext):
    """Обработка запроса поиска (универсальный поиск)."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        await state.clear()
        return
    
    query = message.text.strip()
    
    if not query:
        await message.answer("❌ Введите данные для поиска.")
        return
    
    # Санитизация запроса
    is_valid, error_msg, sanitized = sanitize_search_query(query)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        await state.clear()
        return
    
    # Пробуем найти по всем критериям
    results_plot = await search_by_plot_number(sanitized)
    results_phone = await search_by_phone(sanitized)
    results_name = await search_by_full_name(sanitized)
    
    # Объединяем результаты, убирая дубликаты
    all_results = {}
    for user in results_plot + results_phone + results_name:
        all_results[user["id"]] = user
    
    users = list(all_results.values())
    
    if not users:
        await message.answer(
            f"❌ По запросу '{query}' ничего не найдено.\n\n"
            "Попробуйте использовать команды:\n"
            "/search_plot [номер участка]\n"
            "/search_phone [номер телефона]\n"
            "/search_name [ФИО]"
        )
        await state.clear()
        return
    
    await message.answer(
        f"📋 <b>Найдено пользователей: {len(users)}</b>\n\n",
        parse_mode=ParseMode.HTML
    )
    
    for user in users:
        user_text = format_user_info(user)
        await message.answer(user_text, parse_mode=ParseMode.HTML)
        
        # Отправляем документ, если есть
        if user.get("document_file_id"):
            try:
                await message.answer_photo(
                    user["document_file_id"],
                    caption=f"Документ пользователя: {user['full_name']}"
                )
            except:
                try:
                    await message.answer_document(
                        user["document_file_id"],
                        caption=f"Документ пользователя: {user['full_name']}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке документа: {e}")
    
    await state.clear()

