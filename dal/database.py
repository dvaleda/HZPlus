import sqlite3
from typing import Optional


class Database:
    _instance: Optional['Database'] = None

    def __init__(self, db_path: str = "hzplus.db"):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    @classmethod
    def get_instance(cls, db_path: str = "hzplus.db") -> 'Database':
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        if cls._instance and cls._instance._connection:
            cls._instance._connection.close()
        cls._instance = None

    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def inicijaliziraj_shemu(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS stanica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naziv TEXT NOT NULL,
            grad TEXT NOT NULL,
            zupanija TEXT NOT NULL,
            UNIQUE(naziv, grad)
        );
        CREATE TABLE IF NOT EXISTS vlak (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broj_vlaka TEXT NOT NULL UNIQUE,
            tip TEXT NOT NULL,
            kapacitet INTEGER NOT NULL CHECK(kapacitet > 0),
            id_polazisne_stanice INTEGER NOT NULL,
            id_odredisne_stanice INTEGER NOT NULL,
            vrijeme_polaska TEXT NOT NULL,
            vrijeme_dolaska TEXT NOT NULL,
            cijena_kn REAL NOT NULL CHECK(cijena_kn >= 0),
            FOREIGN KEY (id_polazisne_stanice) REFERENCES stanica(id),
            FOREIGN KEY (id_odredisne_stanice) REFERENCES stanica(id),
            CHECK(id_polazisne_stanice != id_odredisne_stanice)
        );
        CREATE TABLE IF NOT EXISTS sjedalo_vlaka (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_vlaka INTEGER NOT NULL,
            broj_sjedala INTEGER NOT NULL,
            oznaka_vagon TEXT NOT NULL,
            razred INTEGER NOT NULL CHECK(razred IN (1, 2)),
            FOREIGN KEY (id_vlaka) REFERENCES vlak(id) ON DELETE CASCADE,
            UNIQUE(id_vlaka, broj_sjedala, oznaka_vagon)
        );
        CREATE TABLE IF NOT EXISTS korisnik (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ime TEXT NOT NULL,
            prezime TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            lozinka_hash TEXT NOT NULL,
            tip TEXT NOT NULL DEFAULT 'Obični',
            datum_rodenja TEXT NOT NULL,
            oib TEXT NOT NULL UNIQUE,
            telefon TEXT
        );
        CREATE TABLE IF NOT EXISTS popust (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naziv TEXT NOT NULL,
            tip_korisnika TEXT NOT NULL,
            postotak REAL NOT NULL CHECK(postotak >= 0 AND postotak <= 100),
            aktivan INTEGER NOT NULL DEFAULT 1,
            opis TEXT
        );
        CREATE TABLE IF NOT EXISTS karta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_korisnika INTEGER NOT NULL,
            id_vlaka INTEGER NOT NULL,
            id_sjedala INTEGER,
            datum_putovanja TEXT NOT NULL,
            datum_kupnje TEXT NOT NULL,
            cijena_placena REAL NOT NULL CHECK(cijena_placena >= 0),
            status TEXT NOT NULL DEFAULT 'Aktivna',
            popust_postotak REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (id_korisnika) REFERENCES korisnik(id),
            FOREIGN KEY (id_vlaka) REFERENCES vlak(id),
            FOREIGN KEY (id_sjedala) REFERENCES sjedalo_vlaka(id)
        );
        """)
        conn.commit()

    def unesi_testne_podatke(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stanica")
        if cursor.fetchone()[0] > 0:
            return
        stanice = [
            ("Zagreb Glavni kolodvor", "Zagreb", "Grad Zagreb"),
            ("Split", "Split", "Splitsko-dalmatinska"),
            ("Rijeka", "Rijeka", "Primorsko-goranska"),
            ("Osijek", "Osijek", "Osječko-baranjska"),
            ("Varaždin", "Varaždin", "Varaždinska"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO stanica(naziv, grad, zupanija) VALUES (?,?,?)",
            stanice
        )
        vlakovi = [
            ("IC-201", "InterCity", 200, 1, 2, "07:00", "12:30", 15.00),
            ("R-305", "Regionalni", 150, 1, 3, "08:15", "11:45", 9.50),
            ("IC-410", "InterCity", 180, 1, 4, "09:00", "13:20", 18.00),
            ("R-520", "Regionalni", 120, 1, 5, "10:30", "12:00", 5.50),
        ]
        cursor.executemany(
            """INSERT OR IGNORE INTO vlak
               (broj_vlaka, tip, kapacitet, id_polazisne_stanice, id_odredisne_stanice,
                vrijeme_polaska, vrijeme_dolaska, cijena_kn)
               VALUES (?,?,?,?,?,?,?,?)""",
            vlakovi
        )
        cursor.execute("SELECT id, kapacitet FROM vlak")
        for row in cursor.fetchall():
            sjedala = []
            for br in range(1, min(row[1] + 1, 51)):
                sjedala.append((row[0], br, "V1", 2))
            for br in range(1, 11):
                sjedala.append((row[0], br, "V1", 1))
            cursor.executemany(
                "INSERT OR IGNORE INTO sjedalo_vlaka(id_vlaka, broj_sjedala, oznaka_vagon, razred) VALUES (?,?,?,?)",
                sjedala
            )
        popusti = [
            ("Studentski popust", "Student", 50.0, 1, "Popust 50% za studente"),
            ("Učenički popust", "Učenik", 50.0, 1, "Popust 50% za učenike"),
            ("Umirovljenički popust", "Umirovljenik", 30.0, 1, "Popust 30% za umirovljenike"),
            ("Popust za invalide", "Osoba s invaliditetom", 75.0, 1, "Popust 75%"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO popust(naziv, tip_korisnika, postotak, aktivan, opis) VALUES (?,?,?,?,?)",
            popusti
        )
        import hashlib
        korisnici = [
            ("Marko", "Marković", "marko@example.com",
             hashlib.sha256("lozinka123".encode()).hexdigest(),
             "Obični", "1990-05-15", "12345678903", "091-111-2222"),
            ("Ana", "Anić", "ana@student.hr",
             hashlib.sha256("lozinka123".encode()).hexdigest(),
             "Student", "2000-03-22", "23456789013", None),
            ("Pero", "Perić", "pero@example.com",
             hashlib.sha256("lozinka123".encode()).hexdigest(),
             "Umirovljenik", "1955-08-10", "34567890125", "092-333-4444"),
        ]
        cursor.executemany(
            """INSERT OR IGNORE INTO korisnik
               (ime, prezime, email, lozinka_hash, tip, datum_rodenja, oib, telefon)
               VALUES (?,?,?,?,?,?,?,?)""",
            korisnici
        )
        conn.commit()