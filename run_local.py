import sys
import os
import uvicorn
from pathlib import Path

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    print("==================================================================")
    print(" Starting Intelligent Media Processing Pipeline Server...")
    print(" Web Dashboard UI:  http://127.0.0.1:8000/dashboard")
    print(" Swagger API Docs:  http://127.0.0.1:8000/docs")
    print("==================================================================")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
