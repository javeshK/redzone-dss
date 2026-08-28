# Pytest configuration
import sys
from pathlib import Path

# Add backend/ to path so `from app.main import app` works
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
