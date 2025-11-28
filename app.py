from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import bcrypt
import re
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

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

@app.route('/')
def index():
    if 'user_id' in session and 'role' in session:
        if session['role'] == 'organizer':
            return redirect(f"/organizer/{session['user_id']}")
        else:
            return redirect(f"/participant/{session['user_id']}")
    
    return render_template('index.html')

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
            
            cur.execute("""
                INSERT INTO Участник (Фамилия, Имя, Отчество, Место_обучения, Рейтинг, password_hash)
                VALUES (%s, %s, %s, %s, 0, %s) RETURNING ID_Участник
            """, (email, first_name, patronymic, education, password_hash))
            
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

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect('/')

@app.route('/organizer/<int:org_id>')
def organizer_dashboard(org_id):
    if 'user_id' not in session or session['user_id'] != org_id or session['role'] != 'organizer':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT Фамилия, Имя, Отчество, Должность FROM Организатор WHERE ID_Организатор = %s", (org_id,))
    organizer = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM Соревнование WHERE ID_Организатор = %s", (org_id,))
    comp_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Команда")
    teams_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Участник")
    participants_count = cur.fetchone()[0]
    cur.execute("""
        SELECT ID_Соревнование, Название, Тип_соревнования 
        FROM Соревнование 
        WHERE ID_Организатор = %s 
        ORDER BY ID_Соревнование DESC LIMIT 5
    """, (org_id,))
    recent_competitions = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('organizer/dashboard.html',
                         organizer=organizer,
                         org_id=org_id,
                         comp_count=comp_count,
                         teams_count=teams_count,
                         participants_count=participants_count,
                         recent_competitions=recent_competitions)

@app.route('/organizer/<int:org_id>/competitions')
def organizer_competitions(org_id):
    if 'user_id' not in session or session['user_id'] != org_id or session['role'] != 'organizer':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ID_Соревнование, Название, Тип_соревнования, Место_проведения, Даты_проведения
        FROM Соревнование 
        WHERE ID_Организатор = %s
        ORDER BY ID_Соревнование DESC
    """, (org_id,))
    competitions = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('organizer/competitions.html', 
                         competitions=competitions,
                         org_id=org_id)

@app.route('/organizer/<int:org_id>/competitions/add', methods=['GET', 'POST'])
def organizer_add_competition(org_id):
    if 'user_id' not in session or session['user_id'] != org_id or session['role'] != 'organizer':
        return redirect('/login')
    
    if request.method == 'GET':
        return render_template('organizer/add_competition.html', org_id=org_id)
    
    name = request.form['name']
    comp_type = request.form['type']
    location = request.form['location']
    dates = request.form['dates']    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        date_range = f"[{dates.replace(' - ', ',')}]"
        cur.execute("""
            INSERT INTO Соревнование (ID_Организатор, Название, Тип_соревнования, Место_проведения, Даты_проведения)
            VALUES (%s, %s, %s, %s, %s)
        """, (org_id, name, comp_type, location, date_range))
        
        conn.commit()
        flash('Соревнование создано успешно!', 'success')
        return redirect(f'/organizer/{org_id}/competitions')
    
    except Exception as e:
        conn.rollback()
        flash(f'Ошибка при создании соревнования: {str(e)}', 'error')
        return render_template('organizer/add_competition.html', org_id=org_id)
    finally:
        cur.close()
        conn.close()

@app.route('/organizer/<int:org_id>/competition/<int:comp_id>')
def organizer_competition_detail(org_id, comp_id):
    if 'user_id' not in session or session['user_id'] != org_id or session['role'] != 'organizer':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT Название, Тип_соревнования, Место_проведения, Даты_проведения
        FROM Соревнование 
        WHERE ID_Соревнование = %s AND ID_Организатор = %s
    """, (comp_id, org_id))
    competition = cur.fetchone()
    
    if not competition:
        flash('Соревнование не найдено', 'error')
        return redirect(f'/organizer/{org_id}/competitions')

    cur.execute("""
        SELECT DISTINCT к.ID_Команда, к.Название, COUNT(р.ID_Участник) as участников
        FROM Команда к
        JOIN Результаты р ON к.ID_Команда = р.ID_Команда
        WHERE р.ID_Соревнование = %s
        GROUP BY к.ID_Команда, к.Название
    """, (comp_id,))
    teams = cur.fetchall()
    cur.execute("""
        SELECT у.ID_Участник, у.Фамилия, у.Имя, у.Отчество, у.Рейтинг
        FROM Участник у
        JOIN Результаты р ON у.ID_Участник = р.ID_Участник
        WHERE р.ID_Соревнование = %s AND у.ID_Команда IS NULL
    """, (comp_id,))
    participants_without_team = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('organizer/competition_detail.html',
                         competition=competition,
                         comp_id=comp_id,
                         org_id=org_id,
                         teams=teams,
                         participants_without_team=participants_without_team)

@app.route('/organizer/<int:org_id>/competition/<int:comp_id>/results', methods=['GET', 'POST'])
def organizer_competition_results(org_id, comp_id):
    if 'user_id' not in session or session['user_id'] != org_id or session['role'] != 'organizer':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT Название FROM Соревнование WHERE ID_Соревнование = %s AND ID_Организатор = %s", 
                (comp_id, org_id))
    competition = cur.fetchone()
    
    if not competition:
        flash('Соревнование не найдено', 'error')
        return redirect(f'/organizer/{org_id}/competitions')
    
    if request.method == 'POST':
        try:
            team_scores = {}
            for key, value in request.form.items():
                if key.startswith('points_'):
                    team_id = key.replace('points_', '')
                    points = float(value) if value else 0.0
                    team_scores[team_id] = points

            sorted_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)
            current_place = 1
            previous_score = None
            skip_places = 0
            
            for i, (team_id, score) in enumerate(sorted_teams):
                if score == previous_score:
                    skip_places += 1
                else:
                    current_place += skip_places
                    skip_places = 0
                    if i > 0:
                        current_place += 1

                cur.execute("""
                    UPDATE Результаты 
                    SET Баллы = %s, Место = %s
                    WHERE ID_Соревнование = %s AND ID_Команда = %s
                """, (score, current_place, comp_id, team_id))
                
                previous_score = score
            
            conn.commit()
            flash('Баллы и места успешно обновлены! Соревнование завершено.', 'success')
            return redirect(f'/organizer/{org_id}/competitions')
        
        except Exception as e:
            conn.rollback()
            flash(f'Ошибка при обновлении баллов: {str(e)}', 'error')

    cur.execute("""
        SELECT 
            к.ID_Команда, 
            к.Название, 
            COALESCE(AVG(р.Баллы), 0) as средние_баллы,
            MIN(р.Место) as текущее_место
        FROM Команда к
        LEFT JOIN Результаты р ON к.ID_Команда = р.ID_Команда AND р.ID_Соревнование = %s
        WHERE к.ID_Команда IN (
            SELECT DISTINCT ID_Команда FROM Результаты WHERE ID_Соревнование = %s AND ID_Команда IS NOT NULL
        )
        GROUP BY к.ID_Команда, к.Название
        ORDER BY средние_баллы DESC
    """, (comp_id, comp_id))
    teams_with_scores = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('organizer/competition_results.html',
                         competition=competition[0],
                         comp_id=comp_id,
                         org_id=org_id,
                         teams_with_scores=teams_with_scores)

@app.route('/participant/<int:part_id>')
def participant_dashboard(part_id):
    if 'user_id' not in session or session['user_id'] != part_id or session['role'] != 'participant':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT Фамилия, Имя, Отчество, Рейтинг, Место_обучения, ID_Команда 
        FROM Участник WHERE ID_Участник = %s
    """, (part_id,))
    participant = cur.fetchone()
    team_name = "Не в команде"
    if participant[5]:
        cur.execute("SELECT Название FROM Команда WHERE ID_Команда = %s", (participant[5],))
        team_result = cur.fetchone()
        if team_result:
            team_name = team_result[0]

    cur.execute("""
        SELECT с.ID_Соревнование, с.Название, с.Тип_соревнования
        FROM Соревнование с
        WHERE с.ID_Соревнование NOT IN (
            SELECT р.ID_Соревнование FROM Результаты р WHERE р.ID_Участник = %s
        )
        ORDER BY с.ID_Соревнование DESC
        LIMIT 5
    """, (part_id,))
    available_competitions = cur.fetchall()
    cur.execute("""
        SELECT с.Название, р.Место, р.Баллы 
        FROM Результаты р 
        JOIN Соревнование с ON р.ID_Соревнование = с.ID_Соревнование 
        WHERE р.ID_Участник = %s
        ORDER BY р.ID_Результат DESC LIMIT 5
    """, (part_id,))
    recent_results = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('participant/dashboard.html',
                         participant=participant,
                         part_id=part_id,
                         team_name=team_name,
                         available_competitions=available_competitions,
                         recent_results=recent_results)

@app.route('/participant/<int:part_id>/competitions')
def participant_competitions(part_id):
    if 'user_id' not in session or session['user_id'] != part_id or session['role'] != 'participant':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ID_Соревнование, Название, Тип_соревнования, Место_проведения
        FROM Соревнование 
        WHERE ID_Соревнование NOT IN (
            SELECT ID_Соревнование FROM Результаты WHERE ID_Участник = %s
        )
        ORDER BY ID_Соревнование DESC
    """, (part_id,))
    active_competitions = cur.fetchall()
    cur.execute("""
        SELECT с.Название, с.Тип_соревнования, р.Место, р.Баллы, к.Название as команда
        FROM Результаты р
        JOIN Соревнование с ON р.ID_Соревнование = с.ID_Соревнование
        LEFT JOIN Команда к ON р.ID_Команда = к.ID_Команда
        WHERE р.ID_Участник = %s AND р.Баллы > 0
        ORDER BY р.Баллы DESC
    """, (part_id,))
    completed_competitions = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('participant/competitions.html',
                         part_id=part_id,
                         active_competitions=active_competitions,
                         completed_competitions=completed_competitions)

@app.route('/participant/<int:part_id>/competition/<int:comp_id>/register', methods=['GET', 'POST'])
def participant_register_competition(part_id, comp_id):
    if 'user_id' not in session or session['user_id'] != part_id or session['role'] != 'participant':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT Название, Тип_соревнования FROM Соревнование WHERE ID_Соревнование = %s", (comp_id,))
    competition = cur.fetchone()
    
    if not competition:
        flash('Соревнование не найдено', 'error')
        return redirect(f'/participant/{part_id}/competitions')
    
    cur.execute("SELECT 1 FROM Результаты WHERE ID_Участник = %s AND ID_Соревнование = %s", (part_id, comp_id))
    if cur.fetchone():
        flash('Вы уже зарегистрированы на это соревнование', 'error')
        return redirect(f'/participant/{part_id}/competitions')

    cur.execute("SELECT ID_Команда, Название FROM Команда ORDER BY Название")
    available_teams = cur.fetchall()
    
    if request.method == 'POST':
        team_choice = request.form['team_choice']
        
        try:
            if team_choice == 'no_team':
                individual_team_name = f"Индивидуальный_{part_id}_{comp_id}"
                cur.execute("""
                    INSERT INTO Команда (Название, Ментор_команды) 
                    VALUES (%s, 'Индивидуальный участник') 
                    RETURNING ID_Команда
                """, (individual_team_name,))
                individual_team_id = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO Результаты (ID_Соревнование, ID_Участник, ID_Команда, Место, Баллы)
                    VALUES (%s, %s, %s, NULL, 0)
                """, (comp_id, part_id, individual_team_id))
            
            elif team_choice == 'new_team':
                team_name = request.form['team_name']
                team_mentor = request.form.get('team_mentor', '')
                cur.execute("SELECT 1 FROM Команда WHERE Название = %s", (team_name,))
                if cur.fetchone():
                    flash('Команда с таким названием уже существует', 'error')
                    return render_template('participant/register_competition.html',
                                         competition=competition,
                                         comp_id=comp_id,
                                         part_id=part_id,
                                         available_teams=available_teams)
                
                cur.execute("INSERT INTO Команда (Название, Ментор_команды) VALUES (%s, %s) RETURNING ID_Команда", 
                           (team_name, team_mentor))
                new_team_id = cur.fetchone()[0]
                cur.execute("UPDATE Участник SET ID_Команда = %s WHERE ID_Участник = %s", (new_team_id, part_id))
                cur.execute("""
                    INSERT INTO Результаты (ID_Соревнование, ID_Участник, ID_Команда, Место, Баллы)
                    VALUES (%s, %s, %s, NULL, 0)
                """, (comp_id, part_id, new_team_id))
            
            else:
                team_id = int(team_choice)
                cur.execute("UPDATE Участник SET ID_Команда = %s WHERE ID_Участник = %s", (team_id, part_id))
                cur.execute("""
                    INSERT INTO Результаты (ID_Соревнование, ID_Участник, ID_Команда, Место, Баллы)
                    VALUES (%s, %s, %s, NULL, 0)
                """, (comp_id, part_id, team_id))
            
            conn.commit()
            flash('Регистрация на соревнование прошла успешно!', 'success')
            return redirect(f'/participant/{part_id}/competitions')
        
        except Exception as e:
            conn.rollback()
            flash(f'Ошибка при регистрации: {str(e)}', 'error')
    
    cur.close()
    conn.close()
    
    return render_template('participant/register_competition.html',
                         competition=competition,
                         comp_id=comp_id,
                         part_id=part_id,
                         available_teams=available_teams)

@app.route('/participant/<int:part_id>/results')
def participant_results(part_id):
    if 'user_id' not in session or session['user_id'] != part_id or session['role'] != 'participant':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT с.Название, с.Тип_соревнования, р.Место, р.Баллы, к.Название as команда
        FROM Результаты р
        JOIN Соревнование с ON р.ID_Соревнование = с.ID_Соревнование
        LEFT JOIN Команда к ON р.ID_Команда = к.ID_Команда
        WHERE р.ID_Участник = %s
        ORDER BY р.Баллы DESC
    """, (part_id,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('participant/results.html',
                         results=results,
                         part_id=part_id)

if __name__ == '__main__':
    app.run(debug=True)