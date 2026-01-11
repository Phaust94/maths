
import os
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

def whitelisted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = str(update.effective_user.id)
        
        user_whitelist = os.environ.get('USER_WHITELIST', '').split(',')
        admin_user_list = os.environ.get('ADMIN_USER_LIST', '').split(',')

        if user_id not in user_whitelist and user_id not in admin_user_list:
            await update.message.reply_text("You are not authorized to use this bot.")
            return

        return await func(update, context, *args, **kwargs)
    return wrapped
