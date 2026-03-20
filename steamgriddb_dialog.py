import os
import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QScrollArea, QWidget, QGridLayout, QLabel,
    QFileDialog, QMessageBox, QSplitter, QListWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, QObject, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from steamgrid import SteamGridDB


# ── Cache global e session HTTP reutilizável ──────────────────────────────────
_THUMB_CACHE: dict[str, QPixmap] = {}
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "GameHub/1.0"})

# Endpoints da API v2 por tipo de asset
_ASSET_ENDPOINTS = {
    "grid":  "grids",
    "icon":  "icons",
    "hero":  "heroes",
    "logo":  "logos",
}


class ThumbnailSignals(QObject):
    loaded = pyqtSignal(object, QPixmap)


class ThumbnailWorker(QRunnable):
    def __init__(self, url, btn):
        super().__init__()
        self.url = url
        self.btn = btn
        self.signals = ThumbnailSignals()
        self.setAutoDelete(True)

    def run(self):
        try:
            if self.url in _THUMB_CACHE:
                self.signals.loaded.emit(self.btn, _THUMB_CACHE[self.url])
                return
            resp = _SESSION.get(self.url, timeout=10)
            pix  = QPixmap()
            pix.loadFromData(resp.content)
            if not pix.isNull():
                _THUMB_CACHE[self.url] = pix
            self.signals.loaded.emit(self.btn, pix)
        except:
            pass


class SteamGridDBDialog(QDialog):
    def __init__(self, game_name="", asset_type="grid", api_key="", parent=None):
        super().__init__(parent)
        self.api_key        = api_key
        self.asset_type     = asset_type
        self.sgdb           = SteamGridDB(api_key) if api_key else None
        self.games          = []
        self.current_game_id = None
        self.selected_url   = None
        self.save_folder    = ""
        self.result_path    = None
        self._current_page  = 0
        self._has_more      = False
        self._loading       = False

        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(16)

        self.setWindowTitle("SteamGridDB — Selecionar Imagem")
        self.setMinimumSize(980, 660)
        self._build_ui()

        if game_name:
            self.search_input.setText(game_name)
            self._search_games()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # ── Barra de busca ──
        row = QHBoxLayout()
        self.search_input = QLineEdit(placeholderText="Nome do jogo...")
        self.search_input.returnPressed.connect(self._search_games)
        btn_search = QPushButton("Buscar")
        btn_search.clicked.connect(self._search_games)
        row.addWidget(self.search_input)
        row.addWidget(btn_search)
        layout.addLayout(row)

        # ── Splitter: lista de jogos | painel direito ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.games_list = QListWidget()
        self.games_list.setMaximumWidth(210)
        self.games_list.currentRowChanged.connect(self._on_game_selected)
        splitter.addWidget(self.games_list)

        right  = QWidget()
        rl     = QVBoxLayout(right)
        rl.setSpacing(6)

        # Botões de tipo de asset (agora com Logo também)
        type_row = QHBoxLayout()
        self.type_btns = {}
        for label, key in [
            ("Grid/Banner", "grid"),
            ("Ícone",       "icon"),
            ("Hero",        "hero"),
            ("Logo",        "logo"),
        ]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setStyleSheet("""
                QPushButton          { background:#2d2d5a; color:#aaa; border:1px solid #383868;
                                       border-radius:5px; padding:5px 12px; font-size:12px; }
                QPushButton:checked  { background:#4444aa; color:#fff; border-color:#7777dd; }
                QPushButton:hover    { background:#3a3a7a; color:#fff; }
            """)
            b.clicked.connect(lambda _, k=key: self._set_type(k))
            self.type_btns[key] = b
            type_row.addWidget(b)
        type_row.addStretch()
        self.type_btns[self.asset_type].setChecked(True)
        rl.addLayout(type_row)

        # Contador de resultados
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color:#777; font-size:11px;")
        rl.addWidget(self.count_label)

        # Área de scroll com grade de thumbnails
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border:none; }")
        self.grid_container = QWidget()
        self.grid_layout    = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(6)
        self.scroll.setWidget(self.grid_container)
        rl.addWidget(self.scroll)

        # Botão "Carregar mais" + progress bar
        more_row = QHBoxLayout()
        self.btn_more = QPushButton("⬇  Carregar mais")
        self.btn_more.setVisible(False)
        self.btn_more.setStyleSheet("""
            QPushButton       { background:#2d2d5a; color:#aaa; border:1px solid #383868;
                                border-radius:6px; padding:6px 20px; font-size:12px; }
            QPushButton:hover { background:#4444aa; color:#fff; }
        """)
        self.btn_more.clicked.connect(self._load_more)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)        # modo indeterminado
        self.progress.setFixedHeight(4)
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar           { background:#1a1a2e; border:none; border-radius:2px; }
            QProgressBar::chunk    { background:#5555cc; border-radius:2px; }
        """)
        more_row.addStretch()
        more_row.addWidget(self.btn_more)
        more_row.addStretch()
        rl.addWidget(self.progress)
        rl.addLayout(more_row)

        splitter.addWidget(right)
        layout.addWidget(splitter)

        # ── Barra inferior ──
        bottom = QHBoxLayout()
        self.folder_label = QLabel("Pasta de destino: nenhuma selecionada")
        self.folder_label.setStyleSheet("color:#888; font-size:12px;")
        btn_folder = QPushButton("📁 Escolher Pasta")
        btn_folder.clicked.connect(self._choose_folder)
        self.btn_confirm = QPushButton("✔ Usar esta imagem")
        self.btn_confirm.setEnabled(False)
        self.btn_confirm.setStyleSheet("""
            QPushButton          { background:#2563eb; color:#fff; border:none;
                                   border-radius:6px; padding:7px 20px; font-weight:bold; }
            QPushButton:hover    { background:#3b82f6; }
            QPushButton:disabled { background:#1a1a2e; color:#555; }
        """)
        self.btn_confirm.clicked.connect(self._confirm)
        bottom.addWidget(self.folder_label, 1)
        bottom.addWidget(btn_folder)
        bottom.addWidget(self.btn_confirm)
        layout.addLayout(bottom)

    # ── Busca de jogos ────────────────────────────────────────────────────────

    def _search_games(self):
        if not self.sgdb:
            QMessageBox.warning(self, "API Key",
                                "Configure a API Key do SteamGridDB nas Configurações.")
            return
        query = self.search_input.text().strip()
        if not query:
            return
        self.games_list.clear()
        try:
            self.games = self.sgdb.search_game(query)
            for g in self.games:
                self.games_list.addItem(g.name)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _on_game_selected(self, row):
        if 0 <= row < len(self.games):
            self.current_game_id = self.games[row].id
            self._reset_grid()
            self._fetch_page()

    def _set_type(self, key):
        self.asset_type = key
        for k, b in self.type_btns.items():
            b.setChecked(k == key)
        if self.current_game_id:
            self._reset_grid()
            self._fetch_page()

    # ── Paginação ─────────────────────────────────────────────────────────────

    def _reset_grid(self):
        """Limpa a grade e reseta o estado de paginação."""
        while self.grid_layout.count():
            w = self.grid_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self._current_page  = 0
        self._has_more      = False
        self.selected_url   = None
        self.btn_confirm.setEnabled(False)
        self.btn_more.setVisible(False)
        self.count_label.setText("")
        self._image_count   = 0

    def _fetch_page(self):
        if self._loading or not self.current_game_id:
            return
        self._loading = True
        self.progress.setVisible(True)
        self.btn_more.setEnabled(False)

        endpoint = _ASSET_ENDPOINTS.get(self.asset_type, "grids")
        url = (f"https://www.steamgriddb.com/api/v2"
               f"/{endpoint}/game/{self.current_game_id}"
               f"?limit=50&page={self._current_page}")

        # Faz a chamada em thread separada para não travar a UI
        class PageWorker(QRunnable):
            def __init__(self_, url, api_key, signals):
                super().__init__()
                self_.url     = url
                self_.api_key = api_key
                self_.signals = signals
                self_.setAutoDelete(True)

            def run(self_):
                try:
                    resp = _SESSION.get(
                        self_.url,
                        headers={"Authorization": f"Bearer {self_.api_key}"},
                        timeout=15,
                    )
                    data = resp.json()
                    self_.signals.loaded.emit(data)
                except Exception as e:
                    self_.signals.loaded.emit({"success": False, "errors": [str(e)]})

        class PageSignals(QObject):
            loaded = pyqtSignal(dict)

        self._page_signals = PageSignals()
        self._page_signals.loaded.connect(self._on_page_loaded)
        worker = PageWorker(url, self.api_key, self._page_signals)
        self.pool.start(worker)

    def _on_page_loaded(self, data):
        self._loading = False
        self.progress.setVisible(False)
        self.btn_more.setEnabled(True)

        if not data.get("success"):
            errors = data.get("errors", ["Erro desconhecido"])
            QMessageBox.critical(self, "Erro ao buscar imagens", "\n".join(errors))
            return

        assets    = data.get("data", [])
        total     = data.get("total", 0)
        limit     = data.get("limit", 50)
        page      = data.get("page",  0)

        self._has_more = (page + 1) * limit < total
        self.btn_more.setVisible(self._has_more)

        # Dimensões por tipo de asset
        if self.asset_type == "grid":
            thumb_w, thumb_h, cols = 130, 190, 6
        elif self.asset_type == "icon":
            thumb_w, thumb_h, cols = 100, 100, 7
        elif self.asset_type == "hero":
            thumb_w, thumb_h, cols = 200, 75,  4
        else:  # logo
            thumb_w, thumb_h, cols = 180, 80,  4

        start_idx = self._image_count
        for i, asset in enumerate(assets):
            thumb_url = asset.get("thumb", asset.get("url", ""))
            full_url  = asset.get("url",   "")
            if not thumb_url or not full_url:
                continue

            btn = QPushButton()
            btn.setFixedSize(thumb_w, thumb_h)
            btn.setIconSize(QSize(thumb_w - 4, thumb_h - 4))
            btn.setStyleSheet("border:2px solid transparent; border-radius:4px; background:#1a1a2e;")
            btn.clicked.connect(lambda _, u=full_url, b=btn: self._select(u, b))

            idx = start_idx + i
            self.grid_layout.addWidget(btn, idx // cols, idx % cols)

            worker = ThumbnailWorker(thumb_url, btn)
            worker.signals.loaded.connect(self._apply_thumb)
            self.pool.start(worker)

        self._image_count = start_idx + len(assets)
        self._current_page += 1

        # Atualiza contador
        shown = self._image_count
        self.count_label.setText(
            f"{shown} de {total} imagens"
            + (" — clique em 'Carregar mais' para ver o restante" if self._has_more else "")
        )

    def _load_more(self):
        if self._has_more:
            self._fetch_page()

    # ── Interação com thumbnails ──────────────────────────────────────────────

    def _apply_thumb(self, btn, pix):
        try:
            if not pix.isNull():
                btn.setIcon(QIcon(pix))
        except RuntimeError:
            pass  # botão deletado antes do worker terminar

    def _select(self, url, btn):
        self.selected_url = url
        self.btn_confirm.setEnabled(True)
        for i in range(self.grid_layout.count()):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setStyleSheet("border:2px solid transparent; border-radius:4px; background:#1a1a2e;")
        btn.setStyleSheet("border:2px solid #7B68EE; border-radius:4px; background:#1a1a2e;")

    # ── Pasta destino e confirmação ───────────────────────────────────────────

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pasta de destino")
        if folder:
            self.save_folder = folder
            short = folder if len(folder) <= 45 else "…" + folder[-42:]
            self.folder_label.setText(f"📁 {short}")

    def _confirm(self):
        if not self.selected_url:
            return
        if not self.save_folder:
            QMessageBox.warning(self, "Pasta", "Escolha uma pasta de destino primeiro.")
            return
        try:
            resp  = _SESSION.get(self.selected_url, timeout=15)
            ext   = self.selected_url.split(".")[-1].split("?")[0]
            fname = f"sgdb_{self.asset_type}_{abs(hash(self.selected_url)) % 99999}.{ext}"
            path  = os.path.join(self.save_folder, fname)
            with open(path, "wb") as f:
                f.write(resp.content)
            self.result_path = path
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao baixar", str(e))
