import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from strings import LANGS 

# --- ASOSIY SOZLAMALAR ---
# Tokenni o'zingizniki bilan almashtiring
API_TOKEN = '8550803046:AAHWhHvREEzYQV_Gi-9pyT5eX_xD7MKrpUA'
ADMIN_ID = 1424175786 
WEB_APP_URL = "https://rruzcoin.github.io/rruzcoin/" 
SLOGAN = "RRuzcoin: Uncontrolled cash — the path to transparency"

bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('rruz_pro.db', check_same_thread=False)
db = conn.cursor()

# Jadvalni yaratish va yangilash
db.execute('''CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY, b REAL DEFAULT 0, speed REAL DEFAULT 0.00000000000001, 
    dep REAL DEFAULT 0, lang TEXT DEFAULT 'en', status TEXT DEFAULT 'active')''')

# Tezlikni 100% kafolatlash uchun (Oldingi xatolarni tozalash)
db.execute("UPDATE users SET speed = 0.00000000000001 WHERE speed > 0.00000000000001")

db.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card', '8600123456789012')")
db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('wallet', 'bc1q...')")
conn.commit()

# --- KLAVIATURA FUNKSIYALARI ---

def get_kb(uid, lang_code):
    s = LANGS.get(lang_code, LANGS['en'])
    kb = InlineKeyboardMarkup(row_width=2)
    # Professional va Dizaynga mos tugmalar
    kb.add(InlineKeyboardButton(text="⚡ OPEN MINING PORTAL", web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.add(InlineKeyboardButton(text="💼 " + s['wallet'], callback_data="w"),
           InlineKeyboardButton(text="💳 " + s['dep'], callback_data="d"))
    kb.add(InlineKeyboardButton(text="📊 " + s['stats'], callback_data="s"))
    kb.add(InlineKeyboardButton(text="🛠 SUPPORT", url="https://t.me/RRuzcoinofficial"))
    
    if int(uid) == ADMIN_ID:
        kb.add(InlineKeyboardButton(text="💎 SUPER ADMIN PANEL", callback_data="admin_main"))
    return kb

def lang_kb():
    # Bayroqlar va tillar
    flags = {'uz':'🇺🇿','en':'🇬🇧','ru':'🇷🇺','tr':'🇹🇷','ae':'🇦🇪'}
    kb = InlineKeyboardMarkup(row_width=3)
    btns = [InlineKeyboardButton(text=v, callback_data=f"l_{k}") for k, v in flags.items()]
    kb.add(*btns)
    return kb

# --- ASOSIY HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    
    # Kiberpank tabrik va Shior
    welcome_msg = (
        f"🛡 **Welcome to RRuzcoin Node**\n\n"
        f"_{SLOGAN}_\n\n"
        "Choose your language to proceed:"
    )
    await m.answer(welcome_msg, reply_markup=lang_kb())

@dp.callback_query_handler(lambda c: c.data.startswith('l_'))
async def set_language(c: types.CallbackQuery):
    lang_code = c.data.split('_')[1]
    db.execute("UPDATE users SET lang = ? WHERE id = ?", (lang_code, c.from_user.id))
    conn.commit()
    
    s = LANGS.get(lang_code, LANGS['en'])
    # Foydalanuvchi tanlagan tilda asosiy xabar
    final_text = f"✅ **Node Activated!**\n\n_{SLOGAN}_"
    
    await bot.answer_callback_query(c.id, text="Connection established! ⚡")
    await bot.send_message(c.from_user.id, final_text, reply_markup=get_kb(c.from_user.id, lang_code))

# --- ADMIN PANEL (Sizning so'rovingizga ko'ra soddalashtirilgan) ---

@dp.callback_query_handler(text="admin_main")
async def admin_main(c: types.CallbackQuery):
    if c.from_user.id != ADMIN_ID: return
    db.execute("SELECT COUNT(*) FROM users")
    count = db.fetchone()[0]
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("❌ Close", callback_data="close"))
    await c.message.edit_text(f"🛠 **RRuzcoin Admin**\n\n👤 Users: {count}\n🚀 Node Status: 🟢 Active", reply_markup=kb)

if __name__ == '__main__':
    print("RRuzcoin Bot is Running...")
    executor.start_polling(dp, skip_updates=True)
