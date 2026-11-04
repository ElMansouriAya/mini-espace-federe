"""Affiche le contenu des bases de l'organisation B (TP1, question 2)."""
from contextlib import closing
from pathlib import Path
import sqlite3

DOSSIER = Path(__file__).resolve().parent

for nom in ("hopital_tp1.db", "hopital.db"):
    chemin = DOSSIER / nom
    if not chemin.exists():
        print(f"\n{nom} : absente (lancez setup_hopital.py)")
        continue
    print(f"\nBase : {nom}")
    with closing(sqlite3.connect(chemin)) as db:
        for ligne in db.execute("SELECT * FROM admissions ORDER BY date"):
            print(ligne)
