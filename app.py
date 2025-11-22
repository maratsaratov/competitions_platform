from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import bcrypt
import re

app = Flask(__name__)
app.config.from_object('config.Config')

# Утилиты для паролей
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_db_connection():
    return psycopg2.connect(**app.config['DB_CONFIG'])

# Главная страница
@app.route('/')
def index():
    if 'user_id' in session and 'role' in session:
        if session['role'] == 'organizer':
            return redirect(f"/organizer/{session['user_id']}")
        else:
            return redirect(f"/participant/{session['user_id']}")
    
    return render_template('index.html')

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    role = request.form['role']
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if role == 'organizer':
            cur.execute("SELECT ID_Организатор, password_hash FROM Организатор WHERE Фамилия = %s", (email,))
        else:
            cur.execute("SELECT ID_Участник, password_hash FROM Участник WHERE Фамилия = %s", (email,))
        
        user = cur.fetchone()
        
        if user and check_password(password, user[1]):
            session['user_id'] = user[0]
            session['role'] = role
            session['email'] = email
            
            if role == 'organizer':
                return redirect(f"/organizer/{user[0]}")
            else:
                return redirect(f"/participant/{user[0]}")
        else:
            flash('Неверный email или пароль', 'error')
            return render_template('login.html')
    
    except Exception as e:
        flash(f'Ошибка при входе: {str(e)}', 'error')
        return render_template('login.html')
    finally:
        cur.close()
        conn.close()

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    role = request.form['role']
    email = request.form['email']
    password = request.form['password']
    last_name = request.form['last_name']
    first_name = request.form['first_name']
    patronymic = request.form.get('patronymic', '')
    
    if not is_valid_email(email):
        flash('Неверный формат email', 'error')
        return render_template('register.html')
    
    if len(password) < 6:
        flash('Пароль должен быть не менее 6 символов', 'error')
        return render_template('register.html')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем уникальность email (используем поле Фамилия)
        if role == 'organizer':
            cur.execute("SELECT 1 FROM Организатор WHERE Фамилия = %s", (email,))
        else:
            cur.execute("SELECT 1 FROM Участник WHERE Фамилия = %s", (email,))
        
        if cur.fetchone():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('register.html')
        
        password_hash = hash_password(password)
        
        if role == 'organizer':
            position = request.form.get('position', 'Организатор')
            qualification = request.form.get('qualification', 'Базовая')
            
            cur.execute("""
                INSERT INTO Организатор (Фамилия, Имя, Отчество, Должность, Квалификация, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING ID_Организатор
            """, (email, first_name, patronymic, position, qualification, password_hash))
            
            user_id = cur.fetchone()[0]
        else:
            education = request.form.get('education', 'Не указано')
            rating = request.form.get('rating', 0)
            
            cur.execute("""
                INSERT INTO Участник (Фамилия, Имя, Отчество, Место_обучения, Рейтинг, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING ID_Участник
            """, (email, first_name, patronymic, education, rating, password_hash))
            
            user_id = cur.fetchone()[0]
        
        conn.commit()
        
        session['user_id'] = user_id
        session['role'] = role
        session['email'] = email
        
        flash('Регистрация успешна!', 'success')
        
        if role == 'organizer':
            return redirect(f"/organizer/{user_id}")
        else:
            return redirect(f"/participant/{user_id}")
    
    except Exception as e:
        conn.rollback()
        flash(f'Ошибка при регистрации: {str(e)}', 'error')
        return render_template('register.html')
    finally:
        cur.close()
        conn.close()

# Выход
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect('/')

# Панель организатора
@app.route('/organizer/<int:org_id>')
def organizer_dashboard(org_id):
    if 'user_id' not in session or session['user_id'] != org_id or session['role'] != 'organizer':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем информацию об организаторе
    cur.execute("SELECT Фамилия, Имя, Отчество, Должность FROM Организатор WHERE ID_Организатор = %s", (org_id,))
    organizer = cur.fetchone()
    
    # Статистика
    cur.execute("SELECT COUNT(*) FROM Соревнование WHERE ID_Организатор = %s", (org_id,))
    comp_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM Команда")
    teams_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Панель организатора</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="nav-logo">Соревнования</a>
                <div class="nav-menu">
                    <span class="nav-user">Организатор: {organizer[1]} {organizer[0]}</span>
                    <a href="/logout" class="nav-link">Выйти</a>
                </div>
            </div>
        </nav>
        
        <main class="main-content">
            <h1>Панель организатора</h1>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{comp_count}</div>
                    <div class="stat-label">Соревнований</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{teams_count}</div>
                    <div class="stat-label">Команд</div>
                </div>
            </div>
            
            <div class="card">
                <h3>Быстрые действия</h3>
                <a href="/organizer/{org_id}/competitions" class="btn">Мои соревнования</a>
                <a href="/organizer/{org_id}/teams" class="btn">Управление командами</a>
            </div>
        </main>
    </body>
    </html>
    '''

# Панель участника
@app.route('/participant/<int:part_id>')
def participant_dashboard(part_id):
    if 'user_id' not in session or session['user_id'] != part_id or session['role'] != 'participant':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем информацию об участнике
    cur.execute("""
        SELECT Фамилия, Имя, Отчество, Рейтинг, Место_обучения, ID_Команда 
        FROM Участник WHERE ID_Участник = %s
    """, (part_id,))
    participant = cur.fetchone()
    
    # Команда участника
    team_name = "Не в команде"
    if participant[5]:
        cur.execute("SELECT Название FROM Команда WHERE ID_Команда = %s", (participant[5],))
        team_result = cur.fetchone()
        if team_result:
            team_name = team_result[0]
    
    # Результаты
    cur.execute("""
        SELECT с.Название, р.Место, р.Баллы 
        FROM Результаты р 
        JOIN Соревнование с ON р.ID_Соревнование = с.ID_Соревнование 
        WHERE р.ID_Участник = %s
    """, (part_id,))
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    results_html = ""
    for result in results:
        results_html += f'<p>{result[0]} - Место: {result[1]}, Баллы: {result[2]}</p>'
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Личный кабинет</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="nav-logo">Соревнования</a>
                <div class="nav-menu">
                    <span class="nav-user">Участник: {participant[1]} {participant[0]}</span>
                    <a href="/logout" class="nav-link">Выйти</a>
                </div>
            </div>
        </nav>
        
        <main class="main-content">
            <h1>Личный кабинет участника</h1>
            
            <div class="card">
                <h3>Мои данные</h3>
                <p><strong>ФИО:</strong> {participant[0]} {participant[1]} {participant[2]}</p>
                <p><strong>Рейтинг:</strong> {participant[3]}</p>
                <p><strong>Место обучения:</strong> {participant[4]}</p>
                <p><strong>Команда:</strong> {team_name}</p>
            </div>
            
            <div class="card">
                <h3>Мои результаты</h3>
                {results_html if results_html else '<p>Пока нет результатов</p>'}
            </div>
            
            <div class="card">
                <h3>Действия</h3>
                <a href="/participant/{part_id}/join-team" class="btn">Присоединиться к команде</a>
                <a href="/participant/{part_id}/competitions" class="btn">Записаться на соревнование</a>
            </div>
        </main>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)