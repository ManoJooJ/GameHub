import os
import re

def _get_steam_path():
    try:
        import winreg
        for root, sub in [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
            (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Valve\Steam"),
        ]:
            try:
                key = winreg.OpenKey(root, sub)
                path, _ = winreg.QueryValueEx(key, "InstallPath")
                if os.path.isdir(path):
                    return path
            except:
                continue
    except ImportError:
        pass
    return r"C:\Program Files (x86)\Steam"


def _parse_library_paths(vdf_text):
    """Extrai todos os caminhos de bibliotecas do libraryfolders.vdf."""
    paths = []
    for m in re.finditer(r'"path"\s+"([^"]+)"', vdf_text):
        p = m.group(1).replace("\\\\", "\\")
        if os.path.isdir(p):
            paths.append(p)
    return paths


def _parse_acf(text):
    """Extrai nome, appid e installdir de um appmanifest_*.acf."""
    def val(key):
        m = re.search(rf'"{key}"\s+"([^"]+)"', text, re.IGNORECASE)
        return m.group(1) if m else ""
    appid = val("appid")
    name  = val("name")
    return {"appid": appid, "name": name} if appid and name else None


def scan_steam_games():
    """
    Retorna lista de dicts:
      { "name": str, "appid": str, "launch_cmd": str }
    """
    steam_path = _get_steam_path()
    default_lib = os.path.join(steam_path, "steamapps")
    lib_paths = [default_lib]

    vdf_path = os.path.join(default_lib, "libraryfolders.vdf")
    if os.path.exists(vdf_path):
        with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
            extra = _parse_library_paths(f.read())
        lib_paths += [os.path.join(p, "steamapps") for p in extra]

    games = []
    seen = set()
    for lib in lib_paths:
        if not os.path.isdir(lib):
            continue
        for fname in os.listdir(lib):
            if not (fname.startswith("appmanifest_") and fname.endswith(".acf")):
                continue
            try:
                with open(os.path.join(lib, fname), "r", encoding="utf-8", errors="ignore") as f:
                    game = _parse_acf(f.read())
                if game and game["appid"] not in seen:
                    seen.add(game["appid"])
                    game["launch_cmd"] = f"steam://rungameid/{game['appid']}"
                    games.append(game)
            except:
                pass

    return sorted(games, key=lambda g: g["name"].lower())
