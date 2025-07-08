# Basic PGN Cheat Detection

A small Flask application that inspects PGN games for signs of computer assistance.  It runs Stockfish on every position, measures how difficult each move was, looks at the time each player spent, and shows the results as simple charts.

---

## Features

* Stockfish 17.1 evaluation for every half-move
* Position-Complexity Score (PCS) that labels positions as trivial / balanced / critical / chaotic
* Engine-agreement percentages (best move, top-3)
* Opening-book check against the public Lichess database
* Timing analysis (average time, standard deviation, consistency)
* All charts rendered in the browser with Chart.js and no external services

---

## Quick start

1. Clone the repo and set up a virtual environment (optional but recommended):
```bash
$ git clone https://github.com/antvrobin/basic_pgn_cheat_detection
$ cd basic_pgn_cheat_detection
$ python -m venv venv
$ source venv/bin/activate   # on Windows: venv\Scripts\activate
$ pip install -r requirements.txt
```

2. Download a Stockfish binary that matches your operating system and either
   * place the executable in the project root, **or**
   * set the `STOCKFISH_PATH` environment variable.

3. Run the web app:
```bash
$ python app.py
```
Then open <http://localhost:5000>, choose a PGN with clock times, and click “Analyze Game”.

---

## Directory layout
```
├── analyzer/      # The analysis code (engine calls, complexity, metrics)
├── static/        # Front-end assets (JS, CSS)
├── templates/     # Jinja2 pages rendered by Flask
├── uploads/       # Temporary storage for uploaded PGN files
├── app.py         # Flask entry point
└── config.py      # Small helper with engine and API settings
```

---

## Configuration tips

* **Engine depth** – default is depth 12 for a good balance of speed and accuracy.
* **PCS thresholds** – tweak `ComplexityCalculator._categorise_pcs` if you want different ranges.
* **Lichess opening API** – rate-limit delays are set in `Config.API_TIMEOUT` and `EngineAnalyzer.opening_api_delay`.

---

## Common problems

| Problem | Likely cause / fix |
|---------|--------------------|
| *“Stockfish not found”* | Check `STOCKFISH_PATH` or put the binary next to `app.py`. |
| Grey charts / no data | The game did not have clock times or analysis crashed; look at the Flask console for tracebacks. |
| Very slow analysis | Lower `analysis_depth`, or disable PCS calculation. |

---

Released under the MIT licence.  Contributions and bug reports are always welcome.  Enjoy!
