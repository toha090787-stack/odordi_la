import asyncio
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode

# Токен бота
API_TOKEN = '8584061439:AAE9rHB23CTeVpYJLeAdval4h_8AIvrUtqI'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Словарь для хранения выбранного режима пользователей (в памяти)
user_settings = {}

# Константы кнопок
BTN_OPTION_1 = "🔘 Вариант 1 (Позывные)"
BTN_OPTION_2 = "🔘 Вариант 2 (Ники на форуме)"

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_OPTION_1)],
            [KeyboardButton(text=BTN_OPTION_2)]
        ],
        resize_keyboard=True
    )
    return keyboard

def extract_data(text):
    # Разбиваем текст на блоки по слову "ФИО:"
    blocks = re.findall(r"(ФИО:.*?)(?=ФИО:|\Z)", text, re.DOTALL)
    
    results = {
        "callsigns": [],
        "callsign_phones": [],
        "nicks": [],
        "nick_phones": []
    }

    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        fio = re.search(r"ФИО:[ \t]*(.*)", block).group(1).strip() if re.search(r"ФИО:[ \t]*(.*)", block) else ""
        callsign = re.search(r"Позывной:[ \t]*(.*)", block).group(1).strip() if re.search(r"Позывной:[ \t]*(.*)", block) else ""
        phone = re.search(r"Телефон:[ \t]*(.*)", block).group(1).strip() if re.search(r"Телефон:[ \t]*(.*)", block) else "-"
        nick = re.search(r"Ник на форуме:[ \t]*(.*)", block).group(1).strip() if re.search(r"Ник на форуме:[ \t]*(.*)", block) else ""
        
        # Логика: если поле пустое или "-", подставляем ФИО
        display_callsign = callsign if (callsign and callsign != "-") else fio
        display_nick = nick if (nick and nick != "-") else fio
        
        if display_callsign:
            results["callsigns"].append(display_callsign)
            results["callsign_phones"].append(f"{display_callsign} {phone}")
        
        if display_nick:
            results["nicks"].append(display_nick)
            results["nick_phones"].append(f"{display_nick} {phone}")
            
    return results

@dp.message(Command("start"))
async def start(message: types.Message):
    # Устанавливаем режим по умолчанию, если не выбран
    if message.from_user.id not in user_settings:
        user_settings[message.from_user.id] = BTN_OPTION_1
        
    await message.answer(
        "<b>Привет!</b>\n\n1. Выберите вариант вывода кнопкой ниже.\n"
        "2. Пришлите список волонтеров.\n\n"
        f"<i>Сейчас выбран: {user_settings[message.from_user.id]}</i>",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML
    )

@dp.message(F.text.in_([BTN_OPTION_1, BTN_OPTION_2]))
async def change_mode(message: types.Message):
    # Сохраняем выбор пользователя
    user_settings[message.from_user.id] = message.text
    await message.answer(f"✅ Режим изменен на: <b>{message.text}</b>", parse_mode=ParseMode.HTML)

@dp.message(F.text)
async def process_list(message: types.Message):
    # Если в тексте нет ключевого слова "ФИО:", игнорируем или просим список
    if "ФИО:" not in message.text:
        return

    # Получаем текущий режим пользователя (по умолчанию Вариант 1)
    mode = user_settings.get(message.from_user.id, BTN_OPTION_1)
    
    data = extract_data(message.text)
    
    if not data["callsigns"]:
        await message.answer("Ошибка: не удалось извлечь данные. Проверьте формат.")
        return

    if mode == BTN_OPTION_1:
        # Сообщение 1: Список позывных
        await message.answer("<b>Список позывных</b>", parse_mode=ParseMode.HTML)
        await message.answer("\n".join(data["callsigns"]))
        
        # Сообщение 2: Позывной + телефон
        await message.answer("<b>Позывной + телефон</b>", parse_mode=ParseMode.HTML)
        await message.answer("\n".join(data["callsign_phones"]))
    
    else:
        # Сообщение 1: Список Ник на форуме
        await message.answer("<b>Список Ник на форуме</b>", parse_mode=ParseMode.HTML)
        await message.answer("\n".join(data["nicks"]))
        
        # Сообщение 2: Ник на форуме + телефон
        await message.answer("<b>Ник на форуме + телефон</b>", parse_mode=ParseMode.HTML)
        await message.answer("\n".join(data["nick_phones"]))

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
