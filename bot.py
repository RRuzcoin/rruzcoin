import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from strings import LANGS # 22 ta til lug'ati [cite: 2025-12-21]

# --- ASOSIY SOZLAMALAR ---
API_TOKEN = '8550803046:AAHWhHvREEzYQV_Gi-9pyT5eX_xD7MKrpUA'
ADMIN_ID = 1424175786 # Sizning tasdiqlangan ID raqamingiz [cite: 2025-12-21]
MY_CARD = "8600123456789012" # To'lovlar uchun karta [cite: 2025-12-21]
WEB_APP_URL = "https://rruzcoin.github.io/rruzcoin/" # Mining interfeysi [cite: 2025-12-21]

# --- PROXY SOZLAMASI (PythonAnywhere Free Tier uchun shart) ---
# Bu qism Network unreachable xatosini tuzatadi
proxy_url = "http://proxy.server:3128"

bot = Bot(token=API_TOKEN, parse_mode="Markdown", proxy=proxy_url)
dp = Dispatcher(bot)

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('rruz_pro.db', check_same_thread=False)
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY, b REAL DEFAULT 0, speed REAL DEFAULT 1.0, 
    dep REAL DEFAULT 0, lang TEXT DEFAULT 'en')''')
conn.commit()

# --- KLAVIATURA FUNKSIYASI ---
def get_kb(uid, lang_code):
    s = LANGS.get(lang_code, LANGS['en'])
    kb = InlineKeyboardMarkup(row_width=2)
    # Mining Web App tugmasi [cite: 2025-12-21]
    kb.add(InlineKeyboardButton(text=s['mining'], web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.add(InlineKeyboardButton(text=s['wallet'], callback_data="w"),
           InlineKeyboardButton(text=s['dep'], callback_data="d"))
    kb.add(InlineKeyboardButton(text=s['stats'], callback_data="s"))
    # ADMINNI TANISH [cite: 2025-12-21]
    if int(uid) == ADMIN_ID:
        kb.add(InlineKeyboardButton(text="🛠 SUPER ADMIN PANEL", callback_data="admin_panel"))
    return kb

def lang_kb():
    # 22 ta til bayroqlari [cite: 2025-12-21]
    flags = {'uz':'🇺🇿','en':'🇬🇧','ru':'🇷🇺','de':'🇩🇪','tr':'🇹🇷','cn':'🇨🇳','fr':'🇫🇷','es':'🇪🇸',
             'kr':'🇰🇷','jp':'🇯🇵','kz':'🇰🇿','kg':'🇰🇬','tj':'🇹🇯','tm':'🇹🇲','ae':'🇦🇪','it':'🇮🇹',
             'in':'🇮🇳','br':'🇧🇷','vn':'VN','id':'🇮🇩','ph':'🇵🇭','az':'🇦🇿'}
    kb = InlineKeyboardMarkup(row_width=4)
    btns = [InlineKeyboardButton(text=v, callback_data=f"l_{k}") for k, v in flags.items()]
    kb.add(*btns)
    return kb

# --- HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    # Sizning shioringiz: "RRuzcoin: Uncontrolled cash — the path to transparency" [cite: 2025-12-26]
    await m.answer("💎 **RRuzcoin Official Node**\n\nPlease choose your language / Tilni tanlang:", reply_markup=lang_kb())

@dp.callback_query_handler(lambda c: c.data.startswith('l_'))
async def set_language(callback_query: types.CallbackQuery):
    lang_code = callback_query.data.split('_')[1]
    
    db.execute("UPDATE users SET lang = ? WHERE id = ?", (lang_code, callback_query.from_user.id))
    conn.commit()
    
    s = LANGS.get(lang_code, LANGS['en'])
    
    await bot.answer_callback_query(callback_query.id, text="Language updated! ✅")
    
    await bot.send_message(
        callback_query.from_user.id, 
        s['start'], 
        reply_markup=get_kb(callback_query.from_user.id, lang_code)
    )

# --- SUPER ADMIN PANEL FUNKSIYALARI ---

@dp.callback_query_handler(text="admin_panel")
async def admin_menu(c: types.CallbackQuery):
    if c.from_user.id != ADMIN_ID: return
    db.execute("SELECT COUNT(*) FROM users")
    count = db.fetchone()[0]
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("📢 Xabar yuborish (AD)", callback_data="send_ad"))
    await c.message.answer(f"🛠 **RRuzcoin Admin Panel**\n\n👤 Foydalanuvchilar: {count}\n🚀 Tizim: Faol", reply_markup=kb)

@dp.callback_query_handler(text="send_ad")
async def ad_prompt(c: types.CallbackQuery):
    await c.message.answer("📢 Reklama matnini yuboring. Bot uni barcha foydalanuvchilarga tarqatadi.")

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID)
async def broadcast(m: types.Message):
    if m.text and not m.text.startswith('/'):
        db.execute("SELECT id FROM users")
        users = db.fetchall()
        count = 0
        for user in users:
            try:
                await bot.send_message(user[0], m.text)
                count += 1
            except: pass
        await m.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
