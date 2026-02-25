from PIL import Image
import os

def extract_colors(image_path, n=5):
    """Retorna as n cores mais dominantes da imagem como hex."""
    if not image_path or not os.path.exists(image_path):
        return []
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((150, 150))  # reduz pra ser rápido
        result = img.quantize(colors=n).convert("RGB")
        palette = result.getcolors(maxcolors=150*150)
        if not palette:
            return []
        palette.sort(reverse=True)
        colors = []
        for _, rgb in palette[:n]:
            colors.append("#{:02x}{:02x}{:02x}".format(*rgb))
        return colors
    except Exception:
        return []

def is_dark(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    return (r*299 + g*587 + b*114) / 1000 < 128

def darken(hex_color, factor=0.6):
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r*factor), int(g*factor), int(b*factor))

def lighten(hex_color, factor=1.4):
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(
        min(255,int(r*factor)), min(255,int(g*factor)), min(255,int(b*factor)))

def auto_theme_from_image(image_path):
    """Gera um dicionário de cores de tema baseado na imagem."""
    colors = extract_colors(image_path, n=8)
    if not colors:
        return None

    # Cor dominante → header
    dominant = colors[0]
    # Segunda cor → accent
    accent = colors[1] if len(colors) > 1 else colors[0]

    # Header é a cor dominante levemente escurecida
    header = darken(dominant, 0.75)

    # Accent é a segunda cor — se for muito escura, clareia
    if is_dark(accent):
        accent = lighten(accent, 1.6)

    # Fundo é a cor dominante bem escurecida
    bg = darken(dominant, 0.35)

    # Texto: branco se fundo escuro, escuro se fundo claro
    text = "#f0f0f0" if is_dark(header) else "#111111"

    # Borda dos cards: cor intermediária
    border = darken(dominant, 0.55)

    return {
        "bg_color":     bg,
        "accent_color": accent,
        "header_color": header,
        "card_border":  border,
        "text_color":   text,
    }
