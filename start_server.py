import uvicorn
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = open("server_output.log", "w", encoding="utf-8")
sys.stderr = sys.stdout

uvicorn.run("app.main:app", port=8000, host="0.0.0.0", log_level="info")
