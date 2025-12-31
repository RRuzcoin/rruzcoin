import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from strings import LANGS 

# --- KONFIGURATSIYA ---
API_TOKEN = '8550803046:AAHWhHvREEzYQV_Gi-9pyT5eX_xD7MKrpUA'
ADMIN_ID = 1424175786 
WEB_APP_URL = "https://rruzcoin.github.io/rruzcoin/" 
SLOGAN = "RRuzcoin: Uncontrolled cash — the path to transparency"

# PythonAnywhere Free tarif uchun Proxy (O'chirib tashlanmaydi!)
proxy_url = "http://proxy.server:3128"
bot = Bot(token=API_TOKEN, parse_mode="Markdown", proxy=proxy_url)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('rruz_core.db', check_same_thread=False)
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY, b REAL DEFAULT 0, speed REAL DEFAULT 0.00000000000001, 
    dep REAL DEFAULT 0, lang TEXT DEFAULT 'uz')''')
db.execute('''CREATE TABLE IF NOT EXISTS system_settings 
    (id INTEGER PRIMARY KEY, payment_data TEXT)''')
db.execute("INSERT OR IGNORE INTO system_settings (id, payment_data) VALUES (1, 'Hali kiritilmagan')")
conn.commit()

# --- ADMIN STATES ---
class AdminNode(StatesGroup):
    waiting_pay = State()
    waiting_broadcast = State()

# --- SMART KEYBOARDS ---

def main_menu(uid, lang):
    s = LANGS.get(lang, LANGS.get('uz', {}))
    kb = InlineKeyboardMarkup(row_width=2)
    # 3D Tanga dizayni bo'lgan mining panel
    kb.add(InlineKeyboardButton(text="⛏ MINING", web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.add(InlineKeyboardButton(text="💳 " + s.get('wallet', 'HAMYON'), callback_data="user_wallet"),
           InlineKeyboardButton(text="📊 STATISTIKA", callback_data="user_stats"))
    kb.add(InlineKeyboardButton(text="📞 ALOQA", url=f"tg://user?id={ADMIN_ID}"))
    
    if int(uid) == ADMIN_ID:
        kb.add(InlineKeyboardButton(text="💎 SUPER ADMIN PANEL", callback_data="admin_root"))
    return kb

def admin_root_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text="⚙️ HAMYONLARNI SOZLASH", callback_data="adm_pay_set"),
        InlineKeyboardButton(text="👥 FOYDALANUVCHILAR SONI", callback_data="adm_users_list"),
        InlineKeyboardButton(text="📢 GLOBAL E'LON YUBORISH", callback_data="adm_send_all"),
        InlineKeyboardButton(text="🔙 ASOSIY MENYU", callback_data="back_home")
    )
    return kb

# --- HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def start_node(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    
    # 22 ta tilni chiqarish
    kb = InlineKeyboardMarkup(row_width=3)
    btns = [InlineKeyboardButton(text=k.upper(), callback_data=f"setl_{k}") for k in LANGS.keys()]
    kb.add(*btns)
    
    await m.answer(f"🛡 **RRuzcoin Node Interface**\n\n_{SLOGAN}_\n\nTilni tanlang / Choose language:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('setl_'))
async def set_lang(c: types.CallbackQuery):
    lang = c.data.split('_')[1]
    db.execute("UPDATE users SET lang = ? WHERE id = ?", (lang, c.from_user.id))
    conn.commit()
    await bot.edit_message_text(f"✅ **Node Online**\n_{SLOGAN}_", 
                               c.from_user.id, c.message.message_id, 
                               reply_markup=main_menu(c.from_user.id, lang))

# --- SUPER ADMIN LOGIC ---

@dp.callback_query_handler(lambda c: c.data == "admin_root")
async def admin_panel(c: types.CallbackQuery):
    if c.from_user.id == ADMIN_ID:
        await bot.edit_message_text("🕹 **SUPER ADMIN BOSHQUV MARKAZI**\nBarcha tizimlar nazoratingizda.",
                                   c.from_user.id, c.message.message_id, reply_markup=admin_root_kb())

@dp.callback_query_handler(lambda c: c.data == "adm_pay_set")
async def pay_setup(c: types.CallbackQuery):
    if c.from_user.id == ADMIN_ID:
        await bot.send_message(c.from_user.id, "💳 **Hamyonlarni kiriting (Istalgan turdagi kartalarni birin-ketin yozing):**")
        await AdminNode.waiting_pay.set()

@dp.message_handler(state=AdminNode.waiting_pay)
async def save_pay(m: types.Message, state: FSMContext):
    db.execute("UPDATE system_settings SET payment_data = ? WHERE id = 1", (m.text,))
    conn.commit()
    await m.answer("✅ Hamyonlar tizimga saqlandi.")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "adm_users_list")
async def adm_users_count(c: types.CallbackQuery):
    db.execute("SELECT COUNT(id) FROM users")
    count = db.fetchone()[0]
    await bot.answer_callback_query(c.id, text=f"📊 Jami foydalanuvchilar: {count}", show_alert=True)

@dp.callback_query_handler(lambda c: c.data == "adm_send_all")
async def broadcast_start(c: types.CallbackQuery):
    await bot.send_message(c.from_user.id, "📢 **E'lon yuboring (Rasm yoki matn):**")
    await AdminNode.waiting_broadcast.set()

@dp.message_handler(state=AdminNode.waiting_broadcast, content_types=types.ContentTypes.ANY)
async def do_broadcast(m: types.Message, state: FSMContext):
    db.execute("SELECT id FROM users")
    users = db.fetchall()
    for user in users:
        try:
            await m.copy_to(user[0])
        except:
            pass
    await m.answer("✅ E'lon barchaga yuborildi.")
    await state.finish()

# --- USER WALLET & STATS ---

@dp.callback_query_handler(lambda c: c.data == "user_wallet")
async def wallet_info(c: types.CallbackQuery):
    db.execute("SELECT b, lang FROM users WHERE id = ?", (c.from_user.id,))
    user = db.fetchone()
    lang = user[1] if user else 'uz'
    s = LANGS.get(lang, LANGS.get('uz', {}))
    
    text = f"💰 **{s.get('wallet', 'Hamyon')}**\n\nBalans: `{user[0]}` RRuz\n\n_{SLOGAN}_"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton(text="⚡️ BOOST SPEED", callback_data="buy_speed"))
    await bot.send_message(c.from_user.id, text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "buy_speed")
async def buy_speed(c: types.CallbackQuery):
    db.execute("SELECT payment_data FROM system_settings WHERE id = 1")
    pay = db.fetchone()[0]
    msg = f"🏦 **DEPOT TIZIMI (ANONIM)**\n\nTezlikni oshirish uchun quyidagi manzillarga depozit qiling:\n\n`{pay}`"
    await bot.send_message(c.from_user.id, msg)

@dp.callback_query_handler(lambda c: c.data == "user_stats")
async def user_stats(c: types.CallbackQuery):
    db.execute("SELECT speed, dep FROM users WHERE id = ?", (c.from_user.id,))
    data = db.fetchone()
    text = f"📊 **Mining Statistikasi**\n\n🚀 Tezlik: `{data[0]}` RR/sec\n📥 Depozit: `{data[1]}`"
    await bot.answer_callback_query(c.id, text=text, show_alert=True)

@dp.callback_query_handler(lambda c: c.data == "back_home")
async def back_home(c: types.CallbackQuery):
    db.execute("SELECT lang FROM users WHERE id = ?", (c.from_user.id,))
    row = db.fetchone()
    lang = row[0] if row else 'uz'
    await bot.edit_message_text(f"🛡 **Node Active**\n_{SLOGAN}_", c.from_user.id, c.message.message_id, reply_markup=main_menu(c.from_user.id, lang))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
