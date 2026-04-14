from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from ui.game_scene import GameView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YINSH AI Project")
        self.resize(1024, 768) # A good default desktop size

        # 1. The Stacked Widget (Our screen switcher)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 2. Create the two screens
        self.menu_screen = self.create_main_menu()
        self.game_screen = GameView()

        # 3. Add them to the stack
        self.stack.addWidget(self.menu_screen) # Index 0
        self.stack.addWidget(self.game_screen) # Index 1

    def create_main_menu(self):
        # A simple widget to hold our menu layout
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("YINSH")
        title.setStyleSheet("font-size: 64px; font-weight: bold; margin-bottom: 50px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Button 1: Play vs AI (Placeholder)
        btn_ai = QPushButton("Play vs AI (Coming Soon)")
        btn_ai.setFixedSize(300, 60)
        btn_ai.setStyleSheet("font-size: 18px;")
        btn_ai.clicked.connect(self.on_play_ai_clicked)

        # Button 2: 2 Player Local
        btn_2p = QPushButton("2 Player Mode (Local)")
        btn_2p.setFixedSize(300, 60)
        btn_2p.setStyleSheet("font-size: 18px;")
        btn_2p.clicked.connect(self.start_two_player_game)

        # Add everything to the layout
        layout.addWidget(title)
        layout.addWidget(btn_ai, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_2p, alignment=Qt.AlignmentFlag.AlignCenter)

        widget.setLayout(layout)
        return widget

    # --- Button Actions ---
    def on_play_ai_clicked(self):
        print("AI mode clicked! (Does nothing yet)")

    def start_two_player_game(self):
        # Switch the deck of cards to show the game screen (Index 1)
        self.stack.setCurrentIndex(1)
