"""Обработчик команды /start."""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging

from states import RegistrationStates
from database import get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    user = await get_user_by_telegram_id(message.from_user.id)
    
    if user:
        if user["status"] == "approved":
            await message.answer(
                "✅ Вы уже зарегистрированы и одобрены!\n"
                "Если у вас есть вопросы, обратитесь к администратору."
            )
        elif user["status"] == "pending":
            await message.answer(
                "⏳ Ваша заявка находится на рассмотрении.\n"
                "Ожидайте решения администратора."
            )
        elif user["status"] == "rejected":
            await message.answer(
                "❌ Ваша предыдущая заявка была отклонена.\n"
                "Вы можете начать регистрацию заново, отправив /start"
            )
            # Сбрасываем состояние и начинаем заново
            await state.set_state(RegistrationStates.waiting_for_full_name)
            await message.answer(
                "👋 Добро пожаловать!\n\n"
                "Для регистрации в закрытой группе соседей необходимо пройти верификацию.\n\n"
                "Пожалуйста, введите ваше ФИО (полностью):"
            )
        return
    
    # Новый пользователь
    await state.set_state(RegistrationStates.waiting_for_full_name)
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Для регистрации в закрытой группе соседей необходимо пройти верификацию.\n\n"
        "Пожалуйста, введите ваше ФИО (полностью):"
    )
    logger.info(f"Начата регистрация для пользователя {message.from_user.id}")

