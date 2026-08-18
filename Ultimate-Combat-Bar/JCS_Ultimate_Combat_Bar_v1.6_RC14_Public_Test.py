"""
J.C.S. Ultimate Combat Bar for TazUO LegionPy
Version 1.6 RC14 Public Test

Compatibility hotfix for RC13.

RC13 used an API.Gumps.* namespace that is not present on current public
Legion builds. Current Legion exposes those gump helpers directly on API
(API.CreateGump, API.AddGump, API.CreateSimpleButton, etc.).

This launcher installs a compatibility proxy and then executes the RC13 core
without changing its combat logic.

IMPORTANT: Keep this file in the same folder as:
    JCS_Ultimate_Combat_Bar_v1.6_RC13_Public_Test.py
"""

import os
import API

VERSION = "1.6-RC14-PUBLIC-TEST"
CORE_FILE = "JCS_Ultimate_Combat_Bar_v1.6_RC13_Public_Test.py"


class _LegionGumpsCompatibility:
    """Forward legacy API.Gumps.X calls to current top-level API.X calls."""

    def __getattr__(self, name):
        try:
            return getattr(API, name)
        except AttributeError:
            raise AttributeError(
                "Legion API does not provide gump function: API.%s" % name
            )


# RC13 references API.Gumps.*.  On current Legion the same functions are
# top-level API members, so provide a compatibility namespace before loading
# the core script.
API.Gumps = _LegionGumpsCompatibility()

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

API.SysMsg("J.C.S. Ultimate Combat Bar RC14 gump compatibility hotfix loaded.", 68)

with open(_core_path, "r") as _core_handle:
    _source = _core_handle.read()

# Execute the tested RC13 core in this script's global namespace.  The only
# behavioral change is the API.Gumps compatibility mapping above.
exec(compile(_source, _core_path, "exec"), globals(), globals())
