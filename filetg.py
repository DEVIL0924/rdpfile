#!/usr/bin/env python3
"""
Telegram File Storage Bot - Fixed Version
Direct RDP file storage with version management
"""

import os
import sys
import logging
import json
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Telegram Bot imports
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters
    )
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-telegram-bot --quiet")
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters
    )

# ============ CONFIGURATION ============
BOT_TOKEN = "8476220678:AAFQ_QbaqGKo_KexouiuT-6e-SZMjuMmZ2k"
ADMIN_ID = 7521375632  # Your User ID
BASE_PATH = "./telegram_storage"  # RDP Storage Path
# ========================================

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure storage directory exists
Path(BASE_PATH).mkdir(parents=True, exist_ok=True)

class FileStorageBot:
    def __init__(self):
        self.base_path = Path(BASE_PATH)
        self.file_categories = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf', '.odt'],
            'code': ['.py', '.js', '.java', '.cpp', '.c', '.html', '.css', '.php'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'data': ['.json', '.csv', '.xml', '.xlsx', '.sql'],
            'other': []
        }
    
    def get_category(self, filename: str) -> str:
        """Get category based on file extension"""
        ext = Path(filename).suffix.lower()
        for category, extensions in self.file_categories.items():
            if ext in extensions:
                return category
        return 'other'
    
    def get_next_version(self, project: str) -> str:
        """Get next version number for project"""
        project_path = self.base_path / project
        
        if not project_path.exists():
            return "v1.0"
        
        versions = []
        for item in project_path.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                try:
                    # Extract version number (remove 'v' and convert to float)
                    ver_num = float(item.name[1:])
                    versions.append(ver_num)
                except ValueError:
                    continue
        
        if not versions:
            return "v1.0"
        
        latest = max(versions)
        next_ver = latest + 0.1
        return f"v{next_ver:.1f}"
    
    def create_project(self, project_name: str) -> bool:
        """Create new project folder"""
        project_path = self.base_path / project_name
        
        if project_path.exists():
            return False
        
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create project info file
        info = {
            "name": project_name,
            "created": datetime.now().isoformat(),
            "owner": ADMIN_ID,
            "total_versions": 0,
            "total_files": 0,
            "versions": []
        }
        
        with open(project_path / "project_info.json", "w") as f:
            json.dump(info, f, indent=2)
        
        return True
    
    def list_projects(self) -> List[str]:
        """List all projects"""
        projects = []
        for item in self.base_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                projects.append(item.name)
        return sorted(projects)
    
    def get_project_info(self, project_name: str) -> Optional[Dict]:
        """Get project information"""
        info_file = self.base_path / project_name / "project_info.json"
        
        if not info_file.exists():
            return None
        
        with open(info_file, "r") as f:
            return json.load(f)
    
    def save_file(self, project: str, filename: str, file_bytes: bytes) -> str:
        """Save uploaded file with versioning"""
        # Get or create version
        version = self.get_next_version(project)
        version_path = self.base_path / project / version
        version_path.mkdir(parents=True, exist_ok=True)
        
        # Determine category and save
        category = self.get_category(filename)
        category_path = version_path / category
        category_path.mkdir(exist_ok=True)
        
        # Save file
        file_path = category_path / filename
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        # Update project info
        self.update_project_info(project, version, filename)
        
        return str(file_path)
    
    def update_project_info(self, project: str, version: str, filename: str):
        """Update project information after file upload"""
        info_file = self.base_path / project / "project_info.json"
        
        if info_file.exists():
            with open(info_file, "r") as f:
                info = json.load(f)
        else:
            info = {
                "name": project,
                "created": datetime.now().isoformat(),
                "versions": [],
                "total_files": 0
            }
        
        # Add version if not exists
        if version not in info["versions"]:
            info["versions"].append(version)
        
        # Count total files
        total_files = 0
        project_path = self.base_path / project
        for file in project_path.rglob("*"):
            if file.is_file():
                total_files += 1
        
        info["total_files"] = total_files
        info["last_updated"] = datetime.now().isoformat()
        
        with open(info_file, "w") as f:
            json.dump(info, f, indent=2)

# Create bot instance
storage_bot = FileStorageBot()

# ============ TELEGRAM HANDLERS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized access!")
        return
    
    welcome_msg = f"""
<b>🤖 Welcome {user.first_name}! 🤖</b>

<b>📁 RDP File Storage Bot 📁</b>

<b>Your ID:</b> <code>{user.id}</code>
<b>Storage Path:</b> <code>{BASE_PATH}</code>

<b>Commands:</b>
/start - Show this message
/new <project_name> - Create new project
/projects - List all projects
/upload - Upload files
/info <project> - Project info
/clean - Cleanup temporary files
/space - Check storage space

<b>How to use:</b>
1. Create project: /new MyProject
2. Upload files: /upload
3. Files auto-saved with versioning
"""
    
    await update.message.reply_text(welcome_msg, parse_mode='HTML')

async def new_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /new command to create project"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /new <project_name>")
        return
    
    project_name = "_".join(context.args)
    
    if storage_bot.create_project(project_name):
        project_path = storage_bot.base_path / project_name
        await update.message.reply_text(
            f"✅ <b>Project Created!</b>\n\n"
            f"<b>Name:</b> <code>{project_name}</code>\n"
            f"<b>Path:</b> <code>{project_path}</code>\n"
            f"<b>First Version:</b> <code>v1.0</code>\n\n"
            f"Now upload files with /upload",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(f"❌ Project '{project_name}' already exists!")

async def list_projects_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /projects command"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    projects = storage_bot.list_projects()
    
    if not projects:
        await update.message.reply_text("📭 No projects found. Create one with /new")
        return
    
    projects_text = "<b>📂 Your Projects:</b>\n\n"
    for project in projects:
        info = storage_bot.get_project_info(project)
        if info:
            version_count = len(info.get("versions", []))
            file_count = info.get("total_files", 0)
            projects_text += f"• <b>{project}</b> - {version_count} versions, {file_count} files\n"
        else:
            projects_text += f"• <b>{project}</b>\n"
    
    await update.message.reply_text(projects_text, parse_mode='HTML')

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload command"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    projects = storage_bot.list_projects()
    
    if not projects:
        await update.message.reply_text(
            "📭 No projects found!\n"
            "First create project: /new <project_name>"
        )
        return
    
    # Create project selection keyboard
    keyboard = []
    row = []
    for i, project in enumerate(projects):
        row.append(InlineKeyboardButton(f"📁 {project}", callback_data=f"proj_{project}"))
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📤 <b>Select project for upload:</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def project_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project selection callback"""
    query = update.callback_query
    await query.answer()
    
    project_name = query.data.replace("proj_", "")
    context.user_data['upload_project'] = project_name
    
    await query.edit_message_text(
        f"✅ <b>Selected:</b> <code>{project_name}</code>\n\n"
        f"📤 Now send me files (images, documents, videos, etc.)\n"
        f"📁 Auto-saved with versioning\n"
        f"📊 Auto-categorized by file type"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming files"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    if 'upload_project' not in context.user_data:
        await update.message.reply_text("❌ First select project with /upload")
        return
    
    project = context.user_data['upload_project']
    
    # Get file from message
    if update.message.document:
        file_obj = await update.message.document.get_file()
        filename = update.message.document.file_name
        file_type = "document"
    elif update.message.photo:
        file_obj = await update.message.photo[-1].get_file()
        filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        file_type = "photo"
    elif update.message.video:
        file_obj = await update.message.video.get_file()
        filename = update.message.video.file_name or f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        file_type = "video"
    elif update.message.audio:
        file_obj = await update.message.audio.get_file()
        filename = update.message.audio.file_name or f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        file_type = "audio"
    else:
        await update.message.reply_text("❌ Unsupported file type!")
        return
    
    # Download file
    try:
        file_bytes = await file_obj.download_as_bytearray()
    except Exception as e:
        logger.error(f"Download error: {e}")
        await update.message.reply_text("❌ File download failed!")
        return
    
    # Save file to storage
    try:
        saved_path = storage_bot.save_file(project, filename, bytes(file_bytes))
        
        # Get file info
        file_size = len(file_bytes)
        size_str = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/(1024*1024):.1f} MB"
        
        category = storage_bot.get_category(filename)
        
        # Get current version
        version = storage_bot.get_next_version(project)
        
        await update.message.reply_text(
            f"✅ <b>File Saved Successfully!</b>\n\n"
            f"📁 <b>Project:</b> <code>{project}</code>\n"
            f"🔖 <b>Version:</b> <code>{version}</code>\n"
            f"📄 <b>File:</b> <code>{filename}</code>\n"
            f"📂 <b>Category:</b> <code>{category}</code>\n"
            f"📊 <b>Type:</b> <code>{file_type}</code>\n"
            f"💾 <b>Size:</b> <code>{size_str}</code>\n"
            f"📍 <b>Path:</b> <code>{saved_path}</code>",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Save error: {e}")
        await update.message.reply_text(f"❌ Save failed: {str(e)}")

async def project_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /info <project_name>")
        return
    
    project = "_".join(context.args)
    info = storage_bot.get_project_info(project)
    
    if not info:
        await update.message.reply_text(f"❌ Project '{project}' not found!")
        return
    
    # Calculate folder size
    project_path = storage_bot.base_path / project
    total_size = 0
    for file_path in project_path.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    size_mb = total_size / (1024 * 1024)
    
    info_text = f"""
<b>📊 Project Info:</b> <code>{project}</code>

<b>📅 Created:</b> <code>{info.get('created', 'N/A')}</code>
<b>🔢 Versions:</b> <code>{len(info.get('versions', []))}</code>
<b>📄 Total Files:</b> <code>{info.get('total_files', 0)}</code>
<b>💾 Size:</b> <code>{size_mb:.2f} MB</code>

<b>Versions:</b>
"""
    
    for ver in sorted(info.get('versions', [])):
        ver_path = project_path / ver
        ver_files = len([f for f in ver_path.rglob("*") if f.is_file()])
        info_text += f"\n• <code>{ver}</code> - {ver_files} files"
    
    await update.message.reply_text(info_text, parse_mode='HTML')

async def storage_space(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /space command"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    total_size = 0
    total_files = 0
    total_projects = 0
    
    for project in storage_bot.base_path.iterdir():
        if project.is_dir() and not project.name.startswith("."):
            total_projects += 1
            for file_path in project.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    total_files += 1
    
    # Get disk info
    total, used, free = shutil.disk_usage("/")
    
    space_text = f"""
<b>💽 Storage Information</b>

<b>📦 Projects:</b> <code>{total_projects}</code>
<b>📄 Files:</b> <code>{total_files}</code>
<b>📊 Bot Storage:</b> <code>{total_size/(1024*1024):.2f} MB</code>

<b>Disk Space:</b>
<b>💾 Total:</b> <code>{total/(1024**3):.2f} GB</code>
<b>📈 Used:</b> <code>{used/(1024**3):.2f} GB</code>
<b>📉 Free:</b> <code>{free/(1024**3):.2f} GB</code>
<b>📍 Path:</b> <code>{BASE_PATH}</code>
"""
    
    await update.message.reply_text(space_text, parse_mode='HTML')

async def cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clean command"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    # Clean temp files and empty folders
    cleaned = 0
    for temp_file in Path(".").glob("*.tmp"):
        temp_file.unlink()
        cleaned += 1
    
    await update.message.reply_text(f"🧹 Cleaned {cleaned} temporary files")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all projects"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    projects = storage_bot.list_projects()
    
    status = f"""
<b>📢 Bot Status Report</b>

✅ Bot is running
<b>📁 Total Projects:</b> {len(projects)}
<b>💾 Storage:</b> {BASE_PATH}
<b>🕐 Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await update.message.reply_text(status, parse_mode='HTML')

# ============ MAIN FUNCTION ============

def main():
    """Main function to run the bot"""
    print("\n" + "="*50)
    print("🤖 TELEGRAM FILE STORAGE BOT")
    print("="*50)
    print(f"👤 Admin ID: {ADMIN_ID}")
    print(f"📁 Storage Path: {BASE_PATH}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    # Check if storage path exists
    storage_bot.base_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Storage initialized: {storage_bot.base_path}")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("new", new_project))
    application.add_handler(CommandHandler("projects", list_projects_cmd))
    application.add_handler(CommandHandler("upload", upload_command))
    application.add_handler(CommandHandler("info", project_info))
    application.add_handler(CommandHandler("space", storage_space))
    application.add_handler(CommandHandler("clean", cleanup))
    application.add_handler(CommandHandler("status", broadcast))
    
    # Add callback handler
    application.add_handler(CallbackQueryHandler(project_selected, pattern="^proj_"))
    
    # Add file handler
    application.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO,
        handle_file
    ))
    
    # Start bot
    print("🚀 Starting bot...")
    print("📱 Open Telegram and send /start to your bot")
    print("⏳ Bot is now running (Press Ctrl+C to stop)")
    
    try:
        # Run bot with polling
        application.run_polling(
            poll_interval=3,
            timeout=30,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Direct execution without any setup
    main()
