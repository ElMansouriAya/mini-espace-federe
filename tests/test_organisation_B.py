"""Tests de l'Organisation B (hôpital). A est simulée via la même fonction de signature."""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from organisation_B.api.api_hopital import app  # noqa: E402
from organisation_B.database.setup_hopital import creer_base  # noqa: E402
from organisation_B.security.signature import signature_attendue  # noqa: E402
from organisation_B.services import confidentialite  # noqa: E402

CLE_B = "secret-hospital-key-demo"
CONSUMER = "laboratoire-iasd"

CLASSIFS = [
    {"date": "2026-10-01", "categorie": "sous_seuil"},
    {"date": "2026-10-02", "categorie": "au_dessus_seuil"},
    {"date": "2026-10-03", "categorie": "au_dessus_seuil"},
    {"date": "2026-10-04", "categorie": "sous_seuil"},
    {"date": "2026-10-05", "categorie": "au_dessus_seuil"},
    {"date": "2026-10-06", "categorie": "au_dessus_seuil"},
    {"date": "2026-10-07", "categorie": "sous_seuil"},
    {"date": "2026-10-08", "categorie": "sous_seuil"},
    {"date": "2026-10-09", "categorie": "au_dessus_seuil"},
    {"date": "2026-10-10", "categorie": "sous_seuil"},
]


@pytest.fixture(autouse=True)
def base_et_budget():
    creer_base()
    confidentialite.budget_utilise.clear()


@pytest.fixture
def client():
    return TestClient(app)


def paquet(contract_id="contract-test", classifs=None, **extra):
    classifs = CLASSIFS if classifs is None else classifs
    return {
        "contract_id": contract_id,
        "consumer_id": CONSUMER,
        "classifications": classifs,
        "signature": signature_attendue(contract_id, CONSUMER, classifs),
        **extra,
    }


def post(client, corps, cle=CLE_B):
    headers = {"X-API-Key": cle} if cle is not None else {}
    return client.post("/compute", json=corps, headers=headers)


def test_calcul_sans_bruit(client):
    r = post(client, paquet())
    assert r.status_code == 200
    res = r.json()
    assert res["au_dessus_seuil"] == {"n": 5, "moyenne": 16.2, "statut": "OK"}
    assert res["sous_seuil"] == {"n": 5, "moyenne": 7.8, "statut": "OK"}
    assert res["bruit_applique"] is False


def test_cle_incorrecte(client):
    assert post(client, paquet(), cle="mauvaise").status_code == 401


def test_cle_absente(client):
    assert post(client, paquet(), cle=None).status_code == 401


def test_signature_falsifiee_sous_ensemble(client):
    corps = paquet()
    corps["classifications"] = CLASSIFS[:4]  # attaque par différence
    assert post(client, corps).status_code == 403


def test_signature_falsifiee_categorie_modifiee(client):
    corps = paquet()
    corps["classifications"] = [dict(c) for c in CLASSIFS]
    corps["classifications"][0]["categorie"] = "au_dessus_seuil"
    assert post(client, corps).status_code == 403


def test_categorie_inconnue(client):
    classifs = [dict(c) for c in CLASSIFS]
    classifs[0]["categorie"] = "inconnue"
    assert post(client, paquet(classifs=classifs)).status_code == 400


def test_dates_dupliquees(client):
    classifs = CLASSIFS + [CLASSIFS[0]]
    assert post(client, paquet(classifs=classifs)).status_code == 400


def test_liste_vide(client):
    assert post(client, paquet(classifs=[])).status_code == 400


def test_date_absente_de_la_base(client):
    classifs = [{"date": "2030-01-01", "categorie": "sous_seuil"}]
    assert post(client, paquet(classifs=classifs)).status_code == 400


def test_seuil_minimal_supprime_petit_groupe(client):
    classifs = [
        {"date": "2026-10-01", "categorie": "sous_seuil"},
        {"date": "2026-10-02", "categorie": "au_dessus_seuil"},
        {"date": "2026-10-03", "categorie": "au_dessus_seuil"},
        {"date": "2026-10-04", "categorie": "au_dessus_seuil"},
    ]
    res = post(client, paquet(classifs=classifs)).json()
    assert res["sous_seuil"]["statut"] == "SUPPRIME_GROUPE_TROP_PETIT"
    assert res["sous_seuil"]["moyenne"] is None
    assert res["au_dessus_seuil"]["statut"] == "OK"


def test_bruit_borne_et_variable(client):
    moyennes = set()
    for _ in range(3):
        r = post(client, paquet(apply_dp=True, epsilon=1.0))
        assert r.status_code == 200
        res = r.json()
        assert res["bruit_applique"] is True
        for groupe in ("au_dessus_seuil", "sous_seuil"):
            assert 0.0 <= res[groupe]["moyenne"] <= 30.0
            assert res[groupe]["n"] == 5  # effectifs non bruités
        moyennes.add(res["au_dessus_seuil"]["moyenne"])
    assert len(moyennes) > 1  # le bruit change à chaque appel


def test_budget_epuise_au_4e_appel(client):
    corps = paquet(apply_dp=True, epsilon=1.0)
    assert [post(client, corps).status_code for _ in range(3)] == [200, 200, 200]
    assert post(client, corps).status_code == 429


def test_budget_par_contrat(client):
    for _ in range(3):
        post(client, paquet("contract-1", apply_dp=True, epsilon=1.0))
    assert post(client, paquet("contract-2", apply_dp=True, epsilon=1.0)).status_code == 200
