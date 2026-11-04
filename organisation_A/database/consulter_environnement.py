"""Affiche le contenu des bases de l'organisation A (TP1, question 1)."""
from contextlib import closing
from pathlib import Path
import sqlite3

DOSSIER = Path(__file__).resolve().parent

for nom in ("environnement_tp1.db", "environnement.db"):
    chemin = DOSSIER / nom
    if not chemin.exists():
        print(f"\n{nom} : absente (lancez setup_data.py)")
        continue
    print(f"\nBase : {nom}")
    with closing(sqlite3.connect(chemin)) as db:
        for ligne in db.execute("SELECT * FROM qualite_air ORDER BY date"):
            print(ligne)
