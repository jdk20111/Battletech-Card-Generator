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
NUDGE_STEP = 5

bg_image = preview_image = photo_preview = None

# --- Default field setup ---
TEXT_ELEMENTS = {
    "title":  {"pos":[80,40],"size":120,"fill":"#efe31c","outline":"#930000","outline_width":6,"text":""},
    "name":   {"pos":[80,145],"size":180,"fill":"#930000","outline":"#efe31c","outline_width":6,"text":""},
    "MV":     {"pos":[1020,480],"size":120,"fill":"#000000","outline":"#ffffff","outline_width":4,"text":""},
    "SZ":     {"pos":[260,480],"size":120,"fill":"#000000","outline":"#ffffff","outline_width":4,"text":""},
    "TMM":    {"pos":[670,480],"size":120,"fill":"#000000","outline":"#ffffff","outline_width":4,"text":""},
    "short":  {"pos":[265,740],"size":120,"fill":"#000000","outline":"#ffffff","outline_width":4,"text":""},
    "medium": {"pos":[605,740],"size":120,"fill":"#000000","outline":"#ffffff","outline_width":4,"text":""},
    "long":   {"pos":[985,740],"size":120,"fill":"#000000","outline":"#ffffff","outline_width":4,"text":""},
    "PV":     {"pos":[1785,10],"size":140,"fill":"#930000","outline":"#efe31c","outline_width":4,"text":""},
    "Armor":     {"count":0,"pos":[190,945],"size":60,"spacing":61},
    "Structure": {"count":0,"pos":[185,1095],"size":60,"spacing":61},
}

pos_entries, size_vars, outline_vars, fill_vars, outline_color_vars = {}, {}, {}, {}, {}
dot_pos_entries, dot_size_vars, dot_spacing_vars = {}, {}, {}

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

# --- Draw preview ---
def draw_preview():
    global preview_image, photo_preview
    if not bg_image: return
    img = bg_image.copy().resize((int(OUTPUT_SIZE[0]*PREVIEW_SCALE), int(OUTPUT_SIZE[1]*PREVIEW_SCALE)))
    draw = ImageDraw.Draw(img); scale = PREVIEW_SCALE
    # text
    for key,var in vars_map.items():
        if key in ("Armor","Structure"): continue
        t = var.get().upper(); TEXT_ELEMENTS[key]["text"]=t; d=TEXT_ELEMENTS[key]
        pos=(d["pos"][0]*scale,d["pos"][1]*scale); f=load_font(int(d["size"]*scale))
        ow=max(1,int(d["outline_width"]*scale)); o=d["outline"]
        if o:
            for dx in range(-ow,ow+1):
                for dy in range(-ow,ow+1):
                    if dx or dy: draw.text((pos[0]+dx,pos[1]+dy),t,font=f,fill=o)
        draw.text(pos,t,fill=d["fill"],font=f)
    # dots
    try:
        armor,struct = Image.open(ARMOR_DOT).convert("RGBA"),Image.open(STRUCTURE_DOT).convert("RGBA")
        for label,imgdot in [("Armor",armor),("Structure",struct)]:
            d=TEXT_ELEMENTS[label]; c=int(vars_map[label].get() or 0)
            s=int(d["size"]); scaled=imgdot.resize((int(s*scale),int(s*scale)))
            for i in range(c):
                x=int((d["pos"][0]+i*d["spacing"])*scale); y=int(d["pos"][1]*scale)
                img.paste(scaled,(x,y),scaled)
    except Exception as e: print("Dot render error:",e)
    preview_image=img; photo_preview=ImageTk.PhotoImage(img)
    preview_label.config(image=photo_preview); preview_label.image=photo_preview

# --- Background ---
def load_background(p=None):
    global bg_image
    path=p if p and os.path.exists(p) else filedialog.askopenfilename(
        title="Select Background",filetypes=[("Images","*.png;*.jpg;*.jpeg;*.tif;*.tiff")])
    if not path: return
    bg_image=Image.open(path).convert("RGBA").resize(OUTPUT_SIZE); draw_preview()
    status_label.config(text=f"Loaded background: {os.path.basename(path)}")

# --- Save / Load JSON ---
def save_settings():
    os.makedirs(SAVE_DIR,exist_ok=True)
    title=vars_map["title"].get().strip().upper() or "UNTITLED"
    name=vars_map["name"].get().strip().upper() or "CARD"
    path=os.path.join(SAVE_DIR,f"{title}_{name}.json")
    for k in TEXT_ELEMENTS:
        if k in vars_map:
            if k not in ("Armor","Structure"): TEXT_ELEMENTS[k]["text"]=vars_map[k].get().upper()
            else: TEXT_ELEMENTS[k]["count"]=int(vars_map[k].get() or 0)
    with open(path,"w") as f: json.dump(TEXT_ELEMENTS,f,indent=4)
    messagebox.showinfo("Settings Saved",f"Saved to:\n{path}")

def load_settings():
    file=filedialog.askopenfilename(title="Load Settings",filetypes=[("JSON Files","*.json")],initialdir=SAVE_DIR)
    if not file: return
    try:
        with open(file) as f: data=json.load(f)
        for k,v in data.items():
            if k in TEXT_ELEMENTS:
                TEXT_ELEMENTS[k].update(v)
                if k in vars_map:
                    if k in ("Armor","Structure"): vars_map[k].set(str(v.get("count",0)))
                    else: vars_map[k].set(v.get("text",""))
        refresh_appearance_entries(); refresh_dot_entries(); draw_preview()
        status_label.config(text=f"Loaded: {os.path.basename(file)}")
    except Exception as e: messagebox.showerror("Load Failed",str(e))

# --- Save Final TIFF ---
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
    try:
        armor,struct=Image.open(ARMOR_DOT).convert("RGBA"),Image.open(STRUCTURE_DOT).convert("RGBA")
        for label,imgdot in [("Armor",armor),("Structure",struct)]:
            d=TEXT_ELEMENTS[label]; c=int(vars_map[label].get() or 0)
            dot=imgdot.resize((d["size"],d["size"]))
            for i in range(c):
                x=d["pos"][0]+i*d["spacing"]; y=d["pos"][1]; img.paste(dot,(x,y),dot)
    except Exception as e: print("Dot paste error:",e)
    os.makedirs("output",exist_ok=True)
    out=f"output/{vars_map['name'].get().strip().replace(' ','_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.tiff"
    img.save(out,dpi=(300,300)); messagebox.showinfo("TIFF Saved",f"Saved image:\n{out}")

# --- Helpers ---
def nudge_text(k,dx,dy):
    TEXT_ELEMENTS[k]["pos"][0]+=dx; TEXT_ELEMENTS[k]["pos"][1]+=dy
    pos_entries[k]["x"].set(str(TEXT_ELEMENTS[k]["pos"][0]))
    pos_entries[k]["y"].set(str(TEXT_ELEMENTS[k]["pos"][1])); draw_preview()
def nudge_dots(k,dx,dy):
    TEXT_ELEMENTS[k]["pos"][0]+=dx; TEXT_ELEMENTS[k]["pos"][1]+=dy
    dot_pos_entries[k]["x"].set(str(TEXT_ELEMENTS[k]["pos"][0]))
    dot_pos_entries[k]["y"].set(str(TEXT_ELEMENTS[k]["pos"][1])); draw_preview()
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

# --- GUI Layout ---
root=tk.Tk(); root.title("Battletech Card Generator")
main=tk.Frame(root); main.pack(fill=tk.BOTH,expand=True)
left=tk.Frame(main); left.pack(side=tk.LEFT,fill=tk.Y,padx=10,pady=10)

tk.Label(left,text="Stats:",font=("Arial",10,"bold")).pack(anchor="w",pady=4)
vars_map={k:tk.StringVar() for k in TEXT_ELEMENTS}

# Display labels in proper case (with special cases)
display_labels={
    "title":"Title","name":"Name","MV":"MV","SZ":"Size","TMM":"TMM",
    "short":"Short","medium":"Medium","long":"Long","PV":"PV",
    "Armor":"Armor","Structure":"Structure"
}

# Arrange fields in two columns
fields_frame=tk.Frame(left); fields_frame.pack(anchor="w",fill=tk.X)
keys=list(TEXT_ELEMENTS.keys())
numeric_fields={"MV","SZ","TMM","short","medium","long","PV"}
for i,lbl in enumerate(keys):
    f=tk.Frame(fields_frame)
    r=i//2; c=i%2
    f.grid(row=r,column=c,sticky="w",padx=5,pady=2)
    tk.Label(f,text=display_labels.get(lbl,lbl),width=8).pack(side=tk.LEFT)
    var=vars_map[lbl]
    if lbl in ("Armor","Structure") or lbl in numeric_fields:
        spin=Spinbox(f,from_=0,to=50,width=5,textvariable=var,command=draw_preview)
        spin.pack(side=tk.LEFT)
    else:
        e=tk.Entry(f,textvariable=var,width=14)
        e.pack(side=tk.LEFT)
    var.set(str(TEXT_ELEMENTS[lbl].get("text","")) if lbl not in ("Armor","Structure") else str(TEXT_ELEMENTS[lbl]["count"]))
    var.trace_add("write",lambda *_,:draw_preview())

# --- Appearance Section ---
tk.Label(left,text="\nAppearance",font=("Arial",10,"bold")).pack(anchor="w")
for k in [x for x in TEXT_ELEMENTS if x not in ("Armor","Structure")]:
    d=TEXT_ELEMENTS[k]; f=tk.Frame(left); f.pack(anchor="w",pady=3)
    tk.Label(f,text=display_labels.get(k,k),width=7).pack(side=tk.LEFT)
    for sym,dx,dy in [("←",-NUDGE_STEP,0),("↑",0,-NUDGE_STEP),("↓",0,NUDGE_STEP),("→",NUDGE_STEP,0)]:
        tk.Button(f,text=sym,width=2,command=lambda key=k,x=dx,y=dy:nudge_text(key,x,y)).pack(side=tk.LEFT)
    # X/Y
    tk.Label(f,text="X:").pack(side=tk.LEFT)
    xv=tk.StringVar(value=str(d["pos"][0])); tk.Entry(f,textvariable=xv,width=5).pack(side=tk.LEFT)
    tk.Label(f,text="Y:").pack(side=tk.LEFT)
    yv=tk.StringVar(value=str(d["pos"][1])); tk.Entry(f,textvariable=yv,width=5).pack(side=tk.LEFT)
    pos_entries[k]={"x":xv,"y":yv}
    xv.trace_add("write",lambda *_,key=k,v=xv:(TEXT_ELEMENTS[key]["pos"].__setitem__(0,int(v.get() or 0)),draw_preview()))
    yv.trace_add("write",lambda *_,key=k,v=yv:(TEXT_ELEMENTS[key]["pos"].__setitem__(1,int(v.get() or 0)),draw_preview()))
    # Size / Outline width
    tk.Label(f,text="Size:").pack(side=tk.LEFT)
    sv=tk.StringVar(value=str(d["size"])); tk.Entry(f,textvariable=sv,width=4).pack(side=tk.LEFT)
    size_vars[k]=sv; sv.trace_add("write",lambda *_,key=k,v=sv:(TEXT_ELEMENTS[key].__setitem__("size",int(v.get() or 0)),draw_preview()))
    tk.Label(f,text="O:").pack(side=tk.LEFT)
    ow=tk.StringVar(value=str(d["outline_width"])); tk.Entry(f,textvariable=ow,width=4).pack(side=tk.LEFT)
    outline_vars[k]=ow; ow.trace_add("write",lambda *_,key=k,v=ow:(TEXT_ELEMENTS[key].__setitem__("outline_width",int(v.get() or 0)),draw_preview()))
    # Colors
    tk.Label(f,text="Fill:").pack(side=tk.LEFT)
    fc=tk.StringVar(value=d["fill"]); ef=tk.Entry(f,textvariable=fc,width=8); ef.pack(side=tk.LEFT)
    tk.Button(f,text="🎨",command=lambda key=k,v=fc:(v.set(colorchooser.askcolor()[1] or v.get()),TEXT_ELEMENTS[key].__setitem__("fill",v.get()),draw_preview())).pack(side=tk.LEFT)
    fill_vars[k]=fc; fc.trace_add("write",lambda *_,key=k,v=fc:(TEXT_ELEMENTS[key].__setitem__("fill",v.get()),draw_preview()))
    tk.Label(f,text="Out:").pack(side=tk.LEFT)
    oc=tk.StringVar(value=d["outline"]); eo=tk.Entry(f,textvariable=oc,width=8); eo.pack(side=tk.LEFT)
    tk.Button(f,text="🎨",command=lambda key=k,v=oc:(v.set(colorchooser.askcolor()[1] or v.get()),TEXT_ELEMENTS[key].__setitem__("outline",v.get()),draw_preview())).pack(side=tk.LEFT)
    outline_color_vars[k]=oc; oc.trace_add("write",lambda *_,key=k,v=oc:(TEXT_ELEMENTS[key].__setitem__("outline",v.get()),draw_preview()))

# --- Armor / Structure Appearance ---
tk.Label(left,text="\nArmor / Structure Appearance",font=("Arial",10,"bold")).pack(anchor="w",pady=4)
for k in ("Armor","Structure"):
    d=TEXT_ELEMENTS[k]; f=tk.Frame(left); f.pack(anchor="w",pady=3)
    tk.Label(f,text=k,width=7).pack(side=tk.LEFT)
    for sym,dx,dy in [("←",-NUDGE_STEP,0),("↑",0,-NUDGE_STEP),("↓",0,NUDGE_STEP),("→",NUDGE_STEP,0)]:
        tk.Button(f,text=sym,width=2,command=lambda key=k,x=dx,y=dy:nudge_dots(key,x,y)).pack(side=tk.LEFT)
    for lbl,field in [("X","x"),("Y","y"),("Size","size"),("Sp","spacing")]:
        tk.Label(f,text=f"{lbl}:").pack(side=tk.LEFT)
        val=str(d["pos"][0] if field=="x" else d["pos"][1] if field=="y" else d[field])
        v=tk.StringVar(value=val); tk.Entry(f,textvariable=v,width=5).pack(side=tk.LEFT)
        if field=="x": dot_pos_entries[k]={"x":v}
        elif field=="y": dot_pos_entries[k]["y"]=v
        elif field=="size": dot_size_vars[k]=v
        elif field=="spacing": dot_spacing_vars[k]=v
        v.trace_add("write",lambda *_,key=k,f=field,var=v:(TEXT_ELEMENTS[key]["pos"].__setitem__(0,int(var.get() or 0)) if f=="x"
            else TEXT_ELEMENTS[key]["pos"].__setitem__(1,int(var.get() or 0)) if f=="y"
            else TEXT_ELEMENTS[key].__setitem__(f,int(var.get() or 0)),draw_preview()))

# --- Buttons / Preview ---
right=tk.Frame(main); right.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True,padx=10,pady=10)
preview_label=tk.Label(right,bg="#222"); preview_label.pack(fill=tk.BOTH,expand=True)
bottom=tk.Frame(root); bottom.pack(side=tk.BOTTOM,fill=tk.X,pady=5)
tk.Button(bottom,text="Load Background",command=lambda:load_background(DEFAULT_BG)).pack(side=tk.LEFT,padx=10)
tk.Button(bottom,text="Save Settings",command=save_settings).pack(side=tk.LEFT,padx=10)
tk.Button(bottom,text="Load Settings",command=load_settings).pack(side=tk.LEFT,padx=10)
tk.Button(bottom,text="Save Final TIFF",command=save_final).pack(side=tk.LEFT,padx=10)
status_label=tk.Label(root,text=""); status_label.pack(pady=3)
root.after(100,lambda:load_background(DEFAULT_BG))
root.mainloop()
