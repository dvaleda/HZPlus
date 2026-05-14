import pytest
import hashlib
from datetime import date, timedelta

from tests.config import *
from bll.services import ValidationError

# Integracijski testovi (DAL, BLL i UI logika međusobno ispravno povezani)

class TestIntegracija:

    def test_cijeli_tok_registracije_i_kupnje(self, servisi):
        """
        Integracija: stanica→vlak→korisnik→popust→kupnja→provjera u DAL.
        Svaki sloj mora vidjeti ispravan zapis.
        """
        s1 = servisi["stanica"].spremi(nova_stanica("Zagreb GK"))
        s2 = servisi["stanica"].spremi(nova_stanica("Split", "Split", "SDŽ"))
        v  = servisi["vlak"].spremi(
            novi_vlak(s1.id, s2.id, tip=TipVlaka.INTERCITY,
                      kap=200, cijena=100.0))
        servisi["popust"].spremi(
            Popust(None, "Studentski", TipKorisnika.STUDENT, 50.0, True))
        k  = servisi["korisnik"].spremi(
            novi_korisnik("tin@student.hr", "12345678903",
                          TipKorisnika.STUDENT, "2002-05-20"))
        datum = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        karta = servisi["karta"].kupi_kartu(k.id, v.id, datum)

        # Provjera na DAL razini
        doh = servisi["karta"].dohvati_po_id(karta.id)
        assert doh is not None
        assert doh.id_korisnika == k.id
        assert doh.id_vlaka == v.id
        assert doh.cijena_placena == 50.0
        assert doh.popust_postotak == 50.0
        assert doh.status == StatusKarte.AKTIVNA

    def test_bll_sprecava_dvostruku_rezervaciju_sjedala(self, servisi):
        """
        Integracija: BLL mora spriječiti dva korisnika
        da rezerviraju isto sjedalo na isti datum.
        """
        s1 = servisi["stanica"].spremi(nova_stanica("Stanica AA"))
        s2 = servisi["stanica"].spremi(nova_stanica("Stanica BB", "Grad B", "Županija B"))
        v  = servisi["vlak"].spremi(
            novi_vlak(s1.id, s2.id, tip=TipVlaka.REGIONALNI, kap=50))
        db = servisi["db"]
        db.get_connection().execute(
            "INSERT INTO sjedalo_vlaka VALUES (NULL,?,1,'V1',2)", (v.id,))
        db.get_connection().commit()
        sj_id = db.get_connection().execute(
            "SELECT id FROM sjedalo_vlaka WHERE id_vlaka=?", (v.id,)
        ).fetchone()["id"]
        k1 = servisi["korisnik"].spremi(novi_korisnik("k1@t.com", "12345678903"))
        k2 = servisi["korisnik"].spremi(novi_korisnik("k2@t.com", "23456789013"))
        datum = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        servisi["karta"].kupi_kartu(k1.id, v.id, datum, sj_id)
        with pytest.raises(ValidationError, match="zauzeto"):
            servisi["karta"].kupi_kartu(k2.id, v.id, datum, sj_id)

    def test_bll_validacija_sprecava_upis_losih_podataka_u_dal(self, servisi):
        """
        Integracija: neispravni podaci moraju biti odbijeni PRIJE
        nego što dotaknu DAL/bazu. Baza mora ostati prazna.
        """
        k = Korisnik(
            None, "X", "Y", "nije_email",
            hashlib.sha256("x".encode()).hexdigest(),
            TipKorisnika.OBICAN, "1990-01-01", "11111111111"
        )
        with pytest.raises(ValidationError):
            servisi["korisnik"].spremi(k)
        assert len(servisi["korisnik"].dohvati_sve()) == 0

    def test_popust_se_automatski_primjenjuje_pri_kupnji(self, servisi):
        """
        Integracija: popust definiran u bazi mora se automatski
        primijeniti bez eksplicitnog poziva iz UI sloja.
        """
        s1 = servisi["stanica"].spremi(nova_stanica("Stanica CC"))
        s2 = servisi["stanica"].spremi(nova_stanica("Stanica DD", "Grad D", "Županija D"))
        v  = servisi["vlak"].spremi(
            novi_vlak(s1.id, s2.id, tip=TipVlaka.INTERCITY,
                      kap=120, cijena=200.0))
        servisi["popust"].spremi(
            Popust(None, "Invalidski", TipKorisnika.INVALID, 75.0, True))
        k = servisi["korisnik"].spremi(
            novi_korisnik("ivan@t.com", "12345678903",
                          TipKorisnika.INVALID, "1980-01-01"))
        datum = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        karta = servisi["karta"].kupi_kartu(k.id, v.id, datum)
        assert karta.cijena_placena == 50.0   # 200 * 0.25
        assert karta.popust_postotak == 75.0

    def test_otkazivanje_karte_vidljivo_kroz_sve_slojeve(self, servisi):
        """
        Integracija: otkazivanje kroz BLL mora biti vidljivo
        i pri dohvatu kroz DAL.
        """
        s1 = servisi["stanica"].spremi(nova_stanica("Stanica EE"))
        s2 = servisi["stanica"].spremi(nova_stanica("Stanica FF", "Grad F", "Županija F"))
        v  = servisi["vlak"].spremi(
            novi_vlak(s1.id, s2.id, tip=TipVlaka.INTERCITY, kap=150))
        k  = servisi["korisnik"].spremi(novi_korisnik())
        datum = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        karta = servisi["karta"].kupi_kartu(k.id, v.id, datum)
        servisi["karta"].otkazi_kartu(karta.id)
        doh = servisi["karta"].dohvati_po_id(karta.id)
        assert doh.status == StatusKarte.OTKAZANA

    def test_brisanje_korisnika_kroz_bll_i_provjera_u_dal(self, servisi):
        """
        Integracija: brisanje kroz BLL servis mora ukloniti
        zapis i na DAL razini.
        """
        k = servisi["korisnik"].spremi(novi_korisnik())
        assert servisi["korisnik"].dohvati_po_id(k.id) is not None
        servisi["korisnik"].obrisi(k.id)
        assert servisi["korisnik"].dohvati_po_id(k.id) is None

    def test_inicijalizacija_testnih_podataka_puni_bazu(self, servisi):
        """
        Integracija: metoda za inicijalizaciju testnih podataka
        mora napuniti bazu s ispravnim početnim stanjem.
        """
        servisi["db"].unesi_testne_podatke()
        stanice = servisi["stanica"].dohvati_sve()
        vlakovi = servisi["vlak"].dohvati_sve()
        assert len(stanice) >= 4
        assert len(vlakovi) >= 3