import asyncio
from datetime import datetime

import aiohttp
import requests
from apikeys import opentripmapApiKey


def encode_string(place: str):
    return place.replace(" ", "%20")


def get_weather(data: dict):
    code_to_smile = {
        "Clear": "Ясно ☀️",
        "Clouds": "Облачно ☁️",
        "Rain": "Дождь 🌧",
        "Drizzle": "Дождь 🌧",
        "Thunderstorm": "Гроза ⚡️",
        "Snow": "Снег 🌨",
        "Mist": "Туман 🌫"
    }

    city = data["name"]
    cur_weather = data["main"]["temp"]

    weather_description = data["weather"][0]["main"]
    if weather_description in code_to_smile:
        wd = code_to_smile[weather_description]
    else:
        wd = "Посмотри в окно, не пойму что там за погода!"

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind = data["wind"]["speed"]
    sunrise_timestamp = datetime.fromtimestamp(data["sys"]["sunrise"])
    sunset_timestamp = datetime.fromtimestamp(data["sys"]["sunset"])
    length_of_the_day = datetime.fromtimestamp(
        data["sys"]["sunset"]) - datetime.fromtimestamp(
        data["sys"]["sunrise"])

    msg = (f"*Погода в городе: {city}*\nТемпература: {cur_weather}C° {wd}\n"
           f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind} м/с\n"
           f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\nПродолжительность дня:"
           f" {length_of_the_day}\n")

    return msg


def get_locate(data: list):
    places = ""
    for place in data:
        city = "город не указан"
        if 'city' in place['address']:
            city = place['address']['city']
        country = place['address']['country']

        name = place['name']
        if name == "":
            name = "название не указано"

        info = "Описания нет:("
        if 'wikipedia_extracts' in place.keys():
            info = place['wikipedia_extracts']['text']

        tmp = (f"🏙 *Город:* {city}\n"
               f"🎑 *Страна:* {country}\n"
               f"🌉 *Достопримечательность:* {name}\n"
               f"📝 *Описание места:*\n"
               f"{info}\n\n")
        places += tmp

    return places
