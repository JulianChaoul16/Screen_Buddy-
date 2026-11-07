
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel

# Create our application
app = QApplication(sys.argv)

# Create our pet
pet = QLabel("🐒")

# Remove window borders and keep it on top
pet.setWindowFlags(
    Qt.WindowType.FramelessWindowHint
    | Qt.WindowType.WindowStaysOnTopHint
    | Qt.WindowType.Tool
)

# Make the background transparent
pet.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

# Set the character's font and size
pet.setFont(QFont("Segoe UI Emoji", 80))
pet.resize(150, 150)

# Find the usable screen area
screen = app.primaryScreen().availableGeometry()

# Position the character at the bottom-right
x = screen.left() - pet.width() + 1
y = screen.bottom() - pet.height() + 1

pet.move(x, y)

# Display the character
pet.show()

# Start the application event loop
sys.exit(app.exec())
