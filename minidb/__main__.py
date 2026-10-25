import sys
from .cli import run

if __name__ == "__main__":
    db_dir = sys.argv[1] if len(sys.argv) > 1 else "mydb"
    run(db_dir)