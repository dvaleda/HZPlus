import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from datetime import date, timedelta

from models.entities import (
    Korisnik, Vlak, TipVlaka, Karta, StatusKarte, SjedaloVlaka
)
from bll.services import (
    VlakService, KartaService, KorisnikService, ValidationError
)
from ui.tema import (
    PLAVA_TAMNA, PLAVA_SREDNJA, BIJELA, POZADINA,
    TEKST_TAMNI, TEKST_SIVKAST, ZELENA, CRVENA,
    F_PODNASL, F_NORMALAN, F_MALI
)
from ui.komponente import Tablica, InfoOkvir
from ui.tema import kartica


class KorisnikPortal(ttk.Frame):

    def __init__(self, parent,
                 korisnik: Korisnik,
                 vlak_svc: VlakService,
                 karta_svc: KartaService,
                 korisnik_svc: KorisnikService,
                 stanice: list,
                 na_odjava: callable,
                 **kw):
        super().__init__(parent, **kw)
        self._k = korisnik
        self._vsvc = vlak_svc
        self._kasvc = karta_svc
        self._ksvc = korisnik_svc
        self._stanice = stanice
        self._na_odjava = na_odjava
        self._gradi()

    def _gradi(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        top = tk.Frame(self, bg=PLAVA_TAMNA, height=52)
        top.grid(row=0, column=0, sticky="ew")
        top.pack_propagate(False)

        tk.Label(top, text="🚆  HŽPlus",
                 bg=PLAVA_TAMNA, fg=BIJELA,
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=16, pady=10)

        tk.Button(top, text=f"🔓  Odjava ({self._k.puno_ime})",
                  bg=PLAVA_TAMNA, fg="#A8C8F0",
                  font=F_MALI, relief="flat", bd=0,
                  cursor="hand2",
                  command=self._na_odjava).pack(side="right", padx=16)

        tip_boja = {"Student": ZELENA, "Umirovljenik": "#8E44AD",
                    "Učenik": "#E67E22"}.get(
            self._k.tip.value if hasattr(self._k.tip, "value") else self._k.tip,
            PLAVA_SREDNJA)
        tip_str = self._k.tip.value if hasattr(self._k.tip, "value") else self._k.tip
        tk.Label(top, text=f"  {tip_str}  ",
                 bg=tip_boja, fg=BIJELA,
                 font=F_MALI, relief="flat").pack(side="right", padx=4, pady=14)

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        t1 = ttk.Frame(nb)
        nb.add(t1, text="  🔍  Pretraži i kupi kartu  ")
        self._gradi_pretraga(t1)

        t2 = ttk.Frame(nb)
        nb.add(t2, text="  🎫  Moje karte  ")
        self._gradi_moje_karte(t2)

        t3 = ttk.Frame(nb)
        nb.add(t3, text="  👤  Moj profil  ")
        self._gradi_profil(t3)

        nb.bind("<<NotebookTabChanged>>", self._na_promjenu_taba)

    #  TAB 1: PRETRAŽI I KUPI

    def _gradi_pretraga(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Forma pretrage
        forma = kartica(parent, "Pretraži vlakove")
        forma.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        forma.columnconfigure((1, 3, 5), weight=1)

        ttk.Label(forma, text="Polazište *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=0, column=0, sticky="w", padx=4)
        self._pr_pol = tk.StringVar()
        s_vals = ["(sve stanice)"] + [s.naziv for s in self._stanice]
        cb_pol = ttk.Combobox(forma, textvariable=self._pr_pol,
                               values=s_vals, state="readonly", width=22)
        cb_pol.grid(row=0, column=1, sticky="ew", padx=4)
        cb_pol.current(0)

        ttk.Label(forma, text="Odredište *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=0, column=2, sticky="w", padx=4)
        self._pr_odred = tk.StringVar()
        cb_od = ttk.Combobox(forma, textvariable=self._pr_odred,
                              values=s_vals, state="readonly", width=22)
        cb_od.grid(row=0, column=3, sticky="ew", padx=4)
        cb_od.current(0)

        ttk.Label(forma, text="Datum *", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=0, column=4, sticky="w", padx=4)
        self._pr_datum = tk.StringVar(
            value=(date.today() + timedelta(days=1)).strftime("%Y-%m-%d"))
        ttk.Entry(forma, textvariable=self._pr_datum, width=12).grid(
            row=0, column=5, sticky="ew", padx=4)

        tk.Button(forma, text="  🔍  Pretraži  ",
                  bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0,
                  padx=8, pady=6, cursor="hand2",
                  command=self._pretrazi_vlakove).grid(
            row=0, column=6, padx=(8, 0))

        # Rezultati
        rez_f = kartica(parent, "Dostupni vlakovi")
        rez_f.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        rez_f.columnconfigure(0, weight=1)
        rez_f.rowconfigure(0, weight=1)

        stupci = {
            "broj":    ("Br. vlaka", 85,   "center"),
            "tip":     ("Tip",       90,   "center"),
            "od":      ("Polazište", 160,  "w"),
            "do":      ("Odredište", 160,  "w"),
            "pol":     ("Polazak",   65,   "center"),
            "dol":     ("Dolazak",   65,   "center"),
            "cijena":  ("Cijena €",  90,   "e"),
            "popust":  ("Vaš popust",75,   "center"),
            "placate": ("Plaćate €", 90,   "e"),
        }
        self._tbl_vlakovi = Tablica(
            rez_f, stupci, visina=8,
            na_odabir=self._na_odabir_vlaka)
        self._tbl_vlakovi.grid(row=0, column=0, sticky="nsew")
        self._tbl_vlakovi.postavi_tag_boju("dostupan", BIJELA)
        self._tbl_vlakovi.postavi_tag_boju("nedostupan", "#FFF0F0", TEKST_SIVKAST)

        # Kupnja
        kupnja_f = kartica(parent, "Odabir sjedala i kupnja")
        kupnja_f.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        kupnja_f.columnconfigure((1, 3), weight=1)

        ttk.Label(kupnja_f, text="Odabrani vlak:", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(row=0, column=0, sticky="w", padx=4)
        self._kupnja_info = tk.StringVar(value="— nije odabran vlak —")
        ttk.Label(kupnja_f, textvariable=self._kupnja_info,
                  font=F_PODNASL, foreground=PLAVA_TAMNA).grid(
            row=0, column=1, columnspan=3, sticky="w", padx=4)

        ttk.Label(kupnja_f, text="Slobodna sjedala:", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=1, column=0, sticky="w", padx=4, pady=4)
        self._sj_var = tk.StringVar(value="Odaberite vlak za prikaz sjedala")
        self._cb_sjedala = ttk.Combobox(kupnja_f, textvariable=self._sj_var,
                                         state="readonly", width=28)
        self._cb_sjedala.grid(row=1, column=1, sticky="ew", padx=4)

        ttk.Label(kupnja_f, text="Cijena:", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(
            row=1, column=2, sticky="w", padx=4)
        self._cijena_var = tk.StringVar(value="—")
        ttk.Label(kupnja_f, textvariable=self._cijena_var,
                  font=("Segoe UI", 12, "bold"),
                  foreground=ZELENA).grid(row=1, column=3, sticky="w", padx=4)

        self._info_kupnja = InfoOkvir(kupnja_f)
        self._info_kupnja.grid(row=2, column=0, columnspan=4,
                                sticky="ew", pady=4)

        tk.Button(kupnja_f, text="  🎫  Kupi kartu  ",
                  bg=ZELENA, fg=BIJELA,
                  font=F_PODNASL, relief="flat", bd=0,
                  padx=10, pady=8, cursor="hand2",
                  command=self._kupi_kartu).grid(
            row=3, column=0, columnspan=4, pady=4)

        self._odabrani_vlak: Optional[Vlak] = None
        self._vlakovi_lista: List[Vlak] = []

    def _pretrazi_vlakove(self):
        pol_naziv = self._pr_pol.get()
        od_naziv = self._pr_odred.get()
        datum = self._pr_datum.get().strip()

        if not datum:
            messagebox.showwarning("Upozorenje", "Unesite datum putovanja.")
            return

        svi = self._vsvc.dohvati_sve()

        if pol_naziv and pol_naziv != "(sve stanice)":
            svi = [v for v in svi if v.naziv_polazisne == pol_naziv]
        if od_naziv and od_naziv != "(sve stanice)":
            svi = [v for v in svi if v.naziv_odredisne == od_naziv]

        self._vlakovi_lista = svi

        redovi = []
        tagovi = []
        for v in svi:
            cijena, popust = self._kasvc.izracunaj_cijenu(v, self._k)
            pop_txt = f"-{popust:.0f}%" if popust > 0 else "—"
            redovi.append((
                v.id,
                v.broj_vlaka,
                v.tip.value if isinstance(v.tip, TipVlaka) else v.tip,
                v.naziv_polazisne or "",
                v.naziv_odredisne or "",
                v.vrijeme_polaska,
                v.vrijeme_dolaska,
                f"{v.cijena_kn:.2f}",
                pop_txt,
                f"{cijena:.2f}",
            ))
            tagovi.append("dostupan")

        self._tbl_vlakovi.popuni_s_id(redovi)
        self._kupnja_info.set("— odaberite vlak iz liste —")
        self._odabrani_vlak = None

        if not svi:
            messagebox.showinfo("Nema rezultata",
                                "Nema dostupnih vlakova za odabrani kriterij.")

    def _na_odabir_vlaka(self, event=None):
        vid = self._tbl_vlakovi.odabrani_id()
        if vid is None:
            return
        self._odabrani_vlak = next(
            (v for v in self._vlakovi_lista if v.id == vid), None)
        if not self._odabrani_vlak:
            return

        v = self._odabrani_vlak
        cijena, popust = self._kasvc.izracunaj_cijenu(v, self._k)
        pop_txt = f" (popust {popust:.0f}%)" if popust > 0 else ""
        self._kupnja_info.set(
            f"Vlak {v.broj_vlaka}  |  "
            f"{v.naziv_polazisne} → {v.naziv_odredisne}  |  "
            f"{v.vrijeme_polaska}–{v.vrijeme_dolaska}{pop_txt}")
        self._cijena_var.set(f"{cijena:.2f} €")

        # Dohvati slobodna sjedala
        datum = self._pr_datum.get().strip()
        slobodna = self._kasvc.dohvati_slobodna_sjedala(v.id, datum)
        opcije = ["— bez odabira sjedala —"] + [
            f"{s.oznaka_vagon}-{s.broj_sjedala} (razred {s.razred})"
            for s in slobodna
        ]
        self._cb_sjedala.configure(values=opcije)
        self._sj_var.set(opcije[0])
        self._info_kupnja.ocisti()

    def _kupi_kartu(self):
        self._info_kupnja.ocisti()
        if not self._odabrani_vlak:
            self._info_kupnja.postavi_gresku("Odaberite vlak.")
            return
        datum = self._pr_datum.get().strip()

        # Razriješi sjedalo
        sj_txt = self._sj_var.get()
        id_sjedala = None
        if sj_txt and sj_txt != "— bez odabira sjedala —":
            slobodna = self._kasvc.dohvati_slobodna_sjedala(
                self._odabrani_vlak.id, datum)
            dio = sj_txt.split(" ")[0]  # npr. "V1-5"
            for s in slobodna:
                if f"{s.oznaka_vagon}-{s.broj_sjedala}" == dio:
                    id_sjedala = s.id
                    break

        try:
            karta = self._kasvc.kupi_kartu(
                self._k.id, self._odabrani_vlak.id, datum, id_sjedala)
            v = self._odabrani_vlak
            self._info_kupnja.postavi_ok(
                f"Karta kupljena! ID: {karta.id}  |  "
                f"{v.naziv_polazisne} → {v.naziv_odredisne}  |  "
                f"{datum}  |  {karta.cijena_placena:.2f} €")
        except ValidationError as ve:
            self._info_kupnja.postavi_gresku(str(ve))
        except Exception as e:
            self._info_kupnja.postavi_gresku(f"Greška: {e}")

    #  TAB 2: MOJE KARTE

    def _gradi_moje_karte(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Filter
        fil_f = kartica(parent, "Filter karata")
        fil_f.grid(row=0, column=0, sticky="ew", padx=12, pady=8)

        self._filter_status = tk.StringVar(value="Sve")
        for tekst in ("Sve", "Aktivna", "Iskorištena", "Otkazana"):
            ttk.Radiobutton(fil_f, text=tekst,
                            variable=self._filter_status,
                            value=tekst,
                            command=self._ucitaj_moje_karte).pack(
                side="left", padx=8)

        # Tablica karata
        tbl_f = kartica(parent, "Moje karte")
        tbl_f.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        tbl_f.columnconfigure(0, weight=1)
        tbl_f.rowconfigure(0, weight=1)

        stupci = {
            "vlak":     ("Vlak",       85, "center"),
            "od":       ("Polazište",  150, "w"),
            "do":       ("Odredište",  150, "w"),
            "datum":    ("Datum puta", 100, "center"),
            "sjedalo":  ("Sjedalo",    75, "center"),
            "cijena":   ("Cijena €",   85, "e"),
            "popust":   ("Popust %",   65, "center"),
            "status":   ("Status",     90, "center"),
        }
        self._tbl_karte = Tablica(
            tbl_f, stupci, visina=12,
            na_odabir=self._na_odabir_karte)
        self._tbl_karte.grid(row=0, column=0, sticky="nsew")
        self._tbl_karte.postavi_tag_boju("aktivna",    "#EBF9F1", ZELENA)
        self._tbl_karte.postavi_tag_boju("otkazana",   "#FFF0F0", CRVENA)
        self._tbl_karte.postavi_tag_boju("iskorishtena", "#F5F5F5", TEKST_SIVKAST)

        # Akcije
        ak_f = kartica(parent, "Akcije")
        ak_f.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

        self._info_karte = InfoOkvir(ak_f)
        self._info_karte.pack(fill="x", pady=(0, 6))

        self._btn_otkazi = tk.Button(
            ak_f, text="  ✕  Otkaži odabranu kartu  ",
            bg=CRVENA, fg=BIJELA,
            font=F_NORMALAN, relief="flat", bd=0,
            padx=8, pady=7, cursor="hand2",
            state="disabled",
            command=self._otkazi_kartu)
        self._btn_otkazi.pack(side="left", padx=4)

        self._odabrana_karta: Optional[Karta] = None

    def _ucitaj_moje_karte(self):
        karte = self._kasvc.dohvati_za_korisnika(self._k.id)
        filter_s = self._filter_status.get()
        if filter_s != "Sve":
            karte = [k for k in karte
                     if (k.status.value if hasattr(k.status, "value") else k.status)
                     == filter_s]

        redovi = []
        tagovi = []
        for k in karte:
            status_s = k.status.value if hasattr(k.status, "value") else k.status
            redovi.append((
                k.id,
                k.vlak_broj or "",
                k.polazisna or "",
                k.odredisna or "",
                k.datum_putovanja,
                k.broj_sjedala or "—",
                f"{k.cijena_placena:.2f}",
                f"{k.popust_postotak:.0f}%",
                status_s,
            ))
            if status_s == "Aktivna":
                tagovi.append("aktivna")
            elif status_s == "Otkazana":
                tagovi.append("otkazana")
            else:
                tagovi.append("iskorishtena")

        # Koristimo popuni_s_id kako bi mogli dohvatiti ID
        for item in self._tbl_karte._tree.get_children():
            self._tbl_karte._tree.delete(item)
        for i, red in enumerate(redovi):
            tag = tagovi[i]
            iid = str(karte[i].id)
            self._tbl_karte._tree.insert(
                "", "end", iid=iid, values=red[1:], tags=(tag,))

        if not karte:
            self._info_karte.postavi_ok(
                "Nemate karata za odabrani status.")
        else:
            self._info_karte.ocisti()
        self._btn_otkazi.configure(state="disabled")
        self._odabrana_karta = None

    def _na_odabir_karte(self, event=None):
        sel = self._tbl_karte._tree.selection()
        if not sel:
            return
        kid = int(sel[0])
        karta = self._kasvc.dohvati_po_id(kid)
        if karta:
            self._odabrana_karta = karta
            status_s = karta.status.value if hasattr(karta.status, "value") else karta.status
            if status_s == "Aktivna":
                self._btn_otkazi.configure(state="normal")
            else:
                self._btn_otkazi.configure(state="disabled")

    def _otkazi_kartu(self):
        if not self._odabrana_karta:
            return
        if not messagebox.askyesno(
            "Potvrda otkazivanja",
            f"Sigurno želite otkazati kartu #{self._odabrana_karta.id}?\n"
            f"Putovanje: {self._odabrana_karta.datum_putovanja}"
        ):
            return
        try:
            self._kasvc.otkazi_kartu(self._odabrana_karta.id)
            self._info_karte.postavi_ok(
                f"Karta #{self._odabrana_karta.id} uspješno otkazana.")
            self._ucitaj_moje_karte()
        except ValidationError as ve:
            self._info_karte.postavi_gresku(str(ve))
        except Exception as e:
            self._info_karte.postavi_gresku(f"Greška: {e}")

    #  TAB 3: PROFIL

    def _gradi_profil(self, parent):
        parent.columnconfigure(0, weight=1)

        # Nepromjenjivi podaci
        info_f = kartica(parent, "Osobni podaci")
        info_f.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        info_f.columnconfigure((1, 3), weight=1)

        tip_str = self._k.tip.value if hasattr(self._k.tip, "value") else self._k.tip
        polja_fix = [
            ("Ime", self._k.ime),
            ("Prezime", self._k.prezime),
            ("OIB", self._k.oib),
            ("Datum rođenja", self._k.datum_rodenja),
            ("Tip korisnika", tip_str),
        ]
        for i, (labela, vrijednost) in enumerate(polja_fix):
            red = i // 2
            stupac_l = (i % 2) * 2
            ttk.Label(info_f, text=f"{labela}:",
                      font=F_MALI, foreground=TEKST_SIVKAST).grid(
                row=red, column=stupac_l, sticky="w", padx=8, pady=4)
            ttk.Label(info_f, text=vrijednost,
                      font=F_NORMALAN, foreground=TEKST_TAMNI).grid(
                row=red, column=stupac_l + 1, sticky="w", padx=(0, 24), pady=4)

        # Promjenjivi podaci
        edit_f = kartica(parent, "Uredi podatke")
        edit_f.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        edit_f.columnconfigure(1, weight=1)

        ttk.Label(edit_f, text="Email:", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self._prof_email = tk.StringVar(value=self._k.email)
        ttk.Entry(edit_f, textvariable=self._prof_email, width=30).grid(
            row=0, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(edit_f, text="Telefon:", font=F_MALI,
                  foreground=TEKST_SIVKAST).grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self._prof_telefon = tk.StringVar(value=self._k.telefon or "")
        ttk.Entry(edit_f, textvariable=self._prof_telefon, width=30).grid(
            row=1, column=1, sticky="ew", padx=8, pady=4)

        self._info_profil = InfoOkvir(edit_f)
        self._info_profil.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        tk.Button(edit_f, text="  💾  Spremi promjene  ",
                  bg=PLAVA_TAMNA, fg=BIJELA,
                  font=F_NORMALAN, relief="flat", bd=0,
                  padx=8, pady=7, cursor="hand2",
                  command=self._spremi_profil).grid(
            row=3, column=0, columnspan=2, pady=(4, 8))

        # Statistike
        stat_f = kartica(parent, "Statistike")
        stat_f.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._stat_lbl = ttk.Label(stat_f, text="Učitavanje...",
                                    font=F_NORMALAN)
        self._stat_lbl.pack(anchor="w", padx=4)

    def _spremi_profil(self):
        self._info_profil.ocisti()
        self._k.email = self._prof_email.get().strip()
        self._k.telefon = self._prof_telefon.get().strip() or None
        try:
            self._ksvc.spremi(self._k)
            self._info_profil.postavi_ok("Podaci uspješno ažurirani.")
        except ValidationError as ve:
            self._info_profil.postavi_gresku(str(ve))
        except Exception as e:
            self._info_profil.postavi_gresku(f"Greška: {e}")

    def _ucitaj_statistike(self):
        karte = self._kasvc.dohvati_za_korisnika(self._k.id)
        ukupno = len(karte)
        aktivne = sum(
            1 for k in karte
            if (k.status.value if hasattr(k.status, "value") else k.status) == "Aktivna")
        ukupno_potroseno = sum(k.cijena_placena for k in karte
                                if (k.status.value if hasattr(k.status, "value") else k.status)
                                != "Otkazana")
        self._stat_lbl.configure(
            text=f"Ukupno karata: {ukupno}   |   "
                 f"Aktivnih: {aktivne}   |   "
                 f"Ukupno potrošeno: {ukupno_potroseno:.2f} €")

    def _na_promjenu_taba(self, event=None):
        idx = event.widget.index("current")
        if idx == 1:
            self._ucitaj_moje_karte()
        elif idx == 2:
            self._ucitaj_statistike()