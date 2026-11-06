#!/usr/bin/env python3
"""Fill the blank PO as an incremental update and write the delta (bytes appended after the blank).

Each filled text field gets an explicit font size that fits its box (taken from the
appearance pypdf builds with auto-size), and NeedAppearances is turned off, so every
viewer shows the pre-fitted text instead of redrawing it at full size.

Usage: fill_incremental.py blank.pdf values.json out.pdf delta.b64
"""
import json, re, sys, base64
from pypdf import PdfWriter
from pypdf.generic import NameObject, TextStringObject, BooleanObject

blank, vals_path, out_path, delta_path = sys.argv[1:5]
vals = {v["field_id"]: v["value"] for v in json.load(open(vals_path))}
w = PdfWriter(blank, incremental=True)
af = w._root_object["/AcroForm"]

def walk(f, fn):
    f = f.get_object(); fn(f)
    for k in f.get("/Kids", []):
        walk(k, fn)

# 1. auto-size (0 Tf) on the fields we fill, so pypdf fits the text when it builds appearances
def autosize(f):
    if f.get("/FT") == "/Tx" and "/DA" in f and f.get("/T") in vals:
        size = "10" if int(f.get("/Ff", 0)) & 4096 else "0"  # multi-line boxes: fixed 10 pt so 3 lines fit
        f[NameObject("/DA")] = TextStringObject(re.sub(r"(\d+(?:\.\d+)?)\s+Tf", size + " Tf", f["/DA"]))
for f in af["/Fields"]:
    walk(f, autosize)

# multi-line boxes: break the text into lines that fit the box width at 10 pt Helvetica
from reportlab.pdfbase.pdfmetrics import stringWidth
def wrap(f):
    t = f.get("/T")
    if f.get("/FT") == "/Tx" and t in vals and int(f.get("/Ff", 0)) & 4096 and "\n" not in vals[t]:
        r = [float(x) for x in f["/Rect"]]; width = abs(r[2] - r[0]) - 6
        lines, cur = [], ""
        for word in vals[t].split():
            trial = (cur + " " + word).strip()
            if cur and stringWidth(trial, "Helvetica", 10) > width:
                lines.append(cur); cur = word
            else:
                cur = trial
        lines.append(cur)
        vals[t] = "\n".join(lines)
for f in af["/Fields"]:
    walk(f, wrap)

w.update_page_form_field_values(w.pages[0], vals, auto_regenerate=False)

# 2. copy the fitted size from each new appearance into DA, so a redraw also fits
def pin(f):
    if f.get("/FT") == "/Tx" and f.get("/T") in vals and "/AP" in f:
        m = re.search(rb"/\S+\s+([\d.]+)\s+Tf", f["/AP"]["/N"].get_object().get_data())
        if m:
            size = float(m.group(1))
            f[NameObject("/DA")] = TextStringObject(re.sub(r"(\d+(?:\.\d+)?)\s+Tf", f"{size:g} Tf", f["/DA"]))
for f in af["/Fields"]:
    walk(f, pin)

# 3. use our appearances; don't ask viewers to rebuild them
af[NameObject("/NeedAppearances")] = BooleanObject(False)

with open(out_path, "wb") as fh:
    w.write(fh)
full = open(out_path, "rb").read(); base = open(blank, "rb").read()
assert full[:len(base)] == base, "not a pure append"
delta = full[len(base):]
open(delta_path, "w").write(base64.b64encode(delta).decode())
print(f"blank {len(base)} B, delta {len(delta)} B, delta b64 {len(base64.b64encode(delta))} chars")
