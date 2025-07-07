# Chess Cheat Detection Pro

*Analyze PGN games in seconds and visualise positional complexity, engine match rates, timing patterns & more.*

---

## ✨ Key Features

• **Positional Complexity Score (PCS)** – Maia-inspired metric that classifies each position as *Trivial, Balanced, Critical* or *Chaotic*.<br>
• **Engine Agreement** – Best-move, Top-3 and Top-5 match rates calculated with Stockfish.<br>
• **Accuracy & CP-Loss Charts** – Move-by-move accuracy timeline and scatter plots.
• **Timing Patterns** – Correlate thinking time with PCS to spot suspicious consistency.
• **Intuitive Dashboards** – Dark-mode, responsive UI powered by Chart.js.
• **One-click Upload** – Drag & drop any `.pgn`, get instant results.

---

## 🚀 Quick Start

### 1 · Clone & install
```bash
# clone your fork once the remote exists
git clone https://github.com/<YOU>/pgn_cheat.git
cd pgn_cheat

# create Python env (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# install deps
pip install -r requirements.txt  # ⇢ created automatically by venv
```

### 2 · Add Stockfish
Download a recent Stockfish binary and place the executable in the project root **or** adjust `config.py → STOCKFISH_PATH`.

### 3 · Run the app
```bash
python app.py
```
Open `http://localhost:5000` in your browser → upload a PGN → explore the analysis.

---

## 🧐 Folder Structure
```
pgn_cheat/
├── analyzer/            # backend analysis engine (complexity, engine, metrics …)
├── static/              # JS, CSS, icons
├── templates/           # Flask Jinja2 pages
├── uploads/             # user-uploaded PGNs (auto-created)
├── app.py               # Flask entry point
└── README.md            # you’re here
```

---

## ⚙️ Configuration
Edit `config.py` to tweak:
- Engine depth / hash size
- PCS thresholds
- Lichess Opening Explorer API delay

---

## 🩺 Troubleshooting
| Issue | Fix |
|-------|------|
| *Stockfish not found* | Verify `config.py.STOCKFISH_PATH` or place `stockfish.exe` in root |
| Blank graphs | Check browser console for JS errors, ensure analysis finished in backend |
| Large PGNs slow | Increase `move_time_limit` or lower `analysis_depth` in `config.py` |

---

## 🤝 Contributing
Pull requests welcome! Please open an issue first to discuss major changes.

1. Fork → create feature branch → commit ➜ open PR.
2. Follow PEP-8; run `black .`.

---

## 📄 License
MIT – see `LICENSE` for details.
