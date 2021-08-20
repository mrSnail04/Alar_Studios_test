import asyncio
import enum
import logging
import os
from functools import wraps

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError
from flask import (Flask, abort, jsonify, redirect, render_template,
                   request, session as fsession, url_for)
from sqlalchemy import (Column, Enum, Integer, String,
                       create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash


# Создаем сессию SQLAlchemy
engine = create_engine('postgresql://postgres:123456@localhost:5432/test_db')
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Создаём приложение Flask
app = Flask(__name__)
# передаём файл конфигураций
app.config.from_object('config')


# Класс прав пользователя. regular- только смотреть. admin- смотреть,добавлять, удалять, редактировать.
class UserRole(enum.Enum):
    regular = 1
    admin = 2


# Создание таблица пользователя
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.regular)

    def as_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role.name
        }


# Декоратор, который проверяте залогинился ли пользователь
def login_decor(f):
    """Decorator for pages with login authentication requirement"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not fsession.get('is_logged'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# Декоратор, который проверяте есть ли права администратора у пользователя
def admin_decor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if fsession.get('user_role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# Главная страница. Если залогинился, то отобразится список пользователей.
@app.route('/')
@login_decor
def index():
    users = session.query(User).order_by(User.id.asc()).all()
    return render_template(
        'index.html',
        users=[user.as_dict() for user in users],
        role_admin=(fsession['user_role'] == 'admin')
    )


# Страница входа на сайт.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = session.query(User).filter_by(username=username).first()

# Если юзер существует и введённый пароль совпадает с паролем юзера, то перенаправит на главную страницу
        if user and check_password_hash(user.password, password):
            fsession['is_logged'] = True
            fsession['user_id'] = user.id
            fsession['user_role'] = user.role.name
            return redirect(url_for('index'))
    return render_template('login.html')


# Страница выхода с сайта.
@app.route('/logout', methods=['GET'])
@login_decor
def logout():
    fsession['is_logged'] = False
    fsession['user_id'] = None
    fsession['user_role'] = None
    return redirect(url_for('login'))


# Страница создания нового пользователя, пример без ORM
@app.route('/create_user', methods=['POST'])
@login_decor
@admin_decor
def create_user():
    username = request.form['username'],
    password = generate_password_hash(request.form['password']),
    role = request.form['role']
    session.execute(
            'INSERT INTO users (username, password, role) VALUES (:username, :password, :role) RETURNING id',
            {'username': username, 'password': password, 'role': role})
    session.commit()
    return jsonify({'success': True})


# Страница редактирования пользователя
@app.route('/edit_user/<user_id>', methods=['POST'])
@login_decor
@admin_decor
def edit_user(user_id):
    user = session.query(User).get(user_id)
    user.username = request.form['username']
    user.password = generate_password_hash(request.form['password'])
    user.role = request.form['role']
    if not user:
        abort(404)
    session.commit()
    return jsonify(user.as_dict())


# Удаление пользователя
@app.route('/delete_user/<user_id>', methods=['GET'])
@login_decor
@admin_decor
def delete_user(user_id):
    user = session.query(User).get(user_id)
    session.delete(user)
    session.commit()
    return jsonify({'success': True})


#  Задание 2. Python, асинхронные запросы

# URLS сервера с json. Для запуска использовать: python -m http.server -b 127.0.0.1
DATA_URLS = [
    'http://127.0.0.1:8000/json/first_data.json',
    'http://127.0.0.1:8000/json/second_data.json',
    'http://127.0.0.1:8000/json/third_data.json',
]

loop = asyncio.get_event_loop()


# Забираем данный
async def fetch(url, session):
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return []
            return await response.json()
    except (ClientConnectorError, ClientResponseError):
        return []


# Сортировка полученных данных по id.
def sort_results(responses):
    return sorted(sum(responses, []), key=lambda element: element['id'])


# Получаем данные из DATA_URLS асинхронным способом.
async def get_data():
    async with ClientSession(timeout=ClientTimeout(total=2)) as session:
        responses = await asyncio.gather(
            fetch(DATA_URLS[0], session),
            fetch(DATA_URLS[1], session),
            fetch(DATA_URLS[2], session),
        )
    return sort_results(responses)


# Сраница отсортированного json
@app.route('/json_async')
def json_async():
    result = loop.run_until_complete(get_data())
    return jsonify(result)


# Запуск приложения, создание первого пользователя
if __name__ == "__main__":
    Base.metadata.create_all(engine)
    # Создания первого пользователя
    admin_user = session.query(User).filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            role='admin',
            password=generate_password_hash('admin')
        )
        session.add(admin_user)
        session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True)
