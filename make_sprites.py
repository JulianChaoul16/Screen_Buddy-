"""Generate the pet's animation frames into assets/<activity>/frame_XX.png.

Run once (or again after tweaking):  python make_sprites.py

Everything is drawn with QPainter so no extra packages are needed.
Each activity gets its own folder; main.py plays every PNG in a folder
in name order. Drop your own frames (or a <activity>.gif) into assets/
to replace any of these.
"""

import math
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
)

SIZE = 160
ASSETS = Path(__file__).parent / "assets"

FUR = QColor("#7a4a26")
FUR_DARK = QColor("#5a3418")
FACE = QColor("#f2c99a")
STRAW = QColor("#f4cf4a")
STRAW_DARK = QColor("#c99a22")
BAND = QColor("#d6322e")
VEST = QColor("#d6322e")
SHORTS = QColor("#2f63b8")
OUTLINE = QColor("#2b1a0e")
MEAT = QColor("#a5502a")
BONE = QColor("#f5efe2")


def pen(width=3, color=OUTLINE):
    p = QPen(color, width)
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


def limb(p, start, angle_deg, length, color=FUR, width=11):
    """Draw an arm/leg as a thick rounded line with an outline; return the tip."""
    a = math.radians(angle_deg)
    end = QPointF(start.x() + math.cos(a) * length, start.y() + math.sin(a) * length)
    p.setPen(pen(width + 5))
    p.drawLine(start, end)
    p.setPen(pen(width, color))
    p.drawLine(start, end)
    return end


def hand(p, at, r=6):
    p.setPen(pen(2.5))
    p.setBrush(FACE)
    p.drawEllipse(at, r, r)


def draw_meat(p, at, bitten=0):
    p.save()
    p.translate(at)
    p.rotate(-35)
    p.setPen(pen(2.5))
    p.setBrush(BONE)
    p.drawRoundedRect(QRectF(-3, -2, 26, 6), 3, 3)
    p.drawEllipse(QPointF(24, -2), 4, 4)
    p.drawEllipse(QPointF(24, 4), 4, 4)
    p.setBrush(MEAT)
    path = QPainterPath()
    path.addEllipse(QRectF(-26, -13, 30, 26))
    if bitten:
        bite = QPainterPath()
        for i in range(bitten):
            bite.addEllipse(QPointF(-25 + i * 2, -9 + i * 7), 6, 6)
        path = path.subtracted(bite)
    p.drawPath(path)
    p.restore()


def draw_monkey(
    p,
    bob=0.0,
    legs=(100, 80),
    arm_l=120,
    arm_r=60,
    arm_len=24,
    eyes="open",
    mouth="smile",
    hat_tilt=0.0,
    lean=0.0,
    lying=False,
):
    """Draw the pet facing right. Angles in degrees, 0 = right, 90 = down."""
    p.save()
    cx, base = SIZE / 2, SIZE - 14
    if lying:
        p.translate(cx + 4, SIZE / 2 + 34)
        p.rotate(84)
        p.scale(0.82, 0.82)
        p.translate(-cx, -SIZE / 2 - 10)
    p.translate(0, bob)
    p.translate(cx, base)
    p.rotate(lean)
    p.translate(-cx, -base)

    hip = QPointF(cx, base - 30)
    shoulder_y = base - 56

    # tail
    p.setBrush(Qt.BrushStyle.NoBrush)
    tail = QPainterPath(QPointF(cx - 14, base - 34))
    tail.cubicTo(cx - 44, base - 30, cx - 48, base - 70, cx - 30, base - 70)
    tail.cubicTo(cx - 20, base - 70, cx - 22, base - 58, cx - 30, base - 60)
    p.setPen(pen(10))
    p.drawPath(tail)
    p.setPen(pen(6, FUR))
    p.drawPath(tail)

    # legs
    for ang in legs:
        foot = limb(p, QPointF(hip.x() + (6 if ang < 90 else -6), hip.y()), ang, 24)
        p.setPen(pen(2.5))
        p.setBrush(FACE)
        p.drawEllipse(QRectF(foot.x() - 6, foot.y() - 3, 13, 7))

    # back arm
    hand(p, limb(p, QPointF(cx - 14, shoulder_y + 4), arm_l, 24))

    # body: shorts + vest
    p.setPen(pen(3))
    p.setBrush(SHORTS)
    p.drawRoundedRect(QRectF(cx - 19, base - 42, 38, 16), 6, 6)
    p.setBrush(VEST)
    p.drawRoundedRect(QRectF(cx - 18, shoulder_y - 6, 36, 34), 12, 12)
    p.setBrush(FACE)
    belly = QPainterPath()
    belly.moveTo(cx - 5, shoulder_y - 5)
    belly.lineTo(cx + 5, shoulder_y - 5)
    belly.lineTo(cx + 3, shoulder_y + 26)
    belly.lineTo(cx - 3, shoulder_y + 26)
    belly.closeSubpath()
    p.drawPath(belly)
    p.setPen(pen(2))
    p.drawLine(QPointF(cx - 19, base - 34), QPointF(cx + 19, base - 34))

    # head
    head = QPointF(cx + 2, shoulder_y - 28)
    p.setPen(pen(3))
    p.setBrush(FUR)
    p.drawEllipse(QPointF(head.x() - 27, head.y() + 2), 10, 10)
    p.drawEllipse(QPointF(head.x() + 27, head.y() + 2), 10, 10)
    p.setBrush(FACE)
    p.drawEllipse(QPointF(head.x() - 27, head.y() + 2), 5, 5)
    p.drawEllipse(QPointF(head.x() + 27, head.y() + 2), 5, 5)
    p.setBrush(FUR)
    p.drawEllipse(head, 26, 24)
    p.setBrush(FACE)
    p.drawEllipse(QPointF(head.x() - 8, head.y() - 1), 11, 11)
    p.drawEllipse(QPointF(head.x() + 9, head.y() - 1), 11, 11)
    p.drawEllipse(QPointF(head.x() + 1, head.y() + 11), 17, 11)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(QRectF(head.x() - 14, head.y() - 2, 28, 12))

    # eyes
    for ex in (head.x() - 7, head.x() + 10):
        ey = head.y() - 1
        if eyes == "open":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(OUTLINE)
            p.drawEllipse(QPointF(ex, ey), 3.5, 4.5)
            p.setBrush(QColor("white"))
            p.drawEllipse(QPointF(ex + 1.2, ey - 1.6), 1.3, 1.3)
        elif eyes == "happy":
            p.setPen(pen(2.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(ex - 4, ey - 2, 8, 7), 0, 180 * 16)
        else:  # closed
            p.setPen(pen(2.5))
            p.drawLine(QPointF(ex - 4, ey + 1), QPointF(ex + 4, ey + 1))

    # nose + mouth
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(FUR_DARK)
    p.drawEllipse(QPointF(head.x() + 1, head.y() + 7), 2.2, 1.6)
    p.drawEllipse(QPointF(head.x() + 5, head.y() + 7), 2.2, 1.6)
    p.setPen(pen(2.5))
    mx, my = head.x() + 2, head.y() + 13
    if mouth == "smile":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(mx - 9, my - 6, 18, 10), 200 * 16, 140 * 16)
    elif mouth == "grin":
        p.setBrush(QColor("white"))
        grin = QPainterPath(QPointF(mx - 10, my - 2))
        grin.quadTo(mx, my + 12, mx + 10, my - 2)
        grin.closeSubpath()
        p.drawPath(grin)
    elif mouth == "open":
        p.setBrush(QColor("#8a1f1f"))
        p.drawEllipse(QPointF(mx, my + 1), 5, 6)
    elif mouth == "chew":
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(QPointF(mx - 5, my + 1), QPointF(mx + 5, my + 1))
        p.setBrush(FACE)
        p.drawEllipse(QPointF(mx + 11, my - 1), 5, 4)
    elif mouth == "o":
        p.setBrush(QColor("#8a1f1f"))
        p.drawEllipse(QPointF(mx, my + 1), 2.5, 2.5)

    # straw hat
    p.save()
    p.translate(head.x(), head.y() - 16)
    p.rotate(hat_tilt)
    p.setPen(pen(3))
    p.setBrush(STRAW)
    p.drawEllipse(QPointF(0, 2), 38, 8)
    crown = QPainterPath(QPointF(-20, 2))
    crown.cubicTo(-20, -24, 20, -24, 20, 2)
    crown.closeSubpath()
    p.drawPath(crown)
    p.setBrush(BAND)
    band = QPainterPath(QPointF(-20, 1))
    band.lineTo(-19, -6)
    band.quadTo(0, -9, 19, -6)
    band.lineTo(20, 1)
    band.quadTo(0, 4, -20, 1)
    p.drawPath(band)
    p.setPen(pen(1.5, STRAW_DARK))
    for i in range(-30, 31, 10):
        p.drawLine(QPointF(i, 0), QPointF(i * 1.05, 6))
    p.restore()

    # front arm (returns hand position for props)
    front = limb(p, QPointF(cx + 14, shoulder_y + 4), arm_r, arm_len)
    hand(p, front)
    p.restore()
    return front


def text(p, s, x, y, size=14, color=OUTLINE, bold=True):
    f = QFont("Segoe UI", size)
    f.setBold(bold)
    p.setFont(f)
    p.setPen(color)
    p.drawText(QPointF(x, y), s)


def note(p, x, y):
    text(p, "♪", x, y, 18, QColor("#3a3a8a"))


# ---------------------------------------------------------------- activities

def walk(i, n):
    t = i / n * 2 * math.pi
    s = math.sin(t)
    return dict(
        bob=-abs(s) * 4,
        legs=(90 + s * 30, 90 - s * 30),
        arm_l=100 - s * 35,
        arm_r=80 + s * 35,
        mouth="smile",
    )


def idle(i, n):
    return dict(
        bob=math.sin(i / n * 2 * math.pi) * 1.2,
        legs=(100, 80),
        arm_l=105,
        arm_r=75,
        eyes="closed" if i == n - 2 else "open",
    )


def eat(i, n, p=None):
    up = i % 2 == 0
    kw = dict(
        legs=(100, 80),
        arm_l=105,
        arm_r=-95 if up else -60,
        arm_len=22,
        mouth="open" if up else "chew",
        eyes="happy" if not up else "open",
    )
    return kw


def sleep(i, n):
    return dict(
        lying=True,
        legs=(95, 85),
        arm_l=110,
        arm_r=70,
        eyes="closed",
        mouth="o" if i % 2 else "smile",
        bob=math.sin(i / n * 2 * math.pi) * 1.5,
        hat_tilt=-25,
    )


def dance(i, n):
    t = i / n * 2 * math.pi
    return dict(
        bob=-abs(math.sin(t)) * 8,
        lean=math.sin(t) * 12,
        legs=(70, 110) if i % 2 else (95, 85),
        arm_l=-120 + math.sin(t) * 30,
        arm_r=-60 - math.sin(t) * 30,
        eyes="happy",
        mouth="grin",
        hat_tilt=math.sin(t) * 10,
    )


def wave(i, n):
    return dict(
        legs=(100, 80),
        arm_l=105,
        arm_r=-70 + (25 if i % 2 else -10),
        mouth="grin",
        eyes="happy" if i % 2 else "open",
    )


def stretch(i, n):
    # arm stretches way out to the side and snaps back
    reach = [24, 38, 56, 70, 70, 56, 38, 24][i % 8]
    return dict(
        legs=(110, 70),
        arm_l=110,
        arm_r=-5,
        arm_len=reach,
        mouth="grin" if reach > 50 else "smile",
        eyes="open",
        lean=-4,
    )


ACTIVITIES = {
    "walk": (walk, 8),
    "idle": (idle, 6),
    "eat": (eat, 6),
    "sleep": (sleep, 4),
    "dance": (dance, 8),
    "wave": (wave, 4),
    "stretch": (stretch, 8),
}


def render(name, fn, i, n):
    img = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    kw = fn(i, n)
    tip = draw_monkey(p, **kw)

    if name == "eat":
        draw_meat(p, tip + QPointF(4, -4), bitten=min(i // 2, 2))
        if i % 2:
            text(p, "nom", SIZE - 48, 30, 12)
    elif name == "sleep":
        for k in range(1 + i % 3):
            text(p, "z", 108 + k * 12, 70 - k * 14, 12 + k * 3, QColor("#3a3a8a"))
    elif name == "dance":
        note(p, 12 + (i % 4) * 4, 34 - (i % 3) * 6)
        note(p, SIZE - 26, 46 + (i % 2) * 8)
    elif name == "wave":
        if i % 2:
            text(p, "hi!", SIZE - 40, 28, 13)

    p.end()
    return pixelate(img)


# Pixel size: each "pixel" in the final art is PIXEL x PIXEL screen pixels.
PIXEL = 3


def pixelate(img):
    """Shrink to a low-res grid, snap alpha/colours, blow back up with hard edges."""
    small_size = SIZE // PIXEL
    small = img.scaled(
        small_size, small_size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    for y in range(small_size):
        for x in range(small_size):
            c = small.pixelColor(x, y)
            if c.alpha() < 110:
                small.setPixelColor(x, y, QColor(0, 0, 0, 0))
                continue
            # un-premultiply the edge blending, then posterize to a small palette
            a = c.alphaF()
            r, g, b = (min(255, int(v / a)) if a else 0 for v in (c.red(), c.green(), c.blue()))
            r, g, b = (min(255, (v // 24) * 24 + 8) for v in (r, g, b))
            small.setPixelColor(x, y, QColor(r, g, b, 255))
    return small.scaled(
        small_size * PIXEL, small_size * PIXEL,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.FastTransformation,
    )


def main():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)  # noqa: F841
    for name, (fn, n) in ACTIVITIES.items():
        folder = ASSETS / name
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("frame_*.png"):
            old.unlink()
        for i in range(n):
            render(name, fn, i, n).save(str(folder / f"frame_{i:02d}.png"))
        print(f"{name}: {n} frames -> {folder}")


if __name__ == "__main__":
    main()
