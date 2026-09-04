"""
J.C.S. Free Skills Master - InsaneUO / TazUO LegionPy
Beta 1

Trains InsaneUO "free skills" without touching the normal 720 skill-cap budget.

Design:
- All 21 current InsaneUO free skills are visible in one dashboard.
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

APP = "J.C.S. FREE SKILLS MASTER"
VERSION = "BETA 7"
SETTINGS_FILE = "JCS_FreeSkillsMaster_Settings.json"

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

# API skill names can differ from display names.
API_SKILL_NAMES = {
    "Arms Lore": "Arms Lore",
    "Detect Hidden": "Detect Hidden",
    "Forensics": "Forensic Evaluation",
    "Item ID": "Item Identification",
    "Remove Trap": "Remove Trap",
    "Taste ID": "Taste Identification",
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
}

MODULE_SKILLS = set(FREE_SKILLS) - AUTOMATED_SKILLS

# Skills that can be trained while simply standing in place with no saved target,
# tool, resource chest, or harvesting location.
SIT_STILL_SKILLS = {
    "Detect Hidden",
    "Hiding",
    "Tracking",
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
}

TRACKING_CATEGORIES = [
    ("Animals", 1),
    ("Monsters", 2),
    ("NPCs", 3),
    ("Players", 4),
]


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
        self.sit_still = pbool("SitStill", False)
        self.minimal = pbool("Minimal", False)

        self.gump_x = pint("GumpX", 120)
        self.gump_y = pint("GumpY", 120)
        self.ui = None

        self.status = "Ready."
        self.status_label = None
        self.skill_value_labels = {}
        self.skill_state_labels = {}

        self.enabled = {}
        self.targets = {}
        self.next_action_at = {}
        self.last_values = {}
        self.gain_counts = {}

        for skill in FREE_SKILLS:
            key = self._skill_key(skill)
            self.enabled[skill] = pbool("Enabled_" + key, False)
            self.targets[skill] = pint("Target_" + key, 0)
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
        pset("SitStill", 1 if self.sit_still else 0)
        pset("Minimal", 1 if self.minimal else 0)
        pset("TrackingCategory", self.tracking_category)
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
        for skill in FREE_SKILLS:
            key = self._skill_key(skill)
            pset("Enabled_" + key, 1 if self.enabled.get(skill, False) else 0)
            pset("Target_" + key, int(self.targets.get(skill, 0) or 0))
            pset("Gains_" + key, int(self.gain_counts.get(skill, 0) or 0))
        self._remember_pos()

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
        self._button("X", 788, 4, 20, self.close, 22, "Close Free Skills Master.")

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
            tooltip="Enable all currently automatable free skills that have required setup."
        )
        self._button(
            "SIT STILL ON" if self.sit_still else "SIT STILL OFF",
            218, 38, 112, self.toggle_sit_still,
            state=self.sit_still,
            tooltip="Train only skills that need no target, tool, chest, or movement: Detect Hidden, Hiding, Tracking."
        )
        self._button(
            "REFRESH", 336, 38, 72, self.refresh_ui,
            tooltip="Refresh skill values and setup state."
        )

        automated_now = sum(1 for s in AUTOMATED_SKILLS if self._ready(s))
        self._label(
            "{} ready | {} sit-still | {} modules".format(
                automated_now, len(SIT_STILL_SKILLS), len(MODULE_SKILLS)
            ),
            422, 43, 320, C_GOLD, 11
        )

        self._panel(12, 72, 796, 39)
        self.status_label = self._label(self.status, 20, 80, 780, C_TEXT, 12)

        # Two-column grid.
        left = FREE_SKILLS[:11]
        right = FREE_SKILLS[11:]
        self._build_skill_column(left, 14, 122, 382)
        self._build_skill_column(right, 424, 122, 382)

        self._panel(12, 646, 796, 40, C_PANEL_2)
        self._label(
            "Green = training enabled   SET/SPOT = saved setup   MODULE = remaining trainer not integrated yet",
            20, 656, 780, C_MUTED, 11, "center"
        )

        API.AddGump(self.ui)
        try:
            self.ui.SetInScreen()
        except Exception:
            pass

    def _build_skill_column(self, skills, x, y, width):
        self._label("FREE SKILL", x + 4, y, 160, C_ORANGE, 11)
        self._label("SKILL / CAP", x + 166, y, 92, C_ORANGE, 11, "center")
        self._label("CONTROL", x + 264, y, 110, C_ORANGE, 11, "center")
        y += 24

        for skill in skills:
            self._panel(x, y, width, 42)

            value = skill_value(skill)
            cap = skill_cap(skill)
            done = value >= (cap - 0.05)

            self._label(skill, x + 8, y + 5, 156, C_TEXT, 12)
            value_label = self._label(
                "{:.1f} / {:.0f}".format(value, cap),
                x + 166, y + 5, 92,
                C_GREEN if done else C_GOLD,
                11, "center"
            )
            self.skill_value_labels[skill] = value_label

            if skill in MODULE_SKILLS:
                self._button(
                    "MODULE", x + 264, y + 6, 106,
                    lambda s=skill: self.module_info(s),
                    h=26,
                    tooltip="This skill is in the framework but its dedicated trainer is not integrated yet."
                )
            else:
                ready = self._ready(skill)
                active = self._effective_enabled(skill) and ready and not done
                control_text = "DONE" if done else ("ON" if active else "OFF")
                self._button(
                    control_text, x + 264, y + 6, 50,
                    lambda s=skill: self.toggle_skill(s),
                    h=26,
                    state=True if done or active else False,
                    tooltip="Toggle automatic training for {}.".format(skill)
                )

                if skill == "Tracking":
                    self._button(
                        self._tracking_short_label(),
                        x + 322, y + 6, 50,
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
                        x + 322, y + 6, 50,
                        lambda s=skill: self.set_practice_location(s),
                        h=26,
                        state=True if pos_set else None,
                        tooltip="Save the nearby {} practice tile.".format(skill)
                    )
                elif skill in TARGET_SKILLS:
                    target_set = bool(self.targets.get(skill, 0))
                    self._button(
                        "SET" if target_set else "SETUP",
                        x + 322, y + 6, 50,
                        lambda s=skill: self.set_target(s),
                        h=26,
                        state=True if target_set else None,
                        tooltip="Save {} target: {}.".format(
                            skill, TARGET_SKILLS[skill]
                        )
                    )

            sub = self._substatus(skill)
            # Keep helper text out from underneath the CONTROL buttons.
            self._label(sub, x + 8, y + 24, 250, C_MUTED, 9)

            y += 46

    def _build_minimal(self):
        width, height = 430, 82
        self._new_gump(width, height)

        self._label("FREE SKILLS", 12, 6, 142, C_TITLE, 14)
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

    # ---------------- UI callbacks ----------------

    def refresh_ui(self):
        self.status = "Skill values refreshed."
        self.build_ui()

    def toggle_pause(self):
        self.paused = not self.paused
        self.save()
        self.status = "Training paused." if self.paused else "Training resumed."
        self.build_ui()

    def toggle_sit_still(self):
        self.sit_still = not self.sit_still

        if self.sit_still:
            # Make this an exclusive convenience mode so resource/target skills
            # do not unexpectedly fire while the player is parked.
            self.train_all = False
            for skill in AUTOMATED_SKILLS:
                self.enabled[skill] = (
                    skill in SIT_STILL_SKILLS
                    and skill_value(skill) < skill_cap(skill) - 0.05
                )
        else:
            for skill in SIT_STILL_SKILLS:
                self.enabled[skill] = False

        self.save()
        self.status = "Sit Still training {}: Detect Hidden, Hiding, Tracking.".format(
            "ON" if self.sit_still else "OFF"
        )
        self.build_ui()

    def toggle_train_all(self):
        self.train_all = not self.train_all
        if self.train_all:
            self.sit_still = False

        if self.train_all:
            for skill in AUTOMATED_SKILLS:
                if self._ready(skill) and skill_value(skill) < skill_cap(skill) - 0.05:
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

        self.train_all = False
        self.sit_still = False

        if skill_value(skill) >= skill_cap(skill) - 0.05:
            self.status = "{} is already at cap.".format(skill)
            self.build_ui()
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
        serial = request_serial(
            "Free Skills Master: target {} for {}.".format(description, skill)
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

    # ---------------- training ----------------

    def _ready(self, skill):
        if skill not in AUTOMATED_SKILLS:
            return False
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

    def _train_action(self, skill):
        target = int(self.targets.get(skill, 0) or 0)

        if skill in ("Arms Lore", "Begging", "Forensics", "Item ID", "Remove Trap", "Taste ID"):
            return use_skill_target(skill, target)

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
            instrument = find_item(target)
            if not instrument:
                return False, "instrument unavailable"
            try:
                API.UseObject(target)
                return True, "played instrument"
            except Exception:
                return False, "instrument failed"

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

    def train_tick(self):
        if self.paused:
            return

        candidates = []
        for skill in FREE_SKILLS:
            if skill not in AUTOMATED_SKILLS:
                continue
            if not self._effective_enabled(skill):
                continue
            if skill_value(skill) >= skill_cap(skill) - 0.05:
                self.enabled[skill] = False
                continue
            if not self._ready(skill):
                continue
            candidates.append(skill)

        if not candidates:
            return

        now = time.time()

        # Round-robin through enabled skills so one cooldown-heavy skill cannot starve others.
        for offset in range(len(candidates)):
            idx = (self.rotation + offset) % len(candidates)
            skill = candidates[idx]

            if now < float(self.next_action_at.get(skill, 0.0) or 0.0):
                continue

            before = skill_value(skill)
            ok, detail = self._train_action(skill)
            self.next_action_at[skill] = now + self._action_delay(skill)
            self.rotation = (idx + 1) % max(1, len(candidates))

            if ok:
                self.status = "Training {} ({:.1f}/{:.0f})".format(
                    skill, before, skill_cap(skill)
                )
            else:
                self.status = "{}: {}".format(skill, detail)
                # Don't hammer a missing/bad setup.
                self.next_action_at[skill] = now + max(1.5, self._action_delay(skill))
            return

    def refresh_live(self):
        changed = False
        for skill in FREE_SKILLS:
            if self._record_gain(skill):
                changed = True

        # Full gump skill labels can be updated without rebuilding.
        for skill, label in list(self.skill_value_labels.items()):
            value = skill_value(skill)
            cap = skill_cap(skill)
            try:
                label.SetText("{:.1f} / {:.0f}".format(value, cap))
            except Exception:
                try:
                    label.Text = "{:.1f} / {:.0f}".format(value, cap)
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