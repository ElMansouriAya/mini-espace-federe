"""Tests de l'Organisation B pour les TP 1 à 3 (base de 5 jours)."""
import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from organisation_B.api.api_hopital_tp2 import app as app_tp2
from organisation_B.api.api_hopital_v3 import CLE_API_TP3, app as app_v3
from organisation_B.database import setup_hopital
from organisation_B.database.setup_hopital import DB_HOPITAL_TP1, DONNEES_TP1

CLASSIFS_TP3 = [
    {"date": "2026-10-01", "categorie": "non_elevee"},
    {"date": "2026-10-02", "categorie": "elevee"},
    {"date": "2026-10-03", "categorie": "elevee"},
    {"date": "2026-10-04", "categorie": "non_elevee"},
    {"date": "2026-10-05", "categorie": "elevee"},
]
H = {"X-API-Key": CLE_API_TP3}


@pytest.fixture(autouse=True)
def base_tp1():
    setup_hopital.creer_base(DB_HOPITAL_TP1, DONNEES_TP1)


def test_tp1_base_de_cinq_lignes():
    with closing(sqlite3.connect(DB_HOPITAL_TP1)) as db:
        assert db.execute("SELECT COUNT(*) FROM admissions").fetchone()[0] == 5


def test_tp2_admissions_brutes():
    r = TestClient(app_tp2).get("/admissions")
    assert r.status_code == 200
    assert [x["nombre"] for x in r.json()] == [8, 14, 18, 9, 16]


def test_tp2_statistiques():
    r = TestClient(app_tp2).get("/statistiques")
    assert r.json() == {"nombre_jours": 5, "moyenne_admissions": 13.0}


def test_tp3_sans_cle_401():
    r = TestClient(app_v3).post("/analyse-locale", json={"classifications": CLASSIFS_TP3})
    assert r.status_code == 401


def test_tp3_cle_incorrecte_401():
    r = TestClient(app_v3).post(
        "/analyse-locale", json={"classifications": CLASSIFS_TP3}, headers={"X-API-Key": "faux"}
    )
    assert r.status_code == 401


def test_tp3_resultats_attendus():
    r = TestClient(app_v3).post("/analyse-locale", json={"classifications": CLASSIFS_TP3}, headers=H)
    assert r.status_code == 200
    assert r.json() == {
        "elevee": {"nombre_jours": 3, "moyenne_admissions": 16.0},
        "non_elevee": {"nombre_jours": 2, "moyenne_admissions": 8.5},
    }


def test_tp3_categorie_inconnue_400():
    faux = [{"date": "2026-10-01", "categorie": "inconnue"}]
    r = TestClient(app_v3).post("/analyse-locale", json={"classifications": faux}, headers=H)
    assert r.status_code == 400


def test_tp3_dates_en_double_400():
    doublon = CLASSIFS_TP3 + [CLASSIFS_TP3[0]]
    r = TestClient(app_v3).post("/analyse-locale", json={"classifications": doublon}, headers=H)
    assert r.status_code == 400


def test_tp3_attaque_par_difference_reussit():
    """Limite du TP3 : un groupe d'un seul jour révèle l'admission exacte (8)."""
    demande = {"classifications": [{"date": "2026-10-01", "categorie": "non_elevee"}]}
    r = TestClient(app_v3).post("/analyse-locale", json=demande, headers=H)
    assert r.json()["non_elevee"] == {"nombre_jours": 1, "moyenne_admissions": 8.0}
    assert r.json()["elevee"] == {"nombre_jours": 0, "moyenne_admissions": None}
