# Библиотеки
import json
import os
from PIL import Image
from flask import Flask, \
    render_template, redirect, flash, \
    request, url_for, session, send_from_directory,\
    jsonify
from flask_mysqldb import MySQL
from flask_restful import Api, Resource, reqparse
from wtforms import Form, StringField,\
    PasswordField, validators
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt


# Само приложение
app = Flask(__name__)
api = Api(app)

# Парсер для тестов
parser = reqparse.RequestParser()

# Аргументы
parser.add_argument('image', required=True)
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)

# Папка загрузки аватарок
UPLOAD_FOLDER = "static/img"
app.config['UPLOAD_FOLDER_AVA'] = UPLOAD_FOLDER

# Папка загрузки аватарок
UPLOAD_FOLDER_PORTFOLIO = "static/portfolio_thumbnails"
app.config['UPLOAD_FOLDER_PORTFOLIO'] = UPLOAD_FOLDER_PORTFOLIO

# Папка загрузки музыки
UPLOAD_FOLDER_MUSIC = "static/music"
app.config['UPLOAD_FOLDER_MUSIC'] = UPLOAD_FOLDER_MUSIC

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
um = "UPDATE users SET email = %s WHERE username = %s"
un = "UPDATE users SET name = %s WHERE username = %s"
up = "UPDATE users SET password = %s WHERE username = %s"


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


# Изменение содержимого JSON файла
class ChangeJSON:
    # Инициализация
    def __init__(self):
        self.path = "static/users/accounts.json"

    # Информация о пользователе из json файла
    def get_data(self):
        with open(self.path,
                  "rt", encoding="utf8") as f:
            user_list = json.loads(f.read())
        return user_list

    # Запись информации о пользователе в файл
    def write_data(self, filelist):
        with open(self.path,
                  "w", encoding="utf8") as f:
            # Перейти в начало строки
            #  и отступы по 4 пробела
            f.seek(0)
            json.dump(filelist, f,
                      indent=4, ensure_ascii=False)

    # Изменение данных в json файле пользователей
    def json_write_data(self, username, info, tag, w_id):
        # Открываю файл для полного копирования
        # содержимого
        user_info = self.get_data()

        if w_id == 1:
            # Изменяю содержимое соц. сетей
            user_info[username][0]['social'][0][tag] = info

        elif w_id == 2:
            # Образ словаря
            dict_obj = {str(tag): str(info)}

            # Добавление образа, как новый проект в лист словарей
            user_info[username][0]['projects'].append(dict_obj.copy())

        elif w_id == 3:
            # Если данные были занесены до этого, то забиваем все
            # в текущий словарь из листа словарей
            user_info[username][0]['projects'][-1][str(tag)] = str(info)

        elif w_id == 4:
            # Копирую лист из JSON и добавляю туда ссылки, затем сохраняю
            video_json = user_info[username][0]['projects'][-1].get('video')
            video_json.append(tag)
            user_info[username][0]['projects'][-1]['video'] = video_json

        elif w_id == 5:
            # Создаю лист видео или музыки
            user_info[username][0]['projects'][-1][str(tag)] = []

        elif w_id == 6:
            # Копирую лист из JSON и добавляю туда файлы, затем сохраняю
            music_json = user_info[username][0]['projects'][-1].get('music')
            music_json.append(tag)
            user_info[username][0]['projects'][-1]['music'] = music_json

        elif w_id == 7:
            # Удаление проекта
            # Проверка есть ли в листе проекты
            if user_info[username][0]['projects']:
                if -1 < tag < len(user_info[username][0]['projects']):
                    del user_info[username][0]['projects'][int(tag)]

        else:
            # Изменяю информацию
            user_info[username][0][tag] = info

        # Произвожу запись новых данных в файл
        self.write_data(user_info)


# Сравнение и изменение данных соц. сетей
class SocialMediaCheck:
    # Инициализация класса
    def __init__(self):
        pass

    def check_info(self, name, board, f_path, username):
        social_media = request.form[str(name)]

        # Если информация не похожа на то, что было в файле
        if social_media != f_path and social_media != "":
            board.json_write_data(username,
                                  str(social_media),
                                  str(name), 1)


# Портфолио и его изменение
class Portfolio:
    # Добавление предмета в портфолио
    def add_item(self, username, board):
        form_status = False

        title = ""
        content = ""
        filename = ""
        video_list = []
        music_list = []

        # Иконка проекта
        if 'thumbnail' in request.files:
            # Начнем с ИКОНКИ проекта
            thumbnail = request.files['thumbnail']
            # Сохранение файла в папку
            filename = secure_filename(thumbnail.filename)
            thumbnail.save(os.path.join(
                app.config['UPLOAD_FOLDER_PORTFOLIO'], filename))
            # Изменение аватара под размеры
            thumb_img = Image.open(os.path.join(
                app.config['UPLOAD_FOLDER_PORTFOLIO'], filename))
            thumb_size = (450, 325)
            thumb_img.thumbnail(thumb_size, Image.ANTIALIAS)
            # Сохранение измененной иконки
            if ".png" in thumbnail.filename:
                thumb_img.save(os.path.join(
                    app.config['UPLOAD_FOLDER_PORTFOLIO'], filename))
            else:
                if ".jpeg" in thumbnail.filename:
                    filename = filename.replace(".jpeg", "jpg")

                thumb_img.save(os.path.join(
                    app.config['UPLOAD_FOLDER_PORTFOLIO'], filename),
                    "JPEG", quality=100, optimize=True,
                    progressive=True)

        # Название проекта
        if 'title' in request.form:
            title = request.form['title']
            # Проверка на содержание.
            if title == "":
                form_status = False

        # Описание проекта
        if 'content' in request.form:
            content = request.form['content']

            # Проверка на содержание.
            if content == "":
                form_status = False

        # Youtube URL'S
        for i in range(1, 4):
            # Имя формы
            video_input = "video" + str(i)
            # Если пользователь залил ссылки на видео
            if video_input in request.form:
                # Захват видео
                video_url = request.form[video_input]

                # Если ссылка действительна, т.е. не пустая
                if video_url:
                    # Добавляю в список ссылку
                    video_list.append(str(video_url))

        # Музыка
        for i in range(1, 6):
            # Имя формы
            music_input = "music" + str(i)
            # Если пользователь закинул файл с песнями
            if music_input in request.files:
                # Начнем с ИКОНКИ проекта
                music_file = request.files[music_input]

                # Сохранение музыки
                if ".mp3" in music_file.filename:
                    # Сохранение файла в папку
                    music_name = secure_filename(music_file.filename)
                    music_file.save(os.path.join(
                        app.config['UPLOAD_FOLDER_MUSIC'], music_name))
                    # Заношу в список название песни
                    music_list.append(str(music_name))

        # Занесение данных в JSON файл и проверка на подлинность
        if title and content and filename:
            form_status = True
        else:
            form_status = False

        # Если все формы были заполнены корректно
        if form_status:
            # Заносятся в JSON файл шаблон проекта
            board.json_write_data(username, filename, 'image', 2)
            board.json_write_data(username, title, 'title', 3)
            board.json_write_data(username, content, 'content', 3)
            board.json_write_data(username, [], 'video', 5)
            board.json_write_data(username, [], 'music', 5)

            # Если присутствуют видео, то они добавляются под спец.ключом
            if video_list:
                for i in range(len(video_list)):
                    board.json_write_data(username, '',
                                          str(video_list[i]), 4)

            # Если присутствуют песни, то они добавляются под спец.ключом
            if music_list:
                for i in range(len(music_list)):
                    board.json_write_data(username, '', music_list[i][:-4], 6)

    # Удаление предмета из портфолио
    def remove_item(self, username, board, project_id):
        board.json_write_data(username, '', project_id, 7)


# API Портфолио
class PortfolioList(Resource):
    # Вернуть целый список проектов
    def get_list(self):
        json_class = ChangeJSON()
        user_projects = json_class.get_data()
        return user_projects


# Инициализация JSON класса для портфолио
portfolio_class = PortfolioList()


# Функция для проверки пользователя внутри БД
def check_username(username):
    # Захват имени
    # Инициализация курсора
    cursor = mysql.connection.cursor()
    # Проверка пользователя в наличие в БД
    result = cursor.execute("SELECT * FROM users WHERE username = %s",
                            [username])
    # Возвращаю ответ
    return [cursor, result]


# Вернуть все проекты
@app.route('/portfolio/<string:username>',  methods=['GET'])
def get_projects(username):
    # Если пользователь внутри БД
    if check_username(username)[1]:
        # Беру значения из JSON
        user_json = portfolio_class.get_list()

        # Возвращение ответа в виде JSON
        return jsonify(
            {str(username): user_json[username][0]['projects']})

    # Если пользователя нет внутри БД
    else:
        return jsonify({'USER': 'DOES NOT EXIST!'})


# Вернуть все проекты
@app.route('/portfolio/<string:username>/<int:project_id>',  methods=['GET'])
def get_project_id(username, project_id):
    # Если пользователь внутри БД
    if check_username(username)[1]:
        # Беру значения из JSON
        user_json = portfolio_class.get_list()

        # Если проект находится в JSON
        if project_id < len(user_json[username][0]['projects']):
            # Заголовок JSON
            output_name = str(username) + "'s project: " + str(project_id)

            # Возвращение ответа в виде JSON
            return jsonify(
                {output_name: user_json[username][0]['projects'][project_id]})

        # Если данного проекта не существует
        else:
            return jsonify(
                {("PROJECT " + str(project_id)): 'DOES NOT EXIST!'})

    # Если пользователя нет внутри БД
    else:
        return jsonify({'USER': 'DOES NOT EXIST!'})


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
                                 "country": "-",
                                 "short_description": "-",
                                 "description": "-",
                                 "projects": [],
                                 "contacts": "-",
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

        list_db = check_username(port_name)
        # Если проверка была произведена
        if list_db[1]:
            data = list_db[0].fetchone()
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


# Страница измененных настроек
@app.route('/success/<username>')
def success(username):
    if check_username(username)[1]:
        # Если пользователь вошел в свою страницу
        if 'logged_in' in session:
            # Если пользователь вошел в свою панель управления
            if session['logged_in'] and \
                    session['username'] == username:
                return render_template('success.html', user=username)

            # Если пользователь заходит в чужую панель управления
            else:
                return redirect("/{}".format(session['username']))

        # Если пользователь не вошел в систему
        else:
            # Перенаправление на страницу входа
            return redirect(url_for('login'))


# Панель управления неуказанного пользователя
@app.route('/dashboard')
def empty_board():
    return redirect(url_for('error404'))


# Панель управления
@app.route('/dashboard/<string:username>', methods=['POST', 'GET'])
def dashboard(username):
    # Создаю объекты классов содержимого JSON файла,
    # соц. сетей, портфолио
    board = ChangeJSON()
    media = SocialMediaCheck()
    portfolio = Portfolio()

    list_db = check_username(username)

    # Инициализация панели управления
    if request.method == 'GET':
        # Если пользователь найден в базе данных
        if list_db[1]:
            # Если пользователь вошел в свою страницу
            if 'logged_in' in session:
                # Если пользователь вошел в свою панель управления
                if session['logged_in'] and \
                        session['username'] == username:
                    return render_template('dashboard.html',
                                           user=username,
                                           user_data=board.get_data())

                # Если пользователь заходит в чужую панель управления
                else:
                    return redirect("/{}".format(session['username']))

            # Если пользователь не вошел в систему
            else:
                # Перенаправление на страницу входа
                return redirect(url_for('login'))

    # Отправка формы
    if request.method == 'POST':
        # Инициализация пользователя
        user_data = board.get_data()

        # Если аватарка была залита на сервер
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

                # Если аватарка была изменена на другую
                if filename != user_data[username][0]["avatar"]:
                    board.json_write_data(username, filename,
                                          'avatar', 0)

        # Если имя было изменено
        if 'name' in request.form:
            name = request.form['name']
            if name != "":
                if name != user_data[username][0]['name'] \
                        and 50 > len(name) > 1:
                    list_db[0].execute(un, (name, username))
                    # Занесение изменений в Базу Данных
                    mysql.connection.commit()
                    board.json_write_data(username, name,
                                          'name', 0)

        # Если почта была изменена
        if 'mail' in request.form:
            mail = request.form['mail']
            if mail != "":
                if mail != user_data[username][0]['mail'] \
                        and 50 > len(mail) > 6:
                    list_db[0].execute(um, (mail, username))
                    # Занесение изменений в Базу Данных
                    mysql.connection.commit()
                    board.json_write_data(username, mail,
                                          'mail', 0)

        # Если пароль был изменен
        if 'pass' in request.form:
            passw = request.form['pass']
            if passw != "":
                # Зашифрока пароля
                passw = sha256_crypt.encrypt(str(passw))
                list_db[0].execute(up, (passw, username))
                # Занесение изменений в Базу Данных
                mysql.connection.commit()

        # Если описание было изменено
        if 'short_description' in request.form:
            description = request.form['short_description']
            board.json_write_data(username, description,
                                  'short_description', 0)

        # Если описание о человеке было изменено
        if 'description' in request.form:
            about = request.form['description']
            board.json_write_data(username, about,
                                  'description', 0)

        # Если страна была изменена
        if 'country' in request.form:
            country = request.form['country']
            if country != user_data[username][0]['country']:
                board.json_write_data(username, country,
                                      'country', 0)

        # Если социальные сети были изменены(sm - soc.media)
        for sm in ["facebook", "twitter", "youtube"]:
            if sm in request.form:
                f_path = user_data[username][0]['social'][0][str(sm)]
                media.check_info(str(sm), board,
                                 f_path, username)

        # Портфолио
        portfolio.add_item(username, board)

        # Занесение изменений в базу данных
        mysql.connection.commit()
        # Выход курсора
        list_db[0].close()

        # Перенаправление на страницу измененных настроек
        return render_template('success.html',
                               user=username)


# Удаление проекта без заданных параметров 1
@app.route('/delete')
def delete_project_empty():
    # Перенаправление на страницу ошибки
    return redirect(url_for('error404'))


# Удаление проекта без заданных параметров 2
@app.route('/delete/<string:username>')
def delete_project_empty_user(username):
    # Перенаправление на страницу ошибки
    return redirect(url_for('error404'))


# Удаление проекта без заданных параметров 3
@app.route('/delete/<int:project_id>')
def delete_project_empty_id(project_id):
    # Перенаправление на страницу ошибки
    return redirect(url_for('error404'))


# Удаление проекта
@app.route('/delete/<string:username>/<int:project_id>', methods=["POST"])
def delete_project(username, project_id):
    # Создаю объекты классов содержимого JSON файла, портфолио
    board = ChangeJSON()
    portfolio = Portfolio()

    list_db = check_username(username)

    # Если пользователь найден в базе данных
    if list_db[1]:
        # Если пользователь вошел в свою страницу
        if 'logged_in' in session:
            # Если пользователь вошел в свою панель управления
            if session['logged_in'] and \
                    session['username'] == username:
                portfolio.remove_item(username, board, project_id)
                return redirect("/{}".format(session['username']))

            # Если пользователь удаляет файл чужого пользователя
            else:
                return redirect("/{}".format(session['username']))

        # Если пользователь не вошел в систему
        else:
            # Перенаправление на страницу входа
            return redirect(url_for('login'))


# Сама профильная страница
@app.route("/<username>")
def account(username):
    # Объект класса для изменения содержимого JSON
    account_data = ChangeJSON()

    # Флаг для проверки входа
    logged_user = False
    project_available = False

    # Если ответ положительный
    if check_username(username)[1]:
        # Копирование всех данных из JSON файла
        user_data = account_data.get_data()

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
    app.run(port=1025, host='localhost')
