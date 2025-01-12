from flask import Flask, render_template, request, redirect, session, jsonify
import os
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, 
    static_folder='../static',    # 指向上層的 static 資料夾
    template_folder='../templates' # 指向上層的 templates 資料夾
)

# 基本配置
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

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

csrf = CSRFProtect(app)

# 路由
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return jsonify({
            "error": "Template Error",
            "message": str(e)
        }), 500

@app.route('/api/test')
def test():
    return jsonify({
        "status": "success",
        "message": "API is working!",
        "version": "1.0",
        "env": {
            "MYSQL_HOST": os.getenv('MYSQL_HOST', 'not set'),
            "DATABASE": os.getenv('MYSQL_DATABASE', 'not set')
        }
    })

# 錯誤處理
@app.errorhandler(500)
def handle_500(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": str(error)
    }), 500

@app.errorhandler(404)
def handle_404(error):
    return jsonify({
        "error": "Not Found",
        "message": str(error)
    }), 404

# Vercel 需要的
app = app 