import pytest
from datetime import date, timedelta

from tests.config import *

# Jedinični testovi poslovnog sloja (BLL)

class TestStanicaService:

    def test_spremi_ispravnu_stanicu(self, servisi):
        s = servisi["stanica"].spremi(nova_stanica())
        assert s.id is not None

    def test_prekratak_naziv_baca_greski(self, servisi):
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="[Nn]aziv"):
            servisi["stanica"].spremi(Stanica(None, "Z", "Zagreb", "GZ"))

    def test_prazan_grad_baca_greski(self, servisi):
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="Grad"):
            servisi["stanica"].spremi(Stanica(None, "Kolodvor", "", "GZ"))

    def test_brisanje_stanice(self, servisi):
        s = servisi["stanica"].spremi(nova_stanica())
        assert servisi["stanica"].obrisi(s.id) is True


class TestVlakService:

    def _pripremi_stanice(self, servisi):
        s1 = servisi["stanica"].spremi(nova_stanica("Zagreb GK"))
        s2 = servisi["stanica"].spremi(nova_stanica("Split", "Split", "SDŽ"))
        return s1, s2

    def test_spremi_ispravan_ic_vlak(self, servisi):
        s1, s2 = self._pripremi_stanice(servisi)
        v = servisi["vlak"].spremi(novi_vlak(s1.id, s2.id))
        assert v.id is not None

    def test_iste_stanice_baca_greski(self, servisi):
        from bll.services import ValidationError
        s1, _ = self._pripremi_stanice(servisi)
        with pytest.raises(ValidationError, match="iste"):
            servisi["vlak"].spremi(novi_vlak(s1.id, s1.id))

    def test_negativna_cijena_baca_greski(self, servisi):
        from bll.services import ValidationError
        s1, s2 = self._pripremi_stanice(servisi)
        with pytest.raises(ValidationError, match="negativna"):
            servisi["vlak"].spremi(novi_vlak(s1.id, s2.id, cijena=-5.0))

    def test_ic_kapacitet_manji_od_100_baca_greski(self, servisi):
        """Složena validacija: IC vlakovi moraju imati >= 100 mjesta."""
        from bll.services import ValidationError
        s1, s2 = self._pripremi_stanice(servisi)
        with pytest.raises(ValidationError, match="100"):
            servisi["vlak"].spremi(
                novi_vlak(s1.id, s2.id, tip=TipVlaka.INTERCITY, kap=50))

    def test_regionalni_moze_imati_mali_kapacitet(self, servisi):
        s1, s2 = self._pripremi_stanice(servisi)
        v = servisi["vlak"].spremi(
            novi_vlak(s1.id, s2.id, "R-SMALL", TipVlaka.REGIONALNI, kap=40))
        assert v.id is not None

    def test_krivi_format_vremena_baca_greski(self, servisi):
        from bll.services import ValidationError
        s1, s2 = self._pripremi_stanice(servisi)
        v = novi_vlak(s1.id, s2.id)
        v.vrijeme_polaska = "25:00"   # neispravno vrijeme
        with pytest.raises(ValidationError, match="HH:MM"):
            servisi["vlak"].spremi(v)

    def test_ec_kapacitet_manji_od_100_baca_greski(self, servisi):
        """Složena validacija: EC vlakovi moraju imati >= 100 mjesta."""
        from bll.services import ValidationError
        s1, s2 = self._pripremi_stanice(servisi)
        with pytest.raises(ValidationError, match="100"):
            servisi["vlak"].spremi(
                novi_vlak(s1.id, s2.id, tip=TipVlaka.EUROCITY, kap=80))

    def test_nepostojeca_stanica_baca_greski(self, servisi):
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="[Pp]olazišna"):
            servisi["vlak"].spremi(novi_vlak(999, 998))


class TestKorisnikService:

    def test_spremi_ispravnog_korisnika(self, servisi):
        k = servisi["korisnik"].spremi(novi_korisnik())
        assert k.id is not None

    def test_kratko_ime_baca_greski(self, servisi):
        from bll.services import ValidationError
        k = novi_korisnik(); k.ime = "A"
        with pytest.raises(ValidationError, match="[Ii]me"):
            servisi["korisnik"].spremi(k)

    def test_krivi_email_format_baca_greski(self, servisi):
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="[Ee]mail"):
            servisi["korisnik"].spremi(novi_korisnik(email="nije_email"))

    def test_oib_kriva_duljina_baca_greski(self, servisi):
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="OIB"):
            servisi["korisnik"].spremi(novi_korisnik(oib="123456"))

    def test_neispravan_oib_checksum_baca_greski(self, servisi):
        """OIB prolazi duljinu ali pada ISO 7064 MOD 11,10 provjeru."""
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="OIB"):
            servisi["korisnik"].spremi(novi_korisnik(oib="00000000000"))

    def test_buduci_datum_rodenja_baca_greski(self, servisi):
        from bll.services import ValidationError
        buducnost = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        with pytest.raises(ValidationError, match="pro\u0161losti"):
            servisi["korisnik"].spremi(novi_korisnik(oib="98765432106", datum_rod=buducnost))

    def test_umirovljenik_mladi_od_60_baca_greski(self, servisi):
        """Složena validacija: umirovljenik mora imati >= 60 godina."""
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="60"):
            servisi["korisnik"].spremi(
                novi_korisnik(oib="98765432106", tip=TipKorisnika.UMIROVLJENIK,
                              datum_rod="2000-01-01"))

    def test_umirovljenik_stariji_60_prolazi(self, servisi):
        k = servisi["korisnik"].spremi(
            novi_korisnik(oib="98765432106", tip=TipKorisnika.UMIROVLJENIK,
                          datum_rod="1950-06-15"))
        assert k.id is not None

    def test_hash_lozinke_je_deterministican(self, servisi):
        h1 = servisi["korisnik"].hash_lozinke("lozinka")
        h2 = servisi["korisnik"].hash_lozinke("lozinka")
        h3 = servisi["korisnik"].hash_lozinke("druga")
        assert h1 == h2 and h1 != h3

    def test_autentifikacija_ispravnih_podataka(self, servisi):
        import hashlib
        k = Korisnik(
            None, "Marko", "Markić", "marko@test.com",
            hashlib.sha256("loz123".encode()).hexdigest(),
            TipKorisnika.OBICAN, "1990-01-01", "12345678903"
        )
        servisi["korisnik"].spremi(k)
        rez = servisi["korisnik"].autentificiraj("marko@test.com", "loz123")
        assert rez is not None and rez.email == "marko@test.com"

    def test_autentifikacija_krive_lozinke_vraca_none(self, servisi):
        import hashlib
        k = Korisnik(
            None, "Ana", "Anić", "ana@test.com",
            hashlib.sha256("ispravna".encode()).hexdigest(),
            TipKorisnika.OBICAN, "1992-03-10", "12345678903"
        )
        servisi["korisnik"].spremi(k)
        assert servisi["korisnik"].autentificiraj("ana@test.com", "pogresna") is None


class TestPopustService:

    def test_spremi_ispravan_popust(self, servisi):
        p = Popust(None, "Studentski", TipKorisnika.STUDENT, 50.0, True)
        rez = servisi["popust"].spremi(p)
        assert rez.id is not None

    def test_prekratak_naziv_baca_greski(self, servisi):
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="[Nn]aziv"):
            servisi["popust"].spremi(
                Popust(None, "Xx", TipKorisnika.STUDENT, 50.0))

    def test_postotak_veci_od_100_baca_greski(self, servisi):
        from bll.services import ValidationError
        with pytest.raises(ValidationError, match="100"):
            servisi["popust"].spremi(
                Popust(None, "Nevažeći", TipKorisnika.OBICAN, 110.0))

    def test_negativan_postotak_baca_greski(self, servisi):
        from bll.services import ValidationError
        with pytest.raises(ValidationError):
            servisi["popust"].spremi(
                Popust(None, "Nevažeći", TipKorisnika.OBICAN, -5.0))


class TestKartaService:

    def _pripremi(self, servisi):
        s1 = servisi["stanica"].spremi(nova_stanica("Zagreb GK"))
        s2 = servisi["stanica"].spremi(nova_stanica("Split", "Split", "SDŽ"))
        v  = servisi["vlak"].spremi(novi_vlak(s1.id, s2.id,
                                               tip=TipVlaka.INTERCITY, kap=200))
        k  = servisi["korisnik"].spremi(novi_korisnik())
        return v, k

    def _sutra(self):
        return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    def test_kupnja_karte_uspjesno(self, servisi):
        v, k = self._pripremi(servisi)
        karta = servisi["karta"].kupi_kartu(k.id, v.id, self._sutra())
        assert karta.id is not None
        assert karta.status == StatusKarte.AKTIVNA

    def test_kupnja_prosli_datum_baca_greski(self, servisi):
        from bll.services import ValidationError
        v, k = self._pripremi(servisi)
        jucer = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        with pytest.raises(ValidationError, match="prošlosti"):
            servisi["karta"].kupi_kartu(k.id, v.id, jucer)

    def test_kupnja_nepostojeci_korisnik_baca_greski(self, servisi):
        from bll.services import ValidationError
        v, _ = self._pripremi(servisi)
        with pytest.raises(ValidationError, match="Korisnik"):
            servisi["karta"].kupi_kartu(9999, v.id, self._sutra())

    def test_kupnja_nepostojeci_vlak_baca_greski(self, servisi):
        from bll.services import ValidationError
        _, k = self._pripremi(servisi)
        with pytest.raises(ValidationError, match="Vlak"):
            servisi["karta"].kupi_kartu(k.id, 9999, self._sutra())

    def test_student_dobiva_50_posto_popusta(self, servisi):
        s1 = servisi["stanica"].spremi(nova_stanica("Stanica AA"))
        s2 = servisi["stanica"].spremi(nova_stanica("Stanica BB", "Grad B", "Županija B"))
        v  = servisi["vlak"].spremi(novi_vlak(s1.id, s2.id,
                                               tip=TipVlaka.INTERCITY, kap=150,
                                               cijena=100.0))
        servisi["popust"].spremi(
            Popust(None, "Studentski", TipKorisnika.STUDENT, 50.0, True))
        k = servisi["korisnik"].spremi(
            novi_korisnik("s@student.hr", "23456789013",
                          TipKorisnika.STUDENT, "2003-05-10"))
        karta = servisi["karta"].kupi_kartu(k.id, v.id, self._sutra())
        assert karta.cijena_placena == 50.0
        assert karta.popust_postotak == 50.0

    def test_otkazivanje_karte_uspjesno(self, servisi):
        v, k = self._pripremi(servisi)
        karta = servisi["karta"].kupi_kartu(k.id, v.id, self._sutra())
        otkazana = servisi["karta"].otkazi_kartu(karta.id)
        assert otkazana.status == StatusKarte.OTKAZANA

    def test_dvostruko_otkazivanje_baca_greski(self, servisi):
        from bll.services import ValidationError
        v, k = self._pripremi(servisi)
        karta = servisi["karta"].kupi_kartu(k.id, v.id, self._sutra())
        servisi["karta"].otkazi_kartu(karta.id)
        with pytest.raises(ValidationError, match="već otkazana"):
            servisi["karta"].otkazi_kartu(karta.id)

    def test_zauzeto_sjedalo_baca_greski(self, servisi):
        from bll.services import ValidationError
        v, k = self._pripremi(servisi)
        db = servisi["db"]
        db.get_connection().execute(
            "INSERT INTO sjedalo_vlaka VALUES (NULL,?,7,'V1',2)", (v.id,))
        db.get_connection().commit()
        sj_id = db.get_connection().execute(
            "SELECT id FROM sjedalo_vlaka WHERE id_vlaka=?", (v.id,)
        ).fetchone()["id"]
        k2 = servisi["korisnik"].spremi(
            novi_korisnik("drugi@test.com", "23456789013"))
        datum = self._sutra()
        servisi["karta"].kupi_kartu(k.id, v.id, datum, sj_id)
        with pytest.raises(ValidationError, match="zauzeto"):
            servisi["karta"].kupi_kartu(k2.id, v.id, datum, sj_id)