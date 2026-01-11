CREATE DATABASE maths;
CREATE USER maths WITH PASSWORD 'pwd';
GRANT ALL PRIVILEGES ON DATABASE maths TO maths;
ALTER DATABASE maths OWNER TO maths;

CREATE TABLE maths.public.daily (
    date DATE,
    number INT,
    exp_string VARCHAR(255),
    answer INT,
    exp JSON
);

alter table daily
add primary key (date, number)
;

CREATE TABLE tries (
    date DATE,
    number INT,
    user_id BIGINT,
    completed Bool
);


alter table tries
add primary key (date, number, user_id)
