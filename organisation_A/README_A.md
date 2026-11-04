# Organisation A — Direction régionale de l'environnement

Les mesures PM2.5 ne quittent jamais ce nœud : seules des **catégories signées** circulent.

## Structure
| Fichier | TP | Rôle |
|---|---|---|
| `database/setup_data.py` | 1 / 4 | Crée `environnement_tp1.db` (5 j) et `environnement.db` (10 j) |
| `database/consulter_environnement.py` | 1 | Affiche le contenu des bases |
| `api/api_air_tp2.py` | 2 | API ouverte (`/mesures`, `/statistiques`) — données brutes |
| `api/api_air_v3.py` | 3 | API protégée par clé, `/categories` seulement |
| `api/api_air.py` | 4 | Catalogue, négociation de contrat, classifications signées HMAC, audit |
| `security/auth.py` | 3-4 | Vérification de clé API en temps constant |
| `security/signature.py` | 4 | Signature / vérification HMAC-SHA256 |
| `config.py` | all | Clés, secret, finalité, seuil (surchargeables par variables d'env) |

## Lancement (depuis la RACINE du dépôt, venv actif)
```powershell
pip install -r requirements.txt
python organisation_A/database/setup_data.py            # TP4 (10 jours)
python organisation_A/database/setup_data.py --jeu tp1  # TP1-3 (5 jours)

# TP2 / TP3 / TP4 : un seul à la fois sur le port 8001, SANS --reload
python -m uvicorn organisation_A.api.api_air_tp2:app --port 8001
$env:CLE_ENVIRONNEMENT="demo-air-123"; python -m uvicorn organisation_A.api.api_air_v3:app --port 8001
$env:SECRET_FEDERATION="secret-federation-demo"; python -m uvicorn organisation_A.api.api_air:app --port 8001
```
Docs Swagger : http://127.0.0.1:8001/docs — clé TP4 : `secret-air-key-demo`.

## Tests
`python -m pytest tests -v` (15 tests, dont 8 négatifs : finalité, clé, dataset, consommateur, contrat, signature).

## Contrat d'interface avec le nœud B (à vérifier avec le binôme)
- `SECRET_FEDERATION` identique des deux côtés (défaut : `secret-federation-demo`).
- Message signé : JSON `{contract_id, consumer_id, classifications}`, `sort_keys=True`, séparateurs `(",",":")`, `ensure_ascii=False`, UTF-8, HMAC-SHA256 hex.
- Catégories : `au_dessus_seuil` / `sous_seuil`.
