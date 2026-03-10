from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8772077518:AAG-iTTaDQWPR3zGxjw7Y8PZgE-dBkDnQuk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to VCF Editor Bot\n\nSend your VCF file."
    )

async def handle_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    await file.download_to_drive("input.vcf")

    with open("input.vcf") as f:
        data = f.read()

    contacts = data.split("END:VCARD")

    new_contacts = []
    count = 1

    for c in contacts:
        if "BEGIN:VCARD" in c:
            name = f"Lucifer{count:02d}"
            c = c.replace("FN:", f"FN:{name}")
            new_contacts.append(c + "END:VCARD\n")
            count += 1

    with open("output.vcf","w") as f:
        f.writelines(new_contacts)

    await update.message.reply_document(document=open("output.vcf","rb"))

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.FileExtension("vcf"), handle_vcf))

print("Bot running...")
app.run_polling()
