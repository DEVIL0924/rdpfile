from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
import os, zipfile, subprocess, shutil, time

BOT_TOKEN = "8259774690:AAEz5zHmwz6CfFodxRk621kZFFFIPp1f668"
OWNER_ID = 7521375632     # apna Telegram user id yaha daalna
ROOT_DIR = "/root"

def auth(update):
    return update.effective_user.id == OWNER_ID

def unique(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    return f"{base}_{i}{ext}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    await update.message.reply_text("☁️ ROOT CLOUD DRIVE READY")

async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    files = os.listdir(ROOT_DIR)
    text = "\n".join(files) if files else "Empty"
    await update.message.reply_text(f"📂 /root\n{text}")

async def mkdir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    name = " ".join(context.args)
    if not name:
        return await update.message.reply_text("Usage: /mkdir foldername")
    os.makedirs(os.path.join(ROOT_DIR,name), exist_ok=True)
    await update.message.reply_text("📁 Folder created")

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    name = " ".join(context.args)
    path = os.path.join(ROOT_DIR,name)
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    await update.message.reply_text("🗑 Deleted")

async def unzip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    name = " ".join(context.args)
    path = os.path.join(ROOT_DIR,name)
    if path.endswith(".zip"):
        zipfile.ZipFile(path).extractall(ROOT_DIR)
        os.remove(path)
        await update.message.reply_text("📦 ZIP Extracted")

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not auth(update): return
    msg = update.message

    if msg.document:
        file = await msg.document.get_file()
        name = msg.document.file_name
        dest = unique(os.path.join(ROOT_DIR,name))
        await msg.reply_text("⬇️ Downloading...")
        await file.download_to_drive(dest)

        if dest.endswith(".zip"):
            zipfile.ZipFile(dest).extractall(ROOT_DIR)
            os.remove(dest)
            await msg.reply_text("📦 ZIP Extracted")
        elif dest.endswith(".rar"):
            subprocess.call(["unrar","x",dest,ROOT_DIR])
            os.remove(dest)
            await msg.reply_text("📦 RAR Extracted")
        elif dest.endswith(".7z"):
            subprocess.call(["7z","x",dest,f"-o{ROOT_DIR}"])
            os.remove(dest)
            await msg.reply_text("📦 7Z Extracted")
        else:
            await msg.reply_text(f"✅ Saved: {os.path.basename(dest)}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ls", ls))
app.add_handler(CommandHandler("mkdir", mkdir))
app.add_handler(CommandHandler("rm", rm))
app.add_handler(CommandHandler("unzip", unzip_cmd))
app.add_handler(MessageHandler(filters.ALL, upload))
app.run_polling()
