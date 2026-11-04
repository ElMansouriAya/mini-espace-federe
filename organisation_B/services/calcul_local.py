"""Organisation B - Calcul local des agrégats à partir de la base hospitalière."""
from contextlib import closing
from pathlib import Path
import sqlite3

from .confidentialite import resumer

CATEGORIES_VALIDES = {"au_dessus_seuil", "sous_seuil"}
DB_HOPITAL = Path(__file__).resolve().parent.parent / "database" / "hopital.db"


def lire_admissions():
    with closing(sqlite3.connect(DB_HOPITAL)) as conn:
        return dict(conn.execute("SELECT date, nombre FROM admissions").fetchall())


def calculer_agregats(classifications, admissions, apply_dp, epsilon):
    """classifications : liste de dicts {"date", "categorie"}."""
    groupes = {cat: [] for cat in CATEGORIES_VALIDES}
    for c in classifications:
        groupes[c["categorie"]].append(admissions[c["date"]])
    return {
        "au_dessus_seuil": resumer(groupes["au_dessus_seuil"], apply_dp, epsilon),
        "sous_seuil": resumer(groupes["sous_seuil"], apply_dp, epsilon),
        "bruit_applique": apply_dp,
        "epsilon": epsilon if apply_dp else None,
    }
