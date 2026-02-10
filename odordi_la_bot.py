import asyncio
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode

# Токен бота
API_TOKEN = '8584061439:AAE9rHB23CTeVpYJLeAdval4h_8AIvrUtqI'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния для выбора режима
class Form(StatesGroup):
    choosing_mode = State()

# Кнопки выбора
def get_keyboard():
    buttons = [
        [KeyboardButton(text="Вариант 1: Позывные")],
        [KeyboardButton(text="Вариант 2: Ник на форуме")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def extract_data(text):
    blocks = re.findall(r"(ФИО:.*?)(?=ФИО:|\Z)", text, re.DOTALL)
    
    data = {
        "callsigns": [],
        "callsign_phones": [],
        "nicks": [],
        "nick_phones": []
    }

    for block in blocks:
        block = block.strip()
        if not block: continue
            
        fio = (re.search(r"ФИО:[ \t]*(.*)", block).group(1).strip() if re.search(r"ФИО:[ \t]*(.*)", block) else "")
        callsign = (re.search(r"Позывной:[ \t]*(.*)", block).group(1).strip() if re.search(r"Позывной:[ \t]*(.*)", block) else "")
        phone = (re.search(r"Телефон:[ \t]*(.*)", block).group(1).strip() if re.search(r"Телефон:[ \t]*(.*)", block) else "-")
        nick = (re.search(r"Ник на форуме:[ \t]*(.*)", block).group(1).strip() if re.search(r"Ник на форуме:[ \t]*(.*)", block) else "")
        
        # Логика для позывного
        display_callsign = callsign if callsign and callsign != "-" else fio
        # Логика для ника
        display_nick = nick if nick and nick != "-" else fio
        
        if display_callsign:
            data["callsigns"].append(display_callsign)
            data["callsign_phones"].append(f"{display_callsign} {phone}")
        
        if display_nick:
            data["nicks"].append(display_nick)
            data["nick_phones"].append(f"{display_nick} {phone}")
            
    return data

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.set_state(Form.choosing_mode)
    await message.answer(
        "Выберите вариант вывода результата:",
        reply_markup=get_keyboard()
    )

@dp.message(Form.choosing_mode, F.text.contains("Вариант"))
async def mode_selected(message: types.Message, state: FSMContext):
    await state.update_data(mode=message.text)
    await message.answer(f"Выбран: {message.text}. Теперь пришлите список волонтеров.")

@dp.message(F.text)
async def process_list(message: types.Message, state: FSMContext):
    if "ФИО:" not in message.text:
        await message.answer("Пришлите корректный список с полями 'ФИО:'")
        return

    user_data = await state.get_data()
    mode = user_data.get("mode", "Вариант 1: Позывные") # По умолчанию 1

    extracted = extract_data(message.text)

    if not extracted["callsigns"]:
        await message.answer("Данные не найдены.")
        return

    if "Вариант 1" in mode:
        # Отчет 1: Список позывных
        await message.answer("<b>Список позывных</b>", parse_mode=ParseMode.HTML)
        await message.answer("\n".join(extracted["callsigns"]))
        
        # Отчет 2: Позывной + телефон
        await message.answer("<b>Позывной + телефон</b>", parse_mode=ParseMode.HTML)
        await message.answer("\n".join(extracted["callsign_phones"]))
    
    else:
        # Отчет 1: Список Ник на форуме
        await message.answer("<b>Список Ник на форуме</b>", parse_mode=ParseMode.HTML)
        await message.answer("\n".join(extracted["nicks"]))
        
        # Отчет 2: Ник на форуме + телефон
        await message.answer("<b>Ник на форуме + телефон</b>", parse_mode=ParseMode.HTML)
        await message.answer("\n".join(extracted["nick_phones"]))

async def main():
    print("Бот Gemini 3 Flash запущен...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Работа завершена")
