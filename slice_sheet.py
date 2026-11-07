"""Cut a sprite sheet into per-activity frame folders for the pet.

    python slice_sheet.py --preview   # writes assets/luffy/_preview.png with row/frame numbers
    python slice_sheet.py             # exports frames using PICKS below

Sprites are found automatically: the sheet is split into horizontal bands
(rows of sprites), and each band is split wherever there's an empty column gap.
Each exported frame is scaled up with hard pixel edges and placed bottom-centre
on one shared canvas size, so the pet doesn't jump around between activities.
"""

import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter, QPen

PACK = Path(__file__).parent / "assets" / "luffy"
SHEET = PACK / "luffy_sheet.png"
SCALE = 1  # how many screen pixels per sprite pixel
MIN_GAP = 2  # empty columns needed to split two sprites
FLIP = True  # sheet sprites face left; the pet expects right-facing frames

# activity -> (band number, [sprite numbers in that band]) as shown in _preview.png
PICKS = {
    "idle": (0, list(range(7))),
    "walk": (1, list(range(6))),
    "stretch": (10, list(range(6))),
    "dance": (28, list(range(9))),
    "wave": (60, list(range(5))),
    "eat": (37, list(range(11))),
    "sleep": (26, [0, 1]),
    "carry": (47, [2, 3, 4, 5]),
    "land": (26, list(range(10))),
}


def opaque(img, x, y):
    return img.pixelColor(x, y).alpha() > 0


def find_sprites(img):
    w, h = img.width(), img.height()
    row_has = [any(opaque(img, x, y) for x in range(w)) for y in range(h)]

    bands, y = [], 0
    while y < h:
        if row_has[y]:
            top = y
            while y < h and row_has[y]:
                y += 1
            bands.append((top, y))
        y += 1

    result = []
    for top, bottom in bands:
        col_has = [any(opaque(img, x, yy) for yy in range(top, bottom)) for x in range(w)]
        sprites, x = [], 0
        while x < w:
            if col_has[x]:
                left = x
                gap = 0
                while x < w and gap < MIN_GAP:
                    gap = 0 if col_has[x] else gap + 1
                    x += 1
                right = x - gap
                # tighten vertically
                ys = [yy for yy in range(top, bottom)
                      if any(opaque(img, xx, yy) for xx in range(left, right))]
                sprites.append(QRect(left, ys[0], right - left, ys[-1] - ys[0] + 1))
            x += 1
        result.append(sprites)
    return result


def preview(img, bands, out):
    pad = 40
    canvas = QImage(img.width() + pad, img.height(), QImage.Format.Format_ARGB32)
    canvas.fill(QColor("#e8eef3"))
    p = QPainter(canvas)
    p.drawImage(pad, 0, img)
    f = QFont("Segoe UI", 7)
    f.setBold(True)
    p.setFont(f)
    for b, sprites in enumerate(bands):
        if not sprites:
            continue
        p.setPen(QColor("#c0262d"))
        p.drawText(2, sprites[0].top() + 10, f"B{b}")
        for i, r in enumerate(sprites):
            p.setPen(QPen(QColor(0, 120, 255, 140), 1))
            p.drawRect(r.translated(pad, 0))
            p.setPen(QColor("#0050c0"))
            p.drawText(r.left() + pad + 1, r.bottom() + 9, str(i))
    p.end()
    canvas.save(str(out))


def export(img, bands):
    chosen = {
        act: [bands[b][i] for i in idx] for act, (b, idx) in PICKS.items()
    }
    cw = max(r.width() for rs in chosen.values() for r in rs)
    ch = max(r.height() for rs in chosen.values() for r in rs)
    for act, rects in chosen.items():
        folder = PACK / act
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.png"):
            old.unlink()
        for n, r in enumerate(rects):
            frame = QImage(cw, ch, QImage.Format.Format_ARGB32)
            frame.fill(Qt.GlobalColor.transparent)
            p = QPainter(frame)
            sprite = img.copy(r)
            if FLIP:
                sprite = sprite.flipped(Qt.Orientation.Horizontal)
            p.drawImage(QPoint((cw - r.width()) // 2, ch - r.height()), sprite)
            p.end()
            frame = frame.scaled(cw * SCALE, ch * SCALE,
                                 Qt.AspectRatioMode.IgnoreAspectRatio,
                                 Qt.TransformationMode.FastTransformation)
            frame.save(str(folder / f"{n:02d}.png"))
        print(f"{act}: {len(rects)} frames")
    print(f"frame size: {cw * SCALE}x{ch * SCALE}")


def main():
    QGuiApplication.instance() or QGuiApplication(sys.argv)
    img = QImage(str(SHEET)).convertToFormat(QImage.Format.Format_ARGB32)
    bands = find_sprites(img)
    if "--preview" in sys.argv:
        out = PACK / "_preview.png"
        preview(img, bands, out)
        for b, s in enumerate(bands):
            print(f"B{b}: {len(s)} sprites, y={s[0].top() if s else '-'}")
        print("preview ->", out)
    else:
        export(img, bands)


if __name__ == "__main__":
    main()
