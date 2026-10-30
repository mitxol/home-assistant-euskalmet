"""Tests for PEM normalization without importing Home Assistant."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

MODULE_PATH = Path(__file__).parents[1] / "custom_components" / "euskalmet" / "pem.py"
SPEC = spec_from_file_location("euskalmet_pem", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

normalize_pem = MODULE.normalize_pem

KEY = (
    rsa.generate_private_key(public_exponent=65537, key_size=2048)
    .private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    .decode()
)


def _loads(pem: str) -> None:
    serialization.load_pem_private_key(pem.encode(), password=None)


def test_valid_key_is_unchanged():
    assert normalize_pem(KEY) == KEY


def test_single_line_with_spaces():
    _loads(normalize_pem(KEY.replace("\n", " ")))


def test_literal_backslash_n_and_invisible_chars():
    pasted = "﻿  " + KEY.replace("\n", "\\n") + "​ "
    assert normalize_pem(pasted) == KEY


def test_body_only():
    body = "".join(KEY.strip().splitlines()[1:-1])
    assert normalize_pem(body) == KEY


def test_rsa_label_is_kept():
    pem = "-----BEGIN RSA PRIVATE KEY----- AAAA BBBB -----END RSA PRIVATE KEY-----"
    assert normalize_pem(pem).startswith("-----BEGIN RSA PRIVATE KEY-----\nAAAABBBB\n")
