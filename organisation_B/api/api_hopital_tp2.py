"""TP2 - API de l'organisation B (sans authentification : les données brutes circulent).

Lancement (depuis la racine du dépôt) :
  python -m uvicorn organisation_B.api.api_hopital_tp2:app --port 8002
"""
from contextlib import closing
import sqlite3

from fastapi import FastAPI

from ..database.setup_hopital import DB_HOPITAL_TP1

app = FastAPI(title="API Hôpital - TP2")


@app.get("/")
def accueil():
    return {"organisation": "Hôpital régional"}


@app.get("/admissions")
def obtenir_admissions():
    with closing(sqlite3.connect(DB_HOPITAL_TP1)) as db:
        db.row_factory = sqlite3.Row
        lignes = db.execute(
            "SELECT date, ville, nombre FROM admissions ORDER BY date"
        ).fetchall()
    return [dict(ligne) for ligne in lignes]


@app.get("/statistiques")
def statistiques():
    with closing(sqlite3.connect(DB_HOPITAL_TP1)) as db:
        n, moyenne = db.execute("SELECT COUNT(*), AVG(nombre) FROM admissions").fetchone()
    return {"nombre_jours": n, "moyenne_admissions": round(moyenne, 2) if n else None}
