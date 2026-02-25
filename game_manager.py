import json, os, uuid

DATA_FILE = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                         "GameHub", "games.json")

def load_games():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_games(games):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)

def add_game(name, exe_path, icon_path="", banner_path=""):
    games = load_games()
    game  = {
        "id":          str(uuid.uuid4()),
        "name":        name,
        "exe_path":    exe_path,
        "icon_path":   icon_path,    # ✅ caminho original, sem copiar
        "banner_path": banner_path,  # ✅ caminho original, sem copiar
    }
    games.append(game)
    save_games(games)
    return game

def remove_game(game_id):
    games = [g for g in load_games() if g["id"] != game_id]
    save_games(games)

def edit_game(game_id, name, exe_path, icon_path="", banner_path=""):
    games = load_games()
    for g in games:
        if g["id"] == game_id:
            g["name"]        = name
            g["exe_path"]    = exe_path
            g["icon_path"]   = icon_path    # ✅ caminho original
            g["banner_path"] = banner_path  # ✅ caminho original
            break
    save_games(games)
