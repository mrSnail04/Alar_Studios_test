# Alar_Studios_test
Тестовое задание Alar Studios

## Запуск через venv

В начале требуется создать базу данных test_db.  

Для запуска источника json файлов для 2-го задания использовать:
```
python -m http.server -b 127.0.0.1 
```
Приложение  запускается при помощи:
```
python app.py
```

Страница /login используется для входа на сайт.  
После запуска создатся первый пользователь 
username: admin
password: admin

Страница _/logout_ используется для выхода с сайт.

Страница _/create_user_ используется для создания нового пользователя.

Страница _/edit_user/<user_id>_ используется для редактирования пользователя с <user_id> = id пользователя.

Страница _/delete_user/<user_id>_ используется для удаления пользователя с <user_id> = id пользователя.

Страница _/json_async_ используется для вывода отсортированных json данных.
