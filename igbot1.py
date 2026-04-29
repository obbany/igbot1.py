import logging
import instaloader
import pyotp
import asyncio
import ssl
import socket
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# ==================== আপনার টোকেন এখানে পরিবর্তন করুন ====================
# 👇👇👇 এই লাইনে আপনার নতুন টোকেন বসান 👇👇👇
BOT_TOKEN = "7801586678:AAGJbxj5kZGmSoizZLXshN6wplyS3GTlYKQ"
# 👆👆👆 টোকেন চেঞ্জ করতে এখানে নতুন টোকেন দিন 👆👆👆

# লগিং সাইলেন্ট
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.ERROR)

# স্টেটস
WAITING, USERNAME, PASSWORD, TFA = range(4)

# SSL ফিক্স
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

socket.setdefaulttimeout(30)

# ==================== কীবোর্ড ====================
def get_main_keyboard():
    keyboard = [[KeyboardButton("🍪 START COOKIE HUNTER 🍪")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def remove_keyboard():
    return ReplyKeyboardMarkup([[]], resize_keyboard=True)

# ==================== লগইন ফাংশন ====================
async def login_and_get_cookies(username, password, tfa_secret, status_msg):
    try:
        totp = pyotp.TOTP(tfa_secret.replace(" ", ""))
        L = instaloader.Instaloader(quiet=True)
        
        await status_msg.edit_text(f"🔐 Logging in: {username}")
        
        loop = asyncio.get_running_loop()
        
        try:
            await loop.run_in_executor(None, L.login, username, password)
        except instaloader.TwoFactorAuthRequiredException:
            await status_msg.edit_text("🔑 2FA verifying...")
            await loop.run_in_executor(None, L.two_factor_login, totp.now())
        
        cookies = L.context._session.cookies.get_dict()
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        
        return {"cookies": cookie_str, "username": username}, True
        
    except instaloader.exceptions.BadCredentialsException:
        return "Wrong username or password", False
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        return "2FA required - invalid code", False
    except instaloader.exceptions.ConnectionException:
        return "No internet connection", False
    except Exception as e:
        return f"Error: {str(e)[:50]}", False

# ==================== হ্যান্ডলার ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    
    msg = f"""🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪

✨ COOKIE HUNTER ✨

Hey {user}!

⚡ FAST & SECURE
- No Auto-Follow
- No Ads
- Instant Cookies

🎯 Press button below to start

🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪"""
    
    await update.message.reply_text(msg, reply_markup=get_main_keyboard())
    return WAITING

async def start_extractor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """📝 STEP 1/3 - USERNAME
━━━━━━━━━━━━━━━━━━

Send your Instagram username

Example: @john_doe""",
        reply_markup=remove_keyboard()
    )
    return USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().replace('@', '')
    context.user_data['username'] = username
    
    await update.message.reply_text(
        f"""🔐 STEP 2/3 - PASSWORD
━━━━━━━━━━━━━━━━━━

User: {username}

Send your password"""
    )
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text.strip()
    username = context.user_data['username']
    
    await update.message.reply_text(
        f"""🔢 STEP 3/3 - 2FA KEY
━━━━━━━━━━━━━━━━━━

User: {username}

Send your 2FA secret key

Example: JBSWY3DPEHPK3PXP"""
    )
    return TFA

async def get_tfa_and_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tfa_secret = update.message.text.strip()
    username = context.user_data.get('username')
    password = context.user_data.get('password')
    
    status_msg = await update.message.reply_text("⏳ Processing...")
    
    result, success = await login_and_get_cookies(username, password, tfa_secret, status_msg)
    
    try:
        await status_msg.delete()
    except:
        pass
    
    if success:
        cookies = result['cookies']
        if len(cookies) > 400:
            cookies = cookies[:400] + "..."
        
        await update.message.reply_text(
            f"""✅ SUCCESS ✅
━━━━━━━━━

User: {username}

🍪 COOKIE:
{cookies}

💡 Tap to copy
━━━━━━━━━

🔄 Press button to extract again""",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            f"""❌ FAILED ❌
━━━━━━━━━

{result}

💡 Tips:
- Check username/password
- Verify 2FA key
- Check internet

🔄 Press button to try again""",
            reply_markup=get_main_keyboard()
        )
    
    context.user_data.clear()
    return WAITING

# ==================== মেইন ====================
def main():
    print("\n" + "🍪" * 15)
    print("🍪 COOKIE HUNTER BOT 🍪")
    print("🍪" * 15)
    print("\n✅ BOT STARTING...")
    print(f"📌 Using Token: {BOT_TOKEN[:15]}...")
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                MessageHandler(filters.Regex('^🍪 START COOKIE HUNTER 🍪$'), start_extractor)
            ],
            states={
                WAITING: [
                    MessageHandler(filters.Regex('^🍪 START COOKIE HUNTER 🍪$'), start_extractor),
                    CommandHandler("start", start)
                ],
                USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
                PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
                TFA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tfa_and_process)],
            },
            fallbacks=[CommandHandler("start", start)],
        )
        
        app.add_handler(conv_handler)
        print("✅ BOT IS ONLINE!")
        print("📱 Send /start on Telegram")
        print("\n⚠️ Note:")
        print("   • Bot runs while app is open")
        print("   • Close app = Bot stops\n")
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Solutions:")
        print("   1. Check your internet connection")
        print("   2. Make sure BOT_TOKEN is correct")
        print("   3. Restart Pydroid3 app")
        print("   4. Use mobile data instead of WiFi")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
