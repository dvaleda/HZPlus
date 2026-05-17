import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List
from ui.tema import (
    BIJELA, PLAVA_TAMNA, PLAVA_SREDNJA,
    ZELENA, CRVENA, TEKST_TAMNI, TEKST_SIVKAST,
    RUBA_SIVA, POZADINA, F_NORMALAN, F_MALI, F_PODNASL
)


class PoljeUnosa(ttk.Frame):
    """Label + Entry kombinirani widget s opcionalnom validacijom."""

    def __init__(self, parent, labela: str, obavezno: bool = False,
                 sirina: int = 26, lozinka: bool = False, **kw):
        super().__init__(parent, **kw)
        tekst = f"{labela} *" if obavezno else labela
        ttk.Label(self, text=tekst, font=F_MALI,
                  foreground=TEKST_SIVKAST).pack(anchor="w", pady=(4, 1))
        self._var = tk.StringVar()
        show = "*" if lozinka else ""
        self._entry = ttk.Entry(self, textvariable=self._var,
                                width=sirina, show=show)
        self._entry.pack(fill="x")
        self._greska_var = tk.StringVar()
        self._greska_lbl = ttk.Label(self, textvariable=self._greska_var,
                                     font=F_MALI, foreground=CRVENA)
        self._greska_lbl.pack(anchor="w")

    def get(self) -> str:
        return self._var.get().strip()

    def set(self, vrijednost: str):
        self._var.set(vrijednost or "")

    def ocisti(self):
        self._var.set("")
        self._greska_var.set("")

    def postavi_gresku(self, poruka: str):
        self._greska_var.set(poruka)

    def ocisti_gresku(self):
        self._greska_var.set("")


class PadajucaLista(ttk.Frame):
    """Label + Combobox kombinirani widget."""

    def __init__(self, parent, labela: str, vrijednosti: list,
                 obavezno: bool = False, sirina: int = 24, **kw):
        super().__init__(parent, **kw)
        tekst = f"{labela} *" if obavezno else labela
        ttk.Label(self, text=tekst, font=F_MALI,
                  foreground=TEKST_SIVKAST).pack(anchor="w", pady=(4, 1))
        self._var = tk.StringVar()
        self._combo = ttk.Combobox(self, textvariable=self._var,
                                   values=vrijednosti, state="readonly",
                                   width=sirina)
        self._combo.pack(fill="x")

    def get(self) -> str:
        return self._var.get()

    def set(self, vrijednost: str):
        self._var.set(vrijednost or "")

    def ocisti(self):
        self._var.set("")

    def postavi_vrijednosti(self, vrijednosti: list):
        self._combo.configure(values=vrijednosti)

    def bind_odabir(self, fn: Callable):
        self._combo.bind("<<ComboboxSelected>>", fn)


class InfoOkvir(ttk.Frame):
    """Okvir za prikaz poruke o uspjehu ili grešci."""

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._var = tk.StringVar()
        self._lbl = ttk.Label(self, textvariable=self._var,
                              font=F_MALI, wraplength=400)
        self._lbl.pack(anchor="w", padx=8, pady=4)
        self._sakrij()

    def postavi_ok(self, poruka: str):
        self._var.set(f"✓  {poruka}")
        self._lbl.configure(foreground=ZELENA,
                            background="#EAF9F0")
        self.configure(relief="solid", borderwidth=1)
        self._lbl.pack()

    def postavi_gresku(self, poruka: str):
        self._var.set(f"✗  {poruka}")
        self._lbl.configure(foreground=CRVENA,
                            background="#FDECEA")
        self.configure(relief="solid", borderwidth=1)
        self._lbl.pack()

    def ocisti(self):
        self._sakrij()

    def _sakrij(self):
        self._var.set("")
        self.configure(relief="flat", borderwidth=0)


class Tablica(ttk.Frame):
    """Treeview s klizačem i standardnim postavkama."""

    def __init__(self, parent, stupci: dict, visina: int = 10,
                 na_odabir: Optional[Callable] = None,
                 na_dvostruki_klik: Optional[Callable] = None, **kw):
        """
        stupci: {"kljuc": ("Naziv", sirina, "poravnanje"), ...}
        poravnanje: "w" (lijevo), "center", "e" (desno)
        """
        super().__init__(parent, **kw)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            self,
            columns=list(stupci.keys()),
            show="headings",
            height=visina,
            selectmode="browse"
        )
        for k, info in stupci.items():
            naziv, sirina = info[0], info[1]
            poravnanje = info[2] if len(info) > 2 else "w"
            self._tree.heading(k, text=naziv,
                               command=lambda c=k: self._sortiraj(c))
            self._tree.column(k, width=sirina, anchor=poravnanje,
                              stretch=(sirina > 120))

        sv = ttk.Scrollbar(self, orient="vertical",
                           command=self._tree.yview)
        sh = ttk.Scrollbar(self, orient="horizontal",
                           command=self._tree.xview)
        self._tree.configure(yscrollcommand=sv.set,
                             xscrollcommand=sh.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        sv.grid(row=0, column=1, sticky="ns")
        sh.grid(row=1, column=0, sticky="ew")

        if na_odabir:
            self._tree.bind("<<TreeviewSelect>>", na_odabir)
        if na_dvostruki_klik:
            self._tree.bind("<Double-1>", na_dvostruki_klik)

        self._sort_stupac = None
        self._sort_obrnuto = False

    def popuni(self, redovi: List[tuple], tagovi: Optional[List[str]] = None):
        """Briše stare redove i dodaje nove. Svaki red je tuple vrijednosti."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        for i, red in enumerate(redovi):
            tag = tagovi[i] if tagovi and i < len(tagovi) else ""
            self._tree.insert("", "end", values=red, tags=(tag,))

    def popuni_s_id(self, redovi: List[tuple]):
        """Redovi su (id, v1, v2, ...) — id se koristi kao iid."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        for red in redovi:
            iid = str(red[0])
            self._tree.insert("", "end", iid=iid, values=red[1:])

    def odabrani_id(self) -> Optional[int]:
        sel = self._tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def odabrani_vrijednosti(self) -> Optional[tuple]:
        sel = self._tree.selection()
        if not sel:
            return None
        return self._tree.item(sel[0], "values")

    def postavi_tag_boju(self, tag: str, pozadina: str, tekst: str = ""):
        self._tree.tag_configure(tag, background=pozadina,
                                 foreground=tekst or TEKST_TAMNI)

    def _sortiraj(self, stupac: str):
        if self._sort_stupac == stupac:
            self._sort_obrnuto = not self._sort_obrnuto
        else:
            self._sort_stupac = stupac
            self._sort_obrnuto = False
        podaci = [(self._tree.set(k, stupac), k)
                  for k in self._tree.get_children("")]
        podaci.sort(reverse=self._sort_obrnuto)
        for i, (_, k) in enumerate(podaci):
            self._tree.move(k, "", i)