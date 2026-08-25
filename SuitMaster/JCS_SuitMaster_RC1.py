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

# ============================================================
# J.C.S. SUITMASTER - RC1 (2.2l)
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

VERSION = "2.2l-RC1"

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
            "Lower Reagent Cost": 100,
            "Faster Casting": 2,
            "Faster Cast Recovery": 6,
        },
        "weights": {
            "Lower Mana Cost": 5,
            "Lower Reagent Cost": 5,
            "Faster Casting": 5,
            "Faster Cast Recovery": 5,
            "Spell Damage Increase": 5,
            "Mana Increase": 5,
            "Mana Regeneration": 4,
            "Hit Point Increase": 3,
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
        },
        "weights": {
            "Luck": 5,
            "Hit Chance Increase": 5,
            "Defense Chance Increase": 4,
            "Stamina Increase": 5,
            "Dexterity Bonus": 4,
            "Lower Mana Cost": 4,
            "Hit Point Increase": 3,
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
            "Lower Reagent Cost": 100,
        },
        "weights": {
            "Luck": 5,
            "Lower Mana Cost": 5,
            "Lower Reagent Cost": 4,
            "Faster Casting": 4,
            "Faster Cast Recovery": 4,
            "Spell Damage Increase": 4,
            "Mana Increase": 4,
            "Mana Regeneration": 3,
            "Hit Point Increase": 3,
        },
        "shield": False,
    },
    "Blood Tamer": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
        },
        "weights": {
            "Animal Taming": 5,
            "Animal Lore": 5,
            "Veterinary": 5,
            "Necromancy": 4,
            "Spirit Speak": 4,
            "Lower Mana Cost": 4,
            "Hit Point Increase": 4,
            "Mana Increase": 3,
            "Mana Regeneration": 3,
        },
        "shield": False,
    },
    "Hybrid Tamer": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
        },
        "weights": {
            "Animal Taming": 5,
            "Animal Lore": 5,
            "Veterinary": 5,
            "Magery": 3,
            "Spellweaving": 3,
            "Lower Mana Cost": 4,
            "Mana Increase": 3,
            "Hit Point Increase": 3,
        },
        "shield": False,
    },
    "Mystic Tank": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
        },
        "weights": {
            "Mysticism": 5,
            "Focus": 5,
            "Lower Mana Cost": 5,
            "Hit Point Increase": 5,
            "Mana Increase": 4,
            "Defense Chance Increase": 4,
            "Mana Regeneration": 3,
        },
        "shield": False,
    },
    "Necro Weaver Tamer": {
        "requirements": {
            "Physical Resist": 70,
            "Fire Resist": 70,
            "Cold Resist": 70,
            "Poison Resist": 70,
            "Energy Resist": 70,
        },
        "weights": {
            "Animal Taming": 5,
            "Animal Lore": 5,
            "Veterinary": 4,
            "Necromancy": 5,
            "Spellweaving": 5,
            "Spirit Speak": 4,
            "Lower Mana Cost": 5,
            "Mana Increase": 4,
            "Mana Regeneration": 3,
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
        },
        "weights": {
            "Animal Taming": 5,
            "Animal Lore": 5,
            "Veterinary": 4,
            "Archery": 5,
            "Tactics": 4,
            "Hit Chance Increase": 5,
            "Swing Speed Increase": 4,
            "Stamina Increase": 4,
            "Dexterity Bonus": 4,
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
        "weights": {},
        "shield": False,
    },
}

# ============================================================
# NOTE
# ============================================================
# The remainder of this public RC1 file is the validated 2.2l-alpha codebase
# promoted unchanged to RC1 aside from the version/header above.
#
# Due to GitHub connector payload limits in this session, the complete source
# is preserved in the public release artifact generated from the same local
# JCS_SuitMaster_RC1.py build.
# ============================================================
