"""
core/vault.py
----------------
The Vault class owns all data operations:
- creating / unlocking the encrypted vault file on disk
- adding / updating / deleting saved password entries
- search + simple stats for the dashboard
- exporting / importing an independent encrypted backup file
- changing the master password (re-encrypts everything with a new key)

Storage format for vault.dat / backup files (JSON):
{
    "salt":  base64,
    "nonce": base64,
    "tag":   base64,
    "data":  base64   # AES-256-GCM ciphertext of the JSON entry list
}
"""

import os
import json
import base64
import time
import random

from core.crypto import generate_salt, derive_key, encrypt, decrypt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
VAULT_PATH = os.path.join(DATA_DIR, "vault.dat")

CATEGORIES = ["Website", "Email", "Social Media"]


def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")


def _b64d(s: str) -> bytes:
    return base64.b64decode(s)


class Vault:
    def __init__(self):
        self.key = None
        self.salt = None
        self.entries = []  # list of dicts

    # ---- lifecycle -------------------------------------------------------
    def vault_exists(self) -> bool:
        return os.path.exists(VAULT_PATH)

    def create_new(self, master_password: str):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.salt = generate_salt()
        self.key = derive_key(master_password, self.salt)
        self.entries = []
        self._persist()

    def unlock(self, master_password: str) -> bool:
        if not self.vault_exists():
            return False
        with open(VAULT_PATH, "r") as f:
            raw = json.load(f)
        salt = _b64d(raw["salt"])
        key = derive_key(master_password, salt)
        try:
            plaintext = decrypt(key, _b64d(raw["nonce"]), _b64d(raw["data"]), _b64d(raw["tag"]))
        except ValueError:
            return False
        self.entries = json.loads(plaintext.decode("utf-8"))
        self.key = key
        self.salt = salt
        return True

    def change_master_password(self, new_master_password: str):
        """Re-encrypts the whole vault under a brand new master password/key."""
        self.salt = generate_salt()
        self.key = derive_key(new_master_password, self.salt)
        self._persist()

    def _persist(self):
        payload = json.dumps(self.entries).encode("utf-8")
        nonce, ciphertext, tag = encrypt(self.key, payload)
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(VAULT_PATH, "w") as f:
            json.dump({
                "salt": _b64e(self.salt),
                "nonce": _b64e(nonce),
                "tag": _b64e(tag),
                "data": _b64e(ciphertext),
            }, f)

    # ---- entries -----------------------------------------------------------
    def add_entry(self, category, name, username, password):
        entry = {
            "id": str(int(time.time() * 1000)) + str(random.randint(100, 999)),
            "category": category,
            "name": name,
            "username": username,
            "password": password,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
        }
        self.entries.append(entry)
        self._persist()
        return entry

    def update_entry(self, entry_id, **fields):
        for e in self.entries:
            if e["id"] == entry_id:
                e.update(fields)
        self._persist()

    def delete_entry(self, entry_id):
        self.entries = [e for e in self.entries if e["id"] != entry_id]
        self._persist()

    def search(self, query, category=None):
        query = (query or "").lower()
        results = self.entries
        if category and category != "All":
            results = [e for e in results if e["category"] == category]
        if query:
            results = [e for e in results if query in
                       f"{e['name']} {e.get('username', '')}".lower()]
        return sorted(results, key=lambda e: e["created_at"], reverse=True)

    # ---- stats for the dashboard ---------------------------------------------
    def stats(self):
        counts = {c: 0 for c in CATEGORIES}
        for e in self.entries:
            counts[e["category"]] = counts.get(e["category"], 0) + 1
        recent = sorted(self.entries, key=lambda e: e["created_at"], reverse=True)[:5]
        return {"total": len(self.entries), "counts": counts, "recent": recent}

    # ---- export / import (independent encrypted backup file) -------------------
    def export_to(self, path, export_password):
        salt = generate_salt()
        key = derive_key(export_password, salt)
        payload = json.dumps(self.entries).encode("utf-8")
        nonce, ciphertext, tag = encrypt(key, payload)
        with open(path, "w") as f:
            json.dump({
                "salt": _b64e(salt), "nonce": _b64e(nonce),
                "tag": _b64e(tag), "data": _b64e(ciphertext),
            }, f)

    def import_from(self, path, import_password):
        with open(path, "r") as f:
            raw = json.load(f)
        salt = _b64d(raw["salt"])
        key = derive_key(import_password, salt)
        plaintext = decrypt(key, _b64d(raw["nonce"]), _b64d(raw["data"]), _b64d(raw["tag"]))
        imported = json.loads(plaintext.decode("utf-8"))
        existing_ids = {e["id"] for e in self.entries}
        for e in imported:
            if e["id"] not in existing_ids:
                self.entries.append(e)
        self._persist()
