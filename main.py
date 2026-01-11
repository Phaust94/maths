import logging
import os
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Database Connection ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            port=os.environ.get('DB_PORT'),
            dbname=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD')
        )
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Could not connect to database: {e}")
        return None

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Cześć {user.mention_html()}! Jestem Twoim botem do ćwiczenia matematyki. Naciśnij /go, aby rozpocząć.",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued."""
    await update.message.reply_text("Naciśnij /start, aby zacząć.")

async def go_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a new maths challenge."""
    user_id = update.effective_user.id
    conn = get_db_connection()
    if not conn:
        await update.message.reply_text("Błąd połączenia z bazą danych.")
        return

    try:
        with conn.cursor() as cur:
            today = datetime.date.today()
            cur.execute("SELECT number FROM tries WHERE user_id = %s AND date = %s AND completed = TRUE ORDER BY number DESC LIMIT 1", (user_id, today))
            last_completed = cur.fetchone()
            
            next_number = 0
            if last_completed:
                next_number = last_completed[0] + 1

            cur.execute("SELECT exp_string, answer FROM daily WHERE date = %s AND number = %s", (today, next_number))
            exercise = cur.fetchone()

            if not exercise:
                await update.message.reply_text("Gratulacje! Ukończyłeś wszystkie zadania na dzisiaj!")
                return

            exp_string, answer = exercise
            context.user_data['current_exercise'] = {'number': next_number, 'answer': answer}
            
            cur.execute("INSERT INTO tries (date, number, user_id, completed) VALUES (%s, %s, %s, %s)", (today, next_number, user_id, False))
            conn.commit()

            await update.message.reply_text(f"Rozwiąż następujące zadanie: {exp_string}")

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        await update.message.reply_text("Wystąpił błąd bazy danych.")
    finally:
        if conn:
            conn.close()

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles user's answers to maths problems."""
    if 'current_exercise' not in context.user_data:
        return

    user_answer = update.message.text
    correct_answer = str(context.user_data['current_exercise']['answer'])
    exercise_number = context.user_data['current_exercise']['number']
    user_id = update.effective_user.id
    today = datetime.date.today()

    if user_answer == correct_answer:
        conn = get_db_connection()
        if not conn:
            await update.message.reply_text("Błąd połączenia z bazą danych.")
            return
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE tries SET completed = TRUE WHERE user_id = %s AND date = %s AND number = %s", (user_id, today, exercise_number))
                conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            await update.message.reply_text("Wystąpił błąd bazy danych.")
        finally:
            if conn:
                conn.close()
        
        await update.message.reply_text("Poprawna odpowiedź!")
        del context.user_data['current_exercise']
        await go_command(update, context)
    else:
        conn = get_db_connection()
        if not conn:
            await update.message.reply_text("Błąd połączenia z bazą danych.")
            return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT exp_string FROM daily WHERE date = %s AND number = %s", (today, exercise_number))
                exercise = cur.fetchone()
                if exercise:
                    await update.message.reply_text(f"Zła odpowiedź. Spróbuj jeszcze raz: {exercise[0]}")
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            await update.message.reply_text("Wystąpił błąd bazy danych.")
        finally:
            if conn:
                conn.close()

def main() -> None:
    """Start the bot."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
        exit(1)

    db_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    if not all(os.environ.get(var) for var in db_vars):
        logger.error("Database environment variables not set.")
        exit(1)

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("go", go_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    logger.info("Bot started polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
