"""Keep runtime scratch on the project D: volume. Do not use C:\\Temp."""
from __future__ import print_function

import os


def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def force_project_temp(root=None):
    if root is None:
        root = project_root()
    tmp = os.path.join(root, ".tmp")
    if not os.path.isdir(tmp):
        os.makedirs(tmp)
    os.environ["TEMP"] = tmp
    os.environ["TMP"] = tmp
    os.environ["TMPDIR"] = tmp
    return tmp
