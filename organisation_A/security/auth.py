"""Contrôle d'accès par clé API (comparaison en temps constant)."""
import hmac


def cle_valide(fournie, attendue):
    """Compare deux clés sans fuite temporelle. None / vide => refus."""
    if not fournie:
        return False
    return hmac.compare_digest(fournie.encode("utf-8"), attendue.encode("utf-8"))
