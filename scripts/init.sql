CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    full_name VARCHAR(255),
    level VARCHAR(20),
    birth_date DATE,
    phone VARCHAR(50),
    city VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tournaments (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    category_type VARCHAR(50) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    location VARCHAR(255),
    group_format JSONB,
    bracket_size INTEGER DEFAULT 8,
    status VARCHAR(50) DEFAULT 'upcoming',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tournament_pairs (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    player1_name VARCHAR(255) NOT NULL,
    player2_name VARCHAR(255),
    group_number INTEGER,
    seed INTEGER,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    group_number INTEGER NOT NULL,
    pair1_id INTEGER REFERENCES tournament_pairs(id),
    pair2_id INTEGER REFERENCES tournament_pairs(id),
    score_pair1 VARCHAR(50),
    score_pair2 VARCHAR(50),
    winner_pair_id INTEGER REFERENCES tournament_pairs(id),
    played_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bracket_matches (
    id SERIAL PRIMARY KEY,
    tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
    round INTEGER NOT NULL,
    match_number INTEGER NOT NULL,
    pair1_id INTEGER REFERENCES tournament_pairs(id),
    pair2_id INTEGER REFERENCES tournament_pairs(id),
    score_pair1 VARCHAR(50),
    score_pair2 VARCHAR(50),
    winner_pair_id INTEGER REFERENCES tournament_pairs(id)
);

CREATE TABLE IF NOT EXISTS ratings (
    id SERIAL PRIMARY KEY,
    place INTEGER,
    full_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    level VARCHAR(50),
    total_points INTEGER DEFAULT 0,
    tournaments_played INTEGER DEFAULT 0,
    gender VARCHAR(10) DEFAULT 'male',
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Admin user: password = admin123
INSERT INTO users (email, password_hash, is_superuser) VALUES
  ('admin@padelhub.ru', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGTRBMEsJqg9hHJJWzNJGVm7hOm', TRUE)
ON CONFLICT (email) DO NOTHING;

INSERT INTO profiles (user_id, full_name, city) VALUES
  (1, 'Администратор', 'Москва')
ON CONFLICT (user_id) DO NOTHING;

-- Seed ratings
INSERT INTO ratings (place, full_name, city, level, total_points, tournaments_played, gender) VALUES
(1,'Иванов Александр Петрович','Москва','5.0',1250,12,'male'),
(2,'Петров Дмитрий Сергеевич','Санкт-Петербург','4.5',1180,10,'male'),
(3,'Сидоров Михаил Владимирович','Казань','4.5',1050,9,'male'),
(4,'Козлов Андрей Николаевич','Москва','4.0',980,11,'male'),
(5,'Новиков Павел Игоревич','Екатеринбург','4.0',920,8,'male'),
(6,'Морозов Алексей Дмитриевич','Москва','3.5',870,10,'male'),
(7,'Волков Иван Андреевич','Нижний Новгород','3.5',820,7,'male'),
(8,'Соколов Сергей Михайлович','Москва','3.5',780,9,'male'),
(9,'Попов Николай Алексеевич','Краснодар','3.0',730,8,'male'),
(10,'Лебедев Виктор Петрович','Санкт-Петербург','3.0',690,7,'male'),
(1,'Смирнова Ольга Ивановна','Москва','4.5',1100,11,'female'),
(2,'Кузнецова Татьяна Александровна','Москва','4.0',980,10,'female'),
(3,'Попова Анна Сергеевна','Санкт-Петербург','4.0',920,9,'female'),
(4,'Новикова Елена Викторовна','Казань','3.5',850,8,'female'),
(5,'Федорова Ирина Николаевна','Москва','3.5',800,10,'female')
ON CONFLICT DO NOTHING;

-- Seed demo tournament
INSERT INTO tournaments (title, category, category_type, description, start_date, end_date, location, group_format, bracket_size, status, created_by)
VALUES (
  'Открытый Кубок Москвы 2025',
  'A+100',
  'men_doubles',
  'Ежегодный открытый кубок по падел-теннису среди мужских пар. Групповой этап + плей-офф на 8 пар.',
  '2025-07-15','2025-07-20','Москва, PadelHub Арена',
  '{"total_pairs":12,"groups":4,"pairs_per_group":3}',
  8,'upcoming',1
) ON CONFLICT DO NOTHING;

INSERT INTO tournament_pairs (tournament_id, player1_name, player2_name, group_number) VALUES
(1,'Иванов А.П.','Петров Д.С.',1),
(1,'Козлов А.Н.','Новиков П.И.',1),
(1,'Морозов А.Д.','Волков И.А.',1),
(1,'Соколов С.М.','Попов Н.А.',2),
(1,'Лебедев В.П.','Кириллов О.Г.',2),
(1,'Зайцев Р.В.','Борисов К.Л.',2)
ON CONFLICT DO NOTHING;
