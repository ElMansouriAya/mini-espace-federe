"""Création de la base SQLite de l'organisation A (données fictives).

  python organisation_A/database/setup_data.py            -> environnement.db      (10 jours, TP4)
  python organisation_A/database/setup_data.py --jeu tp1  -> environnement_tp1.db  (5 jours, TP1-3)
"""
from contextlib import closing
from pathlib import Path
import argparse
import sqlite3

DOSSIER = Path(__file__).resolve().parent

DONNEES_TP1 = [
    ("2026-10-01", "Tanger", 12.0),
    ("2026-10-02", "Tanger", 35.0),
    ("2026-10-03", "Tanger", 42.0),
    ("2026-10-04", "Tanger", 15.0),
    ("2026-10-05", "Tanger", 38.0),
]

DONNEES_TP4 = [
    ("2026-10-01", "Tanger", 12.0),
    ("2026-10-02", "Tanger", 35.5),
    ("2026-10-03", "Tanger", 42.1),
    ("2026-10-04", "Tanger", 15.2),
    ("2026-10-05", "Tanger", 38.0),
    ("2026-10-06", "Tanger", 45.0),
    ("2026-10-07", "Tanger", 22.1),
    ("2026-10-08", "Tanger", 18.0),
    ("2026-10-09", "Tanger", 31.0),
    ("2026-10-10", "Tanger", 11.5),
]


def creer_base_air(chemin, donnees):
    """Crée (ou réinitialise) la table qualite_air. closing() ferme vraiment
    la connexion (évite le verrouillage de fichier sous Windows)."""
    with closing(sqlite3.connect(chemin)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS qualite_air (
                    date  TEXT PRIMARY KEY,
                    ville TEXT NOT NULL,
                    pm25  REAL NOT NULL CHECK(pm25 >= 0)
                )
            """)
            conn.execute("DELETE FROM qualite_air")
            conn.executemany(
                "INSERT INTO qualite_air (date, ville, pm25) VALUES (?, ?, ?)", donnees
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jeu", choices=["tp1", "tp4"], default="tp4")
    jeu = parser.parse_args().jeu
    if jeu == "tp1":
        chemin, donnees = DOSSIER / "environnement_tp1.db", DONNEES_TP1
    else:
        chemin, donnees = DOSSIER / "environnement.db", DONNEES_TP4
    creer_base_air(chemin, donnees)
    print(f"Base '{chemin.name}' créée ({len(donnees)} jours, données fictives).")


if __name__ == "__main__":
    main()
