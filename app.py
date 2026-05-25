from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import json
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "brawl-gizli-anahtar-2026"  # Değiştirebilirsin

# Admin şifresi (basit tut, sonra değiştirirsin)
ADMIN_PASSWORD = "brawl123"

# Veritabanı oluştur
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image_base64 TEXT,
            date TEXT NOT NULL,
            comments TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Login kontrolü decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM posts ORDER BY id DESC')
    posts = c.fetchall()
    conn.close()
    
    # Yorumları parse et
    posts_list = []
    for post in posts:
        comments = json.loads(post[5]) if post[5] else []
        posts_list.append({
            'id': post[0],
            'title': post[1],
            'content': post[2],
            'image': post[3],
            'date': post[4],
            'comments': comments
        })
    
    return render_template('index.html', posts=posts_list)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Şifre yanlış!')
    return render_template('admin_login.html')

@app.route('/admin')
@login_required
def admin_panel():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM posts ORDER BY id DESC')
    posts = c.fetchall()
    conn.close()
    return render_template('admin.html', posts=posts)

@app.route('/add-post', methods=['POST'])
@login_required
def add_post():
    title = request.form.get('title')
    content = request.form.get('content')
    image = request.form.get('image', '')
    
    if title and content:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO posts (title, content, image_base64, date, comments)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, image, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), json.dumps([])))
        conn.commit()
        conn.close()
    
    return redirect(url_for('admin_panel'))

@app.route('/delete-post/<int:post_id>')
@login_required
def delete_post(post_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/delete-all-posts')
@login_required
def delete_all_posts():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM posts')
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/add-comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    comment_text = request.form.get('comment')
    if comment_text:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT comments FROM posts WHERE id = ?', (post_id,))
        result = c.fetchone()
        if result:
            comments = json.loads(result[0]) if result[0] else []
            comments.append({
                'text': comment_text,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            c.execute('UPDATE posts SET comments = ? WHERE id = ?', (json.dumps(comments), post_id))
            conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)