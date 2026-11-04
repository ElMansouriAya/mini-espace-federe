"""TP2 - API de l'organisation A (sans authentification : les données brutes circulent).

Lancement (depuis la racine du dépôt) :
  python -m uvicorn organisation_A.api.api_air_tp2:app --port 8001
"""
from contextlib import closing
import sqlite3

from fastapi import FastAPI

from organisation_A import config

app = FastAPI(title="API Environnement - TP2")


@app.get("/")
def accueil():
    return {"organisation": "Direction de l'environnement"}


@app.get("/mesures")
def obtenir_mesures():
    with closing(sqlite3.connect(config.DB_AIR_TP1)) as db:
        db.row_factory = sqlite3.Row
        lignes = db.execute("SELECT date, ville, pm25 FROM qualite_air ORDER BY date").fetchall()
    return [dict(l) for l in lignes]


@app.get("/statistiques")
def statistiques():
    with closing(sqlite3.connect(config.DB_AIR_TP1)) as db:
        n, moyenne = db.execute("SELECT COUNT(*), AVG(pm25) FROM qualite_air").fetchone()
    return {"nombre_jours": n, "moyenne_pm25": round(moyenne, 2) if n else None}
