import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8772602783:AAGo0VjMq-KdG4iqp8VG5XoqLJjVDYDCPUw"
OWNER_USERNAME = "Onqirs"  # Ник владельца без @
# -----------------------------------------------

logging.basicConfig(level=logging.INFO)

# --- DEFAULT RULES TEXT ---
DEFAULT_RULES = """📜 **ПРАВИЛА СЕРВЕРА ДЕРЕВЕНСК РП**

1.1 ДМ (Deathmatch)
- Первое нарушение: мут 1 час + кик.
- Повторное (в течение 7 дней): бан 1 день.
- Третье (в течение 14 дней): бан 3 дня.
- Систематика (4+): перманентный бан.

1.2 МДМ (Mass Deathmatch)
- Первое нарушение: бан 3 дня (без предупреждения).
- Повторное: бан 7 дней.
- Третье: перманентный бан.

1.3 ПДМ (Провокация ради ДМ)
- Первое нарушение: мут 2 часа + кик.
- Повторное: бан 1 день.
- Третье: бан 3 дня.

1.4 ДБ (Driveby)
- Первое нарушение: мут 1 час + кик.
- Повторное: бан 1 день.
- Систематика: бан 3 дня.

1.5 СК (Spawnkill)
- Первое нарушение: бан 1 день.
- Повторное: бан 3 дня.
- Третье: бан 7 дней.

1.6 РК (Revenge Kill)
- Первое нарушение: предупреждение + кик.
- Повторное: мут 2 часа.
- Третье: бан 1 день.

1.7 ТК (Team Kill)
- Первое нарушение: мут 30 минут.
- Повторное: мут 2 часа.
- Третье: бан 1 день.

1.8 КНС (Kill No Scene)
- Первое нарушение: мут 1 час.
- Повторное: бан 1 день.
- Третье: бан 3 дня.

2.1 МГ (Metagaming)
- Лёгкое (1–2 фразы): предупреждение + мут 15 минут.
- Использование инфы для преимущества: мут 1 час + кик.
- Рецидив: бан 1 день.

2.2 НРП (Non-RP поведение)
- Единичный случай: предупреждение.
- Намеренное нарушение логики мира: мут 1 час.
- Систематика: бан 1–3 дня.

2.3 Годмод (Godmodding)
- Первое нарушение: мут 30 минут + требование отыграть последствия.
- Повторное: мут 2 часа + бан 1 день.
- Серия случаев (3+ за 7 дней): бан 7 дней.

2.4 ПГ (Powergaming)
- Первое нарушение: предупреждение + мут 15 минут.
- Повторное: мут 1 час.
- Третье: бан 1 день.

2.5 ФРП (Force RP)
- Первое нарушение: мут 30 минут + отмена сцены.
- Повторное: мут 2 часа.
- Третье: бан 1 день.

2.6 БХ (Bunnyhop)
- Первое нарушение: кик + предупреждение.
- Повторное: мут 1 час.
- Третье: бан 1 день.

3.1 Дюп (копирование предметов/денег)
- Любой случай: бан 7 дней + конфискация всех дюпнутых ресурсов.
- Рецидив: перманентный бан.

3.4 Спидхак / Флайхак
- Первое нарушение: бан 3 дня.
- Повторное: перманентный бан.

3.5 Аимбот / Aimlock
- Любой случай: перманентный бан (без предупреждения).

3.6 Телепорт / Telehack
- Первое нарушение: бан 3 дня.
- Повторное: перманентный бан.

3.7 Невидимка / Инвисклон
- Любой случай: бан 7 дней.
- Рецидив: перманентный бан.

3.8 Афк-ферма (макросы, автокликеры)
- Первое нарушение: кик + обнуление заработанного.
- Повторное: бан 1 день.
- Третье: бан 3 дня.

3.9 Лаг-эксплойт (Lag Switch)
- Первое нарушение: бан 1 день.
- Повторное: бан 7 дней.
- Третье: перманентный бан.

3.10 Сокрытие багоузов
- Знание о баге и молчание: предупреждение.
- Использование и сокрытие: бан 3 дня.
- Сообщение о баге администрации: безнаказанно (поощряется).

4.1 Оск (оскорбление игрока вне роли) (оск родных наказывается смотря на сколько жестоко оскорбление)
- Первое нарушение: мут 30 минут.
- Повторное (в течение 7 дней): мут 4 часа.
- Третье: бан 1 день.
- Систематика: бан 3 дня.

4.2 Оск. адм (оскорбление администрации)
- Первое нарушение: мут 2 часа.
- Повторное: бан 1 день.
- Третье: бан 3 дня.

4.3 Провок (целенаправленная провокация на нарушение)
- Первое нарушение: мут 1 час.
- Повторное: мут 4 часа.
- Третье: бан 1 день.

4.4 Буллинг (систематическое травление игрока)
- Первое нарушение: бан 1 день.
- Повторное: бан 7 дней.
- Третье: перманентный бан.

4.5 Дискрим (дискриминация по расе, полу, религии, национальности)
- Первое нарушение: бан 1 день.
- Повторное: бан 7 дней.
- Третье: перманентный бан.

4.6 Угроза ОЖ (угрозы реальной жизнью/здоровьем)
- Первое нарушение: перманентный бан (без исключений).

4.7 Докс (распространение личных данных)
- Первое нарушение: перманентный бан (без исключений).

4.8 Троллинг (разрушение ролевых сцен без цели играть)
- Первое нарушение: кик + предупреждение.
- Повторное: мут 2 часа.
- Третье: бан 1 день.
- Систематика: бан 3 дня.

4.9 Мн. акк (мультиаккаунт для обхода бана)
- Основной аккаунт: увеличение бана вдвое.
- Дополнительные аккаунты: перманентный бан всех.

5.1 Спам / Капс
- Спам (3+ одинаковых сообщения): мут 15 минут.
- Капс (50%+ заглавными): мут 10 минут.
- Рецидив: мут 1 час.

5.2 Реклама (сторонние проекты, ссылки, Discord без разрешения)
- Первое нарушение: мут 1 час + удаление сообщения.
- Повторное: бан 1 день.
- Третье: бан 3 дня.

5.3 Читинг (сторонние программы, инжекторы, эксплойты)
- Любой случай: перманентный бан (без предупреждения).

5.4 НРП‑форма (несоответствие внешнего вида роли)
НРП‑форма — это несоответствие экипировки, униформы или внешнего вида персонажа его роли, профессии и сеттингу сервера.
Шкала наказаний:
- Первое нарушение: предупреждение + требование переодеться.
- Повторное (в течение 7 дней): мут 30 минут + кик.
- Третье: мут 2 часа + бан 1 день.
- Систематика (4+): бан 3 дня + снятие с должности."""

# --- DATABASE SETUP ---
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    role TEXT DEFAULT 'player'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    target_type TEXT,
    target_name TEXT,
    text TEXT,
    video_file_id TEXT,
    status TEXT DEFAULT 'pending',
    assigned_admin_id INTEGER DEFAULT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    media_type TEXT,
    file_id TEXT
)
""")

cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('rules', ?)", (DEFAULT_RULES,))
conn.commit()

# --- FSM STATES ---
class ComplaintStates(StatesGroup):
    waiting_for_target_type = State()
    waiting_for_target_name = State()
    waiting_for_text = State()
    waiting_for_video = State()

class AdminChatState(StatesGroup):
    chatting = State()

class OwnerStates(StatesGroup):
    waiting_for_add_admin_id = State()
    waiting_for_remove_admin_id = State()
    waiting_for_new_rules = State()
    waiting_for_new_news = State()
    waiting_for_broadcast = State()

# --- HELPERS ---
def get_user_role(user_id: int, username: str = "") -> str:
    if username and username.lower() == OWNER_USERNAME.lower():
        return "owner"
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        if row[0] == "owner":
            return "owner"
        return row[0]
    return "player"

def set_user_role(user_id: int, role: str):
    cursor.execute("INSERT INTO users (user_id, role) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET role=?", (user_id, role, role))
    conn.commit()

def get_setting(key: str) -> str:
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else ""

def set_setting(key: str, value: str):
    cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?", (key, value, value))
    conn.commit()

# --- KEYBOARDS ---
def main_keyboard(role: str):
    kb = [
        [KeyboardButton(text="📝 Подать жалобу")],
        [KeyboardButton(text="📜 Правила"), KeyboardButton(text="📰 Новости")]
    ]
    if role in ["admin", "owner"]:
        kb.append([KeyboardButton(text="📋 Жалобы на игроков")])
    if role == "owner":
        kb.append([KeyboardButton(text="👑 Жалобы на админов")])
        kb.append([KeyboardButton(text="⚙️ Управление админами"), KeyboardButton(text="📊 Все жалобы")])
        kb.append([KeyboardButton(text="✏️ Изменить правила"), KeyboardButton(text="➕ Добавить новость")])
        kb.append([KeyboardButton(text="📢 Объявление (Рассылка)")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def target_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 На игрока", callback_data="type_player")],
        [InlineKeyboardButton(text="🛡 На администратора", callback_data="type_admin")]
    ])

def complaint_in_work_kb(complaint_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ответить / Чат", callback_data=f"chat_{complaint_id}")],
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"status_accept_{complaint_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"status_reject_{complaint_id}")
        ]
    ])

# --- ROUTER SETUP ---
router = Router()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

# --- HANDLERS ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    role = get_user_role(user_id, username)
    if username.lower() == OWNER_USERNAME.lower() and role != "owner":
        set_user_role(user_id, "owner")
        role = "owner"
    else:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, role) VALUES (?, ?, ?)", (user_id, username, role))
        conn.commit()

    await message.answer(
        f"Добро пожаловать в бота Деревенск рп.\n\n"
        f"Ваша роль: **{role.upper()}**\n"
        "Выберите действие в меню снизу:",
        reply_markup=main_keyboard(role),
        parse_mode="Markdown"
    )

# --- RULES & NEWS ---
@router.message(F.text == "📜 Правила")
async def show_rules(message: Message):
    rules_text = get_setting("rules")
    if len(rules_text) > 4000:
        for x in range(0, len(rules_text), 4000):
            await message.answer(rules_text[x:x+4000], parse_mode="Markdown")
    else:
        await message.answer(rules_text, parse_mode="Markdown")

@router.message(F.text == "📰 Новости")
async def show_news(message: Message):
    cursor.execute("SELECT text, media_type, file_id FROM news ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        await message.answer("📰 **Свежие новости Деревенск РП:**\n\nПока свежих новостей нет.")
        return
        
    text_val, media_type, file_id = row
    caption_text = f"📰 **Свежие новости Деревенск РП:**\n\n{text_val or ''}"
    
    if media_type == "photo":
        await message.answer_photo(file_id, caption=caption_text, parse_mode="Markdown")
    elif media_type == "video":
        await message.answer_video(file_id, caption=caption_text, parse_mode="Markdown")
    else:
        await message.answer(caption_text, parse_mode="Markdown")

# --- OWNER EDIT RULES & NEWS & BROADCAST ---
@router.message(F.text == "✏️ Изменить правила")
async def edit_rules_start(message: Message, state: FSMContext):
    if get_user_role(message.from_user.id, message.from_user.username or "") != "owner":
        return
    await state.set_state(OwnerStates.waiting_for_new_rules)
    await message.answer("Отправьте новый текст правил сервера:")

@router.message(OwnerStates.waiting_for_new_rules)
async def process_new_rules(message: Message, state: FSMContext):
    set_setting("rules", message.text)
    await state.clear()
    await message.answer("✅ Правила сервера успешно обновлены!", reply_markup=main_keyboard("owner"))

@router.message(F.text == "➕ Добавить новость")
async def add_news_start(message: Message, state: FSMContext):
    if get_user_role(message.from_user.id, message.from_user.username or "") != "owner":
        return
    await state.set_state(OwnerStates.waiting_for_new_news)
    await message.answer("Отправьте новость (это может быть текст, фото с подписью или видео с подписью):")

@router.message(OwnerStates.waiting_for_new_news)
async def process_new_news(message: Message, state: FSMContext):
    text_val = message.caption if message.caption else message.text
    media_type = "text"
    file_id = None
    
    if message.photo:
        media_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        file_id = message.video.file_id
        
    cursor.execute("INSERT INTO news (text, media_type, file_id) VALUES (?, ?, ?)", (text_val, media_type, file_id))
    conn.commit()
    
    await state.clear()
    await message.answer("✅ Новость успешно опубликована!", reply_markup=main_keyboard("owner"))

@router.message(F.text == "📢 Объявление (Рассылка)")
async def broadcast_start(message: Message, state: FSMContext):
    if get_user_role(message.from_user.id, message.from_user.username or "") != "owner":
        return
    await state.set_state(OwnerStates.waiting_for_broadcast)
    await message.answer("📢 Отправьте объявление для рассылки всем игрокам (любой формат: текст, фото, видео, кружочек и т.д.):")

@router.message(OwnerStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    await state.clear()
    
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    
    count = 0
    await message.answer("🚀 Рассылка запущена...")
    for u in users:
        try:
            await message.copy_to(chat_id=u[0])
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
            
    await message.answer(f"✅ Рассылка завершена! Сообщение получили {count} пользователей.", reply_markup=main_keyboard("owner"))

# --- COMPLAINT SUBMISSION FLOW ---
@router.message(F.text == "📝 Подать жалобу")
async def start_complaint(message: Message, state: FSMContext):
    await state.set_state(ComplaintStates.waiting_for_target_type)
    await message.answer("Кого вы хотите указать в жалобе?", reply_markup=target_type_kb())

@router.callback_query(ComplaintStates.waiting_for_target_type, F.data.startswith("type_"))
async def process_target_type(callback: CallbackQuery, state: FSMContext):
    target_type = "player" if callback.data == "type_player" else "admin"
    await state.update_data(target_type=target_type)
    await state.set_state(ComplaintStates.waiting_for_target_name)
    
    label = "игрока" if target_type == "player" else "администратора"
    await callback.message.edit_text(f"Введите ник или ID {label}, на которого подаете жалобу:")
    await callback.answer()

@router.message(ComplaintStates.waiting_for_target_name)
async def process_target_name(message: Message, state: FSMContext):
    await state.update_data(target_name=message.text)
    await state.set_state(ComplaintStates.waiting_for_text)
    await message.answer("Опишите подробнее вашу жалобу (суть нарушения):")

@router.message(ComplaintStates.waiting_for_text)
async def process_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(ComplaintStates.waiting_for_video)
    await message.answer("⚠️ **Обязательно прикрепите видео-доказательство** (отправьте видеофайлом или кружочком/видео):")

@router.message(ComplaintStates.waiting_for_video, F.video | F.document)
async def process_video(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    
    video_id = message.video.file_id if message.video else message.document.file_id
    
    cursor.execute(
        "INSERT INTO complaints (user_id, target_type, target_name, text, video_file_id) VALUES (?, ?, ?, ?, ?)",
        (user_id, data['target_type'], data['target_name'], data['text'], video_id)
    )
    conn.commit()
    complaint_id = cursor.lastrowid
    
    await state.clear()
    await message.answer(f"✅ Ваша жалоба **#{complaint_id}** успешно создана и отправлена в систему!", reply_markup=main_keyboard(get_user_role(user_id, message.from_user.username or "")))

@router.message(ComplaintStates.waiting_for_video)
async def process_wrong_video(message: Message):
    await message.answer("❌ Без видео-доказательства жалоба не может быть принята. Пожалуйста, отправьте видеофайл.")

# --- COMPLAINTS LISTS & TAKING BY NUMBER ---
@router.message(F.text == "📋 Жалобы на игроков")
async def list_player_complaints(message: Message):
    role = get_user_role(message.from_user.id, message.from_user.username or "")
    if role not in ["admin", "owner"]:
        return

    cursor.execute("SELECT id, user_id, target_name, text FROM complaints WHERE target_type = 'player' AND status = 'pending'")
    pending_rows = cursor.fetchall()

    cursor.execute("SELECT id, user_id, target_name, text FROM complaints WHERE target_type = 'player' AND status = 'in_progress' AND assigned_admin_id = ?", (message.from_user.id,))
    my_in_progress_rows = cursor.fetchall()
    
    if not pending_rows and not my_in_progress_rows:
        await message.answer("📭 На данный момент нет доступных открытых жалоб.")
        return

    text_msg = "📋 **СПИСОК ЖАЛОБ НА ИГРОКОВ**\n\n"
    
    if pending_rows:
        text_msg += "⏳ **Ожидают рассмотрения (свободные):**\n"
        for r in pending_rows:
            text_msg += f"• **Жалоба #{r[0]}** | На игрока: `{r[2]}`\n  Суть: _{r[3]}_\n\n"
            
    if my_in_progress_rows:
        text_msg += "🛠 **Взяты в работу вами:**\n"
        for r in my_in_progress_rows:
            text_msg += f"• **Жалоба #{r[0]}** | На игрока: `{r[2]}`\n\n"

    text_msg += "👉 **Чтобы взять жалобу в работу, просто отправьте её номер цифрами в чат** (например: `123`):"
    await message.answer(text_msg, parse_mode="Markdown")

@router.message(F.text == "👑 Жалобы на админов")
async def list_admin_complaints(message: Message):
    role = get_user_role(message.from_user.id, message.from_user.username or "")
    if role != "owner":
        return

    cursor.execute("SELECT id, user_id, target_name, text, status FROM complaints WHERE target_type = 'admin'")
    rows = cursor.fetchall()
    
    if not rows:
        await message.answer("📭 Жалоб на администраторов нет.")
        return
        
    text_msg = "🛡 **СПИСОК ЖАЛОБ НА АДМИНИСТРАТОРОВ**\n\n"
    for r in rows:
        st_map = {"pending": "Ожидает", "in_progress": "В работе", "accepted": "Принята", "rejected": "Отклонена"}
        text_msg += f"• **Жалоба #{r[0]}** [{st_map.get(r[4], r[4])}] | На админа: `{r[2]}`\n  Суть: _{r[3]}_\n\n"

    text_msg += "👉 **Чтобы открыть жалобу, отправьте её номер цифрами в чат:**"
    await message.answer(text_msg, parse_mode="Markdown")

# --- HANDLER FOR NUMBERS (TAKING A COMPLAINT BY ID) ---
@router.message(F.text.isdigit())
async def process_complaint_id_input(message: Message):
    role = get_user_role(message.from_user.id, message.from_user.username or "")
    if role not in ["admin", "owner"]:
        return

    complaint_id = int(message.text.strip())
    
    cursor.execute("SELECT id, user_id, target_type, target_name, text, video_file_id, status, assigned_admin_id FROM complaints WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()
    
    if not row:
        await message.answer(f"❌ Жалоба с номером **#{complaint_id}** не найдена.", parse_mode="Markdown")
        return
        
    cid, author_id, target_type, target_name, text_val, vid, status, admin_id = row

    if target_type == "admin" and role != "owner":
        await message.answer("⛔ Жалобы на администраторов может рассматривать только Владелец.")
        return

    if status == "pending":
        cursor.execute("UPDATE complaints SET status = 'in_progress', assigned_admin_id = ? WHERE id = ?", (message.from_user.id, cid))
        conn.commit()
        status = "in_progress"
        admin_id = message.from_user.id
        
        try:
            await bot.send_message(author_id, f"🛠 **Ваша жалоба #{cid} взята в работу администратором!**\nОжидайте вердикта или ответа в этом чате.", parse_mode="Markdown")
        except Exception:
            pass
            
        await message.answer(f"✅ Вы успешно взяли в работу жалобу **#{cid}**! Игроку отправлено уведомление.", parse_mode="Markdown")
    elif status == "in_progress" and admin_id != message.from_user.id and role != "owner":
        await message.answer(f"⚠️ Жалобу #{cid} уже рассматривает другой администратор.")
        return

    st_text = "В работе" if status == "in_progress" else "Ожидает"
    caption_text = f"📌 **Карточка жалобы #{cid}** [{st_text}]\nКому: {target_name}\nОт ID: {author_id}\n\nСуть: {text_val}"
    
    if vid:
        await message.answer_video(vid, caption=caption_text, reply_markup=complaint_in_work_kb(cid), parse_mode="Markdown")
    else:
        await message.answer(caption_text, reply_markup=complaint_in_work_kb(cid), parse_mode="Markdown")

@router.message(F.text == "📊 Все жалобы")
async def owner_all_complaints(message: Message):
    role = get_user_role(message.from_user.id, message.from_user.username or "")
    if role != "owner":
        return

    cursor.execute("SELECT id, target_type, target_name, status, assigned_admin_id FROM complaints ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    
    if not rows:
        await message.answer("Список жалоб пуст.")
        return

    res = "📊 **Вся история и статус жалоб:**\n\n"
    for r in rows:
        res += f"• **#{r[0]}** ({'Админ' if r[1]=='admin' else 'Игрок'} {r[2]}) - Статус: `{r[3]}` (Админ ID: {r[4] or 'Нет'})\n"
    await message.answer(res, parse_mode="Markdown")

# --- ACTIONS IN CHAT AND CHANGE STATUS ---
@router.callback_query(F.data.startswith("chat_"))
async def open_complaint_chat(callback: CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[1])
    await state.set_state(AdminChatState.chatting)
    await state.update_data(active_complaint_id=cid)
    
    await callback.message.answer(f"💬 Вы вошли в чат по жалобе #{cid}.\nВсе ваши текстовые сообщения будут отправляться автору жалобы.\n\nЧтобы выйти, нажмите кнопку ниже.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Выйти из чата жалобы")]], resize_keyboard=True))
    await callback.answer()

@router.message(AdminChatState.chatting)
async def process_chat_message(message: Message, state: FSMContext):
    if message.text == "❌ Выйти из чата жалобы":
        role = get_user_role(message.from_user.id, message.from_user.username or "")
        await state.clear()
        await message.answer("Вы вышли из режима чата.", reply_markup=main_keyboard(role))
        return

    data = await state.get_data()
    cid = data.get("active_complaint_id")
    
    cursor.execute("SELECT user_id FROM complaints WHERE id = ?", (cid,))
    row = cursor.fetchone()
    if row:
        target_user_id = row[0]
        try:
            await bot.send_message(target_user_id, f"💬 **Ответ от администрации по вашей жалобе #{cid}:**\n\n{message.text}", parse_mode="Markdown")
            await message.answer("Сообщение успешно отправлено пользователю!")
        except Exception as e:
            await message.answer(f"Ошибка при отправке: {e}")

@router.callback_query(F.data.startswith("status_"))
async def change_status(callback: CallbackQuery):
    action, cid = callback.data.split("_")[1], int(callback.data.split("_")[2])
    new_status = "accepted" if action == "accept" else "rejected"
    status_ru = "✅ Принято" if action == "accept" else "❌ Отклонено"
    
    cursor.execute("UPDATE complaints SET status = ? WHERE id = ?", (new_status, cid))
    cursor.execute("SELECT user_id FROM complaints WHERE id = ?", (cid,))
    conn.commit()
    
    row = cursor.fetchone()
    if row:
        try:
            await bot.send_message(row[0], f"📢 **Статус вашей жалобы #{cid} изменен:** {status_ru}", parse_mode="Markdown")
        except Exception:
            pass

    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + f"\n\nРешение: **{status_ru}**", parse_mode="Markdown")
    else:
        await callback.message.edit_text(callback.message.text + f"\n\nРешение: **{status_ru}**", parse_mode="Markdown")
    await callback.answer("Статус жалобы обновлен!")

# --- OWNER ADMIN MANAGEMENT ---
@router.message(F.text == "⚙️ Управление админами")
async def owner_manage_admins(message: Message):
    role = get_user_role(message.from_user.id, message.from_user.username or "")
    if role != "owner":
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать админку (по ID)", callback_data="add_admin")],
        [InlineKeyboardButton(text="➖ Забрать админку (по ID)", callback_data="remove_admin")],
        [InlineKeyboardButton(text="📜 Список администраторов", callback_data="list_admins")]
    ])
    await message.answer("Панель управления администраторами:", reply_markup=kb)

@router.callback_query(F.data == "add_admin")
async def start_add_admin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OwnerStates.waiting_for_add_admin_id)
    await callback.message.answer("Введите Telegram ID пользователя:")
    await callback.answer()

@router.message(OwnerStates.waiting_for_add_admin_id)
async def process_add_admin(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
        set_user_role(uid, "admin")
        await state.clear()
        await message.answer(f"✅ Пользователь с ID `{uid}` теперь Администратор!", parse_mode="Markdown")
    except ValueError:
        await message.answer("Введите корректный числовой Telegram ID.")

@router.callback_query(F.data == "remove_admin")
async def start_remove_admin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OwnerStates.waiting_for_remove_admin_id)
    await callback.message.answer("Введите Telegram ID администратора:")
    await callback.answer()

@router.message(OwnerStates.waiting_for_remove_admin_id)
async def process_remove_admin(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
        set_user_role(uid, "player")
        await state.clear()
        await message.answer(f"🚫 У пользователя с ID `{uid}` забраны права.", parse_mode="Markdown")
    except ValueError:
        await message.answer("Введите корректный числовой Telegram ID.")

@router.callback_query(F.data == "list_admins")
async def list_admins_call(callback: CallbackQuery):
    cursor.execute("SELECT user_id, username FROM users WHERE role = 'admin'")
    rows = cursor.fetchall()
    
    if not rows:
        await callback.message.answer("Список администраторов пуст.")
    else:
        msg = "📜 **Список администраторов:**\n\n"
        for r in rows:
            msg += f"• ID: `{r[0]}` | Username: @{r[1] or 'Нет'}\n"
        await callback.message.answer(msg, parse_mode="Markdown")
    await callback.answer()

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
