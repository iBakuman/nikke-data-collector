from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QCursor, QPixmap, QColor
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout

# 可配置的放大倍数和矩形大小 (configurable magnification factor and region size)
REGION_SIZE = 100       # 默认放大区域的矩形大小 (default sampled square region size in pixels)
MAGNIFICATION = 2       # 默认放大倍率 (default magnification factor)

class Magnifier(QWidget):
    def __init__(self):
        super().__init__()
        # 主窗口逻辑: 设置窗口属性 (Main window logic: set window properties)
        self.setWindowTitle("Magnifier")  # 可以根据需要设置标题 (optional window title)
        # 窗口总是在最前，无边框，工具窗口类型(不在任务栏) (Always on top, frameless, tool window so it doesn't appear in taskbar)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # 根据需要使窗口对鼠标事件透明，这样鼠标可与窗口下方的应用交互 (Make window transparent to mouse events if desired)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # 初始化放大区域大小和倍率 (Initialize region size and magnification)
        self.region_size = REGION_SIZE
        self.magnification = MAGNIFICATION
        # 计算放大显示区域的尺寸 (Calculate magnified display size)
        self.display_size = self.region_size * self.magnification

        # 创建显示放大图像的标签 (Create label for magnified image)
        self.image_label = QLabel(self)
        # 固定标签大小为放大后的尺寸 (Fix label size to the magnified image size)
        self.image_label.setFixedSize(self.display_size, self.display_size)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 创建颜色块和RGB文字标签 (Create color patch and RGB text labels)
        self.color_patch = QLabel(self)
        self.color_patch.setFixedSize(20, 20)
        # 设置初始颜色块样式 (initial color patch style)
        self.color_patch.setStyleSheet("background-color: black; border: 1px solid #333;")
        self.color_text = QLabel(self)
        self.color_text.setText("R:0 G:0 B:0")

        # 布局设置 (Layout setup)
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(5, 0, 5, 5)   # 底部区域内边距 (margins around color info)
        info_layout.setSpacing(5)
        info_layout.addWidget(self.color_patch)
        info_layout.addWidget(self.color_text)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)   # 主窗口无内边距 (no margin around main layout)
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(info_layout)

        # 鼠标实时追踪: 使用计时器定时更新放大器内容 (Mouse tracking in real-time via QTimer)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateMagnifier)
        self.timer.start(30)  # 每 30 毫秒更新一次 (update every 30 ms)

    def updateMagnifier(self):
        # 获取当前鼠标全局坐标 (Get current global mouse cursor position)
        cursor_pos = QCursor.pos()
        # 找到光标所在的屏幕 (Find which screen the cursor is on)
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        screen_geom = screen.geometry()

        # 安全放置窗口位置逻辑 (Safe window positioning to avoid covering cursor or going off-screen)
        win_w = self.width()
        win_h = self.height()
        # 默认将窗口放在鼠标右下方 (default position: bottom-right of cursor)
        margin = (self.region_size + 1) // 2   # 偏移距离，确保不遮挡放大区域 (offset to avoid overlapping captured region)
        pos_x = cursor_pos.x() + margin
        pos_y = cursor_pos.y() + margin
        # 如果超出屏幕右边缘，则移到左侧 (Adjust to left of cursor if hitting right edge)
        if pos_x + win_w > screen_geom.x() + screen_geom.width():
            pos_x = cursor_pos.x() - margin - win_w
        # 如果超出屏幕下边缘，则移到鼠标上方 (Adjust above cursor if hitting bottom edge)
        if pos_y + win_h > screen_geom.y() + screen_geom.height():
            pos_y = cursor_pos.y() - margin - win_h
        # 再次确保窗口未越出屏幕边界 (Clamp position within screen bounds)
        if pos_x < screen_geom.x():
            pos_x = screen_geom.x()
        if pos_y < screen_geom.y():
            pos_y = screen_geom.y()
        # 移动窗口到计算的位置 (Move the window to the new position)
        self.move(pos_x, pos_y)

        # 屏幕截图采样: 捕获鼠标周围区域并放大 (Screen capture of region around cursor and magnify it)
        region_w = self.region_size
        region_h = self.region_size
        # 计算要截取的区域的左上角坐标 (Calculate top-left of capture region)
        reg_x = cursor_pos.x() - region_w // 2
        reg_y = cursor_pos.y() - region_h // 2
        # 确保截取区域在屏幕内 (Clamp capture region within screen bounds)
        if reg_x < screen_geom.x():
            reg_x = screen_geom.x()
        if reg_x + region_w > screen_geom.x() + screen_geom.width():
            reg_x = screen_geom.x() + screen_geom.width() - region_w
        if reg_y < screen_geom.y():
            reg_y = screen_geom.y()
        if reg_y + region_h > screen_geom.y() + screen_geom.height():
            reg_y = screen_geom.y() + screen_geom.height() - region_h

        # 抓取屏幕指定区域 (Grab the specified screen region as an image)
        screenshot = screen.grabWindow(0, reg_x, reg_y, region_w, region_h).toImage()
        # 提取鼠标所在像素的颜色 (Get the color of the pixel under the cursor)
        local_x = cursor_pos.x() - reg_x
        local_y = cursor_pos.y() - reg_y
        pixel_color = QColor(screenshot.pixel(int(local_x), int(local_y)))
        # 更新颜色块和RGB文本 (Update color patch and RGB text)
        self.color_patch.setStyleSheet(f"background-color: {pixel_color.name()}; border: 1px solid #000;")
        self.color_text.setText(f"R:{pixel_color.red()} G:{pixel_color.green()} B:{pixel_color.blue()}")

        # 将截图放大指定倍数 (Scale the screenshot by the magnification factor)
        if self.magnification != 1:
            scaled_img = screenshot.scaled(region_w * self.magnification,
                                           region_h * self.magnification,
                                           Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
            display_pixmap = QPixmap.fromImage(scaled_img)
        else:
            display_pixmap = QPixmap.fromImage(screenshot)
        # 将放大后的图像显示在标签上 (Display the magnified image in the label)
        self.image_label.setPixmap(display_pixmap)

        # 根据需要调整窗口大小 (Adjust window size if needed)
        # 一般情况下窗口大小固定，由布局和控件决定 (Usually not needed if layout is fixed)
        # self.adjustSize()

if __name__ == "__main__":
    app = QApplication([])
    magnifier = Magnifier()
    magnifier.show()
    app.exec()
