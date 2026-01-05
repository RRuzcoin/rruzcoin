import logging
import sqlite3
import re
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- KONFIGURATSIYA ---
API_TOKEN = '8550803046:AAHWhHvREEzYQV_Gi-9pyT5eX_xD7MKrpUA'
ADMIN_ID = 1424175786 
WEB_APP_URL = "https://rruzcoin.github.io/rruzcoin/" 
SLOGAN = "RRuzcoin: Uncontrolled cash — the path to transparency"
BRAND_COIN_URL = "https://rruzcoin.github.io/rruzcoin/IMG_20251231_141643_658.jpg"

proxy_url = "http://proxy.server:3128"
bot = Bot(token=API_TOKEN, parse_mode="Markdown", proxy=proxy_url)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- ADMIN STATES (YANGILANGAN) ---
class AdminNode(StatesGroup):
    waiting_broadcast = State()
    waiting_pay_setup = State()
    waiting_target_id = State()    # Tezlik berish uchun ID
    waiting_speed_amount = State() # Tezlik miqdori

# --- 22 TA TIL ---
LANG_MAP = {
    'uz': '🇺🇿 UZ', 'en': '🇺🇸 EN', 'ru': '🇷🇺 RU', 'de': '🇩🇪 DE',
    'tr': '🇹🇷 TR', 'cn': '🇨🇳 CN', 'fr': '🇫🇷 FR', 'es': '🇪🇸 ES',
    'kr': '🇰🇷 KR', 'jp': '🇯🇵 JP', 'kz': '🇰🇿 KZ', 'kg': '🇰🇬 KG',
    'tj': '🇹🇯 TJ', 'tm': '🇹🇲 TM', 'ae': '🇦🇪 AE', 'it': '🇮🇹 IT',
    'in': '🇮🇳 IN', 'br': '🇧🇷 BR', 'vn': '🇻🇳 VN', 'id': '🇮🇩 ID',
    'ph': '🇵🇭 PH', 'az': '🇦🇿 AZ'
}

# --- BAZA ---
conn = sqlite3.connect('rruz_core.db', check_same_thread=False)
db = conn.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY, b REAL DEFAULT 0, lang TEXT DEFAULT 'uz', speed REAL DEFAULT 0.0000000001)''')
db.execute('''CREATE TABLE IF NOT EXISTS system_settings 
    (id INTEGER PRIMARY KEY, payment_data TEXT)''')
db.execute("INSERT OR IGNORE INTO system_settings (id, payment_data) VALUES (1, 'Hali kiritilmagan')")
conn.commit()

# --- KEYBOARDS ---

def main_menu(uid):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton(text="⛏ START MINING", web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.add(InlineKeyboardButton(text="💳 WALLET", callback_data="user_wallet"),
           InlineKeyboardButton(text="📊 STATS", callback_data="user_stats"))
    kb.add(InlineKeyboardButton(text="🎧 SUPPORT (ANONIM)", callback_data="ask_operator"))
    if int(uid) == ADMIN_ID:
        kb.add(InlineKeyboardButton(text="💎 SUPER ADMIN PANEL", callback_data="admin_root"))
    return kb

def admin_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(text="🚀 TEZLIK BERISH (MANUAL)", callback_data="adm_give_speed"),
        InlineKeyboardButton(text="📢 REKLAMA YUBORISH", callback_data="adm_broadcast"),
        InlineKeyboardButton(text="⚙️ HAMYONLARNI TAHRIRLASH", callback_data="adm_pay_set"),
        InlineKeyboardButton(text="👥 FOYDALANUVCHILAR SONI", callback_data="adm_count"),
        InlineKeyboardButton(text="🔙 ASOSIY MENYU", callback_data="back_home")
    )
    return kb

# --- HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def start_node(m: types.Message):
    db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (m.from_user.id,))
    conn.commit()
    kb = InlineKeyboardMarkup(row_width=3)
    btns = [InlineKeyboardButton(text=val, callback_data=f"setl_{key}") for key, val in LANG_MAP.items()]
    kb.add(*btns)
    await bot.send_photo(m.chat.id, BRAND_COIN_URL, caption=f"🪙 **RRuzcoin Node**\n_{SLOGAN}_", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('setl_'))
async def set_lang(c: types.CallbackQuery):
    lang = c.data.split('_')[1]
    db.execute("UPDATE users SET lang = ? WHERE id = ?", (lang, c.from_user.id))
    conn.commit()
    await bot.delete_message(c.from_user.id, c.message.message_id)
    await bot.send_photo(c.from_user.id, BRAND_COIN_URL, caption=f"✅ **Node Active**\n_{SLOGAN}_", reply_markup=main_menu(c.from_user.id))

# --- SUPER ADMIN FUNKSIYALARI ---

@dp.callback_query_handler(lambda c: c.data == "admin_root")
async def admin_panel(c: types.CallbackQuery):
    if c.from_user.id == ADMIN_ID:
        await bot.edit_message_caption(c.from_user.id, c.message.message_id, caption="🕹 **ADMIN BOSHQUV MARKAZI**", reply_markup=admin_kb())

# 1. Tezlik berish tizimi
@dp.callback_query_handler(lambda c: c.data == "adm_give_speed")
async def ask_user_id(c: types.CallbackQuery):
    await bot.send_message(ADMIN_ID, "👤 Foydalanuvchi ID raqamini kiriting:")
    await AdminNode.waiting_target_id.set()

@dp.message_handler(state=AdminNode.waiting_target_id)
async def ask_speed_amount(m: types.Message, state: FSMContext):
    await state.update_data(target_id=m.text)
    await m.answer("🚀 Qancha tezlik qo'shilsin? (Masalan: 0.0005):")
    await AdminNode.waiting_speed_amount.set()

@dp.message_handler(state=AdminNode.waiting_speed_amount)
async def finalize_speed(m: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data['target_id']
    try:
        new_speed = float(m.text)
        db.execute("UPDATE users SET speed = speed + ? WHERE id = ?", (new_speed, target_id))
        conn.commit()
        await m.answer(f"✅ ID: `{target_id}` ga {new_speed} tezlik qo'shildi!")
        await bot.send_message(target_id, f"🚀 **Tabriklaymiz!**\nAdmin tomonidan mining tezligingiz {new_speed} ga oshirildi!")
    except:
        await m.answer("❌ Xato: Raqam kiriting yoki ID noto'g'ri.")
    await state.finish()

# 2. Hamyonni sozlash
@dp.callback_query_handler(lambda c: c.data == "adm_pay_set")
async def pay_setup(c: types.CallbackQuery):
    await bot.send_message(ADMIN_ID, "💳 Hamyon/Karta ma'lumotlarini kiriting (Barcha turlarini yozish mumkin):")
    await AdminNode.waiting_pay_setup.set()

@dp.message_handler(state=AdminNode.waiting_pay_setup)
async def save_pay(m: types.Message, state: FSMContext):
    db.execute("UPDATE system_settings SET payment_data = ? WHERE id = 1", (m.text,))
    conn.commit()
    await m.answer("✅ Hamyonlar saqlandi.")
    await state.finish()

# --- FOYDALANUVCHI BO'LIMI ---

@dp.callback_query_handler(lambda c: c.data == "user_wallet")
async def wallet_info(c: types.CallbackQuery):
    db.execute("SELECT b FROM users WHERE id = ?", (c.from_user.id,))
    balance = db.fetchone()[0]
    db.execute("SELECT payment_data FROM system_settings WHERE id = 1")
    pay_info = db.fetchone()[0]
    text = f"💰 **HAMYONINGIZ**\n\nBalans: `{balance}` RRuz\n\n🚀 **Boost Speed:** Depozit qiling va chekni supportga yuboring:\n\n`{pay_info}`"
    await bot.send_message(c.from_user.id, text)

# --- ANONIM SUPPORT (FOYDALANUVCHI <-> ADMIN) ---

@dp.message_handler(content_types=['text', 'photo', 'voice', 'video'])
async def handle_messages(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        await bot.send_message(ADMIN_ID, f"📩 **Murojaat!**\nID: `{m.from_user.id}`")
        await m.copy_to(ADMIN_ID)
        await m.answer("✅ Yuborildi.")
    elif m.reply_to_message and m.from_user.id == ADMIN_ID:
        try:
            target_id = re.search(r'ID: `(\d+)`', m.reply_to_message.text or m.reply_to_message.caption).group(1)
            await bot.send_message(target_id, "🎧 **Operator javobi:**")
            await m.copy_to(target_id)
            await m.answer("✅ Javob yuborildi.")
        except:
            await m.answer("❌ ID topilmadi.")

@dp.callback_query_handler(lambda c: c.data == "back_home")
async def back_home(c: types.CallbackQuery):
    await bot.delete_message(c.from_user.id, c.message.message_id)
    await bot.send_photo(c.from_user.id, BRAND_COIN_URL, caption=f"✅ **Node Active**\n_{SLOGAN}_", reply_markup=main_menu(c.from_user.id))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
