import asyncio
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# Токен бота
API_TOKEN = settings.API_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def extract_data(text):
    # Разбиваем текст на блоки по слову "ФИО:"
    blocks = re.findall(r"(ФИО:.*?)(?=ФИО:|\Z)", text, re.DOTALL)
    
    callsigns_only = []
    callsigns_with_phones = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        # Извлекаем значения строк (только в пределах одной строки)
        fio_match = re.search(r"ФИО:[ \t]*(.*)", block)
        callsign_match = re.search(r"Позывной:[ \t]*(.*)", block)
        phone_match = re.search(r"Телефон:[ \t]*(.*)", block)
        
        fio = fio_match.group(1).strip() if fio_match else ""
        callsign = callsign_match.group(1).strip() if callsign_match else ""
        phone = phone_match.group(1).strip() if phone_match else "-"
        
        # ЛОГИКА: Если позывной пустой ИЛИ равен "-", используем ФИО
        if not callsign or callsign == "-":
            display_name = fio
        else:
            display_name = callsign
        
        if display_name:
            callsigns_only.append(display_name)
            callsigns_with_phones.append(f"{display_name} {phone}")
            
    return callsigns_only, callsigns_with_phones

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Пришлите список волонтеров из приложения. В ответ я пришлю тебе в первом сообщении список волонтеров, а во втором список волонтеров с номерами телефонов")

@dp.message(F.text)
async def process_list(message: types.Message):
    if "ФИО:" not in message.text:
        return

    callsigns, callsign_phones = extract_data(message.text)

    if not callsigns:
        await message.answer("Данные не найдены. Убедитесь, что в сообщении есть поля 'ФИО:', 'Позывной:' и 'Телефон:'.")
        return

    # Отчет 1: Список имен/позывных
    await message.answer("\n".join(callsigns))

    # Отчет 2: Имена + Телефоны
    await message.answer("\n".join(callsign_phones))

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
