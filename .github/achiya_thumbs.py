"""Achiya pictures, run on GitHub's server (workflow achiya-thumbs.yml), not on the home computer.

The first page of every Achiya material in data.json that has no picture yet -> img/ach/<id>.webp, and "im" on the item.
ONE request at a time, with pauses: it is someone else's site, and six in parallel got us blocked (HTTP 429) on 2026-10-07.
A copy of shoot_achiya in kol-toda-build/catalog-kit/thumbs.py; here the cache is img/ach itself.
"""
import io, json, os, re, time, urllib.request, urllib.error
import fitz
from PIL import Image

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
FILE = re.compile(r'https://achiyayeda\.org/wp-content/uploads/[^"\'\s<>]+\.(?:pdf|docx?|pptx?|jpe?g|png)', re.I)
OUT = os.path.join("img", "ach")


def get(url):
    time.sleep(1.5)
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read(30_000_000)


def shoot(i, link):
    for attempt in range(6):
        try:
            m = FILE.search(get(link).decode("utf-8", "replace"))
            if not m: return "no file on the page"
            url = m.group(0); ext = url.rsplit(".", 1)[1].lower()
            if ext == "doc": return "old Word"
            data = get(url)
            if ext in ("jpg", "jpeg", "png"):
                im = Image.open(io.BytesIO(data)).convert("RGB")
            else:
                pix = fitz.open(stream=data, filetype=ext)[0].get_pixmap(dpi=60)
                im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            im.thumbnail((400, 520)); im.save(os.path.join(OUT, i + ".webp"), "WEBP", quality=70)
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(180 * (attempt + 1)); continue
            return f"HTTP {e.code}"
        except Exception as e:
            return type(e).__name__
    return "429 six times"


def main():
    d = json.load(open("data.json", encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    todo = sorted({(f["id"][4:], f["u"]) for it in d["items"] if not it.get("im") for f in it["files"] if f["id"].startswith("ach_")})
    print(len(todo), "Achiya materials without a picture", flush=True)
    for i, link in todo:
        if not os.path.exists(os.path.join(OUT, i + ".webp")):
            print(i, shoot(i, link), flush=True)
            time.sleep(4)
    n = 0
    for it in d["items"]:
        if it.get("im"): continue
        k = next((f["id"][4:] for f in it["files"] if f["id"].startswith("ach_") and os.path.exists(os.path.join(OUT, f["id"][4:] + ".webp"))), None)
        if k: it["im"] = f"img/ach/{k}.webp"; n += 1
    json.dump(d, open("data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("pictures set:", n)


if __name__ == "__main__":
    main()
