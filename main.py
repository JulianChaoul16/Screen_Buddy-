
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
)


class DesktopPet(QLabel):
    def __init__(self):
        super().__init__("🐒")

        # Window appearance
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setFont(QFont("Segoe UI Emoji", 80))
        self.resize(150, 150)

        # Screen dimensions
        self.screen_area = (
            QApplication.primaryScreen().availableGeometry()
        )

        # Starting position
        self.x_pos = self.screen_area.left()
        self.y_pos = self.screen_area.bottom() - self.height() + 1

        self.move(self.x_pos, self.y_pos)

        # Movement speed in pixels per update
        self.speed = 3

        # Direction: 1 = right, -1 = left
        self.direction = 1

        # iS THIS GUY moving 
        self.is_moving = True


        # Create a timer to update movement
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(30)
        self.update_interval = 30

        self.state = "WALKING"

        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self.change_behavior)
        self.behavior_timer.start(3000)

    def update_position(self):
        # Move horizontally
        self.x_pos += self.speed * self.direction

        # Reverse direction at screen boundaries
        if self.x_pos + self.width() >= self.screen_area.right() + 1:
            self.x_pos = self.screen_area.right() - self.width() + 1
            self.direction = -1

        elif self.x_pos <= self.screen_area.left():
            self.x_pos = self.screen_area.left()
            self.direction = 1

        self.move(self.x_pos, self.y_pos)

    def stop_movement(self):

        self.timer.stop()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_moving:
                self.stop_movement()
                self.is_moving = False
            else: 
                self.timer.start(self.update_interval)
                self.is_moving = True

    
    def change_behavior(self):
        if self.state == "WALKING":
            self.state = "IDLE"
            self.stop_movement()

        elif self.state == "IDLE":
            self.state = "WALKING"
            self.timer.start(30)

        


        
        

    def contextMenuEvent(self, event):
        # Show a menu when right-clicked
        menu = QMenu(self)

        exit_action = menu.addAction("Exit")
        selected_action = menu.exec(event.globalPos())

        if selected_action == exit_action:
            QApplication.quit()


app = QApplication(sys.argv)

pet = DesktopPet()
pet.show()

sys.exit(app.exec())
