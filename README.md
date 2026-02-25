<h1 align="center">
  🎮 GameHub
</h1>

<p align="center">
  Um Hub/Launcher de jogos pessoal, bonito e personalizável, feito em Python com PyQt6.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white"/>
  <img alt="PyQt6" src="https://img.shields.io/badge/PyQt6-6.x-green?logo=qt&logoColor=white"/>
  <img alt="Pillow" src="https://img.shields.io/badge/Pillow-imaging-orange"/>
  <img alt="Windows" src="https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows"/>
</p>

---

## 📌 O que é o GameHub?

O **GameHub** é um launcher de jogos pessoal para Windows. Ele centraliza todos os seus jogos em um só lugar, com uma interface visual moderna — sem depender de Steam, Epic ou qualquer outra plataforma. Você adiciona seus jogos manualmente, define ícones e banners personalizados, e abre qualquer jogo com um único clique.

---

## ✨ Funcionalidades

- 🗂️ **Adicione seus jogos** informando o nome, o caminho do executável (`.exe`), um ícone e um banner
- 🖱️ **Abra qualquer jogo com um clique** direto no card
- 🖼️ **Banner no hover** — passe o mouse sobre o card para ver o banner do jogo com animação de fade suave
- ✂️ **Editor de crop integrado** — ajuste o enquadramento de ícones e banners antes de salvar (arrastar, redimensionar, grid de terços)
- ✏️ **Editar/remover** jogos pelo menu de contexto (botão direito no card)
- 🔀 **Reordenar cards** arrastando e soltando os jogos na posição que preferir
- 🎨 **Tema totalmente personalizável** — cor de fundo, destaque, cabeçalho, borda dos cards e texto
- 🖼️ **Imagem de fundo** (PNG, JPG ou **GIF animado**)
- 🤖 **Cores automáticas** — extrai as cores dominantes do wallpaper e aplica automaticamente no tema
- 💾 **Dados salvos por usuário** em `AppData\Roaming\GameHub` — cada pessoa que usar o programa terá seus próprios dados separados

---

## 🖥️ Pré-requisitos (para rodar o código)

- [Python 3.13](https://www.python.org/downloads/)
- Dependências:

```bash
pip install PyQt6 Pillow
```

---

## 🚀 Como rodar

```bash
# Clone o repositório
git clone https://github.com/ManoJooJ/GameHub.git
cd GameHub

# Instale as dependências
pip install PyQt6 Pillow

# Execute
python main.py
```

---

## 📦 Como compilar o executável

Para gerar o `.exe` pronto para distribuir (sem precisar de Python instalado):

```bash
# Instale o PyInstaller
pip install pyinstaller

# Compile
pyinstaller --noconfirm --clean --onedir --windowed --name GameHub --icon assets\gamehub.ico main.py
```

O executável gerado ficará em:
```
dist\GameHub\GameHub.exe
```

Basta zipar a pasta `dist\GameHub\` e enviar para outro PC — não precisa instalar nada.

---

## 📁 Estrutura do projeto

```
game_hub/
├── main.py                # Ponto de entrada
├── main_window.py         # Janela principal
├── game_card.py           # Card individual de cada jogo
├── game_manager.py        # Gerenciamento de jogos (CRUD + JSON)
├── add_game_dialog.py     # Dialog de adicionar/editar jogo
├── image_cropper.py       # Editor de crop de imagens
├── settings_dialog.py     # Janela de configurações
├── settings_manager.py    # Gerenciamento de configurações
├── color_extractor.py     # Extração de cores dominantes do wallpaper
└── assets/
    └── gamehub.ico        # Ícone do app
```

---

## 💾 Onde ficam os dados?

Os dados são salvos automaticamente na pasta do usuário do Windows:

```
C:\Users\<nome>\AppData\Roaming\GameHub\
├── games.json        ← lista de jogos adicionados
├── settings.json     ← configurações e tema
└── crops\            ← imagens cortadas (ícones e banners)
```

> As imagens originais (wallpapers, banners) **ficam no local de origem** no seu PC — o programa apenas guarda o caminho delas.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| [Python 3.13](https://python.org) | Linguagem principal |
| [PyQt6](https://pypi.org/project/PyQt6/) | Interface gráfica (GUI) |
| [Pillow](https://pillow.readthedocs.io/) | Processamento de imagens (crop, extração de cores) |
| [PyInstaller](https://pyinstaller.org/) | Geração do executável |

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">Feito por <a href="https://github.com/ManoJooJ">ManoJooJ</a></p>
