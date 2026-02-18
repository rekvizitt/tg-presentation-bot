import asyncio
import configparser
import os

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.presentation import UserPresentation

# Загрузка настроек
config = configparser.ConfigParser()
config.read("settings.ini")
TOKEN = config["BOT"]["Token"]

# Состояния диалога
THEME, SLIDES = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога"""
    await update.message.reply_text(
        "Привет! Я помогу тебе создать презентацию.\n"
        "Для начала, напиши тему будущей презентации:"
    )
    return THEME


async def get_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем тему и спрашиваем количество слайдов"""
    theme = update.message.text
    if len(theme) < 3:
        await update.message.reply_text("Тема слишком короткая. Попробуй еще раз:")
        return THEME

    context.user_data["theme"] = theme
    await update.message.reply_text(
        f"Отлично! Тема: '{theme}'.\nТеперь напиши количество слайдов (от 1 до 15):"
    )
    return SLIDES


async def get_slides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем количество слайдов и запускаем генерацию"""
    slides_input = update.message.text

    # Валидация числа слайдов
    if not slides_input.isdigit():
        await update.message.reply_text("Пожалуйста, введи именно число (например, 5):")
        return SLIDES

    count = int(slides_input)
    if not (1 <= count <= 15):
        await update.message.reply_text(
            "Количество слайдов должно быть от 1 до 15. Попробуй еще раз:"
        )
        return SLIDES

    theme = context.user_data["theme"]
    user_id = update.message.from_user.id
    file_path = f"presentation_{user_id}.pptx"

    status_message = await update.message.reply_text(
        "⏳ Начинаю магию... Генерирую контент и создаю файл. Подожди немного..."
    )

    try:
        # Запуск генерации из вашего класса UserPresentation
        pres_gen = UserPresentation(theme, count)
        await pres_gen.create_presentation(file_path)

        # Отправка готового файла
        await update.message.reply_document(
            document=open(file_path, "rb"),
            filename=f"{theme}.pptx",
            caption="Вот твоя готовая презентация! 🎉",
        )
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при генерации: {e}")
    finally:
        # Удаляем файл после отправки, чтобы не засорять диск
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_message.delete()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Прерывание диалога"""
    await update.message.reply_text(
        "Генерация отменена.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Настройка обработчика диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            THEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_theme)],
            SLIDES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_slides)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен...")
    app.run_polling()
