"""Organisation B (Hôpital) - API : calcul local d'agrégats, seuil minimal, bruit de Laplace.

Lancement depuis la racine du projet (mini-espace-federe/), sans --reload :
    python -m uvicorn organisation_B.api.api_hopital:app --port 8002
"""
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from ..security.auth import verifier_cle
from ..security.signature import signature_valide
from ..services.calcul_local import (
    CATEGORIES_VALIDES,
    calculer_agregats,
    lire_admissions,
)
from ..services.confidentialite import consommer_budget

app = FastAPI(title="Nœud B - Hôpital")


class Classification(BaseModel):
    date: str
    categorie: str


class RequeteCalcul(BaseModel):
    contract_id: str
    consumer_id: str
    classifications: list[Classification]
    signature: str
    apply_dp: bool = False
    epsilon: float = Field(default=1.0, gt=0)


@app.get("/")
def accueil():
    return {"organisation": "Hôpital régional"}


@app.post("/compute")
def calculer(req: RequeteCalcul, x_api_key: Optional[str] = Header(default=None)):
    # 1. Clé API (401)
    verifier_cle(x_api_key)

    classifications = [c.model_dump() for c in req.classifications]

    # 2. Signature émise par A pour ce contrat et ce consommateur (403)
    if not signature_valide(
        req.signature, req.contract_id, req.consumer_id, classifications
    ):
        raise HTTPException(
            status_code=403,
            detail="Signature invalide : classification non émise par le nœud A",
        )

    # 3. Validation du contenu (400)
    if not classifications:
        raise HTTPException(status_code=400, detail="Liste de classifications vide")
    dates = [c["date"] for c in classifications]
    if len(dates) != len(set(dates)):
        raise HTTPException(status_code=400, detail="Date dupliquée")
    for c in classifications:
        if c["categorie"] not in CATEGORIES_VALIDES:
            raise HTTPException(
                status_code=400, detail=f"Catégorie inconnue : {c['categorie']}"
            )

    admissions = lire_admissions()
    inconnues = [d for d in dates if d not in admissions]
    if inconnues:
        raise HTTPException(
            status_code=400,
            detail=f"Dates absentes de la base hospitalière : {inconnues}",
        )

    # 4. Budget de confidentialité si bruit demandé (429)
    if req.apply_dp and not consommer_budget(req.contract_id, req.epsilon):
        raise HTTPException(
            status_code=429,
            detail="Budget de confidentialité épuisé pour ce contrat",
        )

    # 5. Calcul local : seuls des agrégats sortent
    return calculer_agregats(classifications, admissions, req.apply_dp, req.epsilon)