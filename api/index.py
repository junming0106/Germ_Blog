from flask import Flask, render_template, request, redirect, session
import os
from dotenv import load_dotenv

# 基本設置
app = Flask(__name__, 
    static_folder='../static',
    template_folder='../templates')

# 簡單的路由測試
@app.route('/')
def index():
    return "Hello World"  # 先用最簡單的回應測試

# Vercel 需要的
app = app 