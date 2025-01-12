from flask import Flask, jsonify
import os

app = Flask(__name__)

# 基本配置
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

@app.route('/')
def index():
    try:
        return jsonify({
            "status": "success",
            "message": "API is running",
            "env_test": {
                "secret_key": bool(os.getenv('SECRET_KEY')),
                "mysql_host": bool(os.getenv('MYSQL_HOST'))
            }
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": str(type(e))
        }), 500

@app.route('/api/test')
def test():
    return jsonify({
        "status": "success",
        "message": "Test endpoint working"
    })

@app.errorhandler(500)
def handle_500(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": str(error)
    }), 500

# Vercel 需要的
app = app 