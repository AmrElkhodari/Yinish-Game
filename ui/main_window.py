import socket
import random
import string
import json
import pyrebase  # <--- NEW: Client Library
from PySide6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
                               QPushButton, QLabel, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.game_scene import GameView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YINSH AI Project")
        self.resize(1024, 768)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")

        # --- NEW: CLIENT FIREBASE INIT ---
        self.firebase_ready = False
        self.db = None
        try:
            with open('config.json', 'r') as config_file:
                config_data = json.load(config_file)

            if not config_data.get('apiKey') or config_data.get('apiKey') == "YOUR_API_KEY":
                raise ValueError("Public API Key is missing in config.json")

            self.firebase = pyrebase.initialize_app(config_data)
            self.db = self.firebase.database()
            self.firebase_ready = True
            print("✅ Pyrebase Client Connected Successfully!")

        except FileNotFoundError:
            print("❌ Firebase Failed: Could not find config.json")
        except Exception as e:
            print("❌ Firebase Failed:", e)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.menu_screen = self.create_main_menu()
        self.offline_screen = self.create_offline_screen()
        self.online_menu_screen = self.create_online_menu()

        self.stack.addWidget(self.menu_screen)
        self.stack.addWidget(self.offline_screen)
        self.stack.addWidget(self.online_menu_screen)

    def create_main_menu(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("YINSH")
        title.setFont(QFont("Segoe UI", 72, QFont.Weight.Black))
        title.setStyleSheet("color: #FFD54F; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_style = "QPushButton { background-color: #29B6F6; color: white; border-radius: 10px; padding: 15px; font-size: 18px; font-weight: bold; } QPushButton:hover { background-color: #039BE5; }"

        btn_local = QPushButton("Play Local (2 Player)")
        btn_local.setFixedSize(350, 60)
        btn_local.setStyleSheet(btn_style)
        btn_local.clicked.connect(self.start_local_game)

        btn_online = QPushButton("Play Online (Multiplayer)")
        btn_online.setFixedSize(350, 60)
        btn_online.setStyleSheet(btn_style.replace("#29B6F6", "#EF5350").replace("#039BE5", "#E53935"))
        btn_online.clicked.connect(self.check_online_mode)

        layout.addWidget(title)
        layout.addWidget(btn_local, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(15)
        layout.addWidget(btn_online, alignment=Qt.AlignmentFlag.AlignCenter)
        widget.setLayout(layout)
        return widget

    def create_offline_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("No Internet or Database Missing")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_back = QPushButton("Return to Menu")
        btn_back.setFixedSize(250, 50)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        layout.addWidget(title)
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)
        widget.setLayout(layout)
        return widget

    def create_online_menu(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Online Multiplayer")
        title.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your Name...")
        self.name_input.setFixedSize(350, 50)
        self.name_input.setStyleSheet(
            "background-color: #333; color: white; border-radius: 8px; padding: 10px; font-size: 16px;")

        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("Enter Room Code to Join...")
        self.room_input.setFixedSize(350, 50)
        self.room_input.setStyleSheet(
            "background-color: #333; color: white; border-radius: 8px; padding: 10px; font-size: 16px;")

        btn_style = "QPushButton { background-color: #29B6F6; color: white; border-radius: 8px; padding: 10px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #039BE5; }"

        btn_create = QPushButton("Create New Room")
        btn_create.setFixedSize(350, 50)
        btn_create.setStyleSheet(btn_style)
        btn_create.clicked.connect(self.create_online_room)

        btn_join = QPushButton("Join Room")
        btn_join.setFixedSize(350, 50)
        btn_join.setStyleSheet(btn_style.replace("#29B6F6", "#66BB6A").replace("#039BE5", "#43A047"))
        btn_join.clicked.connect(self.join_online_room)

        btn_back = QPushButton("Back")
        btn_back.setFixedSize(350, 40)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(self.name_input, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(btn_create, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(30)
        layout.addWidget(self.room_input, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_join, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)
        widget.setLayout(layout)
        return widget

    def check_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    def check_online_mode(self):
        if self.check_internet() and self.firebase_ready:
            self.stack.setCurrentIndex(2)
        else:
            self.stack.setCurrentIndex(1)

    def start_local_game(self):
        self.launch_game_board(p1_name="Player 1", p2_name="Player 2", db=None, room_code=None, local_color=None)

    def create_online_room(self):
        player_name = self.name_input.text().strip()
        if not player_name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name first!")
            return

        room_code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

        # --- NEW: Pyrebase Push Logic ---
        self.db.child("rooms").child(room_code).set({
            'creator': player_name,
            'joiner': 'Waiting...',
            'last_mover': 'none'
        })

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Room Created!")
        msg_box.setText(f"Your Room Code is:  {room_code}\n\nShare this with your opponent!")

        import PySide6.QtWidgets as QtWidgets
        copy_btn = msg_box.addButton("Copy Code", QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton(QMessageBox.StandardButton.Ok)
        msg_box.exec()

        if msg_box.clickedButton() == copy_btn:
            import PySide6.QtGui as QtGui
            QtGui.QGuiApplication.clipboard().setText(room_code)

        # Pass the self.db instance and room code instead of an admin ref
        self.launch_game_board(p1_name=player_name, p2_name="Waiting...", db=self.db, room_code=room_code,
                               local_color='red')

    def join_online_room(self):
        player_name = self.name_input.text().strip()
        room_code = self.room_input.text().strip().upper()

        if not player_name or not room_code:
            QMessageBox.warning(self, "Missing Info", "Please enter your name and a room code!")
            return

        # --- NEW: Pyrebase Read Logic ---
        room_data = self.db.child("rooms").child(room_code).get().val()

        if not room_data:
            QMessageBox.critical(self, "Error", "Room not found! Check the code.")
            return

        self.db.child("rooms").child(room_code).update({'joiner': player_name})

        creator_name = room_data.get('creator', 'Opponent')
        self.launch_game_board(p1_name=creator_name, p2_name=player_name, db=self.db, room_code=room_code,
                               local_color='blue')

    def launch_game_board(self, p1_name, p2_name, db, room_code, local_color):
        self.game_screen = GameView(p1_name, p2_name, db, room_code, local_color)

        if self.stack.count() > 3:
            old_game = self.stack.widget(3)
            self.stack.removeWidget(old_game)
            old_game.deleteLater()

        self.stack.addWidget(self.game_screen)
        self.stack.setCurrentIndex(3)