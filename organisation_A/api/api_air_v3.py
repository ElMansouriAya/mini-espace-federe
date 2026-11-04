"""TP3 - API protégée de l'organisation A : seulement des catégories, pas de PM2.5 brut.

  PowerShell : $env:CLE_ENVIRONNEMENT="demo-air-123"
  python -m uvicorn organisation_A.api.api_air_v3:app --port 8001
"""
from contextlib import closing
import sqlite3

from fastapi import FastAPI, Header, HTTPException

from organisation_A import config
from organisation_A.security.auth import cle_valide

app = FastAPI(title="API Environnement - TP3")


@app.get("/")
def accueil():
    return {"organisation": "Direction de l'environnement"}


@app.get("/categories")
def categories(x_api_key: str | None = Header(default=None)):
    if not cle_valide(x_api_key, config.CLE_API_TP3):
        raise HTTPException(status_code=401, detail="Clé API invalide")
    with closing(sqlite3.connect(config.DB_AIR_TP1)) as db:
        lignes = db.execute("""
            SELECT date, CASE WHEN pm25 > ? THEN 'elevee' ELSE 'non_elevee' END
            FROM qualite_air ORDER BY date
        """, (config.SEUIL_PM25,)).fetchall()
    return [{"date": d, "categorie": c} for d, c in lignes]
