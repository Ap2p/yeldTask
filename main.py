import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from bot_set import BOT_TOKEN

# BOT_TOKEN в файле bot_set в корневом каталоге.
API_TOKEN: str = BOT_TOKEN
API_CATS_URL: str = 'https://api.thecatapi.com/v1/images/search'  # Котик
API_DOGS_URL: str = 'https://random.dog/woof.json'  # Собака
API_FOX_URL: str = 'https://randomfox.ca/floof/'  # Лиса

# Создаем обхекты бота и диспетчера
bot: Bot = Bot(token=API_TOKEN)
dp: Dispatcher = Dispatcher()


# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands=['start']))
async def process_start_command(message: Message):
    await message.answer('Привет\nМеня зовут Эхо-бот!\nНапиши мне котик, песик или лиса, или вообще хоть что-нибудь :)')


# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer(
        'Напиши мне что-нибудь и в ответ я пришлю тебе твое сообщение. Или попроси прислать фото (котик, песик, лиса).')


# Этот хэндлер будет срабатывать на отправку боту фото
@dp.message(F.content_type == ContentType.PHOTO)
async def send_photo_echo(message: Message):
    print(message)
    await message.reply_photo(message.photo[-1].file_id)


# Этот хэндлер будет срабатывать на отправку боту стикеры
@dp.message(F.content_type == ContentType.STICKER)
async def send_photo_echo(message: Message):
    print(message)
    await message.reply_sticker(message.sticker.file_id)

# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения
# кроме команд /start и /help
@dp.message()
async def send_echo(message: Message):
    text = message.text
    try:
        if text == 'котик':
            async with httpx.AsyncClient() as client:
                photo_response = await client.get(API_CATS_URL)
                photo_response.raise_for_status()
                photo_link = photo_response.json()[0]['url']
            await message.answer_photo(photo_link)
        elif text == 'лиса':
            async with httpx.AsyncClient() as client:
                photo_response = await client.get(API_FOX_URL)
                photo_response.raise_for_status()
                photo_link = photo_response.json()['image']
            await message.answer_photo(photo_link)
        elif text == 'песик':
            async with httpx.AsyncClient() as client:
                photo_response = await client.get(API_DOGS_URL)
                photo_response.raise_for_status()
                photo_link = photo_response.json()['url']
            await message.answer_photo(photo_link)
        else:
            await message.reply(text=message.text)
    except httpx.HTTPStatusError:
        await message.answer("Здесь должна быть картинка, но ее нет, попробуй еще раз")


if __name__ == '__main__':
    dp.run_polling(bot)
