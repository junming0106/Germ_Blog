import mysql.connector
from flask import Flask, flash, render_template, request, redirect, session, jsonify
import os
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect
import markdown

app = Flask(__name__, static_folder='static')
#  os.urandom(n) 隨機生成n個字元的字串
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# MySQL 配置從環境變數獲取
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

csrf = CSRFProtect(app)

@app.route('/')
def index():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT p.id, u.username, p.title, p.content, p.create_at 
            FROM posts p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.create_at DESC
        ''')
        posts = cursor.fetchall()
        return render_template('index.html', posts=posts)
    except mysql.connector.Error as err:
        print(f"資料庫錯誤：{err}")
        return '讀取文章時發生錯誤'
    finally:
        cursor.close()
        conn.close()

@app.route('/post', methods=['GET', 'POST'])
def new_post():
    if not session.get('user_id'):
        return redirect('/login')
        
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        user_id = session.get('user_id')
        
        if not title or not content:
            return '標題和內容不能為空'
            
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO posts (user_id, title, content) 
                VALUES (%s, %s, %s)
            ''', (user_id, title, content))
            
            conn.commit()
            return redirect('/')
            
        except mysql.connector.Error as err:
            conn.rollback()
            print(f"錯誤：{err}")
            return '發文失敗'
        finally:
            cursor.close()
            conn.close()
            
    return render_template('post.html')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT p.id, p.user_id, u.username, p.title, p.content, p.create_at 
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s
        ''', (post_id,))
        post = cursor.fetchone()
        if post:
            post['content'] = markdown.markdown(post['content'])
            return render_template('view_post.html', post=post)
        else:
            return '文章不存在'
            
    except mysql.connector.Error as err:
        print(f"資料庫錯誤：{err}")
        return '讀取文章時發生錯誤'
    finally:
        cursor.close()
        conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        
        if not all([username, password, email]):
            return render_template('register.html', 
                error='missing_fields',
                message='請填寫所有欄位')
            
        if len(password) < 8:
            return render_template('register.html', 
                error='password_length',
                message='密碼長度至少需要8個字元')
            
        if password != confirm_password:
            return render_template('register.html', 
                error='password_mismatch',
                message='密碼不一致')

        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(buffered=True)
            
            cursor.execute('''
                INSERT INTO users (username, password, email) 
                VALUES(%s, %s, %s)
            ''', (username, password, email))
            
            conn.commit()
            session['user_id'] = cursor.lastrowid
            return redirect('/')
            
        except mysql.connector.Error as err:
            if err.errno == 1062:
                return render_template('register.html', 
                    error='username_exists',
                    message='用戶名已存在')
            else:
                return render_template('register.html', 
                    error='database_error',
                    message='註冊失敗')
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            return render_template('login.html', 
                error='missing_fields', 
                message='請填寫所有欄位')
        
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s',
                           (username, password))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['id']
                return redirect('/')
            else:
                return render_template('login.html', 
                    error='invalid_credentials', 
                    message='帳號或密碼錯誤')
                    
        except mysql.connector.Error as err:
            print(f"資料庫錯誤：{err}")
            return render_template('login.html', 
                error='database_error', 
                message='登入時發生錯誤')
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')

#登出
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 刪除文章
@app.route('/post/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 檢查是否為文章作者
        cursor.execute('SELECT user_id FROM posts WHERE id = %s', (post_id,))
        post = cursor.fetchone()
    
        # 刪除文章
        cursor.execute('DELETE FROM posts WHERE id = %s', (post_id,))
        conn.commit()
        
        return jsonify({'message': 'Success'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)