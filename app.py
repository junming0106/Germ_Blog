from config import MYSQL_CONFIG
import mysql.connector
from flask import Flask, render_template, request, redirect, session
import os  # 生成密鑰
from datetime import timedelta  # 加入這行
from flask_wtf.csrf import CSRFProtect
app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)  # 生成密鑰

# 設定 Session 配置
app.config.update(
    SESSION_COOKIE_SECURE=True,    # 只在 HTTPS 傳送
    SESSION_COOKIE_HTTPONLY=True,  # 防止 JavaScript 訪問
    SESSION_COOKIE_SAMESITE='Lax', # 防止 CSRF
    PERMANENT_SESSION_LIFETIME=timedelta(days=1)  # Session 過期時間
)

csrf = CSRFProtect(app)

@app.route('/')
def index():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        # 獲取所有有標題和內容的文章
        cursor.execute('''
            SELECT id, username, title, content, create_at 
            FROM blog 
            WHERE title IS NOT NULL 
            AND content IS NOT NULL 
            ORDER BY create_at DESC
        ''')
        posts = cursor.fetchall()
        return render_template('index.html', posts=posts)
    except mysql.connector.Error as err:
        print(f"資料庫錯誤：{err}")
        return '讀取文章時發生錯誤'
    finally:
        cursor.close()
        conn.close()

# 登入
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 基本驗證
        if not username or not password:
            return '請填寫所有欄位'
            
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute('SELECT * FROM blog WHERE username = %s AND password = %s', 
                         (username, password))
            user = cursor.fetchone()
            
            if user:
                # 可以加入 session 處理
                session['user_id'] = user['id']
                return redirect('/')
            else:
                return '帳號或密碼錯誤'
                
        except mysql.connector.Error as err:
            print(f"資料庫錯誤：{err}")
            return '登入時發生錯誤'
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

# 登出
@app.route('/logout')
def logout():
    # 清除session 就可以登出
    session.clear()
    # 導向首頁
    return redirect('/')

# 註冊頁面，載入時是GET，提交時是POST
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(buffered=True) # 加入buffered=True，可以確保資料完整存入到記憶體中，變免未讀錯誤
        try:
            if username and password and email:
                if len(password) >= 8:
                    if password == confirm_password:
                        cursor.execute('''
                            INSERT INTO blog(username, password, email) 
                            VALUES(%s, %s, %s)
                        ''', (username, password, email))
                        conn.commit()
                    else:
                        return '密碼不一致'
                else:
                    return '密碼長度至少8個字'
            else:
                return redirect('/register')
        except mysql.connector.Error as err:
            conn.rollback()
            print(f"錯誤：{err}")
            if err.errno == 1062:  # 重複的用戶名
                return '用戶名已存在'
            return '註冊失敗'
        finally:
            cursor.close()
            conn.close()
        return redirect('/')
    
    # GET 請求時顯示註冊頁面
    return render_template('register.html')

@app.route('/post', methods=['GET', 'POST'])
def new_post():
    # 判斷使用者是否登入
    if not session.get('user_id'):
        return redirect('/login')
        
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # 基本驗證
        if not title or not content:
            return '標題和內容不能為空'
            
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE blog 
                SET title = %s, content = %s 
                WHERE id = %s
            ''', (title, content, session['user_id']))
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
        # 獲取特定文章的詳細資訊
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
            
    except mysql.connector.Error as err:
        print(f"資料庫錯誤：{err}")
        return '讀取文章時發生錯誤'
    finally:
        cursor.close()
        conn.close()
# 本機端測試
# if __name__ == '__main__':
#     app.run(debug=True)
