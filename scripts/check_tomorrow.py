
import os
import datetime
import psycopg2
import telegram

# --- Configuration ---
CUSTOM_TODAY_DATE = None

async def main():
    try:
        # --- Database Connection ---
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            port=os.environ.get('DB_PORT'),
            dbname=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD')
        )
        cur = conn.cursor()

        # --- Date Handling ---
        if CUSTOM_TODAY_DATE:
            today = datetime.datetime.strptime(CUSTOM_TODAY_DATE, "%Y-%m-%d").date()
        else:
            today = datetime.date.today()
        
        tomorrow = today + datetime.timedelta(days=1)

        # --- Database Check ---
        cur.execute("SELECT COUNT(*) FROM daily WHERE date = %s", (tomorrow,))
        problem_count = cur.fetchone()[0]

        # --- Admin Notification ---
        if problem_count == 0:
            admin_user_list = os.environ.get('ADMIN_USER_LIST', '').split(',')
            bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')

            if not bot_token:
                print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
                return

            if not admin_user_list or admin_user_list == ['']:
                print("Warning: ADMIN_USER_LIST environment variable not set or empty.")
                return

            bot = telegram.Bot(token=bot_token)
            message = "There are no math problems for tomorrow. Generate some!"

            for admin_id in admin_user_list:
                if admin_id:
                    try:
                        await bot.send_message(chat_id=admin_id, text=message)
                        print(f"Notification sent to admin {admin_id}")
                    except telegram.error.TelegramError as e:
                        print(f"Failed to send message to admin {admin_id}: {e}")
        else:
            print(f"Found {problem_count} problems for tomorrow. No notification sent.")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
