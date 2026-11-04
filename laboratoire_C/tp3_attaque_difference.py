"""TP3 - Attaque par différence : le laboratoire choisit LUI-MÊME un groupe d'un seul jour.

Avec l'API du TP3 (api_hopital_v3), la moyenne d'un groupe d'un jour révèle
l'admission exacte de ce jour. Le TP4 refuse ce scénario (signature, seuil minimal).

Lancer : python laboratoire_C/tp3_attaque_difference.py
"""
import os

import requests

URL_HOPITAL = os.getenv("URL_HOPITAL", "http://127.0.0.1:8002")
CLE_HOPITAL = os.getenv("CLE_HOPITAL", "demo-hopital-456")

# Le laboratoire choisit LUI-MÊME le groupe : un seul jour.
demande = {"classifications": [{"date": "2026-10-01", "categorie": "non_elevee"}]}

r = requests.post(
    f"{URL_HOPITAL}/analyse-locale",
    headers={"X-API-Key": CLE_HOPITAL},
    json=demande,
    timeout=5,
)
print(r.json())
