# Mini-espace de données fédéré — Santé et qualité de l'air

Master IASD — Data Spaces & Data Integration & Semantic Interoperability
TP 1 à 4 : prototype d'un espace de données régional (Tanger, données fictives).


## Architecture

| Nœud | Rôle | Port |
|------|------|------|
| Organisation A | Environnement : PM2.5, catalogue, contrat, classifications signées (HMAC) | 8001 | 
| Organisation B | Hôpital : admissions, calcul local, seuil minimal, bruit de Laplace | 8002 | 
| Laboratoire C | Orchestrateur : n'ouvre jamais les bases, ne reçoit que des agrégats | — | 

Flux (TP 4) :

1. C lit le catalogue de A (`GET /catalog`)
2. C demande un contrat à A (`POST /contracts/negotiate`, finalité `research`)
3. C récupère les classifications signées (`GET /classifications`)
4. C transmet le paquet signé à B (`POST /compute`)
5. B vérifie la signature, calcule localement et renvoie uniquement des agrégats

## Arborescence

```
mini-espace-federe/
├── organisation_A/            # voir organisation_A/README_A.md
│   ├── database/
│   ├── api/                        # api_air_tp2, api_air_v3, api_air (TP4)
│   └── security/
├── organisation_B/
│   ├── database/
│   │   ├── setup_hopital.py        # hopital_tp1.db (5 j, TP1-3) / hopital.db (10 j, TP4)
│   │   └── consulter_hopital.py    # TP1 : affiche les bases
│   ├── api/
│   │   ├── api_hopital_tp2.py      # TP2 : /admissions, /statistiques (brut)
│   │   ├── api_hopital_v3.py       # TP3 : /analyse-locale (clé API)
│   │   └── api_hopital.py          # TP4 : POST /compute
│   ├── services/
│   │   ├── confidentialite.py      # seuil minimal, bruit de Laplace, budget epsilon
│   │   └── calcul_local.py         # agrégats calculés près des données
│   └── security/
│       ├── auth.py                 # clé API (401)
│       └── signature.py            # vérification HMAC de A (403)
├── laboratoire_C/
│   ├── tp2_client.py               # TP2
│   ├── tp3_laboratoire.py          # TP3
│   ├── tp3_attaque_difference.py   # TP3, section 8
│   └── client_analyse.py           # TP4
├── tests/
│   ├── test_organisation_B.py      # TP4
│   └── test_organisation_B_tp1_tp3.py
├── requirements.txt
└── README.md
```

## Installation

Python 3.10 ou plus.

Windows PowerShell :
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Linux / macOS :
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Configuration (variables d'environnement)

| Variable | Valeur par défaut (démo) | Utilisée par |
|----------|--------------------------|--------------|
| `CLE_HOPITAL` | `secret-hospital-key-demo` | B (clé API) |
| `CLE_AIR` | `secret-air-key-demo` | A (clé API) |
| `SECRET_FEDERATION` | `secret-federation-demo` | A et B (signature HMAC) |

`SECRET_FEDERATION` doit être **identique** chez A et chez B, sinon B répond 403.
Le format du message signé doit aussi être identique des deux côtés :
JSON de `{contract_id, consumer_id, classifications}` avec `sort_keys=True`,
séparateurs `(",", ":")` et `ensure_ascii=False`.

## TP 1 à 3 (bases de 5 jours)

Un seul TP à la fois : les API utilisent toujours les ports 8001 et 8002.
Arrêtez les serveurs (Ctrl+C) avant de passer au TP suivant.

```
# TP1 : créer et consulter les bases de 5 jours
python organisation_A/database/setup_data.py --jeu tp1
python organisation_B/database/setup_hopital.py --jeu tp1
python organisation_A/database/consulter_environnement.py
python organisation_B/database/consulter_hopital.py

# TP2 : API ouvertes (données brutes) -> attendu : 16 et 8,5
python -m uvicorn organisation_A.api.api_air_tp2:app --port 8001
python -m uvicorn organisation_B.api.api_hopital_tp2:app --port 8002
python laboratoire_C/tp2_client.py

# TP3 : catégories + calcul local + clé API -> attendu : 16, 8,5, différence 7,5
# PowerShell : $env:CLE_ENVIRONNEMENT="demo-air-123" ; $env:CLE_HOPITAL="demo-hopital-456"
python -m uvicorn organisation_A.api.api_air_v3:app --port 8001
python -m uvicorn organisation_B.api.api_hopital_v3:app --port 8002
python laboratoire_C/tp3_laboratoire.py
python laboratoire_C/tp3_attaque_difference.py   # révèle l'admission du 01/10 (8.0)
```

Les clés du TP3 (`demo-air-123`, `demo-hopital-456`) sont différentes de celles du TP4.

## Lancement (TP 4)

Toutes les commandes se lancent **depuis la racine du projet**, dans trois terminaux
avec l'environnement virtuel activé. N'utilisez pas `--reload` : chaque redémarrage
efface les contrats et le budget de confidentialité stockés en mémoire.

**Organisation B (Hôpital)**
```
python organisation_B/database/setup_hopital.py
python -m uvicorn organisation_B.api.api_hopital:app --port 8002
```
Documentation interactive : http://127.0.0.1:8002/docs

**Organisation A (Environnement)** — voir la partie 1
```
python -m uvicorn organisation_A.api.api_air:app --port 8001
```

**Laboratoire C**
```
python laboratoire_C/client_analyse.py
python laboratoire_C/client_analyse.py --bruit
```

## Tests

```
python -m pytest tests -v
```

Les tests de l'Organisation B simulent A avec la même fonction de signature et
couvrent : calcul sans bruit (16,2 / 7,8), clé incorrecte ou absente (401),
signature falsifiée (403), catégorie inconnue, dates dupliquées, liste vide, date
absente (400), seuil minimal, bruit borné et variable, budget épuisé au 4e appel (429).

## Résultats attendus (TP 4)

- Au-dessus du seuil (5 jours) : (14 + 18 + 16 + 20 + 13) / 5 = **16,2**
- Sous le seuil (5 jours) : (8 + 9 + 10 + 7 + 5) / 5 = **7,8**
- Différence : **8,4** admissions par jour

Cette différence suggère une association sur un petit jeu fictif ; elle ne démontre
pas de causalité.

## Limites

- Le seuil minimal de 3 jours n'est pas du k-anonymat.
- Le bruit de Laplace est une illustration : ce n'est pas une implémentation complète
  de confidentialité différentielle (pas de comptabilité formelle rigoureuse, budget
  en mémoire, bornes pédagogiques).
- La fédération ne signifie pas qu'aucune donnée n'est échangée : les classifications
  et les agrégats circulent.
- Une clé API ne suffit pas à garantir la souveraineté des données.
