"""Organisation B - Création des bases hospitalières (données fictives).

  python organisation_B/database/setup_hopital.py            -> hopital.db      (10 jours, TP4)
  python organisation_B/database/setup_hopital.py --jeu tp1  -> hopital_tp1.db  (5 jours, TP1-3)
"""
from contextlib import closing
from pathlib import Path
import argparse
import sqlite3

DOSSIER = Path(__file__).resolve().parent
DB_HOPITAL = DOSSIER / "hopital.db"            # TP4 (10 jours)
DB_HOPITAL_TP1 = DOSSIER / "hopital_tp1.db"    # TP1 à TP3 (5 jours)

DONNEES_TP1 = [
    ("2026-10-01", "Tanger", 8),
    ("2026-10-02", "Tanger", 14),
    ("2026-10-03", "Tanger", 18),
    ("2026-10-04", "Tanger", 9),
    ("2026-10-05", "Tanger", 16),
]

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


def creer_base(chemin=DB_HOPITAL, donnees=DONNEES_HOPITAL):
    # closing() ferme réellement la connexion (verrouillage de fichier sous Windows)
    with closing(sqlite3.connect(chemin)) as conn:
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
                donnees,
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jeu", choices=["tp1", "tp4"], default="tp4")
    jeu = parser.parse_args().jeu
    if jeu == "tp1":
        chemin, donnees = DB_HOPITAL_TP1, DONNEES_TP1
    else:
        chemin, donnees = DB_HOPITAL, DONNEES_HOPITAL
    creer_base(chemin, donnees)
    print(f"Base '{chemin.name}' créée ({len(donnees)} jours, données fictives).")


if __name__ == "__main__":
    main()
