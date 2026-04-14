import asyncio
import logging
import re

from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import Bot, Dispatcher
from pydantic_settings import BaseSettings, SettingsConfigDict
from yandex_music import ClientAsync
from yandex_music.utils.request_async import Request


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env"
    )
    YANDEX_MUSIC_API_TOKEN: str
    PROXY_URL: str
    BOT_TOKEN: str

settings = Settings()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

dp = Dispatcher()
logger = logging.getLogger(__name__)
request = Request(proxy_url=settings.PROXY_URL)
yandex_client_async = ClientAsync(token=settings.YANDEX_MUSIC_API_TOKEN, request=request,)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет. Введите корректный URL. Пример: https://music.yandex.ru/album/1193829/track/10994777")


@dp.message()
async def get_music_info(message: Message):
    logger.info(f"Получено сообщение{message.text}")
    text: str = message.text
    mtch = re.match(r'^https://music\.yandex\.ru/album/(?P<album_id>\d+)/track/(?P<track_id>\d+)$',
             text)
    if not mtch:
        logger.error("Сообщение не корректно")
        await message.answer("Введите корректный URL. Пример: https://music.yandex.ru/album/1193829/track/10994777")
        return

    param_dict = mtch.groupdict()

    logger.info(f"Распарсено: {param_dict}")

    track_id = param_dict['track_id']

    try:
        tracks = await yandex_client_async.tracks(f'{track_id}')
    except Exception as err:
        logger.exception(err)
        await message.answer("Не получилось получить информацию")
        return

    if not tracks:
        logger.error("Неудача в попытке получения трека")
        logger.error(tracks)
        await message.answer("Такого трека не существует")

    track = tracks[0]

    await message.answer(f"""Имя артиста: {', '.join(track.artists_name())}\n"""\
                         f"""Название трека: {track.title}\n"""
                         f"""Длительность(секунды): {track.duration_ms / 1000 if isinstance(track.duration_ms, int) else ' '}"""
                         )

async def main():
    bot = Bot(token= settings.BOT_TOKEN)
    await  dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
