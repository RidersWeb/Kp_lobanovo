"""Обработчики процесса регистрации."""
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, Contact, ReplyKeyboardMarkup, KeyboardButton, 
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.enums import ParseMode
import logging

from states import RegistrationStates
from database import create_user
from config import is_admin, ADMIN_IDS
from security import (
    validate_full_name, validate_phone, validate_plot_number,
    validate_file_extension, validate_file_size, normalize_phone,
    sanitize_text
)

logger = logging.getLogger(__name__)
router = Router()


@router.message(StateFilter(RegistrationStates.waiting_for_full_name))
async def process_full_name(message: Message, state: FSMContext):
    """Обработка ввода ФИО."""
    full_name = message.text.strip()
    
    # Валидация и санитизация ФИО
    is_valid, error_msg = validate_full_name(full_name)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Санитизация текста
    full_name = sanitize_text(full_name, max_length=200)
    
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationStates.waiting_for_phone)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="📱 Отправить номер телефона",
                request_contact=True
            )
        ]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"✅ ФИО сохранено: {full_name}\n\n"
        "Теперь отправьте ваш номер телефона:",
        reply_markup=keyboard
    )
    logger.info(f"Пользователь {message.from_user.id} ввел ФИО: {full_name}")


@router.message(StateFilter(RegistrationStates.waiting_for_phone), F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Обработка отправки контакта."""
    contact: Contact = message.contact
    
    # Проверяем, что контакт принадлежит отправителю
    if contact.user_id != message.from_user.id:
        await message.answer(
            "❌ Пожалуйста, отправьте свой собственный номер телефона."
        )
        return
    
    phone = contact.phone_number
    
    # Нормализуем и валидируем телефон
    phone = normalize_phone(phone)
    is_valid, error_msg = validate_phone(phone)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.waiting_for_plot_number)
    
    await message.answer(
        f"✅ Номер телефона сохранен: {phone}\n\n"
        "Теперь введите номер вашего участка:",
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info(f"Пользователь {message.from_user.id} отправил телефон: {phone}")


@router.message(StateFilter(RegistrationStates.waiting_for_phone))
async def process_phone_text(message: Message, state: FSMContext):
    """Обработка текстового ввода телефона (если не использована кнопка)."""
    phone = message.text.strip()
    
    # Нормализуем и валидируем телефон
    phone = normalize_phone(phone)
    is_valid, error_msg = validate_phone(phone)
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n"
            "Пожалуйста, используйте кнопку 'Отправить номер телефона' или введите номер в формате +7XXXXXXXXXX"
        )
        return
    
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.waiting_for_plot_number)
    
    await message.answer(
        f"✅ Номер телефона сохранен: {phone}\n\n"
        "Теперь введите номер вашего участка:",
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info(f"Пользователь {message.from_user.id} ввел телефон текстом: {phone}")


@router.message(StateFilter(RegistrationStates.waiting_for_plot_number))
async def process_plot_number(message: Message, state: FSMContext):
    """Обработка ввода номера участка."""
    plot_number = message.text.strip()
    
    # Валидация номера участка
    is_valid, error_msg = validate_plot_number(plot_number)
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Санитизация текста
    plot_number = sanitize_text(plot_number, max_length=50)
    
    await state.update_data(plot_number=plot_number)
    await state.set_state(RegistrationStates.waiting_for_document)
    
    await message.answer(
        f"✅ Номер участка сохранен: {plot_number}\n\n"
        "Теперь отправьте фото или документ первого листа выписки из ЕГРН (или другого документа, подтверждающего право собственности):"
    )
    logger.info(f"Пользователь {message.from_user.id} ввел номер участка: {plot_number}")


@router.message(StateFilter(RegistrationStates.waiting_for_document), F.photo | F.document)
async def process_document(message: Message, state: FSMContext, bot: Bot):
    """Обработка загрузки документа."""
    file_id = None
    filename = None
    file_size = None
    is_document = False
    
    if message.photo:
        # Берем фото наибольшего размера
        file_id = message.photo[-1].file_id
        file_size = message.photo[-1].file_size
        filename = "photo.jpg"  # Для фото имя не критично
    elif message.document:
        file_id = message.document.file_id
        filename = message.document.file_name
        file_size = message.document.file_size
        is_document = True
    
    if not file_id:
        await message.answer(
            "❌ Не удалось получить файл. Пожалуйста, отправьте фото или документ еще раз:"
        )
        return
    
    # Валидация расширения файла
    if filename:
        is_valid, error_msg = validate_file_extension(filename, is_document=is_document)
        if not is_valid:
            await message.answer(f"❌ {error_msg}")
            return
    
    # Валидация размера файла
    if file_size:
        is_valid, error_msg = validate_file_size(file_size)
        if not is_valid:
            await message.answer(f"❌ {error_msg}")
            return
    
    # Получаем все данные из состояния
    data = await state.get_data()
    full_name = data.get("full_name")
    phone = data.get("phone")
    plot_number = data.get("plot_number")
    
    if not all([full_name, phone, plot_number]):
        await message.answer(
            "❌ Произошла ошибка. Пожалуйста, начните регистрацию заново командой /start"
        )
        await state.clear()
        return
    
    # Сохраняем пользователя в БД
    try:
        user_id = await create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=full_name,
            phone=phone,
            plot_number=plot_number,
            document_file_id=file_id
        )
        
        # Отправляем уведомление админу
        admin_text = (
            "🔔 <b>Новая заявка на регистрацию</b>\n\n"
            f"<b>ФИО:</b> {full_name}\n"
            f"<b>Телефон:</b> {phone}\n"
            f"<b>Участок:</b> {plot_number}\n"
            f"<b>Telegram ID:</b> {message.from_user.id}\n"
            f"<b>Username:</b> @{message.from_user.username or 'не указан'}\n"
            f"<b>ID заявки:</b> {user_id}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=f"approve_{message.from_user.id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"reject_{message.from_user.id}"
            )
        ]])
        
        # Отправляем текст и документ отдельно для лучшей читаемости всем админам
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    admin_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                
                # Отправляем документ/фото админу
                if message.photo:
                    await bot.send_photo(admin_id, file_id, caption="Документ пользователя")
                else:
                    await bot.send_document(admin_id, file_id, caption="Документ пользователя")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения админу {admin_id}: {e}")
        
        await state.clear()
        await message.answer(
            "✅ Спасибо! Ваша заявка отправлена на рассмотрение администратору.\n\n"
            "Ожидайте решения. Вы получите уведомление, когда администратор рассмотрит вашу заявку."
        )
        
        logger.info(f"Заявка пользователя {message.from_user.id} отправлена админу")
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже или обратитесь к администратору."
        )


@router.message(StateFilter(RegistrationStates.waiting_for_document))
async def process_document_invalid(message: Message):
    """Обработка некорректного типа сообщения вместо документа."""
    await message.answer(
        "❌ Пожалуйста, отправьте фото или документ (PDF, изображение).\n"
        "Текстовые сообщения не принимаются на этом этапе."
    )

