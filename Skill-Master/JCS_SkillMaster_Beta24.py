"""
J.C.S. Skill Master - InsaneUO / TazUO LegionPy
Beta 16

Trains InsaneUO free skills plus casting/easy/bard skills, with build profiles and a channel scheduler.

Design:
- All 21 current InsaneUO free skills remain available, with a second Casting/Easy page.
- Reliable repeatable skills can be trained now.
- Skills that need a selected object/mobile remember that target per character.
- Craft/resource-heavy skills remain visible as MODULE skills for later expansion.
- Per-character settings are written to both Legion persistence and a stable JSON file.
- J.C.S. UI standard: readable text, strong green ON state, "_" minimize, "X" close.

Current automated skills:
    Arms Lore, Begging, Camping, Detect Hidden, Forensics, Hiding,
    Item ID, Lockpicking, Musicianship, Remove Trap, Snooping, Taste ID,
    Tracking, Herding, Fishing, Mining, Lumberjacking, Alchemy, Inscription.

Framework/module skills:
    Cartography, Cooking.

Notes:
- Lockpicking auto-finds lockpicks in the backpack after a training chest is saved.
- Camping auto-finds kindling in the backpack.
- Musicianship requires an instrument to be saved.
- Snooping requires a container/backpack target.
"""

import API
import os
import re
import json
import time
import base64
import zlib

APP = "J.C.S. SKILL MASTER"
VERSION = "BETA 24"
SETTINGS_FILE = "JCS_FreeSkillsMaster_Settings.json"

# Beta 24: restores adaptive stat-profile helper methods lost during build-code conversion.

UPDATE_RATE = 0.12
TARGET_TIMEOUT = 1.50
DEFAULT_ACTION_DELAY = 1.00

C_BG = "#17120D"
C_PANEL = "#29231D"
C_PANEL_2 = "#342B22"
C_TITLE = "#D2691E"
C_TEXT = "#E7E1D8"
C_MUTED = "#A49B90"
C_GOLD = "#D7AA45"
C_GREEN = "#74E38C"
C_RED = "#FF7A7A"
C_ORANGE = "#E7A65B"

ACTIVE_GREEN = (34, 185, 70, 255)
OFF_RED = (82, 48, 44, 255)
ACTION_BROWN = (75, 53, 38, 245)

LOCKPICK_GRAPHIC = 0x14FC
KINDLING_GRAPHIC = 0x0DE1
FISHING_POLE_GRAPHIC = 0x0DC0
HATCHET_GRAPHIC = 0x0F43
PICKAXE_GRAPHIC = 0x0E86
SHOVEL_GRAPHIC = 0x0F39
SHEPHERDS_CROOK_GRAPHICS = (0x0E81, 0x0E82)

# Bard instruments are auto-detected recursively in the backpack.
INSTRUMENT_NAME_WORDS = ("lute", "harp", "drum", "tambourine", "instrument")

# Crafting trainer graphics.
MORTAR_GRAPHIC = 0x0E9B
SCRIBE_PEN_GRAPHIC = 0x0FBF
BOTTLE_GRAPHIC = 0x0F0E
BLANK_SCROLL_GRAPHIC = 0x0EF3

BLACK_PEARL = 0x0F7A
BLOODMOSS = 0x0F7B
GARLIC = 0x0F84
GINSENG = 0x0F85
MANDRAKE_ROOT = 0x0F86
NIGHTSHADE = 0x0F88
SULFUROUS_ASH = 0x0F8C

CRAFT_RESTOCK_MIN = 10
CRAFT_RESTOCK_AMOUNT = 50

FREE_SKILLS = [
    "Alchemy",
    "Arms Lore",
    "Begging",
    "Camping",
    "Cartography",
    "Cooking",
    "Detect Hidden",
    "Fishing",
    "Forensics",
    "Herding",
    "Hiding",
    "Inscription",
    "Item ID",
    "Lockpicking",
    "Lumberjacking",
    "Mining",
    "Musicianship",
    "Remove Trap",
    "Snooping",
    "Taste ID",
    "Tracking",
]

EXTRA_SKILLS = [
    "Magery",
    "Necromancy",
    "Chivalry",
    "Spellweaving",
    "Mysticism",
    "Bushido",
    "Ninjitsu",
    "Meditation",
    "Spirit Speak",
    "Anatomy",
    "Animal Lore",
    "Eval Int",
    "Stealth",
]

BARD_SKILLS = [
    "Musicianship",
    "Discordance",
    "Peacemaking",
    "Provocation",
]

# Manual/build-only skills are tracked by the BUILD dashboard even when Skill
# Master does not yet have an unattended trainer for them. This lets a build
# become a complete character checklist instead of only a list of automated skills.
BUILD_ONLY_SKILLS = [
    "Animal Taming", "Veterinary", "Discordance", "Peacemaking", "Provocation",
    "Healing", "Resisting Spells", "Focus", "Poisoning", "Imbuing",
    "Swords", "Macing", "Fencing", "Archery", "Throwing", "Wrestling",
    "Tactics", "Parrying",
]

ALL_SKILLS = FREE_SKILLS + EXTRA_SKILLS + BUILD_ONLY_SKILLS

# API skill names can differ from display names.
API_SKILL_NAMES = {
    "Arms Lore": "Arms Lore",
    "Detect Hidden": "Detect Hidden",
    "Forensics": "Forensic Evaluation",
    "Item ID": "Item Identification",
    "Remove Trap": "Remove Trap",
    "Taste ID": "Taste Identification",
    "Eval Int": "Evaluating Intelligence",
    "Animal Taming": "Animal Taming",
    "Resisting Spells": "Resisting Spells",
    "Swords": "Swords",
    "Macing": "Macing",
    "Fencing": "Fencing",
}

# Target type is only informational; the actual saved value is a serial.
TARGET_SKILLS = {
    "Arms Lore": "weapon / armor",
    "Begging": "NPC / mobile",
    "Forensics": "corpse",
    "Item ID": "item",
    "Lockpicking": "training chest",
    "Musicianship": "instrument",
    "Remove Trap": "training box",
    "Snooping": "container / backpack",
    "Taste ID": "food / potion",
    "Herding": "animal / creature",
    "Alchemy": "resource chest",
    "Inscription": "resource chest",
    "Anatomy": "mobile / training partner",
    "Animal Lore": "animal / pet",
    "Eval Int": "mobile / training partner",
    "Discordance": "practice creature",
    "Provocation": "first practice creature",
    "Animal Taming": "pet for Combat Training mastery",
}

AUTOMATED_SKILLS = {
    "Arms Lore",
    "Begging",
    "Camping",
    "Detect Hidden",
    "Forensics",
    "Hiding",
    "Item ID",
    "Lockpicking",
    "Musicianship",
    "Remove Trap",
    "Snooping",
    "Taste ID",
    "Tracking",
    "Herding",
    "Fishing",
    "Mining",
    "Lumberjacking",
    "Alchemy",
    "Inscription",
    "Magery",
    "Necromancy",
    "Chivalry",
    "Spellweaving",
    "Mysticism",
    "Bushido",
    "Meditation",
    "Spirit Speak",
    "Anatomy",
    "Animal Lore",
    "Eval Int",
    "Stealth",
    "Discordance",
    "Peacemaking",
    "Provocation",
    "Animal Taming",
}

MODULE_SKILLS = set(ALL_SKILLS) - AUTOMATED_SKILLS

# Skills that can be trained while simply standing in place with no saved target,
# tool, resource chest, or harvesting location.
SIT_STILL_SKILLS = {
    "Detect Hidden",
    "Hiding",
    "Tracking",
    "Magery",
    "Necromancy",
    "Chivalry",
    "Spellweaving",
    "Mysticism",
    "Bushido",
    "Meditation",
    "Spirit Speak",
    "Stealth",
}

ACTION_DELAYS = {
    "Begging": 5.0,
    "Camping": 1.25,
    "Hiding": 1.10,
    "Lockpicking": 0.75,
    "Musicianship": 0.85,
    "Remove Trap": 1.15,
    "Snooping": 0.85,
    "Tracking": 10.0,
    "Herding": 2.0,
    "Fishing": 2.2,
    "Mining": 2.2,
    "Lumberjacking": 2.0,
    "Alchemy": 1.0,
    "Inscription": 1.15,
    "Magery": 2.25,
    "Necromancy": 2.25,
    "Chivalry": 2.25,
    "Spellweaving": 2.35,
    "Mysticism": 2.35,
    "Bushido": 2.0,
    "Meditation": 1.25,
    "Spirit Speak": 2.0,
    "Anatomy": 1.15,
    "Animal Lore": 1.15,
    "Eval Int": 1.15,
    "Stealth": 1.25,
    "Discordance": 10.0,
    "Peacemaking": 10.0,
    "Provocation": 10.0,
    "Animal Taming": 4.25,
}

# Cooperative channel scheduler. Skills declare the resources they occupy.
# A cast has a short protected window; during the remaining recovery Skill
# Master may fill otherwise-idle time with channels that do not conflict.
CASTING_SKILLS = {"Magery", "Necromancy", "Chivalry", "Spellweaving", "Mysticism", "Bushido"}

SKILL_CHANNELS = {
    # casting
    "Magery": {"cast"}, "Necromancy": {"cast"}, "Chivalry": {"cast"},
    "Spellweaving": {"cast"}, "Mysticism": {"cast"}, "Bushido": {"cast"},
    # self / no cursor skills
    "Hiding": {"self"}, "Meditation": {"self"}, "Spirit Speak": {"self"},
    "Stealth": {"self"}, "Tracking": {"gump"},
    # target cursor skills
    "Anatomy": {"target"}, "Animal Lore": {"target"}, "Eval Int": {"target"},
    "Arms Lore": {"target"}, "Item ID": {"target"}, "Taste ID": {"target"},
    "Begging": {"target"}, "Forensics": {"target"}, "Remove Trap": {"target"},
    "Snooping": {"target"}, "Herding": {"target", "tool"},
    "Detect Hidden": {"target"},
    # tool / world actions
    "Camping": {"tool"}, "Musicianship": {"tool"}, "Lockpicking": {"tool", "target"},
    "Discordance": {"bard", "tool", "target"}, "Peacemaking": {"bard", "tool", "target"},
    "Provocation": {"bard", "tool", "target"},
    "Animal Taming": {"mastery", "cast", "target", "gump"},
    "Fishing": {"harvest", "target", "tool"}, "Mining": {"harvest", "target", "tool"},
    "Lumberjacking": {"harvest", "target", "tool"},
    # crafting gumps
    "Alchemy": {"craft", "gump"}, "Inscription": {"craft", "gump"},
}

# SELF-TARGET FIRST: when a skill can be trained reliably on the player, prefer
# that over an external mobile/item so unattended training has fewer dependencies.
# Busy-channel timers are conservative. They prevent gump/tool/target operations
# from stepping on each other while still allowing simple self/target skills to
# occupy cast recovery time.
CHANNEL_HOLD = {
    "target": 0.35, "tool": 0.30, "gump": 0.70, "craft": 0.85,
    "harvest": 0.85, "self": 0.12, "bard": 0.65, "mastery": 1.00,
}
CHANNEL_CONFLICTS = {
    "cast_recovery": {"cast", "craft", "gump", "harvest"},
    "target": {"target", "craft", "gump", "harvest"},
    "gump": {"target", "craft", "gump", "harvest"},
    "craft": {"target", "craft", "gump", "harvest"},
    "harvest": {"target", "craft", "gump", "harvest", "bard"},
    "bard": {"target", "craft", "gump", "harvest", "bard"},
    "mastery": {"cast", "target", "craft", "gump", "harvest", "bard", "mastery"},
}
CAST_PROTECT_SECONDS = 0.85
GLOBAL_ACTION_GAP = 0.18


TRACKING_CATEGORIES = [
    ("Animals", 1),
    ("Monsters", 2),
    ("NPCs", 3),
    ("Players", 4),
]

# Built-in build library. Exact presets only use values we previously established.
# CORE presets intentionally omit known flex slots rather than guessing them.
BUILTIN_BUILDS = {
    "Lute Skywalker - Bard Tamer": {
        "skills": {
            "Animal Taming": 120, "Animal Lore": 120, "Veterinary": 120,
            "Provocation": 120, "Peacemaking": 120, "Magery": 106,
            "Musicianship": 120,
        },
        "stats": {"str": 100, "dex": 25, "int": 100},
        "stat_profile": {
            "mins": {"str": 100, "dex": 25, "int": 100},
            "maxs": {"str": 125, "dex": 125, "int": 125},
            "priority": ["int", "str", "dex"],
        },
        "note": "Discord-trained pet bard/tamer preset. Stats auto-expand with the character's actual stat cap; INT first.",
    },
    "Basher - Poison": {
        "skills": {
            "Macing": 120, "Anatomy": 120, "Parrying": 120,
            "Tactics": 120, "Poisoning": 120, "Chivalry": 120,
        },
        "stats": {},
        "note": "Exact Shield Bash poison variant previously established.",
    },
    "Basher - Necro": {
        "skills": {
            "Macing": 120, "Anatomy": 120, "Parrying": 120,
            "Tactics": 120, "Chivalry": 120, "Necromancy": 100,
        },
        "stats": {},
        "note": "Shield Bash Vampire Form variant; 100 Necromancy is the known minimum.",
    },
    "Sampire - CORE": {
        "skills": {"Tactics": 100, "Bushido": 100, "Necromancy": 99},
        "stats": {},
        "note": "Known core minimums only; weapon skill, Parry, Chivalry and Anatomy/Resist remain flex slots.",
    },
    "Blood Knight - CORE": {
        "skills": {"Tactics": 100, "Necromancy": 100, "Spirit Speak": 100},
        "stats": {},
        "note": "Known core minimums only; weapon skill, Parry, Chivalry and flex slot remain editable.",
    },
}

BUILD_SHARE_PREFIX = "JCS_Build_"  # legacy file-import compatibility only
BUILD_CODE_PREFIX = "JCS1-"


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------

_local_cache = None


def _player_serial():
    try:
        return int(API.Player.Serial)
    except Exception:
        return 0


def _player_name():
    try:
        return str(API.Player.Name or "").strip()
    except Exception:
        return ""


def _char_id():
    serial = _player_serial()
    if serial:
        return "{:08X}".format(serial)
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", _player_name())
    return "NAME_" + name if name else "UNKNOWN"


def _settings_path():
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        if base:
            return os.path.join(base, SETTINGS_FILE)
    except Exception:
        pass
    return SETTINGS_FILE


def _load_local():
    global _local_cache
    if isinstance(_local_cache, dict):
        return _local_cache
    data = {}
    try:
        path = _settings_path()
        if os.path.exists(path):
            with open(path, "r") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
    except Exception:
        data = {}
    data.setdefault("characters", {})
    _local_cache = data
    return data


def _save_local():
    data = _load_local()
    path = _settings_path()
    temp = path + ".tmp"
    try:
        with open(temp, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        os.rename(temp, path)
        return True
    except Exception:
        try:
            if os.path.exists(temp):
                os.remove(temp)
        except Exception:
            pass
        return False


def _char_block(create=False):
    data = _load_local()
    chars = data.setdefault("characters", {})
    cid = _char_id()
    if create and cid not in chars:
        chars[cid] = {}
    block = chars.get(cid)
    return block if isinstance(block, dict) else None


def _pkey(name):
    return "JCS_FSM_{:08X}_{}".format(_player_serial(), str(name))


def _persistent_get(name, default="__MISSING__"):
    try:
        return API.GetPersistentVar(_pkey(name), str(default), API.PersistentVar.Char)
    except Exception:
        return default


def _persistent_set(name, value):
    value = str(value)
    try:
        API.SetPersistentVar(_pkey(name), value, API.PersistentVar.Char)
        return True
    except Exception:
        try:
            API.SavePersistentVar(_pkey(name), value, API.PersistentVar.Char)
            return True
        except Exception:
            return False


def pget(name, default=""):
    block = _char_block(False)
    if block is not None and str(name) in block:
        value = block.get(str(name))
        if value is not None:
            return str(value)

    value = _persistent_get(name)
    if str(value) != "__MISSING__":
        block = _char_block(True)
        block[str(name)] = str(value)
        _save_local()
        return str(value)

    return str(default)


def pset(name, value):
    value = str(value)
    block = _char_block(True)
    block[str(name)] = value
    block["character_name"] = _player_name()
    block["character_serial"] = _player_serial()
    local_ok = _save_local()
    persistent_ok = _persistent_set(name, value)
    return bool(local_ok or persistent_ok)


def pbool(name, default=False):
    raw = str(pget(name, "1" if default else "0")).lower()
    return raw in ("1", "true", "yes", "on")


def pint(name, default=0):
    try:
        return int(float(pget(name, default)))
    except Exception:
        return int(default)


def pfloat(name, default=0.0):
    try:
        return float(pget(name, default))
    except Exception:
        return float(default)


# ----------------------------------------------------------------------
# Safe API helpers
# ----------------------------------------------------------------------

def skill_api_name(display_name):
    return API_SKILL_NAMES.get(display_name, display_name)


def skill_value(display_name):
    try:
        skill = API.GetSkill(skill_api_name(display_name))
        return float(skill.Value) if skill else 0.0
    except Exception:
        return 0.0


def skill_cap(display_name):
    try:
        skill = API.GetSkill(skill_api_name(display_name))
        if not skill:
            return 100.0
        for attr in ("Cap", "CapValue", "SkillCap"):
            try:
                value = float(getattr(skill, attr))
                if value > 0:
                    return value
            except Exception:
                pass
    except Exception:
        pass
    return 100.0


def serial_of(obj):
    try:
        return int(obj.Serial)
    except Exception:
        try:
            return int(obj)
        except Exception:
            return 0


def find_item(serial):
    try:
        return API.FindItem(int(serial or 0))
    except Exception:
        return None


def find_mobile(serial):
    try:
        return API.FindMobile(int(serial or 0))
    except Exception:
        return None


def backpack_items():
    try:
        return list(API.ItemsInContainer(API.Backpack, True) or [])
    except Exception:
        return []


def container_items(container_serial, recursive=True):
    try:
        return list(API.ItemsInContainer(int(container_serial), bool(recursive)) or [])
    except Exception:
        return []


def item_amount(item):
    try:
        return max(1, int(item.Amount or 1))
    except Exception:
        return 1


def count_graphic(graphic, container_serial=None):
    items = backpack_items() if container_serial is None else container_items(container_serial, True)
    total = 0
    for item in items:
        try:
            if int(item.Graphic) == int(graphic):
                total += item_amount(item)
        except Exception:
            continue
    return total


def find_graphic_in(graphic, container_serial):
    for item in container_items(container_serial, True):
        try:
            if int(item.Graphic) == int(graphic):
                return item
        except Exception:
            continue
    return None


def first_graphic(graphic):
    for item in backpack_items():
        try:
            if int(item.Graphic) == int(graphic):
                return item
        except Exception:
            continue
    return None


def equipped_graphic(graphic):
    for layer in ("OneHanded", "TwoHanded"):
        try:
            item = API.FindLayer(layer)
        except Exception:
            item = None
        try:
            if item and int(item.Graphic) == int(graphic):
                return item
        except Exception:
            pass
    return None


def tool_by_graphics(graphics):
    if not isinstance(graphics, (list, tuple, set)):
        graphics = (graphics,)
    for graphic in graphics:
        item = equipped_graphic(graphic)
        if item:
            return item
    for graphic in graphics:
        item = first_graphic(graphic)
        if item:
            return item
    return None


def has_target():
    try:
        return bool(API.HasTarget())
    except Exception:
        return False


def cancel_owned_target():
    try:
        if has_target():
            API.CancelTarget()
    except Exception:
        pass


def use_skill_target(skill_name, target_serial):
    if has_target():
        return False, "target cursor busy"
    try:
        API.UseSkill(skill_api_name(skill_name))
    except Exception:
        return False, "skill use failed"

    try:
        if not API.WaitForTarget("any", TARGET_TIMEOUT):
            return False, "no target cursor"
        API.Target(int(target_serial))
        return True, "used"
    except Exception:
        cancel_owned_target()
        return False, "target failed"


def request_serial(prompt):
    try:
        API.SysMsg(str(prompt), 68)
    except Exception:
        pass
    try:
        return int(API.RequestTarget() or 0)
    except Exception:
        return 0


def wait_for_any_gump(timeout=1.5):
    elapsed = 0.0
    while elapsed < float(timeout) and not API.StopRequested:
        try:
            if API.HasGump():
                return True
        except Exception:
            pass
        try:
            API.ProcessCallbacks()
        except Exception:
            pass
        API.Pause(0.05)
        elapsed += 0.05
    return False


def reply_current_gump(button_id):
    try:
        result = API.ReplyGump(int(button_id))
        return False if result is False else True
    except Exception:
        try:
            API.ReplyGump(int(button_id))
            return True
        except Exception:
            return False


# ----------------------------------------------------------------------
# Application
# ----------------------------------------------------------------------

class FreeSkillsMaster:
    def __init__(self):
        self.running = True
        self.paused = pbool("Paused", False)
        self.train_all = pbool("TrainAll", False)
        self.build_training = pbool("BuildTraining", False)
        self.sit_still = pbool("SitStill", False)
        self.minimal = pbool("Minimal", False)
        self.page = str(pget("Page", "FREE") or "FREE").upper()
        if self.page not in ("FREE", "EXTRA", "BARD", "BUILD"):
            self.page = "FREE"

        self.gump_x = pint("GumpX", 120)
        self.gump_y = pint("GumpY", 120)
        self.ui = None

        self.status = "Ready."
        self.status_label = None
        self.skill_value_labels = {}
        self.skill_state_labels = {}
        self.goal_buttons = {}

        self.enabled = {}
        self.targets = {}
        self.second_targets = {}
        self.goals = {}
        self.goal_editor_gump = None
        self.goal_editor_box = None
        self.goal_editor_skill = None
        self.build_editor_gump = None
        self.build_editor_box = None
        self.skill_picker_gump = None
        self.build_library_gump = None
        self.build_name_gump = None
        self.build_name_box = None
        self.channel_busy_until = {}
        self.auto_build_locks = pbool("AutoBuildLocks", False)
        self.stat_goals = {
            "str": pfloat("StatGoal_STR", 0.0),
            "dex": pfloat("StatGoal_DEX", 0.0),
            "int": pfloat("StatGoal_INT", 0.0),
        }
        self.stat_editor_gump = None
        self.stat_editor_box = None
        self.stat_editor_name = None
        self.build_code_gump = None
        self.build_code_box = None
        self.stat_profile = self._load_stat_profile()
        self.next_lock_sync = 0.0
        self.next_action_at = {}
        self.cast_protect_until = 0.0
        self.global_action_at = 0.0
        self.last_cast_skill = ""
        self.target_busy_since = 0.0
        self.target_watchdog_grace = 2.25
        self.last_values = {}
        self.gain_counts = {}

        for skill in ALL_SKILLS:
            key = self._skill_key(skill)
            self.enabled[skill] = pbool("Enabled_" + key, False)
            self.targets[skill] = pint("Target_" + key, 0)
            self.second_targets[skill] = pint("Target2_" + key, 0)
            self.goals[skill] = pfloat("Goal_" + key, 0.0)
            self.next_action_at[skill] = 0.0
            self.last_values[skill] = skill_value(skill)
            self.gain_counts[skill] = pint("Gains_" + key, 0)

        self.tracking_category = str(pget("TrackingCategory", "Players") or "Players")
        if self.tracking_category not in [x[0] for x in TRACKING_CATEGORIES]:
            self.tracking_category = "Players"

        # Lightweight practice locations for resource skills.
        self.practice_locations = {}
        for _skill in ("Fishing", "Mining", "Lumberjacking"):
            _key = self._skill_key(_skill)
            self.practice_locations[_skill] = (
                pint("PosX_" + _key, 0),
                pint("PosY_" + _key, 0),
                pint("PosZ_" + _key, 0),
                pint("PosG_" + _key, 0),
            )

        self.rotation = 0
        self.last_save_at = time.time()
        self.last_ui_refresh = 0.0

        # Never leave unsupported modules accidentally enabled after an update.
        for skill in MODULE_SKILLS:
            self.enabled[skill] = False

    def _skill_key(self, skill):
        return re.sub(r"[^A-Za-z0-9]+", "_", str(skill)).strip("_")

    def _remember_pos(self):
        if not self.ui:
            return
        try:
            if self.ui.IsDisposed:
                return
        except Exception:
            pass
        try:
            self.gump_x = int(self.ui.GetX())
            self.gump_y = int(self.ui.GetY())
            pset("GumpX", self.gump_x)
            pset("GumpY", self.gump_y)
        except Exception:
            pass

    def save(self):
        pset("Paused", 1 if self.paused else 0)
        pset("TrainAll", 1 if self.train_all else 0)
        pset("BuildTraining", 1 if self.build_training else 0)
        pset("SitStill", 1 if self.sit_still else 0)
        pset("Minimal", 1 if self.minimal else 0)
        pset("Page", self.page)
        pset("TrackingCategory", self.tracking_category)
        pset("AutoBuildLocks", 1 if self.auto_build_locks else 0)
        try:
            pset("StatProfile", json.dumps(self._normalize_stat_profile(self.stat_profile), separators=(",",":")))
        except Exception:
            pass
        for _stat in ("str", "dex", "int"):
            pset("StatGoal_" + _stat.upper(), float(self.stat_goals.get(_stat, 0.0) or 0.0))
        for _skill, _pos in self.practice_locations.items():
            _key = self._skill_key(_skill)
            try:
                _x, _y, _z, _g = _pos
            except Exception:
                _x = _y = _z = _g = 0
            pset("PosX_" + _key, int(_x))
            pset("PosY_" + _key, int(_y))
            pset("PosZ_" + _key, int(_z))
            pset("PosG_" + _key, int(_g))
        for skill in ALL_SKILLS:
            key = self._skill_key(skill)
            pset("Enabled_" + key, 1 if self.enabled.get(skill, False) else 0)
            pset("Target_" + key, int(self.targets.get(skill, 0) or 0))
            pset("Target2_" + key, int(self.second_targets.get(skill, 0) or 0))
            pset("Goal_" + key, float(self.goals.get(skill, 0.0) or 0.0))
            pset("Gains_" + key, int(self.gain_counts.get(skill, 0) or 0))
        self._remember_pos()

    def _goal(self, skill):
        """Return the saved BUILD goal. A goal may intentionally exceed the current skill cap."""
        try:
            configured = float(self.goals.get(skill, 0.0) or 0.0)
        except Exception:
            configured = 0.0
        if configured > 0.0:
            return configured
        return float(skill_cap(skill))

    def _training_goal(self, skill):
        """Highest value the trainer can currently reach without a higher power scroll."""
        goal = float(self._goal(skill))
        cap = float(skill_cap(skill))
        if cap > 0.0:
            return min(goal, cap)
        return goal

    def _at_goal(self, skill):
        return skill_value(skill) >= self._goal(skill) - 0.05

    def _at_training_limit(self, skill):
        return skill_value(skill) >= self._training_goal(skill) - 0.05

    def _required_power_scroll(self, skill):
        goal = float(self._goal(skill))
        cap = float(skill_cap(skill))
        if goal <= cap + 0.05:
            return 0
        # Standard UO power-scroll tiers are 105/110/115/120. Keep this
        # future-proof for custom shards by rounding larger goals to the next 5.
        required = int(((goal + 4.999) // 5) * 5)
        return max(105, required)

    def _goal_text(self, skill):
        goal = self._goal(skill)
        return "{:.0f}".format(goal) if abs(goal - round(goal)) < 0.05 else "{:.1f}".format(goal)

    def _explicit_build_skills(self):
        return [s for s in ALL_SKILLS if float(self.goals.get(s, 0.0) or 0.0) > 0.0]

    def _build_store(self):
        data = _load_local()
        builds = data.setdefault("saved_builds", {})
        return builds if isinstance(builds, dict) else {}

    def _current_build_payload(self, name=""):
        return {
            "format": "JCS_SkillMaster_Build_v1",
            "name": str(name or "Custom Build"),
            "skills": {s: float(self.goals.get(s, 0.0) or 0.0) for s in self._explicit_build_skills()},
            "stats": {k: float(self._normalize_stat_profile(self.stat_profile)["mins"].get(k, 0.0) or 0.0) for k in ("str","dex","int")},
            "stat_profile": self._normalize_stat_profile(self.stat_profile),
        }

    def _apply_build_payload(self, payload, replace=True):
        if not isinstance(payload, dict):
            return False
        skills = payload.get("skills", {})
        stats = payload.get("stats", {})
        if not isinstance(skills, dict):
            return False
        if replace:
            for s in ALL_SKILLS:
                self.goals[s] = 0.0
                self.enabled[s] = False
            for st in ("str","dex","int"):
                self.stat_goals[st] = 0.0
            self.stat_profile = self._normalize_stat_profile({"mins":{},"maxs":{"str":125,"dex":125,"int":125},"priority":["str","dex","int"]})
        applied = 0
        for raw, value in skills.items():
            skill = self._resolve_build_skill(raw)
            if not skill:
                continue
            try:
                value = max(0.0, float(value))
            except Exception:
                continue
            self.goals[skill] = value
            applied += 1
        incoming_profile = payload.get("stat_profile", None)
        if isinstance(incoming_profile, dict):
            self.stat_profile = self._normalize_stat_profile(incoming_profile)
        elif isinstance(stats, dict):
            legacy_mins = {}
            for st in ("str","dex","int"):
                try:
                    legacy_mins[st] = max(0.0, float(stats.get(st, 0.0) or 0.0))
                except Exception:
                    legacy_mins[st] = 0.0
            self.stat_profile = self._normalize_stat_profile({
                "mins": legacy_mins,
                "maxs": {"str":125,"dex":125,"int":125},
                "priority": self._infer_stat_priority(),
            })        self.stat_goals = dict(self._adaptive_stat_targets())
        self.save()
        if self.auto_build_locks:
            self.apply_build_locks(silent=True)
        return applied > 0

    def _build_code(self, name=None):
        payload = self._current_build_payload(str(name or pget("LastBuildName","Shared Build") or "Shared Build"))
        raw = json.dumps(payload, separators=(",",":"), sort_keys=True).encode("utf-8")
        packed = zlib.compress(raw, 9)
        token = base64.urlsafe_b64encode(packed).decode("ascii").rstrip("=")
        return BUILD_CODE_PREFIX + token

    def _decode_build_code(self, code):
        code = re.sub(r"\s+", "", str(code or "").strip())
        if not code.startswith(BUILD_CODE_PREFIX):
            raise ValueError("Build code must start with {}".format(BUILD_CODE_PREFIX))
        token = code[len(BUILD_CODE_PREFIX):]
        token += "=" * ((4 - len(token) % 4) % 4)
        raw = zlib.decompress(base64.urlsafe_b64decode(token.encode("ascii")))
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Invalid build payload")
        return payload

    def open_share_code(self):
        self.close_build_code()
        code = self._build_code()
        g=API.CreateGump(True,True,True); g.SetRect(self.gump_x+90,self.gump_y+90,640,180)
        bg=API.CreateGumpColorBox(.97,C_BG); bg.SetRect(0,0,640,180); g.Add(bg)
        title=API.CreateGumpTTFLabel("SHARE BUILD CODE",15,C_TITLE,"","center",620,False); title.SetRect(10,8,620,22); g.Add(title)
        box=API.CreateGumpTextBox(code,590,52,False,12); box.SetPos(22,42); g.Add(box)
        note=API.CreateGumpTTFLabel("Ctrl+A / Ctrl+C this code and paste it in Discord. No JSON file is needed.",10,C_MUTED,"","center",590,False); note.SetRect(22,102,590,20); g.Add(note)
        close=API.CreateSimpleButton("CLOSE",80,28); close.SetPos(536,136); g.Add(close)
        API.AddControlOnClick(close,self.close_build_code)
        self.build_code_gump=g; self.build_code_box=box; API.AddGump(g)

    def open_import_code(self):
        self.close_build_code()
        g=API.CreateGump(True,True,True); g.SetRect(self.gump_x+90,self.gump_y+90,640,190)
        bg=API.CreateGumpColorBox(.97,C_BG); bg.SetRect(0,0,640,190); g.Add(bg)
        title=API.CreateGumpTTFLabel("IMPORT BUILD CODE",15,C_TITLE,"","center",620,False); title.SetRect(10,8,620,22); g.Add(title)
        box=API.CreateGumpTextBox("",590,52,False,12); box.SetPos(22,42); g.Add(box)
        imp=API.CreateSimpleButton("IMPORT",84,28); imp.SetPos(444,136); g.Add(imp)
        close=API.CreateSimpleButton("CANCEL",84,28); close.SetPos(536,136); g.Add(close)
        self.build_code_gump=g; self.build_code_box=box
        API.AddControlOnClick(imp,self.apply_import_code)
        API.AddControlOnClick(close,self.close_build_code)
        API.AddGump(g)

    def apply_import_code(self):
        try:
            raw = str(self.build_code_box.Text or "").strip()
            payload = self._decode_build_code(raw)
            ok = self._apply_build_payload(payload, replace=True)
            name = str(payload.get("name","Shared Build") or "Shared Build")
            self.close_build_code()
            self.page="BUILD"
            self.status = "Imported build code: {}.".format(name) if ok else "Build code contained no recognized skills."
        except Exception as e:
            self.status = "Build code import failed: {}".format(str(e)[:55])
            self.close_build_code()
        self.build_ui()

    def close_build_code(self):
        if self.build_code_gump:
            try:
                if not self.build_code_gump.IsDisposed:
                    self.build_code_gump.Dispose()
            except Exception:
                pass
        self.build_code_gump=None
        self.build_code_box=None

    def _load_stat_profile(self):
        raw = str(pget("StatProfile", "") or "").strip()
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return self._normalize_stat_profile(data)
            except Exception:
                pass
        mins = {}
        for st in ("str", "dex", "int"):
            try:
                v = float(self.stat_goals.get(st, 0.0) or 0.0)
            except Exception:
                v = 0.0
            if v > 0:
                mins[st] = v
        return self._normalize_stat_profile({
            "mins": mins,
            "maxs": {"str": 125, "dex": 125, "int": 125},
            "priority": self._infer_stat_priority(),
        })

    def _normalize_stat_profile(self, profile):
        profile = profile if isinstance(profile, dict) else {}
        mins = profile.get("mins", {}) if isinstance(profile.get("mins", {}), dict) else {}
        maxs = profile.get("maxs", {}) if isinstance(profile.get("maxs", {}), dict) else {}
        priority = list(profile.get("priority", []) or [])
        clean_mins = {}
        clean_maxs = {}
        for st in ("str", "dex", "int"):
            try:
                clean_mins[st] = max(0.0, float(mins.get(st, 0.0) or 0.0))
            except Exception:
                clean_mins[st] = 0.0
            try:
                clean_maxs[st] = max(clean_mins[st], float(maxs.get(st, 125.0) or 125.0))
            except Exception:
                clean_maxs[st] = max(clean_mins[st], 125.0)
        clean_priority = []
        for st in priority:
            st = str(st).lower()
            if st in ("str", "dex", "int") and st not in clean_priority:
                clean_priority.append(st)
        for st in ("str", "dex", "int"):
            if st not in clean_priority:
                clean_priority.append(st)
        return {"mins": clean_mins, "maxs": clean_maxs, "priority": clean_priority}

    def _infer_stat_priority(self):
        skills = set(self._explicit_build_skills())
        weapon = bool(skills.intersection({"Swords", "Macing", "Fencing", "Archery", "Throwing", "Wrestling"}))
        caster = bool(skills.intersection({"Magery", "Mysticism", "Spellweaving", "Necromancy"}))
        if caster and not weapon:
            return ["int", "str", "dex"]
        if weapon:
            return ["str", "dex", "int"]
        return ["str", "dex", "int"]

    def _adaptive_stat_targets(self):
        profile = self._normalize_stat_profile(self.stat_profile)
        mins = dict(profile["mins"])
        maxs = dict(profile["maxs"])
        priority = list(profile["priority"])
        cap = max(0.0, float(self._stat_total_cap()))
        targets = {st: float(mins.get(st, 0.0) or 0.0) for st in ("str", "dex", "int")}
        minimum_total = sum(targets.values())

        if minimum_total > cap:
            excess = minimum_total - cap
            for st in reversed(priority):
                if excess <= 0.01:
                    break
                reducible = max(0.0, targets[st])
                cut = min(reducible, excess)
                targets[st] -= cut
                excess -= cut
            return targets

        extra = cap - minimum_total
        for st in priority:
            if extra <= 0.01:
                break
            room = max(0.0, float(maxs.get(st, 125.0)) - targets[st])
            add = min(room, extra)
            targets[st] += add
            extra -= add
        return targets

    def cycle_stat_priority(self):
        orders = [
            ["str", "dex", "int"], ["str", "int", "dex"],
            ["dex", "str", "int"], ["dex", "int", "str"],
            ["int", "str", "dex"], ["int", "dex", "str"],
        ]
        current = list(self._normalize_stat_profile(self.stat_profile)["priority"])
        try:
            idx = orders.index(current)
        except Exception:
            idx = -1
        self.stat_profile["priority"] = orders[(idx + 1) % len(orders)]
        self.save()
        if self.auto_build_locks:
            self.apply_build_locks(silent=True)
        self.status = "Stat priority: {}.".format(" > ".join(x.upper() for x in self.stat_profile["priority"]))
        self.build_ui()

    def _stat_value(self, stat):
        try:
            if stat == "str": return float(API.Player.Strength)
            if stat == "dex": return float(API.Player.Dexterity)
            if stat == "int": return float(API.Player.Intelligence)
        except Exception:
            pass
        return 0.0

    def _stat_goal(self, stat):
        try:
            return max(0.0, float(self._adaptive_stat_targets().get(stat, 0.0) or 0.0))
        except Exception:
            return 0.0

    def _stat_total_cap(self):
        """Read the character's total stat cap when exposed by Legion; standard fallback is 225."""
        try:
            for attr in ("StatCap", "StatsCap", "StatCapMax", "StatsCapMax"):
                try:
                    value = float(getattr(API.Player, attr))
                    if value >= 100:
                        return value
                except Exception:
                    pass
        except Exception:
            pass
        return 225.0

    def _stat_goal_total(self):
        return sum(self._stat_goal(st) for st in ("str", "dex", "int"))

    def _required_stat_cap(self):
        # Adaptive mode always builds to the character's CURRENT cap.
        return 0

    def _stat_state_for_goal(self, stat):
        goal = self._stat_goal(stat)
        cur = self._stat_value(stat)
        if goal <= 0:
            return "locked"
        if cur < goal - 0.5:
            return "up"
        if cur > goal + 0.5:
            return "down"
        return "locked"

    def apply_build_locks(self, silent=False):
        """Make build skills rise until goal, lock finished/non-build skills, and steer stats to goals."""
        explicit = set(self._explicit_build_skills())
        skill_ok = 0
        stat_ok = 0
        try:
            for skill in ALL_SKILLS:
                state = "locked"
                if skill in explicit and not self._at_goal(skill):
                    state = "locked" if self._at_training_limit(skill) and self._required_power_scroll(skill) else "up"
                API.SetSkillLock(skill_api_name(skill), state)
                skill_ok += 1
        except Exception as e:
            if not silent:
                self.status = "Skill lock update failed: {}".format(e)
            return False

        for stat in ("str", "dex", "int"):
            try:
                API.SetStatLock(stat, self._stat_state_for_goal(stat))
                stat_ok += 1
            except Exception:
                pass

        if not silent:
            self.status = "Build locks applied: {} skills, {} stats.".format(skill_ok, stat_ok)
            self.build_ui()
        return True

    def toggle_auto_build_locks(self):
        self.auto_build_locks = not self.auto_build_locks
        self.save()
        if self.auto_build_locks:
            self.apply_build_locks(silent=True)
            self.status = "AUTO LOCK ON: build skills rise to goal; completed/non-build skills lock."
        else:
            self.status = "AUTO LOCK OFF. Existing in-game lock states are left as-is."
        self.build_ui()

    def open_stat_editor(self, stat):
        stat = str(stat).lower()
        if stat not in ("str", "dex", "int"):
            return
        self.close_stat_editor()
        g = API.CreateGump(True, True, True)
        g.SetRect(self.gump_x + 235, self.gump_y + 120, 330, 128)
        bg = API.CreateGumpColorBox(0.96, C_BG); bg.SetRect(0,0,330,128); g.Add(bg)
        title = API.CreateGumpTTFLabel("SET {} MINIMUM".format(stat.upper()),14,C_TITLE,"","center",310,False)
        title.SetRect(10,8,310,22); g.Add(title)
        box = API.CreateGumpTextBox(str(int(self._normalize_stat_profile(self.stat_profile)["mins"].get(stat,0))) if self._normalize_stat_profile(self.stat_profile)["mins"].get(stat,0) else "0",120,30,False,16)
        box.SetPos(24,42); g.Add(box)
        save_btn=API.CreateSimpleButton("SAVE",72,28); save_btn.SetPos(160,42); g.Add(save_btn)
        cancel_btn=API.CreateSimpleButton("CANCEL",72,28); cancel_btn.SetPos(240,42); g.Add(cancel_btn)
        cap_need=self._required_stat_cap()
        help_text="Minimum for this build. Extra stat-cap points follow the selected PRIORITY."
        if cap_need:
            help_text += " | build needs {} stat cap".format(cap_need)
        help_label=API.CreateGumpTTFLabel(help_text,10,C_MUTED,"","center",300,False)
        help_label.SetRect(15,82,300,20); g.Add(help_label)
        self.stat_editor_gump=g; self.stat_editor_box=box; self.stat_editor_name=stat
        API.AddControlOnClick(save_btn,self.save_stat_editor)
        API.AddControlOnClick(cancel_btn,self.close_stat_editor)
        API.AddGump(g)

    def save_stat_editor(self):
        stat=self.stat_editor_name
        try: value=float(str(self.stat_editor_box.Text or "0").strip())
        except Exception: value=0.0
        self.stat_profile = self._normalize_stat_profile(self.stat_profile)
        self.stat_profile["mins"][stat] = max(0.0,value)
        self.stat_profile["maxs"][stat] = max(self.stat_profile["mins"][stat], float(self.stat_profile["maxs"].get(stat,125.0)))
        self.stat_goals = dict(self._adaptive_stat_targets())
        self.save()
        self.close_stat_editor()
        if self.auto_build_locks: self.apply_build_locks(silent=True)
        self.status="{} minimum set to {:.0f}; adaptive target is {:.0f}.".format(stat.upper(),value,self._stat_goal(stat))
        self.build_ui()

    def close_stat_editor(self):
        if self.stat_editor_gump:
            try:
                if not self.stat_editor_gump.IsDisposed: self.stat_editor_gump.Dispose()
            except Exception: pass
        self.stat_editor_gump=None; self.stat_editor_box=None; self.stat_editor_name=None

    # ---------------- UI ----------------

    def _new_gump(self, width, height):
        old = self.ui
        if old:
            try:
                if not old.IsDisposed:
                    self._remember_pos()
                    old.Dispose()
            except Exception:
                pass

        self.ui = API.CreateGump(True, True, True)
        self.ui.SetRect(self.gump_x, self.gump_y, width, height)

        bg = API.CreateGumpColorBox(0.92, C_BG)
        bg.SetRect(0, 0, width, height)
        self.ui.Add(bg)

    def _label(self, text, x, y, width, color=C_TEXT, size=12, align="left"):
        label = API.CreateGumpTTFLabel(
            str(text), int(size), color, "", str(align), int(width), False
        )
        label.SetRect(int(x), int(y), int(width), 22)
        self.ui.Add(label)
        return label

    def _panel(self, x, y, w, h, color=C_PANEL):
        panel = API.CreateGumpColorBox(0.60, color)
        panel.SetRect(int(x), int(y), int(w), int(h))
        self.ui.Add(panel)
        return panel

    def _button(self, text, x, y, w, callback, h=25, tooltip=None, state=None):
        button = API.CreateSimpleButton(str(text), int(w), int(h))
        button.SetPos(int(x), int(y))
        try:
            button.DisplayBorder = True
            button.AlwaysShowBackground = True
        except Exception:
            pass

        try:
            if state is True:
                button.SetBackgroundColor(*ACTIVE_GREEN)
            elif state is False:
                button.SetBackgroundColor(*OFF_RED)
            else:
                button.SetBackgroundColor(*ACTION_BROWN)
        except Exception:
            pass

        self.ui.Add(button)
        API.AddControlOnClick(button, callback)
        if tooltip:
            try:
                button.SetTooltip(str(tooltip))
            except Exception:
                pass
        return button

    def build_ui(self):
        self.save()

        if self.minimal:
            self._build_minimal()
            return

        width, height = 820, 700
        self._new_gump(width, height)

        self._label(APP, 16, 7, 430, C_TITLE, 16)
        self._label(VERSION, 448, 9, 90, C_MUTED, 11, "right")

        self._button("_", 762, 4, 20, self.minimize, 22, "Minimize.")
        self._button("X", 788, 4, 20, self.close, 22, "Close Skill Master.")

        self._button(
            "RESUME" if self.paused else "PAUSE",
            16, 38, 78, self.toggle_pause,
            state=self.paused,
            tooltip="Pause or resume all automated training."
        )
        self._button(
            "TRAIN ALL ON" if self.train_all else "TRAIN ALL OFF",
            100, 38, 112, self.toggle_train_all,
            state=self.train_all,
            tooltip="Enable all currently automatable skills that have required setup."
        )
        self._button(
            "SIT STILL ON" if self.sit_still else "SIT STILL OFF",
            218, 38, 112, self.toggle_sit_still,
            state=self.sit_still,
            tooltip="Train only no-target/self-target skills that can be practiced while parked."
        )
        self._button(
            "REFRESH", 336, 38, 72, self.refresh_ui,
            tooltip="Refresh skill values and setup state."
        )
        self._button(
            "FREE", 414, 38, 56, lambda: self.set_page("FREE"),
            state=(self.page == "FREE"),
            tooltip="Show InsaneUO free-skill trainers."
        )
        self._button(
            "CAST", 474, 38, 56, lambda: self.set_page("EXTRA"),
            state=(self.page == "EXTRA"),
            tooltip="Show casting and other easy unattended trainers."
        )
        self._button(
            "BARD", 534, 38, 56, lambda: self.set_page("BARD"),
            state=(self.page == "BARD"),
            tooltip="Show Musicianship, Discordance, Peacemaking and Provocation trainers."
        )
        self._button(
            "BUILD", 594, 38, 60, lambda: self.set_page("BUILD"),
            state=(self.page == "BUILD"),
            tooltip="Open the character build dashboard."
        )
        explicit_build = self._explicit_build_skills()
        done_goals = sum(1 for s in explicit_build if self._at_goal(s))
        self._label(
            "{} / {} build".format(done_goals, len(explicit_build)),
            658, 43, 132, C_GOLD, 10, "center"
        )

        self._panel(12, 72, 796, 39)
        self.status_label = self._label(self.status, 20, 80, 780, C_TEXT, 12)

        if self.page == "BUILD":
            self._build_build_page()
        else:
            # Two-column paged grid keeps the master compact as more trainers are added.
            if self.page == "FREE":
                page_skills = FREE_SKILLS
            elif self.page == "BARD":
                page_skills = BARD_SKILLS
            else:
                page_skills = EXTRA_SKILLS
            split = (len(page_skills) + 1) // 2
            left = page_skills[:split]
            right = page_skills[split:]
            self._build_skill_column(left, 14, 122, 382)
            self._build_skill_column(right, 424, 122, 382)

            self._panel(12, 646, 796, 40, C_PANEL_2)
            self._label(
                "Hover SETUP/SPOT for exact requirements   Green = enabled/done   GOAL = desired level   Manual gains count",
                20, 656, 780, C_MUTED, 11, "center"
            )

        API.AddGump(self.ui)
        try:
            self.ui.SetInScreen()
        except Exception:
            pass

    def _build_setup_kind(self, skill):
        """Return the interactive setup type used by the BUILD pre-flight UI."""
        if skill not in AUTOMATED_SKILLS:
            return "manual"
        if skill in ("Fishing", "Mining", "Lumberjacking"):
            return "spot"
        if skill in ("Discordance", "Provocation"):
            return "bard"
        if skill in ("Musicianship", "Peacemaking"):
            return "auto"
        if skill in TARGET_SKILLS:
            return "target"
        return "auto"

    def _build_setup_configured(self, skill):
        """Whether all user-selectable setup for this skill has been saved."""
        kind = self._build_setup_kind(skill)
        if kind in ("manual", "auto"):
            return True
        if kind == "spot":
            return self._practice_location_set(skill)
        if kind == "bard":
            if skill == "Discordance":
                return bool(int(self.targets.get(skill, 0) or 0))
            if skill == "Provocation":
                return bool(int(self.targets.get(skill, 0) or 0) and int(self.second_targets.get(skill, 0) or 0))
        if kind == "target":
            return bool(int(self.targets.get(skill, 0) or 0))
        return True

    def _build_setup_state(self, skill):
        """Friendly pre-flight state shown directly on each BUILD row."""
        if skill not in AUTOMATED_SKILLS:
            return "MANUAL"
        if not self._build_setup_configured(skill):
            return "SET SPOT" if self._build_setup_kind(skill) == "spot" else "SETUP"
        if self._ready(skill):
            return "READY"
        # Setup is saved, but a backpack/tool/resource dependency is missing.
        if skill in BARD_SKILLS and not self._bard_instrument():
            return "NEED INST"
        if skill == "Camping" and not first_graphic(KINDLING_GRAPHIC):
            return "NEED KINDLING"
        if skill == "Lockpicking" and not first_graphic(LOCKPICK_GRAPHIC):
            return "NEED PICKS"
        if skill == "Herding" and not tool_by_graphics(SHEPHERDS_CROOK_GRAPHICS):
            return "NEED CROOK"
        if skill == "Fishing" and not tool_by_graphics(FISHING_POLE_GRAPHIC):
            return "NEED POLE"
        if skill == "Mining" and not tool_by_graphics((PICKAXE_GRAPHIC, SHOVEL_GRAPHIC)):
            return "NEED TOOL"
        if skill == "Lumberjacking" and not tool_by_graphics(HATCHET_GRAPHIC):
            return "NEED AXE"
        if skill == "Animal Taming" and skill_value("Animal Taming") < 90.0:
            return "WAIT 90"
        if skill in ("Alchemy", "Inscription"):
            return "CHECK CHEST"
        return "WAIT"

    def _build_setup_tooltip(self, skill):
        state = self._build_setup_state(skill)
        base = self._setup_tooltip(skill)
        if state == "READY":
            return "READY FOR BUILD GO. " + base
        if state == "MANUAL":
            return "Skill Master tracks this build skill, but it does not have an unattended trainer yet."
        if state.startswith("NEED") or state.startswith("CHECK") or state.startswith("WAIT"):
            return "Setup is saved, but BUILD GO is waiting on: {}. {}".format(state, base)
        return base

    def _run_build_setup(self, skill):
        """Configure one BUILD-row setup using the same normal trainer setup paths."""
        kind = self._build_setup_kind(skill)
        if kind == "manual":
            self.status = "{} is currently manual-only; no unattended setup is available.".format(skill)
            self.build_ui()
            return
        if kind == "spot":
            self.set_practice_location(skill)
            return
        if kind == "bard":
            self.set_bard_setup(skill)
            return
        if kind == "target":
            self.set_target(skill)
            return
        # AUTO skills need no target selection; show exactly what dependency is missing.
        self.status = "{} setup: {}.".format(skill, self._build_setup_state(skill))
        self.build_ui()

    def prep_all_build_setups(self):
        """Walk through every missing interactive setup in the loaded build."""
        skills = self._explicit_build_skills()
        missing = [s for s in skills if s in AUTOMATED_SKILLS and not self._build_setup_configured(s)]
        if not missing:
            ready = sum(1 for s in skills if s in AUTOMATED_SKILLS and self._ready(s))
            waiting = sum(1 for s in skills if s in AUTOMATED_SKILLS and not self._ready(s))
            self.status = "BUILD PREP: no target/spot setup missing. {} ready; {} waiting on tools/resources/requirements.".format(ready, waiting)
            self.build_ui()
            return

        completed = 0
        cancelled = False
        for skill in missing:
            kind = self._build_setup_kind(skill)
            if kind == "spot":
                try:
                    API.SysMsg("BUILD PREP: target the {} practice spot.".format(skill), 68)
                    API.RequestTarget(10)
                    pos = API.LastTargetPos
                    x, y, z = int(pos.X), int(pos.Y), int(pos.Z)
                    try:
                        graphic = int(API.LastTargetGraphic or 0)
                    except Exception:
                        graphic = 0
                    if not (x or y):
                        cancelled = True
                        break
                    self.practice_locations[skill] = (x, y, z, graphic)
                    completed += 1
                except Exception:
                    cancelled = True
                    break
                continue

            if kind == "bard":
                if skill == "Discordance":
                    first = request_serial("BUILD PREP: target the practice creature for Discordance.")
                    if not first:
                        cancelled = True
                        break
                    self.targets[skill] = int(first)
                    completed += 1
                elif skill == "Provocation":
                    first = request_serial("BUILD PREP: target the creature to PROVOKE.")
                    if not first:
                        cancelled = True
                        break
                    second = request_serial("BUILD PREP: target the SECOND creature the first should attack.")
                    if not second:
                        cancelled = True
                        break
                    self.targets[skill] = int(first)
                    self.second_targets[skill] = int(second)
                    completed += 1
                continue

            if kind == "target":
                desc = TARGET_SKILLS.get(skill, "target")
                serial = request_serial("BUILD PREP: target {} for {}.".format(desc, skill))
                if not serial:
                    cancelled = True
                    break
                self.targets[skill] = int(serial)
                completed += 1

        self.save()
        remaining = [s for s in skills if s in AUTOMATED_SKILLS and not self._build_setup_configured(s)]
        if cancelled:
            self.status = "BUILD PREP stopped after {} setup{}. {} still need setup.".format(completed, "" if completed == 1 else "s", len(remaining))
        else:
            ready = sum(1 for s in skills if s in AUTOMATED_SKILLS and self._ready(s))
            waiting = sum(1 for s in skills if s in AUTOMATED_SKILLS and not self._ready(s))
            self.status = "BUILD PREP complete: {} setup{} saved. {} ready; {} waiting on tools/resources/requirements.".format(completed, "" if completed == 1 else "s", ready, waiting)
        self.build_ui()

    def _build_build_page(self):
        skills = self._explicit_build_skills()
        self._button("ADD", 20, 120, 54, self.open_skill_picker, h=28,
                     tooltip="Pick a skill from a friendly list and add it to this build.")
        self._button("BUILDS", 80, 120, 70, self.open_build_library, h=28,
                     tooltip="Load built-in or saved builds. Shared builds use IMPORT CODE.")
        self._button("SAVE", 156, 120, 58, self.open_build_name_editor, h=28,
                     tooltip="Save this build by name for later use.")
        self._button("SHARE", 220, 120, 62, self.open_share_code, h=28,
                     tooltip="Show a compact JCS1 build code you can copy/paste into Discord.")
        self._button("IMPORT", 288, 120, 62, self.open_import_code, h=28,
                     tooltip="Paste a JCS1 build code from another player.")
        self._button("AUTO LOCK ON" if self.auto_build_locks else "AUTO LOCK OFF", 356, 120, 112,
                     self.toggle_auto_build_locks, h=28, state=self.auto_build_locks,
                     tooltip="Automatically set build skills UP until their goal, then LOCK. Non-build skills are LOCKED.")
        self._button("PREP ALL", 474, 120, 70, self.prep_all_build_setups, h=28,
                     tooltip="Pre-flight this build. Skill Master walks through every missing target, including the 90+ Taming mastery pet, chest, bard target, or harvesting spot so GO can run with as little interaction as possible.")
        self._button("STOP" if self.build_training else "GO", 550, 120, 54,
                     self.toggle_build_training, h=28, state=self.build_training,
                     tooltip="GO trains every automatable skill in THIS build toward its saved goal. PREP ALL first for the most unattended run possible.")

        targets = self._adaptive_stat_targets()
        pri = " > ".join(x.upper() for x in self._normalize_stat_profile(self.stat_profile)["priority"])
        self._button("STAT PRIORITY", 610, 120, 98, self.cycle_stat_priority, h=28,
                     tooltip="Adaptive stats use the character's actual current stat cap. Click to cycle which stat receives extra cap points first.")
        self._label("CAP {:.0f}: STR {:.0f} / DEX {:.0f} / INT {:.0f}".format(
            self._stat_total_cap(), targets["str"], targets["dex"], targets["int"]),
            20, 154, 360, C_GOLD, 9)
        self._label("PRIORITY {}".format(pri), 390, 154, 400, C_MUTED, 9, "right")

        self._label("BUILD SKILL", 18, 180, 175, C_ORANGE, 11)
        self._label("NOW", 198, 180, 56, C_ORANGE, 10, "center")
        self._label("GOAL", 258, 180, 54, C_ORANGE, 10, "center")
        self._label("PROGRESS", 316, 180, 92, C_ORANGE, 10, "center")
        self._label("SETUP", 412, 180, 86, C_ORANGE, 10, "center")
        self._label("TRAIN", 502, 180, 72, C_ORANGE, 10, "center")
        self._label("LOCK", 578, 180, 62, C_ORANGE, 10, "center")
        self._label("EDIT", 644, 180, 142, C_ORANGE, 10, "center")
        y = 204
        if not skills:
            self._panel(18, y, 772, 54)
            self._label("No build loaded. Click ADD, choose skills, set GOALS, then PREP ALL before GO.", 32, y+16, 740, C_MUTED, 12, "center")
        else:
            for skill in skills[:9]:
                val = skill_value(skill); goal = self._goal(skill); done = self._at_goal(skill)
                ps_needed = self._required_power_scroll(skill)
                train_blocked = (ps_needed > 0 and self._at_training_limit(skill))
                setup_state = self._build_setup_state(skill)
                setup_ready = (setup_state == "READY")
                self._panel(18, y, 772, 42)
                self._label(skill, 28, y+8, 164, C_TEXT, 11)
                self._label("{:.1f}".format(val), 198, y+8, 56, C_GREEN if done else C_GOLD, 10, "center")
                goal_tip = "Build goal {:.1f}. Current skill cap {:.1f}.".format(goal, skill_cap(skill))
                if ps_needed:
                    goal_tip += " This build requires a {} Power Scroll for this skill.".format(ps_needed)
                self._button(self._goal_text(skill), 258, y+6, 54, lambda s=skill:self.open_goal_editor(s), h=26, state=True if done else None, tooltip=goal_tip)
                status_text = "DONE" if done else (("NEEDS {} PS".format(ps_needed)) if ps_needed else "NEED {:.1f}".format(max(0.0, goal-val)))
                self._label(status_text, 316, y+8, 92, C_GREEN if done else C_GOLD, 8 if ps_needed else 9, "center")

                if skill in AUTOMATED_SKILLS:
                    if skill == "Animal Taming":
                        taming_value = skill_value("Animal Taming")
                        taming_pet = int(self.targets.get(skill, 0) or 0)
                        if taming_value < 90.0:
                            taming_text = "PET SET" if taming_pet else "90+ PET"
                            taming_ready = False
                        else:
                            taming_text = "READY 90+" if taming_pet else "90+ PET"
                            taming_ready = bool(taming_pet)
                        self._button(
                            taming_text, 412, y+6, 86,
                            lambda s=skill:self.set_target(s), h=26,
                            state=True if taming_ready else None,
                            tooltip=(
                                "Set the controlled pet used by the 90+ Animal Taming Combat Training mastery trainer. "
                                "You may save the pet before 90.0. At 90+ Skill Master uses Combat Training on this pet, "
                                "which can train Animal Taming and Animal Lore together."
                            )
                        )
                    else:
                        self._button(setup_state, 412, y+6, 86,
                                     lambda s=skill:self._run_build_setup(s), h=26,
                                     state=True if setup_ready else None,
                                     tooltip=self._build_setup_tooltip(skill))
                else:
                    self._label("MANUAL", 412, y+8, 86, C_MUTED, 9, "center")

                trainer = ("AUTO 90+" if skill == "Animal Taming" else ("AUTO" if skill in AUTOMATED_SKILLS else "MANUAL"))
                self._label(trainer, 502, y+8, 72, C_GREEN if skill in AUTOMATED_SKILLS else C_MUTED, 9, "center")
                lock_text = "LOCK" if done else ("WAIT PS" if train_blocked else "UP")
                self._label(lock_text, 578, y+8, 62, C_GREEN if done else C_GOLD, 8, "center")
                self._button("GOAL", 644, y+6, 52, lambda s=skill:self.open_goal_editor(s), h=26,
                             tooltip="Edit the desired build level for {}.".format(skill))
                self._button("X", 702, y+6, 28, lambda s=skill:self.remove_build_skill(s), h=26,
                             tooltip="Remove {} from this build only.".format(skill))
                y += 46
            if len(skills) > 9:
                self._label("+ {} more build skills".format(len(skills)-9), 28, y+4, 300, C_MUTED, 10)

        self._panel(12, 646, 796, 40, C_PANEL_2)
        self._label("BUILD PRE-FLIGHT: set goals -> PREP ALL -> resolve any NEED TOOL/RESOURCE warnings -> GO.", 20, 656, 780, C_MUTED, 10, "center")

    def _looks_like_bard_instrument(self, item):
        if not item:
            return False
        try:
            name = str(item.Name or "").strip().lower()
        except Exception:
            name = ""
        if any(word in name for word in INSTRUMENT_NAME_WORDS):
            return True
        try:
            serial = serial_of(item)
            props = str(API.ItemNameAndProps(int(serial), True, 2) or "").lower()
        except Exception:
            props = ""
        return any(word in props for word in INSTRUMENT_NAME_WORDS)

    def _find_bard_instrument(self):
        """Auto-detect an instrument and replace it when the previous one wears out."""
        current = int(self.targets.get("Musicianship", 0) or 0)
        if current:
            item = find_item(current)
            if item and self._looks_like_bard_instrument(item):
                return current

        for item in backpack_items():
            if not self._looks_like_bard_instrument(item):
                continue
            serial = serial_of(item)
            if serial:
                self.targets["Musicianship"] = int(serial)
                return int(serial)

        self.targets["Musicianship"] = 0
        return 0

    def _bard_instrument(self):
        return self._find_bard_instrument()

    def _bard_setup_ready(self, skill):
        instrument = self._bard_instrument()
        if not instrument:
            return False
        if skill in ("Musicianship", "Peacemaking"):
            return True
        if skill == "Discordance":
            return bool(int(self.targets.get(skill, 0) or 0))
        if skill == "Provocation":
            return bool(
                int(self.targets.get(skill, 0) or 0)
                and int(self.second_targets.get(skill, 0) or 0)
            )
        return True

    def _setup_tooltip(self, skill):
        tips = {
            "Arms Lore": "SETUP: Click one weapon or armor item that will stay accessible. Skill Master repeatedly uses Arms Lore on that same item.",
            "Begging": "SETUP: Click a nearby NPC/mobile that will remain in range. Skill Master repeatedly uses Begging on that target.",
            "Forensics": "SETUP: Click a corpse to examine. Corpses expire, so you may need to SETUP again when it disappears.",
            "Item ID": "SETUP: Click any persistent item in your backpack or nearby container. Skill Master repeatedly uses Item Identification on it.",
            "Lockpicking": "SETUP: Click a reusable training chest/box. Keep lockpicks in your backpack. Best results require a chest that can be relocked/reset for repeated attempts.",
            "Musicianship": "NO SETUP REQUIRED: Skill Master automatically finds bard instruments anywhere in your backpack. When one wears out it switches to another automatically, so keep several lutes/harps/drums/tambourines available for long sessions.",
            "Remove Trap": "SETUP: Click a reusable trapped training box. Keep it accessible so Remove Trap can be attempted repeatedly.",
            "Snooping": "SETUP: Click a container/backpack that you are allowed to snoop and that will stay accessible.",
            "Taste ID": "SETUP: Click a food or potion item that will remain available. Skill Master repeatedly uses Taste Identification on it.",
            "Herding": "SETUP: Click the animal/creature to herd. Also keep a shepherd's crook in your backpack. The creature must remain nearby.",
            "Alchemy": "SETUP: Click your Alchemy resource chest. Keep mortar/pestle, bottles and the required reagents stocked there; Skill Master restocks from this chest as recipes change.",
            "Inscription": "SETUP: Click your Inscription resource chest. Keep scribe pens, blank scrolls and Magery reagents stocked there; Skill Master restocks as training recipes change.",
            "Anatomy": "SETUP: Click a nearby mobile or training partner that can remain in range. Skill Master repeatedly uses Anatomy on it.",
            "Animal Lore": "SETUP: Click a nearby pet/animal that can remain in range. Skill Master repeatedly uses Animal Lore on it.",
            "Eval Int": "SETUP: Click a nearby mobile or training partner that can remain in range. Skill Master repeatedly uses Evaluating Intelligence on it.",
            "Discordance": "SETUP: Click one nearby practice creature that will remain in range. Instruments are found automatically in your backpack and replaced automatically when they wear out. Every cycle uses Discordance on that saved creature.",
            "Peacemaking": "NO CREATURE SETUP REQUIRED: Skill Master trains with AREA PEACE by targeting yourself. This also trains Musicianship, so when both skills need gains Skill Master prefers Area Peace and skips redundant Music attempts. Instruments are auto-detected and replaced as they wear out.",
            "Provocation": "SETUP: Click the creature to PROVOKE, then click the SECOND creature it should attack. Instruments are auto-detected and replaced automatically. Keep both creatures nearby and use safe/disposable practice targets.",
            "Animal Taming": "SETUP (90+ TAMING): First train Animal Taming manually to at least 90.0 and activate the Animal Taming mastery that provides Combat Training. Then click one nearby controlled pet. Combat Training can train BOTH Animal Taming and Animal Lore, so when both need gains Skill Master prefers this mastery loop and suppresses redundant Lore attempts. Keep the pet nearby and visible.",
        }
        if skill in ("Fishing", "Mining", "Lumberjacking"):
            need = {"Fishing": "a fishing pole", "Mining": "a pickaxe or shovel", "Lumberjacking": "a hatchet"}[skill]
            terrain = {"Fishing": "water", "Mining": "ore/mountain/cave floor", "Lumberjacking": "tree"}[skill]
            return "SPOT SETUP: Click one nearby {} tile you can repeatedly reach and keep {} in your backpack. Skill Master will reuse that saved tile.".format(terrain, need)
        return tips.get(skill, "SETUP: Click the object/mobile Skill Master should remember for repeated training.")

    def _control_tooltip(self, skill):
        base = "Toggle automatic training for {}.".format(skill)
        if skill in TARGET_SKILLS or skill in ("Fishing", "Mining", "Lumberjacking"):
            return base + " " + self._setup_tooltip(skill)
        if skill == "Camping":
            return base + " Keep kindling in your backpack; the trainer automatically uses it."
        if skill == "Tracking":
            return base + " No saved target is needed; choose the tracking category with the button beside it."
        if skill in ("Magery", "Necromancy", "Chivalry", "Spellweaving", "Mysticism", "Bushido"):
            return base + " No setup target is required; Skill Master chooses a training spell from your current skill and pauses for mana as needed."
        if skill in ("Meditation", "Spirit Speak", "Hiding", "Stealth", "Detect Hidden"):
            return base + " No external setup is required."
        return base

    def set_bard_setup(self, skill):
        if skill not in BARD_SKILLS:
            return

        instrument = self._bard_instrument()
        if skill == "Musicianship":
            self.status = (
                "Musicianship ready: instrument auto-detected."
                if instrument else
                "No bard instrument found. Put lutes/harps/drums/tambourines in your backpack."
            )
            self.save(); self.build_ui(); return

        if skill == "Peacemaking":
            self.status = (
                "Peacemaking ready: AREA PEACE targets yourself; instruments auto-switch."
                if instrument else
                "Peacemaking needs a bard instrument in your backpack; no creature setup is required."
            )
            self.save(); self.build_ui(); return

        first_prompt = {
            "Discordance": "target the practice creature to Discord.",
            "Provocation": "target the creature that should be PROVOKED.",
        }[skill]
        first = request_serial("Skill Master: {}".format(first_prompt))
        if not first:
            self.status = "{} setup cancelled before creature target.".format(skill)
            self.save(); self.build_ui(); return
        self.targets[skill] = int(first)

        if skill == "Provocation":
            second = request_serial(
                "Skill Master: target the SECOND creature that the first should ATTACK."
            )
            if not second:
                self.status = "Provocation setup needs two creatures."
                self.save(); self.build_ui(); return
            self.second_targets[skill] = int(second)
            self.status = "Provocation setup saved: two creatures; instruments auto-detect."
        else:
            self.status = "Discordance setup saved: practice creature; instruments auto-detect."
        self.save(); self.build_ui()

    def _build_skill_column(self, skills, x, y, width):
        self._label("SKILL", x + 4, y, 142, C_ORANGE, 11)
        self._label("VALUE", x + 146, y, 62, C_ORANGE, 11, "center")
        self._label("GOAL", x + 210, y, 54, C_ORANGE, 11, "center")
        self._label("CONTROL", x + 266, y, 108, C_ORANGE, 11, "center")
        y += 24

        for skill in skills:
            self._panel(x, y, width, 42)

            value = skill_value(skill)
            goal = self._goal(skill)
            done = value >= (goal - 0.05)

            self._label(skill, x + 8, y + 5, 136, C_TEXT, 12)
            value_label = self._label(
                "{:.1f}".format(value),
                x + 146, y + 5, 62,
                C_GREEN if done else C_GOLD,
                11, "center"
            )
            self.skill_value_labels[skill] = value_label
            goal_button = self._button(
                self._goal_text(skill), x + 210, y + 6, 52,
                lambda s=skill: self.open_goal_editor(s),
                h=26,
                state=True if done else None,
                tooltip="Set the desired level for {}. Current cap: {:.1f}. Manual gains count too.".format(skill, skill_cap(skill))
            )
            self.goal_buttons[skill] = goal_button

            if skill in MODULE_SKILLS:
                self._button(
                    "MODULE", x + 266, y + 6, 106,
                    lambda s=skill: self.module_info(s),
                    h=26,
                    tooltip="This skill is in the framework but its dedicated trainer is not integrated yet."
                )
            else:
                ready = self._ready(skill)
                active = self._effective_enabled(skill) and ready and not done
                control_text = "DONE" if done else ("ON" if active else "OFF")
                self._button(
                    control_text, x + 266, y + 6, 50,
                    lambda s=skill: self.toggle_skill(s),
                    h=26,
                    state=True if done or active else False,
                    tooltip=self._control_tooltip(skill)
                )

                if skill == "Tracking":
                    self._button(
                        self._tracking_short_label(),
                        x + 320, y + 6, 52,
                        self.cycle_tracking_category,
                        h=26,
                        state=True,
                        tooltip="Tracking category: {}. Click to cycle Animals / Monsters / NPCs / Players.".format(
                            self.tracking_category
                        )
                    )
                elif skill in ("Fishing", "Mining", "Lumberjacking"):
                    pos_set = self._practice_location_set(skill)
                    self._button(
                        "SET" if pos_set else "SPOT",
                        x + 320, y + 6, 52,
                        lambda s=skill: self.set_practice_location(s),
                        h=26,
                        state=True if pos_set else None,
                        tooltip=self._setup_tooltip(skill)
                    )
                elif skill in TARGET_SKILLS:
                    target_set = self._bard_setup_ready(skill) if skill in BARD_SKILLS else bool(self.targets.get(skill, 0))
                    self._button(
                        "SET" if target_set else "SETUP",
                        x + 320, y + 6, 52,
                        (lambda s=skill: self.set_bard_setup(s)) if skill in BARD_SKILLS else (lambda s=skill: self.set_target(s)),
                        h=26,
                        state=True if target_set else None,
                        tooltip=self._setup_tooltip(skill)
                    )

            sub = self._substatus(skill)
            # Keep helper text out from underneath the CONTROL buttons.
            self._label(sub, x + 8, y + 24, 250, C_MUTED, 9)

            y += 46

    def _build_minimal(self):
        width, height = 430, 82
        self._new_gump(width, height)

        self._label("SKILL MASTER", 12, 6, 142, C_TITLE, 14)
        self._button("_", 378, 3, 18, lambda: None, 20, "Already minimized.")
        self._button("X", 402, 3, 18, self.close, 20, "Close.")

        self._button(
            "RESUME" if self.paused else "PAUSE",
            12, 32, 70, self.toggle_pause,
            h=28,
            state=self.paused
        )
        self._button(
            "ALL ON" if self.train_all else "ALL OFF",
            88, 32, 66, self.toggle_train_all,
            h=28,
            state=self.train_all
        )
        self._button(
            "SIT ON" if self.sit_still else "SIT OFF",
            158, 32, 66, self.toggle_sit_still,
            h=28,
            state=self.sit_still
        )
        self._button("EXPAND", 344, 32, 74, self.expand, h=28)

        active = [s for s in AUTOMATED_SKILLS if self._effective_enabled(s) and self._ready(s)]
        current = active[self.rotation % len(active)] if active else "Idle"
        self._label(current[:18], 230, 31, 106, C_TEXT, 11, "center")
        self._label(
            "{} active".format(len(active)),
            230, 51, 106, C_GOLD, 10, "center"
        )
        API.AddGump(self.ui)
        try:
            self.ui.SetInScreen()
        except Exception:
            pass

    def open_goal_editor(self, skill):
        if skill not in ALL_SKILLS:
            return
        self.close_goal_editor()

        g = API.CreateGump(True, True, True)
        g.SetRect(self.gump_x + 170, self.gump_y + 90, 370, 132)
        bg = API.CreateGumpColorBox(0.96, C_BG)
        bg.SetRect(0, 0, 370, 132)
        g.Add(bg)

        title = API.CreateGumpTTFLabel(
            "SET {} GOAL".format(skill.upper()), 14, C_TITLE, "", "center", 350, False
        )
        title.SetRect(10, 8, 350, 22)
        g.Add(title)

        current_goal = self._goal_text(skill)
        box = API.CreateGumpTextBox(str(current_goal), 150, 30, False, 16)
        box.SetPos(18, 42)
        g.Add(box)

        save_btn = API.CreateSimpleButton("SAVE", 72, 28)
        save_btn.SetPos(182, 42)
        g.Add(save_btn)
        cap_btn = API.CreateSimpleButton("CAP", 72, 28)
        cap_btn.SetPos(264, 42)
        g.Add(cap_btn)
        cancel_btn = API.CreateSimpleButton("CANCEL", 72, 24)
        cancel_btn.SetPos(264, 82)
        g.Add(cancel_btn)

        ps_needed = self._required_power_scroll(skill)
        help_text = "Current {:.1f} | cap {:.1f} | CAP resets goal to cap.".format(skill_value(skill), skill_cap(skill))
        if ps_needed:
            help_text += " Needs {} PS for saved goal.".format(ps_needed)
        help_label = API.CreateGumpTTFLabel(
            help_text, 10, C_MUTED, "", "left", 320, False
        )
        help_label.SetRect(18, 84, 240, 20)
        g.Add(help_label)

        self.goal_editor_gump = g
        self.goal_editor_box = box
        self.goal_editor_skill = skill
        API.AddControlOnClick(save_btn, self.save_goal_editor)
        API.AddControlOnClick(cap_btn, self.reset_goal_to_cap)
        API.AddControlOnClick(cancel_btn, self.close_goal_editor)
        API.AddGump(g)

    def save_goal_editor(self):
        skill = self.goal_editor_skill
        if not skill or self.goal_editor_box is None:
            self.close_goal_editor()
            return
        try:
            raw = str(self.goal_editor_box.Text or "").strip()
            value = float(raw)
        except Exception:
            self.status = "Enter a numeric skill goal such as 80, 100, 110, or 120."
            return
        if value < 0.0:
            value = 0.0
        self.goals[skill] = value
        if self._at_goal(skill):
            self.enabled[skill] = False
        self.save()
        self.status = "{} goal set to {:.1f}.".format(skill, self._goal(skill))
        self.close_goal_editor()
        self.build_ui()

    def reset_goal_to_cap(self):
        skill = self.goal_editor_skill
        if skill:
            self.goals[skill] = 0.0
            self.save()
            self.status = "{} goal reset to current cap {:.1f}.".format(skill, skill_cap(skill))
        self.close_goal_editor()
        self.build_ui()

    def close_goal_editor(self):
        if self.goal_editor_gump:
            try:
                if not self.goal_editor_gump.IsDisposed:
                    self.goal_editor_gump.Dispose()
            except Exception:
                pass
        self.goal_editor_gump = None
        self.goal_editor_box = None
        self.goal_editor_skill = None

    def open_build_editor(self):
        self.close_build_editor()
        g = API.CreateGump(True, True, True)
        g.SetRect(self.gump_x + 80, self.gump_y + 80, 650, 190)
        bg = API.CreateGumpColorBox(0.96, C_BG)
        bg.SetRect(0, 0, 650, 190)
        g.Add(bg)
        title = API.CreateGumpTTFLabel("PASTE BUILD LIST (OPTIONAL)", 15, C_TITLE, "", "center", 630, False)
        title.SetRect(10, 8, 630, 22)
        g.Add(title)

        current = ", ".join("{} {}".format(s, self._goal_text(s)) for s in ALL_SKILLS if self.goals.get(s, 0.0) > 0)
        box = API.CreateGumpTextBox(current, 610, 54, False, 14)
        box.SetPos(20, 40)
        g.Add(box)

        help1 = API.CreateGumpTTFLabel(
            "Paste comma-separated goals: Magery 120, Eval Int 120, Meditation 100, Chivalry 80",
            10, C_MUTED, "", "left", 610, False
        )
        help1.SetRect(20, 100, 610, 20)
        g.Add(help1)
        help2 = API.CreateGumpTTFLabel(
            "For normal setup use ADD SKILL on the BUILD page. This box is only a faster paste option.",
            10, C_MUTED, "", "left", 610, False
        )
        help2.SetRect(20, 120, 610, 20)
        g.Add(help2)

        save_btn = API.CreateSimpleButton("APPLY BUILD", 112, 28)
        save_btn.SetPos(390, 148)
        g.Add(save_btn)
        cancel_btn = API.CreateSimpleButton("CANCEL", 90, 28)
        cancel_btn.SetPos(514, 148)
        g.Add(cancel_btn)
        self.build_editor_gump = g
        self.build_editor_box = box
        API.AddControlOnClick(save_btn, self.apply_build_editor)
        API.AddControlOnClick(cancel_btn, self.close_build_editor)
        API.AddGump(g)

    def open_skill_picker(self):
        self.close_skill_picker()
        g = API.CreateGump(True, True, True)
        g.SetRect(self.gump_x + 20, self.gump_y + 40, 800, 610)
        bg = API.CreateGumpColorBox(0.97, C_BG)
        bg.SetRect(0, 0, 800, 610)
        g.Add(bg)
        title = API.CreateGumpTTFLabel("ADD SKILL TO BUILD", 15, C_TITLE, "", "center", 780, False)
        title.SetRect(10, 8, 780, 22); g.Add(title)
        help_label = API.CreateGumpTTFLabel(
            "Click any skill. Automated and manual skills can both be tracked by the build dashboard.",
            10, C_MUTED, "", "center", 770, False)
        help_label.SetRect(15, 34, 770, 22); g.Add(help_label)
        existing = set(self._explicit_build_skills())
        choices = [s for s in ALL_SKILLS if s not in existing]
        rows = 18
        for idx, skill in enumerate(choices):
            ci = idx // rows; ri = idx % rows
            x = 20 + ci * 255; y = 68 + ri * 28
            btn = API.CreateSimpleButton(str(skill), 238, 24); btn.SetPos(x, y)
            try:
                btn.DisplayBorder = True; btn.AlwaysShowBackground = True
                btn.SetBackgroundColor(*ACTION_BROWN)
                btn.SetTooltip("Add {} to this character build.".format(skill))
            except Exception: pass
            g.Add(btn); API.AddControlOnClick(btn, lambda s=skill: self.add_build_skill(s))
        close_btn = API.CreateSimpleButton("CLOSE", 84, 28); close_btn.SetPos(690, 570); g.Add(close_btn)
        API.AddControlOnClick(close_btn, self.close_skill_picker)
        self.skill_picker_gump = g; API.AddGump(g)

    def close_skill_picker(self):
        if self.skill_picker_gump:
            try:
                if not self.skill_picker_gump.IsDisposed:
                    self.skill_picker_gump.Dispose()
            except Exception:
                pass
        self.skill_picker_gump = None

    def add_build_skill(self, skill):
        if skill not in ALL_SKILLS:
            return
        cap = float(skill_cap(skill) or 100.0)
        if cap <= 0:
            cap = 100.0
        self.goals[skill] = cap
        self.save()
        self.close_skill_picker()
        self.status = "{} added to build at goal {:.0f}. Click its GOAL to change it.".format(skill, cap)
        self.page = "BUILD"
        self.build_ui()

    def remove_build_skill(self, skill):
        if skill not in ALL_SKILLS:
            return
        self.goals[skill] = 0.0
        self.enabled[skill] = False
        self.save()
        if self.auto_build_locks:
            self.apply_build_locks(silent=True)
        self.status = "{} removed from build.".format(skill)
        self.build_ui()

    def open_build_name_editor(self):
        self.close_build_name_editor()
        g=API.CreateGump(True,True,True); g.SetRect(self.gump_x+220,self.gump_y+120,380,135)
        bg=API.CreateGumpColorBox(0.97,C_BG); bg.SetRect(0,0,380,135); g.Add(bg)
        title=API.CreateGumpTTFLabel("SAVE BUILD",14,C_TITLE,"","center",360,False); title.SetRect(10,8,360,22); g.Add(title)
        box=API.CreateGumpTextBox(str(pget("LastBuildName","My Build") or "My Build"),230,30,False,16); box.SetPos(18,43); g.Add(box)
        save=API.CreateSimpleButton("SAVE",76,28); save.SetPos(258,43); g.Add(save)
        close=API.CreateSimpleButton("CANCEL",76,24); close.SetPos(258,82); g.Add(close)
        self.build_name_gump=g; self.build_name_box=box
        API.AddControlOnClick(save,self.save_named_build); API.AddControlOnClick(close,self.close_build_name_editor); API.AddGump(g)

    def close_build_name_editor(self):
        if self.build_name_gump:
            try:
                if not self.build_name_gump.IsDisposed: self.build_name_gump.Dispose()
            except Exception: pass
        self.build_name_gump=None; self.build_name_box=None

    def save_named_build(self):
        try: name=str(self.build_name_box.Text or "").strip()
        except Exception: name=""
        if not name:
            self.status="Enter a build name first."; return
        store=self._build_store(); store[name]=self._current_build_payload(name)
        _save_local(); pset("LastBuildName",name)
        self.close_build_name_editor(); self.status="Saved build: {}".format(name); self.build_ui()

    def load_build_named(self, source, name):
        payload=None
        if source=="builtin": payload=BUILTIN_BUILDS.get(name)
        elif source=="saved": payload=self._build_store().get(name)
        if payload and self._apply_build_payload(payload,replace=True):
            self.status="Loaded build: {}".format(name); pset("LastBuildName",name)
        else: self.status="Could not load build: {}".format(name)
        self.close_build_library(); self.page="BUILD"; self.build_ui()

    def delete_saved_build(self, name):
        store=self._build_store()
        if name in store:
            del store[name]; _save_local(); self.status="Deleted saved build: {}".format(name)
        self.close_build_library(); self.open_build_library()

    def open_build_library(self):
        self.close_build_library()
        g=API.CreateGump(True,True,True); g.SetRect(self.gump_x+40,self.gump_y+35,740,620)
        bg=API.CreateGumpColorBox(0.97,C_BG); bg.SetRect(0,0,740,620); g.Add(bg)
        title=API.CreateGumpTTFLabel("BUILD LIBRARY",15,C_TITLE,"","center",720,False); title.SetRect(10,8,720,22); g.Add(title)
        def label(t,x,y,w,c=C_TEXT,s=11):
            z=API.CreateGumpTTFLabel(t,s,c,"","left",w,False); z.SetRect(x,y,w,20); g.Add(z)
        def btn(t,x,y,w,cb):
            b=API.CreateSimpleButton(t,w,24); b.SetPos(x,y); g.Add(b); API.AddControlOnClick(b,cb); return b
        y=42; label("BUILT-IN PRESETS",18,y,300,C_ORANGE,12); y+=24
        for name in sorted(BUILTIN_BUILDS):
            note=str(BUILTIN_BUILDS[name].get("note", ""))
            btn(name,20,y,250,lambda n=name:self.load_build_named("builtin",n))
            label(note[:62],280,y+3,430,C_MUTED,9); y+=28
        y+=8; label("MY SAVED BUILDS",18,y,300,C_ORANGE,12); y+=24
        saved=self._build_store()
        if not saved: label("No named builds saved yet.",22,y,300,C_MUTED,10); y+=24
        for name in sorted(saved)[:8]:
            btn(name,20,y,250,lambda n=name:self.load_build_named("saved",n))
            btn("DELETE",280,y,70,lambda n=name:self.delete_saved_build(n)); y+=28
        y+=8; label("SHARE / IMPORT",18,y,300,C_ORANGE,12); y+=24
        btn("IMPORT BUILD CODE",20,y,180,self.open_import_code)
        label("Paste a JCS1- code shared in Discord.",210,y+3,360,C_MUTED,10); y+=30
        close=API.CreateSimpleButton("CLOSE",84,28); close.SetPos(632,580); g.Add(close); API.AddControlOnClick(close,self.close_build_library)
        self.build_library_gump=g; API.AddGump(g)

    def close_build_library(self):
        if self.build_library_gump:
            try:
                if not self.build_library_gump.IsDisposed: self.build_library_gump.Dispose()
            except Exception: pass
        self.build_library_gump=None

    def _resolve_build_skill(self, name):
        n = re.sub(r"[^a-z0-9]+", "", str(name).lower())
        aliases = {
            "evaluatingintelligence": "Eval Int", "evalint": "Eval Int",
            "itemidentification": "Item ID", "itemid": "Item ID",
            "forensicevaluation": "Forensics", "forensics": "Forensics",
            "tasteidentification": "Taste ID", "tasteid": "Taste ID",
            "detecthidden": "Detect Hidden", "removetrap": "Remove Trap",
            "animallore": "Animal Lore", "spiritsspeak": "Spirit Speak", "spiritspeak": "Spirit Speak",
            "animaltaming": "Animal Taming", "resistingspells": "Resisting Spells", "resist": "Resisting Spells",
            "swordsmanship": "Swords", "swords": "Swords", "macefighting": "Macing", "macing": "Macing",
            "fencing": "Fencing", "parry": "Parrying", "parrying": "Parrying",
        }
        if n in aliases:
            return aliases[n]
        for skill in ALL_SKILLS:
            if re.sub(r"[^a-z0-9]+", "", skill.lower()) == n:
                return skill
        return None

    def apply_build_editor(self):
        try:
            raw = str(self.build_editor_box.Text or "").strip()
        except Exception:
            raw = ""
        if not raw:
            self.status = "Build entry was empty."
            return
        changed = []
        unknown = []
        # Parse from the right so skill names may contain spaces.
        for part in re.split(r"[,;\n]+", raw):
            part = part.strip()
            if not part:
                continue
            m = re.match(r"^(.+?)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*$", part)
            if not m:
                unknown.append(part)
                continue
            skill = self._resolve_build_skill(m.group(1))
            if not skill:
                unknown.append(m.group(1).strip())
                continue
            value = float(m.group(2))
            self.goals[skill] = max(0.0, value)
            if self._at_goal(skill):
                self.enabled[skill] = False
            changed.append(skill)
        self.save()
        if changed:
            self.status = "Build applied: {} goal{} updated{}.".format(
                len(changed), "" if len(changed) == 1 else "s",
                " | unknown: " + ", ".join(unknown[:3]) if unknown else ""
            )
        else:
            self.status = "No recognized build skills found."
        self.close_build_editor()
        self.page = "BUILD"
        if self.auto_build_locks:
            self.apply_build_locks(silent=True)
        self.save()
        self.build_ui()

    def close_build_editor(self):
        if self.build_editor_gump:
            try:
                if not self.build_editor_gump.IsDisposed:
                    self.build_editor_gump.Dispose()
            except Exception:
                pass
        self.build_editor_gump = None
        self.build_editor_box = None
        self.skill_picker_gump = None

    # ---------------- UI callbacks ----------------

    def refresh_ui(self):
        self.status = "Skill values refreshed."
        self.build_ui()

    def set_page(self, page):
        page = str(page or "FREE").upper()
        if page not in ("FREE", "EXTRA", "BARD", "BUILD"):
            page = "FREE"
        self.page = page
        self.save()
        if page == "BUILD":
            self.status = "Character build dashboard. Manual training counts automatically."
        else:
            self.status = "Showing {} trainers.".format("free skill" if page == "FREE" else ("bard" if page == "BARD" else "casting / easy"))
        self.build_ui()

    def toggle_pause(self):
        self.paused = not self.paused
        self.save()
        self.status = "Training paused." if self.paused else "Training resumed."
        self.build_ui()

    def toggle_sit_still(self):
        self.build_training = False
        self.sit_still = not self.sit_still

        if self.sit_still:
            # Make this an exclusive convenience mode so resource/target skills
            # do not unexpectedly fire while the player is parked.
            self.train_all = False
            for skill in AUTOMATED_SKILLS:
                self.enabled[skill] = (
                    skill in SIT_STILL_SKILLS
                    and not self._at_goal(skill)
                )
        else:
            for skill in SIT_STILL_SKILLS:
                self.enabled[skill] = False

        self.save()
        self.status = "Sit Still training {}: no-target / self-target skills only.".format(
            "ON" if self.sit_still else "OFF"
        )
        self.build_ui()

    def _sync_build_training_selection(self):
        """Keep automatic selection limited to the currently loaded BUILD."""
        if not self.build_training:
            return
        explicit = set(self._explicit_build_skills())
        for skill in AUTOMATED_SKILLS:
            self.enabled[skill] = bool(
                skill in explicit
                and not self._at_goal(skill)
                and not self._at_training_limit(skill)
            )

    def toggle_build_training(self):
        """Start/stop training every automatable skill in the active build."""
        explicit = self._explicit_build_skills()
        if not explicit:
            self.status = "BUILD GO needs at least one skill in the build."
            self.build_ui()
            return

        self.build_training = not self.build_training
        self.train_all = False
        self.sit_still = False

        if self.build_training:
            self._sync_build_training_selection()
            try:
                self.apply_build_locks(silent=True)
            except Exception:
                pass

            auto_total = 0
            ready_total = 0
            setup_wait = 0
            manual_total = 0
            ps_wait = 0
            for skill in explicit:
                if self._at_goal(skill):
                    continue
                if skill not in AUTOMATED_SKILLS:
                    manual_total += 1
                    continue
                if self._at_training_limit(skill):
                    ps_wait += 1
                    continue
                auto_total += 1
                if self._ready(skill):
                    ready_total += 1
                else:
                    setup_wait += 1

            self.status = (
                "BUILD GO: {} ready / {} auto | {} need setup | {} manual | {} waiting on cap/PS."
                .format(ready_total, auto_total, setup_wait, manual_total, ps_wait)
            )
        else:
            explicit_set = set(explicit)
            for skill in AUTOMATED_SKILLS:
                if skill in explicit_set:
                    self.enabled[skill] = False
            self.status = "BUILD training stopped. Build goals and setup were kept."

        self.save()
        self.build_ui()

    def toggle_train_all(self):
        self.build_training = False
        self.train_all = not self.train_all
        if self.train_all:
            self.sit_still = False

        if self.train_all:
            for skill in AUTOMATED_SKILLS:
                if self._ready(skill) and not self._at_goal(skill):
                    self.enabled[skill] = True
        else:
            for skill in AUTOMATED_SKILLS:
                self.enabled[skill] = False

        self.save()
        self.status = "Train All {}.".format("enabled" if self.train_all else "disabled")
        self.build_ui()

    def toggle_skill(self, skill):
        if skill not in AUTOMATED_SKILLS:
            return

        self.build_training = False
        self.train_all = False
        self.sit_still = False

        if self._at_goal(skill):
            self.status = "{} is already at its goal of {}.".format(skill, self._goal_text(skill))
            self.build_ui()
            return
        if self._at_training_limit(skill) and self._required_power_scroll(skill):
            self.status = "{} is at its current cap {:.1f}; build goal {} needs a {} Power Scroll.".format(
                skill, skill_cap(skill), self._goal_text(skill), self._required_power_scroll(skill)
            )
            self.build_ui()
            return

        if skill in BARD_SKILLS and not self._bard_setup_ready(skill):
            self.status = "{} needs bard setup first.".format(skill)
            self.set_bard_setup(skill)
            return
        if skill in TARGET_SKILLS and not self.targets.get(skill, 0):
            self.status = "{} needs a target first.".format(skill)
            self.set_target(skill)
            return

        self.enabled[skill] = not self.enabled.get(skill, False)
        self.save()
        self.status = "{} training {}.".format(
            skill, "ON" if self.enabled[skill] else "OFF"
        )
        self.build_ui()

    def set_target(self, skill):
        description = TARGET_SKILLS.get(skill, "target")
        if skill == "Animal Taming" and skill_value("Animal Taming") < 90.0:
            self.status = "Animal Taming mastery trainer unlocks at 90.0. You can save the pet now, but training will wait until 90."
        serial = request_serial(
            "Skill Master: target {} for {}.".format(description, skill)
        )
        if not serial:
            self.status = "{} target cancelled.".format(skill)
            self.build_ui()
            return

        self.targets[skill] = int(serial)
        self.save()
        self.status = "{} target saved: 0x{:X}.".format(skill, int(serial))
        self.build_ui()

    def _practice_location_set(self, skill):
        try:
            x, y, z, g = self.practice_locations.get(skill, (0, 0, 0, 0))
            return bool(int(x) or int(y))
        except Exception:
            return False

    def set_practice_location(self, skill):
        """Ask the player to click a water / ore / tree tile and remember LastTargetPos."""
        try:
            API.SysMsg(
                "Free Skills Master: target a nearby {} practice tile.".format(skill),
                68
            )
        except Exception:
            pass

        try:
            API.RequestTarget(10)
        except Exception:
            self.status = "{} practice target cancelled.".format(skill)
            self.build_ui()
            return

        try:
            pos = API.LastTargetPos
            x = int(pos.X)
            y = int(pos.Y)
            z = int(pos.Z)
        except Exception:
            self.status = "Could not read the targeted {} location.".format(skill)
            self.build_ui()
            return

        try:
            graphic = int(API.LastTargetGraphic or 0)
        except Exception:
            graphic = 0

        self.practice_locations[skill] = (x, y, z, graphic)
        self.save()
        self.status = "{} practice spot saved at {},{}.".format(skill, x, y)
        self.build_ui()

    def _tracking_button_id(self):
        for name, button_id in TRACKING_CATEGORIES:
            if name == self.tracking_category:
                return int(button_id)
        return 4

    def _tracking_short_label(self):
        labels = {
            "Animals": "A",
            "Monsters": "M",
            "NPCs": "N",
            "Players": "P",
        }
        return labels.get(self.tracking_category, "P")

    def cycle_tracking_category(self):
        names = [x[0] for x in TRACKING_CATEGORIES]
        try:
            idx = names.index(self.tracking_category)
        except Exception:
            idx = 3
        self.tracking_category = names[(idx + 1) % len(names)]
        self.save()
        self.status = "Tracking category set to {}.".format(self.tracking_category)
        self.build_ui()

    def module_info(self, skill):
        messages = {
            "Cartography": "Cartography crafting/map module is next-stage work.",
            "Cooking": "Cooking crafting/material module is next-stage work.",
        }
        self.status = messages.get(skill, "{} module is not integrated yet.".format(skill))
        self.build_ui()

    def minimize(self):
        self.minimal = True
        self.save()
        self.build_ui()

    def expand(self):
        self.minimal = False
        self.save()
        self.build_ui()

    def close(self):
        self.running = False
        try:
            self.save()
        except Exception:
            pass
        try:
            if self.ui and not self.ui.IsDisposed:
                self.ui.Dispose()
        except Exception:
            pass

    # ---------------- crafting support ----------------

    def _craft_chest(self, skill):
        return int(self.targets.get(skill, 0) or 0)

    def _ensure_resource(self, skill, graphic, desired=CRAFT_RESTOCK_AMOUNT):
        """Restock one crafting resource from the saved resource chest."""
        have = count_graphic(graphic)
        if have >= CRAFT_RESTOCK_MIN:
            return True

        chest = self._craft_chest(skill)
        if not chest:
            return False

        try:
            API.UseObject(chest)
            API.Pause(0.20)
        except Exception:
            pass

        source = find_graphic_in(graphic, chest)
        if not source:
            return False

        need = max(1, int(desired) - int(have))
        move_amount = min(item_amount(source), need)
        try:
            API.MoveItem(serial_of(source), int(API.Backpack.Serial), int(move_amount))
            API.Pause(0.35)
        except Exception:
            return False

        return count_graphic(graphic) > have

    def _ensure_craft_tool(self, skill, graphic):
        tool = first_graphic(graphic)
        if tool:
            return tool

        chest = self._craft_chest(skill)
        if not chest:
            return None

        try:
            API.UseObject(chest)
            API.Pause(0.20)
        except Exception:
            pass

        source = find_graphic_in(graphic, chest)
        if not source:
            return None

        try:
            API.MoveItem(serial_of(source), int(API.Backpack.Serial), 1)
            API.Pause(0.35)
        except Exception:
            return None

        return first_graphic(graphic)

    def _alchemy_recipe(self):
        value = skill_value("Alchemy")
        # Button IDs from the working omgArturo trainer.
        if value < 55.0:
            return ("Poison", 10)
        if value < 90.0:
            return ("Greater Poison", 17)
        return ("Deadly Poison", 24)

    def _inscription_recipe(self):
        value = skill_value("Inscription")
        # category, item button, name, mana, required resources
        if value < 30.0:
            return (8, 37, "Teleport", 11, (MANDRAKE_ROOT, BLOODMOSS))
        if value < 55.0:
            return (8, 107, "Recall", 11, (MANDRAKE_ROOT, BLOODMOSS, BLACK_PEARL))
        if value < 65.0:
            return (15, 2, "Blade Spirits", 16, (MANDRAKE_ROOT, NIGHTSHADE, BLACK_PEARL))
        if value < 85.0:
            return (15, 65, "Energy Bolt", 20, (BLACK_PEARL, NIGHTSHADE))
        if value < 94.0:
            return (22, 23, "Gate Travel", 40, (BLACK_PEARL, MANDRAKE_ROOT, SULFUROUS_ASH))
        return (22, 72, "Resurrection", 50, (BLOODMOSS, GARLIC, GINSENG))

    def _meditate_if_needed(self, mana_needed):
        try:
            mana = int(API.Player.Mana)
        except Exception:
            return True
        if mana >= int(mana_needed):
            return True
        try:
            API.UseSkill("Meditation")
            return False
        except Exception:
            return False

    def _casting_plan(self, skill):
        value = skill_value(skill)

        if skill == "Necromancy":
            # Proven ladder from J.C.S. Necromancy Trainer v1.0.
            if value >= 80.0:
                return "Vampiric Embrace", "none", 23
            if value >= 60.0:
                return "Horrific Beast", "none", 11
            if value >= 40.0:
                return "Wraith Form", "none", 17
            if value >= 20.0:
                return "Pain Spike", "self", 5
            return "Curse Weapon", "none", 7

        if skill == "Magery":
            if value >= 65.0:
                return "Invisibility", "self", 20
            if value >= 50.0:
                return "Magic Reflection", "self", 14
            if value >= 30.0:
                return "Bless", "self", 9
            return "Heal", "self", 4

        if skill == "Chivalry":
            if value >= 90.0:
                return "Holy Light", "none", 10
            if value >= 70.0:
                return "Enemy of One", "none", 20
            if value >= 50.0:
                return "Divine Fury", "none", 15
            return "Close Wounds", "self", 10

        if skill == "Spellweaving":
            if value >= 90.0:
                return "Essence of Wind", "none", 40
            if value >= 80.0:
                return "Thunderstorm", "none", 32
            if value >= 60.0:
                return "Attunement", "none", 24
            if value >= 44.0:
                return "Immolating Weapon", "none", 16
            return "Gift of Renewal", "self", 8

        if skill == "Mysticism":
            if value >= 50.0:
                return "Cleansing Winds", "self", 20
            return "Healing Stone", "none", 4

        if skill == "Bushido":
            if value >= 80.0:
                return "Evasion", "none", 10
            if value >= 60.0:
                return "Counter Attack", "none", 5
            return "Confidence", "none", 10

        return "", "none", 0

    def _cast_training_spell(self, skill):
        spell, mode, mana_needed = self._casting_plan(skill)
        if not spell:
            return False, "no casting plan"

        try:
            mana = int(API.Player.Mana or 0)
        except Exception:
            mana = 0
        if mana < int(mana_needed):
            try:
                API.UseSkill("Meditation")
            except Exception:
                pass
            return False, "meditating for mana"

        if has_target():
            return False, "target cursor busy"

        try:
            API.CastSpell(spell)
            if mode == "self":
                if API.WaitForTarget("any", TARGET_TIMEOUT):
                    API.Target(int(API.Player.Serial))
                else:
                    return False, "spell target cursor missing"
            return True, "casting {}".format(spell.lower())
        except Exception:
            cancel_owned_target()
            return False, "cast failed: {}".format(spell)

    # ---------------- training ----------------

    def _ready(self, skill):
        if skill not in AUTOMATED_SKILLS:
            return False
        if skill == "Animal Taming":
            return skill_value("Animal Taming") >= 90.0 and bool(int(self.targets.get(skill, 0) or 0))
        if skill in BARD_SKILLS:
            return self._bard_setup_ready(skill)
        if skill in TARGET_SKILLS and not int(self.targets.get(skill, 0) or 0):
            return False
        if skill == "Camping":
            return bool(first_graphic(KINDLING_GRAPHIC))
        if skill == "Lockpicking":
            return bool(first_graphic(LOCKPICK_GRAPHIC)) and bool(self.targets.get(skill, 0))
        if skill == "Tracking":
            return True
        if skill == "Herding":
            return bool(tool_by_graphics(SHEPHERDS_CROOK_GRAPHICS)) and bool(self.targets.get(skill, 0))
        if skill == "Fishing":
            return bool(tool_by_graphics(FISHING_POLE_GRAPHIC)) and self._practice_location_set(skill)
        if skill == "Mining":
            return bool(tool_by_graphics((PICKAXE_GRAPHIC, SHOVEL_GRAPHIC))) and self._practice_location_set(skill)
        if skill == "Lumberjacking":
            return bool(tool_by_graphics(HATCHET_GRAPHIC)) and self._practice_location_set(skill)
        if skill == "Alchemy":
            return bool(self.targets.get(skill, 0)) and bool(
                first_graphic(MORTAR_GRAPHIC) or find_graphic_in(MORTAR_GRAPHIC, self._craft_chest(skill))
            )
        if skill == "Inscription":
            return bool(self.targets.get(skill, 0)) and bool(
                first_graphic(SCRIBE_PEN_GRAPHIC) or find_graphic_in(SCRIBE_PEN_GRAPHIC, self._craft_chest(skill))
            )
        return True

    def _effective_enabled(self, skill):
        return bool(self.enabled.get(skill, False))

    def _substatus(self, skill):
        value = skill_value(skill)
        cap = skill_cap(skill)
        if value >= cap - 0.05:
            return "DONE | gains this trainer: {}".format(self.gain_counts.get(skill, 0))

        if skill in MODULE_SKILLS:
            return "Module reserved for dedicated training logic"

        if skill == "Alchemy":
            chest = self._craft_chest(skill)
            if not chest:
                return "Needs resource chest"
            recipe, _button = self._alchemy_recipe()
            return "{} | chest set | gains: {}".format(
                recipe, self.gain_counts.get(skill, 0)
            )

        if skill == "Inscription":
            chest = self._craft_chest(skill)
            if not chest:
                return "Needs resource chest"
            _cat, _item, recipe, _mana, _regs = self._inscription_recipe()
            return "{} | chest set | gains: {}".format(
                recipe, self.gain_counts.get(skill, 0)
            )

        if skill in ("Magery", "Necromancy", "Chivalry", "Spellweaving", "Mysticism", "Bushido"):
            spell, mode, mana = self._casting_plan(skill)
            return "{} | {} mana | gains: {}".format(
                spell, mana, self.gain_counts.get(skill, 0)
            )

        if skill in ("Meditation", "Spirit Speak", "Stealth"):
            return "Sit-still trainer | gains: {}".format(self.gain_counts.get(skill, 0))

        if skill in BARD_SKILLS:
            inst = self._bard_instrument()
            if not inst:
                return "Needs bard instruments in backpack"
            if skill == "Musicianship":
                return "Auto instrument | gains: {}".format(self.gain_counts.get(skill, 0))
            if skill == "Peacemaking":
                return "Area Peace -> SELF | also trains Music | auto instrument | gains: {}".format(self.gain_counts.get(skill, 0))
            first = int(self.targets.get(skill, 0) or 0)
            if skill == "Provocation":
                second = int(self.second_targets.get(skill, 0) or 0)
                if not (first and second):
                    return "Needs SETUP: two practice creatures"
                return "2 creatures | auto instrument | 10s cycle | gains: {}".format(self.gain_counts.get(skill, 0))
            if not first:
                return "Needs SETUP: practice creature"
            return "Creature set | auto instrument | 10s cycle | gains: {}".format(self.gain_counts.get(skill, 0))

        if skill == "Animal Taming":
            value = skill_value("Animal Taming")
            pet = int(self.targets.get(skill, 0) or 0)
            if value < 90.0:
                return "WAIT 90 | use 90+ PET to preselect mastery pet | currently {:.1f}".format(value)
            if not pet:
                return "90+ READY | click 90+ PET to select Combat Training pet"
            return "Combat Training pet 0x{:X} | also trains Lore | gains: {}".format(pet, self.gain_counts.get(skill, 0))

        if skill in TARGET_SKILLS:
            serial = int(self.targets.get(skill, 0) or 0)
            if serial:
                return "Target 0x{:X} | gains: {}".format(
                    serial, self.gain_counts.get(skill, 0)
                )
            return "Needs target: {}".format(TARGET_SKILLS[skill])

        if skill == "Camping" and not first_graphic(KINDLING_GRAPHIC):
            return "Needs kindling in backpack"

        if skill == "Tracking":
            return "{} | 10s cycle | gains: {}".format(
                self.tracking_category, self.gain_counts.get(skill, 0)
            )

        if skill == "Herding":
            crook = bool(tool_by_graphics(SHEPHERDS_CROOK_GRAPHICS))
            target = bool(self.targets.get(skill, 0))
            if not crook:
                return "Needs shepherd's crook"
            if not target:
                return "Needs animal target"
            return "Animal set | gains: {}".format(self.gain_counts.get(skill, 0))

        if skill in ("Fishing", "Mining", "Lumberjacking"):
            if not self._practice_location_set(skill):
                return "Needs nearby practice SPOT"
            if skill == "Fishing" and not tool_by_graphics(FISHING_POLE_GRAPHIC):
                return "Needs fishing pole"
            if skill == "Mining" and not tool_by_graphics((PICKAXE_GRAPHIC, SHOVEL_GRAPHIC)):
                return "Needs pickaxe/shovel"
            if skill == "Lumberjacking" and not tool_by_graphics(HATCHET_GRAPHIC):
                return "Needs hatchet"
            return "Practice spot saved | gains: {}".format(self.gain_counts.get(skill, 0))

        return "Ready | gains: {}".format(self.gain_counts.get(skill, 0))

    def _action_delay(self, skill):
        return float(ACTION_DELAYS.get(skill, DEFAULT_ACTION_DELAY))

    def _record_gain(self, skill):
        now_value = skill_value(skill)
        old_value = float(self.last_values.get(skill, now_value))
        if now_value > old_value + 0.0001:
            self.gain_counts[skill] = int(self.gain_counts.get(skill, 0)) + 1
            self.last_values[skill] = now_value
            pset("Gains_" + self._skill_key(skill), self.gain_counts[skill])
            return True
        self.last_values[skill] = now_value
        return False

    def _train_bard_skill(self, skill):
        """Run a bard skill while only feeding an instrument if the shard asks for one.

        InsaneUO may immediately present the actual skill target cursor (for
        example Peacemaking says "Whom do you wish to calm?"). In that case an
        instrument must NOT be targeted or the shard responds "You cannot calm
        that!". This mirrors the proven BardMaster behavior.
        """
        instrument = self._bard_instrument()
        first = int(self.targets.get(skill, 0) or 0)
        second = int(self.second_targets.get(skill, 0) or 0)

        if not instrument:
            return False, "no bard instruments found in backpack"
        if skill == "Discordance" and not first:
            return False, "practice creature not set"
        if skill == "Provocation" and not first:
            return False, "first Provocation creature not set"
        if skill == "Provocation" and not second:
            return False, "second Provocation creature not set"
        if has_target():
            return False, "target cursor busy"

        try:
            try:
                API.ClearJournal()            except Exception:
                pass

            API.UseSkill(skill_api_name(skill))
            if not API.WaitForTarget("any", TARGET_TIMEOUT):
                return False, "no bard target cursor"

            # Some shards/skill states explicitly ask the player to choose an
            # instrument first. Only feed an instrument when that wording is
            # actually present. Otherwise the first cursor is the skill target.
            needs_instrument = False
            for phrase in (
                "what instrument shall you play",
                "select the instrument",
                "choose an instrument",
            ):
                try:
                    if API.InJournal(phrase, True):
                        needs_instrument = True
                        break
                except Exception:
                    pass

            if needs_instrument:
                API.Target(int(instrument))
                API.Pause(0.12)
                if not API.WaitForTarget("any", TARGET_TIMEOUT):
                    return False, "no {} target cursor after instrument".format(skill.lower())

            # Area Peace: the actual Peacemaking target is the player.
            if skill == "Peacemaking":
                API.Target(int(API.Player.Serial))
            else:
                API.Target(first)
            API.Pause(0.12)

            if skill == "Provocation":
                if not API.WaitForTarget("any", TARGET_TIMEOUT):
                    return False, "no second Provocation target cursor"
                API.Target(second)

            return True, "{} attempt sent".format(skill.lower())
        except Exception:
            cancel_owned_target()
            return False, "{} attempt failed".format(skill.lower())

    def _wait_for_specific_gump(self, gump_id, timeout=3.0):
        elapsed = 0.0
        while elapsed < float(timeout) and not API.StopRequested:
            try:
                if API.HasGump(int(gump_id)):
                    return True
            except Exception:
                pass
            try:
                API.ProcessCallbacks()
            except Exception:
                pass
            API.Pause(0.05)
            elapsed += 0.05
        return False

    def _train_taming_mastery(self):
        """Train Animal Taming at 90+ with the shard's Combat Training mastery."""
        value = skill_value("Animal Taming")
        if value < 90.0:
            return False, "requires 90.0 Animal Taming before Combat Training mastery"
        pet_serial = int(self.targets.get("Animal Taming", 0) or 0)
        if not pet_serial:
            return False, "SETUP a nearby controlled pet"
        try:
            pet = API.FindMobile(pet_serial)
        except Exception:
            pet = None
        if not pet:
            return False, "saved pet is not visible/in range"
        if has_target():
            return False, "target cursor busy"
        try:
            API.CastSpell("Combat Training")
        except Exception:
            return False, "Combat Training cast failed; verify Animal Taming mastery is active"

        # Preserve the timing from the known-good standalone trainer.
        API.Pause(2.5)
        try:
            if API.HasTarget():
                API.Target(pet_serial)
            elif API.WaitForTarget("any", 1.5):
                API.Target(pet_serial)
            else:
                return False, "Combat Training did not produce a target cursor"
        except Exception:
            return False, "could not target the saved pet"

        gump_id = 0x92E576B6
        if self._wait_for_specific_gump(gump_id, 3.0):
            try:
                API.Pause(0.25)
                API.ReplyGump(0, gump_id)
            except Exception:
                try:
                    API.CloseGump(gump_id)
                except Exception:
                    pass
        else:
            return False, "mastery gump not found; verify mastery and pet eligibility"

        API.Pause(1.5)
        return True, "Combat Training used on saved pet"

    def _train_action(self, skill):
        target = int(self.targets.get(skill, 0) or 0)

        if skill == "Animal Taming":
            return self._train_taming_mastery()

        if skill in ("Arms Lore", "Begging", "Forensics", "Item ID", "Remove Trap", "Taste ID",
                     "Anatomy", "Animal Lore", "Eval Int"):
            return use_skill_target(skill, target)

        if skill in ("Discordance", "Peacemaking", "Provocation"):
            return self._train_bard_skill(skill)

        if skill in ("Magery", "Necromancy", "Chivalry", "Spellweaving", "Mysticism", "Bushido"):
            return self._cast_training_spell(skill)

        if skill in ("Meditation", "Spirit Speak"):
            if has_target():
                return False, "target cursor busy"
            try:
                API.UseSkill(skill_api_name(skill))
                return True, "used"
            except Exception:
                return False, "skill use failed"

        if skill == "Stealth":
            if has_target():
                return False, "target cursor busy"
            try:
                hidden = bool(getattr(API.Player, "IsHidden", False))
            except Exception:
                hidden = False
            try:
                if not hidden:
                    API.UseSkill("Hiding")
                    return True, "hiding first"
                API.UseSkill("Stealth")
                return True, "stealth used"
            except Exception:
                return False, "stealth failed"

        if skill == "Detect Hidden":
            if has_target():
                return False, "target cursor busy"
            try:
                API.UseSkill(skill_api_name(skill))
                if not API.WaitForTarget("any", TARGET_TIMEOUT):
                    return False, "no target cursor"
                try:
                    API.Target(int(API.Player.X), int(API.Player.Y), int(API.Player.Z))
                except Exception:
                    try:
                        API.Target(int(API.Player.Serial))
                    except Exception:
                        cancel_owned_target()
                        return False, "ground target failed"
                return True, "used"
            except Exception:
                cancel_owned_target()
                return False, "skill use failed"

        if skill == "Hiding":
            if has_target():
                return False, "target cursor busy"
            try:
                API.UseSkill("Hiding")
                return True, "used"
            except Exception:
                return False, "skill use failed"

        if skill == "Camping":
            kindling = first_graphic(KINDLING_GRAPHIC)
            if not kindling:
                return False, "out of kindling"
            try:
                API.UseObject(serial_of(kindling))
                return True, "used kindling"
            except Exception:
                return False, "kindling failed"

        if skill == "Musicianship":
            instrument_serial = self._bard_instrument()
            if not instrument_serial:
                return False, "no bard instruments found in backpack"
            try:
                API.UseObject(instrument_serial)
                return True, "played auto-detected instrument"
            except Exception:
                # Clear the cached serial so the next cycle immediately searches
                # for a replacement if this instrument just wore out.
                self.targets["Musicianship"] = 0
                return False, "instrument unavailable; searching for replacement"

        if skill == "Snooping":
            container = find_item(target)
            if not container:
                return False, "container unavailable"
            try:
                API.UseObject(target)
                return True, "snooped"
            except Exception:
                return False, "snoop failed"

        if skill == "Lockpicking":
            pick = first_graphic(LOCKPICK_GRAPHIC)
            if not pick:
                return False, "out of lockpicks"
            if not target:
                return False, "no training chest"
            if has_target():
                return False, "target cursor busy"
            try:
                API.UseObject(serial_of(pick))
                if not API.WaitForTarget("any", TARGET_TIMEOUT):
                    return False, "no lockpick target cursor"
                API.Target(target)
                return True, "lockpick used"
            except Exception:
                cancel_owned_target()
                return False, "lockpick failed"

        if skill == "Tracking":
            # Tracking opens the category gump first. If a category finds
            # trackable mobiles, the shard then opens a results gump.
            # Beta 7 closes that results gump automatically so Tracking can
            # train unattended without leaving server gumps stacked onscreen.
            try:
                # Close only a stale Tracking-related gump before starting.
                try:
                    if API.HasGump():
                        tracking_words = (
                            API.GumpContains("Animals")
                            or API.GumpContains("Monsters")
                            or API.GumpContains("Players")
                            or API.GumpContains("NPC")
                            or API.GumpContains("Track")
                        )
                        if tracking_words:
                            API.CloseGump()
                            API.Pause(0.05)
                except Exception:
                    pass

                API.UseSkill("Tracking")

                waited = 0.0
                while waited < 1.50 and not API.StopRequested:
                    try:
                        if API.HasGump():
                            break
                    except Exception:
                        pass
                    API.ProcessCallbacks()
                    API.Pause(0.05)
                    waited += 0.05

                try:
                    if not API.HasGump():
                        return False, "tracking gump did not open"
                except Exception:
                    return False, "tracking gump did not open"

                button_id = self._tracking_button_id()
                try:
                    result = API.ReplyGump(button_id)
                    if result is False:
                        return False, "tracking category reply failed"
                except Exception:
                    try:
                        API.ReplyGump(button_id)
                    except Exception:
                        return False, "tracking category reply failed"

                # Give the server a short window to open the second/result gump.
                # When no targets are found, there may be no second gump at all.
                result_wait = 0.0
                result_opened = False
                while result_wait < 0.80 and not API.StopRequested:
                    try:
                        API.ProcessCallbacks()
                    except Exception:
                        pass
                    try:
                        if API.HasGump():
                            result_opened = True
                            break
                    except Exception:
                        pass
                    API.Pause(0.05)
                    result_wait += 0.05

                if result_opened:
                    # We do not need to select a tracked creature for skill gain.
                    # Close the list immediately and leave the player's screen clean.
                    API.Pause(0.10)
                    try:
                        API.CloseGump()
                    except Exception:
                        pass
                    return True, "tracking {} - results closed".format(
                        self.tracking_category.lower()
                    )

                return True, "tracking {}".format(self.tracking_category.lower())

            except Exception:
                try:
                    # Defensive cleanup: close a Tracking gump left behind by
                    # an exception, but do not treat cleanup failure as fatal.
                    if API.HasGump():
                        API.CloseGump()
                except Exception:
                    pass
                return False, "tracking failed"

        if skill == "Herding":
            crook = tool_by_graphics(SHEPHERDS_CROOK_GRAPHICS)
            if not crook:
                return False, "no shepherd's crook"
            if not target:
                return False, "no animal target"
            if has_target():
                return False, "target cursor busy"
            try:
                API.UseObject(serial_of(crook))
                if not API.WaitForTarget("any", TARGET_TIMEOUT):
                    return False, "no herding target cursor"
                API.Target(target)
                API.Pause(0.15)
                if not API.WaitForTarget("any", TARGET_TIMEOUT):
                    return False, "no destination cursor"
                # Herd toward the player's current tile. Repeated attempts are enough
                # for training and do not require walking the animal away.
                API.Target(
                    int(API.Player.X),
                    int(API.Player.Y),
                    int(API.Player.Z)
                )
                return True, "herding"
            except Exception:
                cancel_owned_target()
                return False, "herding failed"

        if skill in ("Fishing", "Mining", "Lumberjacking"):
            try:
                x, y, z, graphic = self.practice_locations.get(
                    skill, (0, 0, 0, 0)
                )
            except Exception:
                return False, "practice spot unavailable"

            if skill == "Fishing":
                tool = tool_by_graphics(FISHING_POLE_GRAPHIC)
            elif skill == "Mining":
                tool = tool_by_graphics((PICKAXE_GRAPHIC, SHOVEL_GRAPHIC))
            else:
                tool = tool_by_graphics(HATCHET_GRAPHIC)

            if not tool:
                return False, "training tool unavailable"
            if not (int(x) or int(y)):
                return False, "no practice spot"
            if has_target():
                return False, "target cursor busy"

            try:
                # Mining on InsaneUO is safer on foot.
                if skill == "Mining":
                    try:
                        API.Dismount()
                    except Exception:
                        pass

                API.UseObject(serial_of(tool))
                if not API.WaitForTarget("any", TARGET_TIMEOUT):
                    return False, "tool target cursor missing"

                # Trees normally need the static graphic. Water / cave floor can
                # usually use the position alone; keep the recorded graphic when present.
                if int(graphic or 0):
                    try:
                        API.Target(int(x), int(y), int(z), int(graphic))
                    except Exception:
                        API.Target(int(x), int(y), int(z))
                else:
                    API.Target(int(x), int(y), int(z))

                return True, "{} practice".format(skill.lower())
            except Exception:
                cancel_owned_target()
                return False, "{} target failed".format(skill.lower())

        if skill == "Alchemy":
            chest = self._craft_chest("Alchemy")
            if not chest:
                return False, "set resource chest"

            mortar = self._ensure_craft_tool("Alchemy", MORTAR_GRAPHIC)
            if not mortar:
                return False, "no mortar/pestle"

            if not self._ensure_resource("Alchemy", NIGHTSHADE):
                return False, "need nightshade"
            if not self._ensure_resource("Alchemy", BOTTLE_GRAPHIC):
                return False, "need empty bottles"

            recipe_name, recipe_button = self._alchemy_recipe()

            try:
                # Start clean if an old crafting gump is still open.
                try:
                    if API.HasGump():
                        API.CloseGump()
                        API.Pause(0.05)
                except Exception:
                    pass

                API.UseObject(serial_of(mortar))
                if not wait_for_any_gump(1.75):
                    return False, "alchemy gump did not open"

                if not reply_current_gump(recipe_button):
                    return False, "alchemy recipe reply failed"

                API.Pause(0.20)
                return True, "making {}".format(recipe_name.lower())
            except Exception:
                return False, "alchemy craft failed"

        if skill == "Inscription":
            chest = self._craft_chest("Inscription")
            if not chest:
                return False, "set resource chest"

            pen = self._ensure_craft_tool("Inscription", SCRIBE_PEN_GRAPHIC)
            if not pen:
                return False, "no scribe pen"

            category_button, item_button, recipe_name, mana_needed, regs = self._inscription_recipe()

            if not self._ensure_resource("Inscription", BLANK_SCROLL_GRAPHIC):
                return False, "need blank scrolls"
            for reg in regs:
                if not self._ensure_resource("Inscription", reg):
                    return False, "missing reagent 0x{:04X}".format(int(reg))

            if not self._meditate_if_needed(mana_needed):
                return False, "meditating for mana"

            try:
                try:
                    if API.HasGump():
                        API.CloseGump()
                        API.Pause(0.05)
                except Exception:
                    pass

                API.UseObject(serial_of(pen))
                if not wait_for_any_gump(1.75):
                    return False, "inscription gump did not open"

                if not reply_current_gump(category_button):
                    return False, "circle reply failed"
                if not wait_for_any_gump(1.25):
                    return False, "circle page did not open"

                if not reply_current_gump(item_button):
                    return False, "scroll reply failed"

                API.Pause(0.20)
                return True, "writing {}".format(recipe_name.lower())
            except Exception:
                return False, "inscription craft failed"

        return False, "module not implemented"

    def _channels_for(self, skill):
        return set(SKILL_CHANNELS.get(skill, {"self"}))

    def _channel_available(self, skill, now, recovering_cast=False):
        channels=self._channels_for(skill)
        if recovering_cast and channels.intersection(CHANNEL_CONFLICTS.get("cast_recovery", set())):
            return False
        active={ch for ch,until in self.channel_busy_until.items() if now < float(until or 0.0)}
        for ach in active:
            if channels.intersection(CHANNEL_CONFLICTS.get(ach, set())):
                return False
        return True

    def _mark_channels_busy(self, skill, now):
        for ch in self._channels_for(skill):
            hold=float(CHANNEL_HOLD.get(ch,0.12))
            self.channel_busy_until[ch]=max(float(self.channel_busy_until.get(ch,0.0) or 0.0),now+hold)

    def _pair_selected(self, first, second):
        """True when both skills are part of the active training intent."""
        if self.build_training:
            explicit = set(self._explicit_build_skills())
            return first in explicit and second in explicit
        return bool(self._effective_enabled(first) and self._effective_enabled(second))

    def _prefer_peace_for_music(self):
        """Area Peace can train Peacemaking and Musicianship with one action."""
        if not self._pair_selected("Peacemaking", "Musicianship"):
            return False
        if self._at_goal("Peacemaking") or self._at_goal("Musicianship"):
            return False
        if self._at_training_limit("Peacemaking"):
            return False
        return bool(self._ready("Peacemaking"))

    def _prefer_taming_mastery_for_lore(self):
        """90+ Combat Training mastery can work Animal Taming and Animal Lore together."""
        if not self._pair_selected("Animal Taming", "Animal Lore"):
            return False
        if skill_value("Animal Taming") < 90.0:
            return False
        if not int(self.targets.get("Animal Taming", 0) or 0):
            return False
        # Keep using the joint mastery while either requested skill still needs
        # work. This remains useful if Taming reaches its own goal before Lore.
        if self._at_goal("Animal Taming") and self._at_goal("Animal Lore"):
            return False
        return bool(self._ready("Animal Taming"))

    def _unattended_mode(self):
        return bool(self.build_training or self.train_all or self.sit_still)

    def _target_watchdog_tick(self):
        """Recover an orphaned target cursor during unattended training.

        A legitimate trainer normally consumes its target cursor in well under
        TARGET_TIMEOUT. If a cursor survives beyond the grace period, it is
        almost certainly stale and would otherwise block casting/bard skills
        forever. Manual play is left alone unless an unattended mode is active.
        """
        if not self._unattended_mode():
            self.target_busy_since = 0.0
            return False

        if not has_target():
            self.target_busy_since = 0.0
            return False

        now = time.time()
        if self.target_busy_since <= 0.0:
            self.target_busy_since = now
            return False

        if (now - self.target_busy_since) < float(self.target_watchdog_grace):
            return False

        try:
            API.CancelTarget()
        except Exception:
            return False

        self.target_busy_since = 0.0
        self.status = "Recovered stale target cursor; training resumed."
        # Give the client a moment to clear cursor state before another action.
        self.global_action_at = max(self.global_action_at, time.time() + 0.20)
        return True

    def train_tick(self):
        if self.paused:
            return

        if self._target_watchdog_tick():
            return
        if self.build_training:
            self._sync_build_training_selection()
        candidates=[]
        peace_joint = self._prefer_peace_for_music()
        taming_joint = self._prefer_taming_mastery_for_lore()

        for skill in ALL_SKILLS:
            if skill not in AUTOMATED_SKILLS:
                continue
            if not self._effective_enabled(skill):
                # In BUILD GO, allow Animal Taming to act as the joint mastery
                # driver after Taming itself has reached goal/cap if Lore still
                # needs gains.
                if not (skill == "Animal Taming" and taming_joint):
                    continue

            # Suppress redundant single-skill attempts while a better joint
            # trainer is available.
            if skill == "Musicianship" and peace_joint:
                continue
            if skill == "Animal Lore" and taming_joint:
                continue

            if self._at_goal(skill):
                if skill == "Animal Taming" and taming_joint:
                    pass
                else:
                    self.enabled[skill] = False
                    continue

            if self._at_training_limit(skill):
                if skill == "Animal Taming" and taming_joint and not self._at_goal("Animal Lore"):
                    pass
                else:
                    continue

            if not self._ready(skill):
                continue
            candidates.append(skill)
        if not candidates: return
        now=time.time()
        if now < float(self.global_action_at or 0.0): return
        if now < float(self.cast_protect_until or 0.0): return

        recovering_cast=bool(self.last_cast_skill and now < float(self.next_action_at.get(self.last_cast_skill,0.0) or 0.0))
        ordered=[]
        # During cast recovery, first search every compatible channel. This is
        # data-driven: adding a future trainer only requires declaring channels.
        if recovering_cast:
            for s in candidates:
                if s not in CASTING_SKILLS and self._channel_available(s,now,True): ordered.append(s)
        for offset in range(len(candidates)):
            s=candidates[(self.rotation+offset)%len(candidates)]
            if s not in ordered: ordered.append(s)

        for skill in ordered:
            if now < float(self.next_action_at.get(skill,0.0) or 0.0): continue
            if not self._channel_available(skill,now,recovering_cast): continue
            before=skill_value(skill)
            ok,detail=self._train_action(skill)
            self.next_action_at[skill]=now+self._action_delay(skill)
            self.global_action_at=now+GLOBAL_ACTION_GAP
            self._mark_channels_busy(skill,now)
            try:
                idx=candidates.index(skill); self.rotation=(idx+1)%max(1,len(candidates))
            except Exception: pass
            if ok and skill in CASTING_SKILLS:
                self.last_cast_skill=skill; self.cast_protect_until=now+CAST_PROTECT_SECONDS
            if ok:
                if not has_target():
                    self.target_busy_since = 0.0
                channels="/".join(sorted(self._channels_for(skill))).upper()
                if skill == "Peacemaking" and peace_joint:
                    self.status="JOINT: Area Peace training Peace + Music [{0}]".format(channels)
                elif skill == "Animal Taming" and taming_joint:
                    self.status="JOINT: Combat Training working Taming + Lore [{0}]".format(channels)
                elif recovering_cast and skill not in CASTING_SKILLS:
                    self.status="{} [{}] during {} recovery ({:.1f}/{:.0f})".format(skill,channels,self.last_cast_skill,before,self._goal(skill))
                else:
                    self.status="{} [{}] ({:.1f}/{:.0f})".format(skill,channels,before,self._goal(skill))
            else:
                self.status="{}: {}".format(skill,detail)
                if "target cursor busy" in str(detail).lower() and self._unattended_mode():
                    if self.target_busy_since <= 0.0:
                        self.target_busy_since = time.time()
                self.next_action_at[skill]=now+max(1.5,self._action_delay(skill))
            return

    def refresh_live(self):
        now = time.time()
        if self.auto_build_locks and now >= self.next_lock_sync:
            self.apply_build_locks(silent=True)
            self.next_lock_sync = now + 2.0
        changed = False
        for skill in ALL_SKILLS:
            if self._record_gain(skill):
                changed = True

        # Full gump skill labels can be updated without rebuilding.
        for skill, label in list(self.skill_value_labels.items()):
            value = skill_value(skill)
            try:
                label.SetText("{:.1f}".format(value))
            except Exception:
                try:
                    label.Text = "{:.1f}".format(value)
                except Exception:
                    pass

        if self.status_label is not None:
            try:
                self.status_label.SetText(self.status[:90])
            except Exception:
                try:
                    self.status_label.Text = self.status[:90]
                except Exception:
                    pass

        if changed and (time.time() - self.last_save_at) > 1.0:
            self.save()
            self.last_save_at = time.time()

    def run(self):
        self.build_ui()
        try:
            API.SysMsg("{} {} loaded.".format(APP, VERSION), 68)
            API.SysMsg(
                "Automated free skills: {}. Module skills: {}.".format(
                    len(AUTOMATED_SKILLS), len(MODULE_SKILLS)
                ),
                68
            )
        except Exception:
            pass

        while self.running and not API.StopRequested:
            try:
                self.train_tick()
                self.refresh_live()

                if (time.time() - self.last_save_at) >= 5.0:
                    self.save()
                    self.last_save_at = time.time()

                try:
                    API.ProcessCallbacks()
                except Exception:
                    pass
            except Exception as exc:
                self.status = "Recovered from error: {}".format(str(exc)[:55])

            API.Pause(UPDATE_RATE)

        try:
            self.save()
        except Exception:
            pass
        try:
            if self.ui and not self.ui.IsDisposed:
                self.ui.Dispose()
        except Exception:
            pass


app = FreeSkillsMaster()
app.run()