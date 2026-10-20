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
    status TEXT DEFAULT 'pending',
    assigned_admin_id INTEGER DEFAULT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id INTEGER,
    sender_id INTEGER,
    sender_role TEXT,
    text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# --- FSM STATES ---
class ComplaintStates(StatesGroup):
    waiting_for_target_type = State()
    waiting_for_target_name = State()
    waiting_for_text = State()

class AdminChatState(StatesGroup):
    chatting = State()

class OwnerStates(StatesGroup):
    waiting_for_add_admin_id = State()
    waiting_for_remove_admin_id = State()

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

# --- KEYBOARDS ---
def main_keyboard(role: str):
    kb = [[KeyboardButton(text="📝 Подать жалобу")]]
    if role in ["admin", "owner"]:
        kb.append([KeyboardButton(text="📋 Жалобы на игроков")])
    if role == "owner":
        kb.append([KeyboardButton(text="👑 Жалобы на админов")])
        kb.append([KeyboardButton(text="⚙️ Управление админами"), KeyboardButton(text="📊 Все жалобы")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def target_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 На игрока", callback_data="type_player")],
        [InlineKeyboardButton(text="🛡 На администратора", callback_data="type_admin")]
    ])

def complaint_action_kb(complaint_id: int, status: str, assigned_admin_id: int, user_id: int):
    buttons = []
    if status == "pending":
        buttons.append([InlineKeyboardButton(text="🛠 Взять в работу", callback_data=f"take_{complaint_id}")])
    elif status == "in_progress":
        buttons.append([InlineKeyboardButton(text="💬 Ответить / Чат", callback_data=f"chat_{complaint_id}")])
        buttons.append([
            InlineKeyboardButton(text="✅ Принять", callback_data=f"status_accept_{complaint_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"status_reject_{complaint_id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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
        f"Привет, {message.from_user.first_name}!\n"
        f"Ваша роль: **{role.upper()}**\n\n"
        "Выберите действие в меню снизу:",
        reply_markup=main_keyboard(role),
        parse_mode="Markdown"
    )

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
    data = await state.get_data()
    user_id = message.from_user.id
    
    cursor.execute(
        "INSERT INTO complaints (user_id, target_type, target_name, text) VALUES (?, ?, ?, ?)",
        (user_id, data['target_type'], data['target_name'], message.text)
    )
    conn.commit()
    complaint_id = cursor.lastrowid
    
    await state.clear()
    await message.answer("✅ Ваша жалоба успешно отправлена и принята на рассмотрение!", reply_markup=main_keyboard(get_user_role(user_id, message.from_user.username or "")))
    
    target_str = "Игрока" if data['target_type'] == "player" else "Администратора"
    notify_text = f"🚨 **Новая жалоба #{complaint_id}** (На {target_str})\nОт: ID {user_id}\nНа кого: {data['target_name']}\n\nТекст: {message.text}"
    
    if data['target_type'] == "player":
        cursor.execute("SELECT user_id FROM users WHERE role IN ('admin', 'owner')")
        admins = cursor.fetchall()
        for adm in admins:
            try:
                await bot.send_message(adm[0], notify_text, parse_mode="Markdown")
            except Exception:
                pass
    else:
        cursor.execute("SELECT user_id FROM users WHERE role = 'owner'")
        owners = cursor.fetchall()
        for ow in owners:
            try:
                await bot.send_message(ow[0], notify_text, parse_mode="Markdown")
            except Exception:
                pass

@router.message(F.text == "📋 Жалобы на игроков")
async def list_player_complaints(message: Message):
    role = get_user_role(message.from_user.id, message.from_user.username or "")
    if role not in ["admin", "owner"]:
        return

    cursor.execute("SELECT id, user_id, target_name, text, status, assigned_admin_id FROM complaints WHERE target_type = 'player' AND (status = 'pending' OR assigned_admin_id = ?)", (message.from_user.id,))
    rows = cursor.fetchall()
    
    if not rows:
        await message.answer("📭 Доступных открытых жалоб на игроков нет.")
        return
        
    for row in rows:
        cid, uid, tname, text, status, admin_id = row
        st_text = "Ожидает" if status == "pending" else "В работе"
        msg = f"📌 **Жалоба #{cid}** [{st_text}]\nИгрок: {tname}\nОт ID: {uid}\nТекст: {text}"
        await message.answer(msg, reply_markup=complaint_action_kb(cid, status, admin_id, message.from_user.id), parse_mode="Markdown")

@router.message(F.text == "👑 Жалобы на админов")
async def list_admin_complaints(message: Message):
    role = get_user_role(message.from_user.id, message.from_user.username or "")
    if role != "owner":
        return

    cursor.execute("SELECT id, user_id, target_name, text, status, assigned_admin_id FROM complaints WHERE target_type = 'admin'")
    rows = cursor.fetchall()
    
    if not rows:
        await message.answer("📭 Жалоб на администраторов нет.")
        return
        
    for row in rows:
        cid, uid, tname, text, status, admin_id = row
        st_map = {"pending": "Ожидает", "in_progress": "В работе", "accepted": "Принята", "rejected": "Отклонена"}
        msg = f"🛡 **Жалоба на Админа #{cid}** [{st_map.get(status, status)}]\nАдмин: {tname}\nОт ID: {uid}\nТекст: {text}"
        await message.answer(msg, reply_markup=complaint_action_kb(cid, status, admin_id, message.from_user.id), parse_mode="Markdown")

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

@router.callback_query(F.data.startswith("take_"))
async def take_complaint(callback: CallbackQuery):
    cid = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id
    
    cursor.execute("SELECT status FROM complaints WHERE id = ?", (cid,))
    row = cursor.fetchone()
    if not row or row[0] != "pending":
        await callback.answer("Эта жалоба уже взята другим администратором!", show_alert=True)
        return
        
    cursor.execute("UPDATE complaints SET status = 'in_progress', assigned_admin_id = ? WHERE id = ?", (admin_id, cid))
    conn.commit()
    
    await callback.answer("Вы успешно взяли жалобу в работу!")
    await callback.message.edit_text(callback.message.text + "\n\n🛠 **Статус:** Взята в работу вами.", reply_markup=complaint_action_kb(cid, "in_progress", admin_id, admin_id), parse_mode="Markdown")

@router.callback_query(F.data.startswith("chat_"))
async def open_complaint_chat(callback: CallbackQuery, state: FSMContext):
    cid = int(callback.data.split("_")[1])
    await state.set_state(AdminChatState.chatting)
    await state.update_data(active_complaint_id=cid)
    
    await callback.message.answer(f"💬 Вы вошли в чат по жалобе #{cid}.\nВсе ваши следующие текстовые сообщения будут отправляться автору жалобы.\n\nЧтобы закончить/закрыть диалог, измените статус жалобы на Принято/Отклонено.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Выйти из чата жалобы")]], resize_keyboard=True))
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
            await message.answer(f"Сообщение успешно отправлено пользователю!")
        except Exception as e:
            await message.answer(f"Ошибка при отправке сообщения: {e}")

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

    await callback.message.edit_text(callback.message.text + f"\n\nРешение: **{status_ru}**", parse_mode="Markdown")
    await callback.answer("Статус жалобы обновлен!")

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
    await callback.message.answer("Введите Telegram ID пользователя, которому нужно выдать админку:")
    await callback.answer()

@router.message(OwnerStates.waiting_for_add_admin_id)
async def process_add_admin(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
        set_user_role(uid, "admin")
        await state.clear()
        await message.answer(f"✅ Пользователь с ID `{uid}` успешно назначен Администратором!", parse_mode="Markdown")
    except ValueError:
        await message.answer("Пожалуйста, введите корректный числовой Telegram ID.")

@router.callback_query(F.data == "remove_admin")
async def start_remove_admin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OwnerStates.waiting_for_remove_admin_id)
    await callback.message.answer("Введите Telegram ID администратора, у которого нужно забрать права:")
    await callback.answer()

@router.message(OwnerStates.waiting_for_remove_admin_id)
async def process_remove_admin(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
        set_user_role(uid, "player")
        await state.clear()
        await message.answer(f"🚫 У пользователя с ID `{uid}` забраны права администратора.", parse_mode="Markdown")
    except ValueError:
        await message.answer("Пожалуйста, введите корректный числовой Telegram ID.")

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
