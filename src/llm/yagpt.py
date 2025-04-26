from pprint import pformat

import httpx
import requests

from src.common.log import logger
from src.common.settings import settings


def get_iam_token() -> str:
    url: str = settings.yandex_iam_url
    logger.info(msg := f"Getting IAM token from: {url} ...")
    token: str = settings.yandex_oauth_token
    with requests.Session() as client:
        response = client.post(
            url,
            json={'yandexPassportOauthToken': token}
        )
        response.raise_for_status()
    logger.info(f"{msg} done")
    return response.json()['iamToken']


async def run_query(
        user_text,
        iam_token: str = settings.yandex_iam_token,
        folder_id: str = settings.yandex_folder_id,
):
    # Собираем запрос
    data = {}
    # Указываем тип модели
    data["modelUri"] = f"gpt://{folder_id}/yandexgpt"
    # Настраиваем опции
    data["completionOptions"] = {"temperature": 0.3, "maxTokens": 1000}
    # Указываем контекст для модели
    data["messages"] = [
        {"role": "system", "text": "Ответь на вопрос."},
        {"role": "user", "text": f"{user_text}"},
    ]

    if not iam_token:
        iam_token = get_iam_token()
        settings.yandex_iam_token = iam_token
    url = settings.yandex_gpt_url
    logger.info(
        f"Sending request to {url}, with: {pformat(data)}"
        f"\niam token: {iam_token[:8]}...{iam_token[-8:]}"
    )
    # Отправляем запрос
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {iam_token}"
                },
                json=data,
            )
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"YandexGPT response: {response_data}")
                return response_data
            else:
                logger.error(f"YandexGPT error: {response.text}")
        except httpx.RequestError:
            # "Ошибка: не удалось спросить у LLM. Не очень-то и хотелось :|"
            return None

    # Распечатываем результат
    logger.info(f"Response received: {response}")
    return response

