import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# BOT_TOKEN will be taken from Render Environment Variable
TOKEN = os.getenv("BOT_TOKEN")

# Menu buttons
menu = [
    ["Edit VCF", "Split VCF"],
    ["Merge VCF", "Make VCF"],
]

markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

# Store user mode and files
user_data = {}

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 VCF Editor Bot\nSelect a feature from the menu below:",
        reply_markup=markup
    )

# MENU HANDLER
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data[update.effective_user.id] = {"mode": text}
    
    if text == "Edit VCF":
        await update.message.reply_text("Send your VCF file to rename contacts (Lucifer01, Lucifer02...).")
    elif text == "Split VCF":
        await update.message.reply_text("Send your VCF file to split into smaller files.")
    elif text == "Merge VCF":
        await update.message.reply_text("Send multiple VCF files. After sending all, type /done to merge.")
    elif text == "Make VCF":
        await update.message.reply_text("Send a TXT file containing phone numbers (one per line).")

# HANDLE FILES
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mode = user_data.get(user_id, {}).get("mode")
    
    if not mode:
        await update.message.reply_text("Please select a feature first using the menu.")
        return

    document = update.message.document
    file = await document.get_file()
    filename = document.file_name
    await file.download_to_drive(filename)

    # --- EDIT VCF ---
    if mode == "Edit VCF":
        with open(filename, "r", encoding="utf-8") as f:
            data = f.read()
        contacts = data.split("END:VCARD")
        new_contacts = []
        count = 1
        for c in contacts:
            if "BEGIN:VCARD" in c:
                name = f"Lucifer{count:03d}"
                lines = c.splitlines()
                new_lines = []
                for line in lines:
                    if line.startswith("FN:"):
                        new_lines.append(f"FN:{name}")
                    else:
                        new_lines.append(line)
                new_contacts.append("\n".join(new_lines) + "\nEND:VCARD\n")
                count += 1
        output_file = "edited.vcf"
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(new_contacts)
        await update.message.reply_document(document=open(output_file, "rb"))

    # --- SPLIT VCF ---
    elif mode == "Split VCF":
        with open(filename, "r", encoding="utf-8") as f:
            data = f.read()
        contacts = [c+"END:VCARD\n" for c in data.split("END:VCARD") if "BEGIN:VCARD" in c]
        chunk_size = 500
        files = []
        for i in range(0, len(contacts), chunk_size):
            part = contacts[i:i+chunk_size]
            part_name = f"part_{i//chunk_size+1}.vcf"
            with open(part_name, "w", encoding="utf-8") as f:
                f.writelines(part)
            files.append(part_name)
        for f_name in files:
            await update.message.reply_document(document=open(f_name, "rb"))

    # --- MAKE VCF ---
    elif mode == "Make VCF":
        with open(filename, "r", encoding="utf-8") as f:
            numbers = f.read().splitlines()
        cards = []
        for i, n in enumerate(numbers, 1):
            card = f"""BEGIN:VCARD
VERSION:3.0
FN:Contact{i:03d}
TEL:{n}
END:VCARD
"""
            cards.append(card)
        output_file = "made.vcf"
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(cards)
        await update.message.reply_document(document=open(output_file, "rb"))

# --- MERGE VCF (triggered by /done) ---
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_data.get(user_id, {}).get("mode") != "Merge VCF":
        return
    files = [f for f in os.listdir() if f.endswith(".vcf")]
    merged_content = []
    for f_name in files:
        with open(f_name, "r", encoding="utf-8") as f:
            merged_content.append(f.read())
    output_file = "merged.vcf"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(merged_content))
    await update.message.reply_document(document=open(output_file, "rb"))

# --- MAIN ---
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
