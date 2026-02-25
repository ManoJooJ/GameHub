import json, os

DATA_FILE = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                         "GameHub", "settings.json")

DEFAULTS = {
    "bg_image":     "",
    "bg_color":     "#0d0d1f",
    "accent_color": "#2563eb",
    "header_color": "#131330",
    "card_border":  "#383868",
    "text_color":   "#e2e8f0",
    "game_order":   [],
}

def load_settings():
    if not os.path.exists(DATA_FILE):
        return dict(DEFAULTS)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {**DEFAULTS, **data}

def save_settings(settings):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
