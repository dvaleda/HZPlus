from typing import List, Optional
from models.entities import (
    Stanica, Vlak, TipVlaka, Korisnik, TipKorisnika,
    Karta, StatusKarte, Popust, SjedaloVlaka
)
from dal.database_manager import Database


class StanicaRepository:
    def __init__(self, db: Database):
        self.db = db

    def dohvati_sve(self) -> List[Stanica]:
        rows = self.db.get_connection().execute(
            "SELECT * FROM stanica ORDER BY naziv"
        ).fetchall()
        return [self._map(r) for r in rows]

    def dohvati_po_id(self, id_: int) -> Optional[Stanica]:
        row = self.db.get_connection().execute(
            "SELECT * FROM stanica WHERE id=?", (id_,)
        ).fetchone()
        return self._map(row) if row else None

    def spremi(self, s: Stanica) -> Stanica:
        conn = self.db.get_connection()
        if s.id is None:
            cur = conn.execute(
                "INSERT INTO stanica(naziv, grad, zupanija) VALUES (?,?,?)",
                (s.naziv, s.grad, s.zupanija)
            )
            s.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE stanica SET naziv=?, grad=?, zupanija=? WHERE id=?",
                (s.naziv, s.grad, s.zupanija, s.id)
            )
        conn.commit()
        return s

    def obrisi(self, id_: int) -> bool:
        conn = self.db.get_connection()
        cur = conn.execute("DELETE FROM stanica WHERE id=?", (id_,))
        conn.commit()
        return cur.rowcount > 0

    def pretrazi(self, upit: str) -> List[Stanica]:
        lk = f"%{upit}%"
        rows = self.db.get_connection().execute(
            "SELECT * FROM stanica WHERE naziv LIKE ? OR grad LIKE ? ORDER BY naziv",
            (lk, lk)
        ).fetchall()
        return [self._map(r) for r in rows]

    def _map(self, r) -> Stanica:
        return Stanica(id=r["id"], naziv=r["naziv"], grad=r["grad"], zupanija=r["zupanija"])


class VlakRepository:
    def __init__(self, db: Database):
        self.db = db

    def dohvati_sve(self) -> List[Vlak]:
        rows = self.db.get_connection().execute("""
            SELECT v.*, sp.naziv AS polazisna, so.naziv AS odredisna
            FROM vlak v
            JOIN stanica sp ON v.id_polazisne_stanice = sp.id
            JOIN stanica so ON v.id_odredisne_stanice = so.id
            ORDER BY v.broj_vlaka
        """).fetchall()
        return [self._map(r) for r in rows]

    def dohvati_po_id(self, id_: int) -> Optional[Vlak]:
        row = self.db.get_connection().execute("""
            SELECT v.*, sp.naziv AS polazisna, so.naziv AS odredisna
            FROM vlak v
            JOIN stanica sp ON v.id_polazisne_stanice = sp.id
            JOIN stanica so ON v.id_odredisne_stanice = so.id
            WHERE v.id=?
        """, (id_,)).fetchone()
        return self._map(row) if row else None

    def spremi(self, v: Vlak) -> Vlak:
        conn = self.db.get_connection()
        tip = v.tip.value if isinstance(v.tip, TipVlaka) else v.tip
        if v.id is None:
            cur = conn.execute("""
                INSERT INTO vlak(broj_vlaka, tip, kapacitet, id_polazisne_stanice,
                    id_odredisne_stanice, vrijeme_polaska, vrijeme_dolaska, cijena_kn)
                VALUES (?,?,?,?,?,?,?,?)
            """, (v.broj_vlaka, tip, v.kapacitet, v.id_polazisne_stanice,
                  v.id_odredisne_stanice, v.vrijeme_polaska, v.vrijeme_dolaska, v.cijena_kn))
            v.id = cur.lastrowid
        else:
            conn.execute("""
                UPDATE vlak SET broj_vlaka=?, tip=?, kapacitet=?,
                    id_polazisne_stanice=?, id_odredisne_stanice=?,
                    vrijeme_polaska=?, vrijeme_dolaska=?, cijena_kn=?
                WHERE id=?
            """, (v.broj_vlaka, tip, v.kapacitet, v.id_polazisne_stanice,
                  v.id_odredisne_stanice, v.vrijeme_polaska, v.vrijeme_dolaska,
                  v.cijena_kn, v.id))
        conn.commit()
        return v

    def obrisi(self, id_: int) -> bool:
        conn = self.db.get_connection()
        cur = conn.execute("DELETE FROM vlak WHERE id=?", (id_,))
        conn.commit()
        return cur.rowcount > 0

    def pretrazi(self, upit: str) -> List[Vlak]:
        lk = f"%{upit}%"
        rows = self.db.get_connection().execute("""
            SELECT v.*, sp.naziv AS polazisna, so.naziv AS odredisna
            FROM vlak v
            JOIN stanica sp ON v.id_polazisne_stanice = sp.id
            JOIN stanica so ON v.id_odredisne_stanice = so.id
            WHERE v.broj_vlaka LIKE ? OR sp.naziv LIKE ? OR so.naziv LIKE ?
            ORDER BY v.broj_vlaka
        """, (lk, lk, lk)).fetchall()
        return [self._map(r) for r in rows]

    def _map(self, r) -> Vlak:
        tip_str = r["tip"]
        tip = next((t for t in TipVlaka if t.value == tip_str), TipVlaka.PUTNICKI)
        keys = r.keys()
        return Vlak(
            id=r["id"], broj_vlaka=r["broj_vlaka"], tip=tip,
            kapacitet=r["kapacitet"],
            id_polazisne_stanice=r["id_polazisne_stanice"],
            id_odredisne_stanice=r["id_odredisne_stanice"],
            vrijeme_polaska=r["vrijeme_polaska"],
            vrijeme_dolaska=r["vrijeme_dolaska"],
            cijena_kn=r["cijena_kn"],
            naziv_polazisne=r["polazisna"] if "polazisna" in keys else None,
            naziv_odredisne=r["odredisna"] if "odredisna" in keys else None,
        )


class KorisnikRepository:
    def __init__(self, db: Database):
        self.db = db

    def dohvati_sve(self) -> List[Korisnik]:
        rows = self.db.get_connection().execute(
            "SELECT * FROM korisnik ORDER BY prezime, ime"
        ).fetchall()
        return [self._map(r) for r in rows]

    def dohvati_po_id(self, id_: int) -> Optional[Korisnik]:
        row = self.db.get_connection().execute(
            "SELECT * FROM korisnik WHERE id=?", (id_,)
        ).fetchone()
        return self._map(row) if row else None

    def dohvati_po_emailu(self, email: str) -> Optional[Korisnik]:
        row = self.db.get_connection().execute(
            "SELECT * FROM korisnik WHERE email=?", (email,)
        ).fetchone()
        return self._map(row) if row else None

    def spremi(self, k: Korisnik) -> Korisnik:
        conn = self.db.get_connection()
        tip = k.tip.value if isinstance(k.tip, TipKorisnika) else k.tip
        if k.id is None:
            cur = conn.execute("""
                INSERT INTO korisnik(ime, prezime, email, lozinka_hash,
                    tip, datum_rodenja, oib, telefon)
                VALUES (?,?,?,?,?,?,?,?)
            """, (k.ime, k.prezime, k.email, k.lozinka_hash,
                  tip, k.datum_rodenja, k.oib, k.telefon))
            k.id = cur.lastrowid
        else:
            conn.execute("""
                UPDATE korisnik SET ime=?, prezime=?, email=?, lozinka_hash=?,
                    tip=?, datum_rodenja=?, oib=?, telefon=?
                WHERE id=?
            """, (k.ime, k.prezime, k.email, k.lozinka_hash,
                  tip, k.datum_rodenja, k.oib, k.telefon, k.id))
        conn.commit()
        return k

    def obrisi(self, id_: int) -> bool:
        conn = self.db.get_connection()
        cur = conn.execute("DELETE FROM korisnik WHERE id=?", (id_,))
        conn.commit()
        return cur.rowcount > 0

    def pretrazi(self, upit: str) -> List[Korisnik]:
        lk = f"%{upit}%"
        rows = self.db.get_connection().execute("""
            SELECT * FROM korisnik
            WHERE ime LIKE ? OR prezime LIKE ? OR email LIKE ?
            ORDER BY prezime, ime
        """, (lk, lk, lk)).fetchall()
        return [self._map(r) for r in rows]

    def _map(self, r) -> Korisnik:
        tip_str = r["tip"]
        tip = next((t for t in TipKorisnika if t.value == tip_str), TipKorisnika.OBICAN)
        return Korisnik(
            id=r["id"], ime=r["ime"], prezime=r["prezime"],
            email=r["email"], lozinka_hash=r["lozinka_hash"],
            tip=tip, datum_rodenja=r["datum_rodenja"],
            oib=r["oib"], telefon=r["telefon"]
        )


class PopustRepository:
    def __init__(self, db: Database):
        self.db = db

    def dohvati_sve(self) -> List[Popust]:
        rows = self.db.get_connection().execute(
            "SELECT * FROM popust ORDER BY naziv"
        ).fetchall()
        return [self._map(r) for r in rows]

    def dohvati_po_id(self, id_: int) -> Optional[Popust]:
        row = self.db.get_connection().execute(
            "SELECT * FROM popust WHERE id=?", (id_,)
        ).fetchone()
        return self._map(row) if row else None

    def dohvati_po_tipu_korisnika(self, tip: TipKorisnika) -> Optional[Popust]:
        tip_str = tip.value if isinstance(tip, TipKorisnika) else tip
        row = self.db.get_connection().execute(
            "SELECT * FROM popust WHERE tip_korisnika=? AND aktivan=1 LIMIT 1",
            (tip_str,)
        ).fetchone()
        return self._map(row) if row else None

    def spremi(self, p: Popust) -> Popust:
        conn = self.db.get_connection()
        tip = p.tip_korisnika.value if isinstance(p.tip_korisnika, TipKorisnika) else p.tip_korisnika
        ak = 1 if p.aktivan else 0
        if p.id is None:
            cur = conn.execute(
                "INSERT INTO popust(naziv, tip_korisnika, postotak, aktivan, opis) VALUES (?,?,?,?,?)",
                (p.naziv, tip, p.postotak, ak, p.opis)
            )
            p.id = cur.lastrowid
        else:
            conn.execute("""
                UPDATE popust SET naziv=?, tip_korisnika=?, postotak=?, aktivan=?, opis=?
                WHERE id=?
            """, (p.naziv, tip, p.postotak, ak, p.opis, p.id))
        conn.commit()
        return p

    def obrisi(self, id_: int) -> bool:
        conn = self.db.get_connection()
        cur = conn.execute("DELETE FROM popust WHERE id=?", (id_,))
        conn.commit()
        return cur.rowcount > 0

    def _map(self, r) -> Popust:
        tip_str = r["tip_korisnika"]
        tip = next((t for t in TipKorisnika if t.value == tip_str), TipKorisnika.OBICAN)
        return Popust(
            id=r["id"], naziv=r["naziv"], tip_korisnika=tip,
            postotak=r["postotak"], aktivan=bool(r["aktivan"]), opis=r["opis"]
        )


class KartaRepository:
    def __init__(self, db: Database):
        self.db = db

    def dohvati_sve(self) -> List[Karta]:
        rows = self.db.get_connection().execute("""
            SELECT k.*,
                   ko.ime || ' ' || ko.prezime AS korisnik_ime,
                   v.broj_vlaka AS vlak_broj,
                   sp.naziv AS polazisna, so.naziv AS odredisna,
                   sv.oznaka_vagon || '-' || sv.broj_sjedala AS br_sjedala
            FROM karta k
            JOIN korisnik ko ON k.id_korisnika = ko.id
            JOIN vlak v ON k.id_vlaka = v.id
            JOIN stanica sp ON v.id_polazisne_stanice = sp.id
            JOIN stanica so ON v.id_odredisne_stanice = so.id
            LEFT JOIN sjedalo_vlaka sv ON k.id_sjedala = sv.id
            ORDER BY k.datum_putovanja DESC
        """).fetchall()
        return [self._map(r) for r in rows]

    def dohvati_po_id(self, id_: int) -> Optional[Karta]:
        row = self.db.get_connection().execute("""
            SELECT k.*,
                   ko.ime || ' ' || ko.prezime AS korisnik_ime,
                   v.broj_vlaka AS vlak_broj,
                   sp.naziv AS polazisna, so.naziv AS odredisna,
                   sv.oznaka_vagon || '-' || sv.broj_sjedala AS br_sjedala
            FROM karta k
            JOIN korisnik ko ON k.id_korisnika = ko.id
            JOIN vlak v ON k.id_vlaka = v.id
            JOIN stanica sp ON v.id_polazisne_stanice = sp.id
            JOIN stanica so ON v.id_odredisne_stanice = so.id
            LEFT JOIN sjedalo_vlaka sv ON k.id_sjedala = sv.id
            WHERE k.id=?
        """, (id_,)).fetchone()
        return self._map(row) if row else None

    def dohvati_za_korisnika(self, id_k: int) -> List[Karta]:
        rows = self.db.get_connection().execute("""
            SELECT k.*,
                   ko.ime || ' ' || ko.prezime AS korisnik_ime,
                   v.broj_vlaka AS vlak_broj,
                   sp.naziv AS polazisna, so.naziv AS odredisna,
                   sv.oznaka_vagon || '-' || sv.broj_sjedala AS br_sjedala
            FROM karta k
            JOIN korisnik ko ON k.id_korisnika = ko.id
            JOIN vlak v ON k.id_vlaka = v.id
            JOIN stanica sp ON v.id_polazisne_stanice = sp.id
            JOIN stanica so ON v.id_odredisne_stanice = so.id
            LEFT JOIN sjedalo_vlaka sv ON k.id_sjedala = sv.id
            WHERE k.id_korisnika=?
            ORDER BY k.datum_putovanja DESC
        """, (id_k,)).fetchall()
        return [self._map(r) for r in rows]

    def dohvati_zauzetost_sjedala(self, id_vlaka: int, datum: str) -> list:
        rows = self.db.get_connection().execute("""
            SELECT id_sjedala FROM karta
            WHERE id_vlaka=? AND datum_putovanja=? AND status != 'Otkazana'
        """, (id_vlaka, datum)).fetchall()
        return [r["id_sjedala"] for r in rows if r["id_sjedala"] is not None]

    def spremi(self, k: Karta) -> Karta:
        conn = self.db.get_connection()
        status = k.status.value if isinstance(k.status, StatusKarte) else k.status
        if k.id is None:
            cur = conn.execute("""
                INSERT INTO karta(id_korisnika, id_vlaka, id_sjedala, datum_putovanja,
                    datum_kupnje, cijena_placena, status, popust_postotak)
                VALUES (?,?,?,?,?,?,?,?)
            """, (k.id_korisnika, k.id_vlaka, k.id_sjedala, k.datum_putovanja,
                  k.datum_kupnje, k.cijena_placena, status, k.popust_postotak))
            k.id = cur.lastrowid
        else:
            conn.execute("""
                UPDATE karta SET id_korisnika=?, id_vlaka=?, id_sjedala=?,
                    datum_putovanja=?, cijena_placena=?, status=?, popust_postotak=?
                WHERE id=?
            """, (k.id_korisnika, k.id_vlaka, k.id_sjedala, k.datum_putovanja,
                  k.cijena_placena, status, k.popust_postotak, k.id))
        conn.commit()
        return k

    def obrisi(self, id_: int) -> bool:
        conn = self.db.get_connection()
        cur = conn.execute("DELETE FROM karta WHERE id=?", (id_,))
        conn.commit()
        return cur.rowcount > 0

    def _map(self, r) -> Karta:
        keys = r.keys()
        status_str = r["status"]
        status = next((s for s in StatusKarte if s.value == status_str), StatusKarte.AKTIVNA)
        return Karta(
            id=r["id"], id_korisnika=r["id_korisnika"], id_vlaka=r["id_vlaka"],
            id_sjedala=r["id_sjedala"], datum_putovanja=r["datum_putovanja"],
            datum_kupnje=r["datum_kupnje"], cijena_placena=r["cijena_placena"],
            status=status, popust_postotak=r["popust_postotak"],
            korisnik_ime=r["korisnik_ime"] if "korisnik_ime" in keys else None,
            vlak_broj=r["vlak_broj"] if "vlak_broj" in keys else None,
            polazisna=r["polazisna"] if "polazisna" in keys else None,
            odredisna=r["odredisna"] if "odredisna" in keys else None,
            broj_sjedala=r["br_sjedala"] if "br_sjedala" in keys else None,
        )


class SjedaloRepository:
    def __init__(self, db: Database):
        self.db = db

    def dohvati_za_vlak(self, id_vlaka: int) -> List[SjedaloVlaka]:
        rows = self.db.get_connection().execute(
            "SELECT * FROM sjedalo_vlaka WHERE id_vlaka=? ORDER BY oznaka_vagon, broj_sjedala",
            (id_vlaka,)
        ).fetchall()
        return [self._map(r) for r in rows]

    def dohvati_slobodna(self, id_vlaka: int, datum: str) -> List[SjedaloVlaka]:
        rows = self.db.get_connection().execute("""
            SELECT sv.* FROM sjedalo_vlaka sv
            WHERE sv.id_vlaka=?
              AND sv.id NOT IN (
                SELECT id_sjedala FROM karta
                WHERE id_vlaka=? AND datum_putovanja=? AND status != 'Otkazana'
                  AND id_sjedala IS NOT NULL
              )
            ORDER BY sv.oznaka_vagon, sv.broj_sjedala
        """, (id_vlaka, id_vlaka, datum)).fetchall()
        return [self._map(r) for r in rows]

    def _map(self, r) -> SjedaloVlaka:
        return SjedaloVlaka(
            id=r["id"], id_vlaka=r["id_vlaka"],
            broj_sjedala=r["broj_sjedala"],
            oznaka_vagon=r["oznaka_vagon"], razred=r["razred"]
        )