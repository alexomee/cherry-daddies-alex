from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.environ.get("BADGE_OUT") or os.path.expanduser(
    "~/projects/cherry-daddies/content/rehearsal-reels/assets/badges")
os.makedirs(OUT, exist_ok=True)
FB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
S = 260  # canvas


def shadow_bubble(sym, fill, txtcol=(20, 20, 20, 255), fs=150):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = 26
    # soft shadow
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.rounded_rectangle([pad + 8, pad + 12, S - pad + 8, S - pad + 12], radius=46, fill=(0, 0, 0, 90))
    sh = sh.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(7))
    img.alpha_composite(sh)
    # bubble
    d.rounded_rectangle([pad, pad, S - pad, S - pad], radius=46, fill=fill, outline=(255, 255, 255, 255), width=7)
    # little speech tail
    d.polygon([(S * 0.30, S - pad - 4), (S * 0.46, S - pad - 4), (S * 0.30, S - pad + 30)], fill=fill)
    f = ImageFont.truetype(FB, fs)
    bb = d.textbbox((0, 0), sym, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((S - w) / 2 - bb[0], (S - h) / 2 - bb[1] - 6), sym, font=f, fill=txtcol)
    return img


def sweat_drop():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, top, bot, rw = S / 2, 40, 220, 70
    # teardrop: triangle top + circle bottom
    d.ellipse([cx - rw, bot - 2 * rw, cx + rw, bot], fill=(90, 190, 255, 255), outline=(255, 255, 255, 255), width=7)
    d.polygon([(cx, top), (cx - rw + 8, bot - rw - 6), (cx + rw - 8, bot - rw - 6)], fill=(90, 190, 255, 255))
    d.line([(cx, top), (cx - rw + 10, bot - rw)], fill=(255, 255, 255, 255), width=7)
    d.line([(cx, top), (cx + rw - 10, bot - rw)], fill=(255, 255, 255, 255), width=7)
    # highlight
    d.ellipse([cx - 34, bot - 2 * rw + 22, cx - 4, bot - 2 * rw + 64], fill=(255, 255, 255, 150))
    return img


def note():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([22, 22, S - 22, S - 22], fill=(255, 110, 160, 255), outline=(255, 255, 255, 255), width=7)
    f = ImageFont.truetype(FB, 150)
    sym = "♫"
    bb = d.textbbox((0, 0), sym, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((S - w) / 2 - bb[0], (S - h) / 2 - bb[1] - 6), sym, font=f, fill=(255, 255, 255, 255))
    return img


shadow_bubble("?", (255, 209, 74, 255)).save(f"{OUT}/q.png")          # skeptic
shadow_bubble("??", (255, 150, 60, 255), fs=120).save(f"{OUT}/qq.png")  # confused
sweat_drop().save(f"{OUT}/sweat.png")
note().save(f"{OUT}/note.png")
print("badges:", os.listdir(OUT))
