import os
import random
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QTransform
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
    QSystemTrayIcon,
)

ASSETS = Path(__file__).parent / "assets"

# Shortcut in the Windows Startup folder = "Start with Windows"
STARTUP_LINK = (
    Path(os.environ["APPDATA"])
    / "Microsoft/Windows/Start Menu/Programs/Startup/Desktop Luffy.lnk"
)


def set_autostart(on):
    if not on:
        STARTUP_LINK.unlink(missing_ok=True)
        return
    # pythonw.exe = no console window
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    script = Path(__file__).resolve()
    ps = (
        f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{STARTUP_LINK}');"
        f"$s.TargetPath = '{pythonw}';"
        f"$s.Arguments = '\"{script}\"';"
        f"$s.WorkingDirectory = '{script.parent}';"
        "$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

# Use your own sprite pack (assets/luffy/<activity>/*.png) when it's there,
# otherwise the generated monkey in assets/<activity>/.
if (ASSETS / "luffy" / "walk").is_dir():
    ASSETS = ASSETS / "luffy"

# activity name -> (ms per frame, how long it lasts in ms (min, max), moves?)
ACTIVITIES = {
    "walk": (90, (4000, 9000), True),
    "idle": (250, (2000, 4000), False),
    "eat": (300, (3000, 5000), False),
    "sleep": (1000, (30000, 60000), False),  # slow breathing, long naps
    "dance": (120, (3000, 5000), False),
    "wave": (220, (1500, 2500), False),
    "stretch": (90, (1500, 2500), False),
    "carry": (120, (0, 0), False),  # while dragged/falling (no timeout)
    "land": (90, (900, 900), False),  # plays once after a drop
}

# How often each activity gets picked after the current one finishes
# (0 = never picked at random; only triggered by dragging)
WEIGHTS = {
    "walk": 3,
    "idle": 3,
    "eat": 2,
    "sleep": 18,  # ~60% of picks
    "dance": 2,
    "wave": 1,
    "stretch": 1,
    "carry": 0,
    "land": 0,
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

        # Dragging / falling
        self.ground_y = self.y_pos
        self.press_pos = None  # where the mouse went down (global)
        self.grab_offset = None  # set once a drag actually starts
        self.fall_speed = 0
        self.fall_timer = QTimer(self)
        self.fall_timer.timeout.connect(self.fall_step)

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
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.press_pos is None:
            return
        pos = event.globalPosition().toPoint()

        # Start a drag once the mouse has moved a few pixels
        if self.grab_offset is None:
            if (pos - self.press_pos).manhattanLength() < 5:
                return
            self.grab_offset = self.press_pos - self.pos()
            self.fall_timer.stop()
            self.is_paused = False
            self.set_state("carry")
            self.behavior_timer.stop()

        self.x_pos, self.y_pos = (pos - self.grab_offset).toTuple()
        self.move(self.x_pos, self.y_pos)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        dragged = self.grab_offset is not None
        self.press_pos = self.grab_offset = None

        if dragged:
            # Let go: fall to the ground
            self.fall_speed = 0
            self.fall_timer.start(self.update_interval)
        else:
            self.toggle_pause()

    def fall_step(self):
        self.fall_speed += 2  # gravity
        self.y_pos = min(self.y_pos + self.fall_speed, self.ground_y)
        self.move(self.x_pos, self.y_pos)
        if self.y_pos >= self.ground_y:
            self.fall_timer.stop()
            self.set_state("land")

    def toggle_pause(self):
        # Left click (without dragging) pauses / resumes everything
        if self.is_paused:
            self.is_paused = False
            self.set_state(self.state)
        else:
            self.is_paused = True
            self.move_timer.stop()
            self.anim_timer.stop()
            self.behavior_timer.stop()

    def toggle_visible(self):
        self.setVisible(not self.isVisible())

    def pick(self, name):
        self.is_paused = False
        self.set_state(name)

    def fill_menu(self, menu):
        """One menu, used for both right-clicking Luffy and the tray icon."""
        menu.clear()
        for name in self.frames:
            if WEIGHTS.get(name, 1):  # hide drag-only states
                menu.addAction(name.capitalize(), lambda n=name: self.pick(n))
        menu.addSeparator()
        menu.addAction("Resume" if self.is_paused else "Pause", self.toggle_pause)
        menu.addAction("Hide" if self.isVisible() else "Show", self.toggle_visible)
        autostart = menu.addAction(
            "Start with Windows", lambda: set_autostart(not STARTUP_LINK.exists())
        )
        autostart.setCheckable(True)
        autostart.setChecked(STARTUP_LINK.exists())
        menu.addSeparator()
        menu.addAction("Quit", QApplication.quit)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        self.fill_menu(menu)
        menu.exec(event.globalPos())


app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)  # hiding Luffy shouldn't quit the app

pet = DesktopPet()
pet.show()

# System tray: left-click shows/hides him, right-click opens the controls
tray_icon = pet.frames.get("idle", pet.frames["walk"])[1][0]
tray = QSystemTrayIcon(QIcon(tray_icon), app)
tray.setToolTip("Desktop Luffy")
tray_menu = QMenu()
pet.fill_menu(tray_menu)
tray_menu.aboutToShow.connect(lambda: pet.fill_menu(tray_menu))
tray.setContextMenu(tray_menu)
tray.activated.connect(
    lambda reason: pet.toggle_visible()
    if reason == QSystemTrayIcon.ActivationReason.Trigger
    else None
)
tray.show()

sys.exit(app.exec())
