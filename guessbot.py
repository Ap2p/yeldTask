#!/usr/bin/env python3

from bot_set import BOT_TOKEN_GUESS
import random
import sqlite3
import signal
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Вместо BOT TOKEN GUESS нужно вставить токен вашего бота,
# полученный у @BotFather
BOT_TOKEN: str = BOT_TOKEN_GUESS

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher()

# Количество попыток, доступных пользователю в игре
ATTEMPTS: int = 5

# Константа с именем базы данных
DB_NAME = 'users.db'
users = {}


# Функция для создания таблицы пользователей, если она не существует
def create_table():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    in_game INTEGER,
                    attempts INTEGER,
                    total_games INTEGER,
                    wins INTEGER
    )''')
    conn.commit()
    conn.close()


# Функция для загрузки данных игры из базы данных для данного польозвателя
def load_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_data = cur.fetchone()
    conn.close()

    if user_data:
        # Если данные пользователя найдены в базе данных, возвращаем их в виде словаря
        return {
            'in_game': bool(user_data[1]),
            'attempts': user_data[2],
            'total_games': user_data[3],
            'wins': user_data[4]
        }
    else:
        # Если данных пользователя нет в базе данных, создаем новую запись
        # Не сохраняем 'secret_number', так как оно генерируется при каждой новой игре
        return {
            'in_game': False,
            'attempts': None,
            'total_games': 0,
            'wins': 0
        }


# Функция для сохранения данных игры в базу данных для данного пользователя
def save_user_data(user_id, data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    user_data = (
        user_id, int(data['in_game']), data['attempts'], data['total_games'], data['wins'])
    cur.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?)", user_data)
    conn.commit()
    conn.close()


# Функция возвращающая случайное целое число от 1 до 100
def get_random_number() -> int:
    return random.randint(1, 100)


# Инициализируем объект билдера
kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()

# Создаем объекты кнопок
button_1: KeyboardButton = KeyboardButton(text='Играем!')
button_2: KeyboardButton = KeyboardButton(text='Статистика')
button_3: KeyboardButton = KeyboardButton(text='Прервать')

kb_builder.add(button_1, button_2, button_3)
kb_builder.adjust(2, 1)


# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands=['start']))
async def process_start_command(message: Message):
    await message.answer('Привет!\nДавай сыграем в игру "Угадай число"?\n\n'
                         'Нажми /play чтобы запустить игру :)\n'
                         'Чтобы получить правила игры и список доступных '
                         'команд - отправьте команду /help',
                         reply_markup=kb_builder.as_markup(resize_keyboard=True,
                                                           one_time_keyboard=True))

    # Загружаем данные пользователя из базы данных
    user_data = load_user_data(message.from_user.id)
    if not user_data:
        # Если данных пользователя нет в базе, создаем новую запись
        user_data = {
            'in_game': False,
            'secret_number': None,
            'attempts': None,
            'total_games': 0,
            'wins': 0
        }
    # Обновляем данные пользователя в словаре 'users'
    users[message.from_user.id] = user_data


# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer(f'Правила игры:\n\nЯ загадываю число от 1 до 100, '
                         f'а вам нужно его угадать\nУ вас есть {ATTEMPTS} '
                         f'попыток\n\nДоступные команды:\n/help - правила '
                         f'игры и список команд\n/cancel - выйти из игры\n'
                         f'/stat - посмотреть статистику\n\nДавай сыграем?'
                         f'\n\n/play - чтобы начать игру :)')


# Этот хэндлер будет срабатывать на команду "/stat"
@dp.message(Command(commands=['stat']))
@dp.message(F.text == 'Статистика')
async def process_stat_command(message: Message):
    await message.answer(f'Всего игр сыграно: '
                         f'{users[message.from_user.id]["total_games"]}\n'
                         f'Игр выиграно: {users[message.from_user.id]["wins"]}'
                         f'\nНажми /play чтобы сыграть еще!')


# Этот хэндлер будет срабатывать на команду "/cancel"
@dp.message(F.text == 'Прервать')
@dp.message(Command(commands=['cancel']))
async def process_cancel_command(message: Message):
    if users[message.from_user.id]['in_game']:
        await message.answer('Вы вышли из игры.\nЕсли захотите сыграть '
                             'снова - нажмите /play')
        users[message.from_user.id]['in_game'] = False
        # Сохраняем данные игры пользователя в базу данных
        save_user_data(message.from_user.id, users[message.from_user.id])
    else:
        await message.answer('А мы итак с вами не играем. '
                             'Может, сыграем разок?\nНажмите /play')


# Этот хэндлер будет срабатывать на команду "/play"
@dp.message(Command(commands=['play']))
@dp.message(F.text == 'Играем!')
async def process_positive_answer(message: Message):
    if not users[message.from_user.id]['in_game']:
        await message.answer('Ура!\n\nЯ загадал число от 1 до 100, '
                             'попробуй угадать!')
        users[message.from_user.id]['in_game'] = True
        users[message.from_user.id]['secret_number'] = get_random_number()
        users[message.from_user.id]['attempts'] = ATTEMPTS
        # Сохраняем данные игры пользователя в базу данных
        save_user_data(message.from_user.id, users[message.from_user.id])
    else:
        await message.answer('Пока мы играем в игру я могу '
                             'реагировать только на числа от 1 до 100 '
                             'и команды /cancel и /stat')


# Функция для сохранения данных всех пользователей перед остановкой бота
def save_all_users_data(signal_number, frame):
    for user_id, data in users.items():
        save_user_data(user_id, data)
    print('Данные всех пользователей сохранены. Бот завершает рабту.')
    exit(0)


# Этот хэндлер будет срабатывать на отказ пользователя сыграть в игру
@dp.message(F.text.in_(['Нет', 'Не', 'Не хочу', 'Не буду', 'Прервать']))
async def process_negative_answer(message: Message):
    if not users[message.from_user.id]['in_game']:
        await message.answer('Жаль :(\n\nЕсли захотите поиграть - просто '
                             'нажмите /play')
    else:
        await message.answer('Мы же сейчас с вами играем. Присылайте, '
                             'пожалуйста, числа от 1 до 100')


# Этот хэндлер будет срабатывать на отправку пользователем чисел от 1 до 100
@dp.message(lambda x: x.text and x.text.isdigit() and 1 <= int(x.text) <= 100)
async def process_numbers_answer(message: Message):
    if users[message.from_user.id]['in_game']:
        if int(message.text) == users[message.from_user.id]['secret_number']:
            await message.answer('Ура!!! Вы угадали число!\n\n'
                                 'Может, сыграем еще?\nНажмите /play')
            users[message.from_user.id]['in_game'] = False
            users[message.from_user.id]['total_games'] += 1
            users[message.from_user.id]['wins'] += 1
        elif int(message.text) > users[message.from_user.id]['secret_number']:
            await message.answer('Мое число меньше')
            users[message.from_user.id]['attempts'] -= 1
        elif int(message.text) < users[message.from_user.id]['secret_number']:
            await message.answer('Мое число больше')
            users[message.from_user.id]['attempts'] -= 1

        if users[message.from_user.id]['attempts'] == 0:
            await message.answer(f'К сожалению, у вас больше не осталось '
                                 f'попыток. Вы проиграли :(\n\nМое число '
                                 f'было {users[message.from_user.id]["secret_number"]}\n\nДавайте '
                                 f'сыграем еще? Нажмите /play')
            users[message.from_user.id]['in_game'] = False
            users[message.from_user.id]['total_games'] += 1
            # Сохраняем данные игры пользователя в базу данных
            save_user_data(message.from_user.id, users[message.from_user.id])
    else:
        await message.answer('Мы еще не играем. Хотите сыграть? Нажмите /play')


# Этот хэндлер будет срабатывать на остальные любые сообщения
@dp.message()
async def process_other_text_answers(message: Message):
    if users[message.from_user.id]['in_game']:
        await message.answer('Мы же сейчас с вами играем. '
                             'Присылайте, пожалуйста, числа от 1 до 100')
    else:
        await message.answer('Я довольно ограниченный бот, давайте '
                             'просто сыграем в игру?\nНажмите /play')


if __name__ == '__main__':
    #  Создаем таблицу пользователей при запуске бота
    create_table()
    # Устанавливаем обработчик события завершения для сохранения данных
    signal.signal(signal.SIGINT, save_all_users_data)
    signal.signal(signal.SIGTERM, save_all_users_data)
    dp.run_polling(bot)
