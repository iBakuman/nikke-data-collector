from PySide6.QtCore import Qt



if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QWidget
    import sys

    app = QApplication(sys.argv)

    # 创建窗口
    window = QWidget()
    window.setWindowTitle("控制窗口位置示例")
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # 取消标题栏和边框
    window.setGeometry(1002, 1600, 400, 200)
    # window.resize(400, 300)  # 设置窗口大小
    #
    # window.move(QPoint(100, 160))

    window.show()

    sys.exit(app.exec())

