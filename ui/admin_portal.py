import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List

from models.entities import (
    Vlak, TipVlaka, Korisnik, TipKorisnika, Popust, Stanica
)
from bll.services import (
    VlakService, KorisnikService, PopustService,
    StanicaService, KartaService, ValidationError
)
from ui.theme import (
    PLAVA_TAMNA, PLAVA_SREDNJA, BIJELA, POZADINA,
    TEKST_TAMNI, TEKST_SIVKAST, ZELENA, CRVENA, RUBA_SIVA,
    F_NASLOV, F_PODNASL, F_NORMALAN, F_MALI,
    kartica, pretraga_bar
)
from ui.komponente import Tablica, InfoOkvir, PoljeUnosa, PadajucaLista


class AdminPortal(ttk.Frame):

    def __init__(self, parent,
                 vlak_svc: VlakService,
                 korisnik_svc: KorisnikService,
                 popust_svc: PopustService,
                 stanica_svc: StanicaService,
                 karta_svc: KartaService,
                 stanice: list,
                 na_odjava: callable,
                 **kw):
        super().__init__(parent, **kw)
        self._vsvc  = vlak_svc
        self._ksvc  = korisnik_svc
        self._psvc  = popust_svc
        self._ssvc  = stanica_svc
        self._kasvc = karta_svc
        self._stanice = stanice
        self._na_odjava = na_odjava
        self._gradi()

    def _gradi(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        top = tk.Frame(self, bg=PLAVA_TAMNA, height=52)
        top.grid(row=0, column=0, sticky="ew")
        top.pack_propagate(False)
        tk.Label(top, text="🚆  HŽPlus  —  Admin",
                 bg=PLAVA_TAMNA, fg=BIJELA,
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=16)
        tk.Label(top, text="Upravljački panel djelatnika",
                 bg=PLAVA_TAMNA, fg="#A8C8F0",
                 font=F_MALI).pack(side="left", padx=4)
        tk.Button(top, text="← Natrag na portal",
                  bg=PLAVA_TAMNA, fg="#A8C8F0",
                  font=F_MALI, relief="flat", bd=0,
                  cursor="hand2",
                  command=self._na_odjava).pack(side="right", padx=16)

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew")

        t1 = ttk.Frame(nb)
        nb.add(t1, text="  🚂  Vlakovi  ")
        VlakoviTab(t1, self._vsvc, self._kasvc,
                   self._stanice).pack(fill="both", expand=True)

        t2 = ttk.Frame(nb)
        nb.add(t2, text="  👥  Korisnici  ")
        KorisniciTab(t2, self._ksvc).pack(fill="both", expand=True)

        t3 = ttk.Frame(nb)
        nb.add(t3, text="  🏷️  Popusti  ")
        PopustiTab(t3, self._psvc).pack(fill="both", expand=True)

        t4 = ttk.Frame(nb)
        nb.add(t4, text="  🚉  Stanice  ")
        StaniceTab(t4, self._ssvc).pack(fill="both", expand=True)


# Master-Detail forma za vlakove
class VlakoviTab(ttk.Frame):

    def __init__(self, parent, vsvc: VlakService,
                 kasvc: KartaService, stanice: list, **kw):
        super().__init__(parent, **kw)
        self._vsvc   = vsvc
        self._kasvc  = kasvc
        self._stanice = stanice
        self._odabran: Optional[Vlak] = None
        self._vlakovi: List[Vlak] = []
        self._gradi()
        self._ucitaj()

    def _gradi(self):
        self.columnconfigure(0, weight=1)
        for r in (0, 2): self.rowconfigure(r, weight=1)

        mf = kartica(self, "Vlakovi — popis")
        mf.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
        mf.columnconfigure(0, weight=1)
        mf.rowconfigure(1, weight=1)

        bar = ttk.Frame(mf)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        pretraga_bar(bar, self._pretrazi).pack(side="left")
        tk.Button(bar, text="➕ Novi",  bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2",
                  command=self._novi).pack(side="right", padx=2)
        tk.Button(bar, text="✏️ Uredi", bg="#0070C0", fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2",
                  command=self._uredi).pack(side="right", padx=2)
        tk.Button(bar, text="🗑 Briši", bg=CRVENA, fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2",
                  command=self._obrisi).pack(side="right", padx=2)

        stupci = {
            "broj":   ("Br. vlaka", 85,  "center"),
            "tip":    ("Tip",       90,  "center"),
            "od":     ("Polazište", 145, "w"),
            "do":     ("Odredište", 145, "w"),
            "pol":    ("Polazak",   65,  "center"),
            "dol":    ("Dolazak",   65,  "center"),
            "cijena": ("Cijena €", 85,  "e"),
            "kap":    ("Kap.",      55,  "center"),
        }
        self._tbl = Tablica(mf, stupci, visina=7,
                            na_odabir=self._na_odabir)
        self._tbl.grid(row=1, column=0, sticky="nsew")

        ef = kartica(self, "Detalji vlaka")
        ef.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        self._gradi_edit(ef)

        df = kartica(self, "Karte za odabrani vlak")
        df.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 6))
        df.columnconfigure(0, weight=1)
        df.rowconfigure(0, weight=1)

        kstupci = {
            "id":       ("ID",         42, "center"),
            "korisnik": ("Korisnik",   160, "w"),
            "datum":    ("Datum puta", 100, "center"),
            "sjedalo":  ("Sjedalo",    75, "center"),
            "cijena":   ("Cijena €",   85, "e"),
            "popust":   ("Pop. %",     55, "center"),
            "status":   ("Status",     85, "center"),
        }
        self._tbl_karte = Tablica(df, kstupci, visina=5)
        self._tbl_karte.grid(row=0, column=0, sticky="nsew")

    def _gradi_edit(self, p):
        p.columnconfigure((1, 3, 5), weight=1)

        ttk.Label(p, text="Broj vlaka *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=0, column=0, sticky="w", padx=4, pady=3)
        self._v_broj = tk.StringVar()
        ttk.Entry(p, textvariable=self._v_broj, width=12).grid(
            row=0, column=1, sticky="ew", padx=4)

        ttk.Label(p, text="Tip *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=0, column=2, sticky="w", padx=4)
        self._v_tip = tk.StringVar()
        ttk.Combobox(p, textvariable=self._v_tip,
                     values=[t.value for t in TipVlaka],
                     state="readonly", width=13).grid(
            row=0, column=3, sticky="ew", padx=4)

        ttk.Label(p, text="Kapacitet *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=0, column=4, sticky="w", padx=4)
        self._v_kap = tk.StringVar()
        ttk.Entry(p, textvariable=self._v_kap, width=7).grid(
            row=0, column=5, sticky="ew", padx=4)

        ttk.Label(p, text="Polazišna stanica *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=1, column=0, sticky="w", padx=4, pady=3)
        self._v_pol = tk.StringVar()
        s_vals = [f"{s.id}: {s.naziv}" for s in self._stanice]
        self._cb_pol = ttk.Combobox(p, textvariable=self._v_pol,
                                     values=s_vals, state="readonly", width=24)
        self._cb_pol.grid(row=1, column=1, columnspan=2, sticky="ew", padx=4)

        ttk.Label(p, text="Odredišna stanica *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=1, column=3, sticky="w", padx=4)
        self._v_odred = tk.StringVar()
        self._cb_odred = ttk.Combobox(p, textvariable=self._v_odred,
                                       values=s_vals, state="readonly", width=24)
        self._cb_odred.grid(row=1, column=4, columnspan=2, sticky="ew", padx=4)

        ttk.Label(p, text="Polazak (HH:MM) *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=2, column=0, sticky="w", padx=4, pady=3)
        self._v_vpol = tk.StringVar()
        ttk.Entry(p, textvariable=self._v_vpol, width=7).grid(
            row=2, column=1, sticky="ew", padx=4)

        ttk.Label(p, text="Dolazak (HH:MM) *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=2, column=2, sticky="w", padx=4)
        self._v_vdol = tk.StringVar()
        ttk.Entry(p, textvariable=self._v_vdol, width=7).grid(
            row=2, column=3, sticky="ew", padx=4)

        ttk.Label(p, text="Cijena (€) *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=2, column=4, sticky="w", padx=4)
        self._v_cijena = tk.StringVar()
        ttk.Entry(p, textvariable=self._v_cijena, width=9).grid(
            row=2, column=5, sticky="ew", padx=4)

        bf = ttk.Frame(p)
        bf.grid(row=3, column=0, columnspan=6, pady=6)
        tk.Button(bf, text="💾 Spremi", bg=ZELENA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0, padx=10, pady=6,
                  cursor="hand2", command=self._spremi).pack(side="left", padx=4)
        tk.Button(bf, text="✖ Odustani", bg=BIJELA, fg=TEKST_TAMNI,
                  font=F_NORMALAN, relief="solid", bd=1, padx=8, pady=5,
                  cursor="hand2", command=self._reset).pack(side="left", padx=4)

        self._info_edit = InfoOkvir(p)
        self._info_edit.grid(row=4, column=0, columnspan=6, sticky="ew")

    def _ucitaj(self, upit=""):
        self._vlakovi = (self._vsvc.pretrazi(upit)
                         if upit else self._vsvc.dohvati_sve())
        redovi = []
        for v in self._vlakovi:
            redovi.append((
                v.id,
                v.broj_vlaka,
                v.tip.value if isinstance(v.tip, TipVlaka) else v.tip,
                v.naziv_polazisne or "",
                v.naziv_odredisne or "",
                v.vrijeme_polaska, v.vrijeme_dolaska,
                f"{v.cijena_kn:.2f}", v.kapacitet,
            ))
        self._tbl.popuni_s_id(redovi)

    def _pretrazi(self, u): self._ucitaj(u)

    def _na_odabir(self, _=None):
        vid = self._tbl.odabrani_id()
        if vid is None: return
        self._odabran = next((v for v in self._vlakovi if v.id == vid), None)
        if self._odabran:
            self._popuni_formu(self._odabran)
            self._ucitaj_karte(vid)

    def _popuni_formu(self, v: Vlak):
        self._v_broj.set(v.broj_vlaka)
        self._v_tip.set(v.tip.value if isinstance(v.tip, TipVlaka) else v.tip)
        self._v_kap.set(str(v.kapacitet))
        self._v_vpol.set(v.vrijeme_polaska)
        self._v_vdol.set(v.vrijeme_dolaska)
        self._v_cijena.set(str(v.cijena_kn))
        for s in self._stanice:
            if s.id == v.id_polazisne_stanice:
                self._v_pol.set(f"{s.id}: {s.naziv}")
            if s.id == v.id_odredisne_stanice:
                self._v_odred.set(f"{s.id}: {s.naziv}")
        self._info_edit.ocisti()

    def _ucitaj_karte(self, vlak_id: int):
        try:
            karte = [k for k in self._kasvc.dohvati_sve()
                     if k.id_vlaka == vlak_id]
        except Exception:
            karte = []
        redovi = []
        for k in karte:
            redovi.append((
                k.id,
                k.korisnik_ime or "",
                k.datum_putovanja,
                k.broj_sjedala or "—",
                f"{k.cijena_placena:.2f}",
                f"{k.popust_postotak:.0f}%",
                k.status.value if hasattr(k.status, "value") else k.status,
            ))
        self._tbl_karte.popuni_s_id(redovi)

    def _novi(self):
        self._odabran = None
        for v in [self._v_broj, self._v_tip, self._v_kap,
                  self._v_pol, self._v_odred,
                  self._v_vpol, self._v_vdol, self._v_cijena]:
            v.set("")
        self._info_edit.ocisti()

    def _uredi(self):
        if not self._odabran:
            messagebox.showwarning("Upozorenje", "Odaberite vlak za uređivanje.")

    def _obrisi(self):
        if not self._odabran:
            messagebox.showwarning("Upozorenje", "Odaberite vlak za brisanje.")
            return
        if not messagebox.askyesno(
                "Brisanje", f"Obrisati vlak {self._odabran.broj_vlaka}?"):
            return
        try:
            self._vsvc.obrisi(self._odabran.id)
            self._odabran = None
            self._ucitaj()
            self._novi()
        except Exception as e:
            messagebox.showerror("Greška", str(e))

    def _spremi(self):
        self._info_edit.ocisti()
        try:
            pol_s = self._v_pol.get()
            od_s  = self._v_odred.get()
            if not pol_s or not od_s:
                raise ValidationError("Odaberite polazišnu i odredišnu stanicu.")
            pol_id  = int(pol_s.split(":")[0])
            odred_id = int(od_s.split(":")[0])
            tip_s = self._v_tip.get()
            if not tip_s:
                raise ValidationError("Odaberite tip vlaka.")
            tip = next(t for t in TipVlaka if t.value == tip_s)
            vlak = Vlak(
                id=self._odabran.id if self._odabran else None,
                broj_vlaka=self._v_broj.get(),
                tip=tip,
                kapacitet=int(self._v_kap.get() or 0),
                id_polazisne_stanice=pol_id,
                id_odredisne_stanice=odred_id,
                vrijeme_polaska=self._v_vpol.get(),
                vrijeme_dolaska=self._v_vdol.get(),
                cijena_kn=float(self._v_cijena.get() or 0),
            )
            self._vsvc.spremi(vlak)
            self._info_edit.postavi_ok(
                f"Vlak {vlak.broj_vlaka} uspješno spremljen.")
            self._ucitaj()
        except ValidationError as ve:
            self._info_edit.postavi_gresku(str(ve))
        except (ValueError, StopIteration):
            self._info_edit.postavi_gresku(
                "Kapacitet mora biti cijeli broj; cijena decimalni.")
        except Exception as e:
            self._info_edit.postavi_gresku(str(e))

    def _reset(self):
        if self._odabran:
            self._popuni_formu(self._odabran)
        else:
            self._novi()


# Šifrarnik korisnika
class KorisniciTab(ttk.Frame):
    def __init__(self, parent, svc: KorisnikService, **kw):
        super().__init__(parent, **kw)
        self._svc = svc
        self._odabran: Optional[Korisnik] = None
        self._lista: List[Korisnik] = []
        self._gradi()
        self._ucitaj()

    def _gradi(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        lf = kartica(self, "Korisnici")
        lf.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(1, weight=1)

        bar = ttk.Frame(lf)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        pretraga_bar(bar, self._pretrazi).pack(side="left")
        tk.Button(bar, text="🗑 Briši", bg=CRVENA, fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2",
                  command=self._obrisi).pack(side="right", padx=2)
        tk.Button(bar, text="➕ Novi", bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2",
                  command=self._novi).pack(side="right", padx=2)

        stupci = {
            "id":      ("ID",          42,  "center"),
            "ime":     ("Ime",         90,  "w"),
            "prezime": ("Prezime",     100, "w"),
            "email":   ("Email",       170, "w"),
            "tip":     ("Tip",         110, "center"),
            "oib":     ("OIB",         100, "center"),
        }
        self._tbl = Tablica(lf, stupci, visina=22,
                            na_odabir=self._na_odabir)
        self._tbl.grid(row=1, column=0, sticky="nsew")

        ff = kartica(self, "Detalji korisnika")
        ff.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        ff.columnconfigure(1, weight=1)
        self._gradi_formu(ff)

    def _gradi_formu(self, p):
        polja = [
            ("Ime *",                      "_vi"),
            ("Prezime *",                  "_vp"),
            ("Email *",                    "_ve"),
            ("Lozinka (prazno = zadrži)",  "_vl"),
            ("OIB * (11 znamenki)",        "_vo"),
            ("Datum rođenja * YYYY-MM-DD", "_vd"),
            ("Telefon",                    "_vt"),
        ]
        for i, (lbl, attr) in enumerate(polja):
            ttk.Label(p, text=lbl, font=F_MALI,
                      foreground=TEKST_SIVKAST).grid(
                row=i, column=0, sticky="w", padx=4, pady=3)
            var = tk.StringVar()
            setattr(self, attr, var)
            show = "*" if "ozinka" in lbl else ""
            ttk.Entry(p, textvariable=var, width=26,
                      show=show).grid(row=i, column=1, sticky="ew", padx=4, pady=3)

        row = len(polja)
        ttk.Label(p, text="Tip korisnika *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=row, column=0, sticky="w", padx=4, pady=3)
        self._vtip = tk.StringVar()
        ttk.Combobox(p, textvariable=self._vtip,
                     values=[t.value for t in TipKorisnika],
                     state="readonly", width=24).grid(
            row=row, column=1, sticky="ew", padx=4, pady=3)

        bf = ttk.Frame(p)
        bf.grid(row=row + 1, column=0, columnspan=2, pady=10)
        tk.Button(bf, text="💾 Spremi", bg=ZELENA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0, padx=10, pady=6,
                  cursor="hand2", command=self._spremi).pack(side="left", padx=4)
        tk.Button(bf, text="✖ Odustani", bg=BIJELA, fg=TEKST_TAMNI,
                  font=F_NORMALAN, relief="solid", bd=1, padx=8, pady=5,
                  cursor="hand2", command=self._reset).pack(side="left", padx=4)
        tk.Button(bf, text="🆕 Novi", bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0, padx=10, pady=6,
                  cursor="hand2", command=self._novi).pack(side="left", padx=4)

        self._info = InfoOkvir(p)
        self._info.grid(row=row + 2, column=0, columnspan=2,
                         sticky="ew", pady=5)

    def _ucitaj(self, upit=""):
        self._lista = (self._svc.pretrazi(upit)
                       if upit else self._svc.dohvati_sve())
        redovi = [(k.id, k.ime, k.prezime, k.email,
                   k.tip.value if isinstance(k.tip, TipKorisnika) else k.tip,
                   k.oib)
                  for k in self._lista]
        self._tbl.popuni_s_id(redovi)

    def _pretrazi(self, u): self._ucitaj(u)

    def _na_odabir(self, _=None):
        kid = self._tbl.odabrani_id()
        if kid is None: return
        self._odabran = next((k for k in self._lista if k.id == kid), None)
        if self._odabran:
            self._popuni_formu(self._odabran)

    def _popuni_formu(self, k: Korisnik):
        self._vi.set(k.ime); self._vp.set(k.prezime)
        self._ve.set(k.email); self._vl.set("")
        self._vo.set(k.oib); self._vd.set(k.datum_rodenja)
        self._vt.set(k.telefon or "")
        self._vtip.set(k.tip.value if isinstance(k.tip, TipKorisnika) else k.tip)
        self._info.ocisti()

    def _novi(self):
        self._odabran = None
        self._tbl._tree.selection_remove(self._tbl._tree.selection())
        for v in [self._vi, self._vp, self._ve, self._vl,
                  self._vo, self._vd, self._vt, self._vtip]:
            v.set("")
        self._info.ocisti()

    def _obrisi(self):
        if not self._odabran:
            messagebox.showwarning("Upozorenje", "Odaberite korisnika.")
            return
        if not messagebox.askyesno(
                "Brisanje", f"Obrisati '{self._odabran.puno_ime}'?"):
            return
        try:
            self._svc.obrisi(self._odabran.id)
            self._odabran = None
            self._ucitaj()
            self._novi()
        except Exception as e:
            messagebox.showerror("Greška", str(e))

    def _spremi(self):
        self._info.ocisti()
        try:
            tip_s = self._vtip.get()
            if not tip_s: raise ValidationError("Odaberite tip korisnika.")
            tip = next(t for t in TipKorisnika if t.value == tip_s)
            loz = self._vl.get().strip()
            if loz:
                loz_hash = self._svc.hash_lozinke(loz)
            elif self._odabran:
                loz_hash = self._odabran.lozinka_hash
            else:
                raise ValidationError("Lozinka je obavezna za novog korisnika.")
            k = Korisnik(
                id=self._odabran.id if self._odabran else None,
                ime=self._vi.get(), prezime=self._vp.get(),
                email=self._ve.get(), lozinka_hash=loz_hash,
                tip=tip, datum_rodenja=self._vd.get(),
                oib=self._vo.get(), telefon=self._vt.get() or None,
            )
            self._svc.spremi(k)
            self._info.postavi_ok(f"{k.puno_ime} uspješno spremljen.")
            self._ucitaj()
        except ValidationError as ve:
            self._info.postavi_gresku(str(ve))
        except StopIteration:
            self._info.postavi_gresku("Odaberite tip korisnika.")
        except Exception as e:
            self._info.postavi_gresku(str(e))

    def _reset(self):
        if self._odabran: self._popuni_formu(self._odabran)
        else: self._novi()


# Šifrarnik popusta
class PopustiTab(ttk.Frame):
    def __init__(self, parent, svc: PopustService, **kw):
        super().__init__(parent, **kw)
        self._svc = svc
        self._odabran: Optional[Popust] = None
        self._lista: List[Popust] = []
        self._gradi()
        self._ucitaj()

    def _gradi(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        lf = kartica(self, "Popusti")
        lf.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(1, weight=1)

        bar = ttk.Frame(lf)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        tk.Button(bar, text="➕ Novi", bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2",
                  command=self._novi).pack(side="left", padx=2)
        tk.Button(bar, text="🗑 Briši", bg=CRVENA, fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2",
                  command=self._obrisi).pack(side="left", padx=2)

        stupci = {
            "id":       ("ID",          42,  "center"),
            "naziv":    ("Naziv",       170, "w"),
            "tip":      ("Tip korisnika",120,"center"),
            "postotak": ("Postotak %",  80,  "center"),
            "aktivan":  ("Aktivan",     65,  "center"),
        }
        self._tbl = Tablica(lf, stupci, visina=22,
                            na_odabir=self._na_odabir)
        self._tbl.grid(row=1, column=0, sticky="nsew")

        ff = kartica(self, "Detalji popusta")
        ff.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        ff.columnconfigure(1, weight=1)
        self._gradi_formu(ff)

    def _gradi_formu(self, p):
        for i, (lbl, attr) in enumerate([
            ("Naziv *", "_vn"), ("Postotak % *", "_vpos"), ("Opis", "_vopis")
        ]):
            ttk.Label(p, text=lbl, font=F_MALI,
                      foreground=TEKST_SIVKAST).grid(
                row=i, column=0, sticky="w", padx=4, pady=3)
            var = tk.StringVar(); setattr(self, attr, var)
            ttk.Entry(p, textvariable=var, width=26).grid(
                row=i, column=1, sticky="ew", padx=4, pady=3)

        ttk.Label(p, text="Tip korisnika *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=3, column=0, sticky="w", padx=4, pady=3)
        self._vtip = tk.StringVar()
        ttk.Combobox(p, textvariable=self._vtip,
                     values=[t.value for t in TipKorisnika],
                     state="readonly", width=24).grid(
            row=3, column=1, sticky="ew", padx=4, pady=3)

        ttk.Label(p, text="Aktivan", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=4, column=0, sticky="w", padx=4)
        self._vakt = tk.BooleanVar(value=True)
        ttk.Checkbutton(p, variable=self._vakt).grid(
            row=4, column=1, sticky="w", padx=4)

        bf = ttk.Frame(p)
        bf.grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(bf, text="💾 Spremi", bg=ZELENA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0, padx=10, pady=6,
                  cursor="hand2", command=self._spremi).pack(side="left", padx=4)
        tk.Button(bf, text="✖ Odustani", bg=BIJELA, fg=TEKST_TAMNI,
                  font=F_NORMALAN, relief="solid", bd=1, padx=8, pady=5,
                  cursor="hand2", command=self._reset).pack(side="left", padx=4)
        tk.Button(bf, text="🆕 Novi", bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0, padx=10, pady=6,
                  cursor="hand2", command=self._novi).pack(side="left", padx=4)

        self._info = InfoOkvir(p)
        self._info.grid(row=6, column=0, columnspan=2, sticky="ew", pady=5)

    def _ucitaj(self):
        self._lista = self._svc.dohvati_sve()
        redovi = [(p.id, p.naziv,
                   p.tip_korisnika.value if isinstance(p.tip_korisnika, TipKorisnika)
                   else p.tip_korisnika,
                   f"{p.postotak:.1f}",
                   "Da" if p.aktivan else "Ne")
                  for p in self._lista]
        self._tbl.popuni_s_id(redovi)

    def _na_odabir(self, _=None):
        pid = self._tbl.odabrani_id()
        if pid is None: return
        self._odabran = next((p for p in self._lista if p.id == pid), None)
        if self._odabran: self._popuni(self._odabran)

    def _popuni(self, p: Popust):
        self._vn.set(p.naziv); self._vpos.set(str(p.postotak))
        self._vopis.set(p.opis or ""); self._vakt.set(p.aktivan)
        self._vtip.set(p.tip_korisnika.value
                       if isinstance(p.tip_korisnika, TipKorisnika)
                       else p.tip_korisnika)
        self._info.ocisti()

    def _novi(self):
        self._odabran = None
        self._tbl._tree.selection_remove(self._tbl._tree.selection())
        for v in [self._vn, self._vpos, self._vopis, self._vtip]: v.set("")
        self._vakt.set(True)
        self._info.ocisti()

    def _obrisi(self):
        if not self._odabran:
            messagebox.showwarning("Upozorenje", "Odaberite popust.")
            return
        if not messagebox.askyesno("Brisanje", f"Obrisati '{self._odabran.naziv}'?"):
            return
        try:
            self._svc.obrisi(self._odabran.id)
            self._odabran = None; self._ucitaj(); self._novi()
        except Exception as e:
            messagebox.showerror("Greška", str(e))

    def _spremi(self):
        self._info.ocisti()
        try:
            tip_s = self._vtip.get()
            if not tip_s: raise ValidationError("Odaberite tip korisnika.")
            tip = next(t for t in TipKorisnika if t.value == tip_s)
            p = Popust(
                id=self._odabran.id if self._odabran else None,
                naziv=self._vn.get(), tip_korisnika=tip,
                postotak=float(self._vpos.get() or 0),
                aktivan=self._vakt.get(), opis=self._vopis.get() or None,
            )
            self._psvc.spremi(p)
            self._info.postavi_ok(f"Popust '{p.naziv}' uspješno spremljen.")
            self._ucitaj()
        except ValidationError as ve:
            self._info.postavi_gresku(str(ve))
        except ValueError:
            self._info.postavi_gresku("Postotak mora biti broj.")
        except Exception as e:
            self._info.postavi_gresku(str(e))

    def _reset(self):
        if self._odabran: self._popuni(self._odabran)
        else: self._novi()


# Šifrarnik stanica
class StaniceTab(ttk.Frame):
    def __init__(self, parent, svc: StanicaService, **kw):
        super().__init__(parent, **kw)
        self._svc = svc
        self._odabrana: Optional[Stanica] = None
        self._lista: List[Stanica] = []
        self._gradi()
        self._ucitaj()

    def _gradi(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        lf = kartica(self, "Stanice")
        lf.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(1, weight=1)

        bar = ttk.Frame(lf)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        pretraga_bar(bar, self._pretrazi).pack(side="left")
        tk.Button(bar, text="➕ Novi", bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2", command=self._novi).pack(side="right", padx=2)
        tk.Button(bar, text="🗑 Briši", bg=CRVENA, fg=BIJELA,
                  font=F_MALI, relief="flat", bd=0, padx=8, pady=5,
                  cursor="hand2", command=self._obrisi).pack(side="right", padx=2)

        stupci = {
            "id":       ("ID",      42,  "center"),
            "naziv":    ("Naziv",   180, "w"),
            "grad":     ("Grad",    120, "w"),
            "zupanija": ("Županija",150, "w"),
        }
        self._tbl = Tablica(lf, stupci, visina=22,
                            na_odabir=self._na_odabir)
        self._tbl.grid(row=1, column=0, sticky="nsew")

        ff = kartica(self, "Detalji stanice")
        ff.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        ff.columnconfigure(1, weight=1)

        for i, (lbl, attr) in enumerate([
            ("Naziv *", "_sn"), ("Grad *", "_sg"), ("Županija *", "_sz")
        ]):
            ttk.Label(ff, text=lbl, font=F_MALI,
                      foreground=TEKST_SIVKAST).grid(
                row=i, column=0, sticky="w", padx=4, pady=4)
            var = tk.StringVar(); setattr(self, attr, var)
            ttk.Entry(ff, textvariable=var, width=26).grid(
                row=i, column=1, sticky="ew", padx=4, pady=4)

        bf = ttk.Frame(ff)
        bf.grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(bf, text="💾 Spremi", bg=ZELENA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0, padx=10, pady=6,
                  cursor="hand2", command=self._spremi).pack(side="left", padx=4)
        tk.Button(bf, text="✖ Odustani", bg=BIJELA, fg=TEKST_TAMNI,
                  font=F_NORMALAN, relief="solid", bd=1, padx=8, pady=5,
                  cursor="hand2", command=self._reset).pack(side="left", padx=4)
        tk.Button(bf, text="🆕 Novi", bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0, padx=10, pady=6,
                  cursor="hand2", command=self._novi).pack(side="left", padx=4)

        self._info = InfoOkvir(ff)
        self._info.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)

    def _ucitaj(self, upit=""):
        self._lista = (self._svc.pretrazi(upit)
                       if upit else self._svc.dohvati_sve())
        redovi = [(s.id, s.naziv, s.grad, s.zupanija)
                  for s in self._lista]
        self._tbl.popuni_s_id(redovi)

    def _pretrazi(self, u): self._ucitaj(u)

    def _na_odabir(self, _=None):
        sid = self._tbl.odabrani_id()
        if sid is None: return
        self._odabrana = next((s for s in self._lista if s.id == sid), None)
        if self._odabrana:
            self._sn.set(self._odabrana.naziv)
            self._sg.set(self._odabrana.grad)
            self._sz.set(self._odabrana.zupanija)
            self._info.ocisti()

    def _novi(self):
        self._odabrana = None
        self._tbl._tree.selection_remove(self._tbl._tree.selection())
        for v in [self._sn, self._sg, self._sz]: v.set("")
        self._info.ocisti()

    def _obrisi(self):
        if not self._odabrana:
            messagebox.showwarning("Upozorenje", "Odaberite stanicu.")
            return
        if not messagebox.askyesno("Brisanje",
                f"Obrisati stanicu '{self._odabrana.naziv}'?"):
            return
        try:
            self._svc.obrisi(self._odabrana.id)
            self._odabrana = None; self._ucitaj(); self._novi()
        except Exception as e:
            messagebox.showerror("Greška", str(e))

    def _spremi(self):
        self._info.ocisti()
        from models.entities import Stanica
        try:
            s = Stanica(
                id=self._odabrana.id if self._odabrana else None,
                naziv=self._sn.get(), grad=self._sg.get(),
                zupanija=self._sz.get()
            )
            self._svc.spremi(s)
            self._info.postavi_ok(f"Stanica '{s.naziv}' uspješno spremljena.")
            self._ucitaj()
        except ValidationError as ve:
            self._info.postavi_gresku(str(ve))
        except Exception as e:
            self._info.postavi_gresku(str(e))

    def _reset(self):
        if self._odabrana:
            self._sn.set(self._odabrana.naziv)
            self._sg.set(self._odabrana.grad)
            self._sz.set(self._odabrana.zupanija)
        else:
            self._novi()