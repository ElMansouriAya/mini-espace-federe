"""Organisation B - Vérification de la signature HMAC émise par l'organisation A.

Le secret est partagé avec A (valeur de démonstration, jamais en production).
Le format du message signé DOIT rester identique à celui de A.
"""
import hashlib
import hmac
import json
import os

SECRET_FEDERATION = os.getenv("SECRET_FEDERATION", "secret-federation-demo").encode()


def signature_attendue(contract_id, consumer_id, classifications):
    """classifications : liste de dicts {"date": ..., "categorie": ...}."""
    message = json.dumps(
        {
            "contract_id": contract_id,
            "consumer_id": consumer_id,
            "classifications": classifications,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hmac.new(SECRET_FEDERATION, message, hashlib.sha256).hexdigest()


def signature_valide(signature, contract_id, consumer_id, classifications):
    attendue = signature_attendue(contract_id, consumer_id, classifications)
    return hmac.compare_digest(signature, attendue)
