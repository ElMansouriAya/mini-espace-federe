"""Organisation B - Protections sur les résultats : seuil minimal, bruit de Laplace, budget.

Ce n'est PAS une implémentation formelle de confidentialité différentielle
ni du k-anonymat : c'est une illustration pédagogique.
"""
import math
import random

SEUIL_MIN_JOURS = 3      # seuil minimal de publication (PAS du k-anonymat)
BORNE_MAX = 30.0         # borne pédagogique d'admissions par jour
BUDGET_EPSILON = 3.0     # budget cumulé par contrat (simulation)
RNG = random.SystemRandom()  # aléa non prévisible (et non random.random)

budget_utilise = {}      # contract_id -> epsilon consommé (en mémoire)


def bruit_laplace(echelle):
    u = RNG.random() - 0.5
    while u == -0.5:  # évite log(0)
        u = RNG.random() - 0.5
    return -echelle * math.copysign(1.0, u) * math.log(1 - 2 * abs(u))


def consommer_budget(contract_id, epsilon):
    """Retourne True si le budget le permet (et le consomme), False sinon."""
    utilise = budget_utilise.get(contract_id, 0.0)
    if utilise + epsilon > BUDGET_EPSILON:
        return False
    budget_utilise[contract_id] = utilise + epsilon
    return True


def resumer(valeurs, apply_dp, epsilon):
    n = len(valeurs)
    if n < SEUIL_MIN_JOURS:
        return {"n": n, "moyenne": None, "statut": "SUPPRIME_GROUPE_TROP_PETIT"}
    moyenne = sum(valeurs) / n
    if apply_dp:
        sensibilite = BORNE_MAX / n  # moyenne d'un groupe de taille n fixée
        moyenne += bruit_laplace(sensibilite / epsilon)
        moyenne = min(max(moyenne, 0.0), BORNE_MAX)  # post-traitement
    return {"n": n, "moyenne": round(moyenne, 2), "statut": "OK"}
