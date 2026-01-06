import logging
import sqlite3
import json
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. KONFIGURATSIYA ---
API_TOKEN = '8550803046:AAHWhHvREEzYQV_Gi-9pyT5eX_xD7MKrpUA'
ADMIN_ID = 1424175786 
WEB_APP_URL = "https://rruzcoin.github.io/rruzcoin/" 
REF_BONUS = 0.0000100000 
BRAND_IMG = "https://raw.githubusercontent.com/rruzcoin/rruzcoin/main/IMG_20251231_141643_658.jpg"
SUPPORT_USER = "@RRuzcoin_Admin"

# --- 2. 22 TA TIL LUG'ATI ---
LANGS = {
    'uz': {'start': "💎 RRuzcoin: Uncontrolled cash — the path to transparency.\n\nNode: Faol ✅", 'mining': "⛏ Mining", 'wallet': "💳 Hamyon", 'dep': "🚀 Tezlik", 'stats': "📊 Statistika", 'card_msg': "💳 To'lov: `{}`"},
    'en': {'start': "💎 RRuzcoin: Uncontrolled cash — the path to transparency.\n\nNode: Active ✅", 'mining': "⛏ Mining", 'wallet': "💳 Wallet", 'dep': "🚀 Speed", 'stats': "📊 Stats", 'card_msg': "💳 Payment: `{}`"},
    'ru': {'start': "💎 RRuzcoin: Uncontrolled cash — path to transparency.\n\nНода: Активен ✅", 'mining': "⛏ Майнинг", 'wallet': "💳 Кошелек", 'dep': "🚀 Ускорить", 'stats': "📊 Статистика", 'card_msg': "💳 Карта: `{}`"},
    'de': {'start': "💎 RRuzcoin: Knotenstatus: Aktiv ✅", 'mining': "⛏ Bergbau", 'wallet': "💳 Brieftasche", 'dep': "🚀 Upgrade", 'stats': "📊 Stats", 'card_msg': "💳 Karte: `{}`"},
    'tr': {'start': "💎 RRuzcoin: Düğüm Durumu: Aktif ✅", 'mining': "⛏ Madencilik", 'wallet': "💳 Cüzdan", 'dep': "🚀 Hız", 'stats': "📊 İstatistik", 'card_msg': "💳 Kart: `{}`"},
    'cn': {'start': "💎 RRuzcoin: 节点状态: 活跃 ✅", 'mining': "⛏ 挖矿", 'wallet': "💳 钱包", 'dep': "🚀 提升", 'stats': "📊 统计", 'card_msg': "💳 付款卡: `{}`"},
    'fr': {'start': "💎 RRuzcoin: Statut du nœud: Actif ✅", 'mining': "⛏ Minage", 'wallet': "💳 Portefeuille", 'dep': "🚀 Booster", 'stats': "📊 Stats", 'card_msg': "💳 Carte: `{}`"},
    'es': {'start': "💎 RRuzcoin: Estado del nodo: Activo ✅", 'mining': "⛏ Minería", 'wallet': "💳 Billetera", 'dep': "🚀 Velocidad", 'stats': "📊 Stats", 'card_msg': "💳 Tarjeta: `{}`"},
    'kr': {'start': "💎 RRuzcoin: 노드 상태: 활성 ✅", 'mining': "⛏ 마이닝", 'wallet': "💳 지갑", 'dep': "🚀 속도", 'stats': "📊 통계", 'card_msg': "💳 카드: `{}`"},
    'jp': {'start': "💎 RRuzcoin: ノードの状態: アクティブ ✅", 'mining': "⛏ マイニング", 'wallet': "💳 ウォレット", 'dep': "🚀 速度", 'stats': "📊 統計", 'card_msg': "💳 カード: `{}`"},
    'kz': {'start': "💎 RRuzcoin: Node статусы: Белсенді ✅", 'mining': "⛏ Майнинг", 'wallet': "💳 Әмиян", 'dep': "🚀 Жылдамдық", 'stats': "📊 Статистика", 'card_msg': "💳 Карта: `{}`"},
    'kg': {'start': "💎 RRuzcoin: Node статусу: Активдүү ✅", 'mining': "⛏ Майнинг", 'wallet': "💳 Капчык", 'dep': "🚀 Ылдамдык", 'stats': "📊 Статистика", 'card_msg': "💳 Карта: `{}`"},
    'tj': {'start': "💎 RRuzcoin: Ҳолати Node: Фаъол ✅", 'mining': "⛏ Майнинг", 'wallet': "💳 ҳамён", 'dep': "🚀 Суръат", 'stats': "📊 Омор", 'card_msg': "💳 Корт: `{}`"},
    'tm': {'start': "💎 RRuzcoin: Node ýagdaýy: Aktiw ✅", 'mining': "⛏ Maýning", 'wallet': "💳 Gapjyk", 'dep': "🚀 Tizlik", 'stats': "📊 Statistika", 'card_msg': "💳 Kart: `{}`"},
    'ae': {'start': "💎 RRuzcoin: حالة العقدة: نشط ✅", 'mining': "⛏ التعدين", 'wallet': "💳 المحفظة", 'dep': "🚀 السرعة", 'stats': "📊 الإحصائيات", 'card_msg': "💳 البطاقة: `{}`"},
    'it': {'start': "💎 RRuzcoin: Stato del nodo: Attivo ✅", 'mining': "⛏ Mining", 'wallet': "💳 Portafoglio", 'dep': "🚀 Velocità", 'stats': "📊 Statistiche", 'card_msg': "💳 Carta: `{}`"},
    'in': {'start': "💎 RRuzcoin: नोड स्थिति: सक्रिय ✅", 'mining': "⛏ माइनिंग", 'wallet': "💳 वॉलेट", 'dep': "🚀 गति", 'stats': "📊 आंकड़े", 'card_msg': "💳 कार्ड: `{}`"},
    'br': {'start': "💎 RRuzcoin: Status do Nó: Ativo ✅", 'mining': "⛏ Mineração", 'wallet': "💳 Carteira", 'dep': "🚀 Velocidade", 'stats': "📊 Estatísticas", 'card_msg': "💳 Cartão: `{}`"},
    'vn': {'start': "💎 RRuzcoin: Trạng thái Node: Hoạt động ✅", 'mining': "⛏ Khai thác", 'wallet': "💳 Ví", 'dep': "🚀 Tăng tốc", 'stats': "📊 Thống kê", 'card_msg': "💳 Thẻ: `{}`"},
    'id': {'start': "💎 RRuzcoin: Status Node: Aktif ✅", 'mining': "⛏ Menambang", 'wallet': "💳 Dompet", 'dep': "🚀 Kecepatan", 'stats': "📊 Statistik", 'card_msg': "💳 Kartu: `{}`"},
    'ph': {'start': "💎 RRuzcoin: Status ng Node: Aktibo ✅", 'mining': "⛏ Pagmimina", 'wallet': "💳 Wallet", 'dep': "🚀 Bilis", 'stats': "📊 Stats", 'card_msg': "💳 Card: `{}`"},
    'az': {'start': "💎 RRuzcoin: Node statusu: Aktiv ✅", 'mining': "⛏ Mayninq", 'wallet': "💳 Pulqabı", 'dep': "🚀 Sürət", 'stats': "📊 Statistika", 'card_msg': "💳 Kart: `{}`"}
}

# --- 3. BAZA VA BOT ---
def db_query(query, params=(), fetchone=False, commit=False):
    with sqlite3.connect('rruz_official.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit: conn.commit()
        if fetchone: return cursor.fetchone()
        return cursor.fetchall()

def init_db():
    db_query("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, b REAL DEFAULT 0, lang TEXT DEFAULT 'uz', ref_id INTEGER, status TEXT DEFAULT 'active')", commit=True)
    db_query("CREATE TABLE IF NOT EXISTS admin_p (key TEXT PRIMARY KEY, val TEXT)", commit=True)
    db_query("INSERT OR IGNORE INTO admin_p VALUES ('pay_addr', 'Hali o‘rnatilmadi')", commit=True)

init_db()
bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

# --- 4. KLAVIATURALAR ---
def get_main_kb(uid, lang):
    tr = LANGS.get(lang, LANGS['uz'])
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton(text=tr['mining'], web_app=WebAppInfo(url=WEB_APP_URL)))
    kb.row(InlineKeyboardButton(text=tr['wallet'], callback_data="wlt"), InlineKeyboardButton(text=tr['stats'], callback_data="sts"))
    kb.row(InlineKeyboardButton(text="👥 DO'STLAR", callback_data="refs"), InlineKeyboardButton(text="🎧 SUPPORT", url=f"https://t.me/{SUPPORT_USER.replace('@','')}"))
    kb.add(InlineKeyboardButton(text="🌐 TILLAR / LANGUAGES", callback_data="ch_lang"))
    if int(uid) == ADMIN_ID:
        kb.add(InlineKeyboardButton(text="💎 SUPER ADMIN PANEL", callback_data="admin_root"))
    return kb

# --- 5. HANDLERLAR ---
@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    user = db_query("SELECT lang FROM users WHERE id = ?", (m.from_user.id,), fetchone=True)
    if not user:
        args = m.get_args()
        ref = int(args) if args.isdigit() else None
        db_query("INSERT INTO users (id, ref_id) VALUES (?, ?)", (m.from_user.id, ref), commit=True)
        kb = InlineKeyboardMarkup(row_width=4)
        kb.add(*[InlineKeyboardButton(text=l.upper(), callback_data=f"set_{l}") for l in LANGS.keys()])
        await m.answer("🌍 Choose Language / Tilni tanlang:", reply_markup=kb)
    else:
        lang = user[0]
        await bot.send_photo(m.from_user.id, BRAND_IMG, caption=LANGS[lang]['start'], reply_markup=get_main_kb(m.from_user.id, lang))

@dp.callback_query_handler(lambda c: c.data.startswith('set_'))
async def set_lang(c: types.CallbackQuery):
    lang = c.data.split('_')[1]
    db_query("UPDATE users SET lang = ? WHERE id = ?", (lang, c.from_user.id), commit=True)
    await c.message.delete()
    await bot.send_photo(c.from_user.id, BRAND_IMG, caption=LANGS[lang]['start'], reply_markup=get_main_kb(c.from_user.id, lang))

# Hamyon (Wallet) bo'limi
@dp.callback_query_handler(lambda c: c.data == "wlt")
async def wallet(c: types.CallbackQuery):
    user_data = db_query("SELECT b, lang FROM users WHERE id = ?", (c.from_user.id,), fetchone=True)
    addr = db_query("SELECT val FROM admin_p WHERE key = 'pay_addr'", fetchone=True)[0]
    msg = LANGS[user_data[1]]['card_msg'].format(addr)
    await bot.send_message(c.from_user.id, f"💰 Balance: `{user_data[0]:.10f} RRZC`\n\n{msg}")

# Mining Sync (MA'LUMOT SAQLASH)
@dp.message_handler(content_types=['web_app_data'])
async def sync(m: types.Message):
    data = json.loads(m.web_app_data.data)
    amount = float(data.get('mined', 0))
    db_query("UPDATE users SET b = b + ? WHERE id = ?", (amount, m.from_user.id), commit=True)
    await m.answer(f"✅ Synced! +{amount:.10f} RRZC")

# --- 6. SUPER ADMIN PANEL ---
@dp.callback_query_handler(lambda c: c.data == "admin_root")
async def super_adm(c: types.CallbackQuery):
    if c.from_user.id != ADMIN_ID: return
    users_count = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton(text="💳 Payment Setup", callback_data="adm_pay"),
           InlineKeyboardButton(text="📢 Broadcast", callback_data="adm_bc"),
           InlineKeyboardButton(text="👥 Manage Users", callback_data="adm_users"))
    await bot.send_message(ADMIN_ID, f"💎 **SUPER ADMIN PANEL**\n\nUsers: `{users_count}`", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "adm_pay")
async def adm_pay(c: types.CallbackQuery):
    await bot.send_message(ADMIN_ID, "Yangi to'lov manzilini (karta yoki hamyon) yuboring:\nFormat: `addr 8600...` yoki `addr USDT_...`")

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID and m.text.startswith("addr "))
async def save_addr(m: types.Message):
    new_addr = m.text.replace("addr ", "")
    db_query("UPDATE admin_p SET val = ? WHERE key = 'pay_addr'", (new_addr,), commit=True)
    await m.answer(f"✅ Yangi anonim to'lov manzili o'rnatildi:\n`{new_addr}`")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
