"""Модуль безопасности для валидации и санитизации данных."""
import re
import html
from typing import Optional, Tuple

# Максимальные длины полей
MAX_FULL_NAME_LENGTH = 200
MAX_PHONE_LENGTH = 20
MAX_PLOT_NUMBER_LENGTH = 50
MAX_QUERY_LENGTH = 100

# Разрешенные расширения файлов
ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}

# Максимальный размер файла (20 МБ)
MAX_FILE_SIZE = 20 * 1024 * 1024


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Санитизация текста: удаление опасных символов и экранирование HTML.
    
    Args:
        text: Текст для санитизации
        max_length: Максимальная длина текста
        
    Returns:
        Очищенный текст
    """
    if not text:
        return ""
    
    # Удаляем управляющие символы и невидимые символы
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Экранируем HTML для защиты от XSS
    text = html.escape(text)
    
    # Обрезаем до максимальной длины
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def validate_full_name(full_name: str) -> Tuple[bool, str]:
    """
    Валидация ФИО.
    
    Returns:
        (is_valid, error_message)
    """
    if not full_name or not full_name.strip():
        return False, "ФИО не может быть пустым"
    
    full_name = full_name.strip()
    
    if len(full_name) < 3:
        return False, "ФИО слишком короткое (минимум 3 символа)"
    
    if len(full_name) > MAX_FULL_NAME_LENGTH:
        return False, f"ФИО слишком длинное (максимум {MAX_FULL_NAME_LENGTH} символов)"
    
    # Проверяем, что ФИО содержит только буквы, пробелы, дефисы и апострофы
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-\']+$', full_name):
        return False, "ФИО может содержать только буквы, пробелы, дефисы и апострофы"
    
    return True, ""


def normalize_phone(phone: str) -> str:
    """
    Нормализация номера телефона: добавляет '+' если его нет.
    
    Args:
        phone: Номер телефона
        
    Returns:
        Нормализованный номер телефона
    """
    if not phone:
        return ""
    
    phone = phone.strip()
    
    # Удаляем все пробелы, дефисы, скобки
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Если номер не начинается с +, добавляем его
    if not phone.startswith('+'):
        # Если номер начинается с 8, заменяем на +7
        if phone.startswith('8') and len(phone) >= 11:
            phone = '+7' + phone[1:]
        elif phone.startswith('7') and len(phone) >= 11:
            phone = '+' + phone
        else:
            phone = '+' + phone
    
    return phone


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Валидация номера телефона.
    
    Returns:
        (is_valid, error_message)
    """
    if not phone or not phone.strip():
        return False, "Номер телефона не может быть пустым"
    
    phone = normalize_phone(phone)
    
    if len(phone) > MAX_PHONE_LENGTH:
        return False, f"Номер телефона слишком длинный (максимум {MAX_PHONE_LENGTH} символов)"
    
    # Проверяем формат: должен начинаться с + и содержать только цифры после +
    if not re.match(r'^\+\d{7,15}$', phone):
        return False, "Неверный формат номера телефона. Используйте формат: +7XXXXXXXXXX"
    
    return True, ""


def validate_plot_number(plot_number: str) -> Tuple[bool, str]:
    """
    Валидация номера участка.
    
    Returns:
        (is_valid, error_message)
    """
    if not plot_number or not plot_number.strip():
        return False, "Номер участка не может быть пустым"
    
    plot_number = plot_number.strip()
    
    if len(plot_number) > MAX_PLOT_NUMBER_LENGTH:
        return False, f"Номер участка слишком длинный (максимум {MAX_PLOT_NUMBER_LENGTH} символов)"
    
    # Проверяем, что номер участка содержит только допустимые символы
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ0-9:\-\.\s]+$', plot_number):
        return False, "Номер участка содержит недопустимые символы"
    
    return True, ""


def validate_file_extension(filename: Optional[str], is_document: bool = False) -> Tuple[bool, str]:
    """
    Валидация расширения файла.
    
    Args:
        filename: Имя файла
        is_document: True если это документ, False если фото
        
    Returns:
        (is_valid, error_message)
    """
    if not filename:
        return True, ""  # Если имя файла не указано, пропускаем проверку
    
    filename_lower = filename.lower()
    
    if is_document:
        allowed = ALLOWED_DOCUMENT_EXTENSIONS
        file_type = "документ"
    else:
        allowed = ALLOWED_PHOTO_EXTENSIONS
        file_type = "изображение"
    
    # Проверяем расширение
    if not any(filename_lower.endswith(ext) for ext in allowed):
        allowed_str = ', '.join(allowed)
        return False, f"Недопустимый формат {file_type}. Разрешенные форматы: {allowed_str}"
    
    return True, ""


def validate_file_size(file_size: Optional[int]) -> Tuple[bool, str]:
    """
    Валидация размера файла.
    
    Args:
        file_size: Размер файла в байтах
        
    Returns:
        (is_valid, error_message)
    """
    if file_size is None:
        return True, ""  # Если размер неизвестен, пропускаем проверку
    
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return False, f"Файл слишком большой. Максимальный размер: {max_mb} МБ"
    
    if file_size == 0:
        return False, "Файл пустой"
    
    return True, ""


def sanitize_search_query(query: str) -> Tuple[bool, str, str]:
    """
    Санитизация поискового запроса.
    
    Returns:
        (is_valid, error_message, sanitized_query)
    """
    if not query or not query.strip():
        return False, "Запрос не может быть пустым", ""
    
    query = query.strip()
    
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Запрос слишком длинный (максимум {MAX_QUERY_LENGTH} символов)", ""
    
    # Удаляем опасные символы, но оставляем буквы, цифры, пробелы и некоторые символы
    sanitized = re.sub(r'[^\w\s\-\+\(\):\.]', '', query)
    
    if not sanitized:
        return False, "Запрос содержит только недопустимые символы", ""
    
    return True, "", sanitized

