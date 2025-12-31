import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from strings import LANGS 

# --- ASOSIY SOZLAMALAR ---
API_TOKEN = '8550803046:AAHWhHvREEzYQV_Gi-9pyT5eX_xD7MKrpUA'
ADMIN_ID = 1424175786 
WEB_APP_URL = "https://rruzcoin.github.io/rruzcoin/" 
# Sizning shioringiz [cite: 2025-12-26]
SLOGAN = "RRuzcoin: Uncontrolled cash — the path to transparency"

# PYTHONANYWHERE UCHUN PROXY (MUHIM!)
proxy_url = "http://proxy.server:3128" 

# Botni proxy bilan ishga tushirish (Network unreachable xatosini tuzatadi)
bot = Bot(token=API_TOKEN, parse_mode="Markdown", proxy=proxy_url)
dp = Dispatcher(bot)

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('rruz_pro.db', check_same_thread=False)
db = conn.cursor()

# Jadvalni yaratish va mining tezligini saqlash [cite: 2025-12-21]
db.execute('''CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY, b REAL DEFAULT 0, speed REAL DEFAULT 0.00000000000001, 
    dep REAL DEFAULT 0, lang TEXT DEFAULT 'en', status TEXT DEFAULT 'active')''')

# Eski ma'lumotlarni siz aytgan tezlikka tahrirlash [cite: 2025-12-21]
db.execute("UPDATE users SET speed = 0.00000000000001 WHERE speed > 0.00000000000001")
conn.commit()

# --- KLAVIATURA ---
def get_kb(uid, lang_code):
    s = LANGS.get(lang_code, LANGS['en'])
    kb = InlineKeyboardMarkup(row_width=2)
    # 3D RR tangali portalni ochish tugmasi
    kb.add(InlineKeyboardButton(text="⚡ OPEN MINING PORTAL", web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.add(InlineKeyboardButton(text="💼 " + s['wallet'], callback_data="w"),
           InlineKeyboardButton(text="💰 " + s['dep'], callback_data="d"))
    kb.add(InlineKeyboardButton(text="🛠 SUPPORT", url="https://t.me/RRuzcoinofficial"))
    if int(uid) == ADMIN_ID:
        kb.add(InlineKeyboardButton(text="💎 ADMIN PANEL", callback_data="admin_main"))
    return kb

def lang_kb():
    flags = {'uz':'🇺🇿','en':'🇬🇧','ru':'🇷🇺'}
    kb = InlineKeyboardMarkup(row_width=3)
    btns = [InlineKeyboardButton(text=v, callback_data=f"l_{k}") for k, v in flags.items()]
    kb.add(*btns)
    return kb

# --- HANDLERLAR ---
@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    welcome_msg = f"🛡 **Welcome to RRuzcoin Node**\n\n_{SLOGAN}_"
    await m.answer(welcome_msg, reply_markup=lang_kb())

@dp.callback_query_handler(lambda c: c.data.startswith('l_'))
async def set_language(c: types.CallbackQuery):
    lang_code = c.data.split('_')[1]
    db.execute("UPDATE users SET lang = ? WHERE id = ?", (lang_code, c.from_user.id))
    conn.commit()
    await bot.answer_callback_query(c.id, text="Activated! ⚡")
    await bot.send_message(c.from_user.id, f"✅ **Node Online**\n_{SLOGAN}_", 
                           reply_markup=get_kb(c.from_user.id, lang_code))

if __name__ == '__main__':
    print("RRuzcoin Bot is booting up with Proxy...")
    executor.start_polling(dp, skip_updates=True)
