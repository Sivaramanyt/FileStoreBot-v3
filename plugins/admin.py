from pyrogram import Client, filters
from pyrogram.types import Message
from database import db
from config import Config
import asyncio

def is_admin(user_id):
    return user_id in Config.ADMINS

@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    
    total_users = await db.get_users_count()
    
    stats_text = f"""
📊 **Bot Statistics**

👥 **Users:** {total_users}
🤖 **Bot:** Online ✅
🗄️ **Database:** Connected ✅

**📈 More stats coming soon...**
    """
    
    await message.reply_text(stats_text)

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    
    if message.reply_to_message is None:
        await message.reply_text("""
📢 **Broadcast Message**

**Usage:** Reply to a message with /broadcast

**Example:**
1. Send the message you want to broadcast
2. Reply to it with /broadcast
        """)
        return
    
    users = await db.get_all_users()
    broadcast_msg = message.reply_to_message
    
    success = 0
    failed = 0
    
    status_msg = await message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    for user_id in users:
        try:
            if broadcast_msg.text:
                await client.send_message(user_id, broadcast_msg.text)
            elif broadcast_msg.photo:
                await client.send_photo(user_id, broadcast_msg.photo.file_id, caption=broadcast_msg.caption)
            elif broadcast_msg.video:
                await client.send_video(user_id, broadcast_msg.video.file_id, caption=broadcast_msg.caption)
            elif broadcast_msg.document:
                await client.send_document(user_id, broadcast_msg.document.file_id, caption=broadcast_msg.caption)
            
            success += 1
        except:
            failed += 1
        
        # Update status every 100 users
        if (success + failed) % 100 == 0:
            await status_msg.edit_text(f"""
📢 **Broadcasting...**

✅ **Success:** {success}
❌ **Failed:** {failed}
⏳ **Remaining:** {len(users) - success - failed}
            """)
            await asyncio.sleep(1)  # Rate limiting
    
    await status_msg.edit_text(f"""
📢 **Broadcast Complete!**

✅ **Success:** {success}
❌ **Failed:** {failed}
👥 **Total:** {len(users)}
    """)

@Client.on_message(filters.command("reset_verification") & filters.private)
async def reset_verification_command(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    
    if len(message.command) < 2:
        await message.reply_text("""
🔄 **Reset User Verification**

**Usage:** /reset_verification <user_id>

**Example:** /reset_verification 123456789
        """)
        return
    
    try:
        user_id = int(message.command[1])
        await db.reset_user_verification(user_id)
        await message.reply_text(f"✅ Verification reset for user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID!")

@Client.on_message(filters.command("premium") & filters.private)
async def premium_command(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return
    
    if len(message.command) < 2:
        await message.reply_text("""
💎 **Premium Management**

**Grant Premium:** /premium <user_id> grant
**Remove Premium:** /premium <user_id> remove

**Example:** /premium 123456789 grant
        """)
        return
    
    try:
        user_id = int(message.command[1])
        action = message.command[2].lower() if len(message.command) > 2 else ""
        
        if action == "grant":
            await db.update_user(user_id, {"is_premium": True})
            await message.reply_text(f"✅ Premium granted to user {user_id}")
        elif action == "remove":
            await db.update_user(user_id, {"is_premium": False})
            await message.reply_text(f"❌ Premium removed from user {user_id}")
        else:
            await message.reply_text("❌ Invalid action! Use 'grant' or 'remove'")
            
    except (ValueError, IndexError):
        await message.reply_text("❌ Invalid command format!")
      
