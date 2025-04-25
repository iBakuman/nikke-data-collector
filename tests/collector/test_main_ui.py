from PySide6.QtWidgets import QMainWindow, QApplication

from ui.main import Ui_MainWindow


class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.knockoutOptions.setVisible(False)
        self.ui.championshipOptons.setVisible(False)

def test_main_ui():
    app = QApplication([])
    win =MyMainWindow()
    win.show()
    app.exec()