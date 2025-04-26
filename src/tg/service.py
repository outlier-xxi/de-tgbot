import uuid

import asyncpg
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ChatAction
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from src.common.db import log_action, log_query, update_query
from src.common.log import logger
from src.common.settings import settings
from src.llm.yagpt import run_query
from src.models.public import QueryStatus, ActionType

START, QUESTION, CONTINUE = range(3)

start_keyboard = ReplyKeyboardMarkup(
    [["Задать вопрос"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

continue_keyboard = ReplyKeyboardMarkup(
    [["Новый вопрос", "Завершить"]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User: {update.effective_user.id} started the conversation.")
    pool: asyncpg.pool = context.bot_data['pg_pool']
    user_id = update.effective_user.id
    await log_action(pool, user_id, ActionType.start.value)

    text = "Привет! Я бот DE-task. Для отмены диалога нажмите /cancel. Примеры вопросов:"
    examples_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            settings.q1, callback_data="sample_1"
        )],
        [InlineKeyboardButton(
            settings.q2,
            callback_data="sample_2"
        )],
        [InlineKeyboardButton(
            settings.q3, callback_data="sample_3"
        )],
    ])
    await update.message.reply_text(text, reply_markup=examples_keyboard)
    return QUESTION


# Обработка текстового вопроса
async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id: int = update.effective_user.id
    pool: asyncpg.pool = context.bot_data['pg_pool']

    question: str = ''
    if update and update.message:
        question = update.message.text
    else:
        question = context.user_data['current_question']
    logger.info(f"User {user_id} asked: {question}")
    query_id: uuid.UUID = await log_query(pool, user_id, question)
    await log_action(pool, user_id, ActionType.question.value, query_id=query_id)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    escaped_question = (
        question.replace('.', '\\.').replace('-', '\\-').replace('!', '\\!')
        .replace('+', '\\+')
    )
    if update.message:
        await update.message.reply_text(
            f"🔍 Ищу ответ на вопрос: \t*{escaped_question}*", parse_mode="MarkdownV2"
        )
    else:
        await update.callback_query.edit_message_text(
            f"🔍 Ищу ответ на вопрос:\t*{question}*", parse_mode="MarkdownV2"
        )

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    answer = await run_query(question)
    if not answer:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"🤖 Ничего не вышло. Или попробуйте вновь, или пусть "
                f"{settings.admin_user} разбирается :)\n\n{answer}"
            ),
        )
        await update_query(pool, query_id, user_id, status=QueryStatus.error.value)
        return QUESTION

    alternatives: list = answer.get('result', {}).get('alternatives', [{}])
    answer_text: str = '\n\n'.join(
        alt_item.get('message', {}).get('text', '')
        for alt_item in alternatives
    )
    logger.info(f"User :{user_id}, sending answer len: {len(answer_text)}")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🤖 Ответ: \n\n{answer_text}"
    )

    meta_text: str = answer.get('result', {}).get('usage')
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="MarkdownV2",
        text=f"""
        `Метаданные:`
        `{meta_text}`
        """
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🤖 Вы можете задать следующий вопрос!",
    )
    result_usage: dict = answer.get('result', {}).get('usage', {})
    await update_query(
        pool,
        query_id,
        user_id,
        status=QueryStatus.responded.value,
        response_text=answer_text,
        input_text_tokens=result_usage.get('inputTextTokens', None),
        completion_tokens=result_usage.get('completionTokens', None),
        total_tokens=result_usage.get('totalTokens', None),
    )

    return QUESTION


async def handle_sample_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sample_questions = {
            "sample_1": settings.q1,
            "sample_2": settings.q2,
            "sample_3": settings.q3,
    }
    query = update.callback_query
    question = sample_questions.get(query.data, "Неизвестный вопрос")
    context.user_data['current_question'] = question

    return await handle_question(update, context)


# Обработка продолжения (новый вопрос или завершение)
async def continue_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "Новый вопрос":
        await update.message.reply_text(
            "Введите ваш вопрос:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return QUESTION
    elif choice == "Завершить":
        await update.message.reply_text(
            "Диалог завершён. Нажмите /start, чтобы начать заново.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "Пожалуйста, используйте предоставленные кнопки.",
    )
    return CONTINUE


# Обработка отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Диалог отменён. Нажмите /start, чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await log_action(
        context.bot_data['pg_pool'], update.effective_user.id, ActionType.cancel.value
    )
    return ConversationHandler.END


def prepare_conv_handler() -> ConversationHandler:
    """
    ConversationHandler для управления диалогом
    """
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question),
                CallbackQueryHandler(handle_sample_questions, pattern="^sample_"),  # Обработчик для примеров
                CallbackQueryHandler(cancel, pattern="^cancel"),
                CommandHandler("start", start),
            ],
            CONTINUE: [
                MessageHandler(filters.Regex("^Новый вопрос$"), continue_conversation),
                MessageHandler(filters.Regex("^Завершить$"), cancel),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    return conv_handler
