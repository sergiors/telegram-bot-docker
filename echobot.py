import os
import logging
import dateparser
from dateutils import now, iso

import redis

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)

bot_token = os.environ['TELEGRAM_BOT_TOKEN']
redis_url = os.environ.get('REDIS_URL', 'redis://localhost')
logger = logging.getLogger(__name__)
r = redis.from_url(redis_url)

TYPING_DATE, CHECKING_DATE = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info('User %s starts a scheduling.', user.first_name)

    await update.message.reply_text(
        'Oi! Para agendar um alerta digite o dia/horário que deseja.\n\n' 'Envie /cancel para parar de falar comigo.'
    )

    return TYPING_DATE


async def typing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_dt = dateparser.parse(
        update.message.text,
        settings={
            'TIMEZONE': 'America/Sao_Paulo',
            'RETURN_AS_TIMEZONE_AWARE': True,
        },
    )

    if not user_dt:
        await update.message.reply_text('Perdão, não consegui interpretar a data, por mandar novamente?')
        return TYPING_DATE

    if now() >= user_dt:
        await update.message.reply_text('A data deve ser no futuro. Por favor, informe uma nova data.')
        return TYPING_DATE

    context.user_data['date'] = user_dt

    reply_keyboard = [['Sim', 'Não']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    await update.message.reply_text('Confirmar para %s?' % user_dt.strftime('%d/%m/%Y às %H:%M'), reply_markup=markup)

    return CHECKING_DATE


async def checking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    user = update.effective_user
    create_date = now()
    expiry_date = context.user_data['date']

    r.hset(
        f'schedule:{msg_id}',
        mapping={
            'chat_id': chat_id,
            'user_id': user.id,
            'first_name': user.first_name,
            'username': user.username,
            'create_date': iso(create_date),
            'expiry_date': iso(expiry_date),
        },
    )
    r.set(f'schedule:{msg_id}:ex', '', exat=expiry_date)

    await update.message.reply_text('Agendado!')

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info('User %s canceled the scheduling.', user.first_name)

    await update.message.reply_text(
        'Tchau! Espero que possamos conversar novamente algum dia.',
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat.id
    logger.info(f'Chat ID {chat_id}')
    await update.message.reply_text(update.message.text)


def main() -> None:
    app = Application.builder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TYPING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, typing)],
            CHECKING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, checking)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
