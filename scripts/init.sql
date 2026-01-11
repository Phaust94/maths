CREATE DATABASE maths;
CREATE USER maths WITH PASSWORD 'Gq0NO7hp4IFfKjGSetT3R5D34HW5bKK4';
GRANT ALL PRIVILEGES ON DATABASE maths TO maths;
ALTER DATABASE maths OWNER TO maths;

CREATE TABLE maths.public.daily (
    date DATE,
    number INT,
    exp_string VARCHAR(255),
    answer INT,
    exp JSON
);

CREATE TABLE tries (
    date DATE,
    number INT,
    user_id INT,
    completed Bool
);
