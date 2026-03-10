# bot.py
import os
import asyncio
import pandas as pd
import vobject
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")

# START command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running! ✅")

# Example: echo command
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"You said: {text}")

# Example: handle VCF file
async def handle_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        file = await update.message.document.get_file()
        file_path = f"downloads/{update.message.document.file_name}"
        os.makedirs("downloads", exist_ok=True)
        await file.download_to_drive(file_path)
        await update.message.reply_text(f"VCF saved at {file_path}")
        # Example: parse VCF
        with open(file_path, "r") as f:
            vcard = vobject.readOne(f.read())
        await update.message.reply_text(f"Parsed contact: {vcard.fn.value}")

# Example: handle Excel
async def handle_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        file = await update.message.document.get_file()
        file_path = f"downloads/{update.message.document.file_name}"
        os.makedirs("downloads", exist_ok=True)
        await file.download_to_drive(file_path)
        df = pd.read_excel(file_path)
        await update.message.reply_text(f"Excel rows: {len(df)}")

# Main bot
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_handler(MessageHandler(filters.Document.FileExtension("vcf"), handle_vcf))
    app.add_handler(MessageHandler(filters.Document.FileExtension("xlsx"), handle_excel))

    # Start bot
    await app.start()
    print("Bot started successfully ✅")
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
