import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, FloodWait
from config import Config
from database import db
from shortlink import shortlink
from helpers import *
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot
app = Client(
    "FileStoreBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Global variables for admin operations
broadcast_message = {}
waiting_for_shortlink = {}

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Add user to database
    await db.add_user(user_id, username, first_name)
    
    # Check if it's a verification token
    if len(message.command) > 1:
        param = message.command[1]
        
        if param.startswith("verify_"):
            # Handle verification
            token = param.replace("verify_", "")
            await handle_verification(client, message, token)
            return
        else:
            # Handle file request
            try:
                file_id = decode_file_id(param)
                await send_file_with_verification(client, message, file_id)
                return
            except:
                pass
    
    # Send welcome message
    welcome_text = f"""
🎉 **Welcome to File Store Bot!** 

👋 Hello {first_name}!

**Features:**
📂 Upload and store files permanently
🔗 Get instant sharing links
💎 Premium access available
🔒 Secure file storage

**How to use:**
1. Send me any file/video
2. Get permanent sharing link
3. Share with anyone!

**Free users:** First 3 files are free, then verification required
**Premium users:** Unlimited access without ads

⏰ **Verification validity:** 6 hours only!
    """
    
    await message.reply_text(
        welcome_text,
        reply_markup=get_start_keyboard()
    )

async def handle_verification(client, message: Message, token):
    """Handle verification token with expiry check"""
    user_id = message.from_user.id
    
    # Clean up expired tokens first
    await db.cleanup_expired_tokens()
    
    # Verify the token
    file_id = await db.verify_token(user_id, token)
    
    if file_id:
        # Token is valid and not expired
        await db.reset_user_verification(user_id)  # Reset user's file access count
        
        await message.reply_text(
            "✅ **Verification Successful!**\n\n"
            "🎉 Your verification is complete!\n"
            "📁 You can now access files again.\n"
            "🔄 Your free file counter has been reset to 0.\n\n"
            "Thank you for completing the verification! 🙏"
        )
        
        # Now send the requested file
        await send_file_directly(client, message, file_id)
        
    else:
        # Token is invalid, used, or expired
        await message.reply_text(
            "❌ **Verification Failed!**\n\n"
            "The verification link is either:\n"
            "• ⏰ **Expired** (older than 6 hours)\n"
            "• 🔄 **Already used**\n"
            "• ❌ **Invalid**\n\n"
            "📝 Please request a new file link to get a fresh verification."
        )

async def send_verification_link(client, message: Message, file_id: str):
    """Send verification link with 6-hour expiry information"""
    user_id = message.from_user.id
    
    # Generate verification token
    verification_token = generate_verification_token()
    
    # Store token in database with 6-hour expiry
    await db.create_verification_token(user_id, file_id, verification_token)
    
    # Create verification link
    verification_url = f"https://t.me/{(await client.get_me()).username}?start=verify_{verification_token}"
    short_link = await shortlink.create_short_link(verification_url)
    
    text = f"""
🔒 **Verification Required**

You have reached your free limit of {Config.FREE_LIMIT} files.

**To access this file:**
1. 🔗 Click the verification link below
2. ✅ Complete the verification process  
3. 🔄 Return here automatically to get your file

⏰ **Important:** This verification is valid for **6 hours only**!
⚡ **After 6 hours, you'll need to request the file again.**

🔗 **Verification Link:** 
{short_link}

💎 **Or get Premium for unlimited access without any verification!**
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔓 Verify Now", url=short_link)],
        [InlineKeyboardButton("💎 Get Premium", callback_data="premium_info")],
        [InlineKeyboardButton("⏰ Check Time Left", callback_data=f"check_time_{verification_token}")]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"check_time_"))
async def check_verification_time(client, callback_query: CallbackQuery):
    """Check remaining time for verification token"""
    token = callback_query.data.replace("check_time_", "")
    user_id = callback_query.from_user.id
    
    # Find the verification record
    verification = await db.verifications.find_one({
        "user_id": user_id,
        "token": token,
        "is_used": False
    })
    
    if verification:
        remaining_time = get_time_remaining(verification["created_at"])
        if remaining_time == "Expired":
            await callback_query.answer("❌ This verification has expired! Request a new file link.", show_alert=True)
        else:
            await callback_query.answer(f"⏰ Time remaining: {remaining_time}", show_alert=True)
    else:
        await callback_query.answer("❌ Verification not found or already used!", show_alert=True)

# Add periodic cleanup task for expired tokens
async def cleanup_expired_tokens_task():
    """Background task to clean expired verification tokens every hour"""
    while True:
        try:
            await db.cleanup_expired_tokens()
            logger.info("Cleaned up expired verification tokens")
        except Exception as e:
            logger.error(f"Error cleaning up tokens: {e}")
        
        # Wait for 1 hour
        await asyncio.sleep(3600)

# Rest of the code remains the same...
# (Include all other functions from the previous main.py)

if __name__ == "__main__":
    print("🚀 Starting File Store Bot...")
    
    # Start the cleanup task in background
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_expired_tokens_task())
    
    app.run()
  
