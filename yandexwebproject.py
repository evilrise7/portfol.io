from flask import Flask, \
    render_template, redirect, flash, \
    request, url_for, session

from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, \
    TextAreaField, PasswordField, validators


# Само приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_POSHEL_V_ZHOPU'
app.config['MYSQL_HOST'] = 'sql9.freemysqlhosting.net'
app.config['MYSQL_USER'] = 'sql9281617'
app.config['MYSQL_PASSWORD'] = 'YG8tYECG5Z'
app.config['MYSQL_DB'] = 'sql9281617'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# База Данных
mysql = MySQL(app)

# Сообщение из-за PEP8 не поместилось
m = "INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)"


# Форма Регистрации
class Registration(Form):
    # validators.Length = Длина соответсвующего текстового поля
    name = StringField('Имя', [validators.Length(min=1, max=50)])
    username = StringField('Портнейм', [validators.Length(min=4, max=25)])
    email = StringField('ПортМэйл', [validators.Length(min=6, max=50)])
    password = PasswordField('Пароль', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Пароли не совпадают!')
    ])
    confirm = PasswordField('Подтвердить пароль')


# Начальная страница
@app.route('/')
def main_page():
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

        # Выход курсора
        cursor.close()
        flash('Вы успешно зарегистрированы. Можете приступить к работе',
              'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
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

                flash('Вы уже зашли в аккаунт.', 'success')
                return redirect("/{}".format(session['username']))
            else:
                # Были введены некорректные данные
                error = 'Неверный логин'
                return render_template('login.html', error=error)
            # Выход курсора
            cursor.close()
        else:
            # Если в базе данных не было найдено пользователя
            error = 'Портнейм не найден!'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Сама профильная страница
@app.route("/<username>")
def account(username):

    return render_template('account.html',
                           user=username,
                           avatar="default.png",
                           country="Казахстан")


# О проекте
@app.route('/about')
def about():
    return render_template('about.html')


# Запуск программы
if __name__ == '__main__':
    app.run(port=1000, host='localhost')