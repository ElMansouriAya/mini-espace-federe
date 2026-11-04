"""TP3 - API de calcul local de l'organisation B, protégée par clé API.

  PowerShell : $env:CLE_HOPITAL="demo-hopital-456"
  python -m uvicorn organisation_B.api.api_hopital_v3:app --port 8002

Limite volontaire (cf. section 8 du sujet) : le laboratoire choisit lui-même les
groupes de dates, donc l'attaque par différence fonctionne. Le TP4 la corrige.
"""
from collections import defaultdict
from contextlib import closing
import hmac
import os
import sqlite3
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from ..database.setup_hopital import DB_HOPITAL_TP1

app = FastAPI(title="API Hôpital - TP3")

# Valeur de démonstration, distincte de la clé du TP4 : jamais en production.
CLE_API_TP3 = os.getenv("CLE_HOPITAL", "demo-hopital-456")
CATEGORIES_TP3 = {"elevee", "non_elevee"}


def verifier_cle(x_api_key):
    if not x_api_key or not hmac.compare_digest(
        x_api_key.encode("utf-8"), CLE_API_TP3.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Clé API invalide")


class Classification(BaseModel):
    date: str
    categorie: str


class DemandeAnalyse(BaseModel):
    classifications: List[Classification]


@app.get("/")
def accueil():
    return {"organisation": "Hôpital régional"}


@app.post("/analyse-locale")
def analyse_locale(demande: DemandeAnalyse, x_api_key: Optional[str] = Header(default=None)):
    verifier_cle(x_api_key)

    if any(c.categorie not in CATEGORIES_TP3 for c in demande.classifications):
        raise HTTPException(status_code=400, detail="Catégorie invalide")

    dates = [c.date for c in demande.classifications]
    if len(dates) != len(set(dates)):
        raise HTTPException(status_code=400, detail="Dates en double")

    groupes = {c.date: c.categorie for c in demande.classifications}
    with closing(sqlite3.connect(DB_HOPITAL_TP1)) as db:
        lignes = db.execute("SELECT date, nombre FROM admissions").fetchall()

    statistiques = defaultdict(list)
    for date, nombre in lignes:
        categorie = groupes.get(date)
        if categorie is not None:
            statistiques[categorie].append(nombre)

    resultat = {}
    for categorie in ("elevee", "non_elevee"):
        valeurs = statistiques[categorie]
        resultat[categorie] = {
            "nombre_jours": len(valeurs),
            "moyenne_admissions": round(sum(valeurs) / len(valeurs), 2) if valeurs else None,
        }
    return resultat
