"""
HŽPlus Jedinični testovi prezentacijskog sloja (UI)
Testira logiku forme neovisno od tkinter renderiranja.
Klase se testiraju kroz njihove servise i stanje,
bez pokretanja GUI prozora.
"""
import pytest
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.config import *
from bll.services import ValidationError
from models.entities import TipVlaka, TipKorisnika, StatusKarte
from datetime import date, timedelta


class TestPrezentacijskaLogikaPrijave:

    def test_prijava_ispravnih_podataka_vraca_korisnika(self, servisi):
        k = Korisnik(
            None, "Ana", "Anić", "ana@test.com",
            hashlib.sha256("Loz123!".encode()).hexdigest(),
            TipKorisnika.OBICAN, "1995-03-15", "12345678903"
        )
        servisi["korisnik"].spremi(k)
        rez = servisi["korisnik"].autentificiraj("ana@test.com", "Loz123!")
        assert rez is not None
        assert rez.puno_ime == "Ana Anić"

    def test_prijava_nepostojeci_email_vraca_none(self, servisi):
        assert servisi["korisnik"].autentificiraj("ne@postoji.hr", "loz") is None

    def test_prijava_kriva_lozinka_vraca_none(self, servisi):
        k = Korisnik(
            None, "Pero", "Perić", "pero@test.com",
            hashlib.sha256("ispravna".encode()).hexdigest(),
            TipKorisnika.OBICAN, "1988-07-20", "12345678903"
        )
        servisi["korisnik"].spremi(k)
        assert servisi["korisnik"].autentificiraj("pero@test.com", "kriva") is None

    def test_registracija_validacija_umirovljenik_premlade(self, servisi):
        """Forma ne smije dopustiti registraciju umirovljenika mlađeg od 60."""
        k = novi_korisnik(oib="98765432106", tip=TipKorisnika.UMIROVLJENIK, datum_rod="2000-01-01")
        with pytest.raises(ValidationError, match="60"):
            servisi["korisnik"].spremi(k)

    def test_registracija_validacija_krivog_emaila(self, servisi):
        """Forma ne smije prihvatiti email bez @ i domene."""
        k = novi_korisnik(email="nije-email-format")
        with pytest.raises(ValidationError, match="[Ee]mail"):
            servisi["korisnik"].spremi(k)

    def test_registracija_hash_lozinke_nije_plain_text(self, servisi):
        """Forma mora hashirati lozinku — ne smije pohraniti plain text."""
        k = Korisnik(
            None, "Test", "Testović", "tt@t.com",
            servisi["korisnik"].hash_lozinke("lozinka"),
            TipKorisnika.OBICAN, "1990-01-01", "12345678903"
        )
        servisi["korisnik"].spremi(k)
        doh = servisi["korisnik"].repo.dohvati_po_emailu("tt@t.com")
        assert doh.lozinka_hash != "lozinka"
        assert len(doh.lozinka_hash) == 64   # SHA-256 hex


class TestPrezentacijskaLogikaKupnjeKarte:
    """
    Testira logiku korisničkog portala:
    pretraživanje vlakova, kupnja, otkazivanje.
    Testira kroz KartaService koji portal koristi.
    """

    def _pripremi_sustav(self, servisi):
        s1 = servisi["stanica"].spremi(nova_stanica("Zagreb GK"))
        s2 = servisi["stanica"].spremi(nova_stanica("Split", "Split", "SDŽ"))
        v  = servisi["vlak"].spremi(
            novi_vlak(s1.id, s2.id, tip=TipVlaka.INTERCITY,
                      kap=200, cijena=100.0))
        servisi["popust"].spremi(
            Popust(None, "Studentski", TipKorisnika.STUDENT, 50.0, True))
        k_obican  = servisi["korisnik"].spremi(
            novi_korisnik("obican@test.com", "12345678903"))
        k_student = servisi["korisnik"].spremi(
            novi_korisnik("student@student.hr", "23456789013",
                          TipKorisnika.STUDENT, "2003-06-10"))
        return v, k_obican, k_student

    def _sutra(self):
        return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    def test_forma_prikaza_cijene_s_popustom_za_studenta(self, servisi):
        """Portal mora pokazati smanjenu cijenu studentu."""
        v, _, k_student = self._pripremi_sustav(servisi)
        cijena, popust = servisi["karta"].izracunaj_cijenu(v, k_student)
        assert cijena == 50.0
        assert popust == 50.0

    def test_forma_prikaza_pune_cijene_za_obicnog_korisnika(self, servisi):
        """Portal mora pokazati punu cijenu obicnom korisniku."""
        v, k_obican, _ = self._pripremi_sustav(servisi)
        cijena, popust = servisi["karta"].izracunaj_cijenu(v, k_obican)
        assert cijena == 100.0
        assert popust == 0.0

    def test_gumb_kupi_kreira_kartu(self, servisi):
        """Akcija kupnje u portalu mora kreirati kartu u sustavu."""
        v, k_obican, _ = self._pripremi_sustav(servisi)
        karta = servisi["karta"].kupi_kartu(k_obican.id, v.id, self._sutra())
        assert karta.id is not None
        assert karta.status == StatusKarte.AKTIVNA

    def test_gumb_kupi_s_proslim_datumom_baca_greski(self, servisi):
        """Forma mora spriječiti odabir prošlog datuma."""
        v, k, _ = self._pripremi_sustav(servisi)
        jucer = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        with pytest.raises(ValidationError, match="prošlosti"):
            servisi["karta"].kupi_kartu(k.id, v.id, jucer)

    def test_moje_karte_vraca_samo_karte_korisnika(self, servisi):
        """Tab 'Moje karte' smije prikazati samo karte prijavljenog korisnika."""
        v, k1, k2 = self._pripremi_sustav(servisi)
        datum = self._sutra()
        servisi["karta"].kupi_kartu(k1.id, v.id, datum)
        servisi["karta"].kupi_kartu(k2.id, v.id, datum)
        karte_k1 = servisi["karta"].dohvati_za_korisnika(k1.id)
        karte_k2 = servisi["karta"].dohvati_za_korisnika(k2.id)
        assert len(karte_k1) == 1 and karte_k1[0].id_korisnika == k1.id
        assert len(karte_k2) == 1 and karte_k2[0].id_korisnika == k2.id

    def test_gumb_otkazi_mijenja_status_na_otkazana(self, servisi):
        """Akcija otkazivanja mora promijeniti status karte."""
        v, k, _ = self._pripremi_sustav(servisi)
        karta = servisi["karta"].kupi_kartu(k.id, v.id, self._sutra())
        rez = servisi["karta"].otkazi_kartu(karta.id)
        assert rez.status == StatusKarte.OTKAZANA

    def test_ne_moze_otkazati_vec_otkazanu_kartu(self, servisi):
        """Gumb za otkazivanje mora biti blokiran za već otkazane karte."""
        v, k, _ = self._pripremi_sustav(servisi)
        karta = servisi["karta"].kupi_kartu(k.id, v.id, self._sutra())
        servisi["karta"].otkazi_kartu(karta.id)
        with pytest.raises(ValidationError, match="već otkazana"):
            servisi["karta"].otkazi_kartu(karta.id)


class TestPrezentacijskaLogikaAdminVlakova:
    """
    Testira logiku admin portala za upravljanje vlakovima (Master-Detail).
    Testira kroz VlakService koji admin forma koristi.
    """

    def _pripremi_stanice(self, servisi):
        s1 = servisi["stanica"].spremi(nova_stanica("Zagreb GK"))
        s2 = servisi["stanica"].spremi(nova_stanica("Rijeka", "Rijeka", "PGŽ"))
        return s1, s2

    def test_forma_sprema_novi_vlak(self, servisi):
        s1, s2 = self._pripremi_stanice(servisi)
        v = servisi["vlak"].spremi(novi_vlak(s1.id, s2.id))
        assert v.id is not None

    def test_forma_ne_dozvoljava_isti_polazak_i_odrediste(self, servisi):
        from bll.services import ValidationError
        s1, _ = self._pripremi_stanice(servisi)
        with pytest.raises(ValidationError, match="iste"):
            servisi["vlak"].spremi(novi_vlak(s1.id, s1.id))

    def test_forma_zahtijeva_kapacitet_100_za_ic(self, servisi):
        """Master forma mora odbiti IC vlak s kapacitetom < 100."""
        from bll.services import ValidationError
        s1, s2 = self._pripremi_stanice(servisi)
        with pytest.raises(ValidationError, match="100"):
            servisi["vlak"].spremi(
                novi_vlak(s1.id, s2.id, tip=TipVlaka.INTERCITY, kap=80))

    def test_detail_karte_vraca_karte_za_vlak(self, servisi):
        """Detail prikaz smije prikazati samo karte za odabrani vlak."""
        s1, s2 = self._pripremi_stanice(servisi)
        v1 = servisi["vlak"].spremi(novi_vlak(s1.id, s2.id, "IC-A"))
        v2 = servisi["vlak"].spremi(
            novi_vlak(s1.id, s2.id, "R-B", TipVlaka.REGIONALNI))
        k = servisi["korisnik"].spremi(novi_korisnik())
        datum = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        servisi["karta"].kupi_kartu(k.id, v1.id, datum)
        servisi["karta"].kupi_kartu(k.id, v2.id, datum)
        sve_karte = servisi["karta"].dohvati_sve()
        karte_v1 = [ka for ka in sve_karte if ka.id_vlaka == v1.id]
        karte_v2 = [ka for ka in sve_karte if ka.id_vlaka == v2.id]
        assert len(karte_v1) == 1
        assert len(karte_v2) == 1

    def test_brisanje_vlaka(self, servisi):
        s1, s2 = self._pripremi_stanice(servisi)
        v = servisi["vlak"].spremi(novi_vlak(s1.id, s2.id))
        assert servisi["vlak"].obrisi(v.id) is True
        assert servisi["vlak"].dohvati_po_id(v.id) is None