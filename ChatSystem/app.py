# api/index.py
from ChatSystem.app import app

# Vercel cần cái này để chạy
if __name__ == '__main__':
    app.run()