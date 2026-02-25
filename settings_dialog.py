from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFileDialog, QColorDialog,
                              QFrame, QScrollArea, QWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QMovie, QCursor
from image_cropper import ImageCropper
from color_extractor import auto_theme_from_image
import settings_manager, os

def build_style(s):
    accent  = s['accent_color']
    bg      = s['bg_color']
    text    = s['text_color']
    header  = s['header_color']
    border  = s['card_border']

    # Versão discreta do accent: mistura com o fundo
    def subtle(hex_color, factor=0.45):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Interpola entre a cor e um cinza escuro
        r2 = int(r * factor + 40 * (1 - factor))
        g2 = int(g * factor + 40 * (1 - factor))
        b2 = int(b * factor + 40 * (1 - factor))
        return "#{:02x}{:02x}{:02x}".format(
            min(255, r2), min(255, g2), min(255, b2))

    btn_bg      = subtle(accent, 0.35)   # bem discreto
    btn_hover   = subtle(accent, 0.65)   # um pouco mais vivo no hover

    return f"""
    QDialog, QWidget {{ background:{bg}; color:{text}; }}
    QLabel {{ font-size:13px; color:{text}; }}
    QLabel#section {{
        font-size:15px; font-weight:bold;
        color:{text}; margin-top:8px;
    }}
    QFrame#divider {{ background:{border}; max-height:1px; }}
    QScrollArea {{ border:none; background:{bg}; }}

    QPushButton {{
        background:{btn_bg};
        color:{text};
        border:1px solid {border};
        border-radius:6px;
        padding:7px 16px;
        font-size:12px;
        font-weight:500;
        cursor: pointer;
    }}
    QPushButton:hover {{
        background:{btn_hover};
        border-color:{accent};
        color:#ffffff;
    }}

    QPushButton#save {{
        background:{accent};
        color:#ffffff;
        border:none;
        font-size:13px;
        font-weight:bold;
        padding:8px 24px;
    }}
    QPushButton#save:hover {{
        background:{subtle(accent, 1.3)};
        border:none;
    }}
    QPushButton#reset {{
        background:#3a1010;
        color:#ffaaaa;
        border:1px solid #7f1d1d;
    }}
    QPushButton#reset:hover {{
        background:#7f1d1d;
        color:#ffffff;
        border-color:#ef4444;
    }}
    """


class ColorButton(QPushButton):
    def __init__(self, color, label, accent, text_color, parent=None):
        super().__init__(parent)
        self._color      = color
        self._label      = label
        self._accent     = accent
        self._text_color = text_color
        self.setFixedSize(120, 34)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()
        self.clicked.connect(self._pick)

    def _update_style(self):
        self.setText(self._color)
        self.setStyleSheet(f"""
            QPushButton {{
                background:{self._color};
                color:{'#fff' if self._is_dark() else '#000'};
                border:2px solid {self._accent};
                border-radius:6px;
                font-size:11px;
                font-weight:bold;
            }}
            QPushButton:hover {{
                border-color:#ffffff;
                opacity: 0.9;
            }}
        """)

    def _is_dark(self):
        c = QColor(self._color)
        return (c.red()*299 + c.green()*587 + c.blue()*114) / 1000 < 128

    def _pick(self):
        c = QColorDialog.getColor(QColor(self._color), self.window(), self._label)
        if c.isValid():
            self._color = c.name()
            self._update_style()

    def color(self): return self._color


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️  Configurações")
        self.setFixedSize(520, 580)
        self._s = settings_manager.load_settings()
        self.setStyleSheet(build_style(self._s))
        self._build_ui()

    def _make_btn(self, text, slot, object_name=None):
        """Helper que cria botão já com cursor de mão."""
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(slot)
        if object_name:
            btn.setObjectName(object_name)
        return btn

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget()
        content.setStyleSheet(f"background:{self._s['bg_color']};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # ── Imagem de Fundo ────────────────────────────────
        self._section(layout, "🖼️  Imagem de Fundo")

        self._bg_preview = QLabel()
        self._bg_preview.setFixedSize(200, 112)
        self._bg_preview.setStyleSheet(f"""
            background:{self._s['header_color']};
            border:2px solid {self._s['accent_color']};
            border-radius:6px;
        """)
        self._bg_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_bg_preview()

        btn_choose = self._make_btn("📂  Escolher imagem", self._pick_bg)
        btn_remove = self._make_btn("🗑  Remover fundo",   self._remove_bg)
        btn_auto   = self._make_btn("🎨  Cores automáticas", self._apply_auto_colors)
        btn_auto.setToolTip("Extrai as cores do background e aplica no tema")
        self._auto_btn = btn_auto

        bg_btns = QHBoxLayout()
        bg_btns.addWidget(self._bg_preview)
        bg_btns.addSpacing(12)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)
        btn_col.addWidget(btn_choose)
        btn_col.addWidget(btn_remove)
        btn_col.addWidget(btn_auto)
        btn_col.addStretch()

        bg_btns.addLayout(btn_col)
        bg_btns.addStretch()
        layout.addLayout(bg_btns)

        self._divider(layout)

        # ── Cores ──────────────────────────────────────────
        self._section(layout, "🎨  Cores")

        colors = [
            ("bg_color",     "Cor de fundo"),
            ("accent_color", "Cor de destaque (botões)"),
            ("header_color", "Cor do cabeçalho"),
            ("card_border",  "Borda dos cards"),
            ("text_color",   "Cor do texto"),
        ]
        self._color_btns = {}
        for key, label in colors:
            row = QHBoxLayout()
            lbl = QLabel(label); lbl.setFixedWidth(200)
            btn = ColorButton(
                self._s[key], label,
                self._s["accent_color"],
                self._s["text_color"])
            self._color_btns[key] = btn
            row.addWidget(lbl); row.addWidget(btn); row.addStretch()
            layout.addLayout(row)

        self._divider(layout)

        # ── Botões de ação ─────────────────────────────────
        action_row = QHBoxLayout()
        reset = self._make_btn("↩  Restaurar Padrões", self._reset, "reset")
        save  = self._make_btn("💾  Salvar",            self._save,  "save")
        action_row.addWidget(reset)
        action_row.addStretch()
        action_row.addWidget(save)
        layout.addLayout(action_row)
        layout.addStretch()

    def _section(self, layout, text):
        lbl = QLabel(text); lbl.setObjectName("section")
        layout.addWidget(lbl)

    def _divider(self, layout):
        line = QFrame(); line.setObjectName("divider")
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

    def _update_bg_preview(self):
        path = self._s.get("bg_image", "")
        if path and os.path.exists(path):
            ext = os.path.splitext(path)[1].lower()
            if ext == ".gif":
                movie = QMovie(path)
                movie.jumpToFrame(0)
                frame = movie.currentPixmap().scaled(
                    200, 112,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation)
                self._bg_preview.setPixmap(frame)
                self._bg_preview.setText("")
            else:
                pix = QPixmap(path).scaled(
                    200, 112,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation)
                self._bg_preview.setPixmap(pix)
                self._bg_preview.setText("")
        else:
            self._bg_preview.setPixmap(QPixmap())
            self._bg_preview.setText("Sem imagem")

    def _pick_bg(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar imagem de fundo", "",
            "Imagens e GIFs (*.png *.jpg *.jpeg *.webp *.gif);;Todos (*)")
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext == ".gif":
            self._s["bg_image"] = path
            self._update_bg_preview()
        else:
            cropper = ImageCropper(path, 1920, 1080, "Ajustar Imagem de Fundo", parent=self)
            if cropper.exec() and cropper.result_path:
                self._s["bg_image"] = cropper.result_path
                self._update_bg_preview()

    def _remove_bg(self):
        self._s["bg_image"] = ""
        self._update_bg_preview()

    def _apply_auto_colors(self):
        path = self._s.get("bg_image", "")
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Sem imagem",
                                "Adicione uma imagem de fundo primeiro.")
            return
        theme = auto_theme_from_image(path)
        if not theme:
            QMessageBox.warning(self, "Erro",
                                "Não foi possível extrair as cores da imagem.")
            return
        for key, val in theme.items():
            self._s[key] = val
            if key in self._color_btns:
                self._color_btns[key]._color = val
                self._color_btns[key]._update_style()
        self.setStyleSheet(build_style(self._s))

    def _reset(self):
        self._s = dict(settings_manager.DEFAULTS)
        for key, btn in self._color_btns.items():
            btn._color = self._s[key]
            btn._update_style()
        self.setStyleSheet(build_style(self._s))
        self._update_bg_preview()

    def _save(self):
        for key, btn in self._color_btns.items():
            self._s[key] = btn.color()
        settings_manager.save_settings(self._s)
        self.accept()
