from dataclasses import dataclass
from typing import Optional
from enum import Enum


class TipKorisnika(Enum):
    OBICAN = "Obični"
    STUDENT = "Student"
    UCENIK = "Učenik"
    UMIROVLJENIK = "Umirovljenik"
    INVALID = "Osoba s invaliditetom"


class StatusKarte(Enum):
    AKTIVNA = "Aktivna"
    ISKORISHTENA = "Iskorištena"
    OTKAZANA = "Otkazana"


class TipVlaka(Enum):
    PUTNICKI = "Putnički"
    INTERCITY = "InterCity"
    EUROCITY = "EuroCity"
    REGIONALNI = "Regionalni"


@dataclass
class Stanica:
    id: Optional[int]
    naziv: str
    grad: str
    zupanija: str

    def __str__(self):
        return f"{self.naziv} ({self.grad})"


@dataclass
class Vlak:
    id: Optional[int]
    broj_vlaka: str
    tip: TipVlaka
    kapacitet: int
    id_polazisne_stanice: int
    id_odredisne_stanice: int
    vrijeme_polaska: str
    vrijeme_dolaska: str
    cijena_kn: float
    naziv_polazisne: Optional[str] = None
    naziv_odredisne: Optional[str] = None

    def __str__(self):
        pol = self.naziv_polazisne or f"Stanica {self.id_polazisne_stanice}"
        odred = self.naziv_odredisne or f"Stanica {self.id_odredisne_stanice}"
        return f"Vlak {self.broj_vlaka}: {pol} → {odred} ({self.vrijeme_polaska})"


@dataclass
class Korisnik:
    id: Optional[int]
    ime: str
    prezime: str
    email: str
    lozinka_hash: str
    tip: TipKorisnika
    datum_rodenja: str
    oib: str
    telefon: Optional[str] = None

    @property
    def puno_ime(self) -> str:
        return f"{self.ime} {self.prezime}"

    def __str__(self):
        return f"{self.puno_ime} ({self.email})"


@dataclass
class SjedaloVlaka:
    id: Optional[int]
    id_vlaka: int
    broj_sjedala: int
    oznaka_vagon: str
    razred: int


@dataclass
class Karta:
    id: Optional[int]
    id_korisnika: int
    id_vlaka: int
    id_sjedala: Optional[int]
    datum_putovanja: str
    datum_kupnje: str
    cijena_placena: float
    status: StatusKarte
    popust_postotak: float = 0.0
    korisnik_ime: Optional[str] = None
    vlak_broj: Optional[str] = None
    polazisna: Optional[str] = None
    odredisna: Optional[str] = None
    broj_sjedala: Optional[str] = None

    def status_label(self) -> str:
        return self.status.value if isinstance(self.status, StatusKarte) else self.status


@dataclass
class Popust:
    id: Optional[int]
    naziv: str
    tip_korisnika: TipKorisnika
    postotak: float
    aktivan: bool = True
    opis: Optional[str] = None

    def __str__(self):
        return f"{self.naziv} ({self.postotak}%)"