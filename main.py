from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types.web_app_info import WebAppInfo
from config import BOT_TOKEN, AMPLITUDE_API_KEY, AMPLITUDE_API_URL
import db
import json
import aiohttp




bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def send_amplitude_event(user_id, event_type, event_properties):
    headers = {
        'Content-Type': 'application/json',
        'Accept': '*/*'
    }

    data = {
        "api_key": AMPLITUDE_API_KEY,
        "events": [{
            "user_id": user_id,
            "event_type": event_type,
            "event_properties": event_properties
        }]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(AMPLITUDE_API_URL, headers=headers, json=data) as response:
            if response.status == 200:
                print("Success:", await response.json())
            else:
                print("Error:", await response.text())

async def handle_character_choice(user_id, character_choice):
    event_type = 'character_choice'
    event_properties = {
        'character_choice': character_choice
    }
    await send_amplitude_event(user_id, event_type, event_properties)



@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_id
    name = message.from_user.first_name
    surname = message.from_user.last_name
    username = message.from_user.username

    if  not db.check_user(user_id):
        res = db.insert_user(user_id, username, name, surname)
        if res:
            event_type = 'user_registration'
            event_properties = {
                'user_id': user_id,
                'name': name,
                'surname': surname,
                'username': username
            }
            await send_amplitude_event(user_id, event_type, event_properties)
            await bot.send_message(message.from_user.id,"""
🌟 Добро пожаловать в мир уникального опыта!
🤖 Я ваш верный спутник, созданный с использованием передовых технологий. Моя цель - обеспечить вас незабываемым взаимодействием и развлечением.
🎭 Разговаривайте со мной, как с живым персонажем. Я умею отвечать на ваши вопросы, поддерживать диалоги и даже адаптироваться к вашим предпочтениям.
🌐 Откройте новые горизонты общения с искусственным интеллектом, просто отправив мне сообщение. Давайте начнем увлекательное путешествие в мире виртуальной реальности!
💬 Если у вас есть какие-либо вопросы или просьбы, не стесняйтесь обращаться. Я здесь, чтобы сделать ваше время с ботом незабываемым и интересным.
""")
            await bot.send_message(message.from_user.id, "Пожалуйста, выберите персонажа по кнопке ниже", reply_markup=web_app_keyboard())
        else:
            await bot.send_message(message.from_user.id,"Что то пошло не так!")
    else:
        await bot.send_message(message.from_user.id, """
Вы уже зарегестрированы. Если вы хотите поменять 
персонажа, нажмите на кнопку ниже.
Иначе, просто отправьте текст, чтобы продолжить общение с персонажем """, reply_markup=web_app_keyboard())


@dp.message_handler(commands = ['menu'])
async def change_character(message: types.Message):
    await bot.send_message(message.from_user.id, "Нажмите на кнопку ниже, чтобы поменять персонажа", reply_markup=web_app_keyboard())



def web_app_keyboard():
    keyboard = ReplyKeyboardMarkup(
                resize_keyboard=True, one_time_keyboard=True)
            
    accept_button = KeyboardButton("Выбрать персонажа", web_app=WebAppInfo(url='https://egor-s-n.github.io/site/'))
    keyboard.add(accept_button)

    return keyboard

@dp.message_handler(content_types=['web_app_data'])
async def web_app_answer(messasge: types.Message):
    res = json.loads(messasge.web_app_data.data)
    character = db.get_character(int(res["value"]))

    event_type = 'choose_character'
    event_properties = {
               'choisen_character': character[0],
            }
    await send_amplitude_event(messasge.from_user.id, event_type, event_properties)




    db.update_user_character(messasge.from_user.id, character[0])
    await messasge.answer("Данные успешно обновлены", reply_markup=ReplyKeyboardRemove())
    await messasge.answer(character[2], reply_markup=ReplyKeyboardRemove())


@dp.message_handler(content_types='text')
async def text_processing(message: types.Message):
    character = db.get_user(message.from_user.id)[5]
    if character != None:

        #начинаем сохранять запросы и ответы в БД 
        id_req = db.create_req_res(message.from_user.id, character)

        #Ampitude на отправленный запрос
        event_type = 'user_send_request'
        event_properties = {
                'send_request': 1,
                }
        await send_amplitude_event(message.from_user.id, event_type, event_properties)
        
        #Сохранение сообщения пользователя 
        db.set_request(id_req, message.text)

        # Запрос в Ai 
        req = f"instructions: {db.get_instruction(message.from_user.id)}. User message: {message.text}"
        messages = [
            {"role": "user", "content": req}
        ]
        #получение ответа от Ai
        response_data = await fetch_completion(messages)
        response_text = response_data['choices'][0]['message']['content']
        # отправка Amplitude на получение ответа 
        event_type = 'get-response'
        event_properties = {
                'response': 1,
                }
        await send_amplitude_event(message.from_user.id, event_type, event_properties)

        #Ответ бота 
        await bot.send_message(message.from_user.id, response_text, reply_markup=ReplyKeyboardRemove())

        #Сохранение ответа Ai рядом с запросом 
        db.set_response(id_req, response_text)

        # Amplitude на отправку ответа для пользователя 
        event_type = 'send_answer'
        event_properties = {
                'answer': 1,
                }
        # Amplitude на то, что ответ доставлен 
        await send_amplitude_event(message.from_user.id, event_type, event_properties)
    else:
        await bot.send_message(message.from_user.id, "Чтобы начать общение, пожалуйста, выберите персонажа", reply_markup=web_app_keyboard())


async def fetch_completion(message):
    endpoint = 'http://95.217.14.178:8080/candidates_openai/gpt'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': message,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, headers=headers, json=data) as response:
            return await response.json()


def main():
    db.create_database()
    db.create_tables()
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    main()
# таблица БД (id, user_id,character,  request, response)   -------------
#сохранить запрос пользователя в бд
# рядом сохранять ответ бота
# для ебаной хуйни на сайте можно разбить на два event и просто условие добавить, а на хуйне потом соединить 
# добавить автоскрипт на добавление марио и энштейна в ЬД при первом запуске -----------------