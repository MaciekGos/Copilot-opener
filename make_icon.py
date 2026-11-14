"""Generuje icon.ico odwzorowujace logo.svg (bez zewnetrznych bibliotek SVG)."""
from PIL import Image, ImageDraw

S = 1024  # rysujemy w duzej rozdzielczosci, potem zmniejszamy
k = S / 256


def p(*v):
    return [x * k for x in v]


# tlo: gradient po przekatnej
c1, c2 = (0x6E, 0x40, 0xC9), (0x1F, 0x6F, 0xEB)
bg = Image.new("RGB", (S, S))
px = bg.load()
for y in range(S):
    for x in range(S):
        t = (x + y) / (2 * (S - 1))
        px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=56 * k, fill=255)

# biale elementy na osobnej warstwie
ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(ov)
w = int(14 * k)
d.rounded_rectangle(p(64, 88, 168, 192), radius=16 * k, outline="white", width=w)
d.rectangle(p(112, 70, 190, 128), fill=(0, 0, 0, 0))  # wyciecie rogu
for a, b in [((112, 144), (184, 72)), ((142, 72), (184, 72)), ((184, 72), (184, 114))]:
    d.line(p(*a, *b), fill="white", width=w)
    for q in (a, b):
        r = w / 2
        d.ellipse([q[0] * k - r, q[1] * k - r, q[0] * k + r, q[1] * k + r], fill="white")
d.ellipse(p(174, 174, 218, 218), fill="white")
d.ellipse(p(177, 177, 215, 215), fill=(0x3D, 0xDC, 0x84, 255))

bg.paste(ov, (0, 0), ov)
out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
out.paste(bg, (0, 0), mask)
out = out.resize((256, 256), Image.LANCZOS)
out.save("icon.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("icon.ico gotowe")
