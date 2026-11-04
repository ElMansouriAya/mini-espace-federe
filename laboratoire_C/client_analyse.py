"""Laboratoire C - Orchestrateur : n'a aucun accès direct aux fichiers SQLite.

Scénario du TP 4 : catalogue -> contrat -> classifications signées -> calcul
réalisé par l'hôpital -> agrégats. Inclut les tests négatifs demandés.

Usage (depuis la racine du projet, nœuds A et B démarrés) :
    python laboratoire_C/client_analyse.py
    python laboratoire_C/client_analyse.py --bruit [--epsilon 1.0]
"""
import argparse
import os

import requests

URL_AIR = os.getenv("URL_AIR", "http://127.0.0.1:8001")
URL_HOPITAL = os.getenv("URL_HOPITAL", "http://127.0.0.1:8002")
CLE_A = os.getenv("CLE_AIR", "secret-air-key-demo")
CLE_B = os.getenv("CLE_HOPITAL", "secret-hospital-key-demo")
CONSUMER_ID = "laboratoire-iasd"
DATASET_ID = "dataset-air-tanger"
TIMEOUT = 10


def negocier(session, purpose, cle=CLE_A, dataset_id=DATASET_ID):
    return session.post(
        f"{URL_AIR}/contracts/negotiate",
        json={"dataset_id": dataset_id, "consumer_id": CONSUMER_ID, "purpose": purpose},
        headers={"X-API-Key": cle},
        timeout=TIMEOUT,
    )


def executer_scenario(apply_noise=False, epsilon=1.0):
    session = requests.Session()

    print("1. Découverte du catalogue")
    r = session.get(f"{URL_AIR}/catalog", timeout=TIMEOUT)
    r.raise_for_status()
    print("  ", r.json()[0]["title"])

    print("\n2. Tests négatifs")
    r = negocier(session, "commercial")
    print(f"   Finalité commerciale : attendu 403, reçu {r.status_code}")
    r = negocier(session, "research", dataset_id="dataset-inconnu")
    print(f"   Jeu de données inexistant : attendu 404, reçu {r.status_code}")
    r = negocier(session, "research", cle="mauvaise-cle")
    print(f"   Clé API incorrecte : attendu 401, reçu {r.status_code}")

    print("\n3. Demande autorisée pour la recherche")
    r = negocier(session, "research")
    r.raise_for_status()
    contract_id = r.json()["contract_id"]
    print("   Accord obtenu :", contract_id)

    print("\n4. Récupération des classifications")
    r = session.get(
        f"{URL_AIR}/classifications",
        params={"contract_id": contract_id, "consumer_id": CONSUMER_ID},
        headers={"X-API-Key": CLE_A},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    paquet = r.json()
    print("   Nombre de jours classifiés :", len(paquet["classifications"]))

    print("\n5. Calcul réalisé par l'hôpital", "(avec bruit)" if apply_noise else "(sans bruit)")
    r = session.post(
        f"{URL_HOPITAL}/compute",
        json={**paquet, "apply_dp": apply_noise, "epsilon": epsilon},
        headers={"X-API-Key": CLE_B},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    res = r.json()
    for nom, cle in [
        ("Pollution au-dessus du seuil", "au_dessus_seuil"),
        ("Pollution sous le seuil", "sous_seuil"),
    ]:
        g = res[cle]
        print(f"   {nom} : n={g['n']}, moyenne={g['moyenne']}, statut={g['statut']}")
    a, b = res["au_dessus_seuil"]["moyenne"], res["sous_seuil"]["moyenne"]
    if a is not None and b is not None:
        print(f"   Différence : {a - b:.2f} admissions/jour")

    print("\n6. Test négatif : classifications falsifiées envoyées à l'hôpital")
    faux = dict(paquet)
    faux["classifications"] = paquet["classifications"][:4]  # sous-ensemble choisi par le labo
    r = session.post(
        f"{URL_HOPITAL}/compute", json=faux, headers={"X-API-Key": CLE_B}, timeout=TIMEOUT
    )
    print(f"   Attendu 403 (signature invalide), reçu {r.status_code}")

    print("\n7. Test négatif : clé API de l'hôpital incorrecte")
    r = session.post(
        f"{URL_HOPITAL}/compute", json=paquet, headers={"X-API-Key": "mauvaise-cle"}, timeout=TIMEOUT
    )
    print(f"   Attendu 401, reçu {r.status_code}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client du laboratoire (Nœud C)")
    parser.add_argument("--bruit", action="store_true", help="demander le bruit de Laplace")
    parser.add_argument("--epsilon", type=float, default=1.0)
    args = parser.parse_args()
    try:
        executer_scenario(apply_noise=args.bruit, epsilon=args.epsilon)
    except requests.exceptions.ConnectionError as e:
        raise SystemExit(f"Impossible de joindre un nœud (A sur 8001, B sur 8002 ?) : {e}")
