# GermBlog

一個使用 Flask 和 Tailwind CSS 建立的部落格系統。

## 功能

- 用戶註冊和登入
- 文章發布和管理
- 深色模式支援
- 響應式設計
- 使用 Flask 和 Tailwind CSS 建立

## 使用程式語言

- Python 3.13
- Flask
- MySQL
- Tailwind CSS
- HTML/CSS/JavaScript

# Germ_Blog

## 更新 git

# 1. 確保在正確的目錄

cd ~/Desktop/Blog_web

# 2. 檢查當前狀態

git status

# 3. 添加更改的文件

git add requirements.txt vercel.json

# 4. 提交更改

git commit -m "Update vercel.json and requirements.txt for Vercel deployment"

# 5. 推送到 GitHub

git push origin main

# 6. 部署到 Vercel

{
// 指定 Vercel 配置文件版本
"version": 2,

// 構建設置：告訴 Vercel 如何構建專案
"builds": [
{
"src": "app.py", // 指定入口文件
"use": "@vercel/python" // 使用 Python 運行環境
}
],

// 路由設置：定義如何處理請求
"routes": [
{
"src": "/(.*)", // 匹配所有 URL 路徑
"dest": "/app.py" // 將所有請求轉發到 app.py
}
],

// 環境變數設置
"env": {
"FLASK_ENV": "production", // Flask 運行在生產模式
"FLASK_APP": "app.py" // 指定 Flask 應用入口
}
}
