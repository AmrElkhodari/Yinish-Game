# YINSH - Python Desktop Board Game

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)
![Firebase](https://img.shields.io/badge/Database-Firebase-FFCA28.svg)

A fully functional, cross-platform desktop implementation of the abstract strategy board game **YINSH**. 

This project features a custom-built rule engine, an interactive hexagonal GUI, real-time online multiplayer over Firebase, and a Single Player mode against an AI opponent powered by the **Minimax algorithm with Alpha-Beta Pruning**.

## ✨ Features

* **Complete Rule Engine:** Enforces all official YINSH rules, including valid line sliding, marker flipping, and sequence detection (5-in-a-row).
* **AI Opponent:** Play against an automated agent that calculates multi-turn strategies using a custom game tree and heuristic evaluation.
* **Real-time Multiplayer:** Host and join online rooms via a 5-digit code. Game state is instantly synced using Firebase Client REST APIs (Pyrebase).
* **Time Travel System:** Use the `Left` and `Right` arrow keys to step backward and forward through the history of the match to review past moves.
* **Smooth UI & Audio:** Fully animated piece movements, valid move indicators, and integrated sound effects built on the PySide6 Graphics View Framework.

## 🧠 AI Architecture: Minimax & Alpha-Beta Pruning

The Single Player mode uses a dedicated background thread to run a game-tree search algorithm without freezing the UI.

* **Minimax Search:** The AI simulates future board states by assuming the human player will always make the best possible counter-move. It explores multiple moves ahead to find the path that maximizes its own score while minimizing the opponent's.
* **Alpha-Beta Pruning:** To optimize the massive branching factor of the YINSH hexagonal grid, the algorithm tracks the worst-case and best-case scenarios (Alpha and Beta). If it detects a branch that the opponent will obviously prevent, it instantly "prunes" (cuts off) the calculation, saving millions of unnecessary deep-copies and keeping the AI fast.
* **Heuristic Evaluation:** Since the AI cannot calculate to the end of the game on every turn, it evaluates board states using a custom heuristic function. It scores boards based on:
  1. Rings removed (Win condition - Infinite weight)
  2. Number of connected markers (Immediate threats)
  3. Distance to the center of the board (Positional mobility)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/YINSH-Game.git](https://github.com/YOUR_USERNAME/YINSH-Game.git)
cd YINSH-Game
```

### 2. Install Dependencies
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```
*(Requires PySide6 and Pyrebase4)*

### 3. Firebase Configuration (For Multiplayer)
To keep databases secure, this project uses a "Bring Your Own Database" architecture. To enable online multiplayer:
1. Create a free project on [Firebase](https://firebase.google.com/).
2. Create a Realtime Database and set the security rules to allow reading/writing to the `/rooms` node.
3. Locate your Web App Client Configuration block.
4. Rename `config.example.json` to `config.json` and paste your public keys inside.

*(Note: Local 2-Player and AI modes work perfectly without Firebase configuration).*

## 🎮 How to Play

Run the application from your terminal:
```bash
python main.py
```

* **Play vs AI:** Launches a local game where Player 2 is controlled by the Minimax algorithm.
* **Play Local:** Hot-seat multiplayer for two players sharing the same mouse and screen.
* **Play Online:** Enter your name to generate a 5-letter Room Code. Share the code with a friend so they can join your live game.

## 📁 Repository Structure
* `/core`: Contains the pure Python mathematical logic, the `YinshEngine` state machine, and the `YinshAI` algorithm.
* `/ui`: Contains the PySide6 visual components, animations, multithreading logic, and window managers.
* `/sounds`: `.mp3` and `.wav` audio assets triggered by game events.

---
*Developed as a Computer Science AI & Software Engineering Project.*