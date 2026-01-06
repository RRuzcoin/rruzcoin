import logging
import sqlite3
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- KONFIGURATSIYA ---
API_TOKEN = '8550803046:AAHWhHvREEzYQV_Gi-9pyT5eX_xD7MKrpUA'
ADMIN_ID = 1424175786 
WEB_APP_URL = "https://rruzcoin.github.io/rruzcoin/" 
REF_BONUS = 0.0000100000 
SLOGAN = "RRuzcoin: Uncontrolled cash — the path to transparency"
BRAND_COIN_URL = "https://raw.githubusercontent.com/rruzcoin/rruzcoin/main/IMG_20251231_141643_658.jpg"

# PythonAnywhere bepul tarifi uchun Proxy sozlamasi
PROXY_URL = "http://proxy.server:3128"

logging.basicConfig(level=logging.INFO)

# Botni Proxy bilan ishga tushirish
bot = Bot(token=API_TOKEN, parse_mode="Markdown", proxy=PROXY_URL)
dp = Dispatcher(bot)

# --- BAZA BILAN ISHLASH ---
def db_manage(query, params=(), fetchone=False, commit=False):
    with sqlite3.connect('rruz_core.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit: conn.commit()
        if fetchone: return cursor.fetchone()
        return cursor.fetchall()

def init_db():
    db_manage('''CREATE TABLE IF NOT EXISTS users 
        (id INTEGER PRIMARY KEY, b REAL DEFAULT 0, speed REAL DEFAULT 0.0000000001, referrer_id INTEGER)''', commit=True)
init_db()

# --- ASOSIY MENYU ---
def main_menu(uid):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton(text="⛏ MINING TERMINAL", web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.add(InlineKeyboardButton(text="📊 STATISTIKA", callback_data="network_stats"))
    kb.add(InlineKeyboardButton(text="👥 DO'STLAR", callback_data="friends_list"))
    if int(uid) == ADMIN_ID:
        kb.add(InlineKeyboardButton(text="💎 ADMIN", callback_data="admin_root"))
    return kb

# --- REFERAL TIZIMI BILAN START ---
@dp.message_handler(commands=['start'])
async def start_command(m: types.Message):
    user_id = m.from_user.id
    args = m.get_args()
    
    is_new = db_manage("SELECT id FROM users WHERE id = ?", (user_id,), fetchone=True) is None
    
    if is_new:
        ref_id = None
        if args and args.isdigit() and int(args) != user_id:
            ref_id = int(args)
            # Taklif qilganga bonus berish
            db_manage("UPDATE users SET b = b + ? WHERE id = ?", (REF_BONUS, ref_id), commit=True)
            try:
                await bot.send_message(ref_id, f"🎉 **Yangi do'st qo'shildi!**\nSizga `{REF_BONUS:.10f}` RRZC bonus berildi.")
            except: pass
            
        db_manage("INSERT INTO users (id, referrer_id) VALUES (?, ?)", (user_id, ref_id), commit=True)
    
    await bot.send_photo(
        m.chat.id, 
        BRAND_COIN_URL, 
        caption=f"🪙 **RRuzcoin Node Active**\n\n_{SLOGAN}_", 
        reply_markup=main_menu(user_id)
    )

# --- DO'STLAR BO'LIMI ---
@dp.callback_query_handler(lambda c: c.data == "friends_list")
async def show_friends(c: types.CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={c.from_user.id}"
    invited_count = db_manage("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (c.from_user.id,), fetchone=True)[0]
    
    text = (f"👥 **DO'STLAR**\n\n"
            f"Har bir taklif qilingan do'st uchun:\n`+{REF_BONUS:.10f} RRZC` oling!\n\n"
            f"Siz taklif qilganlar: `{invited_count}` ta\n\n"
            f"Sizning havolangiz:\n`{ref_link}`")
    
    await bot.send_message(c.from_user.id, text)

# --- REAL STATISTIKA ---
@dp.callback_query_handler(lambda c: c.data == "network_stats")
async def show_stats(c: types.CallbackQuery):
    total_users = db_manage("SELECT COUNT(*) FROM users", fetchone=True)[0]
    total_supply = db_manage("SELECT SUM(b) FROM users", fetchone=True)[0] or 0
    user_b = db_manage("SELECT b FROM users WHERE id = ?", (c.from_user.id,), fetchone=True)[0]

    text = (f"📊 **STATISTIKA**\n\n"
            f"👥 Foydalanuvchilar: `{total_users}`\n"
            f"⚡️ Tarmoq kuchi: `4.2 TH/s`\n"
            f"🪙 Sirkulyatsiya: `{total_supply:.6f} RRZC`\n\n"
            f"💰 Sizning balansingiz: `{user_b:.10f}` RRZC")
    
    await bot.answer_callback_query(c.id)
    await bot.send_message(c.from_user.id, text)

# WebApp dan ma'lumot qabul qilish
@dp.message_handler(content_types=['web_app_data'])
async def handle_webapp_data(m: types.Message):
    try:
        data = json.loads(m.web_app_data.data)
        new_balance = float(data.get('new_balance', 0))
        db_manage("UPDATE users SET b = ? WHERE id = ?", (new_balance, m.from_user.id), commit=True)
        await m.answer(f"✅ Balans saqlandi: `{new_balance:.10f}`")
    except:
        await m.answer("❌ Sinxronizatsiyada xato.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
