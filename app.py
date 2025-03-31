import mysql.connector
from flask import Flask, render_template, request, redirect, session, jsonify
import os
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect
import markdown
from werkzeug.utils import secure_filename

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


# 編輯文章
@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if not session.get('user_id'):
        return redirect('/login')
        
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 先取得文章資料
        cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
        post = cursor.fetchone()
        
        if not post:
            return '找不到該文章'
    
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            
            if not title or not content:
                return '標題和內容不能為空'
            
            cursor.execute('UPDATE posts SET title = %s, content = %s WHERE id = %s', 
                         (title, content, post_id))
            conn.commit()
            return redirect('/post/' + str(post_id))
        
        return render_template('edit_post.html', post=post)
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"資料庫錯誤：{err}")
        return '編輯文章失敗'
        
    finally:
        cursor.close()
        conn.close()
        
    return render_template('edit_post.html')    


# API 測試
@app.route('/about-btn', methods=['GET'])
def about_btn():
    return render_template('about.html')

# 上傳圖片資料夾
app.config['UPLOAD_FOLDER'] = 'static/uploads'
# 判斷上傳的圖片格式
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/photo', methods=['GET', 'POST'])
def photo():
    if not session.get('user_id'):
        return redirect('/login')
        
    try:
        # 從資料庫取得照片
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查詢當前用戶的照片
        cursor.execute('''
            SELECT * FROM photos 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        ''', (session.get('user_id'),))
        
        photos = cursor.fetchall()
        
        # 不管是否有照片都返回模板
        return render_template('photo.html', photos=photos)
        
    except mysql.connector.Error as err:
        print(f"資料庫錯誤：{err}")
        # 發生錯誤時也返回模板，但照片列表為空
        return render_template('photo.html', photos=[])
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


# 上傳圖片版面
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')

# 上傳圖片路由
@app.route('/upload_image', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return '沒有選擇檔案'
            
        image = request.files['file']
        if image.filename == '':
            return '沒有選擇檔案'
            
        if image and allowed_file(image.filename):
            try:
                # 儲存圖片
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                # 圖片 URL
                photo_url = f'uploads/{filename}'  # 修改 URL 格式
                
                # 儲存到資料庫
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO photos (filename, url, user_id) 
                    VALUES (%s, %s, %s)
                ''', (filename, photo_url, session.get('user_id')))
                
                conn.commit()
                return redirect('/photo')
                
            except Exception as e:
                print(f"Error: {e}")
                return '上傳失敗'
                
            finally:
                cursor.close()
                conn.close()
        else:
            return '不支援的檔案格式'

    


@app.route('/about', methods=['GET','POST'])
def about():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users')
    users = cursor.fetchall()
    print(users)
    if request.method == 'POST':
        return jsonify({"message": users})
    elif request.method == 'GET':
        return jsonify({"message": users})
    else:
        return jsonify({"message": "Hello, World!"})

@app.route('/photo/delete/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 檢查是否為照片擁有者
        cursor.execute('SELECT * FROM photos WHERE id = %s AND user_id = %s', 
                      (photo_id, session.get('user_id')))
        photo = cursor.fetchone()
        
        if not photo:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # 刪除實際檔案
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # 從資料庫刪除記錄
        cursor.execute('DELETE FROM photos WHERE id = %s', (photo_id,))
        conn.commit()
        
        return jsonify({'message': 'Success'}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
        
    finally:
        cursor.close()
        conn.close()


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
if __name__ == '__main__':
    app.run(debug=True, port=5000)

