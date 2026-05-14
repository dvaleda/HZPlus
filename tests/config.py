"""
Zajednička konfiguracija za sve testove.
Svaki test dobiva svježu in-memory bazu, nema dijeljenog stanja.
"""
import sys
import os
import pytest
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dal.database import Database
from dal.repositories import (
    StanicaRepository, VlakRepository, KorisnikRepository,
    PopustRepository, KartaRepository, SjedaloRepository
)
from bll.services import (
    StanicaService, VlakService, KorisnikService,
    PopustService, KartaService
)
from models.entities import (
    Stanica, Vlak, TipVlaka, Korisnik, TipKorisnika,
    Karta, StatusKarte, Popust
)


@pytest.fixture
def db():
    Database.reset_instance()
    baza = Database(":memory:")
    Database._instance = baza
    baza.inicijaliziraj_shemu()
    yield baza
    baza.close()
    Database.reset_instance()


@pytest.fixture
def repozitoriji(db):
    return {
        "stanica":  StanicaRepository(db),
        "vlak":     VlakRepository(db),
        "korisnik": KorisnikRepository(db),
        "popust":   PopustRepository(db),
        "karta":    KartaRepository(db),
        "sjedalo":  SjedaloRepository(db),
        "db":       db,
    }


@pytest.fixture
def servisi(repozitoriji):
    r = repozitoriji
    s_svc  = StanicaService(r["stanica"])
    v_svc  = VlakService(r["vlak"], r["stanica"])
    k_svc  = KorisnikService(r["korisnik"])
    p_svc  = PopustService(r["popust"])
    ka_svc = KartaService(r["karta"], r["vlak"], r["korisnik"],
                          r["popust"], r["sjedalo"])
    return {
        "stanica":  s_svc, "vlak":     v_svc,
        "korisnik": k_svc, "popust":   p_svc,
        "karta":    ka_svc,
        "db":       repozitoriji["db"],
    }


def nova_stanica(naziv="Zagreb GK", grad="Zagreb", zupanija="Grad Zagreb"):
    return Stanica(None, naziv, grad, zupanija)


def novi_vlak(pol_id, odred_id,
              broj="IC-001", tip=TipVlaka.INTERCITY, kap=200, cijena=85.0):
    return Vlak(None, broj, tip, kap, pol_id, odred_id, "07:00", "12:00", cijena)


def novi_korisnik(email="test@test.com", oib="12345678903",
                  tip=TipKorisnika.OBICAN, datum_rod="1990-06-15"):
    return Korisnik(
        None, "Test", "Korisnik", email,
        hashlib.sha256("lozinka".encode()).hexdigest(),
        tip, datum_rod, oib
    )