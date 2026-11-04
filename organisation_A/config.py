"""Configuration centrale du nœud A (Environnement).

Toutes les valeurs sensibles se surchargent par variables d'environnement.
Les valeurs par défaut sont des valeurs de DÉMONSTRATION : jamais en production.
"""
import os
from pathlib import Path

RACINE_A = Path(__file__).resolve().parent

# Bases : TP1-TP3 (5 jours) et TP4 (10 jours) sont séparées pour ne pas s'écraser.
DB_AIR_TP1 = RACINE_A / "database" / "environnement_tp1.db"
DB_AIR = Path(os.getenv("ENVIRONNEMENT_DB", RACINE_A / "database" / "environnement.db"))

# Clé TP3 (différente de celles du TP4, comme demandé par le sujet)
CLE_API_TP3 = os.getenv("CLE_ENVIRONNEMENT", "demo-air-123")

# Secrets TP4
CLE_API_A = os.getenv("CLE_AIR", "secret-air-key-demo")
# ATTENTION : cette valeur DOIT être identique côté nœud B (même variable d'env).
SECRET_FEDERATION = os.getenv("SECRET_FEDERATION", "secret-federation-demo").encode("utf-8")

# Gouvernance (règle inspirée d'ODRL)
DATASET_ID = "dataset-air-tanger"
FINALITE_AUTORISEE = "research"
CONSOMMATEURS_AUTORISES = {"laboratoire-iasd"}

# Seuil pédagogique (µg/m³), pas une référence réglementaire
SEUIL_PM25 = 30.0
