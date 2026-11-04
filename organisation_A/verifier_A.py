"""Auto-vérification du nœud A : rejoue ce que fera le laboratoire (C).

1) Lancer le serveur :  python -m uvicorn organisation_A.api.api_air:app --port 8001
2) Dans un autre terminal (racine du dépôt) :  python -m organisation_A.verifier_A
"""
import sys
import requests

from organisation_A.security.signature import verifier

URL = "http://127.0.0.1:8001"
H = {"X-API-Key": "secret-air-key-demo"}
BODY = {"dataset_id": "dataset-air-tanger", "consumer_id": "laboratoire-iasd", "purpose": "research"}
echecs = 0


def check(nom, condition, detail=""):
    global echecs
    print(f"  [{'PASS' if condition else 'FAIL'}] {nom} {detail}")
    if not condition:
        echecs += 1


def post(body=None, headers=H):
    return requests.post(f"{URL}/contracts/negotiate", json=body or BODY, headers=headers, timeout=5)


try:
    requests.get(f"{URL}/health", timeout=3)
except requests.ConnectionError:
    sys.exit("Serveur A injoignable sur le port 8001 : lancez uvicorn d'abord.")

print("Catalogue")
r = requests.get(f"{URL}/catalog", timeout=5)
check("GET /catalog = 200", r.status_code == 200)
check("dataset_id présent", r.json()[0]["dataset_id"] == "dataset-air-tanger")

print("Négociation")
r = post()
check("finalité research = 200", r.status_code == 200, r.text[:60])
cid = r.json().get("contract_id")
check("finalité commercial = 403", post({**BODY, "purpose": "commercial"}).status_code == 403)
check("dataset inconnu = 404", post({**BODY, "dataset_id": "x"}).status_code == 404)
check("clé incorrecte = 401", post(headers={"X-API-Key": "faux"}).status_code == 401)
check("consommateur inconnu = 403", post({**BODY, "consumer_id": "pirate"}).status_code == 403)

print("Classifications")
r = requests.get(f"{URL}/classifications", params={"contract_id": cid, "consumer_id": BODY["consumer_id"]}, headers=H, timeout=5)
check("200", r.status_code == 200)
p = r.json()
cl = p["classifications"]
cats = [c["categorie"] for c in cl]
check("10 jours", len(cl) == 10)
check("5 au_dessus_seuil / 5 sous_seuil", cats.count("au_dessus_seuil") == 5 and cats.count("sous_seuil") == 5)
check("aucune valeur PM2.5 exposée", all(set(c) == {"date", "categorie"} for c in cl))
check("signature HMAC valide", verifier(p["signature"], cid, BODY["consumer_id"], cl))
check("signature invalide si liste tronquée", not verifier(p["signature"], cid, BODY["consumer_id"], cl[:4]))
r = requests.get(f"{URL}/classifications", params={"contract_id": "contract-air-inconnu", "consumer_id": BODY["consumer_id"]}, headers=H, timeout=5)
check("contrat inconnu = 403", r.status_code == 403)
r = requests.get(f"{URL}/classifications", params={"contract_id": cid, "consumer_id": "autre"}, headers=H, timeout=5)
check("mauvais consommateur = 403", r.status_code == 403)

print("\nRÉSULTAT :", "NŒUD A PRÊT POUR LE LABORATOIRE" if echecs == 0 else f"{echecs} ÉCHEC(S)")
sys.exit(1 if echecs else 0)
