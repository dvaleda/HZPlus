import tkinter as tk
from tkinter import ttk

PLAVA_TAMNA   = "#003F7F"
PLAVA_SREDNJA = "#0070C0"
PLAVA_SVIJETLA= "#E8F4FD"
ZLATNA        = "#F5A623"
POZADINA      = "#F4F6F9"
BIJELA        = "#FFFFFF"
TEKST_TAMNI   = "#1C2B3A"
TEKST_SIVKAST = "#5A6A7A"
ZELENA        = "#27AE60"
CRVENA        = "#E74C3C"
RUBA_SIVA     = "#D1D9E0"

F_NASLOV   = ("Segoe UI", 15, "bold")
F_PODNASL  = ("Segoe UI", 11, "bold")
F_NORMALAN = ("Segoe UI", 10)
F_MALI     = ("Segoe UI",  9)
F_IKONA    = ("Segoe UI", 18)

def primjeni_temu():
    """Primjeni globalnu ttk temu na aplikaciju."""
    s = ttk.Style()
    s.theme_use("clam")

    s.configure(".",
        background=POZADINA,
        foreground=TEKST_TAMNI,
        font=F_NORMALAN,
        relief="flat",
    )
    s.configure("TFrame",    background=POZADINA)
    s.configure("TLabel",    background=POZADINA, foreground=TEKST_TAMNI)
    s.configure("TEntry",    fieldbackground=BIJELA, relief="solid",
                             borderwidth=1, padding=4)
    s.configure("TCombobox", fieldbackground=BIJELA, relief="solid",
                             borderwidth=1, padding=4)
    s.configure("TButton",   padding=(10, 6), relief="flat")

    s.configure("Prim.TButton",
        background=PLAVA_TAMNA, foreground=BIJELA,
        font=F_NORMALAN, padding=(12, 7), relief="flat")
    s.map("Prim.TButton",
        background=[("active", PLAVA_SREDNJA), ("pressed", "#002855")])

    s.configure("Sec.TButton",
        background=BIJELA, foreground=PLAVA_TAMNA,
        font=F_NORMALAN, padding=(10, 6), relief="solid",
        borderwidth=1)
    s.map("Sec.TButton",
        background=[("active", PLAVA_SVIJETLA)])

    s.configure("Danger.TButton",
        background=CRVENA, foreground=BIJELA,
        font=F_NORMALAN, padding=(10, 6), relief="flat")
    s.map("Danger.TButton",
        background=[("active", "#C0392B")])

    s.configure("Success.TButton",
        background=ZELENA, foreground=BIJELA,
        font=F_NORMALAN, padding=(12, 7), relief="flat")
    s.map("Success.TButton",
        background=[("active", "#219A52")])

    s.configure("Hdr.TFrame",  background=PLAVA_TAMNA)
    s.configure("Hdr.TLabel",  background=PLAVA_TAMNA,
                foreground=BIJELA, font=F_NASLOV)
    s.configure("HdrSub.TLabel", background=PLAVA_TAMNA,
                foreground="#A8C8F0", font=F_NORMALAN)

    s.configure("TLabelframe",
        background=POZADINA, relief="solid",
        borderwidth=1, bordercolor=RUBA_SIVA)
    s.configure("TLabelframe.Label",
        background=POZADINA, foreground=PLAVA_TAMNA,
        font=F_PODNASL)

    s.configure("Treeview",
        background=BIJELA, fieldbackground=BIJELA,
        foreground=TEKST_TAMNI, rowheight=28,
        font=F_NORMALAN)
    s.configure("Treeview.Heading",
        background=PLAVA_TAMNA, foreground=BIJELA,
        font=("Segoe UI", 9, "bold"), relief="flat", padding=6)
    s.map("Treeview",
        background=[("selected", PLAVA_SREDNJA)],
        foreground=[("selected", BIJELA)])
    s.map("Treeview.Heading",
        background=[("active", PLAVA_SREDNJA)])

    s.configure("TNotebook",      background=POZADINA, borderwidth=0)
    s.configure("TNotebook.Tab",
        background="#DDE4ED", foreground=TEKST_SIVKAST,
        padding=(16, 8), font=F_NORMALAN)
    s.map("TNotebook.Tab",
        background=[("selected", BIJELA)],
        foreground=[("selected", PLAVA_TAMNA)])

    # Traka za pretraživanje
    s.configure("Srch.TEntry",
        fieldbackground=BIJELA, relief="solid",
        borderwidth=1, padding=(6, 5))

def kartica(parent, naslov: str = "", **kw) -> ttk.LabelFrame:
    """Kreira standardni LabelFrame s konzistentnim stilom."""
    return ttk.LabelFrame(parent, text=naslov, padding=10, **kw)

def pretraga_bar(parent, on_pretrazi, placeholder: str = "Pretraži...") -> ttk.Frame:
    """Kreira traku za pretraživanje s live-search."""
    f = ttk.Frame(parent)
    var = tk.StringVar()

    lbl = ttk.Label(f, text="🔍", font=("Segoe UI", 11))
    lbl.pack(side="left", padx=(0, 4))

    entry = ttk.Entry(f, textvariable=var, width=28, style="Srch.TEntry")
    entry.pack(side="left")

    def ocisti():
        var.set("")
        on_pretrazi("")
    ttk.Button(f, text="✕", command=ocisti,
               style="Sec.TButton", width=3).pack(side="left", padx=4)

    var.trace_add("write", lambda *_: on_pretrazi(var.get()))
    return f
