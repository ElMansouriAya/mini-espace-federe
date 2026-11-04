"""Organisation B - Contrôle d'accès par clé API (démonstration uniquement)."""
import hmac
import os

from fastapi import HTTPException

CLE_API_B = os.getenv("CLE_HOPITAL", "secret-hospital-key-demo")


def verifier_cle(x_api_key):
    if x_api_key is None or not hmac.compare_digest(x_api_key, CLE_API_B):
        raise HTTPException(status_code=401, detail="Clé API invalide")
