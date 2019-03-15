from requests import get

# Вывода ошибки не будет, т.к. пользователь есть в БД
print(get('http://localhost:8080/portfolio/evil_rise7').json())
# Вывод ошибки, т.к. пользователя нет в БД
print(get('http://localhost:8080/portfolio/bad_user').json())
# Вывода ошибки не будет, т.к. у пользователя есть проект с таким id
print(get('http://localhost:8080/portfolio/evil_rise7/0').json())
# Вывод ошибки, т.к. пользователь ввел недопустимый id
print(get('http://localhost:8080/portfolio/evil_rise7/1001').json())