import os
import uvicorn
from multiprocessing import Process
import time

def run_server():
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://dummy:dummy@127.0.0.1:5432/test_db"
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000)

if __name__ == "__main__":
    p = Process(target=run_server)
    p.start()
    time.sleep(3)  # Give the server time to start
