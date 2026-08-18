import API
import re
import json
import os
import time

# ============================================================
# J.C.S. LOOTMASTER REFORGED - PUBLIC RELEASE CANDIDATE 1
# Native TazUO / Legion automated looting system
#
# Author / Maintainer: XXCAPTAINXX
#
# CREDIT:
#   Lootmaster Reforged was built in homage to the original Lootmaster.
#   The original Lootmaster established the rule-driven looting model that
#   inspired this Legion-native rebuild, including ordered rules, property
#   matching, destination bags, starter presets, rarity filtering and more.
#
#   Reforged is a new Python/Legion implementation and is not the original
#   Lootmaster codebase.
#
# PLATFORM:
#   TazUO Legion Scripting Engine. This is NOT a Razor Enhanced script.
#
# PUBLIC RELEASE NOTES:
#   - Settings persist in JCS_Lootmaster_Settings.json.
#   - First-run safety keeps auto-loot off until a default bag is configured.
#   - Loot speed profiles: Fast / Balanced / Safe.
#   - Automatically pauses while the player is dead.
#   - Automatically skips corpses the player has no right to loot.
#   - Corpse display: Normal / Color / Hide.
#   - Integrated treasure-chest lockpick / Remove Trap / loot workflow.
#
# ============================================================

VERSION = "1.5-RC1" 

LOOT_RANGE = 2
CORPSE_OPEN_DELAY = 0.18
MOVE_DELAY = 0.12
LOOP_DELAY = 0.05
OPL_TIMEOUT = 1
IGNORE_AFTER_LOOT = True
MOVE_CONFIRM_TIMEOUT = 0.80
OPL_BATCH_PAUSE = 0.05
POST_MOVE_PAUSE = 0.05
STABLE_SCAN_PAUSE = 0.07

# Integrated treasure-chest handler.
LOCKPICK_GRAPHIC = 5372
SUCCESS_LOCKPICKING = [
    "The lock quickly yields",
    "This does not appear to be locked",
]
SUCCESS_REMOVE_TRAP = [
    "You successfully render the trap",
    "That doesn't appear to be trapped",
]

KEY_RULES = "JCS_Lootmaster_RulesV2"
KEY_AUTO = "JCS_Lootmaster_AutoLoot"
KEY_DEFAULT_BAG = "JCS_Lootmaster_DefaultBag"
KEY_COMPACT = "JCS_Lootmaster_CompactMode"
KEY_MAIN_X = "JCS_Lootmaster_MainX"
KEY_MAIN_Y = "JCS_Lootmaster_MainY"
KEY_EDITOR_X = "JCS_Lootmaster_EditorX"
KEY_EDITOR_Y = "JCS_Lootmaster_EditorY"
KEY_MARK_CORPSES = "JCS_Lootmaster_MarkCorpses"
KEY_MARK_HUE = "JCS_Lootmaster_MarkCorpseHue"
KEY_CORPSE_DISPLAY = "JCS_Lootmaster_CorpseDisplayMode"
KEY_LOOT_SPEED = "JCS_Lootmaster_LootSpeed"

# Stable local backup/import file.  The filename does not include the
# Lootmaster version, so v2.5/v3.0/etc. can reuse the same settings.
SETTINGS_FILE = "JCS_Lootmaster_Settings.json"
SETTINGS_FORMAT_VERSION = 1

C_BG = "#1D1A17"
C_PANEL = "#29231D"
C_TITLE = "#D2691E"
C_TEXT = "#E7E1D8"
C_MUTED = "#A49B90"
C_GREEN = "#65C466"
C_RED = "#E2675D"
C_GOLD = "#D7AA45"

CORPSE_MARKER_OPTIONS = [
    ("TazUO Looted", 73),
    ("Hue 32", 32),
    ("Hue 53", 53),
    ("Hue 68", 68),
    ("Hue 88", 88),
    ("Hue 1153", 1153),
    ("Hue 1175", 1175),
    ("Custom", None),
]
CORPSE_MARKER_LABELS = [x[0] for x in CORPSE_MARKER_OPTIONS]
CORPSE_DISPLAY_OPTIONS = ["Normal", "Color", "Hide"]

LOOT_SPEED_OPTIONS = ["Fast", "Balanced", "Safe"]
LOOT_SPEED_PROFILES = {
    "Fast": {
        "corpse_open": 0.18,
        "loop": 0.05,
        "opl_timeout": 1,
        "move_confirm": 0.80,
        "opl_batch_pause": 0.05,
        "post_move_pause": 0.05,
        "stable_pause": 0.07,
    },
    "Balanced": {
        "corpse_open": 0.28,
        "loop": 0.08,
        "opl_timeout": 2,
        "move_confirm": 1.20,
        "opl_batch_pause": 0.10,
        "post_move_pause": 0.10,
        "stable_pause": 0.12,
    },
    "Safe": {
        "corpse_open": 0.40,
        "loop": 0.12,
        "opl_timeout": 3,
        "move_confirm": 1.60,
        "opl_batch_pause": 0.16,
        "post_move_pause": 0.15,
        "stable_pause": 0.20,
    },
}

NO_LOOT_MESSAGES = [
    "you may not loot this corpse",
    "you did not earn the right to loot this creature",
    "you did not earn the right to loot",
]


DEFAULT_RULES = [
    {"id":"gold","name":"Gold / Coin Purses","enabled":True,
     "name_any":["gold","coin purse"],"graphics":[0x0EED,41777],"bag":0},
    {"id":"gems","name":"Gems","enabled":True,
     "name_any":["amber","amethyst","citrine","diamond","emerald","ruby",
                 "sapphire","star sapphire","tourmaline","gem"],"bag":0},
    {"id":"slayers","name":"Slayer Weapons","enabled":True,
     "regex":r"(?im)(^|\n).*slayer.*($|\n)|(^|\n)\s*silver\s*($|\n)","bag":0},
    {"id":"pure_elemental_broadsword","name":"100% Elem Broadswords","enabled":True,
     "name_any":["broadsword"],
     "regex":r"(?im)^\s*(fire|cold|poison|energy)\s+damage(?:\s*[:+]?\s*)100\s*%?\s*$","bag":0},
    {"id":"whips","name":"Whips","enabled":True,"name_any":["whip"],"bag":0},
    {"id":"pure_elemental","name":"100% Elemental Weapons","enabled":False,
     "regex":r"(?im)^\s*(fire|cold|poison|energy)\s+damage(?:\s*[:+]?\s*)100\s*%?\s*$","bag":0},
    {"id":"artifacts","name":"Artifacts / Legendary","enabled":True,
     "opl_any":["legendary artifact","major artifact","greater artifact",
                "lesser artifact","minor artifact","legendary magic item"],"bag":0},
    {"id":"maps","name":"Treasure Maps","enabled":True,
     "opl_any":["treasure map"],"bag":0},
]


# Friendly dropdown-driven property builder.
PROPERTY_OPTIONS = [
    "Any Slayer", "Any Element",
    "Dragon Slayer", "Poison Elemental Slayer", "Demon Slayer",
    "Repond Slayer", "Reptile Slayer", "Arachnid Slayer",
    "Undead Slayer", "Silver",
    "Luck", "Damage Increase", "Hit Chance Increase",
    "Defense Chance Increase", "Swing Speed Increase",
    "Faster Casting", "Faster Cast Recovery", "Spell Damage Increase",
    "Lower Mana Cost", "Lower Reagent Cost", "Mana Regeneration",
    "Hit Mana Leech", "Hit Life Leech", "Hit Stamina Leech",
    "Hit Lower Attack", "Hit Lower Defense", "Hit Fireball",
    "Hit Lightning", "Hit Harm", "Hit Magic Arrow", "Hit Dispel",
    "Fire Damage", "Cold Damage", "Poison Damage", "Energy Damage",
    "Physical Damage", "Fire Resist", "Cold Resist", "Poison Resist",
    "Energy Resist", "Physical Resist", "Strength Bonus", "Dexterity Bonus",
    "Intelligence Bonus", "Hit Point Increase", "Stamina Increase",
    "Mana Increase", "Hit Point Regeneration", "Stamina Regeneration",
    "Enhance Potions", "Reflect Physical Damage", "Damage Eater",
    "Fire Eater", "Cold Eater", "Poison Eater", "Energy Eater",
    "Kinetic Eater", "Casting Focus", "Velocity", "Balanced",
    "Mage Weapon", "Use Best Weapon Skill", "Spell Channeling",
    "Cursed", "Antique", "Brittle", "Prized",
    "Animal Taming",
    "Animal Lore",
    "Veterinary",
    "Necromancy",
    "Chivalry",
    "Swords",
    "Tactics",
]

OPERATOR_OPTIONS = ["Exists", "At least", "Equals", "Under"]

# Presets from the original Lootmaster.cs are listed first.
# Enhanced Legion presets follow them.
PRESET_OPTIONS = [
    "None",

    # ---- Original Lootmaster presets ----
    "Gold",
    "Gems",
    "Imbue Materials",
    "Bolts and Arrows",
    "Pure Elemental Weapons",
    "Pure Cold Weapon",
    "Pure Fire Weapon",
    "Pure Energy Weapon",
    "Pure Poison Weapon",
    "Slayers",
    "Reagents Magery",
    "Reagents Necromancy",
    "Reagents Mysticism",
    "Reagents",

    # ---- Legion enhanced presets ----
    "Legendary+",
    "Legendary Armor",
    "Legendary Jewelry",
    "Legendary Weapon",
    "Treasure Map",
    "Valuable Weapon",
    "Caster Jewelry",

    # ---- Build-style starter presets ----
    "Mage Jewelry - Flexible",
    "Mage Armor - Flexible",
    "Dexxer Weapon - Flexible",
    "Dexxer Armor - Flexible",
    "Sampire Weapon - Flexible",
    "Sampire Armor - Flexible",
    "Luck Armor",
    "Luck Jewelry",
    "Blood Knight/Tamer Armor",
    "Blood Knight/Tamer Jewelry",
    "Blood Knight/Tamer Weapon",
    "Blood Knight/Tamer Skill Gear",
]

# Exact graphics used by the original Lootmaster presets.
ORIGINAL_GOLD_GRAPHICS = [3821, 41777]

ORIGINAL_GEM_GRAPHICS = [
    3855, 3859, 3856, 3857, 3861, 3862, 3864, 3877, 3878,
    41779,  # Gem Bag
]

ORIGINAL_MAGERY_REAGENT_GRAPHICS = [
    3962, 3963, 3972, 3973, 3974, 3976, 3560, 3980,
]

ORIGINAL_NECRO_REAGENT_GRAPHICS = [
    3960, 3981, 3965, 3982, 3983,
]

ORIGINAL_MYSTIC_REAGENT_GRAPHICS = [
    16503, 3966, 3968, 3969,
]

ORIGINAL_AMMO_GRAPHICS = [3903, 7163]

ORIGINAL_IMBUE_MATERIAL_GRAPHICS = [
    22332, 12696, 22344, 22338, 22339, 22331, 22328, 22322,
    22049, 22330, 22327, 22341, 22310, 12695, 22316, 22317,
    12689, 12688, 22343, 22345, 22326, 22340, 22342, 22304,
    12691, 22321, 22306, 22334, 12694,
]

# Essence has one graphic with several exact hues in the original.
ORIGINAL_ESSENCE_GRAPHIC = 22300
ORIGINAL_ESSENCE_HUES = [
    0x048E, 0x04F4, 0x01C7, 0x0025, 0x0455, 0x0486,
    0x048D, 0x06BC, 0x0489, 0x0481,
]

PROPERTY_MATCH_OPTIONS = ["All properties", "Any property", "At least count"]

RARITY_OPTIONS = [
    "Any",
    "Minor Magic Item",
    "Lesser Magic Item",
    "Greater Magic Item",
    "Major Magic Item",
    "Minor Artifact",
    "Lesser Artifact",
    "Greater Artifact",
    "Major Artifact",
    "Legendary Artifact",
]

EQUIPMENT_OPTIONS = [
    "Any",
    "Any Armor",
    "Any Jewelry",
    "Any Weapon",
    "Any Shield",
    "Ring",
    "Bracelet",
    "Earrings",
    "RightHand",
    "LeftHand",
    "Head",
    "Gloves",
    "Neck",
    "Arms",
    "OuterTorso",
    "MiddleTorso",
    "InnerTorso",
    "OuterLegs",
    "InnerLegs",
    "Pants",
    "Shoes",
]

BLACKLIST_OPTIONS = [
    "Cursed", "Antique", "Brittle", "Prized",
    "Mage Weapon", "Spell Channeling", "Use Best Weapon Skill",
]

def property_display(c):
    prop = str(c.get("property",""))
    op = str(c.get("operator","Exists"))
    val = c.get("value",None)

    friendly = {
        ">=": "At least",
        "=": "Equals",
        "<=": "Under",
        "At least": "At least",
        "Equals": "Equals",
        "Under": "Under",
        "Exists": "Exists",
    }
    shown = friendly.get(op, op)

    if shown == "Exists" or val is None:
        return prop

    return "{} {} {}".format(prop, shown, val)

def parse_property_number(opl, prop):
    pattern = r"(?im)^\s*" + re.escape(prop) + r"\s*(?:[:+]?\s*)?([-+]?\d+)\s*%?\s*$"
    m = re.search(pattern, opl or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except:
        return None

def property_exists(opl, prop):
    p = prop.lower()
    text = (opl or "").lower()

    if p == "any slayer":
        return bool(re.search(
            r"(?im)(^|\n).*slayer.*($|\n)|(^|\n)\s*silver\s*($|\n)",
            opl or ""
        ))

    if p == "any element":
        return any(
            parse_property_number(opl, x) is not None
            for x in ("Fire Damage","Cold Damage","Poison Damage","Energy Damage")
        )

    return p in text

def compare_number(actual, op, expected):
    if actual is None:
        return False

    if op in (">=", "At least"):
        return actual >= expected

    if op in ("<=", "Under"):
        return actual <= expected

    if op in ("=", "Equals"):
        return actual == expected

    return True

def matches_property_condition(opl, cond):
    prop = str(cond.get("property","")).strip()
    op = str(cond.get("operator","Exists"))
    val = cond.get("value",None)

    if not prop:
        return True

    if prop == "Any Slayer":
        return property_exists(opl,prop)

    if prop == "Any Element":
        if op == "Exists" or val is None:
            return property_exists(opl,prop)
        try:
            expected = int(val)
        except:
            return False
        for elem in ("Fire Damage","Cold Damage","Poison Damage","Energy Damage"):
            if compare_number(parse_property_number(opl,elem),op,expected):
                return True
        return False

    if op == "Exists" or val is None:
        return property_exists(opl,prop)

    try:
        expected = int(val)
    except:
        return False

    return compare_number(parse_property_number(opl,prop),op,expected)

def apply_preset(name,state):
    # Clear exact hidden data left by a previously selected preset.
    state["preset_rule_data"] = {}

    # =========================================================
    # ORIGINAL LOOTMASTER PRESETS
    # =========================================================
    if name == "Gold":
        state["preset_rule_data"] = {
            "graphics": list(ORIGINAL_GOLD_GRAPHICS),
        }

    elif name == "Gems":
        state["preset_rule_data"] = {
            "graphics": list(ORIGINAL_GEM_GRAPHICS),
        }

    elif name == "Imbue Materials":
        # Original Lootmaster requires hue 0 for normal materials and
        # specific hues for Essence. Represent those exact combinations.
        pairs = [
            {"graphic": g, "hue": 0}
            for g in ORIGINAL_IMBUE_MATERIAL_GRAPHICS
        ]
        pairs.extend(
            {"graphic": ORIGINAL_ESSENCE_GRAPHIC, "hue": h}
            for h in ORIGINAL_ESSENCE_HUES
        )
        state["preset_rule_data"] = {
            "graphic_hue_pairs": pairs,
        }

    elif name == "Bolts and Arrows":
        state["preset_rule_data"] = {
            "graphics": list(ORIGINAL_AMMO_GRAPHICS),
        }

    elif name == "Pure Elemental Weapons":
        state["conditions"] = [
            {"property":"Any Element","operator":"Equals","value":100}
        ]

    elif name == "Pure Cold Weapon":
        state["conditions"] = [
            {"property":"Cold Damage","operator":"Equals","value":100}
        ]

    elif name == "Pure Fire Weapon":
        state["conditions"] = [
            {"property":"Fire Damage","operator":"Equals","value":100}
        ]

    elif name == "Pure Energy Weapon":
        state["conditions"] = [
            {"property":"Energy Damage","operator":"Equals","value":100}
        ]

    elif name == "Pure Poison Weapon":
        state["conditions"] = [
            {"property":"Poison Damage","operator":"Equals","value":100}
        ]

    elif name == "Slayers":
        state["conditions"] = [
            {"property":"Any Slayer","operator":"Exists","value":None}
        ]

    elif name == "Reagents Magery":
        state["preset_rule_data"] = {
            "graphics": list(ORIGINAL_MAGERY_REAGENT_GRAPHICS),
        }

    elif name == "Reagents Necromancy":
        state["preset_rule_data"] = {
            "graphics": list(ORIGINAL_NECRO_REAGENT_GRAPHICS),
        }

    elif name == "Reagents Mysticism":
        state["preset_rule_data"] = {
            "graphics": list(ORIGINAL_MYSTIC_REAGENT_GRAPHICS),
        }

    elif name == "Reagents":
        all_reagents = sorted(set(
            ORIGINAL_MAGERY_REAGENT_GRAPHICS
            + ORIGINAL_NECRO_REAGENT_GRAPHICS
            + ORIGINAL_MYSTIC_REAGENT_GRAPHICS
        ))
        state["preset_rule_data"] = {
            "graphics": all_reagents,
        }

    # =========================================================
    # LEGION ENHANCED PRESETS
    # =========================================================
    elif name == "Legendary+":
        state["minimum_rarity"]="Legendary Artifact"

    elif name == "Legendary Armor":
        state["equipment_type"]="Any Armor"
        state["minimum_rarity"]="Legendary Artifact"

    elif name == "Legendary Jewelry":
        state["equipment_type"]="Any Jewelry"
        state["minimum_rarity"]="Legendary Artifact"

    elif name == "Legendary Weapon":
        state["equipment_type"]="Any Weapon"
        state["minimum_rarity"]="Legendary Artifact"

    elif name == "Treasure Map":
        state["opl_any"]=["treasure map"]

    elif name == "Valuable Weapon":
        state["equipment_type"]="Any Weapon"
        state["conditions"]=[
            {"property":"Hit Chance Increase","operator":"At least","value":15},
            {"property":"Damage Increase","operator":"At least","value":30},
            {"property":"Swing Speed Increase","operator":"At least","value":10},
        ]

    elif name == "Caster Jewelry":
        state["equipment_type"]="Any Jewelry"
        state["conditions"]=[
            {"property":"Spell Damage Increase","operator":"At least","value":18},
            {"property":"Lower Reagent Cost","operator":"At least","value":20},
            {"property":"Faster Casting","operator":"At least","value":1},
            {"property":"Faster Cast Recovery","operator":"At least","value":2},
        ]
        state["property_match_mode"]="ALL"
        state["property_match_count"]=4

    elif name == "Mage Jewelry - Flexible":
        state["equipment_type"]="Any Jewelry"
        state["conditions"]=[
            {"property":"Faster Casting","operator":"At least","value":1},
            {"property":"Faster Cast Recovery","operator":"At least","value":2},
            {"property":"Spell Damage Increase","operator":"At least","value":12},
            {"property":"Lower Mana Cost","operator":"At least","value":6},
            {"property":"Lower Reagent Cost","operator":"At least","value":15},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Mage Armor - Flexible":
        state["equipment_type"]="Any Armor"
        state["conditions"]=[
            {"property":"Lower Mana Cost","operator":"At least","value":6},
            {"property":"Mana Regeneration","operator":"At least","value":2},
            {"property":"Lower Reagent Cost","operator":"At least","value":15},
            {"property":"Defense Chance Increase","operator":"At least","value":10},
            {"property":"Mana Increase","operator":"At least","value":5},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Dexxer Weapon - Flexible":
        state["equipment_type"]="Any Weapon"
        state["conditions"]=[
            {"property":"Hit Chance Increase","operator":"At least","value":15},
            {"property":"Damage Increase","operator":"At least","value":30},
            {"property":"Swing Speed Increase","operator":"At least","value":20},
            {"property":"Hit Mana Leech","operator":"At least","value":30},
            {"property":"Hit Lower Defense","operator":"At least","value":30},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Dexxer Armor - Flexible":
        state["equipment_type"]="Any Armor"
        state["conditions"]=[
            {"property":"Hit Chance Increase","operator":"At least","value":5},
            {"property":"Defense Chance Increase","operator":"At least","value":10},
            {"property":"Lower Mana Cost","operator":"At least","value":6},
            {"property":"Stamina Increase","operator":"At least","value":5},
            {"property":"Hit Point Increase","operator":"At least","value":5},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Sampire Weapon - Flexible":
        state["equipment_type"]="Any Weapon"
        state["conditions"]=[
            {"property":"Hit Mana Leech","operator":"At least","value":40},
            {"property":"Hit Life Leech","operator":"At least","value":40},
            {"property":"Swing Speed Increase","operator":"At least","value":20},
            {"property":"Hit Lower Defense","operator":"At least","value":30},
            {"property":"Damage Increase","operator":"At least","value":40},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Sampire Armor - Flexible":
        state["equipment_type"]="Any Armor"
        state["conditions"]=[
            {"property":"Lower Mana Cost","operator":"At least","value":6},
            {"property":"Stamina Increase","operator":"At least","value":5},
            {"property":"Hit Chance Increase","operator":"At least","value":5},
            {"property":"Defense Chance Increase","operator":"At least","value":10},
            {"property":"Mana Increase","operator":"At least","value":5},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Luck Armor":
        state["equipment_type"]="Any Armor"
        state["conditions"]=[
            {"property":"Luck","operator":"At least","value":100},
        ]
        state["property_match_mode"]="ALL"
        state["property_match_count"]=1

    elif name == "Luck Jewelry":
        state["equipment_type"]="Any Jewelry"
        state["conditions"]=[
            {"property":"Luck","operator":"At least","value":100},
        ]
        state["property_match_mode"]="ALL"
        state["property_match_count"]=1

    elif name == "Blood Knight/Tamer Armor":
        state["equipment_type"]="Any Armor"
        state["conditions"]=[
            {"property":"Lower Mana Cost","operator":"At least","value":6},
            {"property":"Stamina Increase","operator":"At least","value":5},
            {"property":"Hit Point Increase","operator":"At least","value":5},
            {"property":"Mana Increase","operator":"At least","value":5},
            {"property":"Defense Chance Increase","operator":"At least","value":10},
            {"property":"Mana Regeneration","operator":"At least","value":2},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Blood Knight/Tamer Jewelry":
        state["equipment_type"]="Any Jewelry"
        state["conditions"]=[
            {"property":"Hit Chance Increase","operator":"At least","value":10},
            {"property":"Defense Chance Increase","operator":"At least","value":10},
            {"property":"Lower Mana Cost","operator":"At least","value":6},
            {"property":"Faster Cast Recovery","operator":"At least","value":2},
            {"property":"Faster Casting","operator":"At least","value":1},
            {"property":"Luck","operator":"At least","value":100},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Blood Knight/Tamer Weapon":
        state["equipment_type"]="Any Weapon"
        state["conditions"]=[
            {"property":"Hit Mana Leech","operator":"At least","value":40},
            {"property":"Hit Life Leech","operator":"At least","value":40},
            {"property":"Swing Speed Increase","operator":"At least","value":20},
            {"property":"Damage Increase","operator":"At least","value":40},
            {"property":"Hit Lower Defense","operator":"At least","value":30},
            {"property":"Hit Chance Increase","operator":"At least","value":10},
        ]
        state["property_match_mode"]="COUNT"
        state["property_match_count"]=3

    elif name == "Blood Knight/Tamer Skill Gear":
        # Skill-bonus gear for this exact template:
        # Swords, Taming/Lore, Necro, Vet, Tactics, Chivalry.
        state["equipment_type"]="Any"
        state["conditions"]=[
            {"property":"Animal Taming","operator":"At least","value":10},
            {"property":"Animal Lore","operator":"At least","value":10},
            {"property":"Veterinary","operator":"At least","value":10},
            {"property":"Necromancy","operator":"At least","value":10},
            {"property":"Chivalry","operator":"At least","value":10},
            {"property":"Swords","operator":"At least","value":10},
            {"property":"Tactics","operator":"At least","value":10},
        ]
        state["property_match_mode"]="ANY"
        state["property_match_count"]=1


RULES = []
_main_gump = None
_editor_gump = None
_status_label = None
_auto_loot = True
_paused = False
_stop_requested = False
_processed_corpses = set()
_default_bag = 0
_compact_mode = False
_mark_corpses = True
_mark_corpse_hue = 73
_corpse_display_mode = "Color"
_loot_speed = "Fast"
_starter_reset_armed_until = 0.0
_colored_corpses = {}  # serial -> original hue

# Main rule-list viewport. The main gump no longer grows with every rule.
RULES_PER_PAGE = 8
_rule_page = 0


# ============================================================
# Persistence
# ============================================================

def pget(name, default=""):
    try:
        return API.GetPersistentVar(name, str(default), API.PersistentVar.Char)
    except:
        return str(default)

def pset(name, value):
    try:
        API.SavePersistentVar(name, str(value), API.PersistentVar.Char)
    except:
        pass

def load_bool(name, default):
    return str(pget(name, "1" if default else "0")).lower() in ("1","true","yes","on")

def sanitize_rule(r):
    out = {
        "id": str(r.get("id","")),
        "name": str(r.get("name","Unnamed Rule")),
        "enabled": bool(r.get("enabled",True)),
        "bag": int(r.get("bag",0) or 0),
    }
    for key in ("name_any","name_all","opl_any","opl_all","reject_any"):
        if isinstance(r.get(key), list):
            vals = [str(x).strip() for x in r[key] if str(x).strip()]
            if vals:
                out[key] = vals
    if r.get("regex"):
        out["regex"] = str(r["regex"])
    if isinstance(r.get("property_conditions"), list):
        conditions=[]
        for c in r.get("property_conditions",[]):
            if not isinstance(c,dict):
                continue
            prop=str(c.get("property","")).strip()
            if not prop:
                continue
            op=str(c.get("operator","Exists"))
            # Normalize old symbolic operators into friendly text.
            op = {
                ">=": "At least",
                "=": "Equals",
                "<=": "Under",
            }.get(op, op)
            val=c.get("value",None)
            if val is not None:
                try: val=int(val)
                except: val=None
            conditions.append({"property":prop,"operator":op,"value":val})
        if conditions:
            out["property_conditions"]=conditions
    mode = str(r.get("property_match_mode", "ALL")).upper()
    if mode not in ("ALL", "ANY", "COUNT"):
        mode = "ALL"
    out["property_match_mode"] = mode
    try:
        out["property_match_count"] = max(1, int(r.get("property_match_count", 1) or 1))
    except:
        out["property_match_count"] = 1

    if isinstance(r.get("blacklist_properties"), list):
        vals=[str(x).strip() for x in r.get("blacklist_properties",[]) if str(x).strip()]
        if vals:
            out["blacklist_properties"] = vals

    if r.get("minimum_rarity"):
        out["minimum_rarity"] = str(r.get("minimum_rarity"))
    if r.get("maximum_rarity"):
        out["maximum_rarity"] = str(r.get("maximum_rarity"))
    if r.get("equipment_type") and str(r.get("equipment_type")) != "Any":
        out["equipment_type"] = str(r.get("equipment_type"))
    out["alert"] = bool(r.get("alert", False))

    for key in ("graphic","hue"):
        if r.get(key) is not None:
            try: out[key] = int(r[key])
            except: pass
    for key in ("graphics","hues"):
        if isinstance(r.get(key), list):
            try: out[key] = [int(x) for x in r[key]]
            except: pass

    if isinstance(r.get("graphic_hue_pairs"), list):
        pairs=[]
        for pair in r.get("graphic_hue_pairs",[]):
            try:
                if isinstance(pair, dict):
                    pairs.append({
                        "graphic": int(pair.get("graphic")),
                        "hue": int(pair.get("hue")),
                    })
                elif isinstance(pair, (list, tuple)) and len(pair) >= 2:
                    pairs.append({
                        "graphic": int(pair[0]),
                        "hue": int(pair[1]),
                    })
            except:
                pass
        if pairs:
            out["graphic_hue_pairs"] = pairs

    return out

def save_rules():
    pset(KEY_RULES, json.dumps([sanitize_rule(r) for r in RULES]))
    autosave_settings()

def repair_known_rule_regexes(rules):
    for r in rules:
        rid = r.get("id", "")
        if rid == "slayers":
            r["regex"] = r"(?im)(^|\n).*slayer.*($|\n)|(^|\n)\s*silver\s*($|\n)"
        elif rid in ("pure_elemental", "pure_elemental_broadsword"):
            r["regex"] = (
                r"(?im)^\s*(fire|cold|poison|energy)\s+damage"
                r"(?:\s*[:+]?\s*)100\s*%?\s*$"
            )
    return rules


def load_rules():
    global RULES
    raw = pget(KEY_RULES, "")
    if raw:
        try:
            arr = json.loads(raw)
            if isinstance(arr, list) and arr:
                RULES = repair_known_rule_regexes([sanitize_rule(r) for r in arr])
                save_rules()
                return
        except:
            pass
    RULES = repair_known_rule_regexes([sanitize_rule(r) for r in DEFAULT_RULES])
    save_rules()



# ============================================================
# Portable local settings file
# ============================================================

def settings_path():
    """
    Keep the settings file independent of the script revision.
    Prefer the current script directory when Python exposes __file__.
    """
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        if base:
            return os.path.join(base, SETTINGS_FILE)
    except:
        pass
    return SETTINGS_FILE


def build_settings_payload():
    return {
        "format_version": SETTINGS_FORMAT_VERSION,
        "lootmaster_version": VERSION,
        "rules": [sanitize_rule(r) for r in RULES],
        "default_bag": int(_default_bag or 0),
        "auto_loot": bool(_auto_loot),
        "compact_mode": bool(_compact_mode),
        "mark_corpses": bool(_mark_corpses),
        "mark_corpse_hue": int(_mark_corpse_hue),
        "corpse_display_mode": str(_corpse_display_mode),
        "loot_speed": str(_loot_speed),
    }


def export_settings(silent=False):
    """
    Write all user configuration to one portable JSON file.
    """
    try:
        path = settings_path()
        payload = build_settings_payload()

        with open(path, "w") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

        if not silent:
            set_status("Settings exported: " + path)
            API.SysMsg("Lootmaster settings exported.", 68)

        return True

    except Exception as e:
        if not silent:
            API.SysMsg("Settings export failed: " + str(e), 33)
        return False


def import_settings(silent=False):
    """
    Import all configuration from the portable JSON file.
    Existing settings are replaced only after the file validates.
    """
    global RULES, _default_bag, _auto_loot, _compact_mode, _mark_corpses, _mark_corpse_hue, _corpse_display_mode, _loot_speed

    path = settings_path()

    if not os.path.exists(path):
        if not silent:
            API.SysMsg("Settings file not found: " + path, 33)
        return False

    try:
        with open(path, "r") as f:
            payload = json.load(f)

        if not isinstance(payload, dict):
            raise Exception("Settings root is not an object.")

        incoming_rules = payload.get("rules")
        if not isinstance(incoming_rules, list):
            raise Exception("Settings file does not contain a rules list.")

        clean_rules = repair_known_rule_regexes(
            [sanitize_rule(r) for r in incoming_rules if isinstance(r, dict)]
        )
        if not clean_rules:
            raise Exception("Settings file contains no valid rules.")

        # Validation succeeded. Apply everything.
        RULES = clean_rules

        try:
            _default_bag = int(payload.get("default_bag", 0) or 0)
        except:
            _default_bag = 0

        _auto_loot = bool(payload.get("auto_loot", True))
        _compact_mode = bool(payload.get("compact_mode", False))
        _mark_corpses = bool(payload.get("mark_corpses", True))
        try:
            _mark_corpse_hue = int(payload.get("mark_corpse_hue", 73) or 73)
        except:
            _mark_corpse_hue = 73

        incoming_mode=str(payload.get("corpse_display_mode","Color") or "Color").title()
        _corpse_display_mode=incoming_mode if incoming_mode in CORPSE_DISPLAY_OPTIONS else "Color"
        if not _mark_corpses and "corpse_display_mode" not in payload:
            _corpse_display_mode="Normal"

        incoming_speed=str(payload.get("loot_speed","Fast") or "Fast").title()
        _loot_speed=incoming_speed if incoming_speed in LOOT_SPEED_OPTIONS else "Fast"
        apply_loot_speed(_loot_speed, False)

        # Mirror imported values back into Legion persistent storage.
        pset(KEY_RULES, json.dumps([sanitize_rule(r) for r in RULES]))
        pset(KEY_DEFAULT_BAG, str(_default_bag))
        pset(KEY_AUTO, "1" if _auto_loot else "0")
        pset(KEY_COMPACT, "1" if _compact_mode else "0")
        pset(KEY_MARK_CORPSES, "1" if _mark_corpses else "0")
        pset(KEY_MARK_HUE, str(_mark_corpse_hue))
        pset(KEY_CORPSE_DISPLAY, _corpse_display_mode)
        pset(KEY_LOOT_SPEED, _loot_speed)

        if not silent:
            refresh_main()
            set_status("Settings imported from " + path)
            API.SysMsg("Lootmaster settings imported.", 68)

        return True

    except Exception as e:
        if not silent:
            API.SysMsg("Settings import failed: " + str(e), 33)
        return False


def autosave_settings():
    """
    Best-effort portable backup. Never interrupt looting if disk I/O fails.
    """
    try:
        export_settings(True)
    except:
        pass


def apply_loot_speed(name, save=True):
    global _loot_speed
    global CORPSE_OPEN_DELAY, LOOP_DELAY, OPL_TIMEOUT
    global MOVE_CONFIRM_TIMEOUT, OPL_BATCH_PAUSE
    global POST_MOVE_PAUSE, STABLE_SCAN_PAUSE

    name=str(name or "Fast").title()
    if name not in LOOT_SPEED_PROFILES:
        name="Fast"

    p=LOOT_SPEED_PROFILES[name]
    _loot_speed=name
    CORPSE_OPEN_DELAY=float(p["corpse_open"])
    LOOP_DELAY=float(p["loop"])
    OPL_TIMEOUT=int(p["opl_timeout"])
    MOVE_CONFIRM_TIMEOUT=float(p["move_confirm"])
    OPL_BATCH_PAUSE=float(p["opl_batch_pause"])
    POST_MOVE_PAUSE=float(p["post_move_pause"])
    STABLE_SCAN_PAUSE=float(p["stable_pause"])

    if save:
        pset(KEY_LOOT_SPEED,_loot_speed)
        autosave_settings()
        set_status("Loot speed: "+_loot_speed)


def cycle_loot_speed():
    try:
        idx=LOOT_SPEED_OPTIONS.index(_loot_speed)
    except:
        idx=0
    apply_loot_speed(LOOT_SPEED_OPTIONS[(idx+1)%len(LOOT_SPEED_OPTIONS)])
    refresh_main()


def player_is_dead():
    try:
        return bool(API.Player.IsDead)
    except:
        return False


def journal_says_no_loot():
    try:
        return bool(API.InJournalAny(NO_LOOT_MESSAGES, True))
    except:
        try:
            return bool(API.InJournalAny(NO_LOOT_MESSAGES))
        except:
            return False


def reset_to_starter_rules():
    """
    Two-click confirmation to avoid accidentally destroying custom rules.
    First click arms reset for 8 seconds; second click performs it.
    """
    global RULES, _starter_reset_armed_until, _rule_page

    now=time.time()
    if now > _starter_reset_armed_until:
        _starter_reset_armed_until=now+8.0
        set_status("STARTER RESET ARMED - click STARTER again within 8 seconds.")
        API.SysMsg("Lootmaster: click STARTER again to confirm rule reset.",33)
        return

    RULES=[sanitize_rule(dict(r)) for r in DEFAULT_RULES]
    RULES=repair_known_rule_regexes(RULES)
    _rule_page=0
    _starter_reset_armed_until=0.0
    save_rules()
    autosave_settings()
    set_status("Starter rules restored. Default bag was kept.")
    API.SysMsg("Lootmaster starter rules restored.",68)
    refresh_main()


# ============================================================
# Item helpers
# ============================================================

def serial(obj):
    try: return int(obj.Serial)
    except:
        try: return int(obj)
        except: return 0

def find_item(s):
    try: return API.FindItem(int(s))
    except: return None

def graphic(item):
    for a in ("Graphic","ItemID","ID"):
        try: return int(getattr(item,a))
        except: pass
    return 0

def hue(item):
    try: return int(item.Hue)
    except: return -1

def amount(item):
    try: return int(item.Amount)
    except: return 0

def item_name(item):
    try: return str(item.Name or "")
    except: return ""

def item_opl(item):
    s = serial(item)
    try:
        t = API.ItemNameAndProps(s, True, OPL_TIMEOUT)
        if t: return str(t)
    except: pass
    return item_name(item)

def container_items(s):
    try:
        x = API.ItemsInContainer(int(s), False)
        return list(x) if x else []
    except:
        return None

def valid_bag(s):
    return bool(s and find_item(s))

def effective_bag(rule):
    """
    Rule-specific bag overrides the default bag.
    If a rule has no custom bag, the global default is used.
    """
    custom = int(rule.get("bag", 0) or 0)
    if valid_bag(custom):
        return custom
    if valid_bag(_default_bag):
        return int(_default_bag)
    return 0

def bag_source_text(rule):
    custom = int(rule.get("bag", 0) or 0)
    if valid_bag(custom):
        return "SET"
    if valid_bag(_default_bag):
        return "DEF"
    return "BAG"


# ============================================================
# Rule classification helpers
# ============================================================

def item_layer(item):
    try:
        return str(item.Layer or "")
    except:
        return ""


def item_matches_equipment_type(item, equipment_type):
    """
    Match either a broad equipment class or a specific equipment slot.

    Broad classes:
      Any Armor   = wearable armor/body slots, excluding jewelry/weapons
      Any Jewelry = Ring, Bracelet, Earrings
      Any Weapon  = hand-layer combat items, excluding shields
      Any Shield  = shield items
    """
    et = str(equipment_type or "Any")
    if et == "Any":
        return True

    raw_layer = item_layer(item)
    layer = raw_layer.lower().replace(" ", "").replace("_", "")
    name = item_name(item).lower()

    # Normalize the common Legion/TazUO layer names.
    jewelry_layers = (
        "ring",
        "bracelet",
        "earrings",
        "earring",
        "talisman",
    )

    armor_layers = (
        "head",
        "gloves",
        "neck",
        "arms",
        "outertorso",
        "middletorso",
        "innertorso",
        "outerlegs",
        "innerlegs",
        "pants",
        "waist",
    )

    hand_layers = (
        "righthand",
        "lefthand",
        "onehanded",
        "twohanded",
    )

    shield_words = (
        "shield",
        "buckler",
        "heater",
        "kite shield",
        "wooden shield",
        "metal shield",
        "order shield",
        "chaos shield",
    )

    weapon_words = (
        "sword", "blade", "katana", "wakizashi", "broadsword",
        "longsword", "scimitar", "cutlass", "saber", "axe",
        "hatchet", "mace", "maul", "hammer", "club", "spear",
        "lance", "pike", "halberd", "bardiche", "bow", "crossbow",
        "whip", "dagger", "kryss", "fencing", "staff", "quarter staff",
        "war fork", "cleaver", "knife",
    )

    if et in ("Any Jewelry", "Jewelry"):
        return (
            any(x in layer for x in jewelry_layers)
            or any(x in name for x in (" ring", "ring ", "bracelet", "earring"))
        )

    if et in ("Any Shield", "Shield"):
        return any(word in name for word in shield_words)

    if et == "Any Weapon":
        # Prefer the equipped layer when available.
        if any(x in layer for x in hand_layers):
            # Don't let shields be classified as weapons.
            if any(word in name for word in shield_words):
                return False
            return True

        # Corpse items can occasionally have weak/missing layer data,
        # so use conservative weapon-name fallback.
        return any(word in name for word in weapon_words)

    if et == "Any Armor":
        if any(x in layer for x in armor_layers):
            return True

        # Conservative name fallback for armor when layer is unavailable.
        armor_words = (
            "helmet", "helm", "cap", "hat",
            "gorget", "gloves", "gauntlets",
            "sleeves", "arms",
            "tunic", "chest", "breastplate", "armor", "armour",
            "leggings", "legs", "greaves", "skirt",
        )
        return any(word in name for word in armor_words)

    aliases = {
        "ring": ("ring",),
        "bracelet": ("bracelet",),
        "earrings": ("earrings", "earring"),
        "righthand": ("righthand", "onehanded", "twohanded"),
        "lefthand": ("lefthand",),
        "head": ("head",),
        "gloves": ("gloves",),
        "neck": ("neck",),
        "arms": ("arms",),
        "outertorso": ("outertorso",),
        "middletorso": ("middletorso",),
        "innertorso": ("innertorso",),
        "outerlegs": ("outerlegs",),
        "innerlegs": ("innerlegs",),
        "pants": ("pants",),
        "shoes": ("shoes",),
    }

    keys = aliases.get(et.lower(), (et.lower().replace(" ", ""),))
    return any(k in layer for k in keys)


def detect_rarity(opl):
    text=(opl or "").lower()
    # Check high/specific rarity names first.
    for rarity in reversed(RARITY_OPTIONS[1:]):
        if rarity.lower() in text:
            return rarity
    return None


def rarity_index(name):
    try:
        return RARITY_OPTIONS.index(name)
    except:
        return 0


def rarity_matches(opl, minimum, maximum):
    if not minimum and not maximum:
        return True
    found=detect_rarity(opl)
    if not found:
        return False
    idx=rarity_index(found)
    if minimum and idx < rarity_index(minimum):
        return False
    if maximum and idx > rarity_index(maximum):
        return False
    return True


def property_conditions_match(opl, rule):
    conditions = rule.get("property_conditions", []) or []
    if not conditions:
        return True

    results=[matches_property_condition(opl or "", c) for c in conditions]
    mode=str(rule.get("property_match_mode", "ALL")).upper()

    if mode == "ANY":
        return any(results)
    if mode == "COUNT":
        try:
            needed=max(1,int(rule.get("property_match_count",1) or 1))
        except:
            needed=1
        return sum(1 for x in results if x) >= needed
    return all(results)


def explain_rule_match(item, opl, rule):
    lines=[]
    name=item_name(item)
    text=(opl or "").lower()

    def add(label_, passed, detail=""):
        lines.append("{}: {}{}".format(
            label_, "PASS" if passed else "FAIL",
            (" ("+detail+")") if detail else ""
        ))
        return passed

    ok=True

    exp=rule.get("graphics",rule.get("graphic"))
    if exp is not None:
        passed=exact_or_in(graphic(item),exp)
        ok = add("Graphic",passed,hex(graphic(item))) and ok

    exp=rule.get("hues",rule.get("hue"))
    if exp is not None:
        passed=exact_or_in(hue(item),exp)
        ok = add("Hue",passed,hex(hue(item))) and ok

    et=rule.get("equipment_type")
    if et:
        passed=item_matches_equipment_type(item,et)
        ok = add("Equipment",passed,item_layer(item) or name) and ok

    if rule.get("name_any"):
        passed=contains_any(name.lower(),rule["name_any"])
        ok = add("Name contains any",passed,name) and ok
    if rule.get("name_all"):
        passed=contains_all(name.lower(),rule["name_all"])
        ok = add("Name contains all",passed,name) and ok
    if rule.get("opl_any"):
        passed=contains_any(text,rule["opl_any"])
        ok = add("OPL contains any",passed) and ok
    if rule.get("opl_all"):
        passed=contains_all(text,rule["opl_all"])
        ok = add("OPL contains all",passed) and ok
    if rule.get("reject_any"):
        passed=not contains_any(text,rule["reject_any"])
        ok = add("Reject text",passed) and ok

    black=rule.get("blacklist_properties",[]) or []
    for prop in black:
        passed=not property_exists(opl,prop)
        ok = add("Reject "+prop,passed) and ok

    minimum=rule.get("minimum_rarity")
    maximum=rule.get("maximum_rarity")
    if minimum or maximum:
        found=detect_rarity(opl) or "None"
        passed=rarity_matches(opl,minimum,maximum)
        ok = add("Rarity",passed,found) and ok

    conditions=rule.get("property_conditions",[]) or []
    results=[]
    for cond in conditions:
        passed=matches_property_condition(opl,cond)
        results.append(passed)
        detail=""
        prop=cond.get("property","")
        if prop not in ("Any Slayer","Any Element"):
            v=parse_property_number(opl,prop)
            if v is not None: detail=str(v)
        lines.append("{}: {}{}".format(
            property_display(cond),
            "PASS" if passed else "FAIL",
            (" ("+detail+")") if detail else ""
        ))

    if conditions:
        passed=property_conditions_match(opl,rule)
        mode=rule.get("property_match_mode","ALL")
        detail=mode
        if str(mode).upper()=="COUNT":
            detail="at least {}".format(rule.get("property_match_count",1))
        ok = add("Property group",passed,detail) and ok

    return ok, lines

# ============================================================
# Rule engine
# ============================================================

def contains_any(text, vals):
    return any(str(v).lower() in text for v in vals or [])

def contains_all(text, vals):
    return all(str(v).lower() in text for v in vals or [])

def exact_or_in(actual, expected):
    if expected is None: return True
    if isinstance(expected,(list,tuple,set)): return actual in expected
    return actual == expected

def matches_rule(item, opl, rule):
    if not rule.get("enabled",True): return False
    if not effective_bag(rule): return False

    # Gold and coin purses can be safely recognized by known graphics,
    # even when their name/OPL has not finished loading yet.
    if rule.get("id") == "gold":
        if graphic(item) in (0x0EED, 41777):
            return True

    name = item_name(item).lower()
    text = (opl or "").lower()

    pairs = rule.get("graphic_hue_pairs", []) or []
    if pairs:
        gi = graphic(item)
        hi = hue(item)
        if not any(
            int(p.get("graphic",-1)) == gi and int(p.get("hue",-999)) == hi
            for p in pairs if isinstance(p,dict)
        ):
            return False

    exp = rule.get("graphics",rule.get("graphic"))
    if exp is not None and not exact_or_in(graphic(item),exp): return False

    exp = rule.get("hues",rule.get("hue"))
    if exp is not None and not exact_or_in(hue(item),exp): return False

    if rule.get("name_any") and not contains_any(name,rule["name_any"]): return False
    if rule.get("name_all") and not contains_all(name,rule["name_all"]): return False
    if rule.get("opl_any") and not contains_any(text,rule["opl_any"]): return False
    if rule.get("opl_all") and not contains_all(text,rule["opl_all"]): return False
    if rule.get("reject_any") and contains_any(text,rule["reject_any"]): return False

    if rule.get("equipment_type") and not item_matches_equipment_type(item,rule.get("equipment_type")):
        return False

    if not rarity_matches(opl or "",rule.get("minimum_rarity"),rule.get("maximum_rarity")):
        return False

    for prop in rule.get("blacklist_properties",[]) or []:
        if property_exists(opl or "",prop):
            return False

    # Dropdown-built property requirements with ALL / ANY / COUNT logic.
    if not property_conditions_match(opl or "",rule):
        return False

    if rule.get("regex"):
        try:
            if re.search(rule["regex"], opl or "", re.I|re.M) is None:
                return False
        except Exception as e:
            API.SysMsg("Regex error in {}: {}".format(rule["name"],e),33)
            return False
    return True

def matching_rule(item, opl):
    for r in RULES:
        if matches_rule(item,opl,r):
            return r
    return None


# ============================================================
# Weight / move verification helpers
# ============================================================

OVERWEIGHT_MESSAGES = [
    "you are too encumbered",
    "you are overloaded",
    "you cannot carry",
    "you can't carry",
    "too heavy",
    "cannot hold more weight",
    "can't hold more weight",
]

def item_container(item):
    try:
        return int(item.Container)
    except:
        return 0

def player_weight():
    try:
        return int(API.Player.Weight)
    except:
        return None

def player_weight_max():
    try:
        return int(API.Player.WeightMax)
    except:
        return None

def overhead_warning(message):
    try:
        API.HeadMsg(message, API.Player, 33)
    except:
        pass
    try:
        API.SysMsg(message, 33)
    except:
        pass

def overweight_now():
    w=player_weight()
    mx=player_weight_max()
    if w is None or mx is None:
        return False
    return w >= mx

def journal_says_overweight():
    try:
        return API.InJournalAny(OVERWEIGHT_MESSAGES, True)
    except:
        return False

# ============================================================
# Loot engine (same proven v1 approach)
# ============================================================

def wait_ready():
    while not API.StopRequested and not _stop_requested:
        busy = False
        try: busy = busy or API.IsProcessingMoveQueue()
        except: pass
        try: busy = busy or API.IsGlobalCooldownActive()
        except: pass
        if not busy: return True
        API.ProcessCallbacks()
        API.Pause(0.05)
    return False

def move_item(item,dest):
    """
    A move counts as successful only after we verify the item left its
    original container and reached the requested destination (or merged
    into an existing stack and its original serial disappeared).
    """
    if not dest:
        API.SysMsg("Loot move blocked: no valid destination bag.",33)
        return False

    if overweight_now():
        overhead_warning("LOOTMASTER: OVERWEIGHT")
        return False

    if not wait_ready():
        return False

    s=serial(item)
    if not s:
        return False

    before=find_item(s)
    before_container=item_container(before) if before else 0

    # Clear only our likely weight-related messages before trying the move.
    try:
        for msg in OVERWEIGHT_MESSAGES:
            API.ClearJournal(msg)
    except:
        pass

    try:
        API.MoveItem(s,int(dest),amount(item) if amount(item)>0 else 0)
    except Exception as e:
        API.SysMsg("Loot move failed: "+str(e),33)
        return False

    # Give the server/client time to acknowledge the move.
    elapsed=0.0
    while elapsed < MOVE_CONFIRM_TIMEOUT:
        API.ProcessCallbacks()

        if journal_says_overweight():
            overhead_warning("LOOTMASTER: OVERWEIGHT")
            return False

        current=find_item(s)

        # Stack merged into an existing stack: original serial can vanish.
        if current is None:
            return True

        current_container=item_container(current)

        if current_container == int(dest):
            return True

        # It left the corpse/original container but the destination could be
        # represented through another root container. Treat a changed
        # container as progress only if it resolves to the destination.
        try:
            if int(current.RootContainer) == int(dest):
                return True
        except:
            pass

        API.Pause(0.05)
        elapsed += 0.05

    # If we're now at/over cap, make that obvious overhead.
    if overweight_now() or journal_says_overweight():
        overhead_warning("LOOTMASTER: OVERWEIGHT")
    else:
        API.SysMsg(
            "Loot move not confirmed: {} stayed in container {}.".format(
                item_name(item) or hex(s),
                hex(before_container) if before_container else "unknown"
            ),
            33
        )

    return False

def loot_container(container_serial,is_corpse=False):
    """
    Fast stable-scan looting.

    Strategy:
      1. Open once and give contents a short arrival window.
      2. Request OPL for the visible batch.
      3. Loot everything that matches.
      4. Re-scan once after moves.
      5. Stop after one unchanged confirmation scan.

    This keeps the anti-missed-gold behavior without the long five-pass
    conservative loop used by Reforged v1.0.
    """
    matched=moved=failed=0

    if not find_item(container_serial):
        return matched,moved,failed

    if is_corpse:
        try:
            API.ClearJournal()
        except:
            pass

    try:
        API.UseObject(container_serial)
        API.Pause(CORPSE_OPEN_DELAY)
    except:
        pass

    if is_corpse and journal_says_no_loot():
        API.SysMsg("Lootmaster: no loot rights - corpse skipped.",68)
        return matched,moved,failed

    # Corpses normally need at most three passes:
    # initial + post-move + stable confirmation.
    max_passes = 3 if is_corpse else 2
    previous_signature = None

    for pass_no in range(max_passes):
        API.ProcessCallbacks()

        if API.StopRequested or _stop_requested:
            break

        if is_corpse and (not _auto_loot or _paused):
            break

        items=container_items(container_serial)

        if items is None:
            API.Pause(0.06)
            continue

        signature=tuple(sorted(serial(i) for i in items if serial(i)))

        # On the confirmation pass, unchanged contents means we're done.
        if pass_no > 0 and signature == previous_signature:
            break

        previous_signature=signature

        # One batch OPL request per pass.
        try:
            ss=[serial(i) for i in items if serial(i)]
            if ss:
                API.RequestOPLData(ss)
                API.Pause(OPL_BATCH_PAUSE)
        except:
            pass

        moved_this_pass=0

        for item in list(items):
            API.ProcessCallbacks()

            if API.StopRequested or _stop_requested:
                break

            if is_corpse and (not _auto_loot or _paused):
                break

            current=find_item(serial(item))
            if not current:
                continue

            # Gold fast-path doesn't need a full OPL round-trip.
            candidate_rule=None
            if graphic(current) in (0x0EED,41777):
                for r in RULES:
                    if r.get("id")=="gold" and r.get("enabled",True):
                        if effective_bag(r):
                            candidate_rule=r
                        break

            if candidate_rule is not None:
                rule=candidate_rule
            else:
                opl=item_opl(current)
                rule=matching_rule(current,opl)

            if not rule:
                continue

            matched += 1

            if move_item(current,effective_bag(rule)):
                moved += 1
                moved_this_pass += 1

                API.SysMsg(
                    "Looted [{}] {}".format(
                        rule["name"],
                        item_name(current) or hex(serial(current))
                    ),
                    68
                )

                if rule.get("alert",False):
                    try:
                        API.HeadMsg(
                            "LOOT: "+rule["name"],
                            API.Player,
                            68
                        )
                    except:
                        pass
            else:
                failed += 1

                if overweight_now() or journal_says_overweight():
                    return matched,moved,failed

        # If we moved anything, refresh contents quickly and do another pass.
        if moved_this_pass:
            previous_signature=None
            API.Pause(POST_MOVE_PAUSE)
            continue

        # Nothing moved on this pass. One short confirmation is enough.
        if pass_no > 0:
            break

        API.Pause(STABLE_SCAN_PAUSE)

    return matched,moved,failed

def color_looted_corpse(corpse):
    if not corpse:
        return
    try:
        s=int(corpse.Serial)
    except:
        s=serial(corpse)
    if not s:
        return
    try:
        if s not in _colored_corpses:
            try: _colored_corpses[s]=int(corpse.Hue)
            except: _colored_corpses[s]=0
        try: corpse.SetHue(int(_mark_corpse_hue))
        except: corpse.Hue=int(_mark_corpse_hue)
    except Exception as e:
        API.SysMsg("Corpse coloring failed: "+str(e),33)

def hide_looted_corpse(corpse):
    if not corpse:
        return
    try: corpse.Destroy()
    except Exception as e: API.SysMsg("Corpse hide failed: "+str(e),33)

def apply_corpse_display(corpse):
    mode=str(_corpse_display_mode or "Color").title()
    if mode=="Hide": hide_looted_corpse(corpse)
    elif mode=="Color": color_looted_corpse(corpse)

def clear_corpse_colors():
    for s,original_hue in list(_colored_corpses.items()):
        try:
            corpse=find_item(s)
            if corpse:
                try: corpse.SetHue(int(original_hue))
                except: corpse.Hue=int(original_hue)
        except: pass
    _colored_corpses.clear()

def set_corpse_display_mode(mode):
    global _corpse_display_mode, _mark_corpses
    mode=str(mode or "").title()
    if mode not in CORPSE_DISPLAY_OPTIONS:
        API.SysMsg("Invalid corpse display mode.",33)
        return False
    if _corpse_display_mode=="Color" and mode!="Color": clear_corpse_colors()
    _corpse_display_mode=mode
    _mark_corpses=(mode!="Normal")
    pset(KEY_CORPSE_DISPLAY,_corpse_display_mode)
    pset(KEY_MARK_CORPSES,"1" if _mark_corpses else "0")
    autosave_settings()
    set_status("Corpse display mode: "+_corpse_display_mode)
    return True

def toggle_corpse_markers():
    current=str(_corpse_display_mode or "Color").title()
    try: idx=CORPSE_DISPLAY_OPTIONS.index(current)
    except: idx=1
    if set_corpse_display_mode(CORPSE_DISPLAY_OPTIONS[(idx+1)%len(CORPSE_DISPLAY_OPTIONS)]): refresh_main()

def set_corpse_marker_hue(value):
    global _mark_corpse_hue
    try: hue_value=max(0,min(65535,int(value)))
    except:
        API.SysMsg("Corpse hue must be a number.",33)
        return False
    _mark_corpse_hue=hue_value
    pset(KEY_MARK_HUE,str(_mark_corpse_hue))
    autosave_settings()
    if str(_corpse_display_mode).title()=="Color":
        for s in list(_colored_corpses.keys()):
            try:
                corpse=find_item(s)
                if corpse:
                    try: corpse.SetHue(int(_mark_corpse_hue))
                    except: corpse.Hue=int(_mark_corpse_hue)
            except: pass
    set_status("Looted corpse hue set to {}.".format(_mark_corpse_hue))
    return True

def next_corpse():
    try: corpse=API.NearestCorpse(LOOT_RANGE)
    except: corpse=None
    if not corpse: return None
    s=serial(corpse)
    if not s: return None
    if s in _processed_corpses:
        try: API.IgnoreObject(s)
        except: pass
        return None
    return corpse

def auto_loot_once():
    if not _auto_loot or _paused:
        return

    if player_is_dead():
        set_status("Dead - auto looting paused.")
        return

    corpse=next_corpse()
    if not corpse:
        return

    s=serial(corpse)
    set_status("Looting corpse {}...".format(hex(s)))

    matched,moved,failed=loot_container(s,True)

    # If weight blocked looting, keep this corpse available for retry.
    if overweight_now() or journal_says_overweight():
        set_status("OVERWEIGHT - corpse left available.")
        return

    _processed_corpses.add(s)

    finished_corpse=find_item(s) or corpse
    apply_corpse_display(finished_corpse)

    if IGNORE_AFTER_LOOT:
        try:
            API.IgnoreObject(s)
        except:
            pass

    set_status(
        "Corpse: {} matched, {} moved, {} failed.".format(
            matched,moved,failed
        )
    )


# ============================================================
# Integrated treasure-chest handler
# ============================================================

def chest_unlock(chest):
    """
    Repeats lockpicking until the shard reports success/unlocked.
    Based on the user's working Legion Chest Handler.
    """
    while not API.StopRequested and not _stop_requested:
        try:
            if not API.FindType(LOCKPICK_GRAPHIC, API.Backpack):
                API.SysMsg("Reforged: You are out of lockpicks.",33)
                return False
            pick=API.Found
        except:
            API.SysMsg("Reforged: Could not locate a lockpick.",33)
            return False

        API.ClearJournal()

        try:
            API.UseObject(pick)
            if API.WaitForTarget():
                API.Target(chest)
            else:
                API.Pause(0.1)
                continue
        except Exception as e:
            API.SysMsg("Lockpick error: "+str(e),33)
            return False

        API.Pause(0.5)

        try:
            if API.InJournalAny(SUCCESS_LOCKPICKING):
                return True
        except:
            pass

        # This shard has no normal lockpicking retry timer.
        API.Pause(0.05)

    return False


def chest_untrap(chest):
    """
    Repeats Remove Trap until the shard reports success/no trap.
    Preserves the timing from the user's working Chest Handler.
    """
    while not API.StopRequested and not _stop_requested:
        API.ClearJournal()

        try:
            API.UseSkill("Remove Trap")
            if not API.WaitForTarget():
                API.Pause(0.1)
                continue
            API.Target(chest)
        except Exception as e:
            API.SysMsg("Remove Trap error: "+str(e),33)
            return False

        API.Pause(3)

        try:
            if API.InJournalAny(SUCCESS_REMOVE_TRAP):
                return True
        except:
            pass

        API.Pause(9)

    return False


def handle_treasure_chest():
    """
    Target -> walk to chest -> unlock -> remove trap -> open ->
    run Reforged's own rule engine on the chest.
    """
    set_status("Target a chest to unlock, disarm, and loot.")
    try:
        API.HeadMsg("Target a chest to open and loot",API.Player,66)
    except:
        pass

    try:
        chest=API.RequestTarget()
    except:
        chest=0

    if not chest:
        set_status("Chest handling cancelled.")
        return

    item=find_item(chest)
    if not item:
        API.SysMsg("Reforged: Chest not found.",33)
        return

    # Walk adjacent if necessary.
    try:
        if int(item.Distance) > 1:
            set_status("Moving to chest...")
            API.Pathfind(item.X,item.Y,item.Z,1)

            while API.Pathfinding() and not API.StopRequested and not _stop_requested:
                API.ProcessCallbacks()
                API.Pause(0.1)
    except Exception as e:
        API.SysMsg("Pathfinding warning: "+str(e),33)

    if API.StopRequested or _stop_requested:
        return

    set_status("Lockpicking chest...")
    if not chest_unlock(chest):
        set_status("Chest unlock failed.")
        return

    set_status("Removing trap...")
    if not chest_untrap(chest):
        set_status("Trap removal failed.")
        return

    if API.StopRequested or _stop_requested:
        return

    set_status("Opening chest...")
    try:
        API.UseObject(chest)
        API.Pause(1.0)
    except Exception as e:
        API.SysMsg("Open chest error: "+str(e),33)
        return

    # Important: use OUR matching/move-verification engine, not
    # API.AutoLootContainer, so all user rules and bags apply.
    set_status("Looting chest with Reforged rules...")
    matched,moved,failed=loot_container(chest,False)

    set_status(
        "Chest complete: {} matched, {} moved, {} failed.".format(
            matched,moved,failed
        )
    )


# ============================================================
# UI helpers
# ============================================================

def label(text,size=14,color=C_TEXT,align="left",width=0):
    return API.CreateGumpTTFLabel(text,size,color,font="Avadonia",
                                  aligned=align,maxWidth=width if width else 0)

def gump_position(g):
    """
    Best-effort read of the current custom-gump screen position.
    Legion builds expose position slightly differently, so try the
    common forms instead of tying Reforged to one implementation.
    """
    if not g:
        return None

    for x_name,y_name in (
        ("X","Y"),
        ("ScreenX","ScreenY"),
        ("Left","Top"),
    ):
        try:
            return int(getattr(g,x_name)), int(getattr(g,y_name))
        except:
            pass

    for rect_name in ("Bounds","Rect","Rectangle"):
        try:
            r=getattr(g,rect_name)
            return int(r.X), int(r.Y)
        except:
            pass

    try:
        p=g.Position
        return int(p.X),int(p.Y)
    except:
        pass

    return None


def save_gump_position(g,x_key,y_key):
    pos=gump_position(g)
    if not pos:
        return
    try:
        x,y=pos
        # Ignore obviously invalid/transient coordinates.
        if x > -3000 and y > -3000:
            pset(x_key,str(x))
            pset(y_key,str(y))
    except:
        pass


def load_gump_position(x_key,y_key,default_x,default_y):
    try:
        x=int(pget(x_key,str(default_x)))
        y=int(pget(y_key,str(default_y)))
        return x,y
    except:
        return default_x,default_y


def dispose(g):
    try:
        if g: g.Dispose()
    except:
        pass

def set_text(c,t):
    try: c.SetText(str(t))
    except: pass

def set_status(t):
    set_text(_status_label,t)
    try: API.SysMsg(str(t),66)
    except: pass

def get_text(tb):
    try: return str(tb.Text)
    except:
        try: return str(tb.GetText())
        except: return ""

def get_checked(cb):
    try: return bool(cb.Checked)
    except:
        try: return bool(cb.IsChecked())
        except: return True

def split_csv(t):
    return [x.strip() for x in str(t or "").split(",") if x.strip()]

def parse_num(t):
    t=str(t or "").strip()
    if not t: return None
    try: return int(t,0)
    except: return None

def new_rule_id():
    try: return "rule_"+str(API.GetTickCount())
    except: return "rule_"+str(len(RULES)+1)


# ============================================================
# Main gump
# ============================================================

def refresh_main():
    global _main_gump, _status_label, _rule_page

    # Preserve the exact place the user dragged the previous gump to.
    save_gump_position(_main_gump,KEY_MAIN_X,KEY_MAIN_Y)
    dispose(_main_gump)

    if _compact_mode:
        refresh_compact()
        return

    W=820
    H=514
    ROW_H=31
    LIST_TOP=198
    LIST_H=RULES_PER_PAGE*ROW_H

    page_count=max(1,(len(RULES)+RULES_PER_PAGE-1)//RULES_PER_PAGE)
    _rule_page=max(0,min(_rule_page,page_count-1))
    start_index=_rule_page*RULES_PER_PAGE

    gx,gy=load_gump_position(KEY_MAIN_X,KEY_MAIN_Y,92,82)

    g=API.CreateGump(True,True,True)
    g.SetRect(gx,gy,W,H)

    bg=API.CreateGumpColorBox(0.94,C_BG)
    bg.SetRect(0,0,W,H)
    g.Add(bg)

    header=API.CreateGumpColorBox(0.58,C_PANEL)
    header.SetRect(7,7,W-14,38)
    g.Add(header)

    title=label("J.C.S. LOOTMASTER REFORGED",19,C_TITLE,"left",470)
    title.SetRect(18,13,470,25)
    g.Add(title)

    sub=label("Native Legion build",10,C_MUTED,"left",130)
    sub.SetRect(492,20,130,16)
    g.Add(sub)

    ver=label("v"+VERSION,11,C_MUTED,"right",70)
    ver.SetRect(W-130,19,70,16)
    g.Add(ver)

    close_b=API.CreateSimpleButton("[X]",36,24)
    close_b.SetPos(W-45,13)
    API.AddControlOnClick(close_b,close_all)
    g.Add(close_b)

    # Top command bar
    cmd=API.CreateGumpColorBox(0.32,C_PANEL)
    cmd.SetRect(7,51,W-14,47)
    g.Add(cmd)

    def top_btn(txt,x,w,cb):
        b=API.CreateSimpleButton(txt,w,26)
        b.SetPos(x,61)
        API.AddControlOnClick(b,cb)
        g.Add(b)
        return b

    top_btn("[AUTO ON]" if _auto_loot else "[AUTO OFF]",15,88,toggle_auto)
    top_btn("[PAUSE]",108,72,toggle_pause)
    top_btn("[MANUAL]",185,78,manual_loot)
    top_btn("[CHEST]",268,76,handle_treasure_chest)
    top_btn("[+ RULE]",349,78,lambda:open_editor(None))
    top_btn("[DEFAULT]",432,82,set_default_bag)
    top_btn("[IMPORT]",519,72,lambda:import_settings(False))
    top_btn("[EXPORT]",596,72,lambda:export_settings(False))
    top_btn("[SMALL]",673,68,toggle_compact)

    # Information strip. Keep paging in its own right-hand zone.
    info=API.CreateGumpColorBox(0.22,C_PANEL)
    info.SetRect(7,103,W-14,43)
    g.Add(info)

    rule_title=label("LOOT RULES",13,C_GOLD,"left",100)
    rule_title.SetRect(16,112,100,18)
    g.Add(rule_title)

    count_lab=label("{} rules".format(len(RULES)),10,C_MUTED,"left",70)
    count_lab.SetRect(113,114,70,16)
    g.Add(count_lab)

    default_text="Default bag: "+(
        hex(_default_bag) if valid_bag(_default_bag) else "NOT SET"
    )
    dl=label(
        default_text,10,
        C_GREEN if valid_bag(_default_bag) else C_RED,
        "left",260
    )
    dl.SetRect(190,114,260,16)
    g.Add(dl)

    # Paging occupies x=600..800 and no longer overlaps bag status.
    def change_page(delta):
        def cb():
            global _rule_page
            max_page=max(
                0,
                (len(RULES)+RULES_PER_PAGE-1)//RULES_PER_PAGE-1
            )
            _rule_page=max(0,min(_rule_page+delta,max_page))
            refresh_main()
        return cb

    prev_b=API.CreateSimpleButton("[< PREV]",72,22)
    prev_b.SetPos(590,110)
    API.AddControlOnClick(prev_b,change_page(-1))
    g.Add(prev_b)

    page_lab=label(
        "{} / {}".format(_rule_page+1,page_count),
        11,C_TEXT,"center",55
    )
    page_lab.SetRect(668,114,55,16)
    g.Add(page_lab)

    next_b=API.CreateSimpleButton("[NEXT >]",72,22)
    next_b.SetPos(730,110)
    API.AddControlOnClick(next_b,change_page(1))
    g.Add(next_b)

    marker_panel=API.CreateGumpColorBox(0.28,C_PANEL)
    marker_panel.SetRect(7,151,W-14,38)
    g.Add(marker_panel)

    marker_title=label("CORPSE",11,C_GOLD,"left",58)
    marker_title.SetRect(16,162,58,17)
    g.Add(marker_title)

    mode_idx=CORPSE_DISPLAY_OPTIONS.index(_corpse_display_mode) if _corpse_display_mode in CORPSE_DISPLAY_OPTIONS else 1
    mode_dd=API.CreateDropDown(105,CORPSE_DISPLAY_OPTIONS,mode_idx)
    mode_dd.SetPos(72,157)
    g.Add(mode_dd)

    def apply_display_mode():
        idx=mode_dd.GetSelectedIndex()
        if 0<=idx<len(CORPSE_DISPLAY_OPTIONS):
            set_corpse_display_mode(CORPSE_DISPLAY_OPTIONS[idx])
            refresh_main()

    mode_apply=API.CreateSimpleButton("[SET]",58,23)
    mode_apply.SetPos(182,157)
    API.AddControlOnClick(mode_apply,apply_display_mode)
    g.Add(mode_apply)

    marker_idx=0
    for i,opt in enumerate(CORPSE_MARKER_OPTIONS):
        if opt[1] == _mark_corpse_hue:
            marker_idx=i
            break

    marker_dd=API.CreateDropDown(132,CORPSE_MARKER_LABELS,marker_idx)
    marker_dd.SetPos(247,157)
    g.Add(marker_dd)

    hue_tb=API.CreateGumpTextBox(str(_mark_corpse_hue),66,23)
    hue_tb.SetPos(385,157)
    g.Add(hue_tb)

    def apply_marker_choice():
        idx=marker_dd.GetSelectedIndex()
        if 0<=idx<len(CORPSE_MARKER_OPTIONS):
            preset_hue=CORPSE_MARKER_OPTIONS[idx][1]
            if preset_hue is None:
                raw=get_text(hue_tb).strip()
                try:
                    val=int(raw,0)
                except:
                    API.SysMsg("Enter a custom hue number.",33)
                    return
            else:
                val=preset_hue
                set_text(hue_tb,str(val))
            if set_corpse_marker_hue(val):
                refresh_main()

    apply_mark=API.CreateSimpleButton("[APPLY]",72,23)
    apply_mark.SetPos(457,157)
    API.AddControlOnClick(apply_mark,apply_marker_choice)
    g.Add(apply_mark)

    clear_mark=API.CreateSimpleButton("[CLEAR]",82,23)
    clear_mark.SetPos(535,157)
    def clear_marker_ui():
        clear_corpse_colors()
        set_status("Looted corpse colors restored.")
    API.AddControlOnClick(clear_mark,clear_marker_ui)
    g.Add(clear_mark)

    clear_done=API.CreateSimpleButton("[RESET]",94,23)
    clear_done.SetPos(649,157)
    API.AddControlOnClick(clear_done,clear_corpses)
    g.Add(clear_done)

    # Rule viewport
    viewport=API.CreateGumpColorBox(0.24,C_PANEL)
    viewport.SetRect(7,191,W-14,LIST_H+34)
    g.Add(viewport)

    heads=[
        ("#",12,28),
        ("RULE",43,280),
        ("STATE",326,54),
        ("BAG",383,54),
        ("EDIT",440,52),
        ("COPY",495,52),
        ("ORDER",550,91),
        ("DEFAULT",644,70),
        ("DELETE",717,82),
    ]
    for txt,x,w in heads:
        q=label(txt,10,C_MUTED,"center",w)
        q.SetRect(x,194,w,17)
        g.Add(q)

    def mk_toggle(rid):
        def cb():
            rr=find_rule(rid)
            if rr:
                rr["enabled"]=not rr.get("enabled",True)
                save_rules()
                refresh_main()
        return cb

    def mk_bag(rid):
        def cb():
            rr=find_rule(rid)
            if not rr:
                return
            set_status("Target custom bag for "+rr["name"]+".")
            try:s=API.RequestTarget()
            except:s=0
            if s and find_item(s):
                rr["bag"]=int(s)
                save_rules()
                refresh_main()
        return cb

    def mk_clear_bag(rid):
        def cb():
            rr=find_rule(rid)
            if rr:
                rr["bag"]=0
                save_rules()
                refresh_main()
                set_status(rr["name"]+" now uses the Default Bag.")
        return cb

    def mk_edit(rid):
        return lambda:open_editor(rid)

    def mk_clone(rid):
        def cb():
            global _rule_page
            rr=find_rule(rid)
            if not rr:return
            cp=sanitize_rule(rr)
            cp["id"]=new_rule_id()
            cp["name"]=rr.get("name","Rule")+" Copy"
            src_i=next((i for i,x in enumerate(RULES) if x["id"]==rid),len(RULES)-1)
            RULES.insert(src_i+1,cp)
            _rule_page=(src_i+1)//RULES_PER_PAGE
            save_rules()
            refresh_main()
            set_status("Cloned: "+rr.get("name","Rule"))
        return cb

    def mk_move(rid,d):
        def cb():
            global _rule_page
            i=next((i for i,x in enumerate(RULES) if x["id"]==rid),None)
            if i is None:return
            j=i+d
            if 0<=j<len(RULES):
                RULES[i],RULES[j]=RULES[j],RULES[i]
                _rule_page=j//RULES_PER_PAGE
                save_rules()
                refresh_main()
        return cb

    def mk_del(rid):
        def cb():
            global RULES,_rule_page
            old_i=next((i for i,x in enumerate(RULES) if x["id"]==rid),0)
            RULES=[x for x in RULES if x["id"]!=rid]
            _rule_page=min(
                old_i//RULES_PER_PAGE,
                max(0,(len(RULES)-1)//RULES_PER_PAGE)
            )
            save_rules()
            refresh_main()
        return cb

    y=LIST_TOP+17

    for local_i in range(RULES_PER_PAGE):
        absolute_i=start_index+local_i

        row_bg=API.CreateGumpColorBox(
            0.34 if local_i%2==0 else 0.23,C_PANEL
        )
        row_bg.SetRect(11,y-1,W-22,ROW_H-2)
        g.Add(row_bg)

        if absolute_i>=len(RULES):
            y+=ROW_H
            continue

        r=RULES[absolute_i]

        num=label(str(absolute_i+1),10,C_MUTED,"center",28)
        num.SetRect(12,y+5,28,17)
        g.Add(num)

        name_color=C_TEXT if r.get("enabled",True) else C_MUTED
        nm=label(r["name"],12,name_color,"left",274)
        nm.SetRect(46,y+5,274,18)
        g.Add(nm)

        b=API.CreateSimpleButton("[ON]" if r.get("enabled",True) else "[OFF]",52,23)
        b.SetPos(327,y+2); API.AddControlOnClick(b,mk_toggle(r["id"])); g.Add(b)

        b=API.CreateSimpleButton("["+bag_source_text(r)+"]",52,23)
        b.SetPos(384,y+2); API.AddControlOnClick(b,mk_bag(r["id"])); g.Add(b)

        b=API.CreateSimpleButton("[E]",50,23)
        b.SetPos(441,y+2); API.AddControlOnClick(b,mk_edit(r["id"])); g.Add(b)

        b=API.CreateSimpleButton("[C]",50,23)
        b.SetPos(496,y+2); API.AddControlOnClick(b,mk_clone(r["id"])); g.Add(b)

        b=API.CreateSimpleButton("[^]",42,23)
        b.SetPos(551,y+2); API.AddControlOnClick(b,mk_move(r["id"],-1)); g.Add(b)

        b=API.CreateSimpleButton("[v]",42,23)
        b.SetPos(597,y+2); API.AddControlOnClick(b,mk_move(r["id"],1)); g.Add(b)

        b=API.CreateSimpleButton("[DEF]",66,23)
        b.SetPos(645,y+2); API.AddControlOnClick(b,mk_clear_bag(r["id"])); g.Add(b)

        b=API.CreateSimpleButton("[DEL]",76,23)
        b.SetPos(718,y+2); API.AddControlOnClick(b,mk_del(r["id"])); g.Add(b)

        y+=ROW_H

    footer_y=474
    footer=API.CreateGumpColorBox(0.40,C_PANEL)
    footer.SetRect(7,footer_y,W-14,31)
    g.Add(footer)

    _status_label=label(
        "First matching enabled rule wins.",
        11,C_MUTED,"left",510
    )
    _status_label.SetRect(16,footer_y+7,510,17)
    g.Add(_status_label)

    starter_b=API.CreateSimpleButton("[STARTER]",86,23)
    starter_b.SetPos(535,footer_y+4)
    API.AddControlOnClick(starter_b,reset_to_starter_rules)
    g.Add(starter_b)

    speed_b=API.CreateSimpleButton("[{}]".format(_loot_speed.upper()),92,23)
    speed_b.SetPos(627,footer_y+4)
    API.AddControlOnClick(speed_b,cycle_loot_speed)
    g.Add(speed_b)

    range_lab=label(
        "{}-{} / {}".format(
            start_index+1 if RULES else 0,
            min(start_index+RULES_PER_PAGE,len(RULES)),
            len(RULES)
        ),
        10,C_MUTED,"right",76
    )
    range_lab.SetRect(728,footer_y+8,76,16)
    g.Add(range_lab)

    _main_gump=g
    API.AddGump(g)

def refresh_compact():
    global _main_gump,_status_label

    save_gump_position(_main_gump,KEY_MAIN_X,KEY_MAIN_Y)
    dispose(_main_gump)

    W=390
    H=112
    gx,gy=load_gump_position(KEY_MAIN_X,KEY_MAIN_Y,100,100)

    g=API.CreateGump(True,True,True)
    g.SetRect(gx,gy,W,H)

    bg=API.CreateGumpColorBox(0.94,C_BG)
    bg.SetRect(0,0,W,H)
    g.Add(bg)

    t=label("LOOTMASTER REFORGED",16,C_TITLE,"center",W)
    t.SetRect(0,5,W,22)
    g.Add(t)

    controls=[
        ("[AUTO]" if _auto_loot else "[OFF]",8,62,toggle_auto),
        ("[PAUSE]",74,62,toggle_pause),
        ("[MANUAL]",140,68,manual_loot),
        ("[CHEST]",212,66,handle_treasure_chest),
        ("[FULL]",282,56,toggle_compact),
        ("[X]",342,38,close_all),
    ]
    for txt,x,w,cb in controls:
        b=API.CreateSimpleButton(txt,w,24)
        b.SetPos(x,32)
        API.AddControlOnClick(b,cb)
        g.Add(b)

    bagtxt="Default: SET" if valid_bag(_default_bag) else "Default: NOT SET"
    bag=label(
        bagtxt,11,
        C_GREEN if valid_bag(_default_bag) else C_RED,
        "center",W
    )
    bag.SetRect(0,62,W,17)
    g.Add(bag)

    _status_label=label(
        "{} | Speed: {}".format(
            "Auto looting active." if _auto_loot and not _paused
            else "Paused." if _paused else "Auto loot off.",
            _loot_speed
        ),
        11,C_MUTED,"center",W-12
    )
    _status_label.SetRect(6,84,W-12,18)
    g.Add(_status_label)

    _main_gump=g
    API.AddGump(g)


# ============================================================
# Rule editor
# ============================================================

def find_rule(rid):
    return next((r for r in RULES if r["id"]==rid),None)

def open_editor(rule_id=None):
    global _editor_gump

    save_gump_position(_editor_gump,KEY_EDITOR_X,KEY_EDITOR_Y)
    dispose(_editor_gump)

    rule=dict(find_rule(rule_id) or {})

    state={
        "bag":int(rule.get("bag",0) or 0),
        "conditions":[dict(c) for c in rule.get("property_conditions",[])],
        "blacklist":list(rule.get("blacklist_properties",[])),
        "opl_any":list(rule.get("opl_any",[])),
        "equipment_type":rule.get("equipment_type") or "Any",
        "minimum_rarity":rule.get("minimum_rarity") or "Any",
        "property_match_mode":str(rule.get("property_match_mode","ALL")).upper(),
        "property_match_count":int(rule.get("property_match_count",1) or 1),
        "preset_rule_data":{
            "graphics":list(rule.get("graphics",[]))
                if isinstance(rule.get("graphics"),list) else [],
            "graphic_hue_pairs":[
                dict(p) for p in rule.get("graphic_hue_pairs",[])
                if isinstance(p,dict)
            ],
        },
    }

    W=900
    H=720
    gx,gy=load_gump_position(KEY_EDITOR_X,KEY_EDITOR_Y,115,42)

    g=API.CreateGump(True,True,True)
    g.SetRect(gx,gy,W,H)

    bg=API.CreateGumpColorBox(0.96,C_BG)
    bg.SetRect(0,0,W,H)
    g.Add(bg)

    header=API.CreateGumpColorBox(0.58,C_PANEL)
    header.SetRect(7,7,W-14,40)
    g.Add(header)

    title_text="EDIT RULE" if rule_id else "NEW RULE"
    title=label(title_text,20,C_TITLE,"left",300)
    title.SetRect(18,14,300,25)
    g.Add(title)

    rule_hint=label(
        rule.get("name","Build a new loot rule"),
        11,C_MUTED,"right",430
    )
    rule_hint.SetRect(405,20,430,17)
    g.Add(rule_hint)

    fields={}

    def panel(x,y,w,h,title_text):
        box=API.CreateGumpColorBox(0.32,C_PANEL)
        box.SetRect(x,y,w,h)
        g.Add(box)
        lab=label(title_text,13,C_GOLD,"left",w-20)
        lab.SetRect(x+10,y+7,w-20,18)
        g.Add(lab)

    def field(key,caption,x,y,width,val=""):
        l=label(caption,11,C_MUTED,"left",135)
        l.SetRect(x,y+4,135,18)
        g.Add(l)
        tb=API.CreateGumpTextBox(str(val or ""),width,24)
        tb.SetPos(x+138,y)
        g.Add(tb)
        fields[key]=tb
        return tb

    # --------------------------------------------------------
    # LEFT: Basic matching
    # --------------------------------------------------------
    panel(10,55,430,210,"BASIC MATCH")
    field("name","Rule name",22,86,245,rule.get("name",""))
    field("name_any","Name contains any",22,117,245,", ".join(rule.get("name_any",[])))
    field("name_all","Name contains all",22,148,245,", ".join(rule.get("name_all",[])))
    field("opl_any","OPL contains any",22,179,245,", ".join(rule.get("opl_any",[])))
    field("reject_any","Reject OPL text",22,210,245,", ".join(rule.get("reject_any",[])))

    # --------------------------------------------------------
    # RIGHT: Preset / category
    # --------------------------------------------------------
    panel(450,55,440,210,"PRESET / CATEGORY")

    pl=label("Quick preset",11,C_MUTED); pl.SetRect(462,87,90,18); g.Add(pl)
    preset_dd=API.CreateDropDown(245,PRESET_OPTIONS,0)
    preset_dd.SetPos(550,82)
    g.Add(preset_dd)
    preset_b=API.CreateSimpleButton("[APPLY]",75,24)
    preset_b.SetPos(802,82)
    g.Add(preset_b)

    eql=label("Equipment",11,C_MUTED); eql.SetRect(462,121,85,18); g.Add(eql)
    eq_name=rule.get("equipment_type") or "Any"
    eq_idx=EQUIPMENT_OPTIONS.index(eq_name) if eq_name in EQUIPMENT_OPTIONS else 0
    eq_dd=API.CreateDropDown(220,EQUIPMENT_OPTIONS,eq_idx)
    eq_dd.SetPos(550,116)
    g.Add(eq_dd)

    rarity_lab=label("Rarity",11,C_MUTED); rarity_lab.SetRect(462,155,70,18); g.Add(rarity_lab)
    min_name=rule.get("minimum_rarity") or "Any"
    max_name=rule.get("maximum_rarity") or "Any"
    min_idx=RARITY_OPTIONS.index(min_name) if min_name in RARITY_OPTIONS else 0
    max_idx=RARITY_OPTIONS.index(max_name) if max_name in RARITY_OPTIONS else 0
    min_dd=API.CreateDropDown(150,RARITY_OPTIONS,min_idx)
    min_dd.SetPos(550,150)
    g.Add(min_dd)
    tolab=label("to",10,C_MUTED,"center",28)
    tolab.SetRect(704,155,28,16)
    g.Add(tolab)
    max_dd=API.CreateDropDown(150,RARITY_OPTIONS,max_idx)
    max_dd.SetPos(735,150)
    g.Add(max_dd)

    preset_status=label("",10,C_GREEN,"left",410)
    preset_status.SetRect(462,188,410,34)
    g.Add(preset_status)

    # Item ID filters on same category panel.
    field(
        "graphic","Graphic",462,226,104,
        hex(rule["graphic"]) if "graphic" in rule else ""
    )
    # Move created graphic field into available right-panel slot.
    fields["graphic"].SetPos(550,226)
    field(
        "hue","Hue",680,226,104,
        hex(rule["hue"]) if "hue" in rule else ""
    )
    fields["hue"].SetPos(735,226)

    # --------------------------------------------------------
    # LEFT LOWER: Properties
    # --------------------------------------------------------
    panel(10,275,555,325,"PROPERTY BUILDER")

    prop_dd=API.CreateDropDown(230,PROPERTY_OPTIONS,0)
    prop_dd.SetPos(22,307)
    g.Add(prop_dd)

    op_dd=API.CreateDropDown(105,OPERATOR_OPTIONS,0)
    op_dd.SetPos(258,307)
    g.Add(op_dd)

    value_tb=API.CreateGumpTextBox("",82,24)
    value_tb.SetPos(369,307)
    g.Add(value_tb)

    add_prop=API.CreateSimpleButton("[ADD]",82,24)
    add_prop.SetPos(458,307)
    g.Add(add_prop)

    condition_rows=[]
    condition_remove_buttons=[]

    for row in range(7):
        y=344+(row*27)

        rowbox=API.CreateGumpColorBox(
            0.22 if row%2 else 0.30,C_PANEL
        )
        rowbox.SetRect(20,y-2,530,25)
        g.Add(rowbox)

        lab=label("",11,C_TEXT,"left",455)
        lab.SetRect(27,y+3,455,18)
        g.Add(lab)
        condition_rows.append(lab)

        xb=API.CreateSimpleButton("[X]",48,21)
        xb.SetPos(493,y)
        g.Add(xb)
        condition_remove_buttons.append(xb)

    def visible_condition_indices():
        total=len(state["conditions"])
        start=max(0,total-7)
        return list(range(start,total))

    def update_conditions():
        indices=visible_condition_indices()
        for row in range(7):
            if row<len(indices):
                idx=indices[row]
                set_text(
                    condition_rows[row],
                    "{}. {}".format(
                        idx+1,
                        property_display(state["conditions"][idx])
                    )
                )
            else:
                set_text(condition_rows[row],"")
        if not state["conditions"]:
            set_text(condition_rows[0],"No property requirements added.")

    def remove_visible_property(row):
        indices=visible_condition_indices()
        if row<0 or row>=len(indices):
            return
        idx=indices[row]
        if 0<=idx<len(state["conditions"]):
            removed=state["conditions"].pop(idx)
            API.SysMsg("Removed: "+property_display(removed),68)
            update_conditions()

    for row,xb in enumerate(condition_remove_buttons):
        API.AddControlOnClick(
            xb,
            (lambda r=row:remove_visible_property(r))
        )

    def add_property():
        pi=prop_dd.GetSelectedIndex()
        oi=op_dd.GetSelectedIndex()
        if not (
            0<=pi<len(PROPERTY_OPTIONS)
            and 0<=oi<len(OPERATOR_OPTIONS)
        ):
            return

        prop=PROPERTY_OPTIONS[pi]
        op=OPERATOR_OPTIONS[oi]
        val=None

        if op!="Exists":
            raw=get_text(value_tb).strip()
            if not raw:
                API.SysMsg("Enter a value for "+prop,33)
                return
            try:
                val=int(raw)
            except:
                API.SysMsg("Value must be a number.",33)
                return

        state["conditions"].append({
            "property":prop,
            "operator":op,
            "value":val,
        })
        set_text(value_tb,"")
        update_conditions()

    API.AddControlOnClick(add_prop,add_property)
    update_conditions()

    # --------------------------------------------------------
    # RIGHT LOWER: Rule behavior / exclusions / destination
    # --------------------------------------------------------
    panel(575,275,315,325,"RULE OPTIONS")

    ml=label("Property matching",11,C_MUTED)
    ml.SetRect(588,307,115,18)
    g.Add(ml)

    mode_value=str(state.get("property_match_mode","ALL")).upper()
    mode_idx={"ALL":0,"ANY":1,"COUNT":2}.get(mode_value,0)
    mode_dd=API.CreateDropDown(170,PROPERTY_MATCH_OPTIONS,mode_idx)
    mode_dd.SetPos(700,302)
    g.Add(mode_dd)

    cl=label("Minimum count",11,C_MUTED)
    cl.SetRect(588,342,105,18)
    g.Add(cl)
    count_tb=API.CreateGumpTextBox(
        str(state.get("property_match_count",1)),70,24
    )
    count_tb.SetPos(700,337)
    g.Add(count_tb)

    bl=label("Reject property",11,C_MUTED)
    bl.SetRect(588,377,105,18)
    g.Add(bl)

    blacklist_dd=API.CreateDropDown(170,BLACKLIST_OPTIONS,0)
    blacklist_dd.SetPos(700,372)
    g.Add(blacklist_dd)

    add_bl=API.CreateSimpleButton("[ADD]",70,23)
    add_bl.SetPos(700,403)
    g.Add(add_bl)

    clear_bl=API.CreateSimpleButton("[CLEAR]",82,23)
    clear_bl.SetPos(776,403)
    g.Add(clear_bl)

    blacklist_label=label("",10,C_RED,"left",280)
    blacklist_label.SetRect(588,435,280,47)
    g.Add(blacklist_label)

    def update_blacklist():
        set_text(
            blacklist_label,
            "Reject: "+(
                ", ".join(state["blacklist"])
                if state["blacklist"] else "None"
            )
        )

    def add_blacklist():
        i=blacklist_dd.GetSelectedIndex()
        if 0<=i<len(BLACKLIST_OPTIONS):
            prop=BLACKLIST_OPTIONS[i]
            if prop not in state["blacklist"]:
                state["blacklist"].append(prop)
            update_blacklist()

    def clear_blacklist():
        state["blacklist"]=[]
        update_blacklist()

    API.AddControlOnClick(add_bl,add_blacklist)
    API.AddControlOnClick(clear_bl,clear_blacklist)
    update_blacklist()

    enabled=API.CreateGumpCheckbox(
        "Enabled",0,bool(rule.get("enabled",True))
    )
    enabled.SetPos(588,499)
    g.Add(enabled)

    alert=API.CreateGumpCheckbox(
        "Overhead alert",0,bool(rule.get("alert",False))
    )
    alert.SetPos(690,499)
    g.Add(alert)

    baglab=label(
        "Bag: "+(
            hex(state["bag"]) if state["bag"]
            else ("DEFAULT" if valid_bag(_default_bag) else "Not Set")
        ),
        11,C_GOLD,"left",280
    )
    baglab.SetRect(588,533,280,18)
    g.Add(baglab)

    def choose_bag():
        try:s=API.RequestTarget()
        except:s=0
        if s and find_item(s):
            state["bag"]=int(s)
            set_text(baglab,"Bag: "+hex(int(s)))

    def use_default_bag():
        state["bag"]=0
        set_text(
            baglab,
            "Bag: DEFAULT" if valid_bag(_default_bag)
            else "Bag: Not Set"
        )

    setbag=API.CreateSimpleButton("[SET BAG]",88,24)
    setbag.SetPos(588,560)
    API.AddControlOnClick(setbag,choose_bag)
    g.Add(setbag)

    defbag=API.CreateSimpleButton("[DEFAULT]",88,24)
    defbag.SetPos(681,560)
    API.AddControlOnClick(defbag,use_default_bag)
    g.Add(defbag)

    # --------------------------------------------------------
    # Preset application
    # --------------------------------------------------------
    def apply_selected_preset():
        idx=preset_dd.GetSelectedIndex()
        if not (0<idx<len(PRESET_OPTIONS)):
            return

        name=PRESET_OPTIONS[idx]

        if name in (
            "Legendary+","Legendary Armor",
            "Legendary Jewelry","Legendary Weapon"
        ):
            state["opl_any"]=[]
            set_text(fields["opl_any"],"")

        apply_preset(name,state)

        if state.get("opl_any"):
            set_text(fields["opl_any"],", ".join(state["opl_any"]))

        if state.get("equipment_type") in EQUIPMENT_OPTIONS:
            try:
                eq_dd.SetSelectedIndex(
                    EQUIPMENT_OPTIONS.index(state["equipment_type"])
                )
            except:
                pass

        if state.get("minimum_rarity") in RARITY_OPTIONS:
            try:
                min_dd.SetSelectedIndex(
                    RARITY_OPTIONS.index(state["minimum_rarity"])
                )
            except:
                pass

        preset_mode=str(state.get("property_match_mode","ALL")).upper()
        try:
            mode_dd.SetSelectedIndex(
                {"ALL":0,"ANY":1,"COUNT":2}.get(preset_mode,0)
            )
        except:
            pass

        try:
            set_text(
                count_tb,
                str(max(1,int(state.get("property_match_count",1) or 1)))
            )
        except:
            set_text(count_tb,"1")

        update_conditions()

        summary=[]
        if state.get("equipment_type")!="Any":
            summary.append(state.get("equipment_type",""))

        if state.get("minimum_rarity")!="Any":
            summary.append(state.get("minimum_rarity","")+"+")

        if state.get("conditions"):
            summary.append("{} props".format(len(state["conditions"])))
            if str(state.get("property_match_mode","ALL")).upper()=="COUNT":
                summary.append(
                    "need {}".format(
                        max(1,int(state.get("property_match_count",1) or 1))
                    )
                )

        pdata=state.get("preset_rule_data",{}) or {}
        if pdata.get("graphics"):
            summary.append("{} item IDs".format(len(pdata["graphics"])))
        if pdata.get("graphic_hue_pairs"):
            summary.append(
                "{} ID/hue pairs".format(len(pdata["graphic_hue_pairs"]))
            )

        set_text(
            preset_status,
            "Applied: "+(" / ".join(summary) if summary else name)
        )

        if not get_text(fields["name"]).strip():
            set_text(fields["name"],name)

    API.AddControlOnClick(preset_b,apply_selected_preset)

    # --------------------------------------------------------
    # Target / build / test / save
    # --------------------------------------------------------
    def target_item_seed():
        set_status("Target item to seed this rule.")
        try:s=API.RequestTarget()
        except:s=0
        item=find_item(s)
        if not item:return

        nm=item_name(item)
        set_text(fields["name"],"Rule for "+(nm or hex(s)))
        set_text(fields["name_any"],nm)
        set_text(fields["graphic"],hex(graphic(item)))
        set_text(fields["hue"],hex(hue(item)))

    def build_rule_from_editor():
        newr={
            "id":rule_id or new_rule_id(),
            "name":get_text(fields["name"]).strip() or "Unnamed Rule",
            "enabled":get_checked(enabled),
            "alert":get_checked(alert),
            "bag":state["bag"],
        }

        for k in ("name_any","name_all","opl_any","reject_any"):
            vals=split_csv(get_text(fields[k]))
            if vals:
                newr[k]=vals

        if state["conditions"]:
            newr["property_conditions"]=[
                dict(c) for c in state["conditions"]
            ]

        if state["blacklist"]:
            newr["blacklist_properties"]=list(state["blacklist"])

        mi=mode_dd.GetSelectedIndex()
        newr["property_match_mode"]=(
            ("ALL","ANY","COUNT")[mi] if 0<=mi<3 else "ALL"
        )

        try:
            newr["property_match_count"]=max(
                1,int(get_text(count_tb).strip() or "1")
            )
        except:
            newr["property_match_count"]=1

        rmi=min_dd.GetSelectedIndex()
        rma=max_dd.GetSelectedIndex()
        ei=eq_dd.GetSelectedIndex()

        if 0<rmi<len(RARITY_OPTIONS):
            newr["minimum_rarity"]=RARITY_OPTIONS[rmi]
        if 0<rma<len(RARITY_OPTIONS):
            newr["maximum_rarity"]=RARITY_OPTIONS[rma]
        if 0<ei<len(EQUIPMENT_OPTIONS):
            newr["equipment_type"]=EQUIPMENT_OPTIONS[ei]

        if rule_id and rule.get("regex"):
            newr["regex"]=rule.get("regex")

        pdata=state.get("preset_rule_data",{}) or {}

        if isinstance(pdata.get("graphics"),list) and pdata.get("graphics"):
            newr["graphics"]=[int(x) for x in pdata["graphics"]]

        if (
            isinstance(pdata.get("graphic_hue_pairs"),list)
            and pdata.get("graphic_hue_pairs")
        ):
            newr["graphic_hue_pairs"]=[
                {
                    "graphic":int(p["graphic"]),
                    "hue":int(p["hue"]),
                }
                for p in pdata["graphic_hue_pairs"]
                if isinstance(p,dict)
                and "graphic" in p
                and "hue" in p
            ]

        gv=parse_num(get_text(fields["graphic"]))
        hv=parse_num(get_text(fields["hue"]))

        if gv is not None:
            newr["graphic"]=gv
            newr.pop("graphics",None)
            newr.pop("graphic_hue_pairs",None)

        if hv is not None:
            newr["hue"]=hv

        return newr

    def test_rule():
        test_rule_=build_rule_from_editor()
        set_status("Target an item to test this rule.")
        try:s=API.RequestTarget()
        except:s=0

        item=find_item(s)
        if not item:return

        opl=item_opl(item)
        passed,lines=explain_rule_match(item,opl,test_rule_)

        API.SysMsg("---- RULE TEST: {} ----".format(test_rule_["name"]),66)

        for line_ in lines:
            API.SysMsg(line_,68 if "PASS" in line_ else 33)

        API.SysMsg(
            "RESULT: "+("MATCH" if passed else "NO MATCH"),
            68 if passed else 33
        )

        try:
            API.HeadMsg(
                "MATCH" if passed else "NO MATCH",
                API.Player,
                68 if passed else 33
            )
        except:
            pass

    def save_editor():
        newr=build_rule_from_editor()

        if rule_id:
            for i,r in enumerate(RULES):
                if r["id"]==rule_id:
                    RULES[i]=newr
                    break
        else:
            RULES.append(newr)

        save_gump_position(g,KEY_EDITOR_X,KEY_EDITOR_Y)
        save_rules()
        dispose(g)
        refresh_main()
        set_status("Rule saved: "+newr["name"])

    # Bottom action bar
    actions=API.CreateGumpColorBox(0.42,C_PANEL)
    actions.SetRect(10,610,W-20,100)
    g.Add(actions)

    target_b=API.CreateSimpleButton("[TARGET ITEM]",112,26)
    target_b.SetPos(22,623)
    API.AddControlOnClick(target_b,target_item_seed)
    g.Add(target_b)

    test_b=API.CreateSimpleButton("[TEST RULE]",105,26)
    test_b.SetPos(140,623)
    API.AddControlOnClick(test_b,test_rule)
    g.Add(test_b)

    clear_props=API.CreateSimpleButton("[CLEAR PROPS]",112,26)
    clear_props.SetPos(251,623)
    def clear_properties():
        state["conditions"]=[]
        update_conditions()
    API.AddControlOnClick(clear_props,clear_properties)
    g.Add(clear_props)

    help_lab=label(
        "Tip: use the [X] beside one property to remove only that property.",
        10,C_MUTED,"left",480
    )
    help_lab.SetRect(375,629,480,17)
    g.Add(help_lab)

    save_b=API.CreateSimpleButton("[SAVE RULE]",130,30)
    save_b.SetPos(270,666)
    API.AddControlOnClick(save_b,save_editor)
    g.Add(save_b)

    def cancel_editor():
        save_gump_position(g,KEY_EDITOR_X,KEY_EDITOR_Y)
        dispose(g)

    cancel_b=API.CreateSimpleButton("[CANCEL]",110,30)
    cancel_b.SetPos(505,666)
    API.AddControlOnClick(cancel_b,cancel_editor)
    g.Add(cancel_b)

    _editor_gump=g
    API.AddGump(g)

def set_default_bag():
    global _default_bag
    set_status("Target the DEFAULT loot bag.")
    try:
        s=API.RequestTarget()
    except:
        s=0
    if s and find_item(s):
        _default_bag=int(s)
        pset(KEY_DEFAULT_BAG,str(_default_bag))
        autosave_settings()
        refresh_main()
        set_status("Default loot bag saved.")

def toggle_compact():
    global _compact_mode
    _compact_mode=not _compact_mode
    pset(KEY_COMPACT,"1" if _compact_mode else "0")
    autosave_settings()
    refresh_main()


# ============================================================
# Main callbacks
# ============================================================

def toggle_auto():
    global _auto_loot
    _auto_loot=not _auto_loot
    pset(KEY_AUTO,"1" if _auto_loot else "0")
    autosave_settings()
    refresh_main()

def toggle_pause():
    global _paused
    _paused=not _paused
    set_status("Paused." if _paused else "Resumed.")

def manual_loot():
    set_status("Target corpse/container.")
    try:s=API.RequestTarget()
    except:s=0
    if s:
        a,b,c=loot_container(s,False)
        set_status("Manual: {} matched, {} moved, {} failed.".format(a,b,c))

def clear_corpses():
    _processed_corpses.clear()
    clear_corpse_colors()
    try:
        API.ClearIgnoreList()
    except:
        pass
    set_status("Corpse ignore list cleared and corpse colors restored.")

def close_all():
    global _stop_requested
    _stop_requested=True
    save_gump_position(_editor_gump,KEY_EDITOR_X,KEY_EDITOR_Y)
    save_gump_position(_main_gump,KEY_MAIN_X,KEY_MAIN_Y)
    dispose(_editor_gump)
    dispose(_main_gump)
    try:API.Stop()
    except:pass


# ============================================================
# Start
# ============================================================

load_rules()
_auto_loot=load_bool(KEY_AUTO,True)
_default_bag=0
try:
    _default_bag=int(pget(KEY_DEFAULT_BAG,"0"))
except:
    _default_bag=0
_compact_mode=load_bool(KEY_COMPACT,False)
_mark_corpses=load_bool(KEY_MARK_CORPSES,True)
try:
    _mark_corpse_hue=int(pget(KEY_MARK_HUE,"73"))
except:
    _mark_corpse_hue=73
try:
    _corpse_display_mode=str(pget(KEY_CORPSE_DISPLAY,"Color") or "Color").title()
except:
    _corpse_display_mode="Color"
if _corpse_display_mode not in CORPSE_DISPLAY_OPTIONS:
    _corpse_display_mode="Color"

try:
    _loot_speed=str(pget(KEY_LOOT_SPEED,"Fast") or "Fast").title()
except:
    _loot_speed="Fast"
if _loot_speed not in LOOT_SPEED_OPTIONS:
    _loot_speed="Fast"
apply_loot_speed(_loot_speed, False)

_first_run = not os.path.exists(settings_path())

# Revision-independent settings file wins when present.
loaded_from_file = import_settings(True)

# If this is the first version using the JSON file, create it immediately
# from the existing persistent configuration so nothing needs re-entering.
if not loaded_from_file:
    autosave_settings()

# Public-release first-run safety:
# do not begin moving loot until the user explicitly chooses a destination.
if _first_run and not valid_bag(_default_bag):
    _auto_loot=False
    pset(KEY_AUTO,"0")
    autosave_settings()

refresh_main()
API.SysMsg("J.C.S. Lootmaster Reforged v{} started.".format(VERSION),66)

if _first_run and not valid_bag(_default_bag):
    set_status("FIRST RUN: click DEFAULT and target your loot bag. Auto loot is OFF.")
    API.SysMsg("Lootmaster FIRST RUN: set DEFAULT loot bag, then enable AUTO.",53)
    try:
        API.HeadMsg("Set DEFAULT loot bag before enabling AUTO",API.Player,53)
    except:
        pass
elif loaded_from_file:
    set_status("Loaded settings | Speed: {}".format(_loot_speed))
else:
    set_status("Settings created | Speed: {}".format(_loot_speed))

_was_dead=False
while not API.StopRequested and not _stop_requested:
    API.ProcessCallbacks()

    dead=player_is_dead()
    if dead:
        if not _was_dead:
            set_status("Dead - auto looting paused.")
            _was_dead=True
        API.Pause(0.25)
        continue
    elif _was_dead:
        _was_dead=False
        set_status("Alive - auto looting resumed.")

    if _auto_loot and not _paused:
        try:
            auto_loot_once()
        except Exception as e:
            API.SysMsg("Lootmaster engine error: "+str(e),33)
            API.Pause(0.50)

    API.Pause(LOOP_DELAY)
