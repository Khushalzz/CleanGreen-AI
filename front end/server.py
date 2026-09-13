"""
Front End Launcher -> Points to Unified Backend Server
"""
import sys
import os
from pathlib import Path

# Add project root and backend to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from server import run

if __name__ == "__main__":
    run()
