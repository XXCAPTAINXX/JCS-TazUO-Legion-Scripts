"""
J.C.S. Ultimate Combat Bar for TazUO LegionPy
Version 1.6 RC14 Public Test

Compatibility hotfix for RC13.

RC13 used an API.Gumps.* namespace that is not present on current public
Legion builds. Current Legion exposes those gump helpers directly on API
(API.CreateGump, API.AddGump, API.CreateSimpleButton, etc.).

This launcher loads the RC13 core, rewrites legacy API.Gumps.* calls to the
current top-level API.* form in memory, and then executes the corrected core.
Combat logic is otherwise unchanged.

IMPORTANT: Keep this file in the same folder as:
    JCS_Ultimate_Combat_Bar_v1.6_RC13_Public_Test.py
"""

import os
import API

VERSION = "1.6-RC14-PUBLIC-TEST"
CORE_FILE = "JCS_Ultimate_Combat_Bar_v1.6_RC13_Public_Test.py"

try:
    _base = os.path.dirname(os.path.abspath(__file__))
except Exception:
    _base = os.getcwd()

_core_path = os.path.join(_base, CORE_FILE)

if not os.path.exists(_core_path):
    raise RuntimeError(
        "RC14 requires %s in the same folder. Download both Combat Bar files."
        % CORE_FILE
    )

with open(_core_path, "r") as _core_handle:
    _source = _core_handle.read()

# Current Legion exposes custom-gump helpers directly on API.  RC13 was built
# against a nested API.Gumps namespace.  Rewrite every legacy reference before
# compilation so this also covers any API.Gumps call outside build_ui.
_source = _source.replace("API.Gumps.", "API.")

API.SysMsg("J.C.S. Ultimate Combat Bar RC14 Legion API hotfix loaded.", 68)

exec(compile(_source, _core_path, "exec"), globals(), globals())
