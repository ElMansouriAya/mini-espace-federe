"""Organisation B - Création de la base hospitalière (données fictives, 10 jours)."""
from contextlib import closing
from pathlib import Path
import sqlite3

DB_HOPITAL = Path(__file__).resolve().parent / "hopital.db"

DONNEES_HOPITAL = [
    ("2026-10-01", "Tanger", 8),
    ("2026-10-02", "Tanger", 14),
    ("2026-10-03", "Tanger", 18),
    ("2026-10-04", "Tanger", 9),
    ("2026-10-05", "Tanger", 16),
    ("2026-10-06", "Tanger", 20),
    ("2026-10-07", "Tanger", 10),
    ("2026-10-08", "Tanger", 7),
    ("2026-10-09", "Tanger", 13),
    ("2026-10-10", "Tanger", 5),
]


def creer_base():
    # closing() ferme réellement la connexion (verrouillage de fichier sous Windows)
    with closing(sqlite3.connect(DB_HOPITAL)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admissions (
                    date TEXT PRIMARY KEY,
                    ville TEXT NOT NULL,
                    nombre INTEGER NOT NULL CHECK(nombre >= 0)
                )
            """)
            conn.execute("DELETE FROM admissions")
            conn.executemany(
                "INSERT INTO admissions (date, ville, nombre) VALUES (?, ?, ?)",
                DONNEES_HOPITAL,
            )


if __name__ == "__main__":
    creer_base()
    print(f"Base hospitalière créée : {DB_HOPITAL}")
