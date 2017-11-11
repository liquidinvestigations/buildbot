import sys
from pathlib import Path

repo = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(repo)]
