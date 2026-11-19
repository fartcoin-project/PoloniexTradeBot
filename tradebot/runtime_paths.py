import json
import os
import shutil
import sys

APP_NAME = "TradeBot"
MIGRATE_FILES = ("config.json", "tradebot_config.py", "secrets.json")
MIGRATE_FOLDERS = ("json", "orderbooks", "data", "logs", "colibri-models", "colibri-state")


def is_frozen():
    return getattr(sys, "frozen", False)


def install_dir():
    """Directory that contains the executable (frozen) or the source package."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    """Writable data folder — AppData when frozen, else the source package."""
    if not is_frozen():
        return os.path.dirname(os.path.abspath(__file__))
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return os.path.join(local_appdata, APP_NAME)
    return os.path.join(os.path.expanduser("~"), "AppData", "Local", APP_NAME)


def app_dir():
    """Writable folder used by the app (config, logs, caches)."""
    return data_dir()


def bundle_dir():
    if is_frozen():
        return sys._MEIPASS
    return install_dir()


def setup_runtime():
    """Prepare cwd, import path, and data folders."""
    if is_frozen():
        _migrate_legacy_data_if_needed(install_dir(), data_dir())

    root = app_dir()
    os.makedirs(root, exist_ok=True)
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)

    for folder in MIGRATE_FOLDERS:
        os.makedirs(os.path.join(root, folder), exist_ok=True)

    _seed_first_run_files(root)


def _data_dir_has_user_data(root):
    for name in MIGRATE_FILES:
        if os.path.exists(os.path.join(root, name)):
            return True
    return False


def _migrate_legacy_data_if_needed(source_root, dest_root):
    """One-time copy from beside the exe into AppData when AppData is empty."""
    if source_root == dest_root:
        return
    if _data_dir_has_user_data(dest_root):
        return
    if not _data_dir_has_user_data(source_root):
        return

    os.makedirs(dest_root, exist_ok=True)
    for name in MIGRATE_FILES:
        src = os.path.join(source_root, name)
        dest = os.path.join(dest_root, name)
        if os.path.isfile(src) and not os.path.exists(dest):
            shutil.copy2(src, dest)

    for name in MIGRATE_FOLDERS:
        src = os.path.join(source_root, name)
        dest = os.path.join(dest_root, name)
        if not os.path.isdir(src):
            continue
        if os.path.exists(dest):
            continue
        shutil.copytree(src, dest)


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
    """Write Poloniex API credentials into the data folder (never bundled in exe)."""
    root = app_dir()
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "tradebot_config.py")
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
    """Load API keys from tradebot_config.py in the data folder (never bundled in exe)."""
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


def secrets_path():
    return os.path.join(app_dir(), "secrets.json")


def _load_secrets():
    path = secrets_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_secrets(data):
    root = app_dir()
    os.makedirs(root, exist_ok=True)
    path = secrets_path()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def read_hf_token():
    """HuggingFace token for Colibri model downloads (never bundled in exe)."""
    return str(_load_secrets().get("hf_token") or "").strip()


def save_hf_token(token):
    """Persist HF token; empty string clears it."""
    data = _load_secrets()
    value = (token or "").strip()
    if value:
        data["hf_token"] = value
    else:
        data.pop("hf_token", None)
    _save_secrets(data)


def colibri_models_dir():
    return os.path.join(app_dir(), "colibri-models")


def colibri_state_dir():
    return os.path.join(app_dir(), "colibri-state")
