"""
J.C.S. SuitMaster RC1 public loader.

Keep this file together with the RC1_payload folder from the SuitMaster
directory. The payload contains the complete 2.2l-RC1 source split into
small text segments for GitHub distribution.
"""

import os
import base64
import zlib

try:
    _base = os.path.dirname(os.path.abspath(__file__))
except Exception:
    _base = os.getcwd()

_payload_dir = os.path.join(_base, "RC1_payload")
_parts = []

for _name in ("part00.txt", "part01.txt", "part02.txt"):
    _path = os.path.join(_payload_dir, _name)
    with open(_path, "r") as _file:
        _parts.append(_file.read().strip())

_source = zlib.decompress(
    base64.b64decode("".join(_parts))
).decode("utf-8")

exec(
    compile(_source, globals().get("__file__", "JCS_SuitMaster_RC1.py"), "exec"),
    globals(),
    globals(),
)
