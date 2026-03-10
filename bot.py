# bot.py
import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Bot token from environment variable
TOKEN = os.getenv("BOT_TOKEN")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running! ✅")

# Example echo handler for messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"You said: {text}")

# Add your VCF editor features here as async functions
# Example:
# async def my_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     ...

async def main():
    # Create the app
    app = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Add your custom feature handlers here
    # app.add_handler(CommandHandler("mycmd", my_feature))

    # Start the bot using run_polling()
    print("Bot starting...")
    await app.run_polling()  # handles start + idle internally

if __name__ == "__main__":
    asyncio.run(main())
