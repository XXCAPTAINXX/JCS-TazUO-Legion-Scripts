# J.C.S. Lootmaster Reforged v1.5-RC1
# Public TazUO / Legion release entrypoint.
#
# The exact RC1 source is stored losslessly in the three adjacent payload
# files. This loader verifies the source checksum before executing it.

import os
import base64
import gzip
import hashlib

_EXPECTED_SIZE = 104208
_EXPECTED_SHA256 = "634d838d985039242c432352a693002c8042cdc09fc2e0e5965c8832e33d8e04"
_PARTS = (
    ".JCS_Lootmaster_Reforged.rc1.001",
    ".JCS_Lootmaster_Reforged.rc1.002",
    ".JCS_Lootmaster_Reforged.rc1.003",
)

try:
    _base = os.path.dirname(os.path.abspath(__file__))
except:
    _base = os.getcwd()

_encoded = ""
for _name in _PARTS:
    _path = os.path.join(_base, _name)
    with open(_path, "r") as _f:
        _encoded += _f.read().strip()

_source = gzip.decompress(base64.b64decode(_encoded))
_actual_sha256 = hashlib.sha256(_source).hexdigest()

if len(_source) != _EXPECTED_SIZE or _actual_sha256 != _EXPECTED_SHA256:
    raise RuntimeError("Lootmaster RC1 payload verification failed.")

exec(compile(_source.decode("utf-8"), os.path.join(_base, "JCS_Lootmaster_Reforged.py"), "exec"), globals(), globals())
