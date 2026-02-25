from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QScrollArea, QLabel, QGridLayout, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor, QMovie
from game_card import GameCard
from add_game_dialog import AddGameDialog
from settings_dialog import SettingsDialog
import game_manager, settings_manager, os

def build_style(s):
    return f"""
    * {{ font-family: 'Segoe UI', sans-serif; }}
    QMainWindow, QWidget#root, QWidget#container {{ background: transparent; }}
    QFrame#header {{ background:{s['header_color']}; border-bottom:1px solid #252550; }}
    QLabel#title  {{ font-size:22px; font-weight:bold; color:{s['text_color']}; letter-spacing:1px; }}
    QPushButton#add, QPushButton#cfg {{
        color:white; border:none; border-radius:8px;
        padding:8px 20px; font-size:13px; font-weight:bold;
    }}
    QPushButton#add {{ background:{s['accent_color']}; }}
    QPushButton#add:hover {{ background:{s['accent_color']}dd; }}
    QPushButton#cfg {{ background:#2d2d5a; padding:8px 14px; }}
    QPushButton#cfg:hover {{ background:#4444aa; }}
    QScrollArea {{ border:none; background:transparent; }}
    QLabel#empty {{ color:#444466; font-size:15px; }}
    QScrollBar:vertical {{ background:#161630; width:8px; border-radius:4px; }}
    QScrollBar::handle:vertical {{ background:{s['card_border']}; border-radius:4px; min-height:30px; }}
    QScrollBar::handle:vertical:hover {{ background:#6060aa; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
    """

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 GameHub")
        self.setMinimumSize(860, 560)
        self.resize(1200, 720)
        self._movie      = None
        self._bg_label   = None
        self._drag_id    = None
        self._game_order = []
        self._build_ui()
        self._apply_theme()
        self._refresh()

    def _build_ui(self):
        self.root = QWidget(); self.root.setObjectName("root")
        self.setCentralWidget(self.root)

        self._bg_label = QLabel(self.root)
        self._bg_label.setObjectName("bg")
        self._bg_label.setGeometry(0, 0, self.width(), self.height())
        self._bg_label.lower()

        vbox = QVBoxLayout(self.root)
        vbox.setSpacing(0); vbox.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame(); header.setObjectName("header"); header.setFixedHeight(62)
        hbox = QHBoxLayout(header); hbox.setContentsMargins(22, 0, 22, 0)
        title = QLabel("🎮 GameHub"); title.setObjectName("title")
        self.add_btn = QPushButton("+ Adicionar Jogo"); self.add_btn.setObjectName("add")
        self.add_btn.clicked.connect(self._add_game)
        cfg_btn = QPushButton("⚙️"); cfg_btn.setObjectName("cfg")
        cfg_btn.setToolTip("Configurações")
        cfg_btn.clicked.connect(self._open_settings)
        hbox.addWidget(title); hbox.addStretch()
        hbox.addWidget(self.add_btn); hbox.addWidget(cfg_btn)
        vbox.addWidget(header)

        # Scroll + grid
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self.container = QWidget(); self.container.setObjectName("container")
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(16); self.grid.setContentsMargins(24, 24, 24, 24)
        scroll.setWidget(self.container)
        vbox.addWidget(scroll)

        # Empty state
        self.empty = QLabel(
            "Nenhum jogo adicionado.\nClique em '+ Adicionar Jogo' para começar! 🎮")
        self.empty.setObjectName("empty")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self.empty)

    def _update_bg_pixmap(self, path):
        pix = QPixmap(path)
        w, h = self.width(), self.height()
        scaled = pix.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        x = (scaled.width()  - w) // 2
        y = (scaled.height() - h) // 2
        self._bg_label.setPixmap(scaled.copy(x, y, w, h))

    def _apply_theme(self):
        s = settings_manager.load_settings()
        self.setStyleSheet(build_style(s))

        if self._movie:
            self._movie.stop()
            self._movie = None

        path = s.get("bg_image", "")
        ext  = os.path.splitext(path)[1].lower() if path else ""

        if path and os.path.exists(path) and ext == ".gif":
            self._bg_label.setStyleSheet("")
            self._movie = QMovie(path)
            self._movie.frameChanged.connect(self._update_gif_frame)
            self._movie.start()
        elif path and os.path.exists(path):
            self._update_bg_pixmap(path)
            self._bg_label.setStyleSheet("")
        else:
            self._bg_label.setPixmap(QPixmap())
            self._bg_label.setStyleSheet(f"background:{s['bg_color']};")

    def _update_gif_frame(self):
        if self._movie:
            pix = self._movie.currentPixmap()
            w, h = self.width(), self.height()
            scaled = pix.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            x = (scaled.width()  - w) // 2
            y = (scaled.height() - h) // 2
            self._bg_label.setPixmap(scaled.copy(x, y, w, h))

    def _refresh(self):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()

        games = game_manager.load_games()

        # Aplica ordem salva
        order = settings_manager.load_settings().get("game_order", [])
        if order:
            id_map = {g["id"]: g for g in games}
            ordered = [id_map[i] for i in order if i in id_map]
            known   = set(order)
            ordered += [g for g in games if g["id"] not in known]
            games = ordered

        self._game_order = [g["id"] for g in games]

        if not games:
            self.container.hide(); self.empty.show(); return

        self.empty.hide(); self.container.show()
        cols = max(2, (self.width() - 48) // (185 + 16))
        for i, game in enumerate(games):
            card = GameCard(game)
            card.removed.connect(self._remove_game)
            card.edit_requested.connect(self._edit_game)
            card.drag_moved.connect(self._on_card_drag)
            self.grid.addWidget(card, i // cols, i % cols)

    def _on_card_drag(self, game_id, global_pos):
        local_pos = self.container.mapFromGlobal(global_pos)
        target_id = None
        for i in range(self.grid.count()):
            item = self.grid.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if w.geometry().contains(local_pos):
                    target_id = w.game["id"]
                    break

        if target_id and target_id != game_id:
            i1 = self._game_order.index(game_id)
            i2 = self._game_order.index(target_id)
            self._game_order[i1], self._game_order[i2] = \
                self._game_order[i2], self._game_order[i1]
            s = settings_manager.load_settings()
            s["game_order"] = self._game_order
            settings_manager.save_settings(s)
            self._drag_id = None
            self._refresh()

    def _add_game(self):
        dlg = AddGameDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            game_manager.add_game(d["name"], d["exe_path"],
                                  d["icon_path"], d["banner_path"])
            self._refresh()

    def _edit_game(self, gid):
        games = game_manager.load_games()
        game  = next((g for g in games if g["id"] == gid), None)
        if not game: return
        dlg = AddGameDialog(self, game=game)
        if dlg.exec():
            d = dlg.get_data()
            game_manager.edit_game(d["id"], d["name"], d["exe_path"],
                                   d["icon_path"], d["banner_path"])
            self._refresh()

    def _remove_game(self, gid):
        game_manager.remove_game(gid)
        self._refresh()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self._apply_theme()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._bg_label.setGeometry(0, 0, self.width(), self.height())
        s    = settings_manager.load_settings()
        path = s.get("bg_image", "")
        ext  = os.path.splitext(path)[1].lower() if path else ""
        if path and os.path.exists(path) and ext != ".gif":
            self._update_bg_pixmap(path)
        self._refresh()
