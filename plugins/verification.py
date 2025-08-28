from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from database import db
from utils.helpers import generate_verification_token, create_verification_keyboard
from utils.shortlink import shortlink_generator
from config import Config
import logging

logger = logging.getLogger(__name__)

async def handle_verification_required(client: Client, message: Message, file_id: str):
    user_id = message.from_user.id
    
    # Generate verification token
    verification_token = generate_verification_token()
    
    # Save verification to database
    await db.add_verification(user_id, verification_token)
    
    # Create verification link
    bot_username = (await client.get_me()).username
    verification_link = f"https://t.me/{bot_username}?start=verify_{verification_token}"
    
    # Generate shortlink for verification
    short_verification_link = await shortlink_generator.generate_shortlink(verification_link)
    
    verification_text = f"""
🔐 **Verification Required!**

You've reached your free file limit ({Config.FREE_FILE_LIMIT} files).

**To access this file:**
1. Click the verification button below
2. Complete the quick verification process
3. Return here to get your file

**⏰ Verification valid for {Config.VERIFICATION_VALIDITY_HOURS} hours**

**💎 Or upgrade to Premium for unlimited access!**
    """
    
    keyboard = create_verification_keyboard(short_verification_link)
    await message.reply_text(verification_text, reply_markup=keyboard)

@Client.on_message(filters.command("start") & filters.regex(r"verify_"))
async def handle_verification(client: Client, message: Message):
    user_id = message.from_user.id
    token = message.command[1].replace("verify_", "")
    
    # Verify token
    is_valid = await db.verify_token(user_id, token)
    
    if is_valid:
        # Reset user's file access count
        await db.update_user(user_id, {
            "files_accessed": 0,
            "last_verification": datetime.now()
        })
        
        await message.reply_text("""
✅ **Verification Successful!**

🎉 You can now access files again!
Your free file counter has been reset.

Thank you for completing the verification! 🙏
        """)
    else:
        await message.reply_text("""
❌ **Verification Failed!**

The verification link is either:
• Invalid
• Expired (older than 6 hours)
• Already used

Please request a new verification link.
        """)
      
