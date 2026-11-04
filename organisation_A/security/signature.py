"""Signature HMAC-SHA256 des classifications émises par le nœud A.

Le format du message DOIT rester identique à celui vérifié par le nœud B :
JSON trié, séparateurs compacts, ensure_ascii=False, encodé en UTF-8.
"""
import hashlib
import hmac
import json

from organisation_A import config


def message_canonique(contract_id, consumer_id, classifications):
    return json.dumps(
        {
            "contract_id": contract_id,
            "consumer_id": consumer_id,
            "classifications": classifications,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def signer(contract_id, consumer_id, classifications, secret=None):
    secret = config.SECRET_FEDERATION if secret is None else secret
    msg = message_canonique(contract_id, consumer_id, classifications)
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def verifier(signature, contract_id, consumer_id, classifications, secret=None):
    attendue = signer(contract_id, consumer_id, classifications, secret)
    return hmac.compare_digest(signature, attendue)
