import os
import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import db
from utils.shortlink import shortlink
from utils.helpers import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is healthy!')
    
    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health server started on port {port}")
    server.serve_forever()

app = Client(
    "FileStoreBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    await db.add_user(user_id, message.from_user.username, first_name)
    
    if len(message.command) > 1:
        param = message.command[1]
        if param.startswith("verify_"):
            token = param.replace("verify_", "")
            await handle_verification(client, message, token)
            return
        else:
            try:
                file_unique_id = decode_file_id(param)
                await send_file_with_verification(client, message, file_unique_id)
                return
            except:
                pass
    
    welcome_text = f"🎉 Welcome to File Store Bot!\n\nHello {first_name}!\n\nSend me any file to get a sharing link!"
    await message.reply_text(welcome_text, reply_markup=get_start_keyboard())

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def handle_file_upload(client, message: Message):
    user_id = message.from_user.id
    
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
    
    try:
        forwarded_msg = await client.copy_message(
            chat_id=Config.STORAGE_CHANNEL_ID,
            from_chat_id=message.chat.id,
            message_id=message.id
        )
        
        file_unique_id = await db.store_file(
            file.file_id, file_name, file_size, file_type, 
            forwarded_msg.id, Config.STORAGE_CHANNEL_ID
        )
        
        encoded_file_id = encode_file_id(file_unique_id)
        bot_username = (await client.get_me()).username
        share_link = f"https://t.me/{bot_username}?start={encoded_file_id}"
        short_link = await shortlink.create_short_link(share_link)
        
        response_text = f"📁 File uploaded!\n\nName: {file_name}\nSize: {get_file_size(file_size)}\n\nLink: {short_link}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Copy Link", url=short_link)]
        ])
        
        await message.reply_text(response_text, reply_markup=keyboard)
        
    except Exception as e:
        await message.reply_text("❌ Upload failed!")

async def handle_verification(client, message, token):
    await message.reply_text("Verification feature coming soon!")

async def send_file_with_verification(client, message, file_unique_id):
    try:
        file_data = await db.get_file(file_unique_id)
        if file_data:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=file_data["channel_id"],
                message_id=file_data["message_id"]
            )
            await message.reply_text("✅ File sent!")
        else:
            await message.reply_text("❌ File not found!")
    except:
        await message.reply_text("❌ Error sending file!")

if __name__ == "__main__":
    print("🚀 Starting File Store Bot...")
    threading.Thread(target=start_health_server, daemon=True).start()
    app.run()
    
