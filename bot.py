import os
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8772077518:AAEIlu2vgGE4tlZAKmtqGxwymIP_OcjaaGc"

user_state = {}
user_data = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✏️ Edit VCF", callback_data="edit")],
        [InlineKeyboardButton("✂️ Split VCF", callback_data="split")],
        [InlineKeyboardButton("⚙️ Advanced VCF Editor", callback_data="advanced")]
    ]

    await update.message.reply_text(
        "👋 Welcome to VCF Bot\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= BUTTON HANDLER =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    await query.message.delete()

    # EDIT
    if query.data == "edit":
        user_state[chat_id] = "EDIT_WAIT_FILE"
        user_data[chat_id] = {}
        await context.bot.send_message(chat_id, "📂 Send VCF file")

    # SPLIT
    elif query.data == "split":
        user_state[chat_id] = "SPLIT_WAIT_FILE"
        user_data[chat_id] = {}
        await context.bot.send_message(chat_id, "📂 Send VCF file for splitting")

    # ADVANCED MENU
    elif query.data == "advanced":
        user_state[chat_id] = "ADV_MENU"

        keyboard = [
            [InlineKeyboardButton("🔗 Merge VCF", callback_data="adv_merge")]
        ]

        await context.bot.send_message(
            chat_id,
            "⚙️ Advanced VCF Editor",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # MERGE START
    elif query.data == "adv_merge":
        user_state[chat_id] = "ADV_MERGE"
        user_data[chat_id] = {"files": []}
        await context.bot.send_message(chat_id, "📁 Send VCF files to merge")

    # MERGE DONE
    elif query.data == "adv_merge_done":

        files = user_data.get(chat_id, {}).get("files", [])

        if not files:
            await context.bot.send_message(chat_id, "❌ No files uploaded")
            return

        merged = ""

        for f in files:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file:
                    merged += file.read() + "\n"
            except:
                pass

        if not merged.strip():
            await context.bot.send_message(chat_id, "❌ Empty files")
            return

        bio = io.BytesIO(merged.encode("utf-8"))
        bio.name = f"merged_{chat_id}.vcf"

        await context.bot.send_document(chat_id, document=bio)
        await context.bot.send_message(chat_id, "✅ Merge Completed!")

        # cleanup
        for f in files:
            try:
                os.remove(f)
            except:
                pass

        user_state[chat_id] = None
        user_data[chat_id] = {}

# ================= FILE HANDLER =================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()

    # EDIT FLOW
    if user_state.get(chat_id) == "EDIT_WAIT_FILE":
        user_data[chat_id] = {
            "vcf": file_bytes.decode("utf-8", errors="ignore")
        }
        user_state[chat_id] = "EDIT_WAIT_NAME"
        await update.message.reply_text("📛 Send base file name")
        return

    # SPLIT FLOW
    if user_state.get(chat_id) == "SPLIT_WAIT_FILE":
        path = f"split_{chat_id}.vcf"

        await file.download_to_drive(path)

        user_state[chat_id] = "SPLIT_WAIT_FILENAME"
        await update.message.reply_text("📛 Send base file name")
        return

    # ADV MERGE FILES
    if user_state.get(chat_id) == "ADV_MERGE":

        path = f"merge_{chat_id}_{len(user_data[chat_id]['files'])}.vcf"

        await file.download_to_drive(path)
        user_data[chat_id]["files"].append(path)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Done", callback_data="adv_merge_done")]
        ])

        await update.message.reply_text("📁 File received", reply_markup=keyboard)
        return

# ================= TEXT HANDLER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    state = user_state.get(chat_id)

    if not state:
        return

    # ================= EDIT =================
    if state == "EDIT_WAIT_NAME":
        user_data[chat_id]["basename"] = text
        user_state[chat_id] = "EDIT_WAIT_CONTACT"
        await update.message.reply_text("👤 Send base contact name (e.g. luci01)")
        return

    if state == "EDIT_WAIT_CONTACT":

        base = text
        vcf = user_data[chat_id]["vcf"]

        lines = vcf.splitlines()
        new_lines = []
        counter = 1

        for line in lines:
            if line.startswith("FN:"):
                new_lines.append(f"FN:{base}{counter:02d}")
                counter += 1
            elif line.startswith("N:"):
                new_lines.append(f"N:{base};;;;")
            else:
                new_lines.append(line)

        result = "\n".join(new_lines)

        bio = io.BytesIO(result.encode("utf-8"))
        bio.name = f"{user_data[chat_id]['basename']}.vcf"

        await update.message.reply_document(document=bio)

        user_state[chat_id] = None
        user_data[chat_id] = {}
        return

    # ================= SPLIT =================
    if state == "SPLIT_WAIT_FILENAME":
        user_data[chat_id] = {"filename": text}
        user_state[chat_id] = "SPLIT_WAIT_COUNT"
        await update.message.reply_text("🔢 How many contacts per file?")
        return

    if state == "SPLIT_WAIT_COUNT":
        try:
            count = int(text)
        except:
            await update.message.reply_text("❌ Send number only")
            return

        user_data[chat_id]["count"] = count
        user_state[chat_id] = "SPLIT_WAIT_CONTACT"
        await update.message.reply_text("👤 Send base contact name")
        return

    if state == "SPLIT_WAIT_CONTACT":

        base = text
        file_name = user_data[chat_id]["filename"]
        chunk_size = user_data[chat_id]["count"]

        with open(f"split_{chat_id}.vcf", "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()

        contacts = data.split("END:VCARD")
        counter = 1

        for i in range(0, len(contacts), chunk_size):
            chunk = contacts[i:i+chunk_size]
            new_vcf = ""

            for c in chunk:
                if c.strip():

                    name = f"{base}{counter:02d}"

                    lines = c.splitlines()
                    temp = []

                    for line in lines:
                        if line.startswith("FN:"):
                            temp.append(f"FN:{name}")
                        elif line.startswith("N:"):
                            temp.append(f"N:{name};;;;")
                        else:
                            temp.append(line)

                    new_vcf += "\n".join(temp) + "\nEND:VCARD\n"
                    counter += 1

            out = f"{file_name}_{i//chunk_size + 1}.vcf"

            with open(out, "w", encoding="utf-8") as f:
                f.write(new_vcf)

            await update.message.reply_document(document=open(out, "rb"))

        await update.message.reply_text("✅ Split Done")
        user_state[chat_id] = None
        return

# ================= MAIN =================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("BOT STARTED...")
    app.run_polling()

if __name__ == "__main__":
    main()