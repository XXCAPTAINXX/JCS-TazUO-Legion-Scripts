"""
J.C.S. Ultimate Combat Bar for TazUO LegionPy
Version 1.6 RC14 Public Test

Combines:
- J.C.S. Sword Attack Bar combat/ability logic
- J.C.S. Super Slayer Bar target classification / slayer weapon switching
- Shield enforcement
- Auto AOE weapon switching
- Learned mob name + body/graphic mappings
- Doom-oriented body ID learning
- Per-character settings and gump position

RC14 compatibility fix:
- Replaced legacy API.Gumps.* calls with the current top-level Legion API.* gump calls.
- This is a standalone script; no RC13 companion file is required.
"""

import time
import re
import API


VERSION = "1.6-RC14-PUBLIC-TEST"

# ============================================================
# Shared configuration
# ============================================================

HOSTILE_NOTORIETIES = [
    API.Notoriety.Gray,
    API.Notoriety.Criminal,
    API.Notoriety.Enemy,
    API.Notoriety.Murderer,
]

MOBS_TO_IGNORE = []

SUMMONS_TO_IGNORE = [
    "an energy vortex",
    "a blade spirit",
    "a rising colossus",
]

ABILITY_OPTIONS = [
    ("eoo", "Enemy of One"),
    ("df", "Divine Fury"),
    ("cw", "Consecrate Weapon"),
    ("honor", "Honor"),
    ("ca", "Counter Attack"),
    ("momentum", "Momentum Strike"),
    ("lightning", "Lightning Strike"),
    ("onslaught", "Onslaught"),
    ("curse", "Curse Weapon"),
    ("bash", "Shield Bash"),
]

WEAPON_OPTIONS = [
    ("doubleaxe", "Double Axe"),
    ("longsword", "Longsword"),
    ("broadsword", "Broadsword"),
    ("bladedwhip", "Bladed Whip"),
    ("radiantscimitar", "Radiant Scimitar"),
    ("compositebow", "Composite Bow"),
    ("soulglaive", "Soul Glaive"),
]

SLAYER_PROFILES = [
    "General Single Target",
    "General AOE",
    "Arachnid",
    "Demon",
    "Dragon",
    "Elemental",
    "Poison Elemental",
    "Fey",
    "Repond",
    "Reptile",
    "Undead",
]

SLAYER_KEYWORDS = {
    "Undead": [
        "skeleton", "zombie", "lich", "mummy", "wraith", "spectre",
        "specter", "ghoul", "vampire", "bone knight", "bone mage",
        "skeletal", "revenant", "ancient lich", "shadow knight",
        "dark guardian", "darknight creeper",
    ],
    "Demon": [
        "daemon", "demon", "balron", "imp", "gargoyle",
        "succubus", "arcane daemon", "ice fiend", "chaos daemon",
        "abyssal", "abyssmal horror", "dark father",
    ],
    "Arachnid": [
        "spider", "scorpion", "terathan", "black widow",
    ],
    "Dragon": [
        "dragon", "drake", "wyrm", "wyvern", "hiryu", "swamp dragon",
    ],
    "Reptile": [
        "serpent", "snake", "lizardman", "lizard man", "ophidian",
    ],
    "Poison Elemental": [
        "poison elemental",
    ],
    "Elemental": [
        "elemental", "golem", "vortex",
    ],
    "Fey": [
        "pixie", "satyr", "centaur", "unicorn", "kirin",
        "ki-rin", "wisp", "dryad", "silvani",
    ],
    "Repond": [
        "orc", "ogre", "troll", "cyclops", "ettin",
        "titan", "ratman", "rat man", "goblin",
        "minotaur", "human",
    ],
}

KNOWN_MOBS = {
    "poison elemental": "Poison Elemental",
    "dark guardian": "Undead",
    "darknight creeper": "Undead",
    "dark knight creeper": "Undead",
    "shadow knight": "Undead",
    "impaler": "Demon",
    "abyssmal horror": "Demon",
    "abyssal horror": "Demon",
    "dark father": "Demon",
    "flesh renderer": "General Single Target",
    "fleshrenderer": "General Single Target",
}

DEFAULTS = {
    "auto_weapon": True,
    "auto_slayer": True,
    "auto_aoe": True,
    "eoo": False,
    "df": False,
    "cw": True,
    "honor": True,
    "ca": False,
    "momentum": False,
    "lightning": False,
    "onslaught": True,
    "curse": False,
    "bash": False,
}

AUTO_AOE_ENTER_COUNT = 3
AUTO_AOE_EXIT_COUNT = 1
AUTO_AOE_RANGE = 2

GOLD_GRAPHIC = 0x0EED
GOLD_MAX_STACK = 60000

EQUIPMENT_LAYERS = [
    "Head", "Neck", "Earrings",
    "Shirt", "Pants", "Shoes",
    "Arms", "Gloves", "Ring", "Bracelet",
    "Waist", "InnerTorso", "MiddleTorso", "OuterTorso",
    "Cloak", "Talisman",
    "OneHanded", "TwoHanded",
]


# ============================================================
# Main class
# ============================================================

class UltimateCombatBar:
    def __init__(self):
        self.ui = None
        self.running = True
        self.paused = False
        self.minimized = False
        self.setup_mode = False

        self.settings = {}
        self.weapon_type = "bladedwhip"

        self.current_enemy = None
        self.current_enemy_serial = 0
        self.current_enemy_name = "None"
        self.current_enemy_graphic = 0

        self.eoo_enemy_key = None

        self.detected_profile = "General Single Target"
        self.classification_source = "Fallback"
        self.active_profile = "None"

        self.manual_aoe = False
        self.auto_aoe_active = False

        self.next_actions = {}
        self.next_weapon_scan = 0.0
        self.next_position_save = 0.0
        self.next_shield_check = 0.0
        self.next_auto_aoe_check = 0.0

        self.full_x = self._load_int("JCS_UCB_FullX", 100)
        self.full_y = self._load_int("JCS_UCB_FullY", 100)
        self.mini_x = self._load_int("JCS_UCB_MiniX", 100)
        self.mini_y = self._load_int("JCS_UCB_MiniY", 100)

        self.weapon_bag = self._load_int("JCS_UCB_WeaponBag", 0)
        self.shield_serial = self._load_int("JCS_UCB_Shield", 0)
        self.send_bag_serial = self._load_int("JCS_UCB_SendBag", 0)
        self.durability_threshold = self._load_int("JCS_UCB_DuraWarnPct", 20)
        self.durability_threshold = max(5, min(95, self.durability_threshold))

        self.low_durability = []
        self.next_durability_check = 0.0
        self.next_durability_warning = 0.0

        self.send_bag_charges = None
        self.next_send_bag_check = 0.0

        self.enchanted_apple_serial = 0
        self.enchanted_apple_graphic = 0
        self.enchanted_apple_count = 0
        self.next_apple_check = 0.0

        self.slayer_weapons = {}
        self.slayer_weapon_types = {}
        for profile in SLAYER_PROFILES:
            key = "JCS_UCB_Slayer_" + profile.replace(" ", "_")
            self.slayer_weapons[profile] = self._load_int(key, 0)

            type_key = "JCS_UCB_SlayerType_" + profile.replace(" ", "_")
            self.slayer_weapon_types[profile] = self._load(type_key, "")

        self._load_settings()

    # ========================================================
    # Persistence
    # ========================================================

    def _load(self, name, default):
        try:
            return API.GetPersistentVar(name, str(default), API.PersistentVar.Char)
        except Exception:
            return str(default)

    def _load_int(self, name, default):
        try:
            return int(self._load(name, default))
        except Exception:
            return default

    def _save_int(self, name, value):
        try:
            API.SavePersistentVar(name, str(int(value)), API.PersistentVar.Char)
        except Exception:
            pass

    def _load_settings(self):
        for key, default in DEFAULTS.items():
            raw = self._load("JCS_UCB_" + key, "1" if default else "0")
            self.settings[key] = str(raw) == "1"

        value = self._load("JCS_UCB_WeaponType", "bladedwhip")
        valid = [entry[0] for entry in WEAPON_OPTIONS]
        self.weapon_type = value if value in valid else "bladedwhip"

    def _save_settings(self):
        for key in DEFAULTS:
            try:
                API.SavePersistentVar(
                    "JCS_UCB_" + key,
                    "1" if self.settings[key] else "0",
                    API.PersistentVar.Char,
                )
            except Exception:
                pass

        try:
            API.SavePersistentVar(
                "JCS_UCB_WeaponType",
                self.weapon_type,
                API.PersistentVar.Char,
            )
        except Exception:
            pass

    def _remember_position(self):
        if not self.ui or self.ui.IsDisposed:
            return

        try:
            x, y = int(self.ui.GetX()), int(self.ui.GetY())
        except Exception:
            return

        if self.minimized:
            self.mini_x, self.mini_y = x, y
            self._save_int("JCS_UCB_MiniX", x)
            self._save_int("JCS_UCB_MiniY", y)
        else:
            self.full_x, self.full_y = x, y
            self._save_int("JCS_UCB_FullX", x)
            self._save_int("JCS_UCB_FullY", y)

    # ========================================================
    # Learning
    # ========================================================

    def _mob_key(self, name):
        cleaned = "".join(ch if ch.isalnum() else "_" for ch in str(name or "").lower())
        return "JCS_UCB_Mob_" + cleaned

    def _graphic_key(self, graphic):
        return "JCS_UCB_Graphic_{:04X}".format(int(graphic or 0))

    def _load_learned_name(self, name):
        try:
            value = API.GetPersistentVar(
                self._mob_key(name),
                "",
                API.PersistentVar.Char
            )
            return value if value in SLAYER_PROFILES else None
        except Exception:
            return None

    def _load_learned_graphic(self, graphic):
        if not graphic:
            return None
        try:
            value = API.GetPersistentVar(
                self._graphic_key(graphic),
                "",
                API.PersistentVar.Char
            )
            return value if value in SLAYER_PROFILES else None
        except Exception:
            return None

    def _save_learning(self, name, graphic, profile):
        if profile not in SLAYER_PROFILES:
            return

        try:
            if name:
                API.SavePersistentVar(
                    self._mob_key(name),
                    profile,
                    API.PersistentVar.Char
                )
            if graphic:
                API.SavePersistentVar(
                    self._graphic_key(graphic),
                    profile,
                    API.PersistentVar.Char
                )
        except Exception:
            pass

    def _clear_current_learning(self):
        if not self.current_enemy_name and not self.current_enemy_graphic:
            return

        try:
            if self.current_enemy_name:
                API.RemovePersistentVar(
                    self._mob_key(self.current_enemy_name),
                    API.PersistentVar.Char
                )
        except Exception:
            pass

        try:
            if self.current_enemy_graphic:
                API.RemovePersistentVar(
                    self._graphic_key(self.current_enemy_graphic),
                    API.PersistentVar.Char
                )
        except Exception:
            pass

        self._classify_current_enemy()
        API.SysMsg("Current mob learning cleared.", 68)

    # ========================================================
    # UI helpers
    # ========================================================

    def _label(self, text, x, y, width, color="#FFFFFF", size=12, align="left"):
        label = API.CreateGumpTTFLabel(text, size, color, "", align, width, False)
        label.SetRect(x, y, width, 20)
        self.ui.Add(label)

    def _button(self, text, x, y, width, callback, height=23):
        button = API.CreateSimpleButton(text, width, height)
        button.SetPos(x, y)
        self.ui.Add(button)
        API.AddControlOnClick(button, callback)

    def _background(self, width, height):
        bg = API.CreateGumpColorBox(0.78, "#17120D")
        bg.SetRect(0, 0, width, height)
        self.ui.Add(bg)

    def _item_icon_button(self, graphic, x, y, width, height, callback):
        """Add clickable item art to the custom gump."""
        try:
            pic = API.CreateGumpItemPic(int(graphic), int(width), int(height))
        except Exception:
            return None

        pic.SetPos(x, y)
        self.ui.Add(pic)

        try:
            API.AddControlOnClick(pic, callback)
        except Exception:
            return None

        return pic

    def build_ui(self):
        old_ui = self.ui

        if old_ui:
            try:
                if not old_ui.IsDisposed:
                    self._remember_position()
            except Exception:
                pass

            try:
                old_ui.Dispose()
            except Exception:
                pass

        self.ui = None

        self.ui = API.CreateGump(True, True, True)
        API.AddGump(self.ui)

        if self.minimized:
            self._build_minimized()
        else:
            self._build_full()

    def refresh_combat_ui(self):
        if self.setup_mode:
            return
        self.build_ui()

    def _build_minimized(self):
        width, height = 470, 42
        self.ui.SetRect(self.mini_x, self.mini_y, width, height)
        self._background(width, height)

        state = "PAUSED" if self.paused else "RUNNING"
        state_color = "#FFD166" if self.paused else "#72E39A"

        self._label("J.C.S. Ultimate Combat", 8, 10, 132, "#E7A65B", 10)
        self._label(state, 138, 10, 48, state_color, 9, "center")

        mode = "AOE" if self.manual_aoe or self.auto_aoe_active else self.detected_profile
        self._label(mode[:12], 188, 10, 62, "#E8EAF0", 9, "center")

        armor_graphic = self._lowest_durability_graphic()
        if armor_graphic:
            control = self._item_icon_button(
                armor_graphic, 254, 5, 30, 30,
                lambda: self.check_durability(True)
            )
            if control is None:
                self._button("Dura", 252, 7, 40, lambda: self.check_durability(True), 28)
        else:
            self._button("Dura", 252, 7, 40, lambda: self.check_durability(True), 28)

        self._refresh_enchanted_apples(False)
        if self.enchanted_apple_graphic:
            self._item_icon_button(
                self.enchanted_apple_graphic, 296, 5, 28, 28,
                self.use_enchanted_apple
            )
            self._label(
                str(self.enchanted_apple_count),
                321, 9, 24, "#FFFFFF", 12, "center"
            )
        else:
            self._button("A", 296, 7, 28, self.use_enchanted_apple, 28)
            self._label("0", 321, 9, 24, "#FFFFFF", 12, "center")

        bag_graphic = 0
        if self.send_bag_serial:
            bag_item = self._find_item(self.send_bag_serial)
            if bag_item:
                try:
                    bag_graphic = int(bag_item.Graphic)
                except Exception:
                    bag_graphic = 0

        if bag_graphic:
            self._item_icon_button(bag_graphic, 348, 5, 28, 28, self.send_gold)
            charges = self._get_send_bag_charges(False)
            charge_text = "?" if charges is None else str(charges)
            self._label(charge_text, 373, 9, 25, "#FFD166", 12, "center")
        else:
            self._button("$", 348, 7, 28, self.send_gold, 28)
            self._label("?", 373, 9, 25, "#FFD166", 12, "center")

        self._button("Open", 400, 7, 32, self.restore, 28)
        self._button("Stop", 435, 7, 32, self.stop, 28)

    def _build_full(self):
        width = 480 if not self.setup_mode else 500
        height = 275 if not self.setup_mode else 812

        self.ui.SetRect(self.full_x, self.full_y, width, height)
        self._background(width, height)

        self._label("J.C.S. ULTIMATE COMBAT BAR", 0, 8, width, "#E7A65B", 16, "center")

        self._button("Pause" if not self.paused else "Resume", 10, 34, 48, self.toggle_pause)
        self._button("AOE ON" if self.manual_aoe else "AOE", 63, 34, 45, self.toggle_manual_aoe)
        self._button("Target", 113, 34, 48, self.target_enemy)

        gold_text = "Bank Gold"
        if self.send_bag_serial:
            charges = self._get_send_bag_charges(False)
            gold_text = "Bank Gold [%s]" % ("?" if charges is None else str(charges))
        self._button(gold_text, 166, 34, 96, self.send_gold)

        apple_count = self._refresh_enchanted_apples(False)
        apple_text = "Apple [%d]" % apple_count
        self._button(apple_text, 267, 34, 65, self.use_enchanted_apple)

        self._button("Setup", 337, 34, 48, self.toggle_setup)
        self._button("Min", 390, 34, 36, self.minimize)
        self._button("Stop", 431, 34, 38, self.stop)

        self._label("Target", 12, 70, 70, "#E7A65B")
        self._label(self.current_enemy_name[:28], 90, 70, 210, "#E8EAF0")

        self._label("Detected", 12, 91, 70, "#E7A65B")
        self._label(self.detected_profile, 90, 91, 160, "#E8EAF0")
        self._label(self.classification_source, 255, 91, 160, "#72E39A", 10, "right")

        self._label("Weapon", 12, 112, 70, "#E7A65B")
        self._label(self.active_profile, 90, 112, 240, "#E8EAF0")

        mode = "Manual AOE" if self.manual_aoe else "Auto AOE" if self.auto_aoe_active else "Auto Slayer"
        self._label("Mode", 12, 133, 70, "#E7A65B")
        self._label(mode, 90, 133, 160, "#72E39A")

        shield_state = "Not Set"
        shield_color = "#949CAA"
        if self.shield_serial:
            shield_state = "Equipped" if self._shield_equipped() else "Missing"
            shield_color = "#72E39A" if self._shield_equipped() else "#FF7A7A"
        self._label("Shield", 12, 154, 70, "#E7A65B")
        self._label(shield_state, 90, 154, 150, shield_color)

        nearby = len(self.enemies(AUTO_AOE_RANGE))
        self._label("Near", 255, 133, 44, "#E7A65B")
        self._label(str(nearby), 302, 133, 30, "#E8EAF0")

        body = "0x{:04X}".format(self.current_enemy_graphic) if self.current_enemy_graphic else "----"
        self._label("Body", 255, 154, 44, "#E7A65B")
        self._label(body, 302, 154, 90, "#E8EAF0")

        dura_text = "OK"
        dura_color = "#72E39A"
        if self.low_durability:
            dura_text = "LOW x%d" % len(self.low_durability)
            dura_color = "#FF7A7A"
        self._label("Dura", 255, 175, 44, "#E7A65B")
        self._label("%s  <%d%%" % (dura_text, self.durability_threshold),
                    302, 175, 110, dura_color, 10)

        state = "PAUSED" if self.paused else "ACTIVE"
        state_color = "#FFD166" if self.paused else "#72E39A"
        self._label(state, 12, 205, 400, state_color, 11, "center")

        if not self.setup_mode:
            self._label("Setup: weapons, shield, gold bag, durability, abilities, and learning.",
                        12, 232, 405, "#B6B0A7", 9, "center")
            return

        self._label("SETUP", 12, 234, 100, "#E7A65B", 14)
        self._label("v1.6 RC14 PUBLIC TEST", 305, 236, 180, "#B6B0A7", 9, "right")
        self._label("Basher / Shield Bash support is BETA - Parry Mastery testers wanted.",
                    12, 254, 474, "#FFD166", 9, "center")

        self._button("Weapon Bag", 12, 278, 110, self.set_weapon_bag)
        self._button("Shield", 128, 278, 82, self.set_shield)

        auto_slayer_text = "Slayer Auto: ON" if self.settings["auto_slayer"] else "Slayer Auto: OFF"
        auto_aoe_text = "Auto AOE: ON" if self.settings["auto_aoe"] else "Auto AOE: OFF"
        self._button(auto_slayer_text, 216, 278, 132, self.toggle_auto_slayer)
        self._button(auto_aoe_text, 354, 278, 132, self.toggle_auto_aoe)

        self._button("Set Send Bag", 12, 308, 110, self.set_send_bag)

        setup_charges = self._get_send_bag_charges(False) if self.send_bag_serial else None
        setup_send_text = "Send Gold"
        if self.send_bag_serial:
            setup_send_text = "Send (%s)" % ("?" if setup_charges is None else str(setup_charges))
        self._button(setup_send_text, 128, 308, 82, self.send_gold)

        self._label("Durability Warning", 216, 304, 135, "#E7A65B", 10)
        self._button("Warn -", 216, 324, 62, lambda: self.adjust_durability(-5))
        self._button("%d%%" % self.durability_threshold, 284, 324, 58,
                     lambda: self.check_durability(True))
        self._button("Warn +", 348, 324, 62, lambda: self.adjust_durability(5))
        self._button("Check Now", 416, 324, 72, lambda: self.check_durability(True))

        self._label("Weapon Assignments", 12, 360, 180, "#E7A65B", 12)

        for index, profile in enumerate(SLAYER_PROFILES):
            col = index % 3
            row = index // 3
            x = 12 + col * 160
            y = 382 + row * 29
            if profile == "General Single Target":
                short = "Single Target"
            elif profile == "General AOE":
                short = "General AOE"
            elif profile == "Poison Elemental":
                short = "Poison Elem"
            else:
                short = profile
            marker = "* " if self.slayer_weapons.get(profile, 0) else ""
            self._button(marker + short, x, y, 152,
                         lambda p=profile: self.assign_slayer_weapon(p), 24)

        self._label("Combat Options", 12, 504, 150, "#E7A65B", 12)

        for index, (key, name) in enumerate(ABILITY_OPTIONS):
            col = index % 3
            row = index // 3
            x = 12 + col * 160
            y = 526 + row * 26
            marker = "ON " if self.settings[key] else "OFF "

            display_name = name
            if key == "eoo":
                display_name = "Enemy of One"
            elif key == "df":
                display_name = "Divine Fury"
            elif key == "cw":
                display_name = "Consecrate"
            elif key == "ca":
                display_name = "Counter Attack"
            elif key == "momentum":
                display_name = "Momentum"
            elif key == "lightning":
                display_name = "Lightning Strike"
            elif key == "curse":
                display_name = "Curse Weapon"
            elif key == "bash":
                display_name = "Shield Bash BETA"

            self._button(marker + display_name, x, y, 152,
                         lambda k=key: self.toggle_setting(k), 22)

        self._label("Teach Target Slayer Type", 12, 634, 190, "#E7A65B", 11)
        self._button("Target Mob", 300, 630, 90, self.target_enemy, 22)
        self._label("1. Target a monster   2. Choose the slayer type below",
                    12, 656, 470, "#E8EAF0", 11)

        learn_profiles = [
            "General Single Target", "Arachnid", "Demon",
            "Dragon", "Elemental", "Poison Elemental",
            "Fey", "Repond", "Reptile", "Undead"
        ]
        for index, profile in enumerate(learn_profiles):
            x = 12 + (index % 3) * 160
            y = 676 + (index // 3) * 23
            if profile == "General Single Target":
                short = "Single Target"
            elif profile == "General AOE":
                short = "General AOE"
            elif profile == "Poison Elemental":
                short = "Poison Elem"
            else:
                short = profile
            self._button(short, x, y, 152,
                         lambda p=profile: self.learn_current_mob(p), 20)

        self._button("Forget Learned Target", 12, 768, 180,
                     self._clear_current_learning, 20)

    # ========================================================
    # UI callbacks
    # ========================================================

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.current_enemy = None
            self.current_enemy_serial = 0
            self._clear_weapon_abilities()
        self.build_ui()

    def toggle_manual_aoe(self):
        self.manual_aoe = not self.manual_aoe
        if self.manual_aoe:
            self.auto_aoe_active = False
            self._equip_profile("General AOE")
        else:
            self._apply_combat_weapon()
        self.build_ui()

    def toggle_setup(self):
        self.setup_mode = not self.setup_mode
        self.build_ui()

    def toggle_auto_slayer(self):
        self.settings["auto_slayer"] = not self.settings["auto_slayer"]
        self._save_settings()
        self.build_ui()

    def toggle_auto_aoe(self):
        self.settings["auto_aoe"] = not self.settings["auto_aoe"]
        if not self.settings["auto_aoe"]:
            self.auto_aoe_active = False
        self._save_settings()
        self.build_ui()

    def toggle_setting(self, key):
        self.settings[key] = not self.settings[key]
        if key == "eoo" and not self.settings[key]:
            self.eoo_enemy_key = None
        self._save_settings()
        self.build_ui()

    def minimize(self):
        self._remember_position()
        self.minimized = True
        self.build_ui()

    def restore(self):
        self._remember_position()
        self.minimized = False
        self.build_ui()

    def stop(self):
        self._clear_weapon_abilities()
        self.running = False

    # ========================================================
    # Setup actions
    # ========================================================

    def set_weapon_bag(self):
        API.SysMsg("Target the Slayer weapon bag.", 68)
        target = API.RequestTarget()
        serial = self._serial_of(target)
        if not serial:
            return
        self.weapon_bag = serial
        self._save_int("JCS_UCB_WeaponBag", serial)
        API.SysMsg("Weapon bag saved.", 68)
        self.build_ui()

    def set_shield(self):
        API.SysMsg("Target your shield.", 68)
        target = API.RequestTarget()
        serial = self._serial_of(target)
        if not serial:
            return
        self.shield_serial = serial
        self._save_int("JCS_UCB_Shield", serial)
        self._ensure_shield()
        API.SysMsg("Shield saved.", 68)
        self.build_ui()

    def _get_send_bag_charges(self, force=False):
        if not self.send_bag_serial:
            self.send_bag_charges = None
            return None

        now = time.time()
        if not force and now < self.next_send_bag_check:
            return self.send_bag_charges

        self.next_send_bag_check = now + 5.0

        if not self._find_item(self.send_bag_serial):
            self.send_bag_charges = None
            return None

        try:
            props = API.ItemNameAndProps(self.send_bag_serial, True, 2) or ""
        except Exception:
            props = ""

        value = None
        for line in str(props).replace("\r", "").split("\n"):
            cleaned = line.strip()
            lower = cleaned.lower()
            if "charge" not in lower:
                continue

            match = re.search(r"charges?\s*[:\-]?\s*(\d+)", lower)
            if not match:
                match = re.search(r"(\d+)\s*charges?", lower)

            if match:
                try:
                    value = int(match.group(1))
                    break
                except Exception:
                    pass

        self.send_bag_charges = value
        return value

    def set_send_bag(self):
        API.SysMsg("Target your Bag of Sending.", 68)
        target = API.RequestTarget()
        serial = self._serial_of(target)
        if not serial:
            return
        self.send_bag_serial = serial
        self._save_int("JCS_UCB_SendBag", serial)
        charges = self._get_send_bag_charges(True)
        if charges is None:
            API.SysMsg("Bag of Sending saved. Charges could not be read.", 68)
        else:
            API.SysMsg("Bag of Sending saved with %d charge(s)." % charges, 68)
        self.build_ui()

    def adjust_durability(self, amount):
        self.durability_threshold = max(
            5, min(95, int(self.durability_threshold) + int(amount))
        )
        self._save_int("JCS_UCB_DuraWarnPct", self.durability_threshold)
        API.SysMsg(
            "Durability warning set to %d%%." % self.durability_threshold, 68
        )
        self.check_durability(True)
        self.build_ui()

    def _detect_assigned_weapon_type(self, serial):
        item = self._find_item(serial)
        if not item:
            return ""

        try:
            name = str(item.Name or "").strip().lower()
        except Exception:
            name = ""

        if "whip" in name:
            return "bladedwhip"
        if "broadsword" in name:
            return "broadsword"
        if "double axe" in name or "doubleaxe" in name:
            return "doubleaxe"
        if "radiant scimitar" in name:
            return "radiantscimitar"
        if "longsword" in name:
            return "longsword"
        if "composite bow" in name:
            return "compositebow"
        if "soul glaive" in name:
            return "soulglaive"
        return ""

    def assign_slayer_weapon(self, profile):
        API.SysMsg("Target weapon for " + profile + ".", 68)
        target = API.RequestTarget()
        serial = self._serial_of(target)
        if not serial:
            return

        self.slayer_weapons[profile] = serial
        key = "JCS_UCB_Slayer_" + profile.replace(" ", "_")
        self._save_int(key, serial)

        weapon_type = self._detect_assigned_weapon_type(serial)
        self.slayer_weapon_types[profile] = weapon_type

        try:
            API.SavePersistentVar(
                "JCS_UCB_SlayerType_" + profile.replace(" ", "_"),
                weapon_type,
                API.PersistentVar.Char
            )
        except Exception:
            pass

        if weapon_type == "bladedwhip":
            API.SysMsg(profile + " whip saved (AOE-capable).", 68)
        elif weapon_type == "broadsword":
            API.SysMsg(profile + " broadsword saved.", 68)
        else:
            API.SysMsg(profile + " weapon saved.", 68)

        self.build_ui()

    def learn_current_mob(self, profile):
        if not self.current_enemy_serial:
            API.SysMsg("Click Target Mob first, then choose a slayer type.", 33)
            return

        self._save_learning(
            self.current_enemy_name,
            self.current_enemy_graphic,
            profile
        )

        self.detected_profile = profile
        self.classification_source = "Learned"
        API.SysMsg(
            "Learned {} = {}.".format(self.current_enemy_name, profile),
            68
        )
        self._apply_combat_weapon()
        self.build_ui()

    def target_enemy(self):
        try:
            if API.HasTarget():
                API.CancelTarget()
        except Exception:
            pass

        API.SysMsg("Target enemy.", 68)
        target = API.RequestTarget()
        serial = self._serial_of(target)
        mob = self._find_mobile(serial)
        if not mob:
            return

        self._set_current_enemy(mob)
        self._apply_combat_weapon()
        self.build_ui()

    # ========================================================
    # Core helpers
    # ========================================================

    def _serial_of(self, value):
        if not value:
            return 0
        try:
            return int(value.Serial)
        except Exception:
            pass
        try:
            return int(value)
        except Exception:
            return 0

    def _find_item(self, serial):
        if not serial:
            return None
        try:
            return API.FindItem(serial)
        except Exception:
            return None

    def _find_mobile(self, serial):
        if not serial:
            return None
        try:
            return API.FindMobile(serial)
        except Exception:
            return None

    def _valid_enemy(self, mobile):
        if not mobile:
            return False

        try:
            if mobile.IsDead:
                return False
        except Exception:
            pass

        try:
            if API.IsFriend(mobile.Serial):
                return False
        except Exception:
            pass

        name = str(mobile.Name or "").strip().lower()

        if name in [entry.lower() for entry in MOBS_TO_IGNORE]:
            return False

        if name in [entry.lower() for entry in SUMMONS_TO_IGNORE]:
            return False

        return True

    def enemies(self, distance):
        try:
            mobiles = API.NearestMobiles(HOSTILE_NOTORIETIES, distance)
        except Exception:
            return []

        if not mobiles:
            return []

        return [m for m in mobiles if self._valid_enemy(m)]

    def _set_current_enemy(self, enemy):
        if not enemy:
            self.current_enemy = None
            self.current_enemy_serial = 0
            self.current_enemy_name = "None"
            self.current_enemy_graphic = 0
            self.detected_profile = "General Single Target"
            self.classification_source = "Fallback"
            return

        self.current_enemy = enemy
        self.current_enemy_serial = int(enemy.Serial)
        self.current_enemy_name = str(enemy.Name or "Unknown")

        try:
            self.current_enemy_graphic = int(enemy.Graphic)
        except Exception:
            self.current_enemy_graphic = 0

        self._classify_current_enemy()

    def _classify_current_enemy(self):
        name = str(self.current_enemy_name or "").strip().lower()
        graphic = self.current_enemy_graphic

        learned_graphic = self._load_learned_graphic(graphic)
        if learned_graphic:
            self.detected_profile = learned_graphic
            self.classification_source = "Learned Body"
            return

        learned_name = self._load_learned_name(name)
        if learned_name:
            self.detected_profile = learned_name
            self.classification_source = "Learned Name"
            return

        known = KNOWN_MOBS.get(name)
        if known:
            self.detected_profile = known
            self.classification_source = "Known"
            return

        for profile in (
            "Poison Elemental", "Dragon",
            "Undead", "Demon", "Arachnid", "Reptile",
            "Elemental", "Fey", "Repond",
        ):
            for keyword in SLAYER_KEYWORDS.get(profile, []):
                if keyword in name:
                    self.detected_profile = profile
                    self.classification_source = "Keyword"
                    return

        self.detected_profile = "General Single Target"
        self.classification_source = "Fallback"

    # ========================================================
    # Enchanted Apple
    # ========================================================

    def _refresh_enchanted_apples(self, force=False):
        now = time.time()
        if not force and now < self.next_apple_check:
            return self.enchanted_apple_count

        self.next_apple_check = now + 3.0
        total = 0
        first_serial = 0
        first_graphic = 0

        try:
            items = API.ItemsInContainer(API.Backpack, True)
        except Exception:
            items = []

        for item in list(items or []):
            try:
                name = str(item.Name or "").strip().lower()
            except Exception:
                name = ""

            if "enchanted apple" not in name:
                serial = self._serial_of(item)
                try:
                    props = API.ItemNameAndProps(serial, False, 1) or ""
                except Exception:
                    props = ""
                name = str(props).replace("\r", "").split("\n")[0].strip().lower()

            if "enchanted apple" not in name:
                continue

            try:
                amount = int(item.Amount or 1)
            except Exception:
                amount = 1

            total += max(1, amount)

            if not first_serial:
                first_serial = self._serial_of(item)
                try:
                    first_graphic = int(item.Graphic or 0)
                except Exception:
                    first_graphic = 0

        self.enchanted_apple_serial = first_serial
        self.enchanted_apple_graphic = first_graphic
        self.enchanted_apple_count = total
        return total

    def use_enchanted_apple(self):
        count = self._refresh_enchanted_apples(True)
        if count <= 0 or not self.enchanted_apple_serial:
            API.SysMsg("No Enchanted Apples found in your backpack.", 33)
            return

        try:
            API.UseObject(self.enchanted_apple_serial)
            API.Pause(0.35)
        except Exception:
            API.SysMsg("Could not use Enchanted Apple.", 33)
            return

        self._refresh_enchanted_apples(True)
        self.refresh_combat_ui()

    # ========================================================
    # Durability + Bank Gold utilities
    # ========================================================

    def _equipped_items(self):
        found = []
        seen = set()
        for layer in EQUIPMENT_LAYERS:
            try:
                item = API.FindLayer(layer)
            except Exception:
                item = None
            if not item:
                continue
            serial = self._serial_of(item)
            if serial and serial not in seen:
                seen.add(serial)
                found.append(item)
        return found

    def _item_durability(self, item):
        serial = self._serial_of(item)
        if not serial:
            return None

        try:
            props = API.ItemNameAndProps(serial, False, 1) or ""
        except Exception:
            props = ""

        if not props:
            try:
                props = API.ItemNameAndProps(serial, True, 1) or ""
            except Exception:
                props = ""

        for line in str(props).replace("\r", "").split("\n"):
            if "durability" not in line.lower():
                continue
            match = re.search(r"(\d+)\s*/\s*(\d+)", line)
            if not match:
                continue
            current = int(match.group(1))
            maximum = int(match.group(2))
            if maximum <= 0:
                return None
            return current, maximum

        return None

    def _lowest_durability_graphic(self):
        worst = None

        for item in self._equipped_items():
            dura = self._item_durability(item)
            if not dura:
                continue

            current, maximum = dura
            if maximum <= 0:
                continue

            percent = 100.0 * current / maximum

            try:
                graphic = int(item.Graphic or 0)
            except Exception:
                graphic = 0

            if not graphic:
                continue

            if worst is None or percent < worst[0]:
                worst = (percent, graphic)

        return worst[1] if worst else 0

    def check_durability(self, force_message=False):
        low = []
        checked = []

        for item in self._equipped_items():
            dura = self._item_durability(item)
            if not dura:
                continue

            current, maximum = dura
            percent = (100.0 * current / maximum) if maximum else 100.0

            try:
                name = str(item.Name or "Gear")
            except Exception:
                name = "Gear"

            entry = (
                self._serial_of(item),
                name,
                current,
                maximum,
                percent
            )
            checked.append(entry)

            if percent <= self.durability_threshold:
                low.append(entry)

        old_serials = set(entry[0] for entry in self.low_durability)
        new_serials = set(entry[0] for entry in low)
        newly_low = new_serials - old_serials
        self.low_durability = low

        if force_message:
            if checked:
                worst_all = min(checked, key=lambda entry: entry[4])
                color = 33 if worst_all[4] <= self.durability_threshold else 68
                API.SysMsg(
                    "Lowest durability: {} - {}/{} ({:.0f}%).".format(
                        worst_all[1],
                        worst_all[2],
                        worst_all[3],
                        worst_all[4]
                    ),
                    color
                )
                if low:
                    API.SysMsg(
                        "%d equipped item(s) are at or below the %d%% warning level." %
                        (len(low), self.durability_threshold),
                        33
                    )
                else:
                    API.SysMsg(
                        "All checked gear is above the %d%% warning level." %
                        self.durability_threshold,
                        68
                    )
            else:
                API.SysMsg(
                    "No equipped durability values could be read.",
                    33
                )
            return low

        now = time.time()
        should_warn = bool(low) and (
            newly_low or now >= self.next_durability_warning
        )

        if should_warn:
            self.next_durability_warning = now + 30.0
            worst = min(low, key=lambda entry: entry[4])
            API.SysMsg(
                "DURABILITY WARNING: {} is {}/{} ({:.0f}%).".format(
                    worst[1], worst[2], worst[3], worst[4]
                ),
                33
            )
            if len(low) > 1:
                API.SysMsg(
                    "%d equipped items are at or below %d%% durability." %
                    (len(low), self.durability_threshold),
                    33
                )

        return low

    def _gold_items(self, recursive=True):
        try:
            items = API.ItemsInContainer(API.Backpack, bool(recursive))
        except Exception:
            items = []

        result = []
        for item in list(items or []):
            try:
                if int(item.Graphic) == GOLD_GRAPHIC and int(item.Amount or 0) > 0:
                    result.append(item)
            except Exception:
                pass
        return result

    def _gold_in_backpack_root(self):
        try:
            items = API.ItemsInContainer(API.Backpack, False)
        except Exception:
            items = []

        result = []
        for item in list(items or []):
            try:
                if int(item.Graphic) == GOLD_GRAPHIC and int(item.Amount or 0) > 0:
                    result.append(item)
            except Exception:
                pass
        return result

    def _combine_gold_to_root(self):
        gold = self._gold_items(True)
        if not gold:
            return []

        root_serials = set(self._serial_of(item) for item in self._gold_in_backpack_root())

        for item in gold:
            serial = self._serial_of(item)
            if not serial or serial in root_serials:
                continue
            try:
                amount = int(item.Amount or 0)
            except Exception:
                amount = 0
            try:
                API.MoveItem(serial, API.Backpack, amount if amount > 0 else 0)
                API.Pause(0.35)
            except Exception:
                pass

        root = self._gold_in_backpack_root()
        for item in list(root):
            serial = self._serial_of(item)
            if not serial:
                continue
            try:
                amount = int(item.Amount or 0)
            except Exception:
                amount = 0
            if amount <= 0:
                continue
            try:
                API.MoveItem(serial, API.Backpack, amount)
                API.Pause(0.20)
            except Exception:
                pass

        return self._gold_in_backpack_root()

    def send_gold(self):
        if not self.send_bag_serial:
            API.SysMsg("Set your Bag of Sending in Setup first.", 33)
            return

        if not self._find_item(self.send_bag_serial):
            API.SysMsg("Saved Bag of Sending is not available.", 33)
            return

        stacks = self._combine_gold_to_root()
        if not stacks:
            API.SysMsg("No gold found in your backpack.", 68)
            return

        stacks = sorted(
            stacks,
            key=lambda item: int(getattr(item, "Amount", 0) or 0),
            reverse=True
        )

        sent = 0
        for item in stacks:
            serial = self._serial_of(item)
            if not serial or not self._find_item(serial):
                continue

            try:
                amount = int(item.Amount or 0)
            except Exception:
                amount = 0

            if amount > GOLD_MAX_STACK:
                API.SysMsg(
                    "Gold stack exceeds 60,000; leaving it unsent for safety.",
                    33
                )
                continue

            try:
                API.UseObject(self.send_bag_serial)
                if API.WaitForTarget("any", 1.5):
                    API.Target(serial)
                    sent += 1
                    API.Pause(0.60)
                else:
                    API.SysMsg("Bag of Sending did not give a target cursor.", 33)
                    break
            except Exception:
                API.SysMsg("Could not send gold.", 33)
                break

        if sent:
            API.Pause(0.25)
            charges = self._get_send_bag_charges(True)
            if charges is None:
                API.SysMsg("Sent %d gold stack(s) to the bank." % sent, 68)
            else:
                API.SysMsg(
                    "Sent %d gold stack(s). Bag of Sending: %d charge(s) left." %
                    (sent, charges),
                    68
                )
            self.refresh_combat_ui()

    # ========================================================
    # Shield + equipment
    # ========================================================

    def _hand_items(self):
        result = []
        for layer in ("OneHanded", "TwoHanded"):
            try:
                item = API.FindLayer(layer)
            except Exception:
                item = None

            if item:
                serial = self._serial_of(item)
                if serial and all(self._serial_of(existing) != serial for existing in result):
                    result.append(item)
        return result

    def _shield_equipped(self):
        if not self.shield_serial:
            return False

        return any(
            self._serial_of(item) == self.shield_serial
            for item in self._hand_items()
        )

    def _ensure_shield(self):
        if not self.shield_serial:
            return True

        if self._shield_equipped():
            return True

        if not self._find_item(self.shield_serial):
            return False

        try:
            API.EquipItem(self.shield_serial)
            API.Pause(0.35)
        except Exception:
            return False

        return self._shield_equipped()

    def _assigned_weapon_serials(self):
        return [serial for serial in self.slayer_weapons.values() if serial]

    def _equipped_assigned_weapon(self):
        assigned = self._assigned_weapon_serials()

        for item in self._hand_items():
            serial = self._serial_of(item)
            if serial in assigned:
                return item

        return None

    def _equipped_assigned_serial(self):
        return self._serial_of(self._equipped_assigned_weapon())

    def _profile_for_serial(self, serial):
        for profile, assigned in self.slayer_weapons.items():
            if assigned == serial:
                return profile
        return None

    def _resolve_profile(self, requested):
        serial = self.slayer_weapons.get(requested, 0)
        if serial:
            return requested, serial

        fallback = "General Single Target"
        return fallback, self.slayer_weapons.get(fallback, 0)

    def _equip_profile(self, requested):
        if not self.settings["auto_slayer"] and not self.manual_aoe:
            return False

        profile, serial = self._resolve_profile(requested)

        if not serial:
            return False

        if self._equipped_assigned_serial() == serial:
            self.active_profile = profile
            self._ensure_shield()
            return True

        backpack = API.FindLayer("Backpack")
        if not backpack:
            return False

        self._ensure_shield()

        current = self._equipped_assigned_weapon()
        if current:
            current_serial = self._serial_of(current)
            if current_serial and current_serial != serial and self.weapon_bag:
                try:
                    API.MoveItem(current_serial, self.weapon_bag, 1)
                    API.Pause(0.40)
                except Exception:
                    return False

        if not self._find_item(serial):
            return False

        try:
            API.MoveItem(serial, backpack.Serial, 1)
            API.Pause(0.35)
            API.EquipItem(serial)
            API.Pause(0.45)
        except Exception:
            return False

        self._ensure_shield()

        if self._equipped_assigned_serial() != serial:
            return False

        self.active_profile = profile
        self.detect_weapon()
        return True

    def _matching_slayer_is_aoe_capable(self):
        profile = self.detected_profile
        serial = self.slayer_weapons.get(profile, 0)
        if not serial:
            return False

        weapon_type = self.slayer_weapon_types.get(profile, "")
        if not weapon_type:
            weapon_type = self._detect_assigned_weapon_type(serial)
            if weapon_type:
                self.slayer_weapon_types[profile] = weapon_type
                try:
                    API.SavePersistentVar(
                        "JCS_UCB_SlayerType_" + profile.replace(" ", "_"),
                        weapon_type,
                        API.PersistentVar.Char
                    )
                except Exception:
                    pass

        return weapon_type == "bladedwhip"

    def _apply_combat_weapon(self):
        if self.manual_aoe:
            self._equip_profile("General AOE")
        elif self.auto_aoe_active:
            if self._matching_slayer_is_aoe_capable():
                self._equip_profile(self.detected_profile)
            else:
                self._equip_profile("General AOE")
        else:
            self._equip_profile(self.detected_profile)

    # ========================================================
    # Auto AOE
    # ========================================================

    def _update_auto_aoe(self):
        if not self.settings["auto_aoe"] or self.manual_aoe:
            self.auto_aoe_active = False
            return

        count = len(self.enemies(AUTO_AOE_RANGE))

        if not self.auto_aoe_active and count >= AUTO_AOE_ENTER_COUNT:
            self.auto_aoe_active = True

            if self._matching_slayer_is_aoe_capable():
                self._equip_profile(self.detected_profile)
            else:
                self._equip_profile("General AOE")

            self.refresh_combat_ui()
            return

        if self.auto_aoe_active and count <= AUTO_AOE_EXIT_COUNT:
            self.auto_aoe_active = False
            self._equip_profile(self.detected_profile)
            self.refresh_combat_ui()
            return

        if self.auto_aoe_active:
            if self._matching_slayer_is_aoe_capable():
                self._equip_profile(self.detected_profile)
            else:
                self._equip_profile("General AOE")

    # ========================================================
    # Sword Attack Bar combat logic
    # ========================================================

    def _ready(self, action, seconds):
        now = time.time()
        if now < self.next_actions.get(action, 0.0):
            return False
        self.next_actions[action] = now + seconds
        return True

    def _mana(self):
        return int(API.Player.Mana or 0)

    def _hits_percent(self):
        maximum = int(API.Player.HitsMax or 0)
        return (100.0 * int(API.Player.Hits or 0) / maximum) if maximum else 0.0

    def _buff_active(self, wanted):
        wanted_text = "".join(ch for ch in wanted.lower() if ch.isalnum())
        try:
            for buff in API.ActiveBuffs():
                title = str(buff.Title or "")
                title_text = "".join(ch for ch in title.lower() if ch.isalnum())
                if wanted_text in title_text or title_text in wanted_text:
                    return True
        except Exception:
            pass

        try:
            return API.BuffExists(wanted)
        except Exception:
            return False

    def _ability_key(self, name):
        return "".join(ch for ch in str(name or "").lower() if ch.isalnum())

    def detect_weapon(self):
        if not self.settings["auto_weapon"] or time.time() < self.next_weapon_scan:
            return

        self.next_weapon_scan = time.time() + 0.50

        try:
            names = API.CurrentAbilityNames()
            abilities = frozenset(self._ability_key(name) for name in names if name)
        except Exception:
            return

        pairs = {
            frozenset(("doublestrike", "whirlwindattack")): "doubleaxe",
            frozenset(("armorignore", "concussionblow")): "longsword",
            frozenset(("crushingblow", "armorignore")): "broadsword",
            frozenset(("bleedattack", "whirlwindattack")): "bladedwhip",
            frozenset(("whirlwindattack", "bladeweave")): "radiantscimitar",
            frozenset(("armorignore", "movingshot")): "ranged",
        }

        detected = pairs.get(abilities)

        if detected == "ranged":
            detected = self.weapon_type if self.weapon_type in ("compositebow", "soulglaive") else "compositebow"

        if not detected:
            return

        self.weapon_type = detected
        self._save_settings()

    def _cast(self, spell, mana, cooldown, buff=None):
        if self._mana() < mana:
            return False
        if buff and self._buff_active(buff):
            return False
        if not self._ready("spell_" + spell, cooldown):
            return False
        API.CastSpell(spell)
        return True

    def _honor(self, enemy):
        if not self.settings["honor"]:
            return

        try:
            full_health = int(enemy.Hits or 0) == int(enemy.HitsMax or 0)
        except Exception:
            full_health = False

        if not full_health:
            return

        if not self._ready("honor_" + str(enemy.Serial), 8.0):
            return

        API.Virtue("honor")
        if API.WaitForTarget("any", 0.75):
            API.Target(enemy.Serial)

    def _enemy_type_key(self, enemy):
        if not enemy:
            return None

        try:
            graphic = int(enemy.Graphic or 0)
        except Exception:
            graphic = 0

        if graphic:
            return "body:{:04X}".format(graphic)

        try:
            name = str(enemy.Name or "").strip().lower()
        except Exception:
            name = ""

        if name:
            return "name:" + "".join(ch for ch in name if ch.isalnum() or ch == " ")

        return None

    def _manage_enemy_of_one(self, enemy):
        if not self.settings["eoo"]:
            self.eoo_enemy_key = None
            return

        if self._mana() < 12:
            return

        new_key = self._enemy_type_key(enemy)
        if not new_key:
            return

        active = self._buff_active("Enemy Of One")

        if active and self.eoo_enemy_key == new_key:
            return

        if active and self.eoo_enemy_key and self.eoo_enemy_key != new_key:
            try:
                API.CastSpell("Enemy of One")
                API.Pause(1.0)
            except Exception:
                return

        if self._mana() >= 12 and not self._buff_active("Enemy Of One"):
            try:
                API.CastSpell("Enemy of One")
                API.Pause(0.6)
            except Exception:
                return

        self.eoo_enemy_key = new_key

    def _new_target(self, enemy):
        if self.current_enemy_serial == int(enemy.Serial):
            return

        self._set_current_enemy(enemy)
        API.HeadMsg("Target: " + str(enemy.Name), API.Player, 68)
        self._apply_combat_weapon()
        self._honor(enemy)
        self.refresh_combat_ui()

        self._manage_enemy_of_one(enemy)

    def _basher_ready(self):
        if not self.settings.get("bash", False):
            return False
        if not self.shield_serial or not self._shield_equipped():
            return False
        try:
            parry = API.GetSkill("Parrying")
            if not parry or float(parry.Value) < 90.0:
                return False
        except Exception:
            return False
        return True

    def _shield_bash(self):
        if not self._basher_ready() or self._mana() < 40:
            return False
        if self._buff_active("Shield Bash"):
            return False
        if not self._ready("mastery_shield_bash", 3.0):
            return False
        try:
            API.CastSpell("Shield Bash")
            return True
        except Exception:
            return False

    def _buffs(self):
        self._shield_bash()

        if self.settings["curse"] and self._hits_percent() < 60:
            self._cast("Curse Weapon", 7, 6.25, "Curse Weapon")

        if self.settings["df"]:
            self._cast("Divine Fury", 8, 18.25, "Divine Fury")

        if self.settings["cw"]:
            self._cast("Consecrate Weapon", 6, 11.25, "Consecrate Weapon")

        if self.settings["ca"] and self._hits_percent() >= 60:
            if not self._buff_active("Confidence") and not self._buff_active("Evasion"):
                self._cast("Counter Attack", 5, 2.0, "Counter Attack")

    def _activate_primary(self):
        if not API.PrimaryAbilityActive():
            API.ToggleAbility("primary")

    def _activate_secondary(self):
        if not API.SecondaryAbilityActive():
            API.ToggleAbility("secondary")

    def _clear_weapon_abilities(self):
        if API.PrimaryAbilityActive():
            API.ToggleAbility("primary")
        if API.SecondaryAbilityActive():
            API.ToggleAbility("secondary")

    def _single_target_ability(self):
        if self.settings["onslaught"] and self._mana() >= 20:
            if self._cast("Onslaught", 20, 7.0, "Onslaught"):
                self._clear_weapon_abilities()
                return

        if self.weapon_type == "broadsword":
            if self._mana() >= 30:
                self._activate_secondary()
            else:
                self._clear_weapon_abilities()
            return

        if self.weapon_type == "radiantscimitar":
            if self._mana() >= 15:
                self._activate_secondary()
            else:
                self._clear_weapon_abilities()
            return

        if self.weapon_type in ("longsword", "compositebow", "soulglaive"):
            if self._mana() >= 30:
                self._activate_primary()
            else:
                self._clear_weapon_abilities()
            return

        if self.weapon_type == "doubleaxe":
            if self._mana() >= 30:
                self._activate_primary()
            else:
                self._clear_weapon_abilities()
            return

        if self.weapon_type == "bladedwhip":
            if self._mana() >= 30:
                self._activate_primary()
            else:
                self._clear_weapon_abilities()
            return

        if self._mana() >= 30:
            self._activate_primary()
        elif self.settings["lightning"] and self._mana() >= 10:
            self._clear_weapon_abilities()
            self._cast("Lightning Strike", 10, 1.0, "Lightning Strike")
        else:
            self._clear_weapon_abilities()

    def _multiple_target_ability(self):
        if self.weapon_type == "radiantscimitar":
            if self._mana() >= 15:
                self._activate_primary()
            else:
                self._clear_weapon_abilities()
            return

        if self.weapon_type in ("bladedwhip", "doubleaxe"):
            if self._mana() >= 15:
                self._activate_secondary()
            else:
                self._clear_weapon_abilities()
            return

        if self.settings["momentum"] and self._mana() >= 10:
            self._clear_weapon_abilities()
            self._cast("Momentum Strike", 10, 1.0, "Momentum Strike")
            return

        self._single_target_ability()

    # ========================================================
    # Unified combat tick
    # ========================================================

    def combat_tick(self):
        ranged = self.weapon_type in ("compositebow", "soulglaive")
        attack_range = 12 if ranged else 1
        nearby_range = 10 if ranged else 1

        victims = self.enemies(attack_range)

        if not victims:
            if self.current_enemy_serial:
                self._set_current_enemy(None)
                self.refresh_combat_ui()
            return

        enemy = victims[0]

        self._new_target(enemy)
        self._update_auto_aoe()

        API.Attack(enemy.Serial)
        self._buffs()

        nearby = len(self.enemies(nearby_range))

        if nearby >= 2:
            self._multiple_target_ability()
        else:
            self._single_target_ability()

    # ========================================================
    # Main loop
    # ========================================================

    def run(self):
        self._ensure_shield()
        self.build_ui()

        API.SysMsg(
            "J.C.S. Ultimate Combat Bar v{} loaded - PUBLIC TEST.".format(VERSION),
            68
        )
        API.SysMsg(
            "Basher / Shield Bash support is BETA and needs Parry Mastery community testing.",
            53
        )

        try:
            while self.running and not API.StopRequested:
                API.ProcessCallbacks()

                now = time.time()

                if now >= self.next_position_save:
                    self._remember_position()
                    self.next_position_save = now + 0.75

                if now >= self.next_shield_check:
                    self._ensure_shield()
                    self.next_shield_check = now + 0.75

                if now >= self.next_durability_check:
                    before = bool(self.low_durability)
                    self.check_durability(False)
                    after = bool(self.low_durability)
                    self.next_durability_check = now + 5.0
                    if before != after and not self.setup_mode:
                        self.refresh_combat_ui()

                if self.send_bag_serial and now >= self.next_send_bag_check:
                    old_charges = self.send_bag_charges
                    new_charges = self._get_send_bag_charges(True)
                    if old_charges != new_charges and not self.setup_mode:
                        self.refresh_combat_ui()

                if now >= self.next_apple_check:
                    old_apples = self.enchanted_apple_count
                    new_apples = self._refresh_enchanted_apples(True)
                    if old_apples != new_apples and not self.setup_mode:
                        self.refresh_combat_ui()

                if not self.paused and not API.Player.IsDead:
                    self.detect_weapon()
                    self.combat_tick()

                API.Pause(0.10)

        finally:
            self._remember_position()
            self._save_settings()
            self._clear_weapon_abilities()

            if self.ui:
                try:
                    self.ui.Dispose()
                except Exception:
                    pass
                self.ui = None

            API.SysMsg("J.C.S. Ultimate Combat Bar stopped.", 33)


UltimateCombatBar().run()
