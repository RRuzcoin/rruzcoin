import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from strings import LANGS 

# --- ASOSIY SOZLAMALAR ---
API_TOKEN = '8550803046:AAHWhHvREEzYQV_Gi-9pyT5eX_xD7MKrpUA'
ADMIN_ID = 1424175786 
WEB_APP_URL = "https://rruzcoin.github.io/rruzcoin/" 
proxy_url = "http://proxy.server:3128" 

bot = Bot(token=API_TOKEN, parse_mode="Markdown", proxy=proxy_url)
dp = Dispatcher(bot)

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('rruz_pro.db', check_same_thread=False)
db = conn.cursor()

# TEZLIKNI YANGILADIK: speed REAL DEFAULT 0.00000000000001
db.execute('''CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY, b REAL DEFAULT 0, speed REAL DEFAULT 0.00000000000001, 
    dep REAL DEFAULT 0, lang TEXT DEFAULT 'en', status TEXT DEFAULT 'active')''')

db.execute('''CREATE TABLE IF NOT EXISTS payments 
    (id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, amount REAL, method TEXT, status TEXT DEFAULT 'pending')''')
db.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')

db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card', '8600123456789012')")
db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('wallet', 'bc1q...')")
conn.commit()

# --- KLAVIATURA FUNKSIYALARI ---

def get_kb(uid, lang_code):
    s = LANGS.get(lang_code, LANGS['en'])
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton(text=s['mining'], web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.add(InlineKeyboardButton(text=s['wallet'], callback_data="w"),
           InlineKeyboardButton(text=s['dep'], callback_data="d"))
    kb.add(InlineKeyboardButton(text=s['stats'], callback_data="s"))
    kb.add(InlineKeyboardButton(text="📞 Aloqa / Support", url="https://t.me/RRuzcoinofficial"))
    if int(uid) == ADMIN_ID:
        kb.add(InlineKeyboardButton(text="🛠 SUPER ADMIN PANEL", callback_data="admin_main"))
    return kb

def admin_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📢 Xabar yuborish (AD)", callback_data="admin_ad"),
        InlineKeyboardButton("👥 Foydalanuvchilarni boshqarish", callback_data="admin_users"),
        InlineKeyboardButton("💰 Depozitlar va To'lovlar", callback_data="admin_pays"),
        InlineKeyboardButton("💳 Hamyon va Kartani ulash", callback_data="admin_settings"),
        InlineKeyboardButton("❌ Paneldan chiqish", callback_data="close_admin")
    )
    return kb

def lang_kb():
    flags = {'uz':'🇺🇿','en':'🇬🇧','ru':'🇷🇺','de':'🇩🇪','tr':'🇹🇷','cn':'🇨🇳','fr':'🇫🇷','es':'🇪🇸',
             'kr':'🇰🇷','jp':'🇯🇵','kz':'🇰🇿','kg':'🇰🇬','tj':'🇹🇯','tm':'🇹🇲','ae':'🇦🇪','it':'🇮🇹',
             'in':'🇮🇳','br':'🇧🇷','vn':'VN','id':'🇮🇩','ph':'🇵🇭','az':'🇦🇿'}
    kb = InlineKeyboardMarkup(row_width=4)
    btns = [InlineKeyboardButton(text=v, callback_data=f"l_{k}") for k, v in flags.items()]
    kb.add(*btns)
    return kb

# --- ASOSIY HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    await m.answer("💎 **RRuzcoin Official Node**\n\nRRuzcoin: Uncontrolled cash — the path to transparency.", reply_markup=lang_kb())

@dp.callback_query_handler(lambda c: c.data.startswith('l_'))
async def set_language(c: types.CallbackQuery):
    lang_code = c.data.split('_')[1]
    db.execute("UPDATE users SET lang = ? WHERE id = ?", (lang_code, c.from_user.id))
    conn.commit()
    s = LANGS.get(lang_code, LANGS['en'])
    await bot.answer_callback_query(c.id, text="Language updated! ✅")
    await bot.send_message(c.from_user.id, s['start'], reply_markup=get_kb(c.from_user.id, lang_code))

# --- SUPER ADMIN PANEL LOGIKASI ---

@dp.callback_query_handler(text="admin_main")
async def admin_main(c: types.CallbackQuery):
    if c.from_user.id != ADMIN_ID: return
    db.execute("SELECT COUNT(*) FROM users")
    count = db.fetchone()[0]
    await c.message.edit_text(f"🛠 **RRuzcoin Super Admin Panel**\n\n👤 Foydalanuvchilar: {count}\n🚀 Node holati: Faol ✅", reply_markup=admin_kb())

@dp.callback_query_handler(text="admin_settings")
async def admin_settings(c: types.CallbackQuery):
    db.execute("SELECT value FROM settings WHERE key='card'")
    card = db.fetchone()[0]
    db.execute("SELECT value FROM settings WHERE key='wallet'")
    wallet = db.fetchone()[0]
    text = f"⚙️ **To'lov sozlamalari**\n\n💳 Karta: `{card}`\n🪙 Hamyon: `{wallet}`\n\nO'zgartirish uchun `SET_CARD: raqam` yoki `SET_WALLET: manzil` deb xabar yuboring."
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_main"))
    await c.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(text="admin_pays")
async def admin_pays(c: types.CallbackQuery):
    db.execute("SELECT * FROM payments WHERE status='pending'")
    pays = db.fetchall()
    text = "💰 **Kutilayotgan to'lovlar:**\n\n"
    if not pays: text += "Hozircha yangi so'rovlar yo'q."
    for p in pays:
        text += f"ID: {p[0]} | User: {p[1]} | Summa: {p[2]} | Usul: {p[3]}\n"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_main"))
    await c.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(text="close_admin")
async def close_admin(c: types.CallbackQuery):
    await c.message.delete()

# --- ADMIN BUYRUQLARINI QABUL QILISH ---

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID)
async def admin_process(m: types.Message):
    if m.text.startswith("SET_CARD:"):
        val = m.text.replace("SET_CARD:", "").strip()
        db.execute("UPDATE settings SET value=? WHERE key='card'", (val,))
        conn.commit()
        await m.answer(f"✅ Karta raqami yangilandi: `{val}`")
    
    elif m.text.startswith("SET_WALLET:"):
        val = m.text.replace("SET_WALLET:", "").strip()
        db.execute("UPDATE settings SET value=? WHERE key='wallet'", (val,))
        conn.commit()
        await m.answer(f"✅ Hamyon manzili yangilandi: `{val}`")

    elif m.text.startswith("AD:"):
        msg = m.text.replace("AD:", "").strip()
        db.execute("SELECT id FROM users")
        for user in db.fetchall():
            try: await bot.send_message(user[0], msg)
            except: pass
        await m.answer("📢 Reklama barcha foydalanuvchilarga yuborildi!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
