import logging
import os
import psycopg2
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import datetime
from auth import whitelisted

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

@whitelisted
async def go_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a new maths challenge."""
    user = update.effective_user
    user_id = user.id
    conn = get_db_connection()
    if not conn:
        await update.message.reply_text("Błąd połączenia z bazą danych.")
        return

    try:
        with conn.cursor() as cur:
            today = datetime.date.today()

            # Get the total number of tasks for today
            cur.execute("SELECT COUNT(*) FROM daily WHERE date = %s", (today,))
            total_tasks = cur.fetchone()[0]

            # Find the smallest 'number' that is not completed for this user and date
            cur.execute(
                "SELECT d.number FROM daily d LEFT JOIN tries t ON d.date = t.date AND d.number = t.number AND t.user_id = %s WHERE d.date = %s AND (t.completed IS NULL OR t.completed = FALSE) ORDER BY d.number ASC LIMIT 1",
                (user_id, today)
            )
            next_uncompleted_task = cur.fetchone()

            if next_uncompleted_task:
                next_number = next_uncompleted_task[0]
            else:
                # All tasks are completed for today or no tasks exist
                next_number = total_tasks # Set to total_tasks to trigger completion message below

            if next_number >= total_tasks:
                await update.message.reply_text("Gratulacje! Ukończyłeś wszystkie zadania na dzisiaj!")
                admin_user_list = os.environ.get('ADMIN_USER_LIST', '').split(',')
                for admin_id in admin_user_list:
                    if admin_id:
                        await context.bot.send_message(chat_id=admin_id, text=f"Użytkownik {user.mention_html()} ukończył wszystkie zadania na dzisiaj.", parse_mode=ParseMode.HTML)
                return

            cur.execute("SELECT exp_string, answer FROM daily WHERE date = %s AND number = %s", (today, next_number))
            exercise = cur.fetchone()

            if not exercise:
                # This case should ideally not be reached if next_uncompleted_task was found
                await update.message.reply_text("Wystąpił problem z pobraniem zadania.")
                return

            exp_string, answer = exercise
            
            # Record the attempt if it doesn't exist, or update if it does (for retries)
            cur.execute(
                "INSERT INTO tries (date, number, user_id, completed) VALUES (%s, %s, %s, FALSE) ON CONFLICT (date, number, user_id) DO NOTHING",
                (today, next_number, user_id)
            )
            conn.commit()

            await update.message.reply_text(f"{next_number + 1} z {total_tasks}\n\nRozwiąż następujące zadanie: {exp_string}")

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        await update.message.reply_text("Wystąpił błąd bazy danych.")
    finally:
        if conn:
            conn.close()

@whitelisted
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles user's answers to maths problems."""
    user_id = update.effective_user.id
    today = datetime.date.today()
    user_answer = update.message.text
    
    conn = get_db_connection()
    if not conn:
        await update.message.reply_text("Błąd połączenia z bazą danych.")
        return
        
    try:
        with conn.cursor() as cur:
            # Find the current uncompleted task
            cur.execute(
                "SELECT t.number, d.answer, d.exp_string FROM tries t JOIN daily d ON t.date = d.date AND t.number = d.number WHERE t.user_id = %s AND t.date = %s AND t.completed = FALSE ORDER BY t.number DESC LIMIT 1",
                (user_id, today)
            )
            current_problem_data = cur.fetchone()

            if not current_problem_data:
                # No current uncompleted problem, possibly already completed or not started
                return

            exercise_number, correct_answer_from_db, exp_string = current_problem_data
            correct_answer = str(correct_answer_from_db)

            cur.execute("SELECT COUNT(*) FROM daily WHERE date = %s", (today,))
            total_tasks = cur.fetchone()[0]


            if user_answer == correct_answer:
                cur.execute("UPDATE tries SET completed = TRUE WHERE user_id = %s AND date = %s AND number = %s", (user_id, today, exercise_number))
                conn.commit()
                
                await update.message.reply_text("✅✅✅Poprawna odpowiedź!")
                await go_command(update, context) # Prompt the next question
            else:
                await update.message.reply_text(f"❌❌❌\nZła odpowiedź. Spróbuj jeszcze raz.\n\n{exercise_number + 1} z {total_tasks}\n\nRozwiąż następujące zadanie: {exp_string}")

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        await update.message.reply_text("Wystąpił błąd bazy danych.")
    finally:
        if conn:
            conn.close()


@whitelisted
async def resume_or_handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resumes a challenge or handles an answer."""
    user_id = update.effective_user.id
    today = datetime.date.today()
    
    conn = get_db_connection()
    if not conn:
        await update.message.reply_text("Błąd połączenia z bazą danych.")
        return
        
    try:
        with conn.cursor() as cur:
            # Check if there's any uncompleted task for the user today
            cur.execute("SELECT number FROM tries WHERE user_id = %s AND date = %s AND completed = FALSE LIMIT 1", (user_id, today))
            uncompleted_task = cur.fetchone()

            if uncompleted_task:
                await handle_answer(update, context)
            else:
                await update.message.reply_text("Nie masz aktywnego zadania. Wciśnij /go")
                return
            # If there is no current try, do nothing and wait for /go
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
    
    if not os.environ.get('USER_WHITELIST'):
        logger.warning("USER_WHITELIST environment variable not set. No users will be able to use the bot.")
    
    if not os.environ.get('ADMIN_USER_LIST'):
        logger.warning("ADMIN_USER_LIST environment variable not set. No admins will receive notifications.")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("go", go_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, resume_or_handle_answer))

    logger.info("Bot started polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
