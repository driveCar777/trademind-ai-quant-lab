import hashlib
import os


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_file_hash(path, expected):
    if not os.path.isfile(path):
        return False, None
    actual = sha256_file(path)
    return actual == expected, actual
