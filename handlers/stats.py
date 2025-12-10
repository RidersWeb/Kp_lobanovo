"""Обработчики статистики и управления пользователями."""
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
import logging

from config import is_admin, GROUP_ID
from database import get_statistics, get_all_users, get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Показать статистику пользователей."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    try:
        stats = await get_statistics()
        
        stats_text = (
            "📊 <b>Статистика пользователей</b>\n\n"
            f"👥 <b>Всего зарегистрировано:</b> {stats['total']}\n\n"
            f"⏳ <b>На рассмотрении:</b> {stats['pending']}\n"
            f"✅ <b>Одобрено:</b> {stats['approved']}\n"
            f"❌ <b>Отклонено:</b> {stats['rejected']}\n"
        )
        
        await message.answer(stats_text, parse_mode=ParseMode.HTML)
        logger.info(f"Админ {message.from_user.id} запросил статистику")
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при получении статистики.")


@router.message(Command("list_users"))
async def cmd_list_users(message: Message):
    """Показать список всех пользователей."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    try:
        users = await get_all_users()
        
        if not users:
            await message.answer("📋 Пользователи не найдены.")
            return
        
        await message.answer(
            f"📋 <b>Всего пользователей: {len(users)}</b>\n\n"
            "Используйте /remove_user [telegram_id] для удаления пользователя из группы.",
            parse_mode=ParseMode.HTML
        )
        
        # Показываем пользователей порциями по 10
        for i in range(0, len(users), 10):
            batch = users[i:i+10]
            users_text = ""
            for user in batch:
                status_emoji = {
                    "pending": "⏳",
                    "approved": "✅",
                    "rejected": "❌"
                }
                emoji = status_emoji.get(user["status"], "❓")
                users_text += (
                    f"{emoji} <b>{user['full_name']}</b>\n"
                    f"   ID: {user['telegram_id']} | Участок: {user['plot_number']}\n"
                    f"   Статус: {user['status']}\n\n"
                )
            
            await message.answer(users_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при получении списка пользователей.")


@router.message(Command("remove_user"))
async def cmd_remove_user(message: Message, bot: Bot):
    """Удалить пользователя из группы."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer(
                "❌ Укажите Telegram ID пользователя для удаления.\n"
                "Пример: /remove_user 123456789\n\n"
                "Используйте /list_users чтобы увидеть всех пользователей."
            )
            return
        
        telegram_id = int(args[1].strip())
        
        # Проверяем, существует ли пользователь в БД
        user = await get_user_by_telegram_id(telegram_id)
        if not user:
            await message.answer(f"❌ Пользователь с ID {telegram_id} не найден в базе данных.")
            return
        
        # Удаляем пользователя из группы
        try:
            from config import GROUP_ID
            
            # Пробуем удалить из группы
            try:
                await bot.ban_chat_member(
                    chat_id=GROUP_ID,
                    user_id=telegram_id
                )
                # Сразу разбаниваем, чтобы он мог быть удален
                await bot.unban_chat_member(
                    chat_id=GROUP_ID,
                    user_id=telegram_id,
                    only_if_banned=True
                )
                
                await message.answer(
                    f"✅ Пользователь <b>{user['full_name']}</b> (ID: {telegram_id}) удален из группы.",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Админ {message.from_user.id} удалил пользователя {telegram_id} из группы")
                
            except Exception as group_error:
                # Если группа мигрировала, пробуем новый ID
                from aiogram.exceptions import TelegramMigrateToChat
                if isinstance(group_error, TelegramMigrateToChat):
                    new_chat_id = group_error.migrate_to_chat_id
                    try:
                        await bot.ban_chat_member(
                            chat_id=new_chat_id,
                            user_id=telegram_id
                        )
                        await bot.unban_chat_member(
                            chat_id=new_chat_id,
                            user_id=telegram_id,
                            only_if_banned=True
                        )
                        await message.answer(
                            f"✅ Пользователь <b>{user['full_name']}</b> (ID: {telegram_id}) удален из группы.\n"
                            f"⚠️ Обновите GROUP_ID в .env на: {new_chat_id}",
                            parse_mode=ParseMode.HTML
                        )
                        logger.info(f"Админ {message.from_user.id} удалил пользователя {telegram_id} из группы (новая)")
                    except Exception as retry_error:
                        await message.answer(
                            f"❌ Ошибка при удалении из группы: {retry_error}\n"
                            f"Проверьте, что бот имеет права на удаление участников."
                        )
                        logger.error(f"Ошибка при удалении пользователя {telegram_id}: {retry_error}")
                else:
                    await message.answer(
                        f"❌ Ошибка при удалении из группы: {group_error}\n"
                        f"Проверьте, что бот имеет права на удаление участников."
                    )
                    logger.error(f"Ошибка при удалении пользователя {telegram_id}: {group_error}")
                    
        except Exception as e:
            await message.answer(f"❌ Произошла ошибка: {e}")
            logger.error(f"Ошибка при удалении пользователя: {e}", exc_info=True)
            
    except ValueError:
        await message.answer("❌ Неверный формат ID. Используйте числовой Telegram ID.")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды удаления: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при обработке команды.")

