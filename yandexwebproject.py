from flask import Flask, render_template


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_POSHEL_V_ZHOPU'


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    return render_template('login.html')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(port=2555, host='127.0.0.1')