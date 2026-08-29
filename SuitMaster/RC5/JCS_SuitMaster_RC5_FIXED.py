import API
import re
import json
import os
import time
import base64
import copy
try:
    import zlib
except:
    zlib = None

# RELEASE CANDIDATE 5 - PUBLIC TEST BUILD
# ============================================================
# J.C.S. SUITMASTER - ALPHA 2.2
# Native TazUO / Legion suit optimizer
#
# PURPOSE
#   Scan a storage chest full of equipment, read item properties,
#   classify wearable slots, build the best available suit for a
#   selected build profile, and pull that suit into a chosen bag.
#
# BUILD PROFILES
#   Basher, Sampire, Blood Knight, Blood Tamer, Mage, Luck Dexer/Caster, Tamers, Mystic Tank, Custom
#
# 2.2 HIGHLIGHTS
#   - Basher whole-suit targets updated from the InsaneUO Shield Bash guide.
#   - Dynamic LMC cap awareness for studded / bone / stone armor.
#   - Soul Charge shield recognition and scoring.
#   - Optional accessory layers expanded for InsaneUO artifact-heavy suits.
#   - UI wording / spacing polished for the first public test release.
#   - RC5: Toggleable Keep Suit Medable profile rule (plain leather or Mage Armor).
#   - 2.2i: Safe 1-3 suit result handling and optimizer time/expansion guards.
#   - 2.2f: Fix editor overflow with paged sections; hide Profiles gump during player inspection.
#   - 2.2d: build scanner, visible-player gear import, flexible equipment skill budget, full share payload.
#   - 2.2c: sectioned profile editor, Luck Dexer/Caster split, Blood Tamer restored.
#
# LOOTMASTER INTEGRATION
#   Writes JCS_SuitMaster_Wanted.json describing current suit
#   deficiencies / useful upgrade properties. LootMaster support
#   can consume this file in a later integration pass.
#
# PLATFORM
#   TazUO Legion Scripting Engine. Not Razor Enhanced.
# ============================================================

VERSION = "RC5"

# ----------------------------
# Files / persistence
# ----------------------------
SETTINGS_FILE = "JCS_SuitMaster_Settings.json"
CACHE_FILE = "JCS_SuitMaster_Cache.json"
WANTED_FILE = "JCS_SuitMaster_Wanted.json"
ACTIVE_SUIT_FILE = "JCS_SuitMaster_ActiveSuit.json"
PROFILES_FILE = "JCS_SuitMaster_Profiles.json"

KEY_CHEST = "JCS_SuitMaster_Chest"  # legacy single-chest key
KEY_CHESTS = "JCS_SuitMaster_Chests"
KEY_PULL_BAG = "JCS_SuitMaster_PullBag"
KEY_MANNEQUIN = "JCS_SuitMaster_Mannequin"
KEY_BUILD = "JCS_SuitMaster_Build"
KEY_X = "JCS_SuitMaster_X"
KEY_Y = "JCS_SuitMaster_Y"

# ----------------------------
# Colors
# ----------------------------
C_BG = "#1D1A17"
C_PANEL = "#29231D"
C_TITLE = "#D2691E"
C_TEXT = "#E7E1D8"
C_MUTED = "#A49B90"
C_GREEN = "#65C466"
C_RED = "#E2675D"
C_GOLD = "#D7AA45"

# ----------------------------
# Scan / move timing
# ----------------------------
OPL_TIMEOUT = 2
OPL_BATCH_PAUSE = 0.12
MOVE_PAUSE = 0.60

# ----------------------------
# Slots
# ----------------------------
SLOTS = [
    "Head",
    "Neck",
    "Arms",
    "Hands",
    "Chest",
    "Legs",
    "Ring",
    "Bracelet",
    "Earrings",
    "Talisman",
    "Belt",
    "Sash",
    "Robe",
    "Back",
    "Shield",
]

CORE_SLOTS = (
    "Head", "Neck", "Arms", "Hands", "Chest", "Legs", "Ring", "Bracelet"
)

# InsaneUO has several artifact-heavy accessory layers. They are included when
# found in the scan, but a missing optional layer never prevents optimization.
OPTIONAL_SLOTS = ("Earrings", "Talisman", "Belt", "Sash", "Robe", "Back", "Shield")

# ----------------------------
# Numeric properties
# ----------------------------
PROPERTIES = [
    "Physical Resist",
    "Fire Resist",
    "Cold Resist",
    "Poison Resist",
    "Energy Resist",
    "Hit Chance Increase",
    "Defense Chance Increase",
    "Damage Increase",
    "Swing Speed Increase",
    "Lower Mana Cost",
    "Lower Reagent Cost",
    "Faster Casting",
    "Faster Cast Recovery",
    "Spell Damage Increase",
    "Hit Point Increase",
    "Stamina Increase",
    "Mana Increase",
    "Hit Point Regeneration",
    "Stamina Regeneration",
    "Mana Regeneration",
    "Strength Bonus",
    "Dexterity Bonus",
    "Intelligence Bonus",
    "Luck",
    "Enhance Potions",
    "Reflect Physical Damage",
    "Casting Focus",
    "Archery",
    "Swordsmanship",
    "Animal Taming",
    "Animal Lore",
    "Veterinary",
    "Chivalry",
    "Peacemaking",
    "Discordance",
    "Musicianship",
    "Bushido",
    "Anatomy",
    "Healing",
    "Spellweaving",
    "Magery",
    "Mysticism",
    "Necromancy",
    "Spirit Speak",
    "Focus",
    "Parrying",
    "Tactics",
    "Hit Life Leech",
    "Hit Mana Leech",
    "Spell Channeling",
    "Soul Charge",
    "Strength Requirement",
    "Dexterity Requirement",
]


# Skills that can appear as equipment bonuses. The optimizer can treat their
# combined points as a flexible suit-level skill budget instead of requiring
# the exact distribution worn when a profile was scanned.
EQUIPMENT_SKILLS = [
    "Alchemy", "Anatomy", "Animal Lore", "Animal Taming", "Archery",
    "Arms Lore", "Begging", "Blacksmithy", "Bushido", "Camping",
    "Carpentry", "Cartography", "Chivalry", "Cooking", "Detecting Hidden",
    "Discordance", "Evaluating Intelligence", "Fencing", "Fishing", "Focus",
    "Forensic Evaluation", "Healing", "Herding", "Hiding", "Inscription",
    "Item Identification", "Lockpicking", "Lumberjacking", "Mace Fighting",
    "Magery", "Meditation", "Mining", "Musicianship", "Mysticism",
    "Necromancy", "Ninjitsu", "Parrying", "Peacemaking", "Poisoning",
    "Provocation", "Remove Trap", "Resisting Spells", "Snooping",
    "Spellweaving", "Spirit Speak", "Stealing", "Stealth", "Swordsmanship",
    "Tactics", "Tailoring", "Taste Identification", "Throwing", "Tinkering",
    "Tracking", "Veterinary", "Wrestling"
]
for _skill_name in EQUIPMENT_SKILLS:
    if _skill_name not in PROPERTIES:
        PROPERTIES.append(_skill_name)

RESISTS = [
    "Physical Resist",
    "Fire Resist",
    "Cold Resist",
    "Poison Resist",
    "Energy Resist",
]

# Caps here are used for score saturation so huge excess values do not
# distort optimization. They do NOT change actual UO game caps.
SCORE_CAPS = {
    "Physical Resist": 75,
    "Fire Resist": 75,
    "Cold Resist": 75,
    "Poison Resist": 75,
    "Energy Resist": 75,
    "Hit Chance Increase": 45,
    "Defense Chance Increase": 45,
    "Damage Increase": 100,
    "Swing Speed Increase": 60,
    "Lower Mana Cost": 40,
    "Lower Reagent Cost": 100,
    "Faster Casting": 4,
    "Faster Cast Recovery": 6,
    "Spell Damage Increase": 100,
    "Hit Point Increase": 50,
    "Stamina Increase": 50,
    "Mana Increase": 50,
    "Hit Point Regeneration": 20,
    "Stamina Regeneration": 20,
    "Mana Regeneration": 20,
    "Strength Bonus": 30,
    "Dexterity Bonus": 30,
    "Intelligence Bonus": 30,
    "Luck": 1500,
    "Enhance Potions": 50,
    "Reflect Physical Damage": 50,
    "Casting Focus": 20,
    "Archery": 30,
    "Swordsmanship": 30,
    "Animal Taming": 30,
    "Animal Lore": 30,
    "Veterinary": 30,
    "Chivalry": 30,
    "Peacemaking": 30,
    "Discordance": 30,
    "Musicianship": 30,
    "Bushido": 30,
    "Anatomy": 30,
    "Healing": 30,
    "Spellweaving": 30,
    "Magery": 30,
    "Mysticism": 30,
    "Necromancy": 30,
    "Spirit Speak": 30,
    "Focus": 30,
    "Parrying": 30,
    "Tactics": 30,
    "Hit Life Leech": 100,
    "Hit Mana Leech": 100,
    "Spell Channeling": 1,
    "Soul Charge": 1,
}

for _skill_name in EQUIPMENT_SKILLS:
    if _skill_name not in SCORE_CAPS:
        SCORE_CAPS[_skill_name] = 30

# Priorities are 0-5. Requirements are total-suit minimums.
BUILD_PROFILES = {
    "Basher": {
        # InsaneUO Shield Bash Basher. The optimizer treats this as a whole-suit
        # constraint problem rather than a BIS-per-slot shopping list.
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Hit Chance Increase": 45,
            "Damage Increase": 100,
            "Lower Mana Cost": 30,
            "Faster Casting": 3,
            "Faster Cast Recovery": 6,
        },
        "weights": {
            "Hit Chance Increase": 5,
            "Damage Increase": 5,
            "Lower Mana Cost": 5,
            "Stamina Increase": 5,
            "Dexterity Bonus": 5,
            "Faster Casting": 5,
            "Faster Cast Recovery": 5,
            "Strength Bonus": 4,
            "Hit Point Increase": 4,
            "Mana Increase": 3,
            "Defense Chance Increase": 3,
            "Swing Speed Increase": 3,
            "Mana Regeneration": 2,
            "Soul Charge": 3,
            "Chivalry": 1,
            "Parrying": 1,
            "Tactics": 1,
            "Anatomy": 1,
        },
        "shield": True,
    },
    "Sampire": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Lower Mana Cost": 30,
        },
        "weights": {
            "Hit Chance Increase": 5,
            "Defense Chance Increase": 4,
            "Stamina Increase": 5,
            "Dexterity Bonus": 4,
            "Lower Mana Cost": 5,
            "Hit Point Increase": 4,
            "Mana Increase": 3,
            "Damage Increase": 3,
            "Swing Speed Increase": 3,
        },
        "shield": False,
    },
    "Blood Knight": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Lower Mana Cost": 30,
        },
        "weights": {
            "Hit Chance Increase": 5,
            "Defense Chance Increase": 4,
            "Lower Mana Cost": 5,
            "Hit Point Increase": 5,
            "Stamina Increase": 4,
            "Mana Increase": 4,
            "Mana Regeneration": 3,
            "Dexterity Bonus": 3,
            "Strength Bonus": 3,
        },
        "shield": False,
    },
    "Mage": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Lower Mana Cost": 30,
            "Lower Reagent Cost": 100,
        },
        "weights": {
            "Lower Mana Cost": 5,
            "Lower Reagent Cost": 4,
            "Faster Casting": 5,
            "Faster Cast Recovery": 5,
            "Spell Damage Increase": 5,
            "Mana Increase": 5,
            "Mana Regeneration": 4,
            "Defense Chance Increase": 3,
            "Intelligence Bonus": 3,
        },
        "shield": False,
    },
    "Luck Dexer": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Hit Chance Increase": 30,
            "Lower Mana Cost": 30,
        },
        "weights": {
            # Lucky Dexer identity: maximize Luck while strongly protecting SSI.
            "Luck": 5,
            "Swing Speed Increase": 5,
            "Hit Chance Increase": 4,
            "Damage Increase": 3,
            "Lower Mana Cost": 3,
            "Stamina Increase": 3,
            "Dexterity Bonus": 2,
            "Hit Point Increase": 2,
            "Defense Chance Increase": 2,
            "Mana Increase": 1,
        },
        "shield": False,
    },
    "Luck Caster": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Lower Mana Cost": 30,
            "Lower Reagent Cost": 100,
            "Faster Casting": 2,
            "Faster Cast Recovery": 4,
        },
        "weights": {
            "Luck": 5,
            "Lower Mana Cost": 5,
            "Lower Reagent Cost": 5,
            "Faster Casting": 5,
            "Faster Cast Recovery": 5,
            "Spell Damage Increase": 5,
            "Mana Increase": 5,
            "Mana Regeneration": 4,
            "Intelligence Bonus": 4,
            "Defense Chance Increase": 3,
            "Hit Point Increase": 3,
        },
        "shield": False,
    },
    "Blood Tamer": {
        # Julius's Blood Knight / Tamer. Current template uses skill gear to add
        # +15 Tactics, +15 Necromancy and +15 Veterinary.
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Lower Mana Cost": 30,
            "Hit Chance Increase": 30,
        },
        "weights": {
            "Hit Chance Increase": 5,
            "Damage Increase": 5,
            "Swing Speed Increase": 5,
            "Lower Mana Cost": 5,
            "Stamina Increase": 5,
            "Hit Point Increase": 4,
            "Defense Chance Increase": 4,
            "Dexterity Bonus": 4,
            "Mana Increase": 4,
            "Mana Regeneration": 3,
            "Hit Life Leech": 5,
            "Hit Mana Leech": 5,
            "Animal Taming": 3,
            "Animal Lore": 3,
            "Chivalry": 3,
            "Swordsmanship": 2,
        },
        "shield": False,
    },
    "Hybrid Tamer": {
        # Based on Slate's InsaneUO hybrid Tamer / Sampire / Whammy concept.
        # Pet tanks and supplies Discord / elemental resist debuffs while the
        # player contributes sustained melee damage and self-healing.
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Lower Mana Cost": 30,
            "Hit Chance Increase": 30,
        },
        "weights": {
            "Hit Chance Increase": 5,
            "Damage Increase": 5,
            "Swing Speed Increase": 5,
            "Lower Mana Cost": 5,
            "Stamina Increase": 5,
            "Hit Point Increase": 4,
            "Defense Chance Increase": 4,
            "Dexterity Bonus": 4,
            "Strength Bonus": 4,
            "Mana Increase": 3,
            "Mana Regeneration": 2,
            "Hit Life Leech": 5,
            "Hit Mana Leech": 5,
            "Animal Taming": 4,
            "Animal Lore": 4,
            "Veterinary": 4,
            "Parrying": 4,
            "Bushido": 3,
            "Spirit Speak": 3,
            "Necromancy": 3,
            "Tactics": 3,
        },
        "shield": False,
    },
    "Mystic Tank": {
        # Based on Pevil's InsaneUO Mystic Tank Discord build.
        # Primary role: survival/tanking in Stone Form, with melee damage and
        # enough casting support to use Mysticism utility reliably.
        "requirements": {
            "Physical Resist": 74,
            "Fire Resist": 74,
            "Cold Resist": 70,
            "Poison Resist": 74,
            "Energy Resist": 74,
            "Lower Mana Cost": 30,
        },
        "weights": {
            "Lower Mana Cost": 5,
            "Stamina Increase": 5,
            "Reflect Physical Damage": 5,
            "Hit Point Increase": 4,
            "Defense Chance Increase": 4,
            "Lower Reagent Cost": 4,
            "Faster Casting": 3,
            "Faster Cast Recovery": 3,
            "Strength Bonus": 4,
            "Dexterity Bonus": 4,
            "Intelligence Bonus": 2,
            "Mana Increase": 3,
            "Hit Life Leech": 5,
            "Hit Mana Leech": 5,
            "Mysticism": 4,
            "Focus": 4,
            "Parrying": 4,
            "Anatomy": 2,
            "Tactics": 2,
            "Healing": 2,
            "Spell Channeling": 2,
        },
        "shield": True,
    },
    "Necro Weaver Tamer": {
        # Based on Wolfsun's updated InsaneUO Necro / Weaver / Tamer Discord build.
        # Confirmed gear emphasis from the discussion: very high Spell Damage Increase,
        # with the pet providing the frontline while the character contributes caster damage.
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Lower Mana Cost": 30,
            "Lower Reagent Cost": 100,
        },
        "weights": {
            "Spell Damage Increase": 5,
            "Lower Mana Cost": 5,
            "Mana Increase": 5,
            "Mana Regeneration": 5,
            "Faster Casting": 4,
            "Faster Cast Recovery": 4,
            "Intelligence Bonus": 4,
            "Hit Point Increase": 3,
            "Defense Chance Increase": 2,
            "Necromancy": 4,
            "Spellweaving": 4,
            "Animal Taming": 3,
            "Animal Lore": 3,
            "Veterinary": 2,
            "Spirit Speak": 3,
            "Luck": 2,
        },
        "shield": False,
    },
    "Archer Tamer": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
            "Lower Mana Cost": 40,
            "Hit Chance Increase": 30,
        },
        "weights": {
            "Hit Chance Increase": 5,
            "Swing Speed Increase": 5,
            "Damage Increase": 5,
            "Lower Mana Cost": 5,
            "Stamina Increase": 5,
            "Mana Increase": 4,
            "Dexterity Bonus": 3,
            "Strength Bonus": 3,
            "Luck": 3,
            "Peacemaking": 4,
            "Animal Taming": 3,
            "Animal Lore": 3,
            "Archery": 5,
            "Chivalry": 2,
            "Veterinary": 2,
            "Discordance": 2,
        },
        "shield": False,
    },
    "Custom": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
        },
        "weights": {
            "Hit Chance Increase": 5,
            "Defense Chance Increase": 5,
            "Lower Mana Cost": 5,
            "Stamina Increase": 4,
            "Hit Point Increase": 4,
            "Mana Increase": 3,
        },
        "shield": False,
    },
}

BUILD_NAMES = ["Basher", "Sampire", "Blood Knight", "Blood Tamer", "Mage", "Luck Dexer", "Luck Caster", "Hybrid Tamer", "Mystic Tank", "Necro Weaver Tamer", "Archer Tamer", "Custom"]

# Properties shown in the first Custom editor.
CUSTOM_EDIT_PROPS = [
    "Hit Chance Increase",
    "Defense Chance Increase",
    "Lower Mana Cost",
    "Stamina Increase",
    "Hit Point Increase",
    "Mana Increase",
    "Dexterity Bonus",
    "Strength Bonus",
    "Damage Increase",
    "Swing Speed Increase",
    "Faster Casting",
    "Faster Cast Recovery",
    "Spell Damage Increase",
    "Luck",
]

_chests = []
_pull_bag = 0
_mannequin = 0
_build = "Basher"
_items = []
_best = None
_status = "Set an equipment chest, then scan."
_main_gump = None
_mini_gump = None
_editor_gump = None


# ============================================================
# API / persistence helpers
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


def request_target(prompt):
    """
    Reliable Legion targeting helper.
    Some builds do not show a cursor when RequestTarget is called directly
    from a gump click callback. Briefly yield first, then request the target.
    """
    try:
        API.SysMsg(str(prompt), 68)
    except:
        pass

    try:
        API.Pause(0.10)
    except:
        pass

    try:
        s = API.RequestTarget()
        return int(s or 0)
    except:
        return 0


def save_chests():
    pset(KEY_CHESTS, json.dumps([int(x) for x in _chests if int(x or 0)]))


def load_chests():
    out = []

    # New multi-chest setting.
    try:
        raw = str(pget(KEY_CHESTS, "[]") or "[]")
        vals = json.loads(raw)
        if isinstance(vals, list):
            for x in vals:
                try:
                    s = int(x or 0)
                    if s and s not in out:
                        out.append(s)
                except:
                    pass
    except:
        pass

    # Migrate old single chest if needed.
    if not out:
        try:
            legacy = int(pget(KEY_CHEST, "0") or 0)
            if legacy:
                out.append(legacy)
        except:
            pass

    return out


def serial(item):
    try:
        return int(item.Serial)
    except:
        try:
            return int(item)
        except:
            return 0


def item_name(item):
    if isinstance(item, dict):
        try:
            n = str(item.get("name", "") or "").strip()
            if n:
                return n
        except:
            pass

    try:
        n = str(item.Name or "").strip()
        if n:
            return n
    except:
        pass
    try:
        s = serial(item)
        t = API.ItemNameAndProps(s, False, 1)
        if t:
            return str(t).split("\n")[0].strip()
    except:
        pass
    return "Unknown Item"


def item_layer(item):
    try:
        return str(item.Layer or "")
    except:
        return ""


def item_graphic(item):
    try:
        return int(item.Graphic)
    except:
        return 0


def item_hue(item):
    try:
        return int(item.Hue)
    except:
        return 0


def item_container(item):
    try:
        return int(item.Container or 0)
    except:
        if isinstance(item, dict):
            try:
                return int(item.get("source_container", 0) or 0)
            except:
                pass
        return 0


def item_opl(item):
    s = serial(item)
    try:
        t = API.ItemNameAndProps(s, True, OPL_TIMEOUT)
        if t:
            return str(t)
    except:
        pass
    return item_name(item)


def recursive_items(container_serial):
    try:
        x = API.ItemsInContainer(int(container_serial), True)
        return list(x) if x else []
    except:
        return []


def set_status(text, hue=None):
    global _status
    _status = str(text)
    try:
        API.SysMsg(_status, 68 if hue is None else hue)
    except:
        pass


def script_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except:
        return "."


def file_path(name):
    return os.path.join(script_dir(), name)


def safe_write_json(path, payload):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    if os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass
    os.rename(tmp, path)


# ============================================================
# Property parsing
# ============================================================

def normalize_text(text):
    return str(text or "").replace("\r", "")


def parse_number(opl, prop):
    # Handles:
    # Hit Chance Increase 15%
    # Hit Chance Increase: 15%
    # Dexterity Bonus +5
    pattern = r"(?im)^\s*" + re.escape(prop) + r"\s*(?:[:+]\s*)?([-+]?\d+)\s*%?\s*$"
    m = re.search(pattern, normalize_text(opl))
    if not m:
        return 0
    try:
        return int(m.group(1))
    except:
        return 0


def parse_props(opl):
    d = {}
    for p in PROPERTIES:
        d[p] = parse_number(opl, p)

    # Soul Charge is commonly exposed as a named shield property rather than
    # a numeric modifier. Store it as a boolean-like 1 for scoring/profile use.
    if "soul charge" in normalize_text(opl).lower():
        d["Soul Charge"] = max(1, int(d.get("Soul Charge", 0) or 0))

    return d


def armor_lmc_traits(item):
    """Return (implicit_lmc, cap_bonus, material_label) for armor material."""
    slot = str(item.get("slot", "") if isinstance(item, dict) else "")
    if slot not in ("Head", "Neck", "Arms", "Hands", "Chest", "Legs"):
        return 0, 0, ""

    if isinstance(item, dict):
        text = (str(item.get("name", "")) + "\n" + str(item.get("opl", ""))).lower()
    else:
        text = (item_name(item) + "\n" + item_opl(item)).lower()

    # InsaneUO Shield Bash guide: studded / bone / stone armor carries 3 LMC
    # and raises the LMC cap by 3 per qualifying piece, to a 55 maximum.
    high_terms = (
        "studded", "bone armor", "bone helm", "bone gloves", "bone arms",
        "bone legs", "stone armor", "stone helm", "stone gloves",
        "stone arms", "stone legs",
    )
    if any(term in text for term in high_terms):
        if "studded" in text:
            label = "Studded"
        elif "bone" in text:
            label = "Bone"
        else:
            label = "Stone"
        return 3, 3, label

    # Plate / ringmail / chainmail have 1 inherent LMC but do not expand the cap.
    low_terms = ("platemail", "plate ", "plate armor", "ringmail", "chainmail")
    if any(term in text for term in low_terms):
        return 1, 0, "Metal"

    return 0, 0, ""


def item_is_medable(item):
    """Return True if an equipped armor piece will preserve Meditation.

    Mage Armor always permits the piece. Naturally medable armor is allowed.
    Studded, bone, stone, ringmail, chainmail and plate families are rejected
    unless Mage Armor is present. Non-armor/accessory slots do not affect this
    rule and are always allowed.
    """
    if not isinstance(item, dict):
        return True

    slot = str(item.get("slot", "") or "")
    if slot not in ("Head", "Neck", "Arms", "Hands", "Chest", "Legs"):
        return True

    name = str(item.get("name", "") or "")
    opl = str(item.get("opl", "") or "")
    text = (name + "\n" + opl).lower()

    # Mage Armor overrides the base armor family's Meditation restriction.
    if "mage armor" in text or "mage armour" in text:
        return True

    # Reuse SuitMaster's existing material detector. These families are not
    # naturally medable and must never enter a medable suit without Mage Armor.
    _implicit_lmc, _cap_bonus, material = armor_lmc_traits(item)
    if material in ("Metal", "Studded", "Bone", "Stone"):
        return False

    # Explicit non-medable families that may not be caught by LMC inference.
    non_medable_terms = (
        "ringmail", "ring mail", "chainmail", "chain mail", "platemail",
        "plate armor", "plate armour", "plate helm", "studded",
        "bone armor", "bone armour", "bone helm", "bone gloves",
        "bone arms", "bone legs", "dragon armor", "dragon armour",
        "dragon helm", "woodland", "stone armor", "stone armour",
        "stone helm", "gargish stone", "gargoyle stone", "hide armor",
        "hide armour",
    )
    if any(term in text for term in non_medable_terms):
        return False

    # Naturally medable armor/headwear families.
    medable_terms = (
        "leather", "leaf", "gargoyle cloth", "gargish cloth",
        "circlet", "elven glasses", "hat", "cap", "hood", "bandana",
        "skullcap", "wizard hat", "wizard's hat", "mask", "jingasa",
    )
    if "studded" not in text and any(term in text for term in medable_terms):
        return True

    # Conservative fallback: unknown body armor is excluded rather than risk
    # silently breaking Meditation.
    return False


def effective_item_props(item):
    """Properties used by the optimizer, including safe inferred IUO traits."""
    props = dict(item.get("props", {}) if isinstance(item, dict) else {})
    opl = str(item.get("opl", "") if isinstance(item, dict) else "")

    implicit_lmc, _, _ = armor_lmc_traits(item)
    # Do not double-count if Legion already exposes inherent LMC in the OPL.
    if implicit_lmc and "lower mana cost" not in opl.lower():
        props["Lower Mana Cost"] = int(props.get("Lower Mana Cost", 0) or 0) + implicit_lmc

    if "soul charge" in opl.lower():
        props["Soul Charge"] = max(1, int(props.get("Soul Charge", 0) or 0))

    return props


def suit_lmc_state(chosen, totals):
    base_cap = 40
    cap_bonus = 0
    material_pieces = []

    for item in chosen or []:
        _, bonus, label = armor_lmc_traits(item)
        if bonus:
            cap_bonus += int(bonus)
            material_pieces.append({
                "slot": item.get("slot"),
                "name": item.get("name"),
                "material": label,
                "cap_bonus": int(bonus),
            })

    cap = min(55, base_cap + cap_bonus)
    raw_lmc = max(0, int((totals or {}).get("Lower Mana Cost", 0) or 0))
    return {
        "raw_lmc": raw_lmc,
        "effective_lmc": min(raw_lmc, cap),
        "base_cap": base_cap,
        "cap_bonus": min(15, cap_bonus),
        "cap": cap,
        "material_pieces": material_pieces,
    }


# ============================================================
# Slot classification
# ============================================================

def classify_slot(item, opl):
    # Slot safety rule:
    #   1) known shard artifact names
    #   2) Legion's actual equipment layer
    #   3) conservative ITEM-NAME fallback only
    # Never use the full OPL/tooltip to infer a slot; property text can contain
    # unrelated words and cause a perfectly valid item to be assigned elsewhere.
    layer = item_layer(item).lower().replace(" ", "")
    name = item_name(item).lower().strip()

    # Narrow InsaneUO artifact exceptions whose real wearable layer is known.
    # Keep these exact/specific; do not use broad words such as "wing" here.
    if "tunic of vigor" in name:
        return "Sash"
    if "dragon's wing" in name or "dragons wing" in name:
        return "Back"
    if "epaulette" in name:
        return "Robe"

    # Prefer Legion's reported wearable layer whenever it is recognizable.
    layer_map = {
        "head": "Head",
        "helmet": "Head",
        "neck": "Neck",
        "gloves": "Hands",
        "hands": "Hands",
        "arms": "Arms",
        "outertorso": "Robe",
        "robe": "Robe",
        "cloak": "Back",
        "earrings": "Earrings",
        "earring": "Earrings",
        "waist": "Belt",
        "middletorso": "Chest",
        "innertorso": "Chest",
        "shirt": "Chest",
        "outerlegs": "Legs",
        "innerlegs": "Legs",
        "pants": "Legs",
        "ring": "Ring",
        "bracelet": "Bracelet",
        "talisman": "Talisman",
    }
    for key, slot in layer_map.items():
        if key in layer:
            return slot

    # Shields may expose only a generic hand layer, so use a conservative
    # item-name check after trying the real layer.
    shield_words = (
        "shield", "buckler", "heater shield", "kite shield",
        "wooden shield", "metal shield", "order shield", "chaos shield"
    )
    if any(x in name for x in shield_words):
        return "Shield"

    # Conservative name-only fallbacks for items whose layer is unavailable.
    if "bracelet" in name:
        return "Bracelet"
    if re.search(r"\bring\b", name):
        return "Ring"
    if "talisman" in name:
        return "Talisman"
    if "earring" in name:
        return "Earrings"
    if "sash" in name:
        return "Sash"
    if "belt" in name or "cincture" in name:
        return "Belt"
    if "cloak" in name:
        return "Back"
    if "robe" in name:
        return "Robe"

    # Armor fallbacks. Head is checked before any broad torso wording so names
    # such as "Winged Helm" can never become Back gear.
    if any(x in name for x in ("helmet", "helm", "cap", "hat", "cowl", "circlet")):
        return "Head"
    if "gorget" in name:
        return "Neck"
    if any(x in name for x in ("gloves", "gauntlets", "mitts")):
        return "Hands"
    if any(x in name for x in ("sleeves", "arm guards", "arm armor", "arm armour")):
        return "Arms"
    if any(x in name for x in ("leggings", "leg armor", "leg armour", "pants", "kilt")):
        return "Legs"
    if any(x in name for x in (
        "tunic", "chest", "breastplate", "armor", "armour", "jacket", "shirt"
    )):
        return "Chest"

    # Unknown/ambiguous equipment is safer to ignore than to put in a wrong slot.
    return None


# ============================================================
# Race compatibility
# ============================================================

def player_race():
    """
    Return a simple race label used by SuitMaster.
    Legion exposes IsGargoyle directly. Elf detection is not always
    exposed consistently, so non-gargoyle characters default to Human
    unless an explicit API property becomes available.
    """
    try:
        if bool(API.Player.IsGargoyle):
            return "Gargoyle"
    except:
        pass

    # Some Legion/TazUO builds may expose IsElf.
    try:
        if bool(API.Player.IsElf):
            return "Elf"
    except:
        pass

    return "Human"


def item_race_compatible(item, opl):
    """
    Reject equipment the current character cannot wear.

    Primary source: tooltip restrictions such as:
      Gargoyles Only
      Elves Only
      Humans Only

    Fallback: Gargish/Gargoyle armor naming, because some custom/artifact
    items may not expose the restriction consistently in cached OPL data.
    """
    race = player_race()
    text = (str(opl or "") + "\n" + item_name(item)).lower()

    garg_only = any(x in text for x in (
        "gargoyles only",
        "gargoyle only",
        "gargoyle-only",
        "gargoyles-only",
    ))

    elf_only = any(x in text for x in (
        "elves only",
        "elf only",
        "elf-only",
        "elves-only",
    ))

    human_only = any(x in text for x in (
        "humans only",
        "human only",
        "human-only",
        "humans-only",
    ))

    # Strong fallback for gargoyle-specific equipment names.
    garg_name = any(x in text for x in (
        "gargish ",
        "gargoyle ",
    ))

    if race == "Gargoyle":
        if elf_only or human_only:
            return False
        return True

    if race == "Elf":
        if garg_only or human_only or garg_name:
            return False
        return True

    # Human
    if garg_only or elf_only or garg_name:
        return False

    return True


# ============================================================
# Inventory scanning / caching
# ============================================================

def scan_chest():
    global _items, _best

    if not _chests:
        set_status("Add at least one equipment chest first.", 33)
        return False

    raw_all = []
    seen_serials = set()
    source_chest_by_serial = {}
    chest_counts = []

    for chest_serial in list(_chests):
        if API.StopRequested:
            break

        try:
            API.UseObject(int(chest_serial))
            API.Pause(0.30)
        except:
            pass

        raw = recursive_items(chest_serial)
        chest_counts.append((int(chest_serial), len(raw)))

        for item in raw:
            s = serial(item)
            if s and s not in seen_serials:
                seen_serials.add(s)
                source_chest_by_serial[s] = int(chest_serial)
                raw_all.append(item)

    if not raw_all:
        set_status("No items found in the configured gear chests.", 33)
        return False

    try:
        ss = [serial(i) for i in raw_all if serial(i)]
        if ss:
            # Large collections can be friendlier to Legion in batches.
            BATCH = 100
            for n in range(0, len(ss), BATCH):
                API.RequestOPLData(ss[n:n+BATCH])
                API.Pause(OPL_BATCH_PAUSE)
    except:
        pass

    found = []
    by_slot = {}
    ignored = 0

    for i, item in enumerate(raw_all):
        if API.StopRequested:
            break

        opl = item_opl(item)

        # Never allow race-incompatible equipment into the optimizer.
        if not item_race_compatible(item, opl):
            ignored += 1
            continue

        slot = classify_slot(item, opl)
        if slot not in SLOTS:
            ignored += 1
            continue

        entry = {
            "serial": serial(item),
            "name": item_name(item),
            "slot": slot,
            "graphic": item_graphic(item),
            "hue": item_hue(item),
            "layer": item_layer(item),
            "source_chest": int(source_chest_by_serial.get(serial(item), 0) or 0),
            "source_container": int(item_container(item) or source_chest_by_serial.get(serial(item), 0) or 0),
            "props": parse_props(opl),
            "opl": opl,
        }
        found.append(entry)
        by_slot[slot] = by_slot.get(slot, 0) + 1

        if i % 25 == 0:
            try:
                API.Pause(0.01)
            except:
                pass

    _items = found
    _best = None

    payload = {
        "version": VERSION,
        "race": player_race(),
        "chests": [int(x) for x in _chests],
        "scanned_at": int(time.time()),
        "items": _items,
    }
    try:
        safe_write_json(file_path(CACHE_FILE), payload)
    except Exception as e:
        set_status("Scan finished, but cache write failed: " + str(e), 33)

    summary = ", ".join("{} {}".format(k, by_slot[k]) for k in SLOTS if by_slot.get(k))
    set_status(
        "Scanned {} chest(s) for {} gear, {} wearable items. {}".format(
            len(_chests), player_race(), len(found), summary or "No classified gear."
        ),
        68
    )
    refresh_main()
    return True

def load_cache():
    global _items
    path = file_path(CACHE_FILE)
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r") as f:
            d = json.load(f)
        data = d.get("items", [])
        if isinstance(data, list):
            _items = data
            return True
    except:
        pass
    return False


# ============================================================
# Optimizer
# ============================================================

def active_profile():
    base = BUILD_PROFILES.get(_build, BUILD_PROFILES["Basher"])
    return {
        "requirements": dict(base.get("requirements", {})),
        "weights": dict(base.get("weights", {})),
        "shield": bool(base.get("shield", False)),
    }


def suit_totals(chosen):
    totals = dict((p, 0) for p in PROPERTIES)
    for item in chosen:
        props = effective_item_props(item)
        for p in PROPERTIES:
            try:
                totals[p] += int(props.get(p, 0) or 0)
            except:
                pass
    return totals


def requirement_deficits(totals, requirements):
    out = {}
    for p, minimum in requirements.items():
        actual = int(totals.get(p, 0) or 0)
        if actual < int(minimum):
            out[p] = int(minimum) - actual
    return out


def score_totals(totals, profile):
    reqs = profile["requirements"]
    weights = profile["weights"]

    score = 0.0

    # Requirements dominate.
    for p, minimum in reqs.items():
        actual = int(totals.get(p, 0) or 0)
        minimum = int(minimum)
        if minimum <= 0:
            continue

        reached = min(actual, minimum)
        score += (float(reached) / float(minimum)) * 10000.0

        if actual < minimum:
            # Large linear penalty for being short.
            score -= float(minimum - actual) * 1200.0

    # Preferences decide among suits that satisfy the important requirements.
    for p, weight in weights.items():
        w = int(weight or 0)
        if w <= 0:
            continue
        actual = int(totals.get(p, 0) or 0)
        cap = int(SCORE_CAPS.get(p, max(actual, 1)))
        useful = min(max(actual, 0), cap)
        score += useful * w * 20.0

    return score


def hard_minimum_state(totals, profile):
    """Return hard-minimum validity and normalized shortfall information.

    RC4 treats every configured requirement as a gate. The flexible equipment
    skill budget is also treated as a hard pool minimum when configured.
    """
    deficits = requirement_deficits(totals, profile.get("requirements", {}))
    unmet = len(deficits)
    normalized_shortfall = 0.0

    for prop, minimum in profile.get("requirements", {}).items():
        minimum = int(minimum or 0)
        if minimum <= 0:
            continue
        actual = int(totals.get(prop, 0) or 0)
        if actual < minimum:
            normalized_shortfall += float(minimum - actual) / float(max(1, minimum))

    budget = max(0, int(profile.get("skill_budget", 0) or 0))
    budget_deficit = 0
    if budget > 0:
        actual_budget = sum(
            max(0, int(totals.get(skill_name, 0) or 0))
            for skill_name in EQUIPMENT_SKILLS
        )
        if actual_budget < budget:
            budget_deficit = budget - actual_budget
            unmet += 1
            normalized_shortfall += float(budget_deficit) / float(max(1, budget))

    return {
        "valid": unmet == 0,
        "deficits": deficits,
        "budget_deficit": budget_deficit,
        "unmet_count": unmet,
        "normalized_shortfall": normalized_shortfall,
    }


def item_rough_score(item, profile):
    props = item.get("props", {})
    score = 0.0

    for p, minimum in profile["requirements"].items():
        value = int(props.get(p, 0) or 0)
        score += min(value, int(minimum)) * 80.0

    for p, w in profile["weights"].items():
        value = int(props.get(p, 0) or 0)
        cap = int(SCORE_CAPS.get(p, max(value, 1)))
        score += min(max(value, 0), cap) * int(w or 0) * 10.0

    return score


def prune_candidates(slot_items, profile, limit=30):
    # Keep the most promising items per slot without pruning away pieces that
    # may be necessary to satisfy a configured hard minimum. RC4 explicitly
    # preserves the strongest contributors for every required property before
    # filling the remainder by the normal rough-score heuristic.
    ranked = sorted(
        slot_items,
        key=lambda x: item_rough_score(x, profile),
        reverse=True
    )

    selected = []
    seen = set()

    def keep(item):
        s = int(item.get("serial", 0) or 0)
        if s in seen:
            return
        seen.add(s)
        selected.append(item)

    # Preserve up to two best contributors for each hard-minimum property.
    # This is especially important for low-numeric stats such as FC/FCR, where
    # a resist-heavy item could otherwise dominate rough-score pruning.
    for prop, minimum in profile.get("requirements", {}).items():
        if int(minimum or 0) <= 0:
            continue
        contributors = sorted(
            slot_items,
            key=lambda x: int(effective_item_props(x).get(prop, 0) or 0),
            reverse=True
        )
        kept_for_prop = 0
        for item in contributors:
            value = int(effective_item_props(item).get(prop, 0) or 0)
            if value <= 0:
                break
            keep(item)
            kept_for_prop += 1
            if kept_for_prop >= 2:
                break

    # Fill with the general best candidates. We allow the preserved hard-min
    # pieces to expand the set slightly beyond limit rather than discard them.
    for item in ranked:
        if len(selected) >= int(limit):
            break
        keep(item)

    return selected



# ============================================================
# Equipment stat safety
# ============================================================

EQUIP_DEBUFF_BUFFER = 22

def player_base_stats():
    """
    Estimate naked/base STR/DEX by subtracting equipment stat increases from
    Legion's current total stats. This is intentionally conservative for suit
    building and is used only for equip-requirement safety checks.
    """
    try:
        strength = int(API.Player.Strength)
    except:
        strength = 0
    try:
        dexterity = int(API.Player.Dexterity)
    except:
        dexterity = 0
    try:
        str_inc = int(API.Player.StrengthIncrease)
    except:
        str_inc = 0
    try:
        dex_inc = int(API.Player.DexterityIncrease)
    except:
        dex_inc = 0

    return {
        "strength": max(0, strength - str_inc),
        "dexterity": max(0, dexterity - dex_inc),
        "current_strength": strength,
        "current_dexterity": dexterity,
    }


def equipment_safety(chosen, totals, buffer_amount=EQUIP_DEBUFF_BUFFER):
    base = player_base_stats()

    max_str_req = 0
    max_dex_req = 0
    str_item = ""
    dex_item = ""

    for item in chosen:
        props = item.get("props", {})
        sr = int(props.get("Strength Requirement", 0) or 0)
        dr = int(props.get("Dexterity Requirement", 0) or 0)

        if sr > max_str_req:
            max_str_req = sr
            str_item = item.get("name", "")
        if dr > max_dex_req:
            max_dex_req = dr
            dex_item = item.get("name", "")

    projected_str = int(base["strength"]) + int(totals.get("Strength Bonus", 0) or 0)
    projected_dex = int(base["dexterity"]) + int(totals.get("Dexterity Bonus", 0) or 0)

    safe_str = projected_str - int(buffer_amount)
    safe_dex = projected_dex - int(buffer_amount)

    str_deficit = max(0, max_str_req - safe_str)
    dex_deficit = max(0, max_dex_req - safe_dex)

    return {
        "buffer": int(buffer_amount),
        "base_strength": int(base["strength"]),
        "base_dexterity": int(base["dexterity"]),
        "projected_strength": projected_str,
        "projected_dexterity": projected_dex,
        "safe_strength": safe_str,
        "safe_dexterity": safe_dex,
        "max_strength_requirement": max_str_req,
        "max_dexterity_requirement": max_dex_req,
        "strength_requirement_item": str_item,
        "dexterity_requirement_item": dex_item,
        "strength_deficit": str_deficit,
        "dexterity_deficit": dex_deficit,
        "safe": (str_deficit == 0 and dex_deficit == 0),
    }


def equipment_safety_penalty(chosen, totals):
    info = equipment_safety(chosen, totals)
    if info["safe"]:
        return 0.0

    # Treat failure to remain equippable after a debuff as effectively a hard
    # minimum violation. This dominates normal preference scoring.
    return (
        float(info["strength_deficit"] + info["dexterity_deficit"]) * 1000000.0
        + 10000000.0
    )


def optimize():
    global _best

    if not _items:
        if not load_cache():
            set_status("Scan the equipment chest first.", 33)
            return None

    profile = active_profile()

    by_slot = dict((s, []) for s in SLOTS)
    for item in _items:
        # Re-check cached items so upgrading SuitMaster cannot reuse an old
        # cache containing race-incompatible gear.
        try:
            fake_opl = item.get("opl", "")
            if not item_race_compatible(item, fake_opl):
                continue
        except:
            pass

        if profile.get("medable", False) and not item_is_medable(item):
            continue

        slot = item.get("slot")
        if slot in by_slot:
            by_slot[slot].append(item)

    required_slots = [
        "Head", "Neck", "Arms", "Hands", "Chest", "Legs", "Ring", "Bracelet"
    ]

    if by_slot["Talisman"]:
        required_slots.append("Talisman")

    if profile["shield"]:
        if by_slot["Shield"]:
            required_slots.append("Shield")
        else:
            set_status("Basher profile wants a shield, but no shield was found. Optimizing without one.", 33)

    missing_slots = [s for s in required_slots if not by_slot[s]]
    if missing_slots:
        if profile.get("medable", False):
            set_status("Cannot build complete medable suit. Missing valid: " + ", ".join(missing_slots), 33)
        else:
            set_status("Cannot build complete suit. Missing: " + ", ".join(missing_slots), 33)
        return None

    # Prune large storage collections first.
    candidates = {}
    for slot in required_slots:
        candidates[slot] = prune_candidates(by_slot[slot], profile, 12)

    # Beam search.
    # Each state: (score, chosen_items, totals)
    beam = [(0.0, [], dict((p, 0) for p in PROPERTIES))]
    BEAM_WIDTH = 350

    for slot in required_slots:
        next_beam = []

        for prior_score, chosen, totals in beam:
            for item in candidates[slot]:
                nt = dict(totals)
                props = item.get("props", {})
                for p in PROPERTIES:
                    nt[p] += int(props.get(p, 0) or 0)

                ns = score_totals(nt, profile)
                next_beam.append((ns, chosen + [item], nt))

        if not next_beam:
            set_status("No complete suit can be built from the current scanned gear.", 33)
            return None

        next_beam.sort(key=lambda x: x[0], reverse=True)
        beam = next_beam[:BEAM_WIDTH]


        optimizer_yield()
        optimizer_yield()

        if API.StopRequested:
            return None

    if not beam:
        set_status("No complete suit could be built from the current gear.", 33)
        return None

    # Final re-rank: normal suit score minus a dominating equipment-safety
    # penalty if STR/DEX could fall below an item's requirement after a debuff.
    safe_ranked = []
    for raw_score, chosen_items, suit_totals in beam:
        penalty = equipment_safety_penalty(chosen_items, suit_totals)
        safe_ranked.append((raw_score - penalty, raw_score, chosen_items, suit_totals))

    safe_ranked.sort(key=lambda x: x[0], reverse=True)
    final_score, score, chosen, totals = safe_ranked[0]

    deficits = requirement_deficits(totals, profile["requirements"])
    equip_safety = equipment_safety(chosen, totals)

    _best = {
        "build": _build,
        "score": score,
        "effective_score": final_score,
        "items": chosen,
        "totals": totals,
        "deficits": deficits,
        "equipment_safety": equip_safety,
    }

    write_wanted_file(_best)

    if not equip_safety.get("safe", True):
        parts = []
        if equip_safety.get("strength_deficit", 0):
            parts.append("STR +{}".format(equip_safety["strength_deficit"]))
        if equip_safety.get("dexterity_deficit", 0):
            parts.append("DEX +{}".format(equip_safety["dexterity_deficit"]))
        set_status(
            "Best suit found, but no fully debuff-safe equip combination was available. Need " + ", ".join(parts),
            33
        )
    elif deficits:
        d = ", ".join("{} -{}".format(k, v) for k, v in deficits.items())
        set_status("Best {} suit found; preview opened. Still short: {}".format(_build, d), 53)
    else:
        set_status("Best {} suit found. Preview opened; nothing has been moved yet.".format(_build), 68)

    show_results()
    return _best


# ============================================================
# LootMaster bridge
# ============================================================

def useful_upgrade_properties(best):
    profile = active_profile()
    totals = best.get("totals", {})
    deficits = best.get("deficits", {})

    wanted = []

    # Hard deficits first.
    for p, deficit in deficits.items():
        wanted.append({
            "property": p,
            "reason": "hard_minimum_deficit",
            "needed_total": int(deficit),
            "priority": 5,
        })

    # Then top weighted properties that are not saturated.
    weighted = sorted(
        profile["weights"].items(),
        key=lambda kv: int(kv[1] or 0),
        reverse=True
    )

    for p, weight in weighted:
        if int(weight or 0) <= 0:
            continue
        actual = int(totals.get(p, 0) or 0)
        cap = int(SCORE_CAPS.get(p, actual))
        if actual < cap:
            wanted.append({
                "property": p,
                "reason": "weighted_upgrade",
                "current_total": actual,
                "soft_target": cap,
                "priority": int(weight),
            })

    return wanted


def basher_wanted_traits(best):
    traits = []
    lmc = best.get("lmc_state") or suit_lmc_state(best.get("items", []), best.get("totals", {}))

    if int(lmc.get("cap", 40) or 40) < 55:
        traits.append({
            "trait": "LMC cap-expanding armor",
            "slots": ["Head", "Neck", "Arms", "Hands", "Chest", "Legs"],
            "materials": ["Studded", "Bone", "Stone"],
            "reason": "raise_lmc_cap",
            "current_cap": int(lmc.get("cap", 40) or 40),
            "priority": 5,
        })

    has_soul_charge = False
    for item in best.get("items", []):
        if item.get("slot") == "Shield" and int(effective_item_props(item).get("Soul Charge", 0) or 0) > 0:
            has_soul_charge = True
            break
    if not has_soul_charge:
        traits.append({
            "trait": "Soul Charge",
            "slot": "Shield",
            "reason": "mana_sustain_upgrade",
            "priority": 3,
        })

    return traits


def write_wanted_file(best):
    # First bridge format. LootMaster can later evaluate each new item by
    # replacing the matching slot and asking whether the full-suit score rises.
    payload = {
        "format": 1,
        "source": "JCS SuitMaster",
        "suitmaster_version": VERSION,
        "build": best.get("build"),
        "generated_at": int(time.time()),
        "current_score": best.get("score"),
        "deficits": best.get("deficits", {}),
        "wanted_properties": useful_upgrade_properties(best),
        "swing_state": best.get("swing_state"),
        "lmc_state": best.get("lmc_state"),
        "wanted_traits": basher_wanted_traits(best) if best.get("build") == "Basher" else [],
        "current_suit": [
            {
                "slot": x.get("slot"),
                "serial": x.get("serial"),
                "name": x.get("name"),
                "props": x.get("props", {}),
            }
            for x in best.get("items", [])
        ],
        "integration_note": (
            "LootMaster should test a candidate by replacing the current item in "
            "the same slot and rescoring the whole suit, including swing and LMC-cap state."
        ),
    }
    try:
        safe_write_json(file_path(WANTED_FILE), payload)
    except Exception as e:
        try:
            API.SysMsg("Wanted-list write failed: " + str(e), 33)
        except:
            pass


# ============================================================
# Mannequin placement
# ============================================================

def place_best_on_mannequin():
    """
    Move the currently previewed suit directly onto the configured mannequin.

    Ultima Online mannequins accept wearable items as their equipment.
    We use the normal Legion MoveItem destination mechanism one piece at a time.
    If the shard rejects a piece, SuitMaster stops and reports it rather than
    continuing blindly through the remaining suit.
    """
    if not _best:
        set_status("Preview a suit first.", 33)
        return False

    if not _mannequin:
        set_status("Set a mannequin first.", 33)
        return False

    moved = 0
    failed = []

    for item in _best.get("items", []):
        s = int(item.get("serial", 0) or 0)
        if not s:
            continue

        try:
            API.MoveItem(s, int(_mannequin), 0)
            API.Pause(MOVE_PAUSE)
            moved += 1
        except:
            failed.append(item.get("name", str(s)))
            break

    if failed:
        set_status(
            "Placed {} item(s) on mannequin, then stopped at: {}".format(
                moved, ", ".join(failed)
            ),
            33
        )
        return False

    save_active_suit(_best, "mannequin")
    set_status(
        "Placed {} suit items on the mannequin. RETURN SUIT can restore them.".format(moved),
        68
    )
    return True


# ============================================================
# Active suit tracking / return
# ============================================================

def save_active_suit(best, location="pull_bag"):
    payload = {
        "format": 1,
        "version": VERSION,
        "build": best.get("build"),
        "location": location,
        "pull_bag": int(_pull_bag or 0),
        "mannequin": int(_mannequin or 0),
        "saved_at": int(time.time()),
        "items": [
            {
                "serial": int(x.get("serial", 0) or 0),
                "name": x.get("name", ""),
                "slot": x.get("slot", ""),
                "source_chest": int(x.get("source_chest", 0) or 0),
                "source_container": int(x.get("source_container", 0) or 0),
            }
            for x in best.get("items", [])
        ],
    }
    try:
        safe_write_json(file_path(ACTIVE_SUIT_FILE), payload)
        return True
    except:
        return False


def load_active_suit():
    path = file_path(ACTIVE_SUIT_FILE)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except:
        return None


def clear_active_suit():
    try:
        path = file_path(ACTIVE_SUIT_FILE)
        if os.path.exists(path):
            os.remove(path)
    except:
        pass


def return_active_suit():
    """
    Return the last pulled SuitMaster suit to the exact storage container
    recorded when the chest scan was performed. If that container is no
    longer valid, fall back to the top-level source chest.
    """
    state = load_active_suit()
    if not state:
        set_status("No pulled SuitMaster suit is recorded to return.", 33)
        return False

    items = state.get("items", [])
    if not items:
        set_status("The active suit record contains no items.", 33)
        return False

    returned = 0
    failed = []

    for item in items:
        s = int(item.get("serial", 0) or 0)
        if not s:
            continue

        dest = int(item.get("source_container", 0) or 0)
        if not dest:
            dest = int(item.get("source_chest", 0) or 0)

        if not dest:
            failed.append(item.get("name", str(s)) + " (no source)")
            continue

        try:
            API.MoveItem(s, dest, 0)
            API.Pause(MOVE_PAUSE)
            returned += 1
        except:
            # If a nested source container is unavailable, try its root chest.
            fallback = int(item.get("source_chest", 0) or 0)
            if fallback and fallback != dest:
                try:
                    API.MoveItem(s, fallback, 0)
                    API.Pause(MOVE_PAUSE)
                    returned += 1
                    continue
                except:
                    pass

            failed.append(item.get("name", str(s)))

    if failed:
        set_status(
            "Returned {} items; could not return: {}".format(
                returned, ", ".join(failed)
            ),
            33
        )
        return False

    clear_active_suit()
    set_status(
        "Returned {} suit items to their original storage containers.".format(returned),
        68
    )
    return True


# ============================================================
# Pull suit
# ============================================================

def pull_best_suit():
    if not _best:
        set_status("Build a suit first.", 33)
        return False

    if not _pull_bag:
        set_status("Set the Pull Bag first.", 33)
        return False

    moved = 0
    failed = []

    for item in _best.get("items", []):
        s = int(item.get("serial", 0) or 0)
        if not s:
            continue

        try:
            API.MoveItem(s, int(_pull_bag), 0)
            API.Pause(MOVE_PAUSE)
            moved += 1
        except Exception as e:
            failed.append(item.get("name", str(s)))

    if failed:
        set_status("Pulled {} items; failed: {}".format(moved, ", ".join(failed)), 33)
    else:
        save_active_suit(_best, "pull_bag")
        set_status(
            "Pulled {} suit items into the selected bag. RETURN SUIT can restore them later.".format(moved),
            68
        )
    return not failed


# ============================================================
# Target helpers
# ============================================================

def add_chest():
    global _chests
    s = request_target("Target an equipment storage chest.")
    if s:
        if s not in _chests:
            _chests.append(s)
            save_chests()
            set_status("Added gear chest: 0x{:X}".format(s), 68)
        else:
            set_status("That chest is already in the gear-chest list.", 53)
        refresh_main()


def remove_chest():
    global _chests
    if not _chests:
        set_status("No gear chests are configured.", 33)
        return

    s = request_target("Target a configured gear chest to remove it.")
    if s:
        if s in _chests:
            _chests.remove(s)
            save_chests()
            set_status("Removed gear chest: 0x{:X}".format(s), 68)
        else:
            set_status("That target is not in SuitMaster's gear-chest list.", 33)
        refresh_main()


def clear_chests():
    global _chests, _items, _best
    _chests = []
    _items = []
    _best = None
    save_chests()
    set_status("Gear chest list cleared.", 68)
    refresh_main()


def target_pull_bag():
    global _pull_bag
    s = request_target("Target the bag where SuitMaster should pull the finished suit.")
    if s:
        _pull_bag = s
        pset(KEY_PULL_BAG, _pull_bag)
        set_status("Pull bag set: 0x{:X}".format(_pull_bag), 68)
        refresh_main()



def target_mannequin():
    global _mannequin
    s = request_target("Target the mannequin SuitMaster should use.")
    if s:
        _mannequin = s
        pset(KEY_MANNEQUIN, _mannequin)
        set_status(
            "Mannequin set: 0x{:X}. Direct suit placement is not enabled until placement is validated.".format(_mannequin),
            68
        )
        refresh_main()


# ============================================================
# UI helpers
# ============================================================

_gump_position_keys = {}

def gump_pos_key(name):
    return "JCS_SuitMaster_GumpPos_" + str(name)

def load_gump_pos(name, default_x, default_y):
    key = gump_pos_key(name)
    try:
        raw = str(pget(key, "") or "")
        if "," in raw:
            a, b = raw.split(",", 1)
            return int(a), int(b)
    except:
        pass
    return int(default_x), int(default_y)

def register_gump_position(g, name):
    try:
        _gump_position_keys[id(g)] = str(name)
    except:
        pass
    return g

def _read_gump_xy(g):
    """Return the live on-screen Legion gump position.

    TazUO exposes GetX()/GetY() on ApiUiBaseControl.  Older SuitMaster builds
    tried the backing X/Y attributes first; those are not reliable on every
    Legion/TazUO build after the user drags a gump.
    """
    if g is None:
        return None

    # Preferred/current Legion API.
    try:
        return int(g.GetX()), int(g.GetY())
    except:
        pass

    # Compatibility fallbacks for older wrappers/builds.
    try:
        return int(g.X), int(g.Y)
    except:
        pass

    try:
        return int(g.GetPos().X), int(g.GetPos().Y)
    except:
        return None


def save_gump_position(g, announce=False):
    try:
        name = _gump_position_keys.get(id(g))
        if not name:
            return False

        pos = _read_gump_xy(g)
        if pos is None:
            if announce:
                try:
                    API.SysMsg("SuitMaster: could not read this gump position.")
                except:
                    pass
            return False

        x, y = pos
        pset(gump_pos_key(name), "{},{}".format(x, y))

        # Keep the old main-position keys synchronized for backward
        # compatibility with existing SuitMaster installs.
        if name == "main":
            try:
                pset(KEY_X, x)
                pset(KEY_Y, y)
            except:
                pass

        if announce:
            try:
                API.SysMsg("SuitMaster: {} position saved ({}, {}).".format(name, x, y))
            except:
                pass
        return True
    except:
        return False


def add_save_pos_button(g):
    """Add the small manual position-memory button requested for every gump."""
    if g is None:
        return None
    try:
        w = int(g.GetWidth())
    except:
        try:
            w = int(g.Width)
        except:
            return None

    try:
        b = API.CreateSimpleButton("S", 22, 20)
        b.SetPos(max(4, w - 30), 5)
        try:
            b.SetTooltip("Save this window position")
        except:
            pass
        API.AddControlOnClick(b, lambda: save_gump_position(g, True))
        g.Add(b)
        return b
    except:
        return None

def dispose(g):
    if g is None:
        return
    save_gump_position(g)
    try:
        _gump_position_keys.pop(id(g), None)
    except:
        pass
    try:
        g.Dispose()
    except:
        pass


# Global SuitMaster font policy.
# Earlier alphas used many 10-12 pt labels which were technically compact but
# too small in actual gameplay. All gumps now share a larger readable baseline.
def readable_font_size(size):
    try:
        s = int(size)
    except:
        s = 12

    if s <= 10:
        return 12
    if s == 11:
        return 13
    if s == 12:
        return 14
    if s == 13:
        return 15
    if s == 14:
        return 16
    if s <= 18:
        return s + 1
    return s + 2


def make_label(text, size=12, color=C_TEXT, width=300, align="left"):
    try:
        return API.CreateGumpTTFLabel(
            str(text),
            readable_font_size(size),
            color,
            font="Avadonia",
            aligned=align,
            maxWidth=width if width else 0
        )
    except:
        return None


def add_label(g, text, x, y, w=300, h=20, size=12, color=C_TEXT, align="left"):
    lbl = make_label(text, size, color, w, align)
    if lbl is None:
        return None
    try:
        lbl.SetRect(x, y, w, h)
    except:
        try:
            lbl.SetPos(x, y)
        except:
            pass
    try:
        g.Add(lbl)
    except:
        pass
    return lbl


def add_button(g, text, x, y, w, h, callback):
    b = API.CreateSimpleButton(text, w, h)
    b.SetPos(x, y)
    API.AddControlOnClick(b, callback)
    g.Add(b)
    return b


def add_panel(g, x, y, w, h):
    box = API.CreateGumpColorBox(0.92, C_PANEL)
    box.SetRect(x, y, w, h)
    g.Add(box)
    return box


def load_pos():
    try:
        x = int(pget(KEY_X, "360"))
        y = int(pget(KEY_Y, "180"))
        return x, y
    except:
        return 360, 180


def save_pos(g):
    # Legacy main-gump position keys. Prefer Legion's documented GetX/GetY.
    pos = _read_gump_xy(g)
    if pos is None:
        return
    try:
        pset(KEY_X, int(pos[0]))
        pset(KEY_Y, int(pos[1]))
    except:
        pass


def set_build_from_dropdown(dd):
    global _build
    try:
        i = int(dd.GetSelectedIndex())
    except:
        i = 0
    if 0 <= i < len(BUILD_NAMES):
        _build = BUILD_NAMES[i]
        pset(KEY_BUILD, _build)
        set_status("Build profile: " + profile_display_name(_build), 68)
        if _build == "Custom":
            show_custom_editor()
        refresh_main()


def refresh_main():
    global _main_gump, _mini_gump
    if _main_gump is not None:
        dispose(_main_gump)
        _main_gump = None
    # When SuitMaster is minimized, refresh the compact scanner bar instead of
    # unexpectedly reopening the full window after scans/build actions.
    if _mini_gump is not None:
        try:
            if not _mini_gump.IsDisposed:
                show_mini_bar()
                return
        except:
            pass
    show_main()


def show_main():
    global _main_gump

    W = 610
    H = 380
    x, y = load_pos()

    g = API.CreateGump(True, True, True)
    g.SetRect(x, y, W, H)

    bg = API.CreateGumpColorBox(0.96, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "J.C.S. SUITMASTER", 18, 12, 330, 26, 18, C_TITLE)
    add_label(g, "v" + VERSION, 505, 16, 80, 18, 10, C_MUTED, "right")

    add_panel(g, 12, 48, 586, 142)
    add_label(g, "STORAGE", 24, 58, 100, 18, 11, C_GOLD)

    chest_text = "{} gear chest{}".format(len(_chests), "" if len(_chests) == 1 else "s")
    if _chests:
        preview = ", ".join("0x{:X}".format(x) for x in _chests[:3])
        if len(_chests) > 3:
            preview += " ..."
        chest_text += " | " + preview

    add_label(g, "Chests: " + chest_text, 24, 82, 548, 18, 10, C_TEXT)
    add_label(
        g,
        "Pull bag: " + ("0x{:X}".format(_pull_bag) if _pull_bag else "Not set"),
        24, 104, 260, 18, 10, C_TEXT
    )
    add_label(
        g,
        "Mannequin: " + ("0x{:X}".format(_mannequin) if _mannequin else "Not set"),
        310, 104, 262, 18, 10, C_TEXT
    )

    add_button(g, "ADD CHEST", 24, 130, 105, 24, add_chest)
    add_button(g, "REMOVE", 139, 130, 85, 24, remove_chest)
    add_button(g, "CLEAR", 234, 130, 75, 24, clear_chests)
    add_button(g, "SCAN ALL", 454, 130, 118, 24, scan_chest)

    add_button(g, "SET PULL BAG", 24, 160, 125, 24, target_pull_bag)
    add_button(g, "SET MANNEQUIN", 159, 160, 140, 24, target_mannequin)
    add_button(g, "RETURN SUIT", 432, 160, 140, 24, return_active_suit)

    add_panel(g, 12, 200, 586, 82)
    add_label(g, "BUILD", 24, 210, 80, 18, 11, C_GOLD)

    try:
        idx = BUILD_NAMES.index(_build)
    except:
        idx = 0

    dd = API.CreateDropDown(190, BUILD_NAMES, idx)
    dd.SetPos(24, 236)
    g.Add(dd)

    add_button(g, "USE PROFILE", 224, 236, 110, 24, lambda: set_build_from_dropdown(dd))
    add_button(g, "PREVIEW SUIT", 344, 236, 230, 24, optimize)

    count = len(_items)
    result_text = "Cached wearable items: {}".format(count)
    if _best:
        result_text += " | Best {} suit ready".format(_best.get("build", _build))
    add_label(g, result_text, 24, 266, 540, 18, 10, C_MUTED)

    add_panel(g, 12, 292, 586, 70)
    add_label(g, "STATUS", 24, 302, 80, 18, 10, C_GOLD)
    add_label(g, _status, 24, 323, 550, 32, 10, C_TEXT)

    _main_gump = g
    API.AddGump(g)


def show_results():
    if not _best:
        return

    best = _best
    totals = best.get("totals", {})
    deficits = best.get("deficits", {})
    items = best.get("items", [])
    profile = active_profile()

    W = 930
    H = 640
    g = API.CreateGump(True, True, True)
    gx, gy = load_gump_pos("results", 320, 105)
    g.SetRect(gx, gy, W, H)
    register_gump_position(g, "results")

    bg = API.CreateGumpColorBox(0.97, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(
        g,
        "{} SUIT".format(profile_display_name(best.get("build", "")).upper()),
        20, 12, 520, 28, 21, C_TITLE
    )
    add_label(
        g,
        "Hard minimums: " + ("MET" if not deficits else "NOT MET"),
        610, 18, 250, 22, 13,
        C_GREEN if not deficits else C_RED,
        "right"
    )

    add_label(
        g,
        "PREVIEW ONLY - nothing moves until you choose a destination below",
        20, 43, 860, 20, 11, C_MUTED
    )

    # --------------------------------------------------------
    # LEFT: selected pieces
    # --------------------------------------------------------
    add_panel(g, 14, 70, 410, 470)
    add_label(g, "SELECTED ITEMS", 30, 84, 210, 22, 14, C_GOLD)

    y = 120
    for item in items:
        slot = str(item.get("slot", "?"))
        name = str(item.get("name", "Unknown"))

        if len(name) > 40:
            name = name[:37] + "..."

        add_label(g, slot, 30, y, 90, 22, 13, C_MUTED)
        add_label(g, name, 125, y, 275, 22, 13, C_TEXT)
        y += 40

    # --------------------------------------------------------
    # RIGHT: suit totals
    # --------------------------------------------------------
    add_panel(g, 438, 70, 478, 470)
    add_label(g, "SUIT TOTALS", 454, 84, 180, 22, 14, C_GOLD)

    # Left stats column
    lx = 454
    lv = 600

    add_label(g, "RESISTS", lx, 120, 120, 20, 13, C_TITLE)
    y = 150
    resist_rows = [
        ("Physical", "Physical Resist"),
        ("Fire", "Fire Resist"),
        ("Cold", "Cold Resist"),
        ("Poison", "Poison Resist"),
        ("Energy", "Energy Resist"),
    ]
    for label_text, prop in resist_rows:
        value = int(totals.get(prop, 0) or 0)
        minimum = int(profile["requirements"].get(prop, 0) or 0)
        color = C_GREEN if (not minimum or value >= minimum) else C_RED

        add_label(g, label_text, lx, y, 120, 22, 13, C_TEXT)
        add_label(g, str(value), lv, y, 52, 22, 14, color, "right")
        y += 28

    add_label(g, "COMBAT", lx, 300, 120, 20, 13, C_TITLE)
    y = 330
    for label_text, prop in [
        ("HCI", "Hit Chance Increase"),
        ("DCI", "Defense Chance Increase"),
        ("Damage Inc", "Damage Increase"),
        ("Swing Speed", "Swing Speed Increase"),
    ]:
        add_label(g, label_text, lx, y, 120, 22, 13, C_TEXT)
        add_label(g, str(totals.get(prop, 0)), lv, y, 52, 22, 14, C_TEXT, "right")
        y += 28

    # Right stats column
    rx = 680
    rv = 835

    add_label(g, "RESOURCES", rx, 120, 130, 20, 13, C_TITLE)
    y = 150
    for label_text, prop in [
        ("HP Increase", "Hit Point Increase"),
        ("Stamina", "Stamina Increase"),
        ("Mana", "Mana Increase"),
        ("LMC", "Lower Mana Cost"),
        ("LRC", "Lower Reagent Cost"),
    ]:
        value = int(totals.get(prop, 0) or 0)
        minimum = int(profile["requirements"].get(prop, 0) or 0)
        color = C_GREEN if (not minimum or value >= minimum) else C_RED

        add_label(g, label_text, rx, y, 135, 22, 13, C_TEXT)
        add_label(g, str(value), rv, y, 52, 22, 14, color, "right")
        y += 28

    add_label(g, "ATTRIBUTES / CASTING", rx, 300, 190, 20, 13, C_TITLE)
    y = 330
    for label_text, prop in [
        ("Dexterity", "Dexterity Bonus"),
        ("Strength", "Strength Bonus"),
        ("Intelligence", "Intelligence Bonus"),
        ("FC", "Faster Casting"),
        ("FCR", "Faster Cast Recovery"),
        ("SDI", "Spell Damage Increase"),
        ("Luck", "Luck"),
    ]:
        add_label(g, label_text, rx, y, 135, 22, 13, C_TEXT)
        add_label(g, str(totals.get(prop, 0)), rv, y, 52, 22, 14, C_TEXT, "right")
        y += 26

    # --------------------------------------------------------
    # Bottom status and actions
    # --------------------------------------------------------
    equip_safety = best.get("equipment_safety", {})
    if equip_safety and not equip_safety.get("safe", True):
        safety_text = "EQUIP SAFETY: NOT SAFE after -{} debuff".format(equip_safety.get("buffer", 22))
        if equip_safety.get("strength_deficit", 0):
            safety_text += " | STR short {}".format(equip_safety["strength_deficit"])
        if equip_safety.get("dexterity_deficit", 0):
            safety_text += " | DEX short {}".format(equip_safety["dexterity_deficit"])
        add_label(g, safety_text, 30, 536, 860, 18, 11, C_RED)
    elif equip_safety:
        safety_text = "Equip-safe after -{} debuff: STR {} vs req {} | DEX {} vs req {}".format(
            equip_safety.get("buffer", 22),
            equip_safety.get("safe_strength", 0),
            equip_safety.get("max_strength_requirement", 0),
            equip_safety.get("safe_dexterity", 0),
            equip_safety.get("max_dexterity_requirement", 0)
        )
        add_label(g, safety_text, 30, 536, 860, 18, 10, C_GREEN)

    if deficits:
        need_text = "NEEDS: " + "   |   ".join(
            "{} +{}".format(k.replace(" Resist", ""), v)
            for k, v in deficits.items()
        )
        add_label(g, need_text, 30, 556, 860, 20, 11, C_RED)
    else:
        add_label(
            g,
            "All hard minimum requirements are satisfied.",
            30, 556, 860, 20, 11, C_GREEN
        )

    add_button(g, "PULL TO BAG", 30, 602, 165, 28, pull_best_suit)
    add_button(g, "RETURN LAST SUIT", 210, 602, 190, 28, return_active_suit)
    add_label(
        g,
        "Mannequin dressing paused pending a safe paperdoll API.",
        420, 606, 300, 20, 10, C_MUTED
    )
    add_button(g, "CLOSE", 816, 602, 84, 28, lambda: dispose(g))

    add_save_pos_button(g)
    API.AddGump(g)


# ============================================================
# Custom priority editor
# ============================================================

def show_custom_editor():
    global _editor_gump

    if _editor_gump is not None:
        dispose(_editor_gump)

    profile = BUILD_PROFILES["Custom"]
    weights = profile["weights"]

    W = 640
    H = 510
    g = API.CreateGump(True, True, True)
    gx, gy = load_gump_pos("legacy_custom", 1040, 170)
    g.SetRect(gx, gy, W, H)
    register_gump_position(g, "legacy_custom")

    bg = API.CreateGumpColorBox(0.97, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "CUSTOM BUILD PRIORITIES", 18, 12, 420, 24, 17, C_TITLE)
    add_label(g, "0 = ignore, 5 = highest priority", 18, 38, 320, 18, 10, C_MUTED)

    controls = {}

    y = 70
    for idx, prop in enumerate(CUSTOM_EDIT_PROPS):
        if idx == 7:
            y = 70

        col = 0 if idx < 7 else 1
        row = idx if idx < 7 else idx - 7
        x = 18 if col == 0 else 326
        yy = 70 + row * 45

        add_label(g, prop, x, yy, 218, 18, 10, C_TEXT)
        opts = ["0", "1", "2", "3", "4", "5"]
        current = int(weights.get(prop, 0) or 0)
        dd = API.CreateDropDown(70, opts, max(0, min(current, 5)))
        dd.SetPos(x + 222, yy - 2)
        g.Add(dd)
        controls[prop] = dd

    add_label(g, "RESIST MINIMUMS", 18, 395, 180, 18, 11, C_GOLD)
    req_controls = {}
    x = 18
    for p, short in [
        ("Physical Resist", "Phys"),
        ("Fire Resist", "Fire"),
        ("Cold Resist", "Cold"),
        ("Poison Resist", "Pois"),
        ("Energy Resist", "Ener"),
    ]:
        add_label(g, short, x, 421, 48, 18, 9, C_MUTED)
        opts = [str(v) for v in range(0, 81, 5)]
        current = int(profile["requirements"].get(p, 70) or 70)
        try:
            idx = opts.index(str((current // 5) * 5))
        except:
            idx = 14
        dd = API.CreateDropDown(78, opts, idx)
        dd.SetPos(x, 442)
        g.Add(dd)
        req_controls[p] = (dd, opts)
        x += 100

    def save_custom():
        for p, dd in controls.items():
            try:
                profile["weights"][p] = int(dd.GetSelectedIndex())
            except:
                pass

        for p, pair in req_controls.items():
            dd, opts = pair
            try:
                i = int(dd.GetSelectedIndex())
                if 0 <= i < len(opts):
                    profile["requirements"][p] = int(opts[i])
            except:
                pass

        save_settings()
        set_status("Custom priorities saved.", 68)
        dispose(g)
        refresh_main()

    add_button(g, "SAVE CUSTOM", 18, 478, 140, 24, save_custom)
    add_button(g, "CLOSE", 540, 478, 80, 24, lambda: dispose(g))

    _editor_gump = g
    add_save_pos_button(g)
    API.AddGump(g)


# ============================================================
# Settings
# ============================================================

def save_settings():
    payload = {
        "version": VERSION,
        "chests": [int(x) for x in _chests],
        "pull_bag": int(_pull_bag or 0),
        "mannequin": int(_mannequin or 0),
        "build": _build,
        "custom_profile": BUILD_PROFILES["Custom"],
    }
    try:
        safe_write_json(file_path(SETTINGS_FILE), payload)
    except:
        pass


def load_settings():
    global _chests, _pull_bag, _mannequin, _build

    _chests = load_chests()

    try:
        _pull_bag = int(pget(KEY_PULL_BAG, "0") or 0)
    except:
        _pull_bag = 0

    try:
        _mannequin = int(pget(KEY_MANNEQUIN, "0") or 0)
    except:
        _mannequin = 0

    b = str(pget(KEY_BUILD, "Basher") or "Basher")
    _build = b if b in BUILD_NAMES else "Basher"

    path = file_path(SETTINGS_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                d = json.load(f)

            saved_chests = d.get("chests")
            if isinstance(saved_chests, list):
                clean = []
                for x in saved_chests:
                    try:
                        s = int(x or 0)
                        if s and s not in clean:
                            clean.append(s)
                    except:
                        pass
                if clean:
                    _chests = clean

            # Migrate alpha 0.1 settings.
            if not _chests:
                try:
                    legacy = int(d.get("chest", 0) or 0)
                    if legacy:
                        _chests = [legacy]
                except:
                    pass

            _pull_bag = int(d.get("pull_bag", _pull_bag) or _pull_bag)
            _mannequin = int(d.get("mannequin", _mannequin) or _mannequin)

            b = d.get("build", _build)
            if b in BUILD_NAMES:
                _build = b

            cp = d.get("custom_profile")
            if isinstance(cp, dict):
                if isinstance(cp.get("requirements"), dict):
                    BUILD_PROFILES["Custom"]["requirements"].update(cp["requirements"])
                if isinstance(cp.get("weights"), dict):
                    BUILD_PROFILES["Custom"]["weights"].update(cp["weights"])
                BUILD_PROFILES["Custom"]["shield"] = bool(cp.get("shield", False))
        except:
            pass

    save_chests()
    load_cache()



# ============================================================
# PROFILE SYSTEM v1 / MAIN UI v2
# Later definitions intentionally override the early-alpha profile/UI
# helpers above. This keeps migration compatibility with older settings.
# ============================================================

BUILTIN_PROFILE_NAMES = ["Basher", "Sampire", "Blood Knight", "Blood Tamer", "Mage", "Luck Dexer", "Luck Caster", "Hybrid Tamer", "Mystic Tank", "Necro Weaver Tamer", "Archer Tamer", "Custom"]

PROFILE_DISPLAY_NAMES = {
    "Basher": "Shield Bash Basher",
    "Sampire": "Sampire",
    "Blood Knight": "Blood Knight",
    "Blood Tamer": "Blood Tamer",
    "Mage": "Mage",
    "Luck Dexer": "Luck Dexer",
    "Luck Caster": "Luck Caster",
    "Hybrid Tamer": "Battle Tamer (Sampire/Whammy)",
    "Mystic Tank": "Mystic Tank",
    "Necro Weaver Tamer": "Necro-Weaver Tamer",
    "Archer Tamer": "Archer Tamer",
    "Custom": "Custom Profile",
}

PROFILE_DESCRIPTIONS = {
    "Basher": "Shield Bash dexer built around 45 HCI, 100 DI, 3/6 casting, 1.25s swing speed and the highest practical LMC.",
    "Sampire": "Vampire-form melee build focused on sustained weapon damage, mana efficiency and survivability.",
    "Blood Knight": "Durable melee/caster hybrid built around aggressive sustain and strong combat stats.",
    "Blood Tamer": "Blood Knight / Tamer melee build tuned to the current Swordsmanship, Taming, Necromancy and Veterinary template.",
    "Mage": "General caster suit emphasizing casting speed, mana economy, spell damage and survivability.",
    "Luck Dexer": "High-luck melee farming suit that still preserves practical dexer combat breakpoints and defenses.",
    "Luck Caster": "High-luck caster farming suit with reagent-free casting, mana economy, casting speed and spell damage.",
    "Hybrid Tamer": "Melee pet build: pet tanks/debuffs while the player fights in Sampire/Whammy style using leeches and Parry/Bushido.",
    "Mystic Tank": "Stone Form melee tank using high resists, LMC, stamina, reflect damage, Mysticism and shield-based defense.",
    "Necro Weaver Tamer": "Pet-backed Necromancy/Spellweaving caster focused heavily on SDI, mana sustain and high-end solo PvM.",
    "Archer Tamer": "Ranged pet build using Archery, Taming/Lore, strong stamina, SSI/HCI, mana sustain and optional bard support.",
    "Custom": "Blank editable profile for building your own Minimum / Target / Priority setup.",
}


PROFILE_SKILLS = {
    "Basher": [
        ("Weapon Skill", "120", "Use the weapon skill for the chosen one-handed Basher weapon"),
        ("Parrying", "120", "Core Shield Bash mastery / defense skill"),
        ("Tactics", "120", "Core melee damage"),
        ("Anatomy", "120", "Core melee damage and combat support"),
        ("Chivalry", "120", "Damage support, utility and travel"),
        ("Necromancy", "100+ variant", "Popular Vampire Form variant; 100 is the stated minimum"),
        ("Poisoning", "120 variant", "Alternative Basher template; 120 with Taste ID gives full poison immunity"),
        ("Healing", "120 variant", "Alternative non-Necro Basher template"),
    ],
    "Sampire": [
        ("Weapon Skill", "120", "Primary melee skill"),
        ("Tactics", "100-120", "Core melee damage"),
        ("Bushido", "100-120", "Core Sampire offense / defense"),
        ("Parrying", "Variable", "Depends on weapon and defense plan"),
        ("Necromancy", "99+", "For Vampire Form"),
        ("Chivalry", "Variable", "Enemy of One, Consecrate, utility"),
        ("Anatomy / Resist", "Variable", "Common flex slot"),
    ],
    "Blood Knight": [
        ("Weapon Skill", "120", "Primary melee skill"),
        ("Tactics", "100-120", "Core damage"),
        ("Necromancy", "100-120", "Main dark-magic component"),
        ("Spirit Speak", "100-120", "Supports Necromancy"),
        ("Parrying", "Variable", "Defense / shield option"),
        ("Chivalry", "Variable", "Utility and damage support"),
        ("Anatomy / Resist", "Variable", "Flex slot"),
    ],
    "Blood Tamer": [
        ("Swordsmanship", "120.0", "Primary melee skill"),
        ("Animal Taming", "115.0", "Pet control"),
        ("Animal Lore", "115.0", "Pet control / effectiveness"),
        ("Chivalry", "105.4", "Damage support, healing and utility"),
        ("Tactics", "110.1", "95.1 base + 15 skill gear"),
        ("Necromancy", "100.0", "85.0 base + 15 skill gear"),
        ("Veterinary", "99.5", "84.5 base + 15 skill gear"),
    ],
    "Mage": [
        ("Magery", "120", "Primary casting skill"),
        ("Evaluating Intelligence", "120", "Spell damage / effectiveness"),
        ("Meditation", "100-120", "Mana sustain"),
        ("Resisting Spells", "100-120", "Defense"),
        ("Inscription", "Optional", "Caster damage / utility"),
        ("Spellweaving / Mysticism", "Optional", "Common specialization"),
        ("Focus / Wrestling", "Optional", "Flex defensive or mana support"),
    ],
    "Luck Dexer": [
        ("Weapon Skill", "120", "Primary melee skill"),
        ("Tactics", "100-120", "Core melee damage"),
        ("Chivalry / Bushido", "Variable", "Common dexer support"),
        ("Flex Skills", "Variable", "Luck profile does not force one exact dexer template"),
    ],
    "Luck Caster": [
        ("Magery / Casting School", "120", "Primary casting school"),
        ("Damage Support", "100-120", "Evaluate Intelligence or equivalent school support"),
        ("Meditation / Focus", "Variable", "Mana sustain as needed"),
        ("Flex Skills", "Variable", "Luck profile does not force one exact caster template"),
    ],
    "Archer Tamer": [
        ("Animal Taming", "110-120", "Pevil prefers 120 Taming for difficult pets"),
        ("Animal Lore", "105-115", "Aim for about 225 combined Taming + Lore"),
        ("Archery", "120", "Primary damage skill"),
        ("Tactics", "100", "Core ranged damage"),
        ("Veterinary", "Optional", "Pevil's preferred pet healing"),
        ("Chivalry", "Optional", "Damage, healing and Sacred Journey"),
        ("Peacemaking", "Optional", "Very useful on InsaneUO because Musicianship is free"),
        ("Discordance", "Optional", "Alternative bard debuff"),
        ("Bushido", "Optional", "Turns it toward an ABC-style Tamer"),
    ],
    "Necro Weaver Tamer": [
        ("Necromancy", "100-120", "Primary damage / utility school"),
        ("Spirit Speak", "100-120", "Supports Necromancy"),
        ("Spellweaving", "100-120", "Primary secondary casting school"),
        ("Animal Taming", "110-120", "Pet control"),
        ("Animal Lore", "110-120", "Pet control / effectiveness"),
        ("Veterinary", "Optional", "Pet healing"),
        ("Magery / Meditation", "Variable", "Common caster support depending on exact version"),
    ],
    "Mystic Tank": [
        ("Weapon Skill", "120", "Pevil used Macing; any melee skill works"),
        ("Tactics", "100+", "Core melee damage"),
        ("Anatomy", "100+", "Damage / healing support"),
        ("Parrying", "100+", "Main tanking skill"),
        ("Healing", "100+", "Survivability"),
        ("Mysticism", "100-120", "Stone Form and utility"),
        ("Focus", "100-120", "Boosts Mysticism and adds mana/stamina regen"),
        ("Imbuing", "Alternative", "Can replace Focus as Mysticism support"),
    ],
    "Hybrid Tamer": [
        ("Animal Taming", "110-115+", "Slate used 110; 115 improves control chance"),
        ("Animal Lore", "110-115+", "Balance with Taming for pet control"),
        ("Veterinary", "90+", "Background pet healing"),
        ("Weapon Skill", "120", "Primary melee damage"),
        ("Tactics", "90+", "Melee damage"),
        ("Spirit Speak / Necromancy", "Variable", "Depends on Wraith vs Vampire style"),
        ("Parrying", "Variable", "Especially useful for 1H + shield"),
        ("Bushido", "Optional", "Useful with suitable weapon / 2H setup"),
    ],
    "Custom": [
        ("Custom", "-", "Use this profile for your own skill template"),
    ],
}

PROFILE_CREATORS = {
    "Archer Tamer": "Pevil",
    "Mystic Tank": "Pevil",
    "Necro Weaver Tamer": "Wolfsun [STAR]",
    "Hybrid Tamer": "Slate",
}

# Max-swing reference supplied from the InsaneUO community.
# Values are minimum stamina needed at the listed SSI.
# "with_debuff" preserves a 22-point stamina buffer from the source chart.
SWING_SPEED_GUIDE = {
    2.5: {
        0: (150, 172), 5: (120, 142), 10: (120, 142), 15: (120, 142),
        20: (90, 112), 25: (90, 112), 30: (90, 112), 35: (60, 82),
        40: (60, 82), 45: (60, 82), 50: (60, 82), 55: (30, 52), 60: (30, 52),
    },
    3.0: {
        0: (210, 232), 5: (180, 202), 10: (180, 202), 15: (180, 202),
        20: (150, 172), 25: (150, 172), 30: (150, 172), 35: (120, 142),
        40: (120, 142), 45: (120, 142), 50: (120, 142), 55: (90, 112), 60: (90, 112),
    },
    3.25: {
        0: (240, None), 5: (210, 232), 10: (210, 232), 15: (210, 232),
        20: (180, 202), 25: (180, 202), 30: (180, 202), 35: (150, 172),
        40: (150, 172), 45: (150, 172), 50: (150, 172), 55: (120, 142), 60: (120, 142),
    },
    3.5: {
        0: (None, None), 5: (240, None), 10: (240, None), 15: (240, None),
        20: (210, 232), 25: (210, 232), 30: (210, 232), 35: (180, 202),
        40: (180, 202), 45: (180, 202), 50: (180, 202), 55: (150, 172), 60: (150, 172),
    },
}

DEXER_PROFILE_NAMES = {
    "Basher", "Sampire", "Blood Knight", "Blood Tamer", "Luck Dexer", "Hybrid Tamer", "Mystic Tank", "Archer Tamer"
}

def profile_creator(name):
    return PROFILE_CREATORS.get(name, "")

def swing_speed_requirement(weapon_speed, ssi, with_debuff=True):
    try:
        speed = float(weapon_speed)
        ssi = int(ssi)
    except:
        return None
    row = SWING_SPEED_GUIDE.get(speed, {}).get(ssi)
    if not row:
        return None
    return row[1] if with_debuff else row[0]

PROFILE_NOTES = {
    "Blood Tamer": "Current template: 120 Swords, 115 Taming/Lore, 105.4 Chivalry, 110.1 Tactics, 100 Necromancy and 99.5 Veterinary. SuitMaster treats the current 45 equipment skill points as a flexible pool; individual skill minimums are only enforced when explicitly configured.",
    "Luck Dexer": "Luck is optimized only after the suit remains functional as a dexer: practical resists, HCI, DI, SSI/stamina and LMC all matter.",
    "Luck Caster": "Luck is optimized only after the suit remains functional as a caster: 100 LRC, useful FC/FCR, mana economy and SDI all matter.",
    "Basher": "InsaneUO Shield Bash: shield required; prioritize 45 HCI, 100 DI, FC/FCR 3/6, enough stamina + SSI for a 1.25s swing, then push LMC as high as the selected armor materials allow. Studded/bone/stone pieces can raise the LMC cap toward 55. Soul Charge is a useful shield bonus, not a mandatory BIS item.",
    "Archer Tamer": "Pevil recommends roughly 225 combined Animal Taming + Animal Lore for strong pet control. Build can flex into Peace, Discord, Chivalry, Bushido or caster support.",
    "Necro Weaver Tamer": "Discord discussion strongly emphasizes SDI; around 150+ SDI was cited as a major performance breakpoint with a well-trained pet.",
    "Mystic Tank": "Stone Form increases resist caps and survivability but slows attacking/casting, so SSI and FC/FCR help offset the penalty.",
    "Hybrid Tamer": "Pet tanks and supplies Discord/elemental debuffs while the player contributes sustained melee damage and self-healing via Vampire Form / weapon leeches.",
}

def profile_display_name(name):
    return PROFILE_DISPLAY_NAMES.get(name, str(name))

def profile_description(name):
    return PROFILE_DESCRIPTIONS.get(name, "User-created SuitMaster profile.")

def profile_skills(name):
    return PROFILE_SKILLS.get(name, [("Custom", "-", "User-created profile")])

def profile_note(name):
    return PROFILE_NOTES.get(name, "")

PROFILE_FIELDS = [
    ("RESISTS", "Physical Resist"),
    ("RESISTS", "Fire Resist"),
    ("RESISTS", "Cold Resist"),
    ("RESISTS", "Poison Resist"),
    ("RESISTS", "Energy Resist"),

    ("COMBAT", "Hit Chance Increase"),
    ("COMBAT", "Defense Chance Increase"),
    ("COMBAT", "Damage Increase"),
    ("COMBAT", "Swing Speed Increase"),
    ("COMBAT", "Reflect Physical Damage"),
    ("COMBAT", "Enhance Potions"),

    ("RESOURCES", "Lower Mana Cost"),
    ("RESOURCES", "Lower Reagent Cost"),
    ("RESOURCES", "Hit Point Increase"),
    ("RESOURCES", "Stamina Increase"),
    ("RESOURCES", "Mana Increase"),
    ("RESOURCES", "Hit Point Regeneration"),
    ("RESOURCES", "Stamina Regeneration"),
    ("RESOURCES", "Mana Regeneration"),

    ("ATTRIBUTES / CASTING", "Strength Bonus"),
    ("ATTRIBUTES / CASTING", "Dexterity Bonus"),
    ("ATTRIBUTES / CASTING", "Intelligence Bonus"),
    ("ATTRIBUTES / CASTING", "Faster Casting"),
    ("ATTRIBUTES / CASTING", "Faster Cast Recovery"),
    ("ATTRIBUTES / CASTING", "Spell Damage Increase"),
    ("ATTRIBUTES / CASTING", "Casting Focus"),
    ("ATTRIBUTES / CASTING", "Luck"),

    ("SKILL BONUSES", "Archery"),
    ("SKILL BONUSES", "Swordsmanship"),
    ("SKILL BONUSES", "Animal Taming"),
    ("SKILL BONUSES", "Animal Lore"),
    ("SKILL BONUSES", "Veterinary"),
    ("SKILL BONUSES", "Chivalry"),
    ("SKILL BONUSES", "Peacemaking"),
    ("SKILL BONUSES", "Discordance"),
    ("SKILL BONUSES", "Musicianship"),
    ("SKILL BONUSES", "Bushido"),
    ("SKILL BONUSES", "Anatomy"),
    ("SKILL BONUSES", "Healing"),
    ("SKILL BONUSES", "Spellweaving"),
    ("SKILL BONUSES", "Magery"),
    ("SKILL BONUSES", "Mysticism"),
    ("SKILL BONUSES", "Necromancy"),
    ("SKILL BONUSES", "Spirit Speak"),
    ("SKILL BONUSES", "Focus"),
    ("SKILL BONUSES", "Parrying"),
    ("SKILL BONUSES", "Tactics"),

    ("WEAPON / SPECIAL", "Hit Life Leech"),
    ("WEAPON / SPECIAL", "Hit Mana Leech"),
    ("WEAPON / SPECIAL", "Soul Charge"),
    ("WEAPON / SPECIAL", "Spell Channeling"),
]

_profile_gump = None
_profile_editor_gump = None
_share_gump = None
_import_gump = None
_skills_gump = None
_profiles = {}

# Capture the built-in values defined near the top of the script.
_BUILTIN_BASE = copy.deepcopy(BUILD_PROFILES)


def make_profile_record(name, source):
    requirements = dict(source.get("requirements", {}))
    weights = dict(source.get("weights", {}))

    targets = {}
    for category, prop in PROFILE_FIELDS:
        req = int(requirements.get(prop, 0) or 0)
        default_cap = int(SCORE_CAPS.get(prop, 0) or 0)
        # Target controls when extra value stops contributing meaningful score.
        # If a property has a built-in score cap, use it; otherwise at least meet min.
        targets[prop] = max(req, default_cap)

    return {
        "name": str(name),
        "requirements": requirements,
        "targets": targets,
        "weights": weights,
        "shield": bool(source.get("shield", False)),
        "medable": bool(source.get("medable", False)),
        "skill_budget": max(0, int(source.get("skill_budget", 0) or 0)),
        "skill_budget_priority": max(0, min(5, int(source.get("skill_budget_priority", 0) or 0))),
        "core_skills": dict(source.get("core_skills", {}) or {}),
        "scan_source": dict(source.get("scan_source", {}) or {}),
    }


def default_profiles():
    out = {}
    for name in BUILTIN_PROFILE_NAMES:
        source = _BUILTIN_BASE.get(name, _BUILTIN_BASE.get("Custom", {}))
        out[name] = make_profile_record(name, source)

    # All true caster / mage presets require full reagent-free casting.
    for caster_name in ("Mage", "Luck Caster", "Necro Weaver Tamer"):
        if caster_name in out:
            out[caster_name]["requirements"]["Lower Reagent Cost"] = 100
            out[caster_name]["targets"]["Lower Reagent Cost"] = 100
            out[caster_name]["weights"]["Lower Reagent Cost"] = 5

    if "Basher" in out:
        p = out["Basher"]
        p["targets"]["Hit Chance Increase"] = 45
        p["targets"]["Damage Increase"] = 100
        p["targets"]["Defense Chance Increase"] = 45
        p["targets"]["Lower Mana Cost"] = 40
        p["targets"]["Faster Casting"] = 3
        p["targets"]["Faster Cast Recovery"] = 6
        p["targets"]["Stamina Increase"] = 50
        p["targets"]["Dexterity Bonus"] = 40
        p["targets"]["Strength Bonus"] = 40
        p["targets"]["Hit Point Increase"] = 30
        p["targets"]["Mana Regeneration"] = 12
        p["targets"]["Mana Increase"] = 30
        p["targets"]["Swing Speed Increase"] = 60
        p["targets"]["Soul Charge"] = 1

    if "Luck Dexer" in out:
        p = out["Luck Dexer"]
        p["targets"]["Luck"] = 1500
        p["targets"]["Hit Chance Increase"] = 45
        p["targets"]["Damage Increase"] = 100
        p["targets"]["Swing Speed Increase"] = 60
        p["targets"]["Lower Mana Cost"] = 40
        p["targets"]["Stamina Increase"] = 50
        p["targets"]["Dexterity Bonus"] = 30
        p["targets"]["Hit Point Increase"] = 30
        p["targets"]["Defense Chance Increase"] = 45

    if "Luck Caster" in out:
        p = out["Luck Caster"]
        p["targets"]["Luck"] = 1500
        p["targets"]["Lower Mana Cost"] = 40
        p["targets"]["Lower Reagent Cost"] = 100
        p["targets"]["Faster Casting"] = 4
        p["targets"]["Faster Cast Recovery"] = 6
        p["targets"]["Spell Damage Increase"] = 150
        p["targets"]["Mana Increase"] = 50
        p["targets"]["Mana Regeneration"] = 12
        p["targets"]["Intelligence Bonus"] = 30

    if "Blood Tamer" in out:
        p = out["Blood Tamer"]
        # Flexible 45-point equipment skill budget from the current build.
        # Exact skill names are not required unless the user adds an individual minimum.
        p["skill_budget"] = 45
        p["skill_budget_priority"] = 5
        p["core_skills"] = {
            "Swordsmanship": {"base": 120.0, "value": 120.0, "cap": 120.0},
            "Animal Taming": {"base": 115.0, "value": 115.0, "cap": 120.0},
            "Animal Lore": {"base": 115.0, "value": 115.0, "cap": 120.0},
            "Chivalry": {"base": 105.4, "value": 105.4, "cap": 120.0},
            "Tactics": {"base": 95.1, "value": 110.1, "cap": 120.0},
            "Necromancy": {"base": 85.0, "value": 100.0, "cap": 120.0},
            "Veterinary": {"base": 84.5, "value": 99.5, "cap": 120.0},
        }
        p["targets"]["Hit Chance Increase"] = 45
        p["targets"]["Damage Increase"] = 100
        p["targets"]["Swing Speed Increase"] = 60
        p["targets"]["Lower Mana Cost"] = 40
        p["targets"]["Stamina Increase"] = 50
        p["targets"]["Hit Point Increase"] = 30
        p["targets"]["Mana Increase"] = 30
        p["targets"]["Hit Life Leech"] = 50
        p["targets"]["Hit Mana Leech"] = 50
        p["targets"]["Tactics"] = 15
        p["targets"]["Necromancy"] = 15
        p["targets"]["Veterinary"] = 15

    if "Hybrid Tamer" in out:
        p = out["Hybrid Tamer"]
        p["targets"]["Hit Chance Increase"] = 45
        p["targets"]["Defense Chance Increase"] = 45
        p["targets"]["Damage Increase"] = 100
        p["targets"]["Swing Speed Increase"] = 60
        p["targets"]["Lower Mana Cost"] = 40
        p["targets"]["Stamina Increase"] = 50
        p["targets"]["Hit Point Increase"] = 30
        p["targets"]["Dexterity Bonus"] = 30
        p["targets"]["Strength Bonus"] = 30
        p["targets"]["Mana Increase"] = 30
        p["targets"]["Mana Regeneration"] = 8
        p["targets"]["Hit Life Leech"] = 50
        p["targets"]["Hit Mana Leech"] = 50
        p["targets"]["Animal Taming"] = 20
        p["targets"]["Animal Lore"] = 20
        p["targets"]["Veterinary"] = 20
        p["targets"]["Parrying"] = 20
        p["targets"]["Bushido"] = 20
        p["targets"]["Spirit Speak"] = 20
        p["targets"]["Necromancy"] = 20

    if "Mystic Tank" in out:
        p = out["Mystic Tank"]
        p["targets"]["Physical Resist"] = 74
        p["targets"]["Fire Resist"] = 74
        p["targets"]["Cold Resist"] = 74
        p["targets"]["Poison Resist"] = 74
        p["targets"]["Energy Resist"] = 74
        p["targets"]["Lower Mana Cost"] = 40
        p["targets"]["Lower Reagent Cost"] = 100
        p["targets"]["Stamina Increase"] = 40
        p["targets"]["Hit Point Increase"] = 30
        p["targets"]["Reflect Physical Damage"] = 40
        p["targets"]["Faster Casting"] = 4
        p["targets"]["Faster Cast Recovery"] = 6
        p["targets"]["Mysticism"] = 20
        p["targets"]["Focus"] = 20
        p["targets"]["Parrying"] = 20
        p["targets"]["Hit Life Leech"] = 50
        p["targets"]["Hit Mana Leech"] = 50
        p["targets"]["Spell Channeling"] = 1

    if "Necro Weaver Tamer" in out:
        p = out["Necro Weaver Tamer"]
        p["targets"]["Spell Damage Increase"] = 150
        p["targets"]["Lower Mana Cost"] = 40
        p["targets"]["Mana Increase"] = 50
        p["targets"]["Mana Regeneration"] = 12
        p["targets"]["Faster Casting"] = 4
        p["targets"]["Faster Cast Recovery"] = 6
        p["targets"]["Intelligence Bonus"] = 30
        p["targets"]["Necromancy"] = 20
        p["targets"]["Spellweaving"] = 20
        p["targets"]["Animal Taming"] = 20
        p["targets"]["Animal Lore"] = 20
        p["targets"]["Spirit Speak"] = 20

    if "Archer Tamer" in out:
        p = out["Archer Tamer"]
        p["targets"]["Hit Chance Increase"] = 45
        p["targets"]["Swing Speed Increase"] = 60
        p["targets"]["Damage Increase"] = 100
        p["targets"]["Lower Mana Cost"] = 55
        p["targets"]["Stamina Increase"] = 50
        p["targets"]["Mana Increase"] = 50
        p["targets"]["Luck"] = 1200
        p["targets"]["Peacemaking"] = 26
        p["targets"]["Archery"] = 20
        p["targets"]["Animal Taming"] = 20
        p["targets"]["Animal Lore"] = 20

    return out


def sanitize_profile(name, raw):
    base = make_profile_record(name, _BUILTIN_BASE.get("Custom", {}))

    if not isinstance(raw, dict):
        return base

    req = raw.get("requirements", {})
    tar = raw.get("targets", {})
    wei = raw.get("weights", {})

    if isinstance(req, dict):
        for _, prop in PROFILE_FIELDS:
            try:
                base["requirements"][prop] = max(0, int(req.get(prop, base["requirements"].get(prop, 0)) or 0))
            except:
                pass

    if isinstance(tar, dict):
        for _, prop in PROFILE_FIELDS:
            try:
                base["targets"][prop] = max(0, int(tar.get(prop, base["targets"].get(prop, 0)) or 0))
            except:
                pass

    if isinstance(wei, dict):
        for _, prop in PROFILE_FIELDS:
            try:
                base["weights"][prop] = max(0, min(5, int(wei.get(prop, base["weights"].get(prop, 0)) or 0)))
            except:
                pass

    base["shield"] = bool(raw.get("shield", base.get("shield", False)))
    base["medable"] = bool(raw.get("medable", base.get("medable", False)))
    try:
        base["skill_budget"] = max(0, int(raw.get("skill_budget", base.get("skill_budget", 0)) or 0))
    except:
        base["skill_budget"] = 0
    try:
        base["skill_budget_priority"] = max(0, min(5, int(raw.get("skill_budget_priority", base.get("skill_budget_priority", 0)) or 0)))
    except:
        base["skill_budget_priority"] = 0
    core = raw.get("core_skills", {})
    if isinstance(core, dict):
        cleaned_core = {}
        for skill_name, values in core.items():
            if isinstance(values, dict):
                cleaned_core[str(skill_name)] = {
                    "base": float(values.get("base", 0) or 0),
                    "value": float(values.get("value", 0) or 0),
                    "cap": float(values.get("cap", 0) or 0),
                }
        base["core_skills"] = cleaned_core
    scan_source = raw.get("scan_source", {})
    base["scan_source"] = dict(scan_source) if isinstance(scan_source, dict) else {}
    base["name"] = str(name)
    return base


def profiles_path():
    return file_path(PROFILES_FILE)


def save_profiles_db():
    payload = {
        "format": 1,
        "suitmaster_version": VERSION,
        "profiles": _profiles,
    }
    safe_write_json(profiles_path(), payload)


def load_profiles_db():
    global _profiles, BUILD_NAMES, BUILD_PROFILES

    defaults = default_profiles()
    path = profiles_path()

    loaded = {}
    saved_version = ""
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                saved_version = str(payload.get("suitmaster_version", "") or "")
            raw_profiles = payload.get("profiles", payload) if isinstance(payload, dict) else {}
            if isinstance(raw_profiles, dict):
                for name, raw in raw_profiles.items():
                    clean_name = str(name or "").strip()
                    if clean_name:
                        loaded[clean_name] = sanitize_profile(clean_name, raw)
        except:
            loaded = {}

    # Built-ins always exist. Saved edits override defaults.
    merged = {}
    for name in BUILTIN_PROFILE_NAMES:
        # 2.2 materially changes the curated Basher logic. Upgrade that built-in
        # once from older profile databases; custom copies remain untouched.
        if name == "Basher" and not saved_version.startswith("2.2"):
            merged[name] = defaults[name]
        elif name == "Blood Tamer" and saved_version != "2.2d":
            # 2.2d replaces exact +Tactics/+Necro/+Vet requirements with a
            # flexible total equipment-skill budget.
            merged[name] = defaults[name]
        else:
            merged[name] = loaded.get(name, defaults[name])

    # Keep any named custom profiles. The old generic Luck built-in was split
    # into Luck Dexer + Luck Caster in 2.2c, so do not resurrect that obsolete
    # built-in from an older profile database.
    for name, profile in loaded.items():
        if name == "Luck":
            continue
        if name not in merged:
            merged[name] = profile

    _profiles = merged

    # Compatibility: older optimizer/UI code uses these globals.
    BUILD_PROFILES = _profiles
    BUILD_NAMES = sorted(
        list(_profiles.keys()),
        key=lambda n: profile_display_name(n).lower()
    )

    try:
        save_profiles_db()
    except:
        pass


def refresh_profile_names():
    global BUILD_NAMES, BUILD_PROFILES
    BUILD_PROFILES = _profiles
    BUILD_NAMES = sorted(
        list(_profiles.keys()),
        key=lambda n: profile_display_name(n).lower()
    )


def active_profile():
    if _build in _profiles:
        p = _profiles[_build]
    else:
        p = _profiles.get("Basher", default_profiles()["Basher"])

    return {
        "name": p.get("name", _build),
        "requirements": dict(p.get("requirements", {})),
        "targets": dict(p.get("targets", {})),
        "weights": dict(p.get("weights", {})),
        "shield": bool(p.get("shield", False)),
        "medable": bool(p.get("medable", False)),
        "skill_budget": int(p.get("skill_budget", 0) or 0),
        "skill_budget_priority": int(p.get("skill_budget_priority", 0) or 0),
        "core_skills": dict(p.get("core_skills", {}) or {}),
        "scan_source": dict(p.get("scan_source", {}) or {}),
    }


def score_totals(totals, profile):
    reqs = profile.get("requirements", {})
    targets = profile.get("targets", {})
    weights = profile.get("weights", {})

    score = 0.0

    # During beam expansion, reward progress toward every hard minimum equally
    # on a normalized basis. Final RC4 ranking applies a true hard gate; this
    # partial score only helps keep promising incomplete combinations alive.
    for p, minimum in reqs.items():
        minimum = int(minimum or 0)
        if minimum <= 0:
            continue

        actual = int(totals.get(p, 0) or 0)
        reached = min(max(actual, 0), minimum)
        score += (float(reached) / float(minimum)) * 1000000.0

    # Preferences contribute only when priority is above zero. Once a minimum
    # is met, priority 0 gives no benefit for overcapping that property.
    for p, weight in weights.items():
        w = int(weight or 0)
        if w <= 0:
            continue

        actual = max(0, int(totals.get(p, 0) or 0))
        target = int(targets.get(p, 0) or 0)
        if target <= 0:
            target = int(SCORE_CAPS.get(p, max(actual, 1)) or max(actual, 1))

        useful = min(actual, target)
        contribution = useful * w * 20.0

        # Luck and SSI define the Lucky Dexer. Luck already has a much larger
        # numeric range than SSI, so SSI gets an explicit profile-specific boost.
        if str(profile.get("name", "")) == "Luck Dexer":
            if p == "Swing Speed Increase":
                contribution *= 6.0
            elif p == "Luck":
                contribution *= 1.25

        score += contribution

    # Flexible equipment-skill budget. Any equipment skill points may satisfy
    # this pool; individual skill minimums can still be configured separately.
    budget = max(0, int(profile.get("skill_budget", 0) or 0))
    budget_priority = max(0, min(5, int(profile.get("skill_budget_priority", 0) or 0)))
    if budget > 0:
        actual_budget = sum(max(0, int(totals.get(skill_name, 0) or 0)) for skill_name in EQUIPMENT_SKILLS)
        reached = min(actual_budget, budget)
        score += (float(reached) / float(budget)) * 1000000.0
        if actual_budget < budget:
            score -= float(budget - actual_budget) * 1200.0
        if budget_priority > 0:
            score += min(actual_budget, budget) * budget_priority * 30.0

    return score


def item_rough_score(item, profile):
    props = effective_item_props(item)
    score = 0.0

    for p, minimum in profile.get("requirements", {}).items():
        value = int(props.get(p, 0) or 0)
        score += min(value, int(minimum or 0)) * 80.0

    targets = profile.get("targets", {})
    for p, w in profile.get("weights", {}).items():
        value = max(0, int(props.get(p, 0) or 0))
        target = int(targets.get(p, 0) or 0)
        if target <= 0:
            target = int(SCORE_CAPS.get(p, max(value, 1)) or max(value, 1))
        contribution = min(value, target) * int(w or 0) * 10.0
        if str(profile.get("name", "")) == "Luck Dexer":
            if p == "Swing Speed Increase":
                contribution *= 6.0
            elif p == "Luck":
                contribution *= 1.25
        score += contribution

    return score


def useful_upgrade_properties(best):
    profile = active_profile()
    totals = best.get("totals", {})
    deficits = best.get("deficits", {})
    wanted = []

    for p, deficit in deficits.items():
        wanted.append({
            "property": p,
            "reason": "hard_minimum_deficit",
            "needed_total": int(deficit),
            "priority": 5,
        })

    weighted = sorted(
        profile["weights"].items(),
        key=lambda kv: int(kv[1] or 0),
        reverse=True
    )

    for p, weight in weighted:
        weight = int(weight or 0)
        if weight <= 0:
            continue

        actual = int(totals.get(p, 0) or 0)
        target = int(profile.get("targets", {}).get(p, 0) or 0)
        if target <= 0:
            target = int(SCORE_CAPS.get(p, actual) or actual)

        if actual < target:
            wanted.append({
                "property": p,
                "reason": "weighted_upgrade",
                "current_total": actual,
                "soft_target": target,
                "priority": weight,
            })

    # Basher LMC is combination-dependent. If material has raised the cap above
    # the normal 40, tell LootMaster to keep looking for LMC up to that live cap.
    if _build == "Basher":
        lmc = best.get("lmc_state") or suit_lmc_state(best.get("items", []), totals)
        current_lmc = int(lmc.get("effective_lmc", 0) or 0)
        live_cap = int(lmc.get("cap", 40) or 40)
        if current_lmc < live_cap:
            existing = None
            for entry in wanted:
                if entry.get("property") == "Lower Mana Cost":
                    existing = entry
                    break
            if existing is not None:
                existing["soft_target"] = live_cap
                existing["reason"] = "basher_dynamic_lmc_target"
                existing["priority"] = 5
            else:
                wanted.append({
                    "property": "Lower Mana Cost",
                    "reason": "basher_dynamic_lmc_target",
                    "current_total": current_lmc,
                    "soft_target": live_cap,
                    "priority": 5,
                })

    return wanted


# ----------------------------
# Share code
# ----------------------------

def profile_share_payload(name):
    p = _profiles.get(name)
    if not p:
        return None

    # Format 2 carries every profile-defining setting. Character/chest serials
    # and cached scanned items are intentionally not part of a profile.
    return {
        "f": 2,
        "n": str(name),
        "r": p.get("requirements", {}),
        "t": p.get("targets", {}),
        "w": p.get("weights", {}),
        "s": 1 if p.get("shield", False) else 0,
        "m": 1 if p.get("medable", False) else 0,
        "b": int(p.get("skill_budget", 0) or 0),
        "bp": int(p.get("skill_budget_priority", 0) or 0),
        "cs": p.get("core_skills", {}),
        "src": p.get("scan_source", {}),
    }


def encode_profile_code(name):
    payload = profile_share_payload(name)
    if not payload:
        return ""

    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if zlib is not None:
        try:
            packed = zlib.compress(raw, 9)
            return "SM2Z:" + base64.urlsafe_b64encode(packed).decode("ascii")
        except:
            pass
    return "SM2:" + base64.urlsafe_b64encode(raw).decode("ascii")


def decode_profile_code(code):
    code = str(code or "").strip().replace("\n", "").replace("\r", "").replace(" ", "")
    if not code:
        raise ValueError("Profile code is empty.")

    if code.startswith("SM2Z:") or code.startswith("SM1Z:"):
        if zlib is None:
            raise ValueError("Compressed profile codes are not supported by this Python build.")
        packed = base64.urlsafe_b64decode(code[5:].encode("ascii"))
        raw = zlib.decompress(packed)
    elif code.startswith("SM2:") or code.startswith("SM1:"):
        raw = base64.urlsafe_b64decode(code[4:].encode("ascii"))
    else:
        raise ValueError("Not a SuitMaster profile code.")

    payload = json.loads(raw.decode("utf-8"))
    fmt = int(payload.get("f", 0) or 0) if isinstance(payload, dict) else 0
    if not isinstance(payload, dict) or fmt not in (1, 2):
        raise ValueError("Unsupported SuitMaster profile format.")

    name = str(payload.get("n", "Imported Profile") or "Imported Profile").strip()
    raw_profile = {
        "requirements": payload.get("r", {}),
        "targets": payload.get("t", {}),
        "weights": payload.get("w", {}),
        "shield": bool(payload.get("s", 0)),
        "medable": bool(payload.get("m", 0)),
        "skill_budget": int(payload.get("b", 0) or 0),
        "skill_budget_priority": int(payload.get("bp", 0) or 0),
        "core_skills": payload.get("cs", {}),
        "scan_source": payload.get("src", {}),
    }
    return name, sanitize_profile(name, raw_profile)


def unique_profile_name(base):
    base = str(base or "Custom Profile").strip() or "Custom Profile"
    if base not in _profiles:
        return base

    i = 2
    while True:
        candidate = "{} {}".format(base, i)
        if candidate not in _profiles:
            return candidate
        i += 1


# ----------------------------
# Input helpers
# ----------------------------

def create_text_input(text, width, height=28, multiline=False, font_size=15):
    try:
        tb = API.CreateGumpTextBox(str(text or ""), width, height, multiline, font_size)
    except:
        tb = API.CreateGumpTextBox(str(text or ""), width, height, multiline)
        try:
            tb.FontSize = font_size
        except:
            pass
    return tb


def read_text_input(tb):
    try:
        return str(tb.Text or "")
    except:
        return ""


# ----------------------------
# Build / visible gear scanners
# ----------------------------

PLAYER_STAT_MAP = {
    "Physical Resist": "PhysicalResistance",
    "Fire Resist": "FireResistance",
    "Cold Resist": "ColdResistance",
    "Poison Resist": "PoisonResistance",
    "Energy Resist": "EnergyResistance",
    "Hit Chance Increase": "HitChanceIncrease",
    "Defense Chance Increase": "DefenseChanceIncrease",
    "Damage Increase": "DamageIncrease",
    "Swing Speed Increase": "SwingSpeedIncrease",
    "Lower Mana Cost": "LowerManaCost",
    "Lower Reagent Cost": "LowerReagentCost",
    "Faster Casting": "FasterCasting",
    "Faster Cast Recovery": "FasterCastRecovery",
    "Spell Damage Increase": "SpellDamageIncrease",
    "Hit Point Increase": "HitPointsIncrease",
    "Stamina Increase": "StaminaIncrease",
    "Mana Increase": "ManaIncrease",
    "Hit Point Regeneration": "HitPointsRegeneration",
    "Stamina Regeneration": "StaminaRegeneration",
    "Mana Regeneration": "ManaRegeneration",
    "Strength Bonus": "StrengthIncrease",
    "Dexterity Bonus": "DexterityIncrease",
    "Intelligence Bonus": "IntelligenceIncrease",
    "Luck": "Luck",
    "Enhance Potions": "EnhancePotions",
    "Reflect Physical Damage": "ReflectPhysicalDamage",
}

VISIBLE_LAYERS = [
    "Helmet", "Necklace", "Earrings", "Bracelet", "Ring", "Talisman",
    "Gloves", "Arms", "InnerTorso", "MiddleTorso", "OuterTorso", "Cloak",
    "Waist", "Shirt", "Pants", "InnerLegs", "OuterLegs", "LeftHand", "RightHand"
]


def read_player_stats():
    out = {}
    for prop, attr in PLAYER_STAT_MAP.items():
        try:
            out[prop] = max(0, int(getattr(API.Player, attr)))
        except:
            out[prop] = 0
    return out


def read_player_skills():
    out = {}
    for skill_name in EQUIPMENT_SKILLS:
        try:
            sk = API.GetSkill(skill_name)
            if not sk:
                continue
            value = float(getattr(sk, "Value", 0) or 0)
            base = float(getattr(sk, "Base", value) or value)
            cap = float(getattr(sk, "Cap", 0) or 0)
            if value > 0 or base > 0:
                out[skill_name] = {"value": value, "base": base, "cap": cap}
        except:
            pass
    return out


def visible_equipment(serial_value):
    items = []
    seen = set()
    for layer_name in VISIBLE_LAYERS:
        try:
            item = API.FindLayer(layer_name, int(serial_value))
        except:
            item = None
        if not item:
            continue
        srl = serial(item)
        if not srl or srl in seen:
            continue
        seen.add(srl)
        opl = item_opl(item)
        slot = classify_slot(item, opl)
        if not slot:
            continue
        items.append({
            "serial": srl, "name": item_name(item), "slot": slot,
            "graphic": item_graphic(item), "hue": item_hue(item),
            "opl": opl, "props": parse_props(opl),
        })
    return items


def total_props_from_items(items):
    totals = dict((p, 0) for p in PROPERTIES)
    for item in items or []:
        props = effective_item_props(item)
        for prop in PROPERTIES:
            totals[prop] += int(props.get(prop, 0) or 0)
    return totals


def make_scanned_profile(name, player_stats=None, skills=None, gear_items=None, source_kind="self", source_name=""):
    player_stats = player_stats or {}
    skills = skills or {}
    gear_items = gear_items or []
    gear_totals = total_props_from_items(gear_items)
    raw = {"requirements": {}, "targets": {}, "weights": {}, "shield": False}

    # Start from the observed build, but only make baseline resists hard minimums.
    for prop in PROPERTIES:
        val = int(player_stats.get(prop, gear_totals.get(prop, 0)) or 0)
        if prop in RESISTS and val > 0:
            raw["requirements"][prop] = min(70, val)
            raw["targets"][prop] = max(min(75, val), raw["requirements"][prop])
            raw["weights"][prop] = 3
        elif val > 0 and prop not in EQUIPMENT_SKILLS:
            raw["targets"][prop] = val
            raw["weights"][prop] = 3

    # Skill budget comes from Value - Base on self scans. For visible-player
    # imports, use all visible +skill points from their equipment.
    if skills:
        skill_budget = int(round(sum(max(0.0, d.get("value", 0) - d.get("base", 0)) for d in skills.values())))
        core = dict((k, v) for k, v in skills.items() if float(v.get("base", 0) or 0) >= 50.0)
    else:
        skill_budget = sum(max(0, int(gear_totals.get(k, 0) or 0)) for k in EQUIPMENT_SKILLS)
        core = {}
    raw["skill_budget"] = skill_budget
    raw["skill_budget_priority"] = 5 if skill_budget else 0
    raw["core_skills"] = core
    raw["scan_source"] = {
        "kind": source_kind,
        "name": str(source_name or ""),
        "visible_gear_count": len(gear_items),
    }

    # Detect a visible shield.
    raw["shield"] = any(i.get("slot") == "Shield" for i in gear_items)
    return sanitize_profile(name, raw)


def scan_my_build_profile():
    global _build
    try:
        player_serial = int(API.Player.Serial)
    except:
        player_serial = 0
    if not player_serial:
        set_status("Could not read your player serial.", 33)
        return
    try:
        char_name = str(API.Player.Name or "My Build")
    except:
        char_name = "My Build"
    skills = read_player_skills()
    items = visible_equipment(player_serial)
    stats = read_player_stats()
    name = unique_profile_name("Scanned - " + char_name)
    _profiles[name] = make_scanned_profile(name, stats, skills, items, "self", char_name)
    save_profiles_db(); refresh_profile_names()
    _build = name; pset(KEY_BUILD, _build); save_settings()
    set_status("Scanned your build: {} skill pts from gear, {} visible items.".format(
        _profiles[name].get("skill_budget", 0), len(items)), 68)
    show_profile_editor(name)
    refresh_main()


def inspect_player_profile():
    global _build, _profile_gump

    # Hide the large Profiles window while the player is choosing a target so
    # the world/paperdoll stays visible. Re-open it if the operation is cancelled
    # or fails; a successful import opens the new profile editor instead.
    if _profile_gump is not None:
        try:
            save_gump_position(_profile_gump, False)
        except:
            pass
        dispose(_profile_gump)
        _profile_gump = None

    target = request_target("Target the player whose VISIBLE equipment you want to import.")
    if not target:
        set_status("No player selected.", 33)
        show_profile_manager()
        return
    try:
        mob = API.FindMobile(int(target))
    except:
        mob = None
    if not mob:
        set_status("That target is not a visible mobile.", 33)
        show_profile_manager()
        return
    try:
        target_name = str(mob.Name or "Player")
    except:
        target_name = "Player"
    items = visible_equipment(int(target))
    if not items:
        set_status("No readable equipped items found on that player.", 33)
        show_profile_manager()
        return
    name = unique_profile_name("Visible Gear - " + target_name)
    _profiles[name] = make_scanned_profile(name, {}, {}, items, "visible_player", target_name)
    save_profiles_db(); refresh_profile_names()
    _build = name; pset(KEY_BUILD, _build); save_settings()
    set_status("Imported {} visible items from {}. Hidden skills/stats are not available.".format(len(items), target_name), 68)
    show_profile_editor(name)
    refresh_main()


# ----------------------------
# Profile manager
# ----------------------------

def dispose_profile_windows():
    global _profile_gump, _profile_editor_gump, _share_gump, _import_gump
    for g in (_profile_gump, _profile_editor_gump, _share_gump, _import_gump):
        if g is not None:
            dispose(g)


def show_profile_manager():
    global _profile_gump

    if _profile_gump is not None:
        dispose(_profile_gump)

    refresh_profile_names()

    W = 820
    H = 500
    g = API.CreateGump(True, True, True)
    gx, gy = load_gump_pos("profiles", 460, 170)
    g.SetRect(gx, gy, W, H)
    register_gump_position(g, "profiles")

    bg = API.CreateGumpColorBox(0.97, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "SUITMASTER PROFILES", 22, 16, 430, 30, 21, C_TITLE)
    add_label(
        g,
        "Built-ins and custom profiles use the same Minimum / Target / Priority model.",
        22, 50, 760, 24, 12, C_MUTED
    )

    add_panel(g, 16, 88, 788, 128)
    add_label(g, "PROFILE", 32, 101, 100, 22, 13, C_GOLD)

    try:
        idx = BUILD_NAMES.index(_build)
    except:
        idx = 0

    dd = API.CreateDropDown(315, [profile_display_name(n) for n in BUILD_NAMES], idx)
    dd.SetPos(32, 132)
    g.Add(dd)

    def selected_name():
        try:
            i = int(dd.GetSelectedIndex())
        except:
            i = 0
        return BUILD_NAMES[i] if 0 <= i < len(BUILD_NAMES) else BUILD_NAMES[0]

    def use_selected():
        global _build
        name = selected_name()
        _build = name
        pset(KEY_BUILD, _build)
        save_settings()
        set_status("Build profile: " + profile_display_name(_build), 68)
        refresh_main()
        dispose(g)

    def edit_selected():
        show_profile_editor(selected_name())

    def duplicate_selected():
        source_name = selected_name()
        new_name = unique_profile_name(source_name + " Copy")
        _profiles[new_name] = sanitize_profile(new_name, copy.deepcopy(_profiles[source_name]))
        _profiles[new_name]["name"] = new_name
        save_profiles_db()
        refresh_profile_names()
        set_status("Created profile: " + new_name, 68)
        dispose(g)
        show_profile_manager()

    def delete_selected():
        global _build
        name = selected_name()
        if name in BUILTIN_PROFILE_NAMES:
            set_status("Built-in profiles cannot be deleted. Use RESET DEFAULT instead.", 33)
            return

        if name in _profiles:
            del _profiles[name]
            if _build == name:
                _build = "Basher"
                pset(KEY_BUILD, _build)
            save_profiles_db()
            refresh_profile_names()
            set_status("Deleted profile: " + name, 68)
            dispose(g)
            show_profile_manager()
            refresh_main()

    def reset_selected():
        name = selected_name()
        if name not in BUILTIN_PROFILE_NAMES:
            set_status("RESET DEFAULT is only for built-in profiles.", 33)
            return

        _profiles[name] = default_profiles()[name]
        save_profiles_db()
        set_status("Reset {} to SuitMaster defaults.".format(name), 68)
        dispose(g)
        show_profile_manager()

    add_button(g, "USE", 365, 130, 75, 28, use_selected)
    add_button(g, "SKILLS", 450, 130, 85, 28, lambda: show_profile_skills(selected_name()))
    add_button(g, "EDIT", 545, 130, 75, 28, edit_selected)
    add_button(g, "DUPLICATE", 630, 130, 95, 28, duplicate_selected)
    add_button(g, "DELETE", 735, 130, 60, 28, delete_selected)

    add_label(
        g,
        "Active: {}".format(profile_display_name(_build)),
        32, 170, 430, 22, 12, C_TEXT
    )
    creator_text = profile_creator(_build)
    add_label(
        g,
        profile_description(_build),
        32, 188, 550, 20, 10, C_MUTED
    )
    if creator_text:
        add_label(g, "Build by: " + creator_text, 32, 207, 360, 18, 10, C_GOLD)
    add_button(g, "RESET DEFAULT", 610, 174, 172, 28, reset_selected)

    add_panel(g, 16, 228, 788, 154)
    add_label(g, "SHARE / CREATE", 32, 241, 180, 22, 13, C_GOLD)
    add_label(
        g,
        "Share codes include the COMPLETE profile: mins, targets, priorities, shield/medable rules, skill budget and scan metadata. No item/chest serials.",
        32, 270, 735, 24, 12, C_TEXT
    )

    def new_profile():
        new_name = unique_profile_name("New Profile")
        _profiles[new_name] = sanitize_profile(
            new_name,
            copy.deepcopy(_profiles.get("Custom", default_profiles()["Custom"]))
        )
        _profiles[new_name]["name"] = new_name
        save_profiles_db()
        refresh_profile_names()
        show_profile_editor(new_name)

    add_button(g, "NEW PROFILE", 32, 316, 155, 30, new_profile)
    add_button(g, "SCAN MY BUILD", 32, 354, 155, 30, scan_my_build_profile)
    add_button(g, "INSPECT PLAYER", 199, 354, 155, 30, inspect_player_profile)
    add_button(g, "SHARE CODE", 199, 316, 155, 30, lambda: show_share_code(selected_name()))
    add_button(g, "IMPORT CODE", 366, 316, 155, 30, show_import_code)
    add_button(g, "CLOSE", 672, 402, 110, 30, lambda: dispose(g))

    _profile_gump = g
    add_save_pos_button(g)
    API.AddGump(g)


def show_share_code(name):
    global _share_gump

    if _share_gump is not None:
        dispose(_share_gump)

    code = encode_profile_code(name)
    W = 900
    H = 315

    g = API.CreateGump(True, True, True)
    gx, gy = load_gump_pos("share", 420, 235)
    g.SetRect(gx, gy, W, H)
    register_gump_position(g, "share")

    bg = API.CreateGumpColorBox(0.98, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "SHARE PROFILE: " + str(name), 22, 16, 700, 28, 19, C_TITLE)
    add_label(
        g,
        "Click in the code box, Ctrl+A, Ctrl+C, then send it to another SuitMaster user.",
        22, 50, 840, 24, 12, C_TEXT
    )

    box = create_text_input(code, 856, 135, True, 13)
    box.SetPos(22, 88)
    g.Add(box)

    add_label(
        g,
        "The receiver uses PROFILES > IMPORT CODE and pastes the entire SM2 code.",
        22, 235, 820, 22, 11, C_MUTED
    )

    add_button(g, "CLOSE", 758, 270, 120, 28, lambda: dispose(g))

    try:
        box.SetFocus()
    except:
        pass

    _share_gump = g
    add_save_pos_button(g)
    API.AddGump(g)


def show_import_code():
    global _import_gump

    if _import_gump is not None:
        dispose(_import_gump)

    W = 900
    H = 350

    g = API.CreateGump(True, True, True)
    gx, gy = load_gump_pos("import", 420, 220)
    g.SetRect(gx, gy, W, H)
    register_gump_position(g, "import")

    bg = API.CreateGumpColorBox(0.98, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "IMPORT PROFILE CODE", 22, 16, 500, 28, 19, C_TITLE)
    add_label(
        g,
        "Paste a SuitMaster SM2 code (older SM1 codes are also accepted).",
        22, 50, 800, 24, 12, C_TEXT
    )

    box = create_text_input("", 856, 165, True, 13)
    box.SetPos(22, 84)
    try:
        box.SetPlaceholder("SM2Z:...")
    except:
        pass
    g.Add(box)

    def do_import():
        try:
            original_name, profile = decode_profile_code(read_text_input(box))
            name = unique_profile_name(original_name)
            profile["name"] = name
            _profiles[name] = profile
            save_profiles_db()
            refresh_profile_names()
            set_status("Imported SuitMaster profile: " + name, 68)
            dispose(g)
            show_profile_manager()
            refresh_main()
        except Exception as e:
            set_status("Profile import failed: " + str(e), 33)

    add_button(g, "IMPORT", 22, 282, 145, 30, do_import)
    add_button(g, "CLOSE", 758, 282, 120, 30, lambda: dispose(g))

    try:
        box.SetFocus()
    except:
        pass

    _import_gump = g
    add_save_pos_button(g)
    API.AddGump(g)



# ----------------------------
# Build skills viewer
# ----------------------------

def show_profile_skills(profile_name):
    global _skills_gump

    if _skills_gump is not None:
        dispose(_skills_gump)

    rows = profile_skills(profile_name)
    W = 900
    H = 560

    g = API.CreateGump(True, True, True)
    gx, gy = load_gump_pos("skills", 465, 135)
    g.SetRect(gx, gy, W, H)
    register_gump_position(g, "skills")

    bg = API.CreateGumpColorBox(0.98, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(
        g,
        profile_display_name(profile_name).upper(),
        22, 14, 680, 32, 20, C_TITLE
    )
    creator = profile_creator(profile_name)
    add_label(
        g,
        profile_description(profile_name),
        22, 47, 840, 38, 11, C_MUTED
    )
    if creator:
        add_label(g, "Build by: " + creator, 22, 84, 420, 20, 10, C_GOLD)

    add_panel(g, 16, 112, 868, 360)
    add_label(g, "SKILL", 32, 126, 235, 24, 12, C_GOLD)
    add_label(g, "TARGET", 315, 126, 105, 24, 12, C_GOLD)
    add_label(g, "ROLE / NOTES", 440, 126, 415, 24, 12, C_GOLD)

    y = 160
    for skill, target, note in rows[:10]:
        add_label(g, str(skill), 32, y, 265, 24, 12, C_TEXT)
        add_label(g, str(target), 315, y, 105, 24, 12, C_TITLE)
        add_label(g, str(note), 440, y, 420, 36, 11, C_TEXT)
        y += 34

    note = profile_note(profile_name)
    if profile_name in DEXER_PROFILE_NAMES:
        swing_tip = "Max-swing reference: at 60 SSI -> Katana 30 stam (52 buffered), War Axe 90 (112), Broadsword/Whip/Hammer Pick 120 (142), Longsword 150 (172)."
        note = (note + "  " if note else "") + swing_tip
    if note:
        add_label(g, note, 32, 485, 690, 58, 10, C_MUTED)

    add_button(g, "EDIT PROFILE", 730, 500, 145, 32, lambda: show_profile_editor(profile_name))
    add_button(g, "CLOSE", 730, 534, 145, 24, lambda: dispose(g))

    _skills_gump = g
    add_save_pos_button(g)
    API.AddGump(g)


# ----------------------------
# Profile editor
# ----------------------------

def show_profile_editor(profile_name, section_name=None):
    """Compact, sectioned profile editor. Avoids the old 50+ row overflow gump."""
    global _profile_editor_gump

    if profile_name not in _profiles:
        return

    if _profile_editor_gump is not None:
        dispose(_profile_editor_gump)

    source = _profiles[profile_name]

    # Build compact editor pages. Any category with too many properties is
    # automatically split into numbered pages so it can never overflow the gump.
    raw_sections = {}
    raw_order = []
    for category, prop in PROFILE_FIELDS:
        if category not in raw_sections:
            raw_sections[category] = []
            raw_order.append(category)
        raw_sections[category].append(prop)

    MAX_FIELDS_PER_PAGE = 8
    section_order = []
    section_fields = {}
    for category in raw_order:
        fields = raw_sections.get(category, [])
        if len(fields) <= MAX_FIELDS_PER_PAGE:
            section_order.append(category)
            section_fields[category] = fields
        else:
            pages = (len(fields) + MAX_FIELDS_PER_PAGE - 1) // MAX_FIELDS_PER_PAGE
            for page in range(pages):
                label = "{} {}/{}".format(category, page + 1, pages)
                start = page * MAX_FIELDS_PER_PAGE
                section_order.append(label)
                section_fields[label] = fields[start:start + MAX_FIELDS_PER_PAGE]

    if section_name not in section_fields:
        section_name = section_order[0]

    W = 840
    H = 610

    g = API.CreateGump(True, True, True)
    gx, gy = load_gump_pos("editor", 360, 105)
    g.SetRect(gx, gy, W, H)
    register_gump_position(g, "editor")

    bg = API.CreateGumpColorBox(0.98, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "PROFILE EDITOR", 20, 12, 260, 30, 21, C_TITLE)
    add_label(g, "Minimum = must reach | Target = useful cap | Priority: 0 = IGNORE, 5 = HIGHEST", 270, 18, 535, 22, 10, C_MUTED)

    add_label(g, "Profile name", 20, 57, 120, 22, 12, C_GOLD)
    name_box = create_text_input(profile_name, 300, 30, False, 16)
    name_box.SetPos(140, 52)
    g.Add(name_box)

    shield_cb = API.CreateGumpCheckbox("", 0, bool(source.get("shield", False)))
    shield_cb.SetPos(474, 57)
    g.Add(shield_cb)
    add_label(g, "Require Shield", 500, 57, 140, 22, 12, C_TEXT)

    medable_cb = API.CreateGumpCheckbox("", 0, bool(source.get("medable", False)))
    medable_cb.SetPos(474, 84)
    g.Add(medable_cb)
    add_label(g, "Keep Suit Medable", 500, 84, 155, 22, 12, C_TEXT)

    add_label(g, "Skill pts", 650, 57, 65, 22, 11, C_GOLD)
    skill_budget_box = create_text_input(str(int(source.get("skill_budget", 0) or 0)), 52, 27, False, 13)
    skill_budget_box.SetPos(712, 52)
    try: skill_budget_box.NumbersOnly = True
    except: pass
    g.Add(skill_budget_box)
    skill_prio_dd = API.CreateDropDown(58, ["0", "1", "2", "3", "4", "5"], max(0, min(5, int(source.get("skill_budget_priority", 0) or 0))))
    skill_prio_dd.SetPos(770, 52)
    g.Add(skill_prio_dd)

    add_label(g, "SECTION", 20, 116, 80, 22, 11, C_GOLD)
    section_dd = API.CreateDropDown(235, section_order, section_order.index(section_name))
    section_dd.SetPos(100, 112)
    g.Add(section_dd)

    add_label(g, "Edit one page at a time. OPEN PAGE keeps edits in memory. Skill pts = flexible TOTAL +skill required from gear.",
              355, 115, 455, 38, 10, C_MUTED)

    add_panel(g, 16, 156, 808, 374)
    add_label(g, section_name, 32, 170, 280, 22, 13, C_TITLE)
    add_label(g, "PROPERTY", 32, 200, 300, 20, 11, C_GOLD)
    add_label(g, "MIN", 470, 200, 55, 20, 11, C_GOLD)
    add_label(g, "TARGET", 555, 200, 70, 20, 11, C_GOLD)
    add_label(g, "PRIORITY", 655, 200, 90, 20, 11, C_GOLD)

    controls = {}
    y = 232
    for prop in section_fields[section_name]:
        add_label(g, prop, 32, y + 4, 390, 22, 12, C_TEXT)

        min_box = create_text_input(str(int(source.get("requirements", {}).get(prop, 0) or 0)), 64, 27, False, 14)
        min_box.SetPos(465, y)
        try: min_box.NumbersOnly = True
        except: pass
        g.Add(min_box)

        target_box = create_text_input(str(int(source.get("targets", {}).get(prop, 0) or 0)), 72, 27, False, 14)
        target_box.SetPos(550, y)
        try: target_box.NumbersOnly = True
        except: pass
        g.Add(target_box)

        current_priority = max(0, min(5, int(source.get("weights", {}).get(prop, 0) or 0)))
        prio_dd = API.CreateDropDown(82, ["0", "1", "2", "3", "4", "5"], current_priority)
        prio_dd.SetPos(650, y)
        g.Add(prio_dd)

        controls[prop] = (min_box, target_box, prio_dd)
        y += 38

    def capture_page():
        data = {
            "requirements": dict(source.get("requirements", {})),
            "targets": dict(source.get("targets", {})),
            "weights": dict(source.get("weights", {})),
            "shield": bool(source.get("shield", False)),
            "medable": bool(source.get("medable", False)),
            "skill_budget": int(source.get("skill_budget", 0) or 0),
            "skill_budget_priority": int(source.get("skill_budget_priority", 0) or 0),
            "core_skills": dict(source.get("core_skills", {}) or {}),
            "scan_source": dict(source.get("scan_source", {}) or {}),
        }
        for prop, trio in controls.items():
            min_box, target_box, prio_dd = trio
            try: data["requirements"][prop] = max(0, int(read_text_input(min_box).strip() or "0"))
            except: data["requirements"][prop] = 0
            try: data["targets"][prop] = max(0, int(read_text_input(target_box).strip() or "0"))
            except: data["targets"][prop] = 0
            try: data["weights"][prop] = max(0, min(5, int(prio_dd.GetSelectedIndex())))
            except: data["weights"][prop] = 0
            if data["requirements"][prop] > 0 and data["targets"][prop] < data["requirements"][prop]:
                data["targets"][prop] = data["requirements"][prop]

        try: data["shield"] = bool(shield_cb.GetIsChecked())
        except:
            try: data["shield"] = bool(shield_cb.IsChecked)
            except: pass
        try: data["medable"] = bool(medable_cb.GetIsChecked())
        except:
            try: data["medable"] = bool(medable_cb.IsChecked)
            except: pass
        try: data["skill_budget"] = max(0, int(read_text_input(skill_budget_box).strip() or "0"))
        except: data["skill_budget"] = 0
        try: data["skill_budget_priority"] = max(0, min(5, int(skill_prio_dd.GetSelectedIndex())))
        except: data["skill_budget_priority"] = 0
        return data

    def open_section():
        try: index = int(section_dd.GetSelectedIndex())
        except: index = 0
        index = max(0, min(len(section_order) - 1, index))
        # Preserve edits made on this page in memory while navigating sections.
        _profiles[profile_name] = sanitize_profile(profile_name, capture_page())
        show_profile_editor(profile_name, section_order[index])

    def save_editor():
        global _build
        requested_name = read_text_input(name_box).strip()
        if not requested_name:
            set_status("Profile name cannot be blank.", 33)
            return

        data = capture_page()
        if requested_name != profile_name:
            if requested_name in _profiles:
                set_status("A profile with that name already exists.", 33)
                return
            _profiles[requested_name] = sanitize_profile(requested_name, data)
            if profile_name not in BUILTIN_PROFILE_NAMES:
                try: del _profiles[profile_name]
                except: pass
            if _build == profile_name:
                _build = requested_name
                pset(KEY_BUILD, _build)
        else:
            _profiles[profile_name] = sanitize_profile(profile_name, data)

        save_profiles_db()
        refresh_profile_names()
        save_settings()
        set_status("Saved profile: " + requested_name, 68)
        dispose(g)
        show_profile_manager()
        refresh_main()

    def share_current():
        requested_name = read_text_input(name_box).strip() or profile_name
        _profiles[requested_name] = sanitize_profile(requested_name, capture_page())
        show_share_code(requested_name)

    add_button(g, "OPEN PAGE", 20, 552, 145, 32, open_section)
    add_button(g, "SAVE PROFILE", 180, 552, 150, 32, save_editor)
    add_button(g, "SHARE CODE", 345, 552, 135, 32, share_current)
    add_button(g, "CLOSE", 690, 552, 125, 32, lambda: dispose(g))

    _profile_editor_gump = g
    add_save_pos_button(g)
    API.AddGump(g)


# ----------------------------
# Main gump v2
# ----------------------------

def set_build_from_dropdown(dd):
    global _build
    try:
        i = int(dd.GetSelectedIndex())
    except:
        i = 0

    if 0 <= i < len(BUILD_NAMES):
        _build = BUILD_NAMES[i]
        pset(KEY_BUILD, _build)
        save_settings()
        set_status("Build profile: " + profile_display_name(_build), 68)
        refresh_main()


def refresh_main():
    global _main_gump
    if _main_gump is not None:
        dispose(_main_gump)
    show_main()


def show_main():
    global _main_gump

    refresh_profile_names()

    W = 790
    H = 500
    x, y = load_gump_pos("main", *load_pos())

    g = API.CreateGump(True, True, True)
    g.SetRect(x, y, W, H)
    register_gump_position(g, "main")

    bg = API.CreateGumpColorBox(0.97, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "J.C.S. SUITMASTER", 20, 12, 430, 30, 22, C_TITLE)
    add_label(g, "v" + VERSION, 675, 18, 90, 20, 11, C_MUTED, "right")

    # STORAGE
    add_panel(g, 14, 52, 762, 180)
    add_label(g, "STORAGE", 30, 66, 130, 22, 13, C_GOLD)

    chest_count = len(_chests)
    add_label(
        g,
        "{} gear chest{} configured".format(chest_count, "" if chest_count == 1 else "s"),
        30, 96, 300, 24, 14, C_TEXT
    )

    if _chests:
        preview = "   ".join("0x{:X}".format(v) for v in _chests[:4])
        if len(_chests) > 4:
            preview += "   +{} more".format(len(_chests) - 4)
        add_label(g, preview, 30, 123, 720, 22, 11, C_MUTED)

    add_label(
        g,
        "Pull bag: " + ("0x{:X}".format(_pull_bag) if _pull_bag else "Not set"),
        30, 151, 320, 23, 13, C_TEXT
    )

    add_button(g, "ADD CHEST", 30, 187, 125, 30, add_chest)
    add_button(g, "REMOVE", 166, 187, 105, 30, remove_chest)
    add_button(g, "CLEAR", 282, 187, 95, 30, clear_chests)
    add_button(g, "SET PULL BAG", 388, 187, 145, 30, target_pull_bag)
    add_button(g, "SCAN ALL", 621, 187, 135, 30, scan_chest)

    # BUILD
    add_panel(g, 14, 244, 762, 130)
    add_label(g, "BUILD PROFILE", 30, 258, 180, 22, 13, C_GOLD)

    try:
        idx = BUILD_NAMES.index(_build)
    except:
        idx = 0

    dd = API.CreateDropDown(270, [profile_display_name(n) for n in BUILD_NAMES], idx)
    dd.SetPos(30, 292)
    g.Add(dd)

    add_button(g, "USE", 312, 290, 75, 31, lambda: set_build_from_dropdown(dd))
    add_button(g, "SKILLS", 397, 290, 90, 31, lambda: show_profile_skills(_build))
    add_button(g, "PROFILES", 497, 290, 105, 31, show_profile_manager)
    add_button(g, "PREVIEW SUIT", 612, 290, 144, 31, optimize)

    profile = active_profile()
    req_count = len([v for v in profile.get("requirements", {}).values() if int(v or 0) > 0])
    priority_count = len([v for v in profile.get("weights", {}).values() if int(v or 0) > 0])

    add_label(
        g,
        "{}  |  {} hard minimums  |  {} weighted stats{}".format(
            profile_display_name(_build),
            req_count,
            priority_count,
            "  |  shield required" if profile.get("shield") else ""
        ),
        30, 328, 720, 23, 12, C_TEXT
    )
    creator = profile_creator(_build)
    desc = profile_description(_build)
    if creator:
        desc += "  |  Build by: " + creator
    add_label(
        g,
        desc,
        30, 350, 720, 20, 10, C_MUTED
    )

    # STATUS
    add_panel(g, 14, 386, 762, 96)
    add_label(g, "STATUS", 30, 400, 100, 22, 12, C_GOLD)

    result_text = "{} wearable items cached".format(len(_items))
    if _best:
        result_text += "  |  {} preview ready".format(_best.get("build", _build))
    add_label(g, result_text, 30, 426, 700, 22, 12, C_MUTED)
    add_label(g, _status, 30, 449, 720, 28, 12, C_TEXT)

    _main_gump = g
    add_save_pos_button(g)
    API.AddGump(g)


# ----------------------------
# Settings v2
# ----------------------------

def save_settings():
    payload = {
        "version": VERSION,
        "chests": [int(x) for x in _chests],
        "pull_bag": int(_pull_bag or 0),
        "mannequin": int(_mannequin or 0),
        "build": _build,
    }
    try:
        safe_write_json(file_path(SETTINGS_FILE), payload)
    except:
        pass


def load_settings():
    global _chests, _pull_bag, _mannequin, _build

    load_profiles_db()

    _chests = load_chests()

    try:
        _pull_bag = int(pget(KEY_PULL_BAG, "0") or 0)
    except:
        _pull_bag = 0

    try:
        _mannequin = int(pget(KEY_MANNEQUIN, "0") or 0)
    except:
        _mannequin = 0

    requested_build = str(pget(KEY_BUILD, "Basher") or "Basher")

    path = file_path(SETTINGS_FILE)
    legacy_custom = None

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                d = json.load(f)

            saved_chests = d.get("chests")
            if isinstance(saved_chests, list):
                clean = []
                for x in saved_chests:
                    try:
                        s = int(x or 0)
                        if s and s not in clean:
                            clean.append(s)
                    except:
                        pass
                if clean:
                    _chests = clean

            if not _chests:
                try:
                    legacy = int(d.get("chest", 0) or 0)
                    if legacy:
                        _chests = [legacy]
                except:
                    pass

            _pull_bag = int(d.get("pull_bag", _pull_bag) or _pull_bag)
            _mannequin = int(d.get("mannequin", _mannequin) or _mannequin)

            b = str(d.get("build", requested_build) or requested_build)
            requested_build = b

            # Migrate Custom edits from alpha 0.8 and earlier.
            cp = d.get("custom_profile")
            if isinstance(cp, dict):
                legacy_custom = cp
        except:
            pass

    if legacy_custom:
        migrated = sanitize_profile("Custom", legacy_custom)
        _profiles["Custom"] = migrated
        try:
            save_profiles_db()
        except:
            pass

    refresh_profile_names()
    _build = requested_build if requested_build in _profiles else "Basher"
    pset(KEY_BUILD, _build)

    save_chests()
    load_cache()


# Safety override: normal Legion EquipItem only equips the player, not a
# mannequin paperdoll. Keep this function inert until TazUO exposes a safe path.
def place_best_on_mannequin():
    set_status(
        "Mannequin dressing is paused: Legion currently exposes player EquipItem, not mannequin paperdoll equip.",
        33
    )
    return False




# ============================================================
# SUITMASTER 2.0 - DEXXER / LOCK / CANDIDATE SYSTEM
# ============================================================

LOCKS_FILE = "JCS_SuitMaster_Locks.json"

_top_suits = []
_candidate_index = 0
_locked_items = {}

# Melee dexxers commonly swap among slayer weapons. SuitMaster therefore
# optimizes against the slower common 3.25-speed case rather than one exact
# weapon. Weapon SSI is assumed to be zero unless this is expanded later.
MELEE_DEXXER_PROFILES = {
    "Basher",
    "Sampire",
    "Blood Knight",
    "Hybrid Tamer",
    "Mystic Tank",
}

DEX_SWING_DEFAULT = {
    "weapon_speed": 3.25,
    "weapon_ssi": 0,
    "debuff_buffer": 22,
    "stamina_first": True,
}


def locks_path():
    return file_path(LOCKS_FILE)


def save_locks():
    try:
        safe_write_json(
            locks_path(),
            {
                "format": 1,
                "locks": dict((str(k), int(v)) for k, v in _locked_items.items())
            }
        )
    except:
        pass


def load_locks():
    global _locked_items

    _locked_items = {}
    path = locks_path()
    if not os.path.exists(path):
        return

    try:
        with open(path, "r") as f:
            d = json.load(f)

        raw = d.get("locks", {}) if isinstance(d, dict) else {}
        if isinstance(raw, dict):
            for slot, value in raw.items():
                try:
                    serial_value = int(value or 0)
                    if slot in SLOTS and serial_value:
                        _locked_items[slot] = serial_value
                except:
                    pass
    except:
        _locked_items = {}


def locked_item_entries():
    out = []
    if not _locked_items:
        return out

    by_serial = {}
    for item in _items:
        try:
            by_serial[int(item.get("serial", 0) or 0)] = item
        except:
            pass

    for slot, serial_value in list(_locked_items.items()):
        item = by_serial.get(int(serial_value))
        if item:
            out.append(item)

    return out


def lock_target_item():
    global _locked_items

    if not _items:
        set_status("Scan your gear chests before locking an item.", 33)
        return

    try:
        API.SysMsg("Target the armor, jewelry, talisman, or shield to lock.", 68)
        target = int(API.RequestTarget() or 0)
    except:
        target = 0

    if not target:
        set_status("No item selected.", 33)
        return

    match = None
    for item in _items:
        if int(item.get("serial", 0) or 0) == target:
            match = item
            break

    if not match:
        set_status("That item is not in the current SuitMaster scan.", 33)
        return

    slot = match.get("slot")
    if slot not in SLOTS:
        set_status("SuitMaster cannot lock that item slot.", 33)
        return

    _locked_items[slot] = target
    save_locks()
    set_status("Locked {}: {}".format(slot, match.get("name", "item")), 68)
    refresh_main()


def clear_locked_items():
    global _locked_items
    _locked_items = {}
    save_locks()
    set_status("All locked suit pieces cleared.", 68)
    refresh_main()


def dex_swing_state(totals, profile_name=None):
    """
    Return the stamina/SSI state for the common melee loadout.

    Stamina is estimated as:
      naked/base DEX + suit DEX Bonus + suit Stamina Increase

    The 22-point buffered thresholds come from the supplied InsaneUO community
    max-swing chart. SuitMaster deliberately favors stamina over SSI because
    stamina has broader combat value and survives weapon swaps better.
    """
    name = profile_name or _build

    if name not in MELEE_DEXXER_PROFILES:
        return None

    base = player_base_stats()
    projected_stamina = (
        int(base.get("dexterity", 0))
        + int(totals.get("Dexterity Bonus", 0) or 0)
        + int(totals.get("Stamina Increase", 0) or 0)
    )

    suit_ssi = int(totals.get("Swing Speed Increase", 0) or 0)
    weapon_ssi = int(DEX_SWING_DEFAULT.get("weapon_ssi", 0) or 0)
    total_ssi = max(0, suit_ssi + weapon_ssi)

    speed = float(DEX_SWING_DEFAULT["weapon_speed"])
    buffer_enabled = bool(DEX_SWING_DEFAULT.get("debuff_buffer", 0))
    use_buffer = True if buffer_enabled else False

    # Find the smallest SSI breakpoint that this stamina total safely supports.
    required_ssi = None
    required_stamina = None

    for candidate_ssi in sorted(SWING_SPEED_GUIDE.get(speed, {}).keys()):
        req = swing_speed_requirement(speed, candidate_ssi, use_buffer)
        if req is None:
            continue

        if projected_stamina >= int(req):
            required_ssi = int(candidate_ssi)
            required_stamina = int(req)
            break

    if required_ssi is None:
        # Character is below even the highest-SSI buffered stamina row.
        available = []
        for candidate_ssi in sorted(SWING_SPEED_GUIDE.get(speed, {}).keys()):
            req = swing_speed_requirement(speed, candidate_ssi, use_buffer)
            if req is not None:
                available.append((candidate_ssi, req))
        if available:
            required_ssi, required_stamina = available[-1]

    meets = (
        required_ssi is not None
        and projected_stamina >= int(required_stamina)
        and total_ssi >= int(required_ssi)
    )

    stamina_short = 0
    ssi_short = 0

    if required_stamina is not None:
        stamina_short = max(0, int(required_stamina) - projected_stamina)
    if required_ssi is not None:
        ssi_short = max(0, int(required_ssi) - total_ssi)

    return {
        "weapon_speed": speed,
        "projected_stamina": projected_stamina,
        "suit_ssi": suit_ssi,
        "weapon_ssi": weapon_ssi,
        "total_ssi": total_ssi,
        "required_ssi": required_ssi,
        "required_stamina": required_stamina,
        "stamina_short": stamina_short,
        "ssi_short": ssi_short,
        "meets_max_swing": meets,
        "buffer": int(DEX_SWING_DEFAULT.get("debuff_buffer", 0) or 0),
    }


def dex_swing_adjustment(totals, profile_name=None):
    state = dex_swing_state(totals, profile_name)
    if not state:
        return 0.0

    # Missing max swing is a major combat penalty.
    if not state["meets_max_swing"]:
        return -(
            250000.0
            + state["stamina_short"] * 15000.0
            + state["ssi_short"] * 10000.0
        )

    # Once max swing is reached, reward the stamina route and discourage
    # unnecessary SSI. This explicitly encodes the user's stamina-first rule.
    stamina = float(state["projected_stamina"])
    excess_ssi = max(0, state["total_ssi"] - int(state["required_ssi"] or 0))

    return stamina * 180.0 - excess_ssi * 90.0


def basher_suit_adjustment(chosen, totals):
    """Whole-suit scoring that cannot be represented by per-property caps."""
    if _build != "Basher":
        return 0.0

    score = 0.0
    lmc = suit_lmc_state(chosen, totals)

    # The normal profile scores LMC through 40. Basher gets additional credit
    # only when armor material actually expands the cap above 40.
    above_base = max(0, int(lmc["effective_lmc"]) - int(lmc["base_cap"]))
    score += above_base * 500.0

    # A cap-expanding piece is strategically useful only if the suit can exploit
    # it; small tie-breaker keeps such combinations in the beam without making
    # material names more important than actual suit totals.
    if lmc["cap"] > 40 and lmc["raw_lmc"] >= 38:
        score += (lmc["cap"] - 40) * 45.0

    # Soul Charge is explicitly useful for Basher mana sustain, but it is not
    # mandatory and should never outweigh missed HCI/DI/casting minimums.
    shield_soul_charge = False
    for item in chosen or []:
        if item.get("slot") == "Shield":
            if int(effective_item_props(item).get("Soul Charge", 0) or 0) > 0:
                shield_soul_charge = True
                break
    if shield_soul_charge:
        score += 2500.0

    return score


def build_combination_adjustment(chosen, totals, profile_name=None):
    name = profile_name or _build
    if name == "Basher":
        return basher_suit_adjustment(chosen, totals)
    return 0.0


def top_unique_suits(ranked, count=5):
    seen = set()
    out = []

    for final_score, raw_score, chosen, totals in ranked:
        key = tuple(sorted(int(x.get("serial", 0) or 0) for x in chosen))
        if key in seen:
            continue
        seen.add(key)

        deficits = requirement_deficits(totals, active_profile()["requirements"])
        equip = equipment_safety(chosen, totals)
        swing = dex_swing_state(totals, _build)
        lmc = suit_lmc_state(chosen, totals) if _build == "Basher" else None

        out.append({
            "build": _build,
            "score": raw_score,
            "effective_score": final_score,
            "items": chosen,
            "totals": totals,
            "deficits": deficits,
            "equipment_safety": equip,
            "swing_state": swing,
            "lmc_state": lmc,
        })

        if len(out) >= int(count):
            break

    return out


def candidate_label(index, candidate):
    totals = candidate.get("totals", {})
    swing = candidate.get("swing_state")
    text = "#{}  Score {:.0f}".format(index + 1, float(candidate.get("score", 0) or 0))

    if swing:
        text += " | Stam {} / SSI {}".format(
            swing.get("projected_stamina", 0),
            swing.get("total_ssi", 0)
        )

    if candidate.get("deficits"):
        text += " | MINIMUMS SHORT"
    else:
        text += " | minimums met"

    return text


def select_candidate(index):
    global _candidate_index, _best

    if not _top_suits:
        return

    index = max(0, min(int(index), len(_top_suits) - 1))
    _candidate_index = index
    _best = _top_suits[index]
    write_wanted_file(_best)
    show_results()


def candidate_prev():
    select_candidate(_candidate_index - 1)


def candidate_next():
    select_candidate(_candidate_index + 1)


def optimize():
    global _best, _top_suits, _candidate_index

    if not _items:
        if not load_cache():
            set_status("Scan the equipment chest first.", 33)
            return None

    profile = active_profile()

    by_slot = dict((s, []) for s in SLOTS)
    for item in _items:
        try:
            if not item_race_compatible(item, item.get("opl", "")):
                continue
        except:
            pass

        slot = item.get("slot")
        if slot in by_slot:
            by_slot[slot].append(item)

    required_slots = list(CORE_SLOTS)

    # Include every discovered non-shield accessory layer. This lets artifact
    # combinations contribute without making a missing optional layer fatal.
    for optional_slot in ("Earrings", "Talisman", "Belt", "Sash", "Robe", "Back"):
        if by_slot.get(optional_slot):
            required_slots.append(optional_slot)

    if profile["shield"]:
        if by_slot["Shield"]:
            required_slots.append("Shield")
        else:
            set_status(
                "{} wants a shield, but no shield was found. Optimizing without one.".format(
                    profile_display_name(_build)
                ),
                33
            )

    missing_slots = [s for s in required_slots if not by_slot[s]]
    if missing_slots:
        set_status("Cannot build complete suit. Missing: " + ", ".join(missing_slots), 33)
        return None

    # Apply locked pieces. One lock per slot is supported because a suit can
    # only wear one item from each SuitMaster slot.
    candidates = {}
    invalid_locks = []

    for slot in required_slots:
        locked_serial = int(_locked_items.get(slot, 0) or 0)

        if locked_serial:
            locked = [
                item for item in by_slot[slot]
                if int(item.get("serial", 0) or 0) == locked_serial
            ]
            if locked:
                candidates[slot] = locked
            else:
                invalid_locks.append(slot)
                candidates[slot] = prune_candidates(by_slot[slot], profile, 12)
        else:
            candidates[slot] = prune_candidates(by_slot[slot], profile, 12)

    if invalid_locks:
        set_status(
            "Some locks were not found in the scan: " + ", ".join(invalid_locks),
            33
        )

    # Three is a DISPLAY MAXIMUM, never a quota the solver must chase.
    # Work out how many distinct full combinations are even possible before
    # starting the beam search. This is especially important when several
    # pieces are locked or a slot has only one candidate.
    possible_unique = 1
    for slot in required_slots:
        possible_unique *= max(1, len(candidates.get(slot, [])))
        if possible_unique >= 3:
            possible_unique = 3
            break
    desired_results = max(1, min(3, int(possible_unique)))

    beam = [(0.0, [], dict((p, 0) for p in PROPERTIES))]
    BEAM_WIDTH = 350

    # Safety guards: a pathological chest should never make the UI appear
    # permanently frozen. The timer is checked throughout expansion, not only
    # after an entire slot has been processed.
    BUILD_TIME_LIMIT = 30.0
    BUILD_EXPANSION_LIMIT = 450000
    build_started = time.time()
    expansions = 0

    for slot in required_slots:
        next_beam = []

        for prior_score, chosen, totals in beam:
            for item in candidates[slot]:
                expansions += 1
                if expansions % 250 == 0:
                    if API.StopRequested:
                        return None
                    if (time.time() - build_started) >= BUILD_TIME_LIMIT or expansions >= BUILD_EXPANSION_LIMIT:
                        set_status(
                            "Build search stopped by safety limit. Try fewer chest items or lock a few pieces.",
                            33
                        )
                        return None
                    try:
                        API.ProcessCallbacks()
                    except:
                        pass
                    try:
                        API.Pause(0.001)
                    except:
                        pass

                nt = dict(totals)
                props = effective_item_props(item)

                for p in PROPERTIES:
                    nt[p] += int(props.get(p, 0) or 0)

                new_chosen = chosen + [item]
                ns = score_totals(nt, profile)
                ns += build_combination_adjustment(new_chosen, nt, _build)
                next_beam.append((ns, new_chosen, nt))

        next_beam.sort(key=lambda x: x[0], reverse=True)
        beam = next_beam[:BEAM_WIDTH]

        try:
            API.Pause(0.01)
        except:
            pass

        if API.StopRequested:
            return None

        if (time.time() - build_started) >= BUILD_TIME_LIMIT:
            set_status(
                "Build search stopped by safety limit. Try fewer chest items or lock a few pieces.",
                33
            )
            return None

    if not beam:
        set_status("No complete suit could be built from the current gear.", 33)
        return None

    valid_ranked = []
    fallback_ranked = []

    for raw_score, chosen, totals in beam:
        equip_penalty = equipment_safety_penalty(chosen, totals)
        swing_adjust = dex_swing_adjustment(totals, _build)
        final_score = raw_score - equip_penalty + swing_adjust

        gate = hard_minimum_state(totals, profile)
        entry = (final_score, raw_score, chosen, totals)

        if gate["valid"]:
            valid_ranked.append(entry)
        else:
            # If no fully valid suit exists, fallback candidates are ordered by
            # fewest failed minimums, then smallest normalized deficit, and only
            # then by ordinary optimization score.
            fallback_ranked.append((
                gate["unmet_count"],
                gate["normalized_shortfall"],
                -final_score,
                entry,
            ))

    if valid_ranked:
        valid_ranked.sort(key=lambda x: x[0], reverse=True)
        ranked = valid_ranked
        hard_minimum_fallback = False
    else:
        fallback_ranked.sort(key=lambda x: (x[0], x[1], x[2]))
        ranked = [x[3] for x in fallback_ranked]
        hard_minimum_fallback = True

    _top_suits = top_unique_suits(ranked, desired_results)

    if not _top_suits:
        set_status("Optimizer found no usable suit candidates.", 33)
        return None

    _candidate_index = 0
    _best = _top_suits[0]
    write_wanted_file(_best)

    swing = _best.get("swing_state")

    if hard_minimum_fallback:
        deficits = _best.get("deficits", {})
        if deficits:
            set_status(
                "No complete suit meets every configured minimum. Showing closest fallback: "
                + ", ".join("{} +{}".format(k, v) for k, v in deficits.items()),
                53
            )
        else:
            set_status(
                "No complete suit meets every configured hard minimum. Showing closest fallback.",
                53
            )
    elif swing and not swing.get("meets_max_swing", True):
        set_status(
            "Best suit found, but max-swing target is still short: stamina +{} / SSI +{}.".format(
                swing.get("stamina_short", 0),
                swing.get("ssi_short", 0)
            ),
            53
        )
    elif _best.get("deficits"):
        d = ", ".join("{} -{}".format(k, v) for k, v in _best["deficits"].items())
        set_status("Best suit found; still short: {}".format(d), 53)
    else:
        if len(_top_suits) == 1:
            msg = "1 unique suit available. Showing it now."
        else:
            msg = "{} unique suit options ready. Showing #1.".format(len(_top_suits))
        set_status(msg, 68)

    show_results()
    return _best


def show_results():
    if not _best:
        return

    best = _best
    totals = best.get("totals", {})
    deficits = best.get("deficits", {})
    items = best.get("items", [])
    profile = active_profile()
    swing = best.get("swing_state")
    lmc_state = best.get("lmc_state")
    equip_safety = best.get("equipment_safety", {})

    W = 970
    H = 700

    g = API.CreateGump(True, True, True)
    gx, gy = load_gump_pos("results", 320, 105)
    g.SetRect(gx, gy, W, H)
    register_gump_position(g, "results")

    bg = API.CreateGumpColorBox(0.97, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(
        g,
        "{} SUIT".format(profile_display_name(best.get("build", "")).upper()),
        20, 12, 530, 28, 21, C_TITLE
    )

    if _top_suits:
        add_label(
            g,
            "Candidate {} of {}".format(_candidate_index + 1, len(_top_suits)),
            720, 17, 220, 22, 13, C_GOLD, "right"
        )

    add_label(
        g,
        "Preview only | no items move until you choose PULL SUIT",
        20, 43, 880, 20, 11, C_MUTED
    )

    # Selected items
    add_panel(g, 14, 70, 420, 500)
    add_label(g, "SELECTED ITEMS", 30, 84, 220, 22, 14, C_GOLD)

    locked_set = set(int(v) for v in _locked_items.values())

    y = 120
    for item in items:
        slot = str(item.get("slot", "?"))
        name = str(item.get("name", "Unknown"))
        is_locked = int(item.get("serial", 0) or 0) in locked_set

        if len(name) > 40:
            name = name[:37] + "..."

        add_label(g, slot, 30, y, 90, 22, 13, C_MUTED)
        add_label(
            g,
            ("[LOCK] " if is_locked else "") + name,
            125, y, 285, 22, 12,
            C_GOLD if is_locked else C_TEXT
        )
        y += 30

    # Stats
    add_panel(g, 448, 70, 508, 500)
    add_label(g, "SUIT TOTALS", 464, 84, 180, 22, 14, C_GOLD)

    lx = 464
    lv = 610

    add_label(g, "RESISTS", lx, 120, 120, 20, 13, C_TITLE)
    y = 150
    for label_text, prop in [
        ("Physical", "Physical Resist"),
        ("Fire", "Fire Resist"),
        ("Cold", "Cold Resist"),
        ("Poison", "Poison Resist"),
        ("Energy", "Energy Resist"),
    ]:
        value = int(totals.get(prop, 0) or 0)
        minimum = int(profile["requirements"].get(prop, 0) or 0)
        color = C_GREEN if (not minimum or value >= minimum) else C_RED
        add_label(g, label_text, lx, y, 120, 22, 13, C_TEXT)
        add_label(g, str(value), lv, y, 55, 22, 14, color, "right")
        y += 28

    add_label(g, "COMBAT", lx, 300, 120, 20, 13, C_TITLE)
    y = 330
    for label_text, prop in [
        ("HCI", "Hit Chance Increase"),
        ("DCI", "Defense Chance Increase"),
        ("Damage Inc", "Damage Increase"),
        ("SSI", "Swing Speed Increase"),
        ("LRC", "Lower Reagent Cost"),
    ]:
        value = int(totals.get(prop, 0) or 0)
        minimum = int(profile.get("requirements", {}).get(prop, 0) or 0)
        target = int(profile.get("targets", {}).get(prop, 0) or 0)
        color = C_RED if minimum and value < minimum else (C_GREEN if target and value >= target else C_TEXT)
        add_label(g, label_text, lx, y, 120, 22, 12, C_TEXT)
        add_label(g, str(value), lv, y, 55, 22, 13, color, "right")
        y += 26

    if lmc_state:
        lmc_text = "{} / {}".format(lmc_state.get("effective_lmc", 0), lmc_state.get("cap", 40))
        lmc_color = C_GREEN if int(lmc_state.get("effective_lmc", 0)) >= int(lmc_state.get("cap", 40)) else C_GOLD
    else:
        lmc_text = str(totals.get("Lower Mana Cost", 0))
        lmc_color = C_TEXT
    add_label(g, "LMC / cap", lx, y, 120, 22, 12, C_TEXT)
    add_label(g, lmc_text, lv - 20, y, 75, 22, 13, lmc_color, "right")

    rx = 700
    rv = 886

    add_label(g, "RESOURCES / STATS", rx, 120, 190, 20, 13, C_TITLE)
    y = 150
    for label_text, prop in [
        ("HP Increase", "Hit Point Increase"),
        ("Stam Increase", "Stamina Increase"),
        ("Mana Increase", "Mana Increase"),
        ("Dex Bonus", "Dexterity Bonus"),
        ("Str Bonus", "Strength Bonus"),
        ("Int Bonus", "Intelligence Bonus"),
        ("Mana Regen", "Mana Regeneration"),
    ]:
        add_label(g, label_text, rx, y, 145, 22, 12, C_TEXT)
        add_label(g, str(totals.get(prop, 0)), rv, y, 50, 22, 13, C_TEXT, "right")
        y += 26

    add_label(g, "CASTING / OTHER", rx, 350, 170, 20, 13, C_TITLE)
    y = 380
    for label_text, prop in [
        ("FC", "Faster Casting"),
        ("FCR", "Faster Cast Recovery"),
        ("SDI", "Spell Damage Increase"),
        ("Luck", "Luck"),
    ]:
        add_label(g, label_text, rx, y, 145, 22, 12, C_TEXT)
        add_label(g, str(totals.get(prop, 0)), rv, y, 50, 22, 13, C_TEXT, "right")
        y += 26

    # Swing and equipment safety strip.
    strip_y = 580

    if swing:
        swing_color = C_GREEN if swing.get("meets_max_swing") else C_RED
        swing_text = (
            "1.25s SWING (3.25 weapon): stam {} | SSI {} | breakpoint stam {} + SSI {} | {}"
        ).format(
            swing.get("projected_stamina", 0),
            swing.get("total_ssi", 0),
            swing.get("required_stamina", "?"),
            swing.get("required_ssi", "?"),
            "READY" if swing.get("meets_max_swing") else "SHORT"
        )
        add_label(g, swing_text, 30, strip_y, 900, 20, 11, swing_color)
        strip_y += 22

    if equip_safety:
        safe = equip_safety.get("safe", True)
        color = C_GREEN if safe else C_RED
        equip_text = "EQUIP SAFETY (-{}): STR {} / req {} | DEX {} / req {} | {}".format(
            equip_safety.get("buffer", 22),
            equip_safety.get("safe_strength", 0),
            equip_safety.get("max_strength_requirement", 0),
            equip_safety.get("safe_dexterity", 0),
            equip_safety.get("max_dexterity_requirement", 0),
            "SAFE" if safe else "NOT SAFE"
        )
        add_label(g, equip_text, 30, strip_y, 900, 20, 11, color)
        strip_y += 22

    if deficits:
        need_text = "NEEDS: " + " | ".join(
            "{} +{}".format(k.replace(" Resist", ""), v)
            for k, v in deficits.items()
        )
        add_label(g, need_text, 30, strip_y, 900, 20, 11, C_RED)
    else:
        add_label(g, "All hard minimum requirements are satisfied.", 30, strip_y, 900, 20, 11, C_GREEN)

    # Candidate navigation / actions.
    add_button(g, "PREVIOUS", 30, 655, 105, 30, candidate_prev)
    add_button(g, "NEXT", 145, 655, 105, 30, candidate_next)
    add_button(g, "PULL SUIT", 275, 655, 165, 30, pull_best_suit)
    add_button(g, "RETURN SUIT", 450, 655, 155, 30, return_active_suit)
    add_button(g, "CLOSE", 842, 655, 95, 30, lambda: dispose(g))

    add_save_pos_button(g)
    API.AddGump(g)


# Preserve the final v1.9 load behavior, then add lock persistence.
_load_settings_v19 = load_settings

def load_settings():
    _load_settings_v19()
    load_locks()




def show_mini_bar():
    """Tiny on-the-go SuitMaster bar: inspect players, restore, or save position."""
    global _mini_gump, _main_gump

    if _main_gump is not None:
        try:
            save_gump_position(_main_gump, False)
        except:
            pass
        dispose(_main_gump)
        _main_gump = None

    if _mini_gump is not None:
        try:
            dispose(_mini_gump)
        except:
            pass
        _mini_gump = None

    W = 205
    H = 38
    x, y = load_gump_pos("mini", 25, 25)
    g = API.CreateGump(True, True, True)
    g.SetRect(x, y, W, H)
    register_gump_position(g, "mini")

    bg = API.CreateGumpColorBox(0.94, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "SM", 8, 9, 28, 18, 12, C_TITLE)

    inspect_btn = add_button(g, "INSPECT", 38, 5, 82, 27, inspect_player_profile)
    try:
        inspect_btn.SetTooltip("Target a player and import their visible equipment")
    except:
        pass

    def restore_full():
        global _mini_gump
        try:
            save_gump_position(g, False)
        except:
            pass
        dispose(g)
        _mini_gump = None
        show_main()

    restore_btn = add_button(g, "^", 125, 5, 32, 27, restore_full)
    try:
        restore_btn.SetTooltip("Restore full SuitMaster")
    except:
        pass

    add_save_pos_button(g)
    _mini_gump = g
    API.AddGump(g)

def minimize_main():
    show_mini_bar()

# Main UI v2.0
def show_main():
    global _main_gump

    refresh_profile_names()

    W = 840
    H = 550
    x, y = load_gump_pos("main", *load_pos())

    g = API.CreateGump(True, True, True)
    g.SetRect(x, y, W, H)
    register_gump_position(g, "main")

    bg = API.CreateGumpColorBox(0.97, C_BG)
    bg.SetRect(0, 0, W, H)
    g.Add(bg)

    add_label(g, "J.C.S. SUITMASTER", 20, 10, 430, 30, 22, C_TITLE)
    add_label(g, "InsaneUO Gear Optimizer", 22, 36, 300, 18, 10, C_MUTED)
    add_label(g, "v" + VERSION, 680, 18, 90, 20, 11, C_MUTED, "right")
    add_button(g, "_", 776, 5, 26, 20, minimize_main)

    # STORAGE
    add_panel(g, 14, 60, 812, 175)
    add_label(g, "GEAR STORAGE", 30, 74, 160, 22, 13, C_GOLD)

    chest_count = len(_chests)
    add_label(
        g,
        "{} gear chest{} configured".format(chest_count, "" if chest_count == 1 else "s"),
        30, 104, 300, 24, 14, C_TEXT
    )

    add_label(
        g,
        "Pull bag: " + ("0x{:X}".format(_pull_bag) if _pull_bag else "Not set"),
        30, 134, 320, 23, 12, C_TEXT
    )

    add_button(g, "ADD CHEST", 30, 189, 120, 30, add_chest)
    add_button(g, "REMOVE", 160, 189, 100, 30, remove_chest)
    add_button(g, "CLEAR", 270, 189, 90, 30, clear_chests)
    add_button(g, "PULL BAG", 370, 189, 120, 30, target_pull_bag)
    add_button(g, "SCAN GEAR", 666, 189, 135, 30, scan_chest)

    # BUILD
    add_panel(g, 14, 247, 812, 148)
    add_label(g, "BUILD PROFILE", 30, 261, 180, 22, 13, C_GOLD)

    try:
        idx = BUILD_NAMES.index(_build)
    except:
        idx = 0

    dd = API.CreateDropDown(285, [profile_display_name(n) for n in BUILD_NAMES], idx)
    dd.SetPos(30, 294)
    g.Add(dd)

    add_button(g, "APPLY", 327, 292, 75, 31, lambda: set_build_from_dropdown(dd))
    add_button(g, "SKILLS", 412, 292, 90, 31, lambda: show_profile_skills(_build))
    add_button(g, "PROFILES", 512, 292, 105, 31, show_profile_manager)
    add_button(g, "BUILD SUIT", 647, 292, 154, 31, optimize)

    creator = profile_creator(_build)
    desc = profile_description(_build)
    if creator:
        desc += " | Build by: " + creator

    add_label(g, desc, 30, 335, 765, 38, 11, C_MUTED)

    # LOCKS / DEXXER LOGIC
    add_panel(g, 14, 407, 812, 82)
    add_label(g, "SUIT CONTROL", 30, 420, 150, 20, 12, C_GOLD)

    locked_count = len(_locked_items)
    lock_text = "{} locked piece{}".format(locked_count, "" if locked_count == 1 else "s")
    add_label(g, lock_text, 30, 448, 170, 22, 12, C_TEXT)

    add_button(g, "LOCK ITEM", 210, 441, 120, 30, lock_target_item)
    add_button(g, "CLEAR LOCKS", 340, 441, 130, 30, clear_locked_items)

    if _build in MELEE_DEXXER_PROFILES:
        add_label(
            g,
            "Dexxer: 1.25s swing target | 3.25 weapon safety case | weapon SSI 0 | -22 stam buffer",
            495, 446, 305, 32, 10, C_TITLE
        )

    # STATUS
    add_panel(g, 14, 501, 812, 37)
    add_label(g, _status, 30, 509, 770, 24, 11, C_TEXT)

    _main_gump = g
    add_save_pos_button(g)
    API.AddGump(g)


# ============================================================
# Entry
# ============================================================

load_settings()
set_status("SuitMaster {} ready. Add/scan gear, choose a build, then Build Suit.".format(VERSION), 68)
show_main()

while not API.StopRequested:
    # Legion gump button callbacks are queued and must be serviced explicitly.
    # Without this, buttons may appear clickable but their Python callbacks
    # (including RequestTarget) will not reliably execute.
    try:
        API.ProcessCallbacks()
    except:
        pass
    API.Pause(0.05)

save_settings()
if _main_gump is not None:
    save_pos(_main_gump)
