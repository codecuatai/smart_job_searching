"""One configuration source: the repository-root .env, with process overrides."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)


def database_path():
    value = Path(os.getenv('DATABASE_PATH') or 'var/data/unitalent.db')
    return value if value.is_absolute() else ROOT / value


def ai_url():
    return os.getenv('AI_SERVICE_URL') or f"http://127.0.0.1:{os.getenv('AI_PORT', '8001')}"


def allowed_origins():
    port = os.getenv('WEB_PORT', '3000')
    value = os.getenv('ALLOWED_ORIGINS') or f'http://localhost:{port},http://127.0.0.1:{port}'
    return [origin.strip() for origin in value.split(',') if origin.strip()]
