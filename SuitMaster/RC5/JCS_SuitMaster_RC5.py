# J.C.S. SuitMaster RC5 - PUBLIC BUILD
# Self-contained RC5 package. No RC4 file is required.

import os
import base64
import bz2


def _here():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except:
        return os.getcwd()


base = _here()
payload_dir = os.path.join(base, "RC5_payload")
parts = []
for i in range(4):
    path = os.path.join(payload_dir, "part{:02d}.txt".format(i))
    if not os.path.exists(path):
        raise RuntimeError("SuitMaster RC5 is incomplete. Missing: " + path)
    with open(path, "r") as f:
        parts.append(f.read().strip())

packed = "".join(parts)
source = bz2.decompress(base64.b85decode(packed.encode("ascii"))).decode("utf-8")

if 'VERSION = "RC5"' not in source:
    raise RuntimeError("SuitMaster RC5 payload validation failed.")

exec(compile(source, "JCS_SuitMaster_RC5_full.py", "exec"), globals(), globals())
