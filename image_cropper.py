from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QSizePolicy)
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor
from PIL import Image
import os, tempfile

STYLE = """
QDialog { background:#12122a; color:#fff; }
QPushButton {
    background:#2d2d5a; color:white; border:none;
    border-radius:6px; padding:7px 18px; font-size:12px;
}
QPushButton:hover { background:#4444aa; }
QPushButton#confirm {
    background:#2563eb; font-weight:bold; font-size:13px; padding:8px 24px;
}
QPushButton#confirm:hover { background:#3b82f6; }
QLabel#hint { color:#6666aa; font-size:12px; }
"""

class CropCanvas(QLabel):
    def __init__(self, pixmap, target_w, target_h, parent=None):
        super().__init__(parent)
        self.target_w = target_w
        self.target_h = target_h
        self._orig_pixmap = pixmap

        max_display = 600
        scale = min(max_display / pixmap.width(), max_display / pixmap.height(), 1.0)
        self._disp_w = int(pixmap.width() * scale)
        self._disp_h = int(pixmap.height() * scale)
        self._scale = scale
        self._display_pixmap = pixmap.scaled(
            self._disp_w, self._disp_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)

        self.setFixedSize(self._disp_w, self._disp_h)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

        ratio = target_w / target_h
        crop_h = min(self._disp_h, int(self._disp_w / ratio))
        crop_w = int(crop_h * ratio)
        self._crop = QRect(
            (self._disp_w - crop_w) // 2,
            (self._disp_h - crop_h) // 2,
            crop_w, crop_h)

        self._drag_start = None
        self._crop_start = None
        self._resizing   = None

    def _handle_size(self): return 12

    def _handle_rects(self):
        r = self._crop
        h = self._handle_size()
        return {
            'tl': QRect(r.left()  - h//2, r.top()    - h//2, h, h),
            'tr': QRect(r.right() - h//2, r.top()    - h//2, h, h),
            'bl': QRect(r.left()  - h//2, r.bottom() - h//2, h, h),
            'br': QRect(r.right() - h//2, r.bottom() - h//2, h, h),
        }

    def mousePressEvent(self, e):
        pos = e.pos()
        for key, rect in self._handle_rects().items():
            if rect.contains(pos):
                self._resizing   = key
                self._drag_start = pos
                self._crop_start = QRect(self._crop)
                self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
                return
        if self._crop.contains(pos):
            self._drag_start = pos
            self._crop_start = QRect(self._crop)
            self._resizing   = None
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseMoveEvent(self, e):
        if self._drag_start is None:
            return
        dx = e.pos().x() - self._drag_start.x()
        dy = e.pos().y() - self._drag_start.y()
        r  = QRect(self._crop_start)
        ratio = self.target_w / self.target_h

        if self._resizing:
            k = self._resizing
            if 'r' in k:
                new_w = max(60, r.width() + dx)
            else:
                new_w = max(60, r.width() - dx)
            new_h = int(new_w / ratio)

            if 'l' in k: r.setLeft(r.right() - new_w)
            else:         r.setRight(r.left() + new_w)
            if 't' in k: r.setTop(r.bottom() - new_h)
            else:         r.setBottom(r.top() + new_h)
        else:
            r.moveTopLeft(self._crop_start.topLeft() + QPoint(dx, dy))

        r.setLeft  (max(0, r.left()))
        r.setTop   (max(0, r.top()))
        r.setRight (min(self._disp_w, r.right()))
        r.setBottom(min(self._disp_h, r.bottom()))
        self._crop = r
        self.update()

    def mouseReleaseEvent(self, e):
        self._drag_start = None
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._display_pixmap)

        p.setBrush(QColor(0, 0, 0, 140))
        p.setPen(Qt.PenStyle.NoPen)
        r = self._crop
        p.drawRect(0,         0,          self._disp_w, r.top())
        p.drawRect(0,         r.bottom(), self._disp_w, self._disp_h - r.bottom())
        p.drawRect(0,         r.top(),    r.left(),     r.height())
        p.drawRect(r.right(), r.top(),    self._disp_w - r.right(), r.height())

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(99, 179, 237), 2))
        p.drawRect(r)
        p.setBrush(QColor(99, 179, 237))
        for rect in self._handle_rects().values():
            p.drawRect(rect)

        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        for i in (1, 2):
            x = r.left() + r.width()  * i // 3
            y = r.top()  + r.height() * i // 3
            p.drawLine(x, r.top(), x, r.bottom())
            p.drawLine(r.left(), y, r.right(), y)

        p.end()

    def get_cropped_path(self, original_path):
        r     = self._crop
        scale = 1.0 / self._scale
        x1 = int(r.left()   * scale)
        y1 = int(r.top()    * scale)
        x2 = int(r.right()  * scale)
        y2 = int(r.bottom() * scale)

        img = Image.open(original_path).convert("RGBA")
        cropped = img.crop((x1, y1, x2, y2)).resize(
            (self.target_w, self.target_h), Image.LANCZOS)

        # ✅ Salva na pasta AppData do usuário, não na pasta do projeto
        app_data = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                                "GameHub", "crops")
        os.makedirs(app_data, exist_ok=True)

        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".png", dir=app_data)
        cropped.save(tmp.name, format="PNG")
        return tmp.name


class ImageCropper(QDialog):
    def __init__(self, image_path, target_w, target_h, title="Ajustar imagem", parent=None):
        super().__init__(parent)
        self.image_path  = image_path
        self.result_path = None
        self.setWindowTitle(title)
        self.setStyleSheet(STYLE)
        self.setModal(True)
        self._build_ui(target_w, target_h)

    def _build_ui(self, tw, th):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hint = QLabel("🖱️  Arraste para mover · Cantos para redimensionar")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        pixmap = QPixmap(self.image_path)
        self.canvas = CropCanvas(pixmap, tw, th, self)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        center = QHBoxLayout()
        center.addStretch(); center.addWidget(self.canvas); center.addStretch()
        layout.addLayout(center)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel  = QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        confirm = QPushButton("Aplicar");  confirm.setObjectName("confirm")
        confirm.clicked.connect(self._apply)  # ✅ método existe agora
        btns.addWidget(cancel); btns.addWidget(confirm)
        layout.addLayout(btns)

        self.adjustSize()

    def _apply(self):  # ✅ método que estava faltando
        self.result_path = self.canvas.get_cropped_path(self.image_path)
        self.accept()
