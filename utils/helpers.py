from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import base64
import secrets
import string
from datetime import datetime, timedelta

def get_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def encode_file_id(file_id):
    """Encode file ID for URL sharing"""
    return base64.urlsafe_b64encode(file_id.encode()).decode().rstrip('=')

def decode_file_id(encoded_id):
    """Decode file ID from URL"""
    # Add padding if necessary
    padding = 4 - len(encoded_id) % 4
    if padding != 4:
        encoded_id += '=' * padding
    return base64.urlsafe_b64decode(encoded_id).decode()

def generate_verification_token():
    """Generate a random verification token"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def get_verification_expiry_text():
    """Get formatted expiry time text"""
    return f"{Config.VERIFICATION_VALIDITY_HOURS} hours"

def get_time_remaining(created_at):
    """Get remaining time for verification in human readable format"""
    expiry_time = created_at + timedelta(hours=Config.VERIFICATION_VALIDITY_HOURS)
    remaining = expiry_time - datetime.now()
    
    if remaining.total_seconds() <= 0:
        return "Expired"
    
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m remaining"
    else:
        return f"{minutes}m remaining"

def get_start_keyboard():
    """Get start command keyboard"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Upload Files", callback_data="help_upload")],
        [InlineKeyboardButton("💎 Get Premium", callback_data="premium_info"),
         InlineKeyboardButton("ℹ️ Help", callback_data="help_main")],
        [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/your_channel")]
    ])
    return keyboard

def get_premium_keyboard():
    """Create premium purchase keyboard"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Pay Now", callback_data="show_payment")],
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ])
    return keyboard

def get_payment_keyboard():
    """Create payment keyboard"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Payment Done", callback_data="payment_done")],
        [InlineKeyboardButton("🔙 Back", callback_data="premium_info")]
    ])
    return keyboard

def get_admin_keyboard():
    """Create admin panel keyboard"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🔗 Change Shortlink", callback_data="change_shortlink")],
        [InlineKeyboardButton("🔄 Reset User", callback_data="reset_user")]
    ])
    return keyboard
    
