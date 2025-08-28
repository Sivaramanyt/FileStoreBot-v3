import os
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, FloodWait
from config import Config
from database import db
from utils.shortlink import shortlink
from utils.helpers import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Health check server for Koyeb
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is healthy!')
    
    def log_message(self, format, *args):
        pass  # Disable logging

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"✅ Health server started on port {port}")
    server.serve_forever()

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

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def handle_file_upload(client, message: Message):
    user_id = message.from_user.id
    
    # Check if user exists in database
    user = await db.get_user(user_id)
    if not user:
        await db.add_user(user_id, message.from_user.username, message.from_user.first_name)
    
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
    
    file_name = getattr(file, 'file_name', f'{file_type}_{file.file_id}')
    file_size = getattr(file, 'file_size', 0)
    
    # Store file in database
    await db.store_file(file.file_id, file_name, file_size, file_type, message.id)
    
    # Create sharing link
    encoded_file_id = encode_file_id(file.file_id)
    bot_username = (await client.get_me()).username
    share_link = f"https://t.me/{bot_username}?start={encoded_file_id}"
    
    # Generate shortlink
    short_link = await shortlink.create_short_link(share_link)
    
    response_text = f"""
📁 **File Uploaded Successfully!**

**📋 File Details:**
• **Name:** `{file_name}`
• **Size:** `{get_file_size(file_size)}`
• **Type:** `{file_type.title()}`

**🔗 Sharing Links:**
• **Direct Link:** `{share_link}`
• **Short Link:** `{short_link}`

**💡 Share these links with anyone to give them access to your file!**
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Copy Short Link", url=short_link)],
        [InlineKeyboardButton("💎 Get Premium", callback_data="premium_info")]
    ])
    
    await message.reply_text(response_text, reply_markup=keyboard)

@app.on_callback_query()
async def callback_handler(client, callback_query: CallbackQuery):
    """Handle all callback queries from inline keyboards"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        if data == "help_upload":
            await callback_query.edit_message_text(
                """
📁 **How to Upload Files**

**Steps:**
1. Send me any file/video/document
2. I'll store it permanently 
3. You'll get a sharing link
4. Share the link with anyone!

**Supported files:**
• Videos (MP4, AVI, MKV, etc.)
• Documents (PDF, DOC, TXT, etc.) 
• Images (JPG, PNG, GIF, etc.)
• Audio files (MP3, WAV, etc.)

**File size limit:** Up to 2GB per file
                """,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="start")
                ]])
            )
        
        elif data == "premium_info":
            user = await db.get_user(user_id)
            if user and user.get("is_premium"):
                text = "✅ **You are already a Premium user!**\n\nEnjoy unlimited file access without verification!"
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="start")]])
            else:
                text = f"""
💎 **Premium Features**

✅ **Unlimited file access**
✅ **No verification required** 
✅ **No ads or waiting**
✅ **Priority support**
✅ **Faster downloads**

**Price:** ₹{Config.PREMIUM_PRICE} only!

**Payment Method:** Google Pay UPI
                """
                keyboard = get_premium_keyboard()
            
            await callback_query.edit_message_text(text, reply_markup=keyboard)
        
        elif data == "show_payment":
            text = f"""
💳 **Payment Information**

**Amount:** ₹{Config.PREMIUM_PRICE}
**UPI ID:** `{Config.PREMIUM_UPI_ID}`

**Steps:**
1. Pay ₹{Config.PREMIUM_PRICE} to above UPI ID
2. Take screenshot of payment
3. Click "Payment Done" below  
4. Send screenshot to admin for verification

**QR Code will be sent below:**
            """
            
            keyboard = get_payment_keyboard()
            
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            
            # Send QR code
            try:
                await client.send_photo(
                    callback_query.message.chat.id,
                    Config.PREMIUM_QR_URL,
                    caption="**Scan this QR code to pay**"
                )
            except:
                pass
        
        elif data == "payment_done":
            text = f"""
✅ **Payment Process Started**

Please send your payment screenshot to the admin for verification.

**Contact Admin:** Send screenshot here and mention your user ID: `{user_id}`

After verification, you'll get premium access instantly!
            """
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="premium_info")]])
            await callback_query.edit_message_text(text, reply_markup=keyboard)
        
        elif data == "help_main":
            text = """
ℹ️ **Help & Support**

**Commands:**
• `/start` - Start the bot
• Upload any file to get sharing link

**How it works:**
1. Upload files → Get permanent links
2. First 3 files are free
3. After that, verification required
4. Premium users get unlimited access

**Need help?**
Contact: @YourSupportUsername
            """
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="start")]])
            await callback_query.edit_message_text(text, reply_markup=keyboard)
        
        elif data == "start":
            # Back to start message
            welcome_text = f"""
🎉 **Welcome to File Store Bot!** 

👋 Hello {callback_query.from_user.first_name}!

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
            
            await callback_query.edit_message_text(welcome_text, reply_markup=get_start_keyboard())
        
        # Admin callbacks
        elif data == "bot_stats" and user_id == Config.OWNER_ID:
            total_users = await db.get_total_users()
            text = f"""
📊 **Bot Statistics**

👥 Total Users: {total_users}
📁 Total Files: {await db.files.count_documents({})}
💎 Premium Users: {await db.users.count_documents({"is_premium": True})}
            """
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
            await callback_query.edit_message_text(text, reply_markup=keyboard)
        
        elif data == "broadcast" and user_id == Config.OWNER_ID:
            text = "📢 **Broadcast Message**\n\nSend the message you want to broadcast to all users:"
            broadcast_message[user_id] = True
            await callback_query.edit_message_text(text)
        
        elif data == "change_shortlink" and user_id == Config.OWNER_ID:
            text = """
🔗 **Change Shortlink Service**

Send the new shortlink URL and API key in this format:
`URL API_KEY`

Example:
`https://gplinks.in 1234567890abcdef`
            """
            waiting_for_shortlink[user_id] = True
            await callback_query.edit_message_text(text)
        
        # Always answer the callback query
        await callback_query.answer()
        
    except Exception as e:
        print(f"Callback error: {e}")
        await callback_query.answer("❌ Something went wrong! Try again.", show_alert=True)

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

async def send_file_with_verification(client, message: Message, file_id: str):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await db.add_user(user_id, message.from_user.username, message.from_user.first_name)
        user = await db.get_user(user_id)
    
    # Check if user is premium
    if user.get("is_premium", False):
        await send_file_directly(client, message, file_id)
        return
    
    # Check force subscription
    if not await check_force_subscription(client, user_id):
        await send_force_sub_message(client, message)
        return
    
    # Check free limit
    files_accessed = user.get("files_accessed", 0)
    
    if files_accessed < Config.FREE_LIMIT:
        # Send file directly for free users under limit
        await send_file_directly(client, message, file_id)
        await db.update_user_access(user_id)
    else:
        # Send verification link
        await send_verification_link(client, message, file_id)

async def send_file_directly(client, message: Message, file_id: str):
    try:
        # Get file from database
        file_data = await db.get_file(file_id)
        if not file_data:
            await message.reply_text("❌ File not found or expired!")
            return
        
        # Forward the file
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=file_data["message_id"]
        )
        
        # Send file info
        info_text = f"""
📁 **File Information**

**Name:** `{file_data['file_name']}`
**Size:** `{get_file_size(file_data['file_size'])}`
**Type:** `{file_data['file_type'].title()}`
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Get Premium", callback_data="premium_info")]
        ])
        
        await message.reply_text(info_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await message.reply_text("❌ Error occurred while sending file!")

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

async def check_force_subscription(client, user_id):
    try:
        for channel_id in Config.FORCE_SUB_CHANNELS:
            if channel_id.strip():
                try:
                    member = await client.get_chat_member(channel_id, user_id)
                    if member.status in ["left", "kicked"]:
                        return False
                except UserNotParticipant:
                    return False
        return True
    except:
        return True

async def send_force_sub_message(client, message: Message):
    text = "🔒 **Please join our channel(s) to use this bot:**"
    buttons = []
    
    for i, channel_id in enumerate(Config.FORCE_SUB_CHANNELS):
        if channel_id.strip():
            try:
                chat = await client.get_chat(channel_id)
                buttons.append([InlineKeyboardButton(f"Join {chat.title}", url=f"https://t.me/{chat.username}")])
            except:
                pass
    
    buttons.append([InlineKeyboardButton("✅ Check Subscription", callback_data="check_sub")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    await message.reply_text(text, reply_markup=keyboard)

@app.on_message(filters.command("admin"))
async def admin_panel(client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        await message.reply_text("❌ You are not authorized to use this command!")
        return
    
    text = """
🔧 **Admin Panel**

Welcome to the admin panel. Choose an option:
    """
    
    await message.reply_text(text, reply_markup=get_admin_keyboard())

@app.on_message(filters.command("reset"))
async def reset_user_command(client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        await message.reply_text("❌ You are not authorized to use this command!")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: /reset <user_id>")
        return
    
    try:
        user_id = int(message.command[1])
        await db.reset_user_verification(user_id)
        await message.reply_text(f"✅ User {user_id} verification reset successfully!")
    except ValueError:
        await message.reply_text("❌ Invalid user ID!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@app.on_message(filters.command("premium"))
async def make_premium_command(client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        await message.reply_text("❌ You are not authorized to use this command!")
        return
    
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: /premium <user_id>")
        return
    
    try:
        user_id = int(message.command[1])
        await db.make_premium(user_id)
        await message.reply_text(f"✅ User {user_id} is now premium!")
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                "🎉 **Congratulations!**\n\nYou are now a Premium user!\nEnjoy unlimited file access without verification."
            )
        except:
            pass
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID!")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@app.on_message(filters.command("stats"))
async def stats_command(client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        await message.reply_text("❌ You are not authorized to use this command!")
        return
    
    total_users = await db.get_total_users()
    total_files = await db.files.count_documents({})
    premium_users = await db.users.count_documents({"is_premium": True})
    
    text = f"""
📊 **Detailed Bot Statistics**

👥 **Users:**
├ Total Users: {total_users}
├ Premium Users: {premium_users}
└ Free Users: {total_users - premium_users}

📁 **Files:**
└ Total Files Stored: {total_files}

💎 **Premium Rate:**
└ {round((premium_users/total_users)*100, 2) if total_users > 0 else 0}%
    """
    
    await message.reply_text(text)

@app.on_message(filters.text & filters.private & ~filters.command(["start", "admin", "reset", "premium", "stats"]))
async def handle_text_messages(client, message: Message):
    user_id = message.from_user.id
    
    # Handle broadcast message
    if user_id in broadcast_message and broadcast_message[user_id]:
        if user_id != Config.OWNER_ID:
            return
        
        broadcast_message[user_id] = False
        users = await db.get_all_users()
        
        success = 0
        failed = 0
        
        status_message = await message.reply_text("📢 Broadcasting message...")
        
        for user in users:
            try:
                await client.send_message(user, message.text)
                success += 1
                await asyncio.sleep(0.1)  # Avoid flood wait
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await client.send_message(user, message.text)
                    success += 1
                except:
                    failed += 1
            except:
                failed += 1
        
        await status_message.edit_text(
            f"📢 **Broadcast Completed**\n\n✅ Success: {success}\n❌ Failed: {failed}"
        )
    
    # Handle shortlink change
    elif user_id in waiting_for_shortlink and waiting_for_shortlink[user_id]:
        if user_id != Config.OWNER_ID:
            return
        
        waiting_for_shortlink[user_id] = False
        
        try:
            parts = message.text.strip().split(' ', 1)
            if len(parts) != 2:
                await message.reply_text("❌ Invalid format! Use: URL API_KEY")
                return
            
            url, api_key = parts
            await db.update_shortlink(url, api_key)
            
            await message.reply_text(
                f"✅ **Shortlink Updated Successfully!**\n\n**URL:** `{url}`\n**API Key:** `{api_key}`"
            )
        except Exception as e:
            await message.reply_text(f"❌ Error updating shortlink: {e}")

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

if __name__ == "__main__":
    print("🚀 Starting File Store Bot...")
    
    # Start health server in background for Koyeb
    threading.Thread(target=start_health_server, daemon=True).start()
    
    # Start the cleanup task in background
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_expired_tokens_task())
    
    # Start bot
    app.run()
                                          
