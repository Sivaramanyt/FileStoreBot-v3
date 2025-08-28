from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message
from database import db
from utils.helpers import create_premium_keyboard
from config import Config

@Client.on_callback_query(filters.regex("buy_premium"))
async def handle_premium_purchase(client: Client, callback: CallbackQuery):
    premium_text = f"""
💎 **Premium Membership**

**🌟 Premium Benefits:**
• ✅ Unlimited file access
• ✅ No verification required
• ✅ No ads or waiting
• ✅ Priority support
• ✅ Faster downloads

**💰 Pricing:**
• Monthly: ₹99
• Yearly: ₹999 (Save ₹189!)

**📱 Payment Methods:**
• UPI ID: `{Config.PREMIUM_UPI_ID}`
• QR Code available below

**📞 Support:** Contact @YourSupportBot after payment
    """
    
    keyboard = create_premium_keyboard()
    await callback.edit_message_text(premium_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("pay_upi"))
async def show_upi_payment(client: Client, callback: CallbackQuery):
    upi_text = f"""
💳 **UPI Payment**

**📱 Pay using any UPI app:**

**UPI ID:** `{Config.PREMIUM_UPI_ID}`

**Steps:**
1. Open any UPI app (GPay, PhonePe, Paytm, etc.)
2. Send money to the above UPI ID
3. Send payment screenshot to @YourSupportBot
4. Your premium will be activated within 24 hours

**💰 Amount:** ₹99 (Monthly) or ₹999 (Yearly)
    """
    
    await callback.edit_message_text(upi_text, reply_markup=create_premium_keyboard())

@Client.on_callback_query(filters.regex("show_qr"))
async def show_qr_payment(client: Client, callback: CallbackQuery):
    await callback.answer("Sending QR Code...")
    
    qr_text = f"""
📱 **Scan QR Code to Pay**

**📱 Scan with any UPI app:**
• Google Pay
• PhonePe
• Paytm
• Any UPI app

**💰 Amount:** ₹99 (Monthly) or ₹999 (Yearly)

**After payment:** Send screenshot to @YourSupportBot
    """
    
    try:
        await client.send_photo(
            callback.message.chat.id,
            Config.PREMIUM_QR_URL,
            caption=qr_text,
            reply_markup=create_premium_keyboard()
        )
    except:
        await callback.edit_message_text(
            f"QR Code: {Config.PREMIUM_QR_URL}\n\n{qr_text}",
            reply_markup=create_premium_keyboard()
  )
      
