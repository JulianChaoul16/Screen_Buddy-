import random
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
)

ASSETS = Path(__file__).parent / "assets"

# Use your own sprite pack (assets/luffy/<activity>/*.png) when it's there,
# otherwise the generated monkey in assets/<activity>/.
if (ASSETS / "luffy" / "walk").is_dir():
    ASSETS = ASSETS / "luffy"

# activity name -> (ms per frame, how long it lasts in ms (min, max), moves?)
ACTIVITIES = {
    "walk": (90, (4000, 9000), True),
    "idle": (250, (2000, 4000), False),
    "eat": (300, (3000, 5000), False),
    "sleep": (600, (5000, 9000), False),
    "dance": (120, (3000, 5000), False),
    "wave": (220, (1500, 2500), False),
    "stretch": (90, (1500, 2500), False),
}

# How often each activity gets picked after the current one finishes
WEIGHTS = {
    "walk": 5,
    "idle": 3,
    "eat": 2,
    "sleep": 1,
    "dance": 2,
    "wave": 1,
    "stretch": 1,
}


def load_frames(name):
    """Every PNG in assets/<name>/ in filename order."""
    folder = ASSETS / name
    files = sorted(folder.glob("*.png")) if folder.is_dir() else []
    return [QPixmap(str(f)) for f in files if f.stat().st_size > 0]


class DesktopPet(QLabel):
    def __init__(self):
        super().__init__()

        # Window appearance
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Load every activity's frames, plus mirrored copies for facing left
        mirror = QTransform().scale(-1, 1)
        self.frames = {}
        for name in ACTIVITIES:
            right = load_frames(name)
            if right:
                left = [f.transformed(mirror) for f in right]
                self.frames[name] = {1: right, -1: left}

        if "walk" not in self.frames:
            raise SystemExit("No frames in assets/walk - run make_sprites.py first")

        first = self.frames["walk"][1][0]
        self.resize(first.size())

        # Screen dimensions
        self.screen_area = QApplication.primaryScreen().availableGeometry()

        # Starting position
        self.x_pos = self.screen_area.left()
        self.y_pos = self.screen_area.bottom() - self.height() + 1
        self.move(self.x_pos, self.y_pos)

        # Movement speed in pixels per update
        self.speed = 3

        # Direction: 1 = right, -1 = left
        self.direction = 1

        # Paused by a left click?
        self.is_paused = False

        # Movement timer
        self.update_interval = 30
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_position)

        # Animation timer (flips through frames)
        self.frame_index = 0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.next_frame)

        # Behavior timer (decides when to switch activity)
        self.behavior_timer = QTimer(self)
        self.behavior_timer.setSingleShot(True)
        self.behavior_timer.timeout.connect(self.change_behavior)

        self.state = None
        self.set_state("walk")

    # ------------------------------------------------------------ behavior

    def set_state(self, name):
        if name not in self.frames:
            name = "idle" if "idle" in self.frames else "walk"

        self.state = name
        self.frame_index = 0
        frame_ms, (lo, hi), moves = ACTIVITIES[name]

        self.anim_timer.start(frame_ms)
        self.show_frame()

        if moves and not self.is_paused:
            self.move_timer.start(self.update_interval)
        else:
            self.move_timer.stop()

        self.behavior_timer.start(random.randint(lo, hi))

    
    def change_behavior(self):
        # Pick a different activity, weighted so walking comes up most
        options = [n for n in self.frames if n != self.state]
        weights = [WEIGHTS.get(n, 1) for n in options]
        next_state = random.choices(options, weights)[0]

        if next_state == "walk":
            # Randomly choose a direction
            self.direction = random.choice([-1, 1])

        # Starts the animation/movement and schedules the next change
        self.set_state(next_state)


    # ------------------------------------------------------------ animation

    def show_frame(self):
        frames = self.frames[self.state][self.direction]
        self.setPixmap(frames[self.frame_index % len(frames)])

    def next_frame(self):
        self.frame_index += 1
        self.show_frame()

    # ------------------------------------------------------------ movement

    def update_position(self):
        # Move horizontally
        self.x_pos += self.speed * self.direction

        # Reverse direction at screen boundaries
        if self.x_pos + self.width() >= self.screen_area.right() + 1:
            self.x_pos = self.screen_area.right() - self.width() + 1
            self.direction = -1
            self.show_frame()

        elif self.x_pos <= self.screen_area.left():
            self.x_pos = self.screen_area.left()
            self.direction = 1
            self.show_frame()

        self.move(self.x_pos, self.y_pos)

    # ------------------------------------------------------------ input

    def mousePressEvent(self, event):
        # Left click pauses / resumes everything
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_paused:
                self.is_paused = False
                self.set_state(self.state)
            else:
                self.is_paused = True
                self.move_timer.stop()
                self.anim_timer.stop()
                self.behavior_timer.stop()

    def contextMenuEvent(self, event):
        # Right click: pick an activity or exit
        menu = QMenu(self)

        actions = {}
        for name in self.frames:
            actions[menu.addAction(name.capitalize())] = name
        menu.addSeparator()
        exit_action = menu.addAction("Exit")

        selected_action = menu.exec(event.globalPos())

        if selected_action == exit_action:
            QApplication.quit()
        elif selected_action in actions:
            self.is_paused = False
            self.set_state(actions[selected_action])


app = QApplication(sys.argv)

pet = DesktopPet()
pet.show()

sys.exit(app.exec())
