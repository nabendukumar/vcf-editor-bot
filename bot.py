import os
import zipfile
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("8772077518:AAHk8hzSBU1vh-rVogeFnjLKWsPj5HxAwh0")

menu = [
    ["Edit VCF", "Split VCF"],
    ["Merge VCF", "Make VCF"],
]

markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

user_files = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 VCF Editor Bot\n\nSelect a feature:",
        reply_markup=markup
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_files[update.effective_user.id] = {"mode": text}

    if text == "Edit VCF":
        await update.message.reply_text("Send VCF file to rename contacts.")

    elif text == "Split VCF":
        await update.message.reply_text("Send VCF file to split.")

    elif text == "Merge VCF":
        await update.message.reply_text("Send multiple VCF files then type /done")

    elif text == "Make VCF":
        await update.message.reply_text("Send TXT file with numbers.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    mode = user_files.get(user_id, {}).get("mode")

    doc = update.message.document
    file = await doc.get_file()
    filename = doc.file_name

    await file.download_to_drive(filename)

    # EDIT VCF
    if mode == "Edit VCF":

        with open(filename) as f:
            data = f.read()

        contacts = data.split("END:VCARD")

        new_contacts = []
        count = 1

        for c in contacts:
            if "BEGIN:VCARD" in c:

                name = f"Lucifer{count:03d}"
                lines = c.splitlines()
                new = []

                for line in lines:
                    if line.startswith("FN:"):
                        new.append(f"FN:{name}")
                    else:
                        new.append(line)

                new_contacts.append("\n".join(new) + "\nEND:VCARD\n")
                count += 1

        with open("edited.vcf","w") as f:
            f.writelines(new_contacts)

        await update.message.reply_document(document=open("edited.vcf","rb"))

    # SPLIT VCF
    elif mode == "Split VCF":

        with open(filename) as f:
            data = f.read()

        contacts = [c+"END:VCARD\n" for c in data.split("END:VCARD") if "BEGIN:VCARD" in c]

        size = 500
        files = []

        for i in range(0,len(contacts),size):

            part = contacts[i:i+size]
            name = f"part_{i//size+1}.vcf"

            with open(name,"w") as f:
                f.writelines(part)

            files.append(name)

        for f in files:
            await update.message.reply_document(document=open(f,"rb"))

    # MAKE VCF
    elif mode == "Make VCF":

        with open(filename) as f:
            numbers = f.read().splitlines()

        cards = []
        count = 1

        for n in numbers:

            name = f"Contact{count:03d}"

            card = f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
TEL:{n}
END:VCARD
"""

            cards.append(card)
            count += 1

        with open("made.vcf","w") as f:
            f.writelines(cards)

        await update.message.reply_document(document=open("made.vcf","rb"))

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_files.get(user_id, {}).get("mode") != "Merge VCF":
        return

    files = [f for f in os.listdir() if f.endswith(".vcf")]

    merged = []

    for file in files:
        with open(file) as f:
            merged.append(f.read())

    with open("merged.vcf","w") as f:
        f.write("\n".join(merged))

    await update.message.reply_document(document=open("merged.vcf","rb"))

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main() 
