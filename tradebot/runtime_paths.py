import os
import shutil
import sys


def is_frozen():
    return getattr(sys, "frozen", False)


def app_dir():
    """Writable folder — exe directory when frozen, else backend/tradebot."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir():
    if is_frozen():
        return sys._MEIPASS
    return app_dir()


def setup_runtime():
    """Prepare cwd, import path, and data folders."""
    root = app_dir()
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)

    for folder in ("json", "orderbooks", "data", "logs"):
        os.makedirs(os.path.join(root, folder), exist_ok=True)

    _seed_first_run_files(root)


def _seed_first_run_files(root):
    config_path = os.path.join(root, "config.json")
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as handle:
            handle.write(
                '{\n    "time": "",\n    "quote_currency": "BTC",\n    "budget": 0.0,\n'
                '    "balance": 0.00000000,\n    "advice": "0.0005",\n'
                '    "exclude": []\n}\n'
            )

    api_config = os.path.join(root, "tradebot_config.py")
    if os.path.exists(api_config):
        return

    example_name = "tradebot_config.EXAMPLE.py"
    for candidate in (os.path.join(root, example_name), os.path.join(bundle_dir(), example_name)):
        if os.path.exists(candidate):
            shutil.copy(candidate, api_config)
            return


PLACEHOLDER_API_KEY = "Poloniex_api_key"
PLACEHOLDER_API_SECRET = "Poloniex_api_secret"


def read_api_credentials():
    """Return (api_key, api_secret) from tradebot_config.py."""
    path = os.path.join(app_dir(), "tradebot_config.py")
    if not os.path.exists(path):
        return "", ""
    try:
        module = load_tradebot_config()
    except (FileNotFoundError, OSError, ImportError, AttributeError):
        return "", ""
    key = getattr(module, "SECRET_API_KEY", "") or ""
    secret = getattr(module, "SECRET_API_SECRET", "") or ""
    return str(key), str(secret)


def save_api_credentials(api_key, api_secret):
    """Write Poloniex API credentials beside the app (never bundled in exe)."""
    path = os.path.join(app_dir(), "tradebot_config.py")
    content = (
        "# SECURITY WARNING: keep the secret key used in production secret!\n"
        f"SECRET_API_KEY = {api_key!r}\n"
        f"SECRET_API_SECRET = {api_secret!r}\n"
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def api_config_ready():
    key, secret = read_api_credentials()
    if not key or not secret:
        return False
    return key != PLACEHOLDER_API_KEY and secret != PLACEHOLDER_API_SECRET


def load_tradebot_config():
    """Load API keys from tradebot_config.py next to the app (never bundled in exe)."""
    import importlib.util

    root = app_dir()
    if root not in sys.path:
        sys.path.insert(0, root)
    path = os.path.join(root, "tradebot_config.py")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"tradebot_config.py not found in {root}. "
            "Copy tradebot_config.EXAMPLE.py and add your Poloniex API keys."
        )
    spec = importlib.util.spec_from_file_location("tradebot_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

