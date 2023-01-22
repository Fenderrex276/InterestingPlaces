import asyncio
import pprint

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode

from states import PlaceStates
from apikeys import graphhopperApiKey, openweatherApiKey, opentripmapApiKey
from utils import encode_string, get_weather, get_locate

RADIUS = 1000
LIMIT_PLACES = 5
LANG = 'ru'


class Weather:
    def __init__(self, bot: Bot, dp: Dispatcher):
        self.bot = bot
        self.dp = dp
        self.register_commands()
        self.register_handlers()

    def register_commands(self):
        self.dp.register_message_handler(self.start_handler, commands=["start"])

    def register_handlers(self):
        self.dp.register_message_handler(self.check_place, state=PlaceStates.input_place)
        for i in range(100):
            self.dp.register_callback_query_handler(self.answer_to_user, text=str(i), state=PlaceStates.is_clicked)
        self.dp.register_callback_query_handler(self.try_again, text='again', state=PlaceStates.is_clicked)

    async def start_handler(self, message: types.Message):
        msg = "Добро пожаловать в бот, который выводит интересные места и погоду по любому введеному адресу"

        msg1 = "Пожалуйста введите название места"
        await PlaceStates.input_place.set()
        await self.bot.send_message(message.from_user.id, msg)
        await self.bot.send_message(message.from_user.id, msg1)

    async def get_data(self, coords):
        lat = coords['lat']
        lon = coords['lng']
        url_weather = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={openweatherApiKey}"
        url_places = f"https://api.opentripmap.com/0.1/{LANG}/places/radius?radius={RADIUS}&limit=5&lon={lon}&lat={lat}&format=json&apikey={opentripmapApiKey}"
        tasks = []
        async with aiohttp.ClientSession() as session:
            tasks.append(asyncio.create_task(session.get(url=url_weather)))
            tasks.append(asyncio.create_task(session.get(url=url_places)))

            responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]

    async def get_interesting_places(self, places_data):
        tasks = []
        async with aiohttp.ClientSession() as session:
            for place in places_data:
                xid = place["xid"]
                url = f"https://api.opentripmap.com/0.1/{LANG}/places/xid/{xid}?apikey={opentripmapApiKey}"

                tasks.append(asyncio.create_task(session.get(url=url)))

            responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]

    async def check_place(self, message: types.Message, state: FSMContext):

        # print(message.text)
        buttons = types.InlineKeyboardMarkup()
        msg = 'Выберите нужное место'
        url = f"https://graphhopper.com/api/1/geocode?q={encode_string(message.text)}&locale=ru&key={graphhopperApiKey}"
        async with aiohttp.ClientSession() as session:
            response = await session.get(url=url)
            answer = await response.json()
            # print(answer)
            answer = answer['hits']
            tmp_array = []
            if not answer:
                msg = 'Данной локации не найдено, попробуйте ещё раз'
            else:
                await PlaceStates.is_clicked.set()
                for i in range(len(answer)):
                    if 'city' in answer[i]:
                        buttons.add(types.InlineKeyboardButton(text=answer[i]['name'] + ", " + answer[i]['city'],
                                                               callback_data=str(i)))
                    else:
                        buttons.add(types.InlineKeyboardButton(text=answer[i]['name'] + ", " + answer[i]['country'],
                                                               callback_data=str(i)))
                    tmp_array.append({str(i): answer[i]['point']})

                await state.update_data(points=tmp_array)

        #data = await state.get_data()
        #print(data)
        await self.bot.send_message(message.from_user.id, text=msg, reply_markup=buttons)

    async def answer_to_user(self, message: types.CallbackQuery, state: FSMContext):

        data = await state.get_data()
        current_coords = data['points'][int(message.data)][message.data]
        response = await self.get_data(coords=current_coords)

        weather_data = response[0]
        places_data = response[1]

        tmp = await self.get_interesting_places(places_data)
        print("interesting places")
        pprint.pprint(tmp)
        if not places_data:
            place = "Интересных мест в данной локации не найдено:("
        else:
            place = get_locate(tmp)

        try_again_keyboard = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text="Ввести ещё", callback_data="again")
        )

        await self.bot.send_message(text=get_weather(weather_data),
                                    parse_mode=ParseMode.MARKDOWN,
                                    chat_id=message.message.chat.id)
        await self.bot.send_message(text=place, reply_markup=try_again_keyboard,
                                    chat_id=message.message.chat.id,
                                    parse_mode=ParseMode.MARKDOWN)

    async def try_again(self, call: types.CallbackQuery):
        await PlaceStates.input_place.set()
        await call.message.answer(text="Пожалуйста введите название места")
