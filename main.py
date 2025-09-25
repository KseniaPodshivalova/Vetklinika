import base64
import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, url_for, request, flash, redirect, abort, session
from jinja2 import FileSystemLoader, Environment
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "GOKDFGIJELJ;NO;RJKJ.BKIJ"
dir = "output"
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

nav_links = {
    "Главная" : "message",
    "Услуги" : "usl",
    "Врачи" : "doc",
    "Контакты": "kont",
    "Профиль": "prof"
}


def fix_photo_data():
    conn = sql_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_pac, photo FROM Pacienti WHERE typeof(photo) = 'text'")
    text_photos = cur.fetchall()
    for row in text_photos:
        photo_str = row['photo']
        try:
            photo_bytes = base64.b64decode(photo_str)
            cur.execute("UPDATE Pacienti SET photo = ? WHERE id_pac = ?", (photo_bytes, row['id_pac']))
        except:
            print(f"Не удалось преобразовать фото пациента {row['id_pac']}")

    cur.execute("SELECT id_vr, photo FROM Vra4i WHERE typeof(photo) = 'text'")
    text_photos = cur.fetchall()
    for row in text_photos:
        photo_str = row['photo']
        try:
            photo_bytes = base64.b64decode(photo_str)
            cur.execute("UPDATE Vra4i SET photo = ? WHERE id_vr = ?", (photo_bytes, row['id_vr']))
        except:
            print(f"Не удалось преобразовать фото врача {row['id_vr']}")

    conn.commit()
    conn.close()


@app.template_filter('b64d')
def base64_filter(data):
    if data:
        if isinstance(data, bytes):
            return base64.b64encode(data).decode('utf-8')
        elif isinstance(data, str):
            try:
                base64.b64decode(data)
                return data
            except:
                return ''
    return ''


def readBLOB(n):
    try:
        with open(f"blob1/{n}.jpg", "rb") as f:
            return f.read()
    except IOError as e:
        print(e)
        return False


def sql_connection():
    con = None
    try:
        con = sqlite3.connect("db.db")
        con.row_factory = sqlite3.Row
        return con
    except sqlite3.Error as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None


def close_db_connection(conn):
    if conn:
        conn.close()


def sql(con):
    cursorObj = con.cursor()
    try:
        cursorObj.execute('''
                CREATE TABLE IF NOT EXISTS Vra4i (
                id_vr INTEGER PRIMARY KEY AUTOINCREMENT,
                FIO TEXT,
                specialnost TEXT,
                photo TEXT,
                stage INTEGER
            )''')
        print("Таблица Vra4i успешно создана или уже существовала.")

        cursorObj.execute('''
                        CREATE TABLE IF NOT EXISTS Pacienti (
                        id_pac INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        photo BLOB,
                        vid TEXT,
                        data_rozd date,
                        adress TEXT,
                        telephone INTEGER,
                        id_us INTEGER,
                        FOREIGN KEY (id_us) REFERENCES Users (id_us)
                    )''')

        print("Таблица Pacienti успешно создана или уже существовала.")

        cursorObj.execute('''
                                CREATE TABLE  IF NOT EXISTS Uslugi (
                                id_usl INTEGER PRIMARY KEY AUTOINCREMENT,
                                title TEXT,
                                price INTEGER,
                                id_vr INTEGER,
                                FOREIGN KEY (id_vr) REFERENCES Vra4i (id_vr)
                            )''')

        print("Таблица Uslugi успешно создана или уже существовала.")

        cursorObj.execute('''
                                        CREATE TABLE  IF NOT EXISTS Users (
                                        id_us INTEGER PRIMARY KEY AUTOINCREMENT,
                                        name TEXT,
                                        password Text,
                                        avatar BLOB,
                                        role TEXT CHECK(role IN ('admin', 'doctor', 'owner')) NOT NULL DEFAULT 'owner', 
                                        birth date, 
                                        address Text,
                                        tel TEXT,
                                        email TEXT
                                        

                                    )''')

        print("Таблица Users успешно создана или уже существовала.")

        cursorObj.execute('''
                    CREATE TABLE IF NOT EXISTS Vrach_Pacient (
                        id_vr INTEGER,
                        id_pac INTEGER,
                        PRIMARY KEY (id_vr, id_pac),
                        FOREIGN KEY (id_vr) REFERENCES Users(id_us),
                        FOREIGN KEY (id_pac) REFERENCES Pacienti(id_pac)
                    )
                ''')
        print("Таблица Vrach_Pacient создана")

    except Error as e:
        print(f"Ошибка при создании таблицы: {e}")

    # cursorObj.executemany("INSERT INTO Vra4i Values (?, ?, ?, ?, ?)", doctors)
    # cursorObj.executemany("INSERT INTO Pacienti Values (?, ?, ?, ?, ?, ?, ?, ?)", patients_list)
    # cursorObj.executemany("INSERT INTO Uslugi Values (?, ?, ?, ?)", ser)
    # cursorObj.executemany("INSERT INTO Users Values (?, ?, ?)", users)

    con.commit()
    cursorObj.close()


file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)


def base64_encode_and_decode(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ''


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        conn = sql_connection()
        if not conn:
            flash("Ошибка подключения к базе данных", "error")
            return render_template('login.html', nav_links=nav_links)

        try:
            cur = conn.cursor()
            cur.execute("SELECT id_us, password, role FROM Users WHERE name = ?", (name,))
            user_data = cur.fetchone()

            if user_data and check_password_hash(user_data[1], password):
                session['user_id'] = user_data[0]
                session['username'] = name
                session['role'] = user_data[2]
                session['logged_in'] = True
                print(f"{name} ({user_data[2]}) вошел в систему")
                return redirect(url_for("prof"))
            else:
                flash("Неверное имя пользователя или пароль", "error")
        except sqlite3.Error as e:
            flash(f"Ошибка базы данных: {e}", "error")
        finally:
            conn.close()

    return render_template('login.html', nav_links=nav_links, title="Логин")


@app.route("/reg", methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']
        avatar = request.files.get('avatar')

        conn = sql_connection()
        if not conn:
            flash("Ошибка подключения к базе данных", "error")
            return render_template('reg.html', nav_links=nav_links)

        try:
            cur = conn.cursor()
            cur.execute("SELECT id_us FROM Users WHERE name = ?", (name,))
            if cur.fetchone():
                flash("Пользователь с таким именем уже существует", "error")
            else:
                hashed_password = generate_password_hash(password)
                avatar = request.files.get('avatar')
                avatar_data = None
                if avatar and avatar.filename:
                    try:
                        avatar_data = avatar.read()
                    except Exception as e:
                        flash(f"Ошибка при чтении файла: {str(e)}", "error")
                cur.execute("INSERT INTO Users (name, password, avatar, role) VALUES (?, ?, ?, ?)",
                            (name, hashed_password, avatar_data, role))
                conn.commit()

                session['user_id'] = cur.lastrowid
                session['username'] = name
                session['role'] = role
                session['logged_in'] = True

                flash("Регистрация успешна!", "success")
                return redirect(url_for("prof"))

        except sqlite3.Error as e:
            flash(f"Ошибка базы данных: {e}", "error")
            conn.rollback()
            print(f"SQLite error: {e}")
        finally:
            conn.close()

    return render_template('reg.html', nav_links=nav_links)


@app.route("/logout")
def logout():
    if 'username' in session:
        print(f"Пользователь {session['username']} вышел из системы")
    session.clear()
    return redirect(url_for('index'))


@app.route("/message")
def message():
    conn = sql_connection()
    cur = conn.cursor()

    if session.get('role') == 'owner':
        cur.execute('SELECT * FROM Pacienti WHERE id_us = ?', (session['user_id'],))
    elif session.get('role') == 'doctor':
        cur.execute('''
            SELECT p.* 
            FROM Pacienti p
            JOIN Vrach_Pacient vp ON p.id_pac = vp.id_pac
            WHERE vp.id_vr = ?
        ''', (session['user_id'],))
    else:
        # Для админов - все пациенты
        cur.execute('SELECT * FROM Pacienti')

    patients_data = cur.fetchall()
    patients_list = [dict(row) for row in patients_data]

    conn.close()
    return render_template('message.html',
                           nav_links=nav_links,
                           animals=patients_list,
                           title="Пациенты")


@app.route("/message/<int:patient_id>")
def one_pac(patient_id):
    conn = sql_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Pacienti WHERE id_pac = ?", (patient_id,))
    patient_data = cur.fetchone()
    conn.close()

    if patient_data is None:
        return abort(404)

    patient_info = dict(patient_data)
    patient_info['photo'] = base64.b64encode(patient_info['photo']).decode('utf-8') if patient_info['photo'] else None

    return render_template('one_pac.html', patient=patient_info, nav_links=nav_links)


@app.route("/doc")
def doc():
    conn = sql_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM Vra4i')
    doctors = cur.fetchall()
    conn.close()

    return render_template('doc.html',
                          doc=doctors,
                          nav_links=nav_links,
                          title="Доктора")


@app.route("/doc/<int:id_vr>")
def one_doc(id_vr):
    conn = sql_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Vra4i WHERE id_vr = ?", (id_vr,))
    doc_data = cur.fetchone()
    conn.close()

    doc_info = dict(doc_data)
    doc_info['photo'] = base64.b64encode(doc_info['photo']).decode('utf-8') if doc_info['photo'] else None

    return render_template('one_doc.html', doc=doc_info, nav_links=nav_links)


@app.route("/usl")
def usl():
    conn = sql_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM Uslugi')
    ser = cur.fetchall()
    conn.close()
    return render_template('usl.html', uslugi = ser, nav_links=nav_links, title="Услуги")


@app.route("/usl/<int:id_usl>")
def one_usl(id_usl):
    conn = sql_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Uslugi WHERE id_usl = ?", (id_usl,))
    ser = cur.fetchone()
    conn.close()

    return render_template('one_usl.html', usl=ser, nav_links=nav_links)


@app.route("/kont", methods=["POST", "GET"])
def kont():
    if request.method == 'POST':
        if len(request.form['name']) > 3:
            flash('Сообщение отправлено')
            print(request.form)
        else:
            flash('Ошибка отправки')

    return render_template('kont.html', nav_links=nav_links)


@app.route("/prof")
def prof():
    if 'logged_in' not in session or not session['logged_in']:
        return render_template('auth_error.html',
                               error_message="Для доступа к этой странице требуется авторизация",
                               nav_links=nav_links), 401

    conn = sql_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, avatar, email, tel, address, birth 
            FROM Users 
            WHERE id_us = ?
        """, (session['user_id'],))
        user_data = cur.fetchone()

        if user_data:
            user_dict = dict(user_data)

            avatar_base64 = None
            if user_dict.get('avatar'):
                try:
                    if isinstance(user_dict['avatar'], bytes):
                        avatar_base64 = base64.b64encode(user_dict['avatar']).decode('utf-8')
                    elif isinstance(user_dict['avatar'], str):
                        avatar_base64 = user_dict['avatar']
                except Exception as e:
                    print(f"Ошибка обработки аватара: {e}")

            pet_data = None
            if session.get('role') == 'owner':
                cur.execute("SELECT * FROM Pacienti WHERE id_us = ?", (session['user_id'],))
                pet_row = cur.fetchone()
                if pet_row:
                    pet_data = dict(pet_row)
                    if pet_data.get('photo'):
                        try:
                            if isinstance(pet_data['photo'], bytes):
                                pet_data['photo'] = base64.b64encode(pet_data['photo']).decode('utf-8')
                            elif isinstance(pet_data['photo'], str):
                                # Если изображение уже в base64
                                pet_data['photo'] = pet_data['photo']
                        except Exception as e:
                            print(f"Ошибка обработки фото питомца: {e}")

            return render_template('prof.html',
                                   name=user_dict.get('name'),
                                   avatar=avatar_base64,
                                   email=user_dict.get('email'),
                                   telephone=user_dict.get('tel'),
                                   address=user_dict.get('address'),
                                   birth=user_dict.get('birth'),
                                   pet=pet_data,
                                   nav_links=nav_links)
        else:
            flash("Пользователь не найден", "error")
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Ошибка при получении данных: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        conn.close()


@app.route("/delete_pacient/<int:id_pac>", methods=['POST'])
def delete_pacient(id_pac):
    if session.get('role') not in ['doctor', 'admin']:
        abort(403)

    conn = sql_connection()
    try:
        cur = conn.cursor()

        if session['role'] == 'doctor':
            cur.execute('''
                DELETE FROM Vrach_Pacient 
                WHERE id_vr = ? AND id_pac = ?
            ''', (session['user_id'], id_pac))

            if cur.rowcount == 0:
                abort(403)

        cur.execute('DELETE FROM Pacienti WHERE id_pac = ?', (id_pac,))
        conn.commit()
        flash("Пациент удален", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка удаления: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for('message'))

@app.route("/edit_profile", methods=['GET', 'POST'])
def edit_profile():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        telephone = request.form.get('tel')
        address = request.form.get('address')
        birth = request.form.get('birth')

        conn = sql_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE Users 
                SET email = ?, tel = ?, address = ?, birth = ?
                WHERE id_us = ?
            """, (email, telephone, address, birth, session['user_id']))
            conn.commit()
            flash("Профиль успешно обновлен", "success")
            return redirect(url_for('prof'))
        except Exception as e:
            flash(f"Ошибка при обновлении профиля: {str(e)}", "error")
            conn.rollback()
        finally:
            conn.close()

    conn = sql_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT email, tel, address, birth FROM Users WHERE id_us = ?",
                    (session['user_id'],))
        user_row = cur.fetchone()
        user_data = dict(user_row) if user_row else {}
        return render_template('edit_profile.html',
                               user_data=user_data,
                               nav_links=nav_links)
    except Exception as e:
        flash(f"Ошибка при получении данных: {str(e)}", "error")
        return redirect(url_for('prof'))
    finally:
        conn.close()


@app.route("/edit_prof_doc", methods=['GET', 'POST'])
def edit_prof_doc():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        telephone = request.form.get('tel')
        birth = request.form.get('birth')

        conn = sql_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE Users 
                SET email = ?, 
                    tel = ?, 
                    birth = ?
                WHERE id_us = ?
            """, (email, telephone, birth, session['user_id']))

            conn.commit()
            flash("Профиль успешно обновлен", "success")
            return redirect(url_for('prof'))
        except Exception as e:
            flash(f"Ошибка при обновлении профиля: {str(e)}", "error")
            conn.rollback()
        finally:
            conn.close()

    conn = sql_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT email, tel, birth FROM Users WHERE id_us = ?",
                    (session['user_id'],))
        user_row = cur.fetchone()
        user_data = dict(user_row) if user_row else {}
        return render_template('edit_prof_doc.html',
                               user_data=user_data,
                               nav_links=nav_links)
    except Exception as e:
        flash(f"Ошибка при получении данных: {str(e)}", "error")
        return redirect(url_for('prof'))
    finally:
        conn.close()


@app.errorhandler(401)
def unauthorized(error):
    return render_template('auth_error.html', error_message="Для доступа к этой странице требуется авторизация", nav_links=nav_links), 401


@app.errorhandler(404)
def pageNotFount(error):
    return render_template('page404.html', title="Страница не найдена")


@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        fio = request.form['fio']
        stage = request.form['stage']
        specialnost = request.form['specialnost']
        image_file = request.files['photo']
        image_data = image_file.read() if image_file else None
        conn = sql_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO Vra4i (FIO, specialnost, photo, stage) VALUES (?, ?, ?, ?)",
                            (fio, specialnost, image_data, stage))
                conn.commit()
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении врача: {e}")
            finally:

                conn.close()

    return render_template('doc.html', nav_links=nav_links)


@app.route('/add_usl', methods=['GET', 'POST'])
def add_usl():
    if request.method == 'POST':
        usl = request.form['usl']
        price = request.form['price']
        conn = sql_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Uslugi (title, price) VALUES (?, ?)",
                    (usl, price))
        conn.commit()
        conn.close()

    return render_template('usl.html', nav_links=nav_links)


@app.route('/add_pac', methods=['GET', 'POST'])
def add_pac():
    if request.method == 'POST':
        name = request.form['name']
        vid = request.form['vid']
        date = request.form['date']
        id_us = request.form['id_us']
        adr = request.form['adr']
        tel = request.form['tel']
        image_file = request.files['photo']
        image_data = image_file.read() if image_file else None

        conn = sql_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO Pacienti (name, photo, vid, data_rozd, id_us, adress, telephone) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (name, image_data, vid, date, id_us, adr, tel))
                conn.commit()
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении врача: {e}")
            finally:

                conn.close()

    return render_template('message.html', nav_links=nav_links)


@app.route("/edit_pacient/<int:id_pac>", methods=['GET', 'POST'])
def edit_pacient(id_pac):
    if session.get('role') not in ['doctor', 'admin']:
        abort(403)

    conn = sql_connection()
    cur = conn.cursor()

    if session['role'] == 'doctor':
        cur.execute('''
            SELECT 1 FROM Vrach_Pacient 
            WHERE id_vr = ? AND id_pac = ?
        ''', (session['user_id'], id_pac))

        if not cur.fetchone():
            conn.close()
            abort(403)

    if request.method == 'POST':
        vid = request.form['vid']
        date = request.form['date']
        adr = request.form['adr']
        tel = request.form['tel']

        try:
            cur.execute('''
                UPDATE Pacienti SET
                    vid = ?,
                    data_rozd = ?,
                    adress = ?,
                    telephone = ?
                WHERE id_pac = ?
            ''', (vid, date, adr, tel, id_pac))
            conn.commit()
            flash("Данные успешно обновлены", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Ошибка обновления: {str(e)}", "error")
        finally:
            conn.close()

        return redirect(url_for('message'))

    cur.execute('SELECT * FROM Pacienti WHERE id_pac = ?', (id_pac,))
    patient = cur.fetchone()

    if not patient:
        conn.close()
        abort(404)

    pacient = dict(patient)
    conn.close()

    return render_template('edit_pacient.html',
                           pacient=pacient,
                           nav_links=nav_links)


@app.route("/edit_doctor/<int:id_vr>", methods=['GET', 'POST'])
def edit_doctor(id_vr):
    if session.get('role') != 'admin':
        abort(403)

    conn = sql_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        fio = request.form['fio']
        specialnost = request.form['specialnost']
        stage = request.form['stage']

        try:
            cur.execute('''
                UPDATE Vra4i SET
                    FIO = ?,
                    specialnost = ?,
                    stage = ?
                WHERE id_vr = ?
            ''', (fio, specialnost, stage, id_vr))
            conn.commit()
            flash("Данные врача обновлены", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Ошибка обновления: {str(e)}", "error")
        finally:
            conn.close()

        return redirect(url_for('doc'))

    cur.execute('SELECT * FROM Vra4i WHERE id_vr = ?', (id_vr,))
    doctor = dict(cur.fetchone())
    conn.close()

    return render_template('edit_doctor.html',
                           doctor=doctor,
                           nav_links=nav_links)


# Удаление врача
@app.route("/delete_doctor/<int:id_vr>", methods=['POST'])
def delete_doctor(id_vr):
    if session.get('role') != 'admin':
        abort(403)

    conn = sql_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM Vra4i WHERE id_vr = ?', (id_vr,))
        conn.commit()
        flash("Врач удален", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка удаления: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for('doc'))


# Редактирование услуги
@app.route("/edit_usluga/<int:id_usl>", methods=['GET', 'POST'])
def edit_usluga(id_usl):
    if session.get('role') != 'admin':
        abort(403)

    conn = sql_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']

        try:
            cur.execute('''
                UPDATE Uslugi SET
                    title = ?,
                    price = ?
                WHERE id_usl = ?
            ''', (title, price, id_usl))
            conn.commit()
            flash("Услуга обновлена", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Ошибка обновления: {str(e)}", "error")
        finally:
            conn.close()

        return redirect(url_for('usl'))

    cur.execute('SELECT * FROM Uslugi WHERE id_usl = ?', (id_usl,))
    usluga = dict(cur.fetchone())
    conn.close()

    return render_template('edit_usluga.html',
                           usluga=usluga,
                           nav_links=nav_links)


# Удаление услуги
@app.route("/delete_usluga/<int:id_usl>", methods=['POST'])
def delete_usluga(id_usl):
    if session.get('role') != 'admin':
        abort(403)

    conn = sql_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM Uslugi WHERE id_usl = ?', (id_usl,))
        conn.commit()
        flash("Услуга удалена", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Ошибка удаления: {str(e)}", "error")
    finally:
        conn.close()

    return redirect(url_for('usl'))

if __name__ == '__main__':
    con = sql_connection()
    if con:
        sql(con)
        fix_photo_data()
        con.close()
    app.run(debug=True)