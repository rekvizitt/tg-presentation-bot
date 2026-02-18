from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text("hello world")


if __name__ == "__main__":
    # Замените 'TOKEN' на ваш токен от @BotFather
    app = ApplicationBuilder().token("YOUR_TOKEN_HERE").build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
