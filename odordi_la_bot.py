import asyncio
import re
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.INFO)

API_TOKEN = '8584061439:AAE9rHB23CTeVpYJLeAdval4h_8AIvrUtqI'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния
class Form(StatesGroup):
    choosing_mode = State()      # Выбор режима (1, 2 или 3)
    waiting_for_list = State()   # Ожидание текста со списком (бесконечный цикл)

# Клавиатура выбора режима
def get_mode_keyboard():
    buttons = [
        [KeyboardButton(text="1. Позывной")],
        [KeyboardButton(text="2. Ник на форуме")],
        [KeyboardButton(text="3. ФИО")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Клавиатура "Назад", которая будет видна всегда при вводе списков
def get_back_keyboard():
    buttons = [
        [KeyboardButton(text="⬅️ Назад к выбору режима")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def extract_data(text, mode):
    # Разбиваем текст на блоки по слову "ФИО:"
    blocks = re.findall(r"(ФИО:.*?)(?=ФИО:|\Z)", text, re.DOTALL)
    
    names_only = []
    names_with_phones = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        fio = re.search(r"ФИО:[ \t]*([^\n]*)", block)
        callsign = re.search(r"Позывной:[ \t]*([^\n]*)", block)
        nick = re.search(r"Ник на форуме:[ \t]*([^\n]*)", block)
        phone = re.search(r"Телефон:[ \t]*([^\n]*)", block)
        
        fio_val = fio.group(1).strip() if fio else ""
        call_val = callsign.group(1).strip() if callsign else ""
        nick_val = nick.group(1).strip() if nick else ""
        phone_val = phone.group(1).strip() if phone else "-"

        # Очистка пустых значений
        if fio_val == "-": fio_val = ""
        if call_val == "-": call_val = ""
        if nick_val == "-": nick_val = ""

        display_name = ""
        if mode == 1:
            display_name = call_val if call_val else fio_val
        elif mode == 2:
            display_name = nick_val if nick_val else fio_val
        elif mode == 3:
            display_name = fio_val if fio_val else call_val
        
        if display_name:
            names_only.append(display_name)
            names_with_phones.append(f"{display_name} {phone_val}")
            
    return names_only, names_with_phones

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.set_state(Form.choosing_mode)
    await message.answer(
        "Выберите вариант вывода результата:",
        reply_markup=get_mode_keyboard()
    )

# Обработчик кнопки "Назад" (срабатывает в любом состоянии)
@dp.message(F.text == "⬅️ Назад к выбору режима")
async def back_to_selection(message: types.Message, state: FSMContext):
    await state.set_state(Form.choosing_mode)
    await message.answer(
        "Выберите новый режим вывода:",
        reply_markup=get_mode_keyboard()
    )

@dp.message(Form.choosing_mode, F.text.regexp(r"^\d\."))
async def mode_selected(message: types.Message, state: FSMContext):
    mode = int(message.text[0])
    await state.update_data(mode=mode)
    await state.set_state(Form.waiting_for_list)
    
    mode_names = {1: "Позывной", 2: "Ник на форуме", 3: "ФИО"}
    await message.answer(
        f"✅ Режим установлен: <b>{mode_names[mode]}</b>\n"
        f"Присылайте списки. Я буду обрабатывать их в этом формате.\n\n"
        f"Чтобы сменить формат, нажмите кнопку ниже 👇",
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )

@dp.message(Form.waiting_for_list, F.text)
async def process_list(message: types.Message, state: FSMContext):
    # Если это кнопка "Назад", она обработается специальным хендлером выше, 
    # но добавим проверку для надежности
    if message.text == "⬅️ Назад к выбору режима":
        return

    if "ФИО:" not in message.text:
        await message.answer(
            "⚠️ В тексте не найдены данные (нет поля 'ФИО:').\n"
            "Пожалуйста, скопируйте список корректно или смените режим.",
            reply_markup=get_back_keyboard()
        )
        return

    user_data = await state.get_data()
    mode = user_data.get('mode', 1)

    names, names_phones = extract_data(message.text, mode)

    if not names:
        await message.answer("Не удалось извлечь данные. Проверьте формат.")
        return

    # Заголовки в зависимости от режима
    h_single = {1: "Список позывных", 2: "Список ников на форуме", 3: "Список ФИО"}
    h_phones = {1: "Позывные + телефоны", 2: "Ники + телефоны", 3: "ФИО + телефоны"}

    # Отправка результатов
    await message.answer(f"<b>{h_single.get(mode)}:</b>\n\n" + "\n".join(names), parse_mode=ParseMode.HTML)
    await message.answer(f"<b>{h_phones.get(mode)}:</b>\n\n" + "\n".join(names_phones), parse_mode=ParseMode.HTML)
    
    # Мы НЕ меняем состояние и НЕ убираем клавиатуру. 
    # Пользователь может просто прислать следующий текст.
    await message.answer("👆 Готово. Можете прислать следующий список или сменить режим кнопкой «Назад».", 
                         reply_markup=get_back_keyboard())

async def main():
    print("Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
