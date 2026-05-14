import tkinter as tk
from tkinter import messagebox
from typing import Optional

from models.entities import Korisnik
from dal.database import Database
from dal.repositories import (
    StanicaRepository, VlakRepository, KorisnikRepository,
    PopustRepository, KartaRepository, SjedaloRepository
)
from bll.services import (
    StanicaService, VlakService, KorisnikService,
    PopustService, KartaService
)
from ui.theme import (
    primjeni_temu, POZADINA
)
from ui.prijava import EkranPrijave
from ui.korisnik_portal import KorisnikPortal
from ui.admin_portal import AdminPortal


class HZPlusApp:

    ADMIN_LOZINKA = "admin123"

    def __init__(self, db_path: str = "hzplus.db"):
        self._db = Database(db_path)
        self._db.inicijaliziraj_shemu()
        self._db.unesi_testne_podatke()

        s_repo  = StanicaRepository(self._db)
        v_repo  = VlakRepository(self._db)
        k_repo  = KorisnikRepository(self._db)
        p_repo  = PopustRepository(self._db)
        ka_repo = KartaRepository(self._db)
        sj_repo = SjedaloRepository(self._db)

        self._s_svc  = StanicaService(s_repo)
        self._v_svc  = VlakService(v_repo, s_repo)
        self._k_svc  = KorisnikService(k_repo)
        self._p_svc  = PopustService(p_repo)
        self._ka_svc = KartaService(ka_repo, v_repo, k_repo, p_repo, sj_repo)
        self._stanice = s_repo.dohvati_sve()

        self._root = tk.Tk()
        self._root.title("HŽPlus — Sustav za upravljanje željezničkim prijevozom")
        self._root.geometry("1280x800")
        self._root.minsize(900, 600)
        self._root.configure(bg=POZADINA)

        primjeni_temu()

        self._trenutni_widget: Optional[tk.Widget] = None
        self._pokazi_prijavu()

        self._root.protocol("WM_DELETE_WINDOW", self._zatvori)

    def _ocisti(self):
        if self._trenutni_widget:
            self._trenutni_widget.destroy()
            self._trenutni_widget = None

    def _pokazi_prijavu(self):
        self._ocisti()
        frame = EkranPrijave(
            self._root,
            svc=self._k_svc,
            na_prijavu=self._na_prijavu_korisnika,
            na_admin=self._pokazi_admin_prijavu,
        )
        frame.pack(fill="both", expand=True)
        self._trenutni_widget = frame

    def _na_prijavu_korisnika(self, korisnik: Korisnik):
        self._ocisti()
        portal = KorisnikPortal(
            self._root,
            korisnik=korisnik,
            vlak_svc=self._v_svc,
            karta_svc=self._ka_svc,
            korisnik_svc=self._k_svc,
            stanice=self._stanice,
            na_odjava=self._pokazi_prijavu,
        )
        portal.pack(fill="both", expand=True)
        self._trenutni_widget = portal

    def _pokazi_admin_prijavu(self):
        from tkinter import simpledialog
        lozinka = simpledialog.askstring(
            "Admin pristup",
            "Unesite admin lozinku:",
            show="*",
            parent=self._root
        )
        if lozinka == self.ADMIN_LOZINKA:
            self._pokazi_admin()
        elif lozinka is not None:
            messagebox.showerror("Pogrešna lozinka",
                                 "Admin lozinka nije ispravna.")

    def _pokazi_admin(self):
        self._ocisti()
        admin = AdminPortal(
            self._root,
            vlak_svc=self._v_svc,
            korisnik_svc=self._k_svc,
            popust_svc=self._p_svc,
            stanica_svc=self._s_svc,
            karta_svc=self._ka_svc,
            stanice=self._stanice,
            na_odjava=self._pokazi_prijavu,
        )
        admin.pack(fill="both", expand=True)
        self._trenutni_widget = admin

    def _zatvori(self):
        self._db.close()
        self._root.destroy()

    def pokreni(self):
        self._root.mainloop()


def main():
    app = HZPlusApp()
    app.pokreni()


if __name__ == "__main__":
    main()
