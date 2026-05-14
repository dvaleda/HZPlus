import hashlib
import re
from datetime import datetime, date
from typing import List, Optional, Tuple

from models.entities import (
    Stanica, Vlak, TipVlaka, Korisnik, TipKorisnika,
    Karta, StatusKarte, Popust, SjedaloVlaka
)
from dal.repositories import (
    StanicaRepository, VlakRepository, KorisnikRepository,
    PopustRepository, KartaRepository, SjedaloRepository
)


class ValidationError(Exception):
    pass


class StanicaService:
    def __init__(self, repo: StanicaRepository):
        self.repo = repo

    def dohvati_sve(self) -> List[Stanica]:
        return self.repo.dohvati_sve()

    def dohvati_po_id(self, id_: int) -> Optional[Stanica]:
        return self.repo.dohvati_po_id(id_)

    def pretrazi(self, upit: str) -> List[Stanica]:
        return self.repo.pretrazi(upit)

    def spremi(self, s: Stanica) -> Stanica:
        if not s.naziv or len(s.naziv.strip()) < 2:
            raise ValidationError("Naziv stanice mora imati barem 2 znaka.")
        if not s.grad or len(s.grad.strip()) < 2:
            raise ValidationError("Grad mora biti naveden.")
        if not s.zupanija or len(s.zupanija.strip()) < 2:
            raise ValidationError("Županija mora biti navedena.")
        return self.repo.spremi(s)

    def obrisi(self, id_: int) -> bool:
        return self.repo.obrisi(id_)


class VlakService:
    def __init__(self, repo: VlakRepository, stanica_repo: StanicaRepository):
        self.repo = repo
        self.stanica_repo = stanica_repo

    def dohvati_sve(self) -> List[Vlak]:
        return self.repo.dohvati_sve()

    def dohvati_po_id(self, id_: int) -> Optional[Vlak]:
        return self.repo.dohvati_po_id(id_)

    def pretrazi(self, upit: str) -> List[Vlak]:
        return self.repo.pretrazi(upit)

    def spremi(self, v: Vlak) -> Vlak:
        if not v.broj_vlaka or len(v.broj_vlaka.strip()) < 2:
            raise ValidationError("Broj vlaka mora imati barem 2 znaka.")
        if v.kapacitet <= 0:
            raise ValidationError("Kapacitet mora biti pozitivan broj.")
        if v.kapacitet > 1000:
            raise ValidationError("Kapacitet ne može biti veći od 1000.")
        if v.cijena_kn < 0:
            raise ValidationError("Cijena ne može biti negativna.")
        if v.id_polazisne_stanice == v.id_odredisne_stanice:
            raise ValidationError("Polazišna i odredišna stanica ne smiju biti iste.")
        try:
            datetime.strptime(v.vrijeme_polaska, "%H:%M")
        except ValueError:
            raise ValidationError("Vrijeme polaska mora biti HH:MM.")
        try:
            datetime.strptime(v.vrijeme_dolaska, "%H:%M")
        except ValueError:
            raise ValidationError("Vrijeme dolaska mora biti HH:MM.")
        # Složena validacija: IC i EC moraju imati kapacitet >= 100
        tip = v.tip if isinstance(v.tip, TipVlaka) else next(
            (t for t in TipVlaka if t.value == v.tip), None
        )
        if tip in (TipVlaka.INTERCITY, TipVlaka.EUROCITY) and v.kapacitet < 100:
            raise ValidationError(
                f"{tip.value} vlakovi moraju imati kapacitet najmanje 100 mjesta."
            )
        if not self.stanica_repo.dohvati_po_id(v.id_polazisne_stanice):
            raise ValidationError("Polazišna stanica ne postoji.")
        if not self.stanica_repo.dohvati_po_id(v.id_odredisne_stanice):
            raise ValidationError("Odredišna stanica ne postoji.")
        return self.repo.spremi(v)

    def obrisi(self, id_: int) -> bool:
        return self.repo.obrisi(id_)


class KorisnikService:
    def __init__(self, repo: KorisnikRepository):
        self.repo = repo

    def dohvati_sve(self) -> List[Korisnik]:
        return self.repo.dohvati_sve()

    def dohvati_po_id(self, id_: int) -> Optional[Korisnik]:
        return self.repo.dohvati_po_id(id_)

    def pretrazi(self, upit: str) -> List[Korisnik]:
        return self.repo.pretrazi(upit)

    def hash_lozinke(self, lozinka: str) -> str:
        return hashlib.sha256(lozinka.encode()).hexdigest()
    
    def autentificiraj(self, email: str, lozinka: str):
        korisnik = self.repo.dohvati_po_emailu(email)
        if korisnik and korisnik.lozinka_hash == self.hash_lozinke(lozinka):
            return korisnik
        return None

    def spremi(self, k: Korisnik) -> Korisnik:
        if not k.ime or len(k.ime.strip()) < 2:
            raise ValidationError("Ime mora imati barem 2 znaka.")
        if not k.prezime or len(k.prezime.strip()) < 2:
            raise ValidationError("Prezime mora imati barem 2 znaka.")
        if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', k.email):
            raise ValidationError("Email nije u ispravnom formatu.")
        if not re.match(r'^\d{11}$', k.oib):
            raise ValidationError("OIB mora imati točno 11 znamenki.")
        self._validiraj_oib(k.oib)
        try:
            datum_rod = datetime.strptime(k.datum_rodenja, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Datum rođenja mora biti YYYY-MM-DD.")
        danas = date.today()
        if datum_rod >= danas:
            raise ValidationError("Datum rođenja mora biti u prošlosti.")
        starost = (danas - datum_rod).days // 365
        if starost > 120:
            raise ValidationError("Nevažeći datum rođenja.")
        tip = k.tip if isinstance(k.tip, TipKorisnika) else next(
            (t for t in TipKorisnika if t.value == k.tip), TipKorisnika.OBICAN
        )
        # Složena validacija: umirovljenici moraju imati 60+ godina
        if tip == TipKorisnika.UMIROVLJENIK and starost < 60:
            raise ValidationError(
                "Umirovljenici moraju imati barem 60 godina. "
                "Datum rođenja ne odgovara statusu umirovljenika."
            )
        # Složena validacija: studenti moraju imati studentski email ili biti mlađi od 30
        if tip == TipKorisnika.STUDENT:
            email_lower = k.email.lower()
            studentski = any(d in email_lower for d in ["@student.", "@fer.", ".edu"])
            if not studentski and starost >= 30:
                raise ValidationError(
                    "Studenti moraju imati studentski email (@student.*, @fer.*, *.edu) "
                    "ili biti mlađi od 30 godina."
                )
        return self.repo.spremi(k)

    def obrisi(self, id_: int) -> bool:
        return self.repo.obrisi(id_)

    def _validiraj_oib(self, oib: str):
        # Provjera kontrolne znamenke OIB-a
        try:
            a = 10
            for i in range(10):
                a = (a + int(oib[i])) % 10
                if a == 0:
                    a = 10
                a = (a * 2) % 11
            k = 11 - a
            if k == 10:
                k = 0
            if k != int(oib[10]):
                raise ValidationError("OIB nije ispravan (ne prolazi provjeru).")
        except (ValueError, IndexError):
            raise ValidationError("OIB mora sadržavati samo znamenke.")


class PopustService:
    def __init__(self, repo: PopustRepository):
        self.repo = repo

    def dohvati_sve(self) -> List[Popust]:
        return self.repo.dohvati_sve()

    def dohvati_po_id(self, id_: int) -> Optional[Popust]:
        return self.repo.dohvati_po_id(id_)

    def dohvati_za_korisnika(self, korisnik: Korisnik) -> Optional[Popust]:
        return self.repo.dohvati_po_tipu_korisnika(korisnik.tip)

    def spremi(self, p: Popust) -> Popust:
        if not p.naziv or len(p.naziv.strip()) < 3:
            raise ValidationError("Naziv popusta mora imati barem 3 znaka.")
        if not (0 <= p.postotak <= 100):
            raise ValidationError("Postotak mora biti između 0 i 100.")
        return self.repo.spremi(p)

    def obrisi(self, id_: int) -> bool:
        return self.repo.obrisi(id_)


class KartaService:
    def __init__(self, karta_repo: KartaRepository, vlak_repo: VlakRepository,
                 korisnik_repo: KorisnikRepository, popust_repo: PopustRepository,
                 sjedalo_repo: SjedaloRepository):
        self.karta_repo = karta_repo
        self.vlak_repo = vlak_repo
        self.korisnik_repo = korisnik_repo
        self.popust_repo = popust_repo
        self.sjedalo_repo = sjedalo_repo

    def dohvati_sve(self) -> List[Karta]:
        return self.karta_repo.dohvati_sve()

    def dohvati_po_id(self, id_: int) -> Optional[Karta]:
        return self.karta_repo.dohvati_po_id(id_)

    def dohvati_za_korisnika(self, id_k: int) -> List[Karta]:
        return self.karta_repo.dohvati_za_korisnika(id_k)

    def izracunaj_cijenu(self, vlak: Vlak, korisnik: Korisnik) -> Tuple[float, float]:
        popust = self.popust_repo.dohvati_po_tipu_korisnika(korisnik.tip)
        postotak = popust.postotak if (popust and popust.aktivan) else 0.0
        return round(vlak.cijena_kn * (1 - postotak / 100), 2), postotak

    def kupi_kartu(self, id_korisnika: int, id_vlaka: int,
                   datum_putovanja: str, id_sjedala: Optional[int] = None) -> Karta:
        korisnik = self.korisnik_repo.dohvati_po_id(id_korisnika)
        if not korisnik:
            raise ValidationError("Korisnik ne postoji.")
        vlak = self.vlak_repo.dohvati_po_id(id_vlaka)
        if not vlak:
            raise ValidationError("Vlak ne postoji.")
        try:
            datum_obj = datetime.strptime(datum_putovanja, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Datum putovanja mora biti YYYY-MM-DD.")
        if datum_obj < date.today():
            raise ValidationError("Datum putovanja ne može biti u prošlosti.")
        if id_sjedala is not None:
            zauzeta = self.karta_repo.dohvati_zauzetost_sjedala(id_vlaka, datum_putovanja)
            if id_sjedala in zauzeta:
                raise ValidationError("Odabrano sjedalo je već zauzeto za taj datum.")
        cijena, postotak = self.izracunaj_cijenu(vlak, korisnik)
        karta = Karta(
            id=None, id_korisnika=id_korisnika, id_vlaka=id_vlaka,
            id_sjedala=id_sjedala, datum_putovanja=datum_putovanja,
            datum_kupnje=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cijena_placena=cijena, status=StatusKarte.AKTIVNA,
            popust_postotak=postotak
        )
        return self.karta_repo.spremi(karta)

    def otkazi_kartu(self, id_karte: int) -> Karta:
        karta = self.karta_repo.dohvati_po_id(id_karte)
        if not karta:
            raise ValidationError("Karta ne postoji.")
        if karta.status == StatusKarte.OTKAZANA:
            raise ValidationError("Karta je već otkazana.")
        datum_put = datetime.strptime(karta.datum_putovanja, "%Y-%m-%d").date()
        if datum_put < date.today():
            raise ValidationError("Ne može se otkazati karta za putovanje koje je prošlo.")
        karta.status = StatusKarte.OTKAZANA
        return self.karta_repo.spremi(karta)

    def spremi(self, karta: Karta) -> Karta:
        return self.karta_repo.spremi(karta)

    def obrisi(self, id_: int) -> bool:
        return self.karta_repo.obrisi(id_)

    def dohvati_slobodna_sjedala(self, id_vlaka: int, datum: str) -> List[SjedaloVlaka]:
        return self.sjedalo_repo.dohvati_slobodna(id_vlaka, datum)