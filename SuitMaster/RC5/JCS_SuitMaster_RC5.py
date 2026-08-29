# J.C.S. SuitMaster RC5 loader
# Applies the RC5 meditation-safe suit update to the preserved public RC4 source.
import os
import hashlib

RC4_SHA256 = '58a701669f6902701c7d846a2f0aefcd21201b0b7b4b862b51e25cc93f2863a6'
RC5_SHA256 = '83414487314d03f42879894a984053a5950a00d1092095e681ab43bab70691ac'

def _here():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except:
        return os.getcwd()

base = _here()
candidates = [
    os.path.normpath(os.path.join(base, "..", "RC4", "JCS_SuitMaster_RC4.py")),
    os.path.normpath(os.path.join(base, "JCS_SuitMaster_RC4.py")),
]
rc4_path = None
for p in candidates:
    if os.path.exists(p):
        rc4_path = p
        break
if not rc4_path:
    raise RuntimeError("SuitMaster RC5 needs the RC4 source folder beside RC5. Download the complete SuitMaster folder.")
raw = open(rc4_path, "rb").read()
if hashlib.sha256(raw).hexdigest() != RC4_SHA256:
    raise RuntimeError("SuitMaster RC4 source does not match the RC5 base. Re-download the complete SuitMaster folder.")
text = raw.decode("utf-8")
lines = text.splitlines(True)
OPS = [(12, 13, ['# RELEASE CANDIDATE 5 - PUBLIC TEST BUILD\n']), (31, 31, ['#   - RC5: Toggleable Keep Suit Medable profile rule (plain leather or Mage Armor).\n']), (45, 46, ['VERSION = "RC5"\n']), (906, 906, ['\n', 'def item_is_medable(item):\n', '    """Return True when an armor piece is safe for Meditation.\n', '\n', '    Keep Suit Medable is deliberately conservative: normal leather is\n', '    naturally medable, while any armor with Mage Armor is allowed regardless\n', '    of its base material. Unknown body armor is rejected rather than risk\n', '    silently breaking Meditation. Non-armor accessory slots are unaffected.\n', '    """\n', '    if not isinstance(item, dict):\n', '        return True\n', '\n', '    slot = str(item.get("slot", "") or "")\n', '    if slot not in ("Head", "Neck", "Arms", "Hands", "Chest", "Legs"):\n', '        return True\n', '\n', '    text = (str(item.get("name", "")) + "\\n" + str(item.get("opl", ""))).lower()\n', '\n', '    # Mage Armor overrides the normal meditation restriction of the material.\n', '    if "mage armor" in text or "mage armour" in text:\n', '        return True\n', '\n', '    # Plain leather is naturally medable. Studded leather is not.\n', '    if "leather" in text and "studded" not in text:\n', '        return True\n', '\n', '    # Cloth-style headwear can occupy the Head slot and remains medable.\n', '    cloth_head_terms = ("hat", "cap", "hood", "bandana", "skullcap", "wizard\'s hat", "wizard hat")\n', '    if slot == "Head" and any(term in text for term in cloth_head_terms):\n', '        return True\n', '\n', '    # Bone and other normal armor families block Meditation unless Mage Armor\n', '    # was caught above.\n', '    non_medable_terms = (\n', '        "studded", "bone", "platemail", "plate ", "plate armor", "plate armour",\n', '        "ringmail", "chainmail", "dragon armor", "dragon armour", "dragon helm",\n', '        "woodland", "stone armor", "stone armour", "stone helm",\n', '        "gargish stone", "gargoyle stone"\n', '    )\n', '    if any(term in text for term in non_medable_terms):\n', '        return False\n', '\n', '    return False\n', '\n', '\n', 'def filter_medable_items(items):\n', '    return [item for item in items if item_is_medable(item)]\n', '\n']), (1562, 1562, ['        if profile.get("medable", False) and not item_is_medable(item):\n', '            continue\n', '\n']), (1581, 1582, ['        if profile.get("medable", False):\n', '            set_status("Cannot build complete medable suit. Missing valid: " + ", ".join(missing_slots), 33)\n', '        else:\n', '            set_status("Cannot build complete suit. Missing: " + ", ".join(missing_slots), 33)\n']), (3066, 3066, ['        "medable": bool(source.get("medable", False)),\n']), (3263, 3263, ['    base["medable"] = bool(raw.get("medable", base.get("medable", False)))\n']), (3383, 3383, ['        "medable": bool(p.get("medable", False)),\n']), (3560, 3560, ['        "m": 1 if p.get("medable", False) else 0,\n']), (3608, 3608, ['        "medable": bool(payload.get("m", 0)),\n']), (4001, 4002, ['        "Share codes include the COMPLETE profile: mins, targets, priorities, shield/medable rules, skill budget and scan metadata. No item/chest serials.",\n']), (4272, 4272, ['    medable_cb = API.CreateGumpCheckbox("", 0, bool(source.get("medable", False)))\n', '    medable_cb.SetPos(474, 84)\n', '    g.Add(medable_cb)\n', '    add_label(g, "Keep Suit Medable", 500, 84, 155, 22, 12, C_TEXT)\n', '\n']), (4282, 4283, ['    add_label(g, "SECTION", 20, 116, 80, 22, 11, C_GOLD)\n']), (4284, 4285, ['    section_dd.SetPos(100, 112)\n']), (4288, 4289, ['              355, 115, 455, 38, 10, C_MUTED)\n']), (4290, 4296, ['    add_panel(g, 16, 156, 808, 374)\n', '    add_label(g, section_name, 32, 170, 280, 22, 13, C_TITLE)\n', '    add_label(g, "PROPERTY", 32, 200, 300, 20, 11, C_GOLD)\n', '    add_label(g, "MIN", 470, 200, 55, 20, 11, C_GOLD)\n', '    add_label(g, "TARGET", 555, 200, 70, 20, 11, C_GOLD)\n', '    add_label(g, "PRIORITY", 655, 200, 90, 20, 11, C_GOLD)\n']), (4298, 4299, ['    y = 232\n']), (4328, 4328, ['            "medable": bool(source.get("medable", False)),\n']), (4347, 4347, ['            except: pass\n', '        try: data["medable"] = bool(medable_cb.GetIsChecked())\n', '        except:\n', '            try: data["medable"] = bool(medable_cb.IsChecked)\n'])]
for i1, i2, replacement in reversed(OPS):
    lines[i1:i2] = replacement
source = "".join(lines)
if hashlib.sha256(source.encode("utf-8")).hexdigest() != RC5_SHA256:
    raise RuntimeError("SuitMaster RC5 reconstruction failed integrity check.")
exec(compile(source, "JCS_SuitMaster_RC5.py", "exec"), globals(), globals())
