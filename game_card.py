from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, pyqtProperty, QEasingCurve, QRect, QRectF, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPainterPath, QPen, QMovie
import subprocess, os


CARD_W, CARD_H = 185, 275


class GameCard(QWidget):
    removed        = pyqtSignal(str)
    edit_requested = pyqtSignal(str)
    drag_moved     = pyqtSignal(str, object)

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self._hover_progress = 0.0
        self._dragging       = False
        self._drag_origin    = None

        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

        self._icon_pix     = None
        self._icon_movie   = None
        self._banner_pix   = None
        self._banner_movie = None

        self._load_asset(game.get("icon_path",   ""), is_banner=False)
        self._load_asset(game.get("banner_path", ""), is_banner=True)

        self._anim = QPropertyAnimation(self, b"hover_progress")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Carregamento de assets (estático ou GIF) ───────────────────────────

    def _load_asset(self, path, is_banner):
        if not path or not os.path.exists(path):
            return

        if path.lower().endswith(".gif"):
            movie = QMovie(path)
            movie.setScaledSize(QSize(CARD_W, CARD_H))
            movie.frameChanged.connect(self.update)   # redesenha a cada frame
            movie.start()
            if is_banner:
                self._banner_movie = movie
            else:
                self._icon_movie = movie
        else:
            pix = QPixmap(path).scaled(
                CARD_W, CARD_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            if is_banner:
                self._banner_pix = pix
            else:
                self._icon_pix = pix

    def _current_frame(self, movie, pix):
        """Retorna o frame atual do QMovie (GIF) ou o QPixmap estático."""
        if movie:
            return movie.currentPixmap()
        return pix

    def _draw_centered(self, painter, pixmap):
        """
        Desenha o pixmap centralizado no card.
        Necessário para KeepAspectRatioByExpanding, onde uma das dimensões
        pode exceder CARD_W/CARD_H — centralizar evita corte assimétrico.
        O clip path arredondado já impede qualquer 'vazamento'.
        """
        if not pixmap or pixmap.isNull():
            return
        x = (CARD_W - pixmap.width())  // 2
        y = (CARD_H - pixmap.height()) // 2
        painter.drawPixmap(x, y, pixmap)

    # ── Propriedade animada ────────────────────────────────────────────────

    @pyqtProperty(float)
    def hover_progress(self): return self._hover_progress

    @hover_progress.setter
    def hover_progress(self, val):
        self._hover_progress = val
        self.update()

    # ── Eventos de mouse ──────────────────────────────────────────────────

    def enterEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def leaveEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = e.pos()
            self._dragging    = False

    def mouseMoveEvent(self, e):
        if not (e.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._drag_origin is None:
            return
        if (e.pos() - self._drag_origin).manhattanLength() > 10:
            self._dragging = True
            self.drag_moved.emit(self.game["id"], self.mapToGlobal(e.pos()))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            if not self._dragging:
                exe = self.game.get("exe_path", "")
                if exe:
                    if exe.startswith("steam://"):
                        # Jogos importados via varredura Steam
                        subprocess.Popen(["start", "", exe], shell=True)
                    elif os.path.exists(exe):
                        subprocess.Popen([exe], cwd=os.path.dirname(exe))
            self._dragging    = False
            self._drag_origin = None

    # ── Menu de contexto ──────────────────────────────────────────────────

    def _context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#1a1a2e; color:white; border:1px solid #333355;
                    border-radius:6px; padding:4px; }
            QMenu::item { padding:6px 18px; border-radius:4px; }
            QMenu::item:selected { background:#3d3d7a; }
        """)
        edit_action   = menu.addAction("✏️  Editar Jogo")
        menu.addSeparator()
        remove_action = menu.addAction("🗑  Remover Jogo")
        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_action:
            self.edit_requested.emit(self.game["id"])
        elif action == remove_action:
            self.removed.emit(self.game["id"])

    # ── Renderização ──────────────────────────────────────────────────────

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform,
        )

        # Clip arredondado — impede vazamento de qualquer camada
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, CARD_W, CARD_H), 12, 12)
        p.setClipPath(clip)

        # Camada 1 — ícone (estado padrão)
        icon_frame = self._current_frame(self._icon_movie, self._icon_pix)
        if icon_frame:
            p.setOpacity(1.0)
            self._draw_centered(p, icon_frame)
        else:
            p.fillRect(0, 0, CARD_W, CARD_H, QColor(28, 28, 55))
            p.setPen(QColor(140, 140, 200))
            p.setFont(QFont("Segoe UI Emoji", 52, QFont.Weight.Bold))
            p.drawText(
                QRect(0, 0, CARD_W, CARD_H - 40),
                Qt.AlignmentFlag.AlignCenter,
                self.game["name"][0].upper(),
            )

        # Camada 2 — banner com fade no hover (suporta GIF)
        if self._hover_progress > 0:
            banner_frame = self._current_frame(self._banner_movie, self._banner_pix)
            if banner_frame:
                p.setOpacity(self._hover_progress)
                self._draw_centered(p, banner_frame)

        # Camada 3 — overlay com nome do jogo
        if self._hover_progress > 0:
            p.setOpacity(self._hover_progress * 0.88)
            p.fillRect(0, CARD_H - 70, CARD_W, 70, QColor(0, 0, 0))
            p.setOpacity(self._hover_progress)
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Segoe UI Emoji", 11, QFont.Weight.Bold))
            p.drawText(
                QRect(10, CARD_H - 65, CARD_W - 20, 60),
                Qt.AlignmentFlag.AlignVCenter,
                self.game["name"],
            )

        # Borda colorida (desabilita clip para não cortar a borda)
        p.setOpacity(1.0)
        p.setClipping(False)

        import settings_manager
        s = settings_manager.load_settings()
        base_color = QColor(s.get("card_border", "#6060cc"))

        if self._hover_progress > 0:
            r = min(255, int(base_color.red()   * (1 + self._hover_progress * 0.6)))
            g = min(255, int(base_color.green() * (1 + self._hover_progress * 0.6)))
            b = min(255, int(base_color.blue()  * (1 + self._hover_progress * 0.6)))
            border_color = QColor(r, g, b)
            pen_width    = 3
        else:
            border_color = base_color
            pen_width    = 2

        p.setPen(QPen(border_color, pen_width))
        p.drawRoundedRect(1, 1, CARD_W - 2, CARD_H - 2, 12, 12)
        p.end()
