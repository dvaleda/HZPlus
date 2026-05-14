import pytest
import hashlib
from datetime import date, timedelta

from tests.config import *

# Jedinični testovi sloja za pristup podacima (DAL)

class TestStanicaRepository:
    """Testovi CRUD operacija nad StanicaRepository."""

    def test_spremi_novu_stanicu_dodjeljuje_id(self, repozitoriji):
        repo = repozitoriji["stanica"]
        s = repo.spremi(nova_stanica())
        assert s.id is not None and s.id > 0

    def test_dohvati_po_id_vraca_ispravne_podatke(self, repozitoriji):
        repo = repozitoriji["stanica"]
        s = repo.spremi(nova_stanica("Split", "Split", "SDŽ"))
        doh = repo.dohvati_po_id(s.id)
        assert doh is not None
        assert doh.naziv == "Split"
        assert doh.grad == "Split"

    def test_dohvati_sve_vraca_sve_stanice(self, repozitoriji):
        repo = repozitoriji["stanica"]
        repo.spremi(nova_stanica("Zagreb GK"))
        repo.spremi(nova_stanica("Rijeka", "Rijeka", "PGŽ"))
        repo.spremi(nova_stanica("Osijek", "Osijek", "OBŽ"))
        assert len(repo.dohvati_sve()) == 3

    def test_azuriranje_mijenja_naziv(self, repozitoriji):
        repo = repozitoriji["stanica"]
        s = repo.spremi(nova_stanica("Stari"))
        s.naziv = "Novi"
        repo.spremi(s)
        assert repo.dohvati_po_id(s.id).naziv == "Novi"

    def test_brisanje_vraca_true_i_uklanja_zapis(self, repozitoriji):
        repo = repozitoriji["stanica"]
        s = repo.spremi(nova_stanica())
        assert repo.obrisi(s.id) is True
        assert repo.dohvati_po_id(s.id) is None

    def test_brisanje_nepostojece_vraca_false(self, repozitoriji):
        assert repozitoriji["stanica"].obrisi(99999) is False

    def test_pretraga_po_dijelu_naziva(self, repozitoriji):
        repo = repozitoriji["stanica"]
        repo.spremi(nova_stanica("Zagreb GK"))
        repo.spremi(nova_stanica("Zadar", "Zadar", "ZDŽ"))
        rez = repo.pretrazi("Zagr")
        assert len(rez) == 1 and rez[0].naziv == "Zagreb GK"

    def test_pretraga_praznim_upitom_vraca_sve(self, repozitoriji):
        repo = repozitoriji["stanica"]
        repo.spremi(nova_stanica("A", "A", "A"))
        repo.spremi(nova_stanica("B", "B", "B"))
        assert len(repo.pretrazi("")) == 2


class TestVlakRepository:
    """Testovi CRUD i JOIN operacija nad VlakRepository."""

    def _stanice(self, repo):
        s1 = repo.spremi(nova_stanica("Zagreb GK"))
        s2 = repo.spremi(nova_stanica("Split", "Split", "SDŽ"))
        return s1, s2

    def test_spremi_novi_vlak(self, repozitoriji):
        s1, s2 = self._stanice(repozitoriji["stanica"])
        v = repozitoriji["vlak"].spremi(novi_vlak(s1.id, s2.id))
        assert v.id is not None

    def test_dohvat_ukljucuje_nazive_stanica(self, repozitoriji):
        s1, s2 = self._stanice(repozitoriji["stanica"])
        v = repozitoriji["vlak"].spremi(novi_vlak(s1.id, s2.id))
        doh = repozitoriji["vlak"].dohvati_po_id(v.id)
        assert doh.naziv_polazisne == "Zagreb GK"
        assert doh.naziv_odredisne == "Split"

    def test_brisanje_vlaka(self, repozitoriji):
        s1, s2 = self._stanice(repozitoriji["stanica"])
        v = repozitoriji["vlak"].spremi(novi_vlak(s1.id, s2.id))
        assert repozitoriji["vlak"].obrisi(v.id) is True
        assert repozitoriji["vlak"].dohvati_po_id(v.id) is None

    def test_pretraga_po_broju_vlaka(self, repozitoriji):
        s1, s2 = self._stanice(repozitoriji["stanica"])
        repozitoriji["vlak"].spremi(novi_vlak(s1.id, s2.id, "IC-100"))
        repozitoriji["vlak"].spremi(novi_vlak(s1.id, s2.id, "R-200",
                                              TipVlaka.REGIONALNI))
        rez = repozitoriji["vlak"].pretrazi("IC")
        assert len(rez) == 1 and rez[0].broj_vlaka == "IC-100"

    def test_azuriranje_cijene(self, repozitoriji):
        s1, s2 = self._stanice(repozitoriji["stanica"])
        v = repozitoriji["vlak"].spremi(novi_vlak(s1.id, s2.id))
        v.cijena_kn = 120.0
        repozitoriji["vlak"].spremi(v)
        assert repozitoriji["vlak"].dohvati_po_id(v.id).cijena_kn == 120.0


class TestKorisnikRepository:
    """Testovi CRUD operacija nad KorisnikRepository."""

    def test_spremi_novog_korisnika(self, repozitoriji):
        k = repozitoriji["korisnik"].spremi(novi_korisnik())
        assert k.id is not None

    def test_dohvati_po_emailu(self, repozitoriji):
        repozitoriji["korisnik"].spremi(novi_korisnik("marko@test.com"))
        doh = repozitoriji["korisnik"].dohvati_po_emailu("marko@test.com")
        assert doh is not None and doh.ime == "Test"

    def test_dohvati_nepostojeci_email_vraca_none(self, repozitoriji):
        assert repozitoriji["korisnik"].dohvati_po_emailu("ne@postoji.hr") is None

    def test_azuriranje_tipa(self, repozitoriji):
        k = repozitoriji["korisnik"].spremi(novi_korisnik())
        k.tip = TipKorisnika.STUDENT
        repozitoriji["korisnik"].spremi(k)
        assert repozitoriji["korisnik"].dohvati_po_id(k.id).tip == TipKorisnika.STUDENT

    def test_brisanje_korisnika(self, repozitoriji):
        k = repozitoriji["korisnik"].spremi(novi_korisnik())
        assert repozitoriji["korisnik"].obrisi(k.id) is True
        assert repozitoriji["korisnik"].dohvati_po_id(k.id) is None

    def test_pretraga_po_prezimenu(self, repozitoriji):
        k = repozitoriji["korisnik"].spremi(novi_korisnik())
        rez = repozitoriji["korisnik"].pretrazi("Korisnik")
        assert len(rez) >= 1


class TestKartaRepository:
    """Testovi operacija nad KartaRepository."""

    def _pripremi(self, repozitoriji):
        s1 = repozitoriji["stanica"].spremi(nova_stanica("ZG"))
        s2 = repozitoriji["stanica"].spremi(nova_stanica("ST", "Split", "SDŽ"))
        v  = repozitoriji["vlak"].spremi(novi_vlak(s1.id, s2.id))
        k  = repozitoriji["korisnik"].spremi(novi_korisnik())
        return v, k

    def _sutra(self):
        return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    def test_spremi_kartu(self, repozitoriji):
        v, k = self._pripremi(repozitoriji)
        karta = Karta(None, k.id, v.id, None, self._sutra(),
                      "2026-01-01 10:00:00", 85.0, StatusKarte.AKTIVNA, 0.0)
        rez = repozitoriji["karta"].spremi(karta)
        assert rez.id is not None

    def test_dohvati_za_korisnika(self, repozitoriji):
        v, k = self._pripremi(repozitoriji)
        karta = Karta(None, k.id, v.id, None, self._sutra(),
                      "2026-01-01 10:00:00", 85.0, StatusKarte.AKTIVNA, 0.0)
        repozitoriji["karta"].spremi(karta)
        rez = repozitoriji["karta"].dohvati_za_korisnika(k.id)
        assert len(rez) == 1 and rez[0].id_korisnika == k.id

    def test_zauzetost_sjedala(self, repozitoriji):
        v, k = self._pripremi(repozitoriji)
        db = repozitoriji["db"]
        db.get_connection().execute(
            "INSERT INTO sjedalo_vlaka VALUES (NULL,?,5,'V1',2)", (v.id,))
        db.get_connection().commit()
        sj_id = db.get_connection().execute(
            "SELECT id FROM sjedalo_vlaka WHERE id_vlaka=?", (v.id,)
        ).fetchone()["id"]

        datum = self._sutra()
        karta = Karta(None, k.id, v.id, sj_id, datum,
                      "2026-01-01 10:00:00", 85.0, StatusKarte.AKTIVNA, 0.0)
        repozitoriji["karta"].spremi(karta)
        zauzeta = repozitoriji["karta"].dohvati_zauzetost_sjedala(v.id, datum)
        assert sj_id in zauzeta

    def test_otkazana_karta_nije_zauzeto_sjedalo(self, repozitoriji):
        v, k = self._pripremi(repozitoriji)
        db = repozitoriji["db"]
        db.get_connection().execute(
            "INSERT INTO sjedalo_vlaka VALUES (NULL,?,3,'V1',2)", (v.id,))
        db.get_connection().commit()
        sj_id = db.get_connection().execute(
            "SELECT id FROM sjedalo_vlaka WHERE id_vlaka=?", (v.id,)
        ).fetchone()["id"]

        datum = self._sutra()
        karta = Karta(None, k.id, v.id, sj_id, datum,
                      "2026-01-01 10:00:00", 85.0, StatusKarte.OTKAZANA, 0.0)
        repozitoriji["karta"].spremi(karta)
        zauzeta = repozitoriji["karta"].dohvati_zauzetost_sjedala(v.id, datum)
        assert sj_id not in zauzeta