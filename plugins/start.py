from pyrogram import Client, filters
from pyrogram.types import Message
from database import db
from utils.helpers import get_start_keyboard
from config import Config

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Add user to database
    await db.add_user(user_id, username)
    
    # Check if user is accessing a file
    if len(message.command) > 1:
        file_id = message.command[1]
        await handle_file_access(client, message, file_id)
        return
    
    start_text = f"""
🔥 **Welcome to File Store Bot!** 🔥

Hi {message.from_user.mention}! 👋

**🌟 What I can do:**
• 📁 Store your files permanently
• 🔗 Generate shareable links
• 💎 Premium features available
• 🔐 Secure file access

**📋 How to use:**
1. Send me any file/video
2. Get permanent sharing link
3. Share with anyone!

**🎯 Note:** First 3 files are free, then verification required or buy premium!

**👑 Premium Benefits:**
• No verification needed
• Unlimited file access
• Priority support
    """
    
    await message.reply_text(
        start_text,
        reply_markup=get_start_keyboard()
    )

async def handle_file_access(client: Client, message: Message, file_id: str):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await db.add_user(user_id, message.from_user.username)
        user = await db.get_user(user_id)
    
    # Check if user is premium
    if user.get("is_premium", False):
        await send_file_to_user(client, message, file_id)
        return
    
    # Check file access count
    files_accessed = user.get("files_accessed", 0)
    
    if files_accessed < Config.FREE_FILE_LIMIT:
        # User can access file for free
        await db.update_user(user_id, {"files_accessed": files_accessed + 1})
        await send_file_to_user(client, message, file_id)
    else:
        # User needs verification
        from plugins.verification import handle_verification_required
        await handle_verification_required(client, message, file_id)

async def send_file_to_user(client: Client, message: Message, file_id: str):
    try:
        # In a real implementation, you'd retrieve the file from database
        # and forward it to the user
        await message.reply_text("🎉 Here's your file!")
        # await client.send_document(message.chat.id, file_id)
    except Exception as e:
        await message.reply_text("❌ File not found or expired!")
  
