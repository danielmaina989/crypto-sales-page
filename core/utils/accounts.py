import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ACCOUNTS_FILE = BASE_DIR / 'accounts.json'


def load_accounts():
    """Load accounts from the local `accounts.json` file.

    - Uses the `accounts.json` in the repository root.
    - Raises FileNotFoundError with a helpful message if missing.
    - Returns a dict of accounts.
    """
    if not ACCOUNTS_FILE.exists():
        raise FileNotFoundError(
            f"Local accounts file not found: {ACCOUNTS_FILE}\n"
            "Create it from `accounts.example.json` and do NOT commit it to git."
        )

    with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

