
import datetime
import json
import os
import random
import psycopg2

random.seed(42)

# Configuration Constants
DAYS_FROM = 0
DAYS_TO = 0
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
    x = random.randint(1, 20)
    y = random.randint(1, 20)
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
        for day_offset in range(DAYS_FROM, DAYS_TO + 1):
            current_date = today + datetime.timedelta(days=day_offset)
            number = 0
            
            # Easy problems
            for _ in range(NUM_EASY_PROBLEMS):
                exp_string, answer, rpn_exp = generate_easy_problem()
                cur.execute(
                    "INSERT INTO daily (date, number, exp_string, answer, exp) VALUES (%s, %s, %s, %s, %s)",
                    (current_date, number, exp_string, answer, rpn_exp)
                )
                number += 1
            
            # Medium problems
            for _ in range(NUM_MEDIUM_PROBLEMS):
                exp_string, answer, rpn_exp = generate_medium_problem()
                cur.execute(
                    "INSERT INTO daily (date, number, exp_string, answer, exp) VALUES (%s, %s, %s, %s, %s)",
                    (current_date, number, exp_string, answer, rpn_exp)
                )
                number += 1

            # Hard problems
            for _ in range(NUM_HARD_PROBLEMS):
                exp_string, answer, rpn_exp = generate_hard_problem()
                cur.execute(
                    "INSERT INTO daily (date, number, exp_string, answer, exp) VALUES (%s, %s, %s, %s, %s)",
                    (current_date, number, exp_string, answer, rpn_exp)
                )
                number += 1
        
        conn.commit()
        cur.close()
        conn.close()
        print("Successfully generated and inserted problems.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    main()

