from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory
import sqlite3, os
from werkzeug.utils import secure_filename

# --- Настройки ---
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "webm"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --- Проверка расширения файла ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Создание базы данных ---
def create_db():
    conn = sqlite3.connect("social.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            media TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# --- Главная страница ---
@app.route("/")
def home():
    conn = sqlite3.connect("social.db")
    c = conn.cursor()
    c.execute("""
        SELECT posts.content, posts.media, users.username
        FROM posts JOIN users ON posts.user_id = users.id
        ORDER BY posts.id DESC
    """)
    posts = c.fetchall()
    conn.close()

    post_html = ""
    for content, media, author in posts:
        post_html += f"<p><b>{author}:</b> {content}</p>"
        if media:
            ext = media.rsplit(".", 1)[1].lower()
            if ext in {"png", "jpg", "jpeg", "gif"}:
                post_html += f"<img src='/uploads/{media}' width='300'><br>"
            else:
                post_html += f"<video width='320' controls><source src='/uploads/{media}' type='video/mp4'></video><br>"
        post_html += "<hr>"

    return f"""
        <h1>Мини-соцсеть 🌐</h1>
        <p>
            <a href='/register'>Регистрация</a> |
            <a href='/login'>Вход</a> |
            <a href='/new_post'>Новый пост</a>
        </p>
        {post_html}
    """

# --- Регистрация ---
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("social.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
            conn.commit()
            conn.close()
            return "<h2>Аккаунт создан! <a href='/login'>Войти</a></h2>"
        except sqlite3.IntegrityError:
            conn.close()
            return "<h2>Имя занято 😅 <a href='/register'>Попробовать другое</a></h2>"

    return render_template_string("""
        <h1>Регистрация</h1>
        <form method="post">
            Имя: <input type="text" name="username" required><br>
            Пароль: <input type="password" name="password" required><br>
            <input type="submit" value="Зарегистрироваться">
        </form>
    """)

# --- Вход ---
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("social.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
        user = c.fetchone()
        conn.close()
        if user:
            return f"<h2>Привет, {username}! 🎉</h2><p><a href='/'>На главную</a></p>"
        else:
            return "<h2>Неправильные данные 😢 <a href='/login'>Попробовать снова</a></h2>"

    return render_template_string("""
        <h1>Вход</h1>
        <form method="post">
            Имя: <input type="text" name="username" required><br>
            Пароль: <input type="password" name="password" required><br>
            <input type="submit" value="Войти">
        </form>
    """)

# --- Новый пост с медиа ---
@app.route("/new_post", methods=["GET","POST"])
def new_post():
    if request.method=="POST":
        username = request.form["username"]
        content = request.form.get("content","")
        file = request.files.get("media")
        filename = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect("social.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user:
            c.execute("INSERT INTO posts (user_id, content, media) VALUES (?,?,?)",
                      (user[0], content, filename))
            conn.commit()
        conn.close()
        return redirect("/")

    return render_template_string("""
        <h1>Новый пост</h1>
        <form method="post" enctype="multipart/form-data">
            Логин: <input type="text" name="username" required><br>
            Текст: <br><textarea name="content"></textarea><br>
            Картинка/Видео: <input type="file" name="media"><br>
            <input type="submit" value="Опубликовать">
        </form>
    """)

# --- Маршрут для отдачи медиа ---
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Запуск ---
if __name__=="__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    create_db()
    app.run(debug=True)
