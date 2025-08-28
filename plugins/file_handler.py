from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from utils.helpers import format_file_size, generate_verification_token
from utils.shortlink import shortlink_generator
from config import Config
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def handle_file_upload(client: Client, message: Message):
    if message.chat.type != "private":
        return
    
    user_id = message.from_user.id
    
    # Get file info
    if message.document:
        file = message.document
        file_type = "document"
    elif message.video:
        file = message.video
        file_type = "video"
    elif message.audio:
        file = message.audio
        file_type = "audio"
    elif message.photo:
        file = message.photo
        file_type = "photo"
    else:
        return

    # Save file to database
    file_unique_id = await db.save_file(
        file_id=file.file_id,
        file_name=getattr(file, 'file_name', f'{file_type}_{file.file_id}'),
        file_size=getattr(file, 'file_size', 0),
        mime_type=getattr(file, 'mime_type', 'unknown'),
        uploaded_by=user_id
    )
    
    # Generate sharing link
    bot_username = (await client.get_me()).username
    sharing_link = f"https://t.me/{bot_username}?start={file_unique_id}"
    
    # Generate shortlink
    short_link = await shortlink_generator.generate_shortlink(sharing_link)
    
    file_info = f"""
📁 **File Uploaded Successfully!**

**📋 File Details:**
• **Name:** {getattr(file, 'file_name', 'Unknown')}
• **Size:** {format_file_size(getattr(file, 'file_size', 0))}
• **Type:** {file_type.upper()}

**🔗 Sharing Links:**
• **Direct Link:** `{sharing_link}`
• **Short Link:** `{short_link}`

**💡 Share these links with anyone to give them access to your file!**
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Copy Short Link", url=short_link)],
        [InlineKeyboardButton("📤 Share Link", switch_inline_query=short_link)]
    ])
    
    await message.reply_text(file_info, reply_markup=keyboard)
  
