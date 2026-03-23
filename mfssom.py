from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import re
from datetime import datetime

# ================ بيانات البوت ================
API_ID = 30060665
API_HASH = "0f381728a1285e4a5e44972743fafa97"
BOT_TOKEN = "8764912480:AAH7Msf8WIux7PBcjl_zBpC4VrNYkMbWFt0"

app = Client("login_code_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
active_sessions = {}

def extract_code(text):
    """استخراج الكود من النص - يدعم 5 أو 6 أرقام"""
    if not text: return None
    # بحث عن 5 أو 6 أرقام متتالية
    match = re.search(r'\b(\d{5})\b|\b(\d{6})\b', str(text))
    return match.group(0) if match else None

def is_login_message(text):
    """التحقق إذا كانت الرسالة تحتوي على كلمات مفتاحية للكود"""
    if not text: return False
    text = str(text).lower()
    keywords = [
        "login code", "verification code", "كود تسجيل الدخول", 
        "كود التحقق", "your code", "code:", "كود:", "is your code",
        "telegram code", "login", "verification"
    ]
    return any(keyword in text for keyword in keywords)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "🔑 **مرحباً بك في بوت جلب كود تسجيل الدخول!**\n\n"
        "**📌 كيفية الاستخدام:**\n\n"
        "1️⃣ احصل على جلسة حسابك من @StringSessionBot\n"
        "2️⃣ أرسل لي الجلسة (النص الطويل)\n"
        "3️⃣ استخدم الأوامر التالية:\n"
        "   • /getcode - جلب آخر كود\n"
        "   • /search - بحث متقدم في كل المحادثات\n"
        "   • /status - عرض حالة الجلسة\n"
        "   • /test - اختبار صلاحية الجلسة\n"
        "   • /stop - إنهاء الجلسة\n\n"
        "⚠️ استخدم حساب ثانوي للحماية",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📱 شرح الحصول على جلسة", callback_data="how_to_get_session")
        ]])
    )

@app.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply_text(
        "**📚 قائمة الأوامر:**\n\n"
        "/start - بدء البوت\n"
        "/getcode - جلب آخر كود\n"
        "/search - بحث متقدم في كل المحادثات\n"
        "/status - عرض حالة الجلسة\n"
        "/test - اختبار صلاحية الجلسة\n"
        "/stop - إنهاء الجلسة\n"
        "/help - عرض المساعدة"
    )

@app.on_message(filters.command("status"))
async def status_command(client, message):
    user_id = message.from_user.id
    if user_id in active_sessions:
        info = active_sessions[user_id]["info"]
        await message.reply_text(
            f"✅ **جلسة نشطة**\n\n"
            f"• الاسم: {info['name']}\n"
            f"• المعرف: `{info['id']}`\n"
            f"• اليوزرنيم: @{info['username'] if info['username'] else 'لا يوجد'}"
        )
    else:
        await message.reply_text("❌ لا توجد جلسة نشطة")

@app.on_message(filters.command("stop"))
async def stop_command(client, message):
    user_id = message.from_user.id
    if user_id in active_sessions:
        try: await active_sessions[user_id]["client"].stop()
        except: pass
        del active_sessions[user_id]
        await message.reply_text("✅ تم إنهاء الجلسة")
    else:
        await message.reply_text("❌ لا توجد جلسة نشطة")

@app.on_message(filters.command("test"))
async def test_command(client, message):
    user_id = message.from_user.id
    if user_id not in active_sessions:
        await message.reply_text("❌ لا توجد جلسة")
        return
    
    waiting = await message.reply_text("🔄 جاري اختبار الجلسة...")
    try:
        user_client = active_sessions[user_id]["client"]
        me = await user_client.get_me()
        
        # جلب أول 5 محادثات للاختبار
        dialogs = []
        async for dialog in user_client.get_dialogs():
            chat_name = dialog.chat.title or dialog.chat.first_name or "محادثة"
            dialogs.append(chat_name)
            if len(dialogs) >= 5: break
        
        await waiting.delete()
        await message.reply_text(
            f"✅ **الجلسة تعمل بشكل ممتاز**\n\n"
            f"المستخدم: {me.first_name}\n"
            f"المحادثات المتاحة: {', '.join(dialogs)}"
        )
    except Exception as e:
        await waiting.delete()
        await message.reply_text(f"❌ الجلسة غير صالحة: {str(e)}")

@app.on_message(filters.command("getcode"))
async def getcode_command(client, message):
    user_id = message.from_user.id
    if user_id not in active_sessions:
        await message.reply_text("❌ أرسل جلسة حسابك أولاً")
        return
    
    waiting = await message.reply_text("🔄 جاري البحث عن الكود...")
    
    try:
        user_client = active_sessions[user_id]["client"]
        found_codes = []
        
        # البحث في جميع المحادثات
        async for dialog in user_client.get_dialogs():
            chat = dialog.chat
            chat_name = chat.title or chat.first_name or "محادثة"
            
            # جلب آخر 30 رسالة من كل محادثة
            async for msg in user_client.get_chat_history(chat.id, limit=30):
                if msg.text:
                    code = extract_code(msg.text)
                    if code and (is_login_message(msg.text) or len(code) in [5, 6]):
                        found_codes.append({
                            'code': code,
                            'chat': chat_name,
                            'date': msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                            'text': msg.text[:100]
                        })
                        if len(found_codes) >= 5: break
            if len(found_codes) >= 5: break
        
        await waiting.delete()
        
        if found_codes:
            # ترتيب النتائج من الأحدث للأقدم
            found_codes.sort(key=lambda x: x['date'], reverse=True)
            
            response = "✅ **تم العثور على أكود:**\n\n"
            for i, item in enumerate(found_codes[:3], 1):
                response += f"{i}️⃣ **الكود:** `{item['code']}`\n"
                response += f"   📱 من: {item['chat']}\n"
                response += f"   📅 في: {item['date']}\n\n"
            
            await message.reply_text(response)
        else:
            await message.reply_text(
                "❌ **لم يتم العثور على أي كود**\n\n"
                "🔍 **جرب:**\n"
                "• /search للبحث بشكل أعمق\n"
                "• أرسل كود جديد لحسابك ثم ابحث فوراً\n"
                "• تأكد أن الكود لم يُحذف"
            )
            
    except Exception as e:
        await waiting.delete()
        await message.reply_text(f"❌ خطأ: {str(e)}")

@app.on_message(filters.command("search"))
async def search_command(client, message):
    user_id = message.from_user.id
    if user_id not in active_sessions:
        await message.reply_text("❌ أرسل جلسة حسابك أولاً")
        return
    
    waiting = await message.reply_text("🔄 جاري البحث المتقدم في جميع المحادثات...")
    
    try:
        user_client = active_sessions[user_id]["client"]
        all_codes = []
        chats_searched = 0
        
        # البحث في جميع المحادثات
        async for dialog in user_client.get_dialogs():
            chats_searched += 1
            chat = dialog.chat
            chat_name = chat.title or chat.first_name or "محادثة"
            
            # جلب آخر 50 رسالة من كل محادثة
            async for msg in user_client.get_chat_history(chat.id, limit=50):
                if msg.text:
                    # بحث عن أي 5-6 أرقام
                    numbers = re.findall(r'\b\d{5,6}\b', str(msg.text))
                    for num in numbers:
                        all_codes.append({
                            'code': num,
                            'chat': chat_name,
                            'date': msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                            'text': msg.text[:50]
                        })
            
            # تحديث رسالة التقدم كل 10 محادثات
            if chats_searched % 10 == 0:
                await waiting.edit_text(f"🔄 تم البحث في {chats_searched} محادثة...")
        
        await waiting.delete()
        
        if all_codes:
            # ترتيب وتصفية النتائج
            all_codes.sort(key=lambda x: x['date'], reverse=True)
            unique_codes = []
            seen = set()
            
            for item in all_codes:
                if item['code'] not in seen and len(unique_codes) < 10:
                    seen.add(item['code'])
                    unique_codes.append(item)
            
            response = f"✅ **تم العثور على {len(unique_codes)} كود**\n"
            response += f"📊 تم البحث في {chats_searched} محادثة\n\n"
            
            for i, item in enumerate(unique_codes[:5], 1):
                response += f"{i}️⃣ **`{item['code']}`**\n"
                response += f"   📱 {item['chat']} - {item['date']}\n"
            
            await message.reply_text(response)
        else:
            await message.reply_text(f"❌ لم يتم العثور على أكود في {chats_searched} محادثة")
            
    except Exception as e:
        await waiting.delete()
        await message.reply_text(f"❌ خطأ: {str(e)}")

@app.on_message(filters.text & filters.private)
async def handle_session(client, message):
    text = message.text.strip()
    user_id = message.from_user.id
    
    if text.startswith('/') or len(text) < 50:
        return
    
    waiting = await message.reply_text("🔄 جاري التحقق من الجلسة...")
    
    try:
        user_client = Client(f"user_{user_id}", api_id=API_ID, api_hash=API_HASH, session_string=text, in_memory=True)
        await user_client.connect()
        me = await user_client.get_me()
        
        active_sessions[user_id] = {
            "client": user_client,
            "info": {
                "id": me.id,
                "name": me.first_name,
                "username": me.username
            },
            "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        await waiting.delete()
        await message.reply_text(
            f"✅ **تم التحقق بنجاح!**\n\n"
            f"الاسم: {me.first_name}\n"
            f"المعرف: `{me.id}`\n\n"
            f"**الأوامر المتاحة:**\n"
            f"• /getcode - جلب الكود\n"
            f"• /search - بحث متقدم\n"
            f"• /test - اختبار الجلسة",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 بحث عن أكود", callback_data="search_now")
            ]])
        )
        
    except Exception as e:
        await waiting.delete()
        await message.reply_text(f"❌ جلسة غير صالحة: {str(e)[:100]}")

@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == "how_to_get_session":
        await callback_query.message.edit_text(
            "**📱 خطوات الحصول على جلسة:**\n\n"
            "1️⃣ اذهب إلى @StringSessionBot\n"
            "2️⃣ أرسل /start\n"
            "3️⃣ اختر Pyrogram (رقم 1)\n"
            "4️⃣ أرسل رقم هاتفك مع مفتاح الدولة\n"
            "5️⃣ أرسل كود التحقق\n"
            "6️⃣ إذا طلب كلمة مرور التحقق بخطوتين، أرسلها\n"
            "7️⃣ انسخ الجلسة الناتجة وأرسلها لي",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")
            ]])
        )
    
    elif data == "back_to_start":
        await start_command(client, callback_query.message)
    
    elif data == "search_now":
        await callback_query.answer()
        msg = callback_query.message
        msg.from_user = callback_query.from_user
        await search_command(client, msg)

if __name__ == "__main__":
    print("=" * 50)
    print("✅ بوت جلب أكود تسجيل الدخول - النسخة المطورة")
    print("=" * 50)
    print("\n📱 البوت يعمل...")
    print("=" * 50)
    app.run()