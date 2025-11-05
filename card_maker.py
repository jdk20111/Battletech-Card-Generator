from PIL import Image, ImageDraw, ImageFont, ImageTk
import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox, Spinbox
from datetime import datetime
import os, json

# --- Constants ---
OUTPUT_SIZE = (2100, 1500)  # 7×5 in @300 DPI
PREVIEW_SCALE = 0.3
DEFAULT_BG = os.path.join("assets", "Battletech Card Blank 11-1-25 v1.png")
SAVE_DIR = "saved_cards"
ASSETS_DIR = "assets"
ARMOR_DOT = os.path.join(ASSETS_DIR, "armor_dot.png")
STRUCTURE_DOT = os.path.join(ASSETS_DIR, "structure_dot.png")
MECH_PICS_DIR = os.path.join(ASSETS_DIR, "mech_pics")
NUDGE_STEP = 5

bg_image = preview_image = photo_preview = mech_image = None

# --- Defaults (from your screenshot) ---
TEXT_ELEMENTS = {
    "model":  {"pos":[80,40],"size":120,"fill":"#efe31c","outline":"#930000","outline_width":6,"text":""},
    "name":   {"pos":[80,145],"size":180,"fill":"#930000","outline":"#efe31c","outline_width":6,"text":""},
    "MV":     {"pos":[1020,480],"size":120,"fill":"#930000","outline":"#ffffff","outline_width":4,"text":""},
    "SZ":     {"pos":[260,480],"size":120,"fill":"#930000","outline":"#ffffff","outline_width":4,"text":""},
    "TMM":    {"pos":[670,480],"size":120,"fill":"#930000","outline":"#ffffff","outline_width":4,"text":""},
    "short":  {"pos":[305,740],"size":120,"fill":"#930000","outline":"#ffffff","outline_width":4,"text":""},
    "medium": {"pos":[625,740],"size":120,"fill":"#930000","outline":"#ffffff","outline_width":4,"text":""},
    "long":   {"pos":[950,740],"size":120,"fill":"#930000","outline":"#ffffff","outline_width":4,"text":""},
    "PV":     {"pos":[1785,10],"size":140,"fill":"#930000","outline":"#efe31c","outline_width":4,"text":""},
    "Armor":     {"count":0,"pos":[180,945],"size":60,"spacing":61,"per_row":13,"row_gap":5},
    "Structure": {"count":0,"pos":[180,1095],"size":60,"spacing":61,"per_row":13,"row_gap":5},
}

MECH_IMAGE = {
    "path": None,
    "pos": [1280, 110],     # X, Y
    "size": [666, 888],     # Width, Height
    "aspect_ratio": 666 / 888,
}

# --- State maps ---
pos_entries, size_vars, outline_vars, fill_vars, outline_color_vars = {}, {}, {}, {}, {}
dot_pos_entries, dot_size_vars, dot_spacing_vars, dot_per_row_vars, dot_row_gap_vars = {}, {}, {}, {}, {}
mech_pos_entries, mech_size_vars = {}, {}

# --- Font loader ---
def load_font(size):
    candidates = [
        os.path.join("fonts", "Steiner.otf"),
        r"C:\\Users\\Jonathan\\AppData\\Local\\Microsoft\\Windows\\Fonts\\STEINER.OTF",
        "arialbd.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

# --- Load background image ---
def load_background(p=None):
    global bg_image
    path = p if p and os.path.exists(p) else filedialog.askopenfilename(
        title="Select Background",
        filetypes=[("Images","*.png;*.jpg;*.jpeg;*.tif;*.tiff")]
    )
    if not path:
        return
    bg_image = Image.open(path).convert("RGBA").resize(OUTPUT_SIZE)
    draw_preview()

# --- Load mech image file ---
def load_mech_image(name):
    global mech_image
    if not name or name == "None":
        mech_image = None
        MECH_IMAGE["path"] = None
        draw_preview()
        return
    path = os.path.join(MECH_PICS_DIR, name)
    if os.path.exists(path):
        mech_image = Image.open(path).convert("RGBA")
        MECH_IMAGE["path"] = path
        if mech_image.height != 0:
            MECH_IMAGE["aspect_ratio"] = mech_image.width / mech_image.height
        draw_preview()

# --- Preview render ---
def draw_preview():
    global preview_image, photo_preview
    if not bg_image:
        return

    img = bg_image.copy().resize((int(OUTPUT_SIZE[0]*PREVIEW_SCALE), int(OUTPUT_SIZE[1]*PREVIEW_SCALE)))
    draw = ImageDraw.Draw(img)
    scale = PREVIEW_SCALE

    # Text elements
    for key, var in vars_map.items():
        if key in ("Armor","Structure"):  # skip dot counters
            continue
        t = var.get().upper()
        TEXT_ELEMENTS[key]["text"] = t
        d = TEXT_ELEMENTS[key]
        pos = (d["pos"][0]*scale, d["pos"][1]*scale)
        f = load_font(int(d["size"]*scale))
        ow = max(1, int(d["outline_width"]*scale))
        o = d["outline"]
        if o:
            for dx in range(-ow, ow+1):
                for dy in range(-ow, ow+1):
                    if dx or dy:
                        draw.text((pos[0]+dx, pos[1]+dy), t, font=f, fill=o)
        draw.text(pos, t, fill=d["fill"], font=f)
    
    # Mech image
    if mech_image:
        mech_scaled = mech_image.resize((int(MECH_IMAGE["size"][0]*scale), int(MECH_IMAGE["size"][1]*scale)))
        img.paste(mech_scaled, (int(MECH_IMAGE["pos"][0]*scale), int(MECH_IMAGE["pos"][1]*scale)), mech_scaled)

    # Armor/Structure dots with wrapping
    try:
        armor, struct = Image.open(ARMOR_DOT).convert("RGBA"), Image.open(STRUCTURE_DOT).convert("RGBA")
        for label, imgdot in [("Armor", armor), ("Structure", struct)]:
            d = TEXT_ELEMENTS[label]
            c = int(vars_map[label].get() or 0)
            s = int(d["size"])
            scaled = imgdot.resize((int(s*scale), int(s*scale)))
            per_row = int(d.get("per_row", 13))
            row_gap = int(d.get("row_gap", 5))
            for i in range(c):
                row = i // per_row
                col = i % per_row
                x = int((d["pos"][0] + col * d["spacing"]) * scale)
                y = int((d["pos"][1] + row * (d["size"] + row_gap)) * scale)
                img.paste(scaled, (x, y), scaled)
    except Exception as e:
        print("Dot render error:", e)

    preview_image = img
    photo_preview = ImageTk.PhotoImage(img)
    preview_label.config(image=photo_preview)
    preview_label.image = photo_preview

# --- Aspect ratio helpers for mech image ---
def update_mech_width(var):
    try:
        w = int(var.get() or 0)
        if keep_aspect_ratio.get() and MECH_IMAGE.get("aspect_ratio", 0) > 0:
            MECH_IMAGE["size"][1] = int(w / MECH_IMAGE["aspect_ratio"])
            mech_size_vars["h"].set(str(MECH_IMAGE["size"][1]))
        MECH_IMAGE["size"][0] = w
        draw_preview()
    except ValueError:
        pass

def update_mech_height(var):
    try:
        h = int(var.get() or 0)
        if keep_aspect_ratio.get() and MECH_IMAGE.get("aspect_ratio", 0) > 0:
            MECH_IMAGE["size"][0] = int(h * MECH_IMAGE["aspect_ratio"])
            mech_size_vars["w"].set(str(MECH_IMAGE["size"][0]))
        MECH_IMAGE["size"][1] = h
        draw_preview()
    except ValueError:
        pass

# --- Helpers ---
def nudge_text(k, dx, dy):
    TEXT_ELEMENTS[k]["pos"][0] += dx
    TEXT_ELEMENTS[k]["pos"][1] += dy
    pos_entries[k]["x"].set(str(TEXT_ELEMENTS[k]["pos"][0]))
    pos_entries[k]["y"].set(str(TEXT_ELEMENTS[k]["pos"][1]))
    draw_preview()

def nudge_dots(k, dx, dy):
    TEXT_ELEMENTS[k]["pos"][0] += dx
    TEXT_ELEMENTS[k]["pos"][1] += dy
    dot_pos_entries[k]["x"].set(str(TEXT_ELEMENTS[k]["pos"][0]))
    dot_pos_entries[k]["y"].set(str(TEXT_ELEMENTS[k]["pos"][1]))
    draw_preview()

def nudge_mech(dx, dy):
    MECH_IMAGE["pos"][0] += dx
    MECH_IMAGE["pos"][1] += dy
    mech_pos_entries["x"].set(str(MECH_IMAGE["pos"][0]))
    mech_pos_entries["y"].set(str(MECH_IMAGE["pos"][1]))
    draw_preview()

def toggle_section(frame, var):
    if var.get():
        frame.pack(anchor="w", fill="x", pady=3)
    else:
        frame.forget()

# --- GUI ---
root = tk.Tk()
root.title("Battletech Card Generator")

# UI state (must be after root)
keep_aspect_ratio = tk.BooleanVar(value=True)
show_text_appearance = tk.BooleanVar(value=True)
show_armor_appearance = tk.BooleanVar(value=True)
show_mech_appearance = tk.BooleanVar(value=True)

main = tk.Frame(root); main.pack(fill=tk.BOTH, expand=True)
left = tk.Frame(main); left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

# --- Stats Section ---
tk.Label(left, text="Stats:", font=("Arial",10,"bold")).pack(anchor="w", pady=4)
vars_map = {k: tk.StringVar() for k in TEXT_ELEMENTS}

display_labels = {
    "model":"Model","name":"Name","MV":"MV","SZ":"Size","TMM":"TMM",
    "short":"Short","medium":"Medium","long":"Long","PV":"PV",
    "Armor":"Armor","Structure":"Structure"
}

fields_frame = tk.Frame(left); fields_frame.pack(anchor="w", fill=tk.X)
keys = list(TEXT_ELEMENTS.keys())
numeric_fields = {"MV","SZ","TMM","short","medium","long","PV"}

for i, lbl in enumerate(keys):
    f = tk.Frame(fields_frame)
    r, c = i // 2, i % 2
    f.grid(row=r, column=c, sticky="w", padx=5, pady=2)
    tk.Label(f, text=display_labels.get(lbl,lbl), width=8).pack(side=tk.LEFT)
    var = vars_map[lbl]
    if lbl in ("Armor","Structure") or lbl in numeric_fields:
        spin = Spinbox(f, from_=0, to=50, width=5, textvariable=var, command=draw_preview)
        spin.pack(side=tk.LEFT)
    else:
        e = tk.Entry(f, textvariable=var, width=14); e.pack(side=tk.LEFT)
    var.set(str(TEXT_ELEMENTS[lbl].get("text","")) if lbl not in ("Armor","Structure") else str(TEXT_ELEMENTS[lbl]["count"]))
    var.trace_add("write", lambda *_,: draw_preview())

# --- Mech Image selector in Stats ---
tk.Label(left, text="\nMech Image", font=("Arial",10,"bold")).pack(anchor="w", pady=(8,2))
mech_files = []
try:
    mech_files = [f for f in os.listdir(MECH_PICS_DIR) if f.lower().endswith(".png")]
except FileNotFoundError:
    os.makedirs(MECH_PICS_DIR, exist_ok=True)
mech_files.insert(0, "None")
selected_mech = tk.StringVar(value="None")
f_mech_select = tk.Frame(left); f_mech_select.pack(anchor="w", pady=3)
tk.Label(f_mech_select, text="Select:").pack(side=tk.LEFT)
tk.OptionMenu(f_mech_select, selected_mech, *mech_files, command=load_mech_image).pack(side=tk.LEFT)

# --- Text Appearance (collapsible) ---
header_text_frame = tk.Frame(left); header_text_frame.pack(anchor="w", pady=(8,2))
tk.Checkbutton(header_text_frame, text="Text Appearance", variable=show_text_appearance,
               command=lambda: toggle_section(text_appearance_frame, show_text_appearance),
               font=("Arial",10,"bold")).pack(side=tk.LEFT)
text_appearance_frame = tk.Frame(left); text_appearance_frame.pack(anchor="w", fill="x", pady=3)
for k in [x for x in TEXT_ELEMENTS if x not in ("Armor","Structure")]:
    d = TEXT_ELEMENTS[k]; f = tk.Frame(text_appearance_frame); f.pack(anchor="w", pady=3)
    tk.Label(f, text=display_labels.get(k,k), width=7).pack(side=tk.LEFT)
    for sym, dx, dy in [("←",-NUDGE_STEP,0),("↑",0,-NUDGE_STEP),("↓",0,NUDGE_STEP),("→",NUDGE_STEP,0)]:
        tk.Button(f, text=sym, width=2, command=lambda key=k, x=dx, y=dy: nudge_text(key, x, y)).pack(side=tk.LEFT)
    tk.Label(f, text="X:").pack(side=tk.LEFT)
    xv = tk.StringVar(value=str(d["pos"][0])); tk.Entry(f, textvariable=xv, width=5).pack(side=tk.LEFT)
    tk.Label(f, text="Y:").pack(side=tk.LEFT)
    yv = tk.StringVar(value=str(d["pos"][1])); tk.Entry(f, textvariable=yv, width=5).pack(side=tk.LEFT)
    pos_entries[k] = {"x": xv, "y": yv}
    xv.trace_add("write", lambda *_, key=k, v=xv: (TEXT_ELEMENTS[key]["pos"].__setitem__(0, int(v.get() or 0)), draw_preview()))
    yv.trace_add("write", lambda *_, key=k, v=yv: (TEXT_ELEMENTS[key]["pos"].__setitem__(1, int(v.get() or 0)), draw_preview()))
    tk.Label(f, text="Size:").pack(side=tk.LEFT)
    sv = tk.StringVar(value=str(d["size"])); tk.Entry(f, textvariable=sv, width=4).pack(side=tk.LEFT)
    size_vars[k] = sv
    sv.trace_add("write", lambda *_, key=k, v=sv: (TEXT_ELEMENTS[key].__setitem__("size", int(v.get() or 0)), draw_preview()))
    tk.Label(f, text="O:").pack(side=tk.LEFT)
    ow = tk.StringVar(value=str(d["outline_width"])); tk.Entry(f, textvariable=ow, width=4).pack(side=tk.LEFT)
    outline_vars[k] = ow
    ow.trace_add("write", lambda *_, key=k, v=ow: (TEXT_ELEMENTS[key].__setitem__("outline_width", int(v.get() or 0)), draw_preview()))
    tk.Label(f, text="Fill:").pack(side=tk.LEFT)
    fc = tk.StringVar(value=d["fill"]); ef = tk.Entry(f, textvariable=fc, width=8); ef.pack(side=tk.LEFT)
    tk.Button(f, text="🎨", command=lambda key=k, v=fc: (v.set(colorchooser.askcolor()[1] or v.get()),
            TEXT_ELEMENTS[key].__setitem__("fill", v.get()), draw_preview())).pack(side=tk.LEFT)
    fill_vars[k] = fc
    fc.trace_add("write", lambda *_, key=k, v=fc: (TEXT_ELEMENTS[key].__setitem__("fill", v.get()), draw_preview()))
    tk.Label(f, text="Out:").pack(side=tk.LEFT)
    oc = tk.StringVar(value=d["outline"]); eo = tk.Entry(f, textvariable=oc, width=8); eo.pack(side=tk.LEFT)
    tk.Button(f, text="🎨", command=lambda key=k, v=oc: (v.set(colorchooser.askcolor()[1] or v.get()),
            TEXT_ELEMENTS[key].__setitem__("outline", v.get()), draw_preview())).pack(side=tk.LEFT)
    outline_color_vars[k] = oc
    oc.trace_add("write", lambda *_, key=k, v=oc: (TEXT_ELEMENTS[key].__setitem__("outline", v.get()), draw_preview()))

# --- Armor / Structure Appearance (collapsible) ---
header_armor_frame = tk.Frame(left); header_armor_frame.pack(anchor="w", pady=(8,2))
tk.Checkbutton(header_armor_frame, text="Armor / Structure Appearance", variable=show_armor_appearance,
               command=lambda: toggle_section(armor_appearance_frame, show_armor_appearance),
               font=("Arial",10,"bold")).pack(side=tk.LEFT)
armor_appearance_frame = tk.Frame(left); armor_appearance_frame.pack(anchor="w", fill="x", pady=3)
for k in ("Armor","Structure"):
    d = TEXT_ELEMENTS[k]; f = tk.Frame(armor_appearance_frame); f.pack(anchor="w", pady=3)
    tk.Label(f, text=k, width=7).pack(side=tk.LEFT)
    for sym,dx,dy in [("←",-NUDGE_STEP,0),("↑",0,-NUDGE_STEP),("↓",0,NUDGE_STEP),("→",NUDGE_STEP,0)]:
        tk.Button(f, text=sym, width=2, command=lambda key=k, x=dx, y=dy: nudge_dots(key, x, y)).pack(side=tk.LEFT)
    for lbl, field in [("X","x"),("Y","y"),("Size","size"),("Sp","spacing"),("PerRow","per_row"),("RowGap","row_gap")]:
        tk.Label(f, text=f"{lbl}:").pack(side=tk.LEFT)
        val = str(d["pos"][0] if field=="x" else d["pos"][1] if field=="y" else d[field])
        v = tk.StringVar(value=val); tk.Entry(f, textvariable=v, width=5).pack(side=tk.LEFT)
        if field == "x":
            dot_pos_entries[k] = {"x": v}
        elif field == "y":
            dot_pos_entries[k]["y"] = v
        elif field == "size":
            dot_size_vars[k] = v
        elif field == "spacing":
            dot_spacing_vars[k] = v
        elif field == "per_row":
            dot_per_row_vars[k] = v
        elif field == "row_gap":
            dot_row_gap_vars[k] = v
        def _trace(*_, key=k, f=field, var=v):
            if f == "x":
                TEXT_ELEMENTS[key]["pos"][0] = int(var.get() or 0)
            elif f == "y":
                TEXT_ELEMENTS[key]["pos"][1] = int(var.get() or 0)
            else:
                TEXT_ELEMENTS[key][f] = int(var.get() or 0)
            draw_preview()
        v.trace_add("write", _trace)

# --- Mech Image Appearance (collapsible) ---
header_mech_frame = tk.Frame(left); header_mech_frame.pack(anchor="w", pady=(8,2))
tk.Checkbutton(header_mech_frame, text="Mech Image Appearance", variable=show_mech_appearance,
               command=lambda: toggle_section(mech_appearance_frame, show_mech_appearance),
               font=("Arial",10,"bold")).pack(side=tk.LEFT)
mech_appearance_frame = tk.Frame(left); mech_appearance_frame.pack(anchor="w", fill="x", pady=3)

f = tk.Frame(mech_appearance_frame); f.pack(anchor="w", pady=3)
# nudge
for sym,dx,dy in [("←",-NUDGE_STEP,0),("↑",0,-NUDGE_STEP),("↓",0,NUDGE_STEP),("→",NUDGE_STEP,0)]:
    tk.Button(f, text=sym, width=2, command=lambda x=dx, y=dy: nudge_mech(x, y)).pack(side=tk.LEFT)

# X/Y + W/H + Keep Aspect
tk.Label(f, text="X:").pack(side=tk.LEFT)
xv = tk.StringVar(value=str(MECH_IMAGE["pos"][0])); tk.Entry(f, textvariable=xv, width=5).pack(side=tk.LEFT)
tk.Label(f, text="Y:").pack(side=tk.LEFT)
yv = tk.StringVar(value=str(MECH_IMAGE["pos"][1])); tk.Entry(f, textvariable=yv, width=5).pack(side=tk.LEFT)
mech_pos_entries = {"x": xv, "y": yv}
xv.trace_add("write", lambda *_, v=xv: (MECH_IMAGE["pos"].__setitem__(0, int(v.get() or 0)), draw_preview()))
yv.trace_add("write", lambda *_, v=yv: (MECH_IMAGE["pos"].__setitem__(1, int(v.get() or 0)), draw_preview()))

tk.Label(f, text="W:").pack(side=tk.LEFT)
wv = tk.StringVar(value=str(MECH_IMAGE["size"][0])); tk.Entry(f, textvariable=wv, width=5).pack(side=tk.LEFT)
tk.Label(f, text="H:").pack(side=tk.LEFT)
hv = tk.StringVar(value=str(MECH_IMAGE["size"][1])); tk.Entry(f, textvariable=hv, width=5).pack(side=tk.LEFT)
mech_size_vars = {"w": wv, "h": hv}
keep_aspect_ratio = tk.BooleanVar(value=True)
tk.Checkbutton(f, text="Keep Aspect", variable=keep_aspect_ratio).pack(side=tk.LEFT, padx=6)
wv.trace_add("write", lambda *_, v=wv: update_mech_width(v))
hv.trace_add("write", lambda *_, v=hv: update_mech_height(v))

# --- Right side preview ---
right = tk.Frame(main); right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
preview_label = tk.Label(right, bg="#222"); preview_label.pack(fill=tk.BOTH, expand=True)

# --- Bottom buttons ---
bottom = tk.Frame(root); bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
tk.Button(bottom, text="Load Background", command=lambda: load_background(DEFAULT_BG)).pack(side=tk.LEFT, padx=10)
tk.Button(bottom, text="Save Settings", command=lambda: save_settings()).pack(side=tk.LEFT, padx=10)
tk.Button(bottom, text="Load Settings", command=lambda: load_settings()).pack(side=tk.LEFT, padx=10)
tk.Button(bottom, text="Save Final TIFF", command=lambda: save_final()).pack(side=tk.LEFT, padx=10)

status_label = tk.Label(root, text=""); status_label.pack(pady=3)

# --- Save/Load & Export (unchanged logic) ---
def save_settings():
    os.makedirs(SAVE_DIR, exist_ok=True)
    model = vars_map["model"].get().strip().upper() or "UNTITLED"
    name  = vars_map["name"].get().strip().upper() or "CARD"
    path  = os.path.join(SAVE_DIR, f"{model}_{name}.json")
    for k in TEXT_ELEMENTS:
        if k in vars_map:
            if k not in ("Armor","Structure"):
                TEXT_ELEMENTS[k]["text"] = vars_map[k].get().upper()
            else:
                TEXT_ELEMENTS[k]["count"] = int(vars_map[k].get() or 0)
    TEXT_ELEMENTS["MechImage"] = MECH_IMAGE
    with open(path, "w") as f:
        json.dump(TEXT_ELEMENTS, f, indent=4)
    messagebox.showinfo("Settings Saved", f"Saved to:\n{path}")

def load_settings():
    file = filedialog.askopenfilename(title="Load Settings", filetypes=[("JSON Files","*.json")], initialdir=SAVE_DIR)
    if not file: return
    try:
        with open(file) as f: data = json.load(f)
        if "title" in data and "model" not in data:
            data["model"] = data.pop("title")
        for k,v in data.items():
            if k in TEXT_ELEMENTS:
                TEXT_ELEMENTS[k].update(v)
                if k in vars_map:
                    if k in ("Armor","Structure"): vars_map[k].set(str(v.get("count",0)))
                    else: vars_map[k].set(v.get("text",""))
        if "MechImage" in data:
            MECH_IMAGE.update(data["MechImage"])
            if MECH_IMAGE["path"]:
                mech_name = os.path.basename(MECH_IMAGE["path"])
                load_mech_image(mech_name)
        refresh_appearance_entries(); refresh_dot_entries(); refresh_mech_entries(); draw_preview()
        messagebox.showinfo("Loaded", f"Loaded: {os.path.basename(file)}")
    except Exception as e:
        messagebox.showerror("Load Failed", str(e))

def save_final():
    if not bg_image:
        messagebox.showwarning("No Background","Please load a background first!"); return
    img=bg_image.copy(); draw=ImageDraw.Draw(img)
    for k,v in vars_map.items():
        if k in ("Armor","Structure"): continue
        t=v.get().upper(); d=TEXT_ELEMENTS[k]; f=load_font(d["size"]); pos=tuple(d["pos"])
        ow=d["outline_width"]; o=d["outline"]
        if o:
            for dx in range(-ow,ow+1):
                for dy in range(-ow,ow+1):
                    if dx or dy: draw.text((pos[0]+dx,pos[1]+dy),t,font=f,fill=o)
        draw.text(pos,t,fill=d["fill"],font=f)
    armor,struct=Image.open(ARMOR_DOT).convert("RGBA"),Image.open(STRUCTURE_DOT).convert("RGBA")
    if mech_image:
        mech_scaled = mech_image.resize(tuple(MECH_IMAGE["size"]))
        img.paste(mech_scaled, tuple(MECH_IMAGE["pos"]), mech_scaled)
    for label,imgdot in [("Armor",armor),("Structure",struct)]:
        d=TEXT_ELEMENTS[label]; c=int(vars_map[label].get() or 0)
        dot=imgdot.resize((d["size"],d["size"]))
        per_row=d.get("per_row",13); row_gap=d.get("row_gap",5)
        for i in range(c):
            row=i//per_row; col=i%per_row
            x=d["pos"][0]+col*d["spacing"]; y=d["pos"][1]+row*(d["size"]+row_gap)
            img.paste(dot,(x,y),dot)
    os.makedirs("output",exist_ok=True)
    out=f"output/{vars_map['name'].get().strip().replace(' ','_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.tiff"
    img.save(out,dpi=(300,300)); messagebox.showinfo("TIFF Saved",f"Saved image:\n{out}")

# --- Refresh helpers for UI fields ---
def refresh_appearance_entries():
    for k in [x for x in TEXT_ELEMENTS if x not in ("Armor","Structure")]:
        d=TEXT_ELEMENTS[k]
        pos_entries[k]["x"].set(str(d["pos"][0])); pos_entries[k]["y"].set(str(d["pos"][1]))
        size_vars[k].set(str(d["size"])); outline_vars[k].set(str(d["outline_width"]))
        fill_vars[k].set(d["fill"]); outline_color_vars[k].set(d["outline"])

def refresh_dot_entries():
    for k in ("Armor","Structure"):
        d=TEXT_ELEMENTS[k]
        dot_pos_entries[k]["x"].set(str(d["pos"][0])); dot_pos_entries[k]["y"].set(str(d["pos"][1]))
        dot_size_vars[k].set(str(d["size"])); dot_spacing_vars[k].set(str(d["spacing"]))
        dot_per_row_vars[k].set(str(d["per_row"])); dot_row_gap_vars[k].set(str(d["row_gap"]))

def refresh_mech_entries():
    mech_pos_entries["x"].set(str(MECH_IMAGE["pos"][0]))
    mech_pos_entries["y"].set(str(MECH_IMAGE["pos"][1]))
    mech_size_vars["w"].set(str(MECH_IMAGE["size"][0]))
    mech_size_vars["h"].set(str(MECH_IMAGE["size"][1]))

# --- Start ---
root.after(100, lambda: load_background(DEFAULT_BG))
root.mainloop()
