from flask import Flask, render_template, request, redirect, session, jsonify
import os
from datetime import timedelta
import mysql.connector
import logging

# 設置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__,
    static_folder='../static',
    template_folder='../templates'
)

# 基本配置
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# MySQL 配置
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

# Session 配置
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=1)
)

@app.route('/')
def index():
    try:
        logger.info('Attempting database connection')
        logger.debug(f'MySQL Config: {MYSQL_CONFIG}')
        
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        logger.info('Executing query')
        cursor.execute('''
            SELECT id, username, title, content, create_at 
            FROM blog 
            WHERE title IS NOT NULL 
            AND content IS NOT NULL 
            ORDER BY create_at DESC
        ''')
        
        posts = cursor.fetchall()
        logger.info(f'Found {len(posts)} posts')
        
        return render_template('index.html', posts=posts)
        
    except mysql.connector.Error as db_err:
        logger.error(f'Database error: {db_err}')
        return jsonify({
            "error": "Database error",
            "details": str(db_err),
            "type": "database"
        }), 500
        
    except Exception as e:
        logger.error(f'General error: {e}')
        return jsonify({
            "error": "Server error",
            "details": str(e),
            "type": "general"
        }), 500
        
    finally:
        try:
            cursor.close()
            conn.close()
            logger.info('Database connection closed')
        except:
            pass

@app.errorhandler(500)
def handle_500(error):
    logger.error(f'500 error: {error}')
    return jsonify({
        "error": "Internal Server Error",
        "message": str(error),
        "env_check": {
            "mysql_host": bool(os.getenv('MYSQL_HOST')),
            "mysql_user": bool(os.getenv('MYSQL_USER')),
            "mysql_db": bool(os.getenv('MYSQL_DATABASE'))
        }
    }), 500

@app.errorhandler(404)
def handle_404(error):
    logger.error(f'404 error: {error}')
    return jsonify({
        "error": "Not Found",
        "message": str(error)
    }), 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            return '請填寫所有欄位'
            
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute('SELECT * FROM blog WHERE username = %s AND password = %s', 
                         (username, password))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['id']
                return redirect('/')
            else:
                return '帳號或密碼錯誤'
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT id, username, title, content, create_at 
            FROM blog 
            WHERE id = %s
        ''', (post_id,))
        post = cursor.fetchone()
        
        if post:
            return render_template('view_post.html', post=post)
        else:
            return '文章不存在'
    finally:
        cursor.close()
        conn.close()

# 其他路由...

# Vercel 需要的
app = app 