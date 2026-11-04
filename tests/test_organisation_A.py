"""Tests du nœud A. Lancer depuis la racine : python -m pytest tests -v"""
import pytest
from fastapi.testclient import TestClient

from organisation_A import config
from organisation_A.api import api_air
from organisation_A.database.setup_data import creer_base_air, DONNEES_TP4
from organisation_A.security.signature import signer, verifier

CLE = "secret-air-key-demo"
H = {"X-API-Key": CLE}
DEMANDE = {"dataset_id": "dataset-air-tanger", "consumer_id": "laboratoire-iasd", "purpose": "research"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "env_test.db"
    creer_base_air(db, DONNEES_TP4)
    monkeypatch.setattr(config, "DB_AIR", db)
    monkeypatch.setattr(config, "CLE_API_A", CLE)
    api_air.contrats.clear()
    api_air.journal.clear()
    return TestClient(api_air.app)


def contrat(client):
    return client.post("/contracts/negotiate", json=DEMANDE, headers=H).json()["contract_id"]


def test_catalogue_200(client):
    r = client.get("/catalog")
    assert r.status_code == 200 and r.json()[0]["dataset_id"] == "dataset-air-tanger"


def test_negociation_ok(client):
    r = client.post("/contracts/negotiate", json=DEMANDE, headers=H)
    assert r.status_code == 200 and r.json()["status"] == "AGREED"


def test_negatif_finalite_commerciale_403(client):
    r = client.post("/contracts/negotiate", json={**DEMANDE, "purpose": "commercial"}, headers=H)
    assert r.status_code == 403


def test_negatif_dataset_inconnu_404(client):
    r = client.post("/contracts/negotiate", json={**DEMANDE, "dataset_id": "x"}, headers=H)
    assert r.status_code == 404


def test_negatif_cle_incorrecte_401(client):
    r = client.post("/contracts/negotiate", json=DEMANDE, headers={"X-API-Key": "mauvaise"})
    assert r.status_code == 401


def test_negatif_sans_cle_401(client):
    assert client.post("/contracts/negotiate", json=DEMANDE).status_code == 401


def test_negatif_consommateur_inconnu_403(client):
    r = client.post("/contracts/negotiate", json={**DEMANDE, "consumer_id": "pirate"}, headers=H)
    assert r.status_code == 403


def test_classifications_10_jours_signees(client):
    cid = contrat(client)
    r = client.get("/classifications", params={"contract_id": cid, "consumer_id": "laboratoire-iasd"}, headers=H)
    assert r.status_code == 200
    p = r.json()
    assert len(p["classifications"]) == 10
    cats = [c["categorie"] for c in p["classifications"]]
    assert cats.count("au_dessus_seuil") == 5 and cats.count("sous_seuil") == 5
    assert verifier(p["signature"], cid, "laboratoire-iasd", p["classifications"])


def test_aucune_valeur_pm25_brute_exposee(client):
    cid = contrat(client)
    p = client.get("/classifications", params={"contract_id": cid, "consumer_id": "laboratoire-iasd"}, headers=H).json()
    assert all(set(c) == {"date", "categorie"} for c in p["classifications"])


def test_signature_falsifiee_detectee(client):
    cid = contrat(client)
    p = client.get("/classifications", params={"contract_id": cid, "consumer_id": "laboratoire-iasd"}, headers=H).json()
    assert not verifier(p["signature"], cid, "laboratoire-iasd", p["classifications"][:4])


def test_signature_liee_au_consommateur():
    cl = [{"date": "2026-10-01", "categorie": "sous_seuil"}]
    assert signer("c1", "labo", cl) != signer("c1", "autre", cl)


def test_negatif_contrat_inconnu_403(client):
    r = client.get("/classifications", params={"contract_id": "contract-air-zzz", "consumer_id": "laboratoire-iasd"}, headers=H)
    assert r.status_code == 403


def test_negatif_consommateur_different_du_contrat_403(client):
    cid = contrat(client)
    r = client.get("/classifications", params={"contract_id": cid, "consumer_id": "autre"}, headers=H)
    assert r.status_code == 403


def test_negatif_classifications_sans_cle_401(client):
    r = client.get("/classifications", params={"contract_id": "x", "consumer_id": "y"})
    assert r.status_code == 401


def test_audit_trace_les_refus(client):
    client.post("/contracts/negotiate", json={**DEMANDE, "purpose": "commercial"}, headers=H)
    j = client.get("/audit", headers=H).json()
    assert j[-1]["statut"] == 403 and j[-1]["evenement"] == "negociation"
    assert client.get("/audit").status_code == 401
