"""Обработчики для администратора."""
from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
import logging

from config import is_admin, GROUP_ID
from database import update_user_status, get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery, bot: Bot):
    """Обработка одобрения пользователя."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для выполнения этого действия", show_alert=True)
        return
    
    telegram_id = int(callback.data.split("_")[1])
    
    try:
        # Обновляем статус в БД
        await update_user_status(telegram_id, "approved")
        
        # Получаем информацию о пользователе
        user = await get_user_by_telegram_id(telegram_id)
        
        # Генерируем одноразовую ссылку-приглашение
        try:
            invite_link = await bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                member_limit=1,
                name=f"invite_{telegram_id}"
            )
            invite_url = invite_link.invite_link
        except Exception as e:
            logger.error(f"Ошибка при создании invite link: {e}", exc_info=True)
            invite_url = None
        
        # Отправляем уведомление пользователю
        if invite_url:
            await bot.send_message(
                telegram_id,
                f"✅ <b>Ваша заявка одобрена!</b>\n\n"
                f"Доступ разрешен. Вступайте в чат соседей по ссылке:\n"
                f"{invite_url}\n\n"
                f"Ссылка одноразовая и действительна только для вас.",
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_message(
                telegram_id,
                "✅ <b>Ваша заявка одобрена!</b>\n\n"
                "Обратитесь к администратору для получения доступа в группу.",
                parse_mode=ParseMode.HTML
            )
        
        # Обновляем сообщение админа
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ <b>ОДОБРЕНО</b>",
            parse_mode=ParseMode.HTML
        )
        await callback.answer("✅ Пользователь одобрен", show_alert=True)
        
        logger.info(f"Пользователь {telegram_id} одобрен админом")
        
    except Exception as e:
        logger.error(f"Ошибка при одобрении пользователя: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_user(callback: CallbackQuery, bot: Bot):
    """Обработка отклонения пользователя."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для выполнения этого действия", show_alert=True)
        return
    
    telegram_id = int(callback.data.split("_")[1])
    
    try:
        # Обновляем статус в БД
        await update_user_status(telegram_id, "rejected")
        
        # Отправляем уведомление пользователю
        await bot.send_message(
            telegram_id,
            "❌ <b>Ваша заявка отклонена</b>\n\n"
            "Проверьте данные и попробуйте зарегистрироваться заново командой /start.\n"
            "Если вы считаете, что это ошибка, обратитесь к администратору.",
            parse_mode=ParseMode.HTML
        )
        
        # Обновляем сообщение админа
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ <b>ОТКЛОНЕНО</b>",
            parse_mode=ParseMode.HTML
        )
        await callback.answer("❌ Заявка отклонена", show_alert=True)
        
        logger.info(f"Пользователь {telegram_id} отклонен админом")
        
    except Exception as e:
        logger.error(f"Ошибка при отклонении пользователя: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)

