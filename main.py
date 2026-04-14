import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create the window and show it
    window = MainWindow()
    window.show()

    # Run the application loop
    sys.exit(app.exec())