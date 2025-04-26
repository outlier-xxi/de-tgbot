import time

import asyncpg
from telegram.error import InvalidToken
from telegram.ext import (
    Application,
)

from src.common.db import init_pool
from src.common.log import logger
from src.common.settings import settings
from src.llm.yagpt import get_iam_token
from src.tg.service import prepare_conv_handler


async def post_init(application: Application) -> None:
    """
    Post initialization hook
    """
    # app.bot_data: Shared variables
    application.bot_data['pg_pool']: asyncpg.pool = await init_pool()

    settings.yandex_iam_token = get_iam_token()
    logger.info(f"IAM token set: {settings.yandex_iam_token[:8]}...{settings.yandex_iam_token[-8:]}")


def main():
    while True:
        try:
            app: Application = (
                Application.builder()
                .token(settings.bot_token)
                .post_init(post_init)
                .build()
            )
            break
        except InvalidToken:
            logger.error("❌ Failed to start. Sorry :(")

        logger.info(f"I don't care. Sleeping: {settings.start_retry} ...")
        time.sleep(settings.start_retry)
        logger.info("Ok, well, once again ...")

    # ConversationHandler для управления диалогом
    conv_handler = prepare_conv_handler()
    app.add_handler(conv_handler)
    logger.info("Bot started. Yeah we did it! :)")

    app.run_polling()


if __name__ == "__main__":
    main()
