import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
import hashlib

from models.entities import Korisnik, TipKorisnika
from bll.services import KorisnikService, ValidationError
from ui.theme import (
    PLAVA_TAMNA, PLAVA_SREDNJA, PLAVA_SVIJETLA, BIJELA,
    POZADINA, TEKST_TAMNI, TEKST_SIVKAST, ZELENA, CRVENA,
    RUBA_SIVA, F_NASLOV, F_PODNASL, F_NORMALAN, F_MALI, F_IKONA,
    primjeni_temu
)
from ui.komponente import PoljeUnosa, PadajucaLista, InfoOkvir

class EkranPrijave(ttk.Frame):

    def __init__(self, parent,
                 svc: KorisnikService,
                 na_prijavu: Callable[[Korisnik], None],
                 na_admin: Callable[[], None],
                 **kw):
        super().__init__(parent, **kw)
        self._svc = svc
        self._na_prijavu = na_prijavu
        self._na_admin = na_admin
        self._mod = "prijava"   # "prijava" ili "registracija"
        self.configure(style="TFrame")
        self._gradi()

    def _gradi(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Centralni okvir
        centar = ttk.Frame(self, width=420)
        centar.grid(row=0, column=0)
        centar.columnconfigure(0, weight=1)

        # Logo / branding
        logo_f = tk.Frame(centar, bg=PLAVA_TAMNA, height=80)
        logo_f.pack(fill="x", pady=(40, 0))
        logo_f.pack_propagate(False)
        tk.Label(logo_f, text="🚆  HŽPlus",
                 bg=PLAVA_TAMNA, fg=BIJELA,
                 font=("Segoe UI", 20, "bold")).pack(expand=True)

        # Kartica
        kartica = tk.Frame(centar, bg=BIJELA,
                           relief="solid", bd=1)
        kartica.pack(fill="both", padx=0, pady=0)
        kartica.columnconfigure(0, weight=1)

        # Tabovi prijava / registracija
        tab_f = tk.Frame(kartica, bg=BIJELA)
        tab_f.pack(fill="x")
        tab_f.columnconfigure((0, 1), weight=1)

        self._btn_tab_prijava = tk.Button(
            tab_f, text="Prijava", font=F_PODNASL,
            bg=BIJELA, fg=PLAVA_TAMNA,
            relief="flat", bd=0, pady=10,
            cursor="hand2",
            command=lambda: self._prebaci_mod("prijava"))
        self._btn_tab_prijava.grid(row=0, column=0, sticky="ew")

        self._btn_tab_reg = tk.Button(
            tab_f, text="Registracija", font=F_PODNASL,
            bg="#F0F0F0", fg=TEKST_SIVKAST,
            relief="flat", bd=0, pady=10,
            cursor="hand2",
            command=lambda: self._prebaci_mod("registracija"))
        self._btn_tab_reg.grid(row=0, column=1, sticky="ew")

        # Linija ispod aktivnog taba
        self._tab_indikator = tk.Frame(tab_f, bg=PLAVA_TAMNA, height=3)
        self._tab_indikator.grid(row=1, column=0, sticky="ew")

        # Sadržaj ovisno o modu
        self._sadrzaj_f = tk.Frame(kartica, bg=BIJELA, padx=32, pady=24)
        self._sadrzaj_f.pack(fill="both")

        self._info = InfoOkvir(kartica)
        self._info.pack(fill="x", padx=32, pady=(0, 8))

        # Admin link
        admin_f = tk.Frame(centar, bg=POZADINA)
        admin_f.pack(fill="x", pady=8)
        tk.Label(admin_f, text="Djelatnik HŽ-a?",
                 bg=POZADINA, fg=TEKST_SIVKAST,
                 font=F_MALI).pack(side="left", padx=16)
        btn_admin = tk.Label(admin_f, text="Admin pristup →",
                              bg=POZADINA, fg=PLAVA_TAMNA,
                              font=(F_MALI[0], F_MALI[1], "underline"),
                              cursor="hand2")
        btn_admin.pack(side="left")
        btn_admin.bind("<Button-1>", lambda _: self._na_admin())

        self._gradi_formu_prijave()

    def _prebaci_mod(self, mod: str):
        self._mod = mod
        self._info.ocisti()
        for w in self._sadrzaj_f.winfo_children():
            w.destroy()
        if mod == "prijava":
            self._btn_tab_prijava.configure(bg=BIJELA, fg=PLAVA_TAMNA)
            self._btn_tab_reg.configure(bg="#F0F0F0", fg=TEKST_SIVKAST)
            self._tab_indikator.grid(row=1, column=0, sticky="ew")
            self._gradi_formu_prijave()
        else:
            self._btn_tab_prijava.configure(bg="#F0F0F0", fg=TEKST_SIVKAST)
            self._btn_tab_reg.configure(bg=BIJELA, fg=PLAVA_TAMNA)
            self._tab_indikator.grid(row=1, column=1, sticky="ew")
            self._gradi_formu_registracije()

    def _gradi_formu_prijave(self):
        f = self._sadrzaj_f

        ttk.Label(f, text="Email adresa", font=F_MALI,
                  foreground=TEKST_SIVKAST,
                  background=BIJELA).pack(anchor="w", pady=(0, 2))
        self._p_email = tk.StringVar()
        email_e = ttk.Entry(f, textvariable=self._p_email, width=32)
        email_e.pack(fill="x", pady=(0, 12))
        email_e.focus_set()

        ttk.Label(f, text="Lozinka", font=F_MALI,
                  foreground=TEKST_SIVKAST,
                  background=BIJELA).pack(anchor="w", pady=(0, 2))
        self._p_lozinka = tk.StringVar()
        loz_e = ttk.Entry(f, textvariable=self._p_lozinka,
                          show="*", width=32)
        loz_e.pack(fill="x", pady=(0, 20))
        loz_e.bind("<Return>", lambda _: self._prijavi())

        btn = tk.Button(f, text="Prijava", font=F_PODNASL,
                        bg=PLAVA_TAMNA, fg=BIJELA,
                        relief="flat", bd=0, pady=10,
                        cursor="hand2",
                        command=self._prijavi)
        btn.pack(fill="x")

    def _gradi_formu_registracije(self):
        f = self._sadrzaj_f
        f.columnconfigure((0, 1), weight=1)

        # Ime i prezime u redu
        self._r_ime = PoljeUnosa(f, "Ime", obavezno=True, sirina=16)
        self._r_ime.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._r_prezime = PoljeUnosa(f, "Prezime", obavezno=True, sirina=16)
        self._r_prezime.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self._r_email = PoljeUnosa(f, "Email adresa", obavezno=True, sirina=34)
        self._r_email.grid(row=1, column=0, columnspan=2, sticky="ew", pady=4)

        self._r_lozinka = PoljeUnosa(f, "Lozinka", obavezno=True,
                                      sirina=34, lozinka=True)
        self._r_lozinka.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)

        self._r_oib = PoljeUnosa(f, "OIB (11 znamenki)", obavezno=True, sirina=34)
        self._r_oib.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)

        self._r_datum = PoljeUnosa(f, "Datum rođenja (YYYY-MM-DD)",
                                    obavezno=True, sirina=34)
        self._r_datum.grid(row=4, column=0, columnspan=2, sticky="ew", pady=4)

        tipovi = [t.value for t in TipKorisnika]
        self._r_tip = PadajucaLista(f, "Tip korisnika", tipovi,
                                     obavezno=True, sirina=32)
        self._r_tip.grid(row=5, column=0, columnspan=2, sticky="ew", pady=4)

        self._r_telefon = PoljeUnosa(f, "Telefon (neobavezno)", sirina=34)
        self._r_telefon.grid(row=6, column=0, columnspan=2, sticky="ew", pady=4)

        btn = tk.Button(f, text="Registracija", font=F_PODNASL,
                        bg=ZELENA, fg=BIJELA,
                        relief="flat", bd=0, pady=10,
                        cursor="hand2",
                        command=self._registriraj)
        btn.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(16, 0))

    def _prijavi(self):
        email = self._p_email.get().strip()
        lozinka = self._p_lozinka.get()
        if not email or not lozinka:
            self._info.postavi_gresku("Unesite email i lozinku.")
            return
        korisnik = self._svc.autentificiraj(email, lozinka)
        if korisnik:
            self._info.postavi_ok(f"Dobrodošli, {korisnik.puno_ime}!")
            self.after(600, lambda: self._na_prijavu(korisnik))
        else:
            self._info.postavi_gresku("Neispravni email ili lozinka.")

    def _registriraj(self):
        self._info.ocisti()
        try:
            tip_s = self._r_tip.get()
            if not tip_s:
                raise ValidationError("Odaberite tip korisnika.")
            tip = next(t for t in TipKorisnika if t.value == tip_s)
            loz = self._r_lozinka.get()
            if not loz:
                raise ValidationError("Lozinka je obavezna.")

            k = Korisnik(
                id=None,
                ime=self._r_ime.get(),
                prezime=self._r_prezime.get(),
                email=self._r_email.get(),
                lozinka_hash=self._svc.hash_lozinke(loz),
                tip=tip,
                datum_rodenja=self._r_datum.get(),
                oib=self._r_oib.get(),
                telefon=self._r_telefon.get() or None,
            )
            self._svc.spremi(k)
            self._info.postavi_ok(
                f"Račun za {k.puno_ime} uspješno stvoren! Možete se prijaviti.")
            self._prebaci_mod("prijava")
            self._p_email.set(k.email)
        except ValidationError as ve:
            self._info.postavi_gresku(str(ve))
        except StopIteration:
            self._info.postavi_gresku("Odaberite tip korisnika.")
        except Exception as e:
            self._info.postavi_gresku(f"Greška: {e}")