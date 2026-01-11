
import datetime
import json
import os
import random
import psycopg2

# random.seed(43)

# Configuration Constants
DAYS_FROM = 1
DAYS_TO = 1
NUM_EASY_PROBLEMS = 5
NUM_MEDIUM_PROBLEMS = 3
NUM_HARD_PROBLEMS = 2

def generate_easy_problem():
    """Generates an easy problem (X * Y)."""
    x = random.randint(1, 10)
    y = random.randint(1, 10)
    exp_string = f"{x} * {y}"
    answer = x * y
    rpn_exp = [f"num({x})", f"num({y})", "op(mul)"]
    return exp_string, answer, json.dumps(rpn_exp)

def generate_medium_problem():
    """Generates a medium problem (X * Y + Z or X * Y - Z)."""
    x = random.randint(1, 10)
    y = random.randint(1, 10)
    z = random.randint(1, 100)
    
    term1 = x * y
    
    if random.choice([True, False]): # True for addition, False for subtraction
        exp_string = f"{x} * {y} + {z}"
        answer = term1 + z
        rpn_exp = [f"num({x})", f"num({y})", "op(mul)", f"num({z})", "op(add)"]
    else:
        # Subtraction, ensure non-negative result
        if term1 < z:
            exp_string = f"{z} - {x} * {y}"
            answer = z - term1
            rpn_exp = [f"num({z})", f"num({x})", f"num({y})", "op(mul)", "op(sub)"]
        else:
            exp_string = f"{x} * {y} - {z}"
            answer = term1 - z
            rpn_exp = [f"num({x})", f"num({y})", "op(mul)", f"num({z})", "op(sub)"]
        
    return exp_string, answer, json.dumps(rpn_exp)

def generate_hard_problem():
    """Generates a hard problem (X * Y +/- Z * W)."""
    x = random.randint(1, 10)
    y = random.randint(1, 10)
    z = random.randint(1, 10)
    w = random.randint(1, 10)
    
    if random.choice([True, False]):
        # Addition
        exp_string = f"{x} * {y} + {z} * {w}"
        answer = x * y + z * w
        rpn_exp = [f"num({x})", f"num({y})", "op(mul)", f"num({z})", f"num({w})", "op(mul)", "op(add)"]
    else:
        # Subtraction, ensuring non-negative result
        term1 = x * y
        term2 = z * w
        if term1 < term2:
            x, z = z, x
            y, w = w, y
            term1, term2 = term2, term1
            
        exp_string = f"{x} * {y} - {z} * {w}"
        answer = term1 - term2
        rpn_exp = [f"num({x})", f"num({y})", "op(mul)", f"num({z})", f"num({w})", "op(mul)", "op(sub)"]
        
    return exp_string, answer, json.dumps(rpn_exp)

def main():
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST'),
            port=os.environ.get('DB_PORT'),
            dbname=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD')
        )
        cur = conn.cursor()

        today = datetime.date.today()
        total_tasks_per_day = NUM_EASY_PROBLEMS + NUM_MEDIUM_PROBLEMS + NUM_HARD_PROBLEMS

        for day_offset in range(DAYS_FROM, DAYS_TO + 1):
            current_date = today + datetime.timedelta(days=day_offset)
            print(f"--- Generating problems for {current_date} ---")
            
            number = 0
            
            problem_generators = {
                "easy": (generate_easy_problem, NUM_EASY_PROBLEMS),
                "medium": (generate_medium_problem, NUM_MEDIUM_PROBLEMS),
                "hard": (generate_hard_problem, NUM_HARD_PROBLEMS),
            }

            for level, (generator, count) in problem_generators.items():
                for _ in range(count):
                    while True:
                        exp_string, answer, rpn_exp = generator()
                        
                        print(f"\nDate: {current_date}")
                        print(f"Problem: {number + 1} of {total_tasks_per_day} ({level})")
                        print(f"Expression: {exp_string}")
                        
                        user_input = input("Press Enter to approve, or enter any text to reroll: ")
                        
                        if user_input == "":
                            cur.execute(
                                "INSERT INTO daily (date, number, exp_string, answer, exp) VALUES (%s, %s, %s, %s, %s)",
                                (current_date, number, exp_string, answer, rpn_exp)
                            )
                            number += 1
                            break
                        else:
                            print("Rerolling...")
        
        conn.commit()
        cur.close()
        conn.close()
        print("\nSuccessfully generated and inserted all problems.")

    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")

if __name__ == "__main__":
    main()

