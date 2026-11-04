"""TP4 - Nœud A (Environnement) : catalogue, contrat, classifications signées.

Lancement (depuis la racine du dépôt, SANS --reload : les contrats sont en mémoire) :
  python -m uvicorn organisation_A.api.api_air:app --port 8001
"""
from contextlib import closing
from datetime import datetime, timezone
import sqlite3
from typing import Optional
import uuid

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from organisation_A import config
from organisation_A.security.auth import cle_valide
from organisation_A.security.signature import signer

app = FastAPI(
    title="Nœud A - Environnement",
    description="Espace de données fédéré Santé & Qualité de l'air - fournisseur de classifications signées.",
)

# Catalogue simplifié inspiré de DCAT (non conforme au standard).
CATALOGUE = [
    {
        "dataset_id": config.DATASET_ID,
        "title": "Qualité de l'air - PM2.5 à Tanger",
        "description": "Concentrations journalières de PM2.5 (données fictives).",
        "publisher": "Organisation Environnement",
        "temporal_coverage": "2026-10-01/2026-10-10",
        "unit": "µg/m³",
        "access_endpoint": "/contracts/negotiate",
        "allowed_purpose": config.FINALITE_AUTORISEE,  # règle inspirée d'ODRL
    }
]

contrats = {}      # contract_id -> contrat (en mémoire, perdu au redémarrage)
journal = []       # journal d'accès (audit), en mémoire


class DemandeContrat(BaseModel):
    dataset_id: str
    consumer_id: str
    purpose: str


def tracer(evenement, statut, **details):
    journal.append({
        "horodatage": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evenement": evenement,
        "statut": statut,
        **details,
    })


def refuser(code, detail, evenement, **details):
    """Journalise puis lève l'erreur HTTP."""
    tracer(evenement, code, motif=detail, **details)
    raise HTTPException(status_code=code, detail=detail)


def controler_cle(x_api_key, evenement):
    if not cle_valide(x_api_key, config.CLE_API_A):
        refuser(401, "Clé API invalide", evenement)


@app.get("/")
def accueil():
    return {"organisation": "Direction de l'environnement", "role": "Nœud A"}


@app.get("/health")
def health():
    return {"status": "ok", "contrats_actifs": len(contrats)}


@app.get("/catalog")
def lire_catalogue():
    return CATALOGUE


@app.post("/contracts/negotiate")
def negocier_contrat(demande: DemandeContrat, x_api_key: Optional[str] = Header(default=None)):
    ev = "negociation"
    # Ordre des contrôles imposé par le sujet : clé (401) > dataset (404) > finalité (403) > consommateur (403)
    controler_cle(x_api_key, ev)
    if demande.dataset_id != config.DATASET_ID:
        refuser(404, "Jeu de données inexistant", ev, consumer_id=demande.consumer_id)
    if demande.purpose != config.FINALITE_AUTORISEE:
        refuser(403, "Finalité non autorisée", ev, consumer_id=demande.consumer_id, purpose=demande.purpose)
    if demande.consumer_id not in config.CONSOMMATEURS_AUTORISES:
        refuser(403, "Consommateur non autorisé", ev, consumer_id=demande.consumer_id)

    contract_id = f"contract-air-{uuid.uuid4().hex[:8]}"
    contrats[contract_id] = {
        "status": "AGREED",
        "dataset_id": demande.dataset_id,
        "consumer_id": demande.consumer_id,
        "purpose": demande.purpose,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    tracer(ev, 200, contract_id=contract_id, consumer_id=demande.consumer_id, purpose=demande.purpose)
    return {"contract_id": contract_id, "status": "AGREED"}


@app.get("/classifications")
def lire_classifications(
    contract_id: str,
    consumer_id: str,
    x_api_key: Optional[str] = Header(default=None),
):
    ev = "classifications"
    controler_cle(x_api_key, ev)
    contrat = contrats.get(contract_id)
    if contrat is None:
        refuser(403, "Contrat inconnu", ev, contract_id=contract_id)
    if contrat["status"] != "AGREED" or contrat["dataset_id"] != config.DATASET_ID:
        refuser(403, "Contrat non applicable", ev, contract_id=contract_id)
    if contrat["purpose"] != config.FINALITE_AUTORISEE or contrat["consumer_id"] != consumer_id:
        refuser(403, "Consommateur ou finalité non autorisé", ev,
                contract_id=contract_id, consumer_id=consumer_id)

    with closing(sqlite3.connect(config.DB_AIR)) as conn:
        lignes = conn.execute("SELECT date, pm25 FROM qualite_air ORDER BY date").fetchall()

    # Seule la catégorie sort de chez A : jamais la valeur PM2.5 exacte.
    classifications = [
        {"date": d, "categorie": "au_dessus_seuil" if pm25 > config.SEUIL_PM25 else "sous_seuil"}
        for d, pm25 in lignes
    ]
    tracer(ev, 200, contract_id=contract_id, consumer_id=consumer_id, jours=len(classifications))
    return {
        "contract_id": contract_id,
        "consumer_id": consumer_id,
        "classifications": classifications,
        "signature": signer(contract_id, consumer_id, classifications),
    }


@app.get("/audit")
def lire_audit(x_api_key: Optional[str] = Header(default=None)):
    """Journal d'accès du nœud A (traçabilité)."""
    controler_cle(x_api_key, "audit")
    return journal