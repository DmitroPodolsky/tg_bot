from aiogram import Bot, Dispatcher, types, executor
import logging

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import TELEGRAM_API,SECRET_KEY
from db import db_start, create_film, delete_film, edit_film, check_film, select_film

NOTSUB_MS = 'nope,go sub'
CHANNELS = [["Канал2",-1001589094714,'https://t.me/uahshwa']]#["Канал1",-1001803048093,'https://t.me/seventhphantominfo']
logging.basicConfig(level=logging.INFO)
SUB_CHANNELS = []
storage = MemoryStorage()
bot = Bot(TELEGRAM_API)
dp = Dispatcher(bot,storage=storage)

async def on_startup(_):
    await db_start()#разворачиваем бд

class Check_password(StatesGroup):
    password = State()
    clear = State()

class Set_Channel(StatesGroup):
    name = State()
    id = State()
    link = State()

class Del_Channel(StatesGroup):
    link = State()

class Set_Film(StatesGroup):
    name = State()

class Del_Film(StatesGroup):
    code = State()

class Select_Film(StatesGroup):
    code = State()

class Insert_Film(StatesGroup):
    code = State()
    name = State()

async def check_sub(channels,user_id):
    global SUB_CHANNELS
    check_error = False
    for channel in range(len(channels)):
        check=await bot.get_chat_member(chat_id=channels[channel][1],user_id=user_id)
        if check['status']=='left':
            check_error=True
            SUB_CHANNELS.append((channels[channel][0],channels[channel][2]))
    if check_error:
        return False
    return True

def get_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/create_channel'))
    kb.add(KeyboardButton('/delete_channel'))
    kb.add(KeyboardButton('/create_film'))
    kb.add(KeyboardButton('/delete_film'))
    kb.add(KeyboardButton('/change_film'))
    return kb

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/cancel'))

    return kb

def get_clava_inline():
    global SUB_CHANNELS
    idk = InlineKeyboardMarkup(row_width=len(CHANNELS))  # указываем сколько столбиков будет
    for channel in SUB_CHANNELS:
        idk.add(InlineKeyboardButton(text=channel[0],url=channel[1]))
    SUB_CHANNELS=[]
    return idk

@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.reply('Вы прервали операцию!',
                        reply_markup=get_keyboard())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == 'private':
        if await check_sub(CHANNELS,message.from_user.id):
            await bot.send_message(message.from_user.id,'Добро пожаловать, введите код фильма ',reply_markup=get_cancel_keyboard())
            await Select_Film.code.set()
        else:
            await bot.send_message(message.from_user.id, NOTSUB_MS,reply_markup=get_clava_inline())

@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.chat.type == 'private':
        await message.answer('введите секретный ключ',reply_markup=get_cancel_keyboard())

        await Check_password.password.set()

@dp.message_handler(state=Check_password.password)
async def check_password(message: types.Message, state: FSMContext):
    if message.text != SECRET_KEY:
        await message.reply('неверный пароль, попробуйте ввести другой')
        return
    await message.answer('вот вам открытый функционал',reply_markup=get_keyboard())
    await Check_password.next()

@dp.message_handler(commands=['create_film'],state=Check_password.clear)
async def film_create(message: types.Message):
    await message.reply("отправьте название фильма",
                        reply_markup=get_cancel_keyboard())
    await Set_Film.name.set()

@dp.message_handler(state=Set_Film.name)
async def add_name_film(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    answer = await create_film(state)
    await message.reply(f'фильм добавлен, его код: <b>{answer}</b>',parse_mode='HTML')
    await state.finish()

@dp.message_handler(commands=['delete_film'],state=Check_password.clear)
async def del_code_film(message: types.Message):
    await message.reply("отправьте код фильма",
                        reply_markup=get_cancel_keyboard())
    await Del_Film.code.set()

@dp.message_handler(state=Del_Film.code)
async def add_code_film(message: types.Message, state: FSMContext):
    if not await check_film(message.text):
        await message.reply('нету такого кода, введите ещё раз')
        return
    async with state.proxy() as data:
        data['code'] = message.text
    await delete_film(state)
    await message.reply('фильм удалён')
    await state.finish()

@dp.message_handler(commands=['change_film'],state=Check_password.clear)
async def add_code_film(message: types.Message):
    await message.reply("отправьте код фильма",
                        reply_markup=get_cancel_keyboard())
    await Insert_Film.code.set()

@dp.message_handler(state=Insert_Film.code)
async def add_code_film(message: types.Message, state: FSMContext):
    if not await check_film(message.text):
        await message.reply('нету такого кода, введите ещё раз')
        return
    async with state.proxy() as data:
        data['code'] = message.text
    await message.reply('дайте новое название фильму')
    await Insert_Film.next()

@dp.message_handler(state=Insert_Film.name)
async def add_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await edit_film(state)
    await message.reply('фильм изменён')
    await state.finish()

@dp.message_handler(state=Select_Film.code)
async def add_code_film(message: types.Message, state: FSMContext):
    if not await check_film(message.text):
        await message.reply('нету такого кода, введите ещё раз')
        return
    async with state.proxy() as data:
        data['code'] = message.text
    answer = await select_film(message.text)
    await message.reply(f'название фильма: <b>{answer}</b>',parse_mode='HTML')
    await state.finish()

@dp.message_handler(commands=['create_channel'],state=Check_password.clear)
async def channel_create(message: types.Message):
    await message.reply("сначало отправьте имя своего канала",
                        reply_markup=get_cancel_keyboard())
    await Set_Channel.name.set()

@dp.message_handler(commands=['delete_channel'],state=Check_password.clear)
async def channel_delete(message: types.Message):
    await message.reply("отправьте ссылку на ваш канал",
                        reply_markup=get_cancel_keyboard())
    await Del_Channel.link.set()

@dp.message_handler(state=Del_Channel.link)
async def del_channel(message: types.Message, state: FSMContext):
    global CHANNELS
    deleter = True
    for channel in range(len(CHANNELS)):
        if CHANNELS[channel][2]==message.text:
            deleter=channel
    if deleter:
        await message.answer('такого канала не существует')
        return
    CHANNELS.pop(deleter)
    await message.answer('канал успешно удалён')
    await state.finish()

@dp.message_handler(state=Set_Channel.name)
async def add_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply('дайте id канала')
    await Set_Channel.next()

@dp.message_handler(state=Set_Channel.id)
async def add_id(message: types.Message, state: FSMContext) -> None:
    try:
        await bot.get_chat_member(chat_id=message.text,user_id=message.from_user.id)
    except:
        await message.reply('не правильно ввели id канала или я не администратор данного канала')
        return
    async with state.proxy() as data:
        data['id'] = message.text

    await message.reply('дайте ссылку на канал')
    await Set_Channel.next()

@dp.message_handler(state=Set_Channel.link)
async def add_link(message: types.Message, state: FSMContext) -> None:
    global CHANNELS
    try:
        check=InlineKeyboardMarkup(row_width=1)
        check.add(InlineKeyboardButton(text='check',url=message.text))
        await message.answer(text='проверка пройдена',reply_markup=check)
    except:
        await message.reply('не правильно ввели ссылку на канал')
        return
    async with state.proxy() as data:
        data['link'] = message.text
        CHANNELS.append([data['name'],data['id'],data['link']])

    await message.reply('канал добавлен')
    await state.finish()

@dp.message_handler()
async def echo_upper(message: types.Message):
    if message.chat.type == 'private':
        await bot.send_message(message.from_user.id, 'nope')

if __name__ == '__main__':
    executor.start_polling(dp,skip_updates=True,on_startup=on_startup)