import sqlite3

# Создаём базу данных (если ещё нет)
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Создаём таблицу пользователей
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

conn.commit()
conn.close()
