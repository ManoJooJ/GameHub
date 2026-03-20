from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFileDialog, QFormLayout,
                              QMessageBox, QWidget)
from PyQt6.QtCore import Qt
from image_cropper import ImageCropper
from steamgriddb_dialog import SteamGridDBDialog
import settings_manager, os


STYLE = """
QDialog { background:#12122a; color:#fff; }
QLabel  { color:#bbb; font-size:13px; }
QLineEdit {
    background:#1e1e3a; border:1px solid #383868;
    border-radius:6px; padding:6px 10px; color:#fff; font-size:13px;
}
QLineEdit:focus { border-color:#5555cc; }
QPushButton {
    background:#2d2d5a; color:white; border:none;
    border-radius:6px; padding:6px 14px; font-size:12px;
}
QPushButton:hover { background:#4444aa; }
QPushButton#confirm {
    background:#2563eb; padding:8px 22px;
    font-size:13px; font-weight:bold;
}
QPushButton#confirm:hover { background:#3b82f6; }
QPushButton#sgdb {
    background:#1b4d2e; color:#4ade80; border:1px solid #166534;
    padding:6px 8px; font-size:11px;
}
QPushButton#sgdb:hover { background:#166534; color:#fff; }
"""


ICON_W,   ICON_H   = 185, 275
BANNER_W, BANNER_H = 185, 275


class AddGameDialog(QDialog):
    def __init__(self, parent=None, game=None):
        super().__init__(parent)
        self._edit_mode = game is not None
        self._game = game or {}
        self.setWindowTitle("Editar Jogo" if self._edit_mode else "Adicionar Jogo")
        self.setFixedSize(560, 290)
        self.setStyleSheet(STYLE)
        self._build_ui()

        if self._edit_mode:
            self.name_input.setText(game.get("name", ""))
            self.exe_input.setText(game.get("exe_path", ""))
            self.icon_input.setText(game.get("icon_path", ""))
            self.banner_input.setText(game.get("banner_path", ""))

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 22, 22, 22)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input   = QLineEdit(); self.name_input.setPlaceholderText("Ex: GTA V")
        self.exe_input    = QLineEdit(); self.exe_input.setPlaceholderText("Caminho do .exe")
        self.icon_input   = QLineEdit(); self.icon_input.setPlaceholderText("PNG/GIF do ícone")
        self.banner_input = QLineEdit(); self.banner_input.setPlaceholderText("PNG/JPG/GIF do banner (hover)")

        form.addRow("Nome:",           self.name_input)
        form.addRow("Executável:",     self._row(self.exe_input,    "exe"))
        form.addRow("Ícone:",          self._row(self.icon_input,   "icon"))
        form.addRow("Banner (hover):", self._row(self.banner_input, "banner"))

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel  = QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        label   = "Salvar Alterações" if self._edit_mode else "Adicionar Jogo"
        confirm = QPushButton(label); confirm.setObjectName("confirm")
        confirm.clicked.connect(self._confirm)
        btns.addWidget(cancel); btns.addWidget(confirm)
        layout.addLayout(btns)

    def _row(self, field, mode):
        container = QHBoxLayout()
        container.setSpacing(4)

        btn_browse = QPushButton("…")
        btn_browse.setFixedWidth(34)
        btn_browse.clicked.connect(lambda: self._browse(field, mode))
        container.addWidget(field)
        container.addWidget(btn_browse)

        # Botão SteamGridDB — apenas para ícone e banner
        if mode in ("icon", "banner"):
            asset_type = "icon" if mode == "icon" else "grid"
            btn_sgdb = QPushButton("🎮 SGDB")
            btn_sgdb.setObjectName("sgdb")
            btn_sgdb.setToolTip("Buscar imagem no SteamGridDB")
            btn_sgdb.setFixedWidth(70)
            btn_sgdb.clicked.connect(lambda: self._browse_sgdb(field, asset_type))
            container.addWidget(btn_sgdb)

        w = QWidget(); w.setLayout(container)
        return w

    def _browse(self, field, mode):
        if mode == "exe":
            path, _ = QFileDialog.getOpenFileName(
                self, "Selecionar .exe", "",
                "Executáveis (*.exe *.bat *.sh);;Todos (*)")
            if path:
                field.setText(path)
                if not self.name_input.text():
                    self.name_input.setText(
                        os.path.splitext(os.path.basename(path))[0])
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar imagem", "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.gif);;Todos (*)")
        if not path:
            return

        # GIF: pula o cropper direto
        if path.lower().endswith(".gif"):
            field.setText(path)
            return

        if mode == "icon":
            tw, th, title = ICON_W, ICON_H, "Ajustar Ícone"
        else:
            tw, th, title = BANNER_W, BANNER_H, "Ajustar Banner"

        cropper = ImageCropper(path, tw, th, title, parent=self)
        if cropper.exec() and cropper.result_path:
            field.setText(cropper.result_path)

    def _browse_sgdb(self, field, asset_type):
        api_key   = settings_manager.load_settings().get("sgdb_api_key", "")
        game_name = self.name_input.text().strip()
        dlg = SteamGridDBDialog(
            game_name=game_name,
            asset_type=asset_type,
            api_key=api_key,
            parent=self,
        )
        if dlg.exec() and dlg.result_path:
            field.setText(dlg.result_path)

    def _confirm(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Insira o nome do jogo.")
            return
        if not self.exe_input.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Selecione o executável.")
            return
        self.accept()

    def get_data(self):
        data = {
            "name":        self.name_input.text().strip(),
            "exe_path":    self.exe_input.text().strip(),
            "icon_path":   self.icon_input.text().strip(),
            "banner_path": self.banner_input.text().strip(),
        }
        if self._edit_mode:
            data["id"] = self._game["id"]
        return data
