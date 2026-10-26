#!/usr/bin/env python3
"""Export original archived FarmVille skin artwork without importing game code."""
import hashlib
import io
import json
import struct
import zlib
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "FarmVillage"
DEST = ROOT / "static/assets/skin"
DEST.mkdir(parents=True, exist_ok=True)
records = []


def png(width, height, rgba):
    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content) & 0xffffffff)
    rows = b"".join(b"\0" + rgba[y*width*4:(y+1)*width*4] for y in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def tags(path):
    data = path.read_bytes()
    if data[:3] == b"CWS":
        data = data[:8] + zlib.decompress(data[8:])
    elif data[:3] != b"FWS":
        return
    off = 8 + (5 + 4 * (data[8] >> 3) + 7) // 8 + 4
    while off + 2 <= len(data):
        header = struct.unpack_from("<H", data, off)[0]
        off += 2
        kind, size = header >> 6, header & 63
        if size == 63:
            size = struct.unpack_from("<I", data, off)[0]
            off += 4
        yield kind, data[off:off+size]
        off += size


def extract(logical, filename_prefix):
    path = SOURCE / logical if logical.startswith("embeds/") else resolve(logical)
    if not path:
        return
    for kind, content in tags(path):
        if kind not in (20, 36, 35, 21):
            continue
        cid = struct.unpack_from("<H", content)[0]
        rgba = bytearray()
        if kind in (20, 36):
            fmt, width, height = struct.unpack_from("<BHH", content, 2)
            if fmt == 5:
                raw = zlib.decompress(content[7:])
                for pos in range(0, len(raw), 4):
                    a, r, g, b = raw[pos:pos+4]
                    if kind == 20:
                        a = 255
                    elif a and a < 255:
                        r, g, b = [min(255, round(c * 255 / a)) for c in (r, g, b)]
                    rgba.extend((r, g, b, a))
            elif fmt == 3:
                count = content[7] + 1
                raw = zlib.decompress(content[8:])
                size = 4 if kind == 36 else 3
                palette = raw[:count*size]
                pixels = raw[count*size:]
                stride = (width + 3) & ~3
                for y in range(height):
                    for x in range(width):
                        index = pixels[y*stride+x]
                        p = palette[index*size:(index+1)*size]
                        rgba.extend(p if size == 4 else p + b"\xff")
            else:
                continue
            name = f"{filename_prefix}-{cid}.png"
            data = png(width, height, rgba)
        else:
            # Preserve the exact archived JPEG stream. Optional SWF alpha is not
            # applied here; these are kept for inspection, not assumed cutouts.
            if kind == 35:
                size = struct.unpack_from("<I", content, 2)[0]
                data = content[6:6+size]
            else:
                data = content[2:]
            if data[:4] == b"\xff\xd9\xff\xd8":
                data = data[2:]
            if not data.startswith(b"\xff\xd8"):
                continue
            name = f"{filename_prefix}-{cid}.jpg"
            if kind == 35 and content[6+size:]:
                original = Image.open(io.BytesIO(data)).convert("RGBA")
                alpha = zlib.decompress(content[6+size:])
                if len(alpha) == original.width * original.height:
                    original.putalpha(Image.frombytes("L", original.size, alpha))
                    image_bytes = io.BytesIO()
                    original.save(image_bytes, "PNG")
                    data = image_bytes.getvalue()
                    name = f"{filename_prefix}-{cid}.png"
        (DEST / name).write_bytes(data)
        records.append({"path": "/static/assets/skin/"+name, "logical": logical,
                        "sourcePath": str(path), "swfCharacterId": cid,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "method": "Original SWF raster symbol with original alpha exported to PNG" if name.endswith(".png") else "Original embedded JPEG bytes"})


import pyamf
manifest = pyamf.get_decoder(pyamf.AMF3, zlib.decompress((SOURCE / "assethash/v9/assethash.master.amf.gz").read_bytes())).readElement()


def resolve(logical):
    group, file = logical.split("/", 1)
    hashed = manifest.get(group, {}).get(file)
    if not hashed:
        return
    path = SOURCE / "LocalData/assets" / group / Path(file).parent / (str(hashed) + Path(file).suffix)
    return path if path.is_file() else None


copies = {
    "royal-sky.jpg": "dialogs/FV_Support/FV_RoyalWedding/royalWedding_skyBg.jpg",
    "blue-button.png": "dialogs/4d_elements/City_xPromo/xpromoCity_Button_Send.png",
    "blue-button-dim.png": "dialogs/4d_elements/City_xPromo/xpromoCity_Button_Send_dim.png",
    "blue-panel.png": "dialogs/4d_elements/City_xPromo/xpromoCity_Panel_Send.png",
    "underwater-button.png": "dialogs/underwater/Button.png",
    "animal-frame.png": "dialogs/midwest/AnimalFrame_big_noBG.png",
    "biodome-wood-frame.png": "dialogs/FV_Support/buildables/FV_Biodome2013_buildable_woodframe.png",
}
for name, logical in copies.items():
    path = resolve(logical)
    if path:
        data = path.read_bytes()
        (DEST / name).write_bytes(data)
        records.append({"path": "/static/assets/skin/"+name, "logical": logical,
                        "sourcePath": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                        "method": "Exact file copy"})
for logical, prefix in {
    "embeds/Flash/v855097-855094/FV_Preloader.swf": "original-preloader",
    "embeds/Flash/v855097-855094/FarmGame.swf": "game",
    "dialogs/FV_GenericPopUp.swf": "generic-popup",
    "dialogs/FV_GenericLrgPopUp.swf": "large-popup",
    "dialogs/FV_GenericMedPopUp.swf": "medium-popup",
    "dialogs/FV_GenericPopUp_GreenBlue_btns.swf": "greenblue-popup",
    "dialogs/FV_Tutorial_popUp.swf": "tutorial-popup",
    "preloader/FV_LoadBar.swf": "loadbar",
    "preloader/FV_Preloader_ZyngaBrand.swf": "preloader",
    "preloader/FV_Preload_Faster.swf": "preload-faster",
}.items():
    extract(logical, prefix)
aliases = {
    "sky.jpg": "royal-sky.jpg", "loading-frame.png": "original-preloader-32.png",
    "cream-cloud.png": "original-preloader-30.png", "dialog-panel.png": "large-popup-1.png",
    "header-wood.png": "loadbar-1.png", "cyan-meter.png": "game-659.png",
    "green-meter.png": "game-588.png", "crop-tile.png": "game-24.png",
    "cream-card.png": "game-519.png",
}
by_path = {record["path"]: record for record in records}
for name, original in aliases.items():
    path = DEST / original
    if path.is_file():
        (DEST / name).write_bytes(path.read_bytes())
        record = dict(by_path["/static/assets/skin/" + original])
        record.update(path="/static/assets/skin/" + name, aliasOf="/static/assets/skin/" + original)
        records.append(record)
for record in records:
    image = Image.open(ROOT / record["path"].lstrip("/"))
    record.update(width=image.width, height=image.height)
for name, original in {"merkin.ttf": "MERKIN__.ttf", "badaboom-bb.ttf": "BADABB__.TTF"}.items():
    path = resolve("fonts/" + original)
    if path:
        data = path.read_bytes()
        (DEST / name).write_bytes(data)
        records.append({"path": "/static/assets/skin/" + name, "logical": "fonts/" + original,
                        "sourcePath": str(path), "sha256": hashlib.sha256(data).hexdigest(),
                        "method": "Exact original font file copy"})
for record in records:
    record["sourceSha256"] = hashlib.sha256(Path(record["sourcePath"]).read_bytes()).hexdigest()
(ROOT / "data/skin-assets.json").write_text(json.dumps(records, indent=2) + "\n")
print(json.dumps({"files": len(records), "bytes": sum((ROOT / r['path'].lstrip('/')).stat().st_size for r in records)}, indent=2))
