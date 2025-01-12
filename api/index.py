from app import app

# Vercel 需要這個處理函數
def handler(request, context):
    return app 