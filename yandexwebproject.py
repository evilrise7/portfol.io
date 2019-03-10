from flask import Flask, \
    render_template, redirect, flash, \
    request, url_for, session, send_from_directory

from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, StringField,\
    PasswordField, validators
from werkzeug.utils import secure_filename
import json
import os
from PIL import Image


# Само приложение
app = Flask(__name__)

# Папка загрузки аватарок
UPLOAD_FOLDER = "static/img"
app.config['UPLOAD_FOLDER_AVA'] = UPLOAD_FOLDER
# База данных конфиги
app.config['SECRET_KEY'] = 'IDIDNOT'
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = 'SG5Ztve51L'
app.config['MYSQL_PASSWORD'] = '2KZ7XrdVVy'
app.config['MYSQL_DB'] = 'SG5Ztve51L'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# База Данных
mysql = MySQL(app)

# Сообщение из-за PEP8 не поместилось
m = "INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)"


# Форма Регистрации
class Registration(Form):
    # validators.Length = Длина соответсвующего текстового поля
    name = StringField('Name', [validators.Length(min=1, max=50)],
                       render_kw={"placeholder": "Name"})
    username = StringField('Portname', [validators.Length(min=4, max=30)],
                           render_kw={"placeholder": "Portname"})
    email = StringField('Portmail', [validators.Length(min=6, max=50)],
                        render_kw={"placeholder": "Portmail"})
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Does not match!')
    ], render_kw={"placeholder": "Password"})
    confirm = PasswordField('Confirm Password',
                            render_kw={"placeholder": "Confirm Password"})


# Информация о пользователе из json файла
def get_data():
    with open("static/users/accounts.json",
              "rt", encoding="utf8") as f:
        user_list = json.loads(f.read())
    return user_list


# Изменение данных в json файле пользователей
def json_write_data(username, info, tag):
    with open("static/users/accounts.json",
              "rt", encoding="utf8") as f:
        user_info = json.loads(f.read())
    user_info[username][0][tag] = info

    with open("static/users/accounts.json",
              "w", encoding="utf8") as f:
        # Перейти в начало строки и отступы по 4 пробела
        f.seek(0)
        json.dump(user_info, f, indent=4, ensure_ascii=False)


# Иконка
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='img/favicon.ico')


# Начальная страница
@app.route('/')
def main_page():
    # session.clear()
    return render_template('index.html')


# Регистрация Пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = Registration(request.form)
    if request.method == 'POST' and form.validate():
        # Имя
        name = form.name.data
        # Почта
        email = form.email.data
        # Имя пользователя
        username = form.username.data
        # Перешифрование пароля
        password = sha256_crypt.encrypt(str(form.password.data))

        # Инициализация курсора
        cursor = mysql.connection.cursor()
        # Занесение данных в Базу Данных
        cursor.execute(m, (name, email, username, password))
        # Занесение изменений в Базу Данных
        mysql.connection.commit()

        # Заносим в JSON аккаунт
        try:
            with open("static/users/accounts.json", encoding="utf8") as f:
                # Загрузка JSON файла
                accounts = json.load(f)
        # Если файл пустой
        except Exception:
            accounts = {}

        # Форма данных
        data = {str(username): [{"avatar": "default.png",
                                 "name": name,
                                 "country": "Does not exist",
                                 "short_description": "Does not exist",
                                 "description": "Does not exist",
                                 "projects": [],
                                 "contacts": "Does not exist",
                                 "mail": email,
                                 "social": [{"facebook": "",
                                             "twitter": "",
                                             "youtube": ""}]}]}
        # Обновляем
        accounts.update(data)
        # Заносим информацию
        with open("static/users/accounts.json",
                  "w", encoding="utf8") as f:
            # Перейти в начало строки и отступы по 4 пробела
            f.seek(0)
            json.dump(accounts, f, indent=4, ensure_ascii=False)

        # Выход курсора
        cursor.close()
        flash('Congratulations! Now you can log in!',
              'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже вошел
    if 'logged_in' in session:
        return redirect("/{}".format(session['username']))
    # Если пользователь новый
    if request.method == 'POST':
        # Получаю данные из текстовых форм
        # Пользователь
        port_name = request.form['username']
        # Пароль
        port_pass = request.form['password']

        # Инициализация курсора
        cursor = mysql.connection.cursor()
        # Проверка пользователя в наличие в БД
        result = cursor.execute("SELECT * FROM users WHERE username = %s",
                                [port_name])
        # Если проверка была произведена
        if result:
            data = cursor.fetchone()
            password_crypt = data['password']

            # Сравнение паролей(зашифрованного и обычного)
            if sha256_crypt.verify(port_pass, password_crypt):
                # Вход был произведен
                session['logged_in'] = True
                session['username'] = port_name

                flash('You are already logged in', 'success')
                return redirect("/{}".format(session['username']))
            else:
                # Были введены некорректные данные
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Выход курсора
            cursor.close()
        else:
            # Если в базе данных не было найдено пользователя
            error = 'Portname does not exist!'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Выход пользователя
@app.route('/logout')
def logout():
    if session['logged_in']:
        session.clear()  # Очистка данных входа
        # Всплавающее сообщение
        flash('You are logged out.', 'success')
        return redirect(url_for('login'))


# Панель управления неуказанного пользователя
@app.route('/dashboard')
def empty_board():
    return redirect(url_for('error404'))


# Панель управления
@app.route('/dashboard/<username>', methods=['POST', 'GET'])
def dashboard(username):
    # Захват имени
    # Инициализация курсора
    cursor = mysql.connection.cursor()
    # Проверка пользователя в наличие в БД
    result = cursor.execute("SELECT * FROM users WHERE username = %s",
                            [username])
    if request.method == 'GET':
        # Если пользователь найден в базе данных
        if result:
            # Если пользователь вошел в свою страницу
            if 'logged_in' in session:
                # Если пользователь вошел в свою панель управления
                if session['logged_in'] and \
                        session['username'] == username:
                    return render_template('dashboard.html',
                                           user=username,
                                           user_data=get_data())

                # Если пользователь заходит в чужую панель управления
                else:
                    return redirect("/{}".format(session['username']))

            # Если пользователь не вошел в систему
            else:
                # Перенаправление на страницу входа
                return redirect(url_for('login'))

    # Отправка формы
    if request.method == 'POST':
        # Если аватарка был залит на сервер
        if 'file' in request.files:
            # Аватарка
            file = request.files['file']
            if ".png" in file.filename or \
                    ".jpg" in file.filename or\
                    ".jpeg" in file.filename:
                # Сохранение файла в папку
                filename = secure_filename(file.filename)
                file.save(os.path.join(
                    app.config['UPLOAD_FOLDER_AVA'], filename))
                # Изменение аватара под размеры
                avatar = Image.open(os.path.join(
                    app.config['UPLOAD_FOLDER_AVA'], filename))
                avatar_size = (170, 170)
                avatar.thumbnail(avatar_size, Image.ANTIALIAS)
                # Сохранение измененной аватарки
                if ".png" in file.filename:
                    avatar.save(os.path.join(
                        app.config['UPLOAD_FOLDER_AVA'], filename))
                else:
                    if ".jpeg" in file.filename:
                        filename = filename.replace(".jpeg", "jpg")

                    avatar.save(os.path.join(
                        app.config['UPLOAD_FOLDER_AVA'], filename),
                        "JPEG", quality=100, optimize=True,
                        progressive=True)

        # Если почта была изменена
        if 'mail' in request.form:
            mail = request.form['mail']
            json_write_data(username, mail, 'mail')

        # Если описание было изменено
        if 'description' in request.form:
            description = request.form['description']
            json_write_data(username, description, 'short_description')

        # Если описание о человеке было изменено
        if 'about' in request.form:
            about = request.form['about']
            json_write_data(username, about, 'description')
        return "ok"


# Сама профильная страница
@app.route("/<username>")
def account(username):
    # Захват имени
    # Инициализация курсора
    cursor = mysql.connection.cursor()
    # Проверка пользователя в наличие в БД
    result = cursor.execute("SELECT * FROM users WHERE username = %s",
                            [username])
    # Флаг для проверки входа
    logged_user = False
    project_available = False

    # Если ответ положительный
    if result:
        user_data = get_data()
        # Проверка на содержание фото-проектов
        if user_data[username][0]['projects']:
            project_available = True

        # Если пользователь вошел в свою страницу
        if 'logged_in' in session:
            if session['logged_in'] and session['username'] == username:
                logged_user = True

        # Информация о пользователе из json файла
        return render_template('account.html',
                               user=username,
                               user_data=user_data,
                               logged=logged_user,
                               project_flag=project_available)

    # Если Хьюстон у нас...
    else:
        return redirect(url_for('error404'))


# Ошибка 404
@app.route('/404')
def error404():
    return render_template('404.html')


# Запуск программы
if __name__ == '__main__':
    app.run(port=1019, host='localhost')