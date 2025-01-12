from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello from Vercel!"

@app.route('/api/test')
def test():
    return {"message": "Test endpoint working"}

# Vercel 需要的
app = app 