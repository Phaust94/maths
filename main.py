import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm your maths practice bot. Send me a math problem!",
        # For more complex replies, consider reply_markup=ForceReply(selective=True)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued."""
    await update.message.reply_text("I can help you practice maths! Try /start to begin.")

def main() -> None:
    """Start the bot."""
    # Use environment variable for bot token
    # Get your bot token from BotFather on Telegram.
    # Store it as an environment variable, e.g., export TELEGRAM_BOT_TOKEN='YOUR_TOKEN_HERE'
    # Or replace os.environ.get('TELEGRAM_BOT_TOKEN') with 'YOUR_TOKEN_HERE' (not recommended for production)
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set. Please set it to your bot token.")
        exit(1)

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # on different commands - register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Run the bot until the user presses Ctrl-C
    # Set a polling interval of 2 seconds
    logger.info("Bot started polling every 2 seconds...")
    application.run_polling(poll_interval=2)

if __name__ == "__main__":
    main()
