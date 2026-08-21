"""
J.C.S. Artisan Workshop for TazUO LegionPy
Version Beta 1

Crafts supported weapons and armor, applies configurable imbues, manages named
templates, stages resources from a secure chest, maintains crafting tools, and
moves completed products into a selected output container.

Safety limits: rejected non-exceptional items are retained in the backpack.
Salvage, reforging, and elemental conversion are intentionally deferred.
"""

import re
import json
import base64
import API


VERSION = "BETA 1"
PRODUCT_NAME = "J.C.S. ARTISAN WORKSHOP"
TEMPLATE_SLOTS = 24
TEMPLATES_PER_PAGE = 6
# A final full-weight imbue can be near 12% success. Twenty attempts gives
# about a 92% cumulative chance while retaining a hard material-loss guard.
MAX_IMBUE_ATTEMPTS = 20
# Stage enough consumable ingredients for ten consecutive attempts. If an
# unusually bad streak uses that reserve, the next retry stages another block.
# Rare special ingredients are only staged once because failures retain them.
IMBUE_RETRY_RESERVE = 10
WEIGHT_SAFETY_MARGIN = 20

TOOL_RECIPES = {
    "tinker": ("tinker tools", (15, 23)),
    "tailoring": ("sewing kit", (15, 44)),
    "smith": ("smith's hammer", (15, 93)),
    "fletching": ("fletching tools", (142,)),
}

TOOL_GRAPHICS = {
    "tinker": (0x1EB8, 0x1EBC),
    "tailoring": (0x0F9D,),
    "smith": (0x13E3,),
    "fletching": (0x1022,),
}

SMITH_GUMP = 0x38920ABD
IMBUE_MAIN_GUMP = 0x65290B89
IMBUE_PROPERTY_GUMP = 0x6731CF94
IMBUE_CONFIRM_GUMP = 0xEA767EE4

SMITH_BLADED = 22
SMITH_KATANA = 37

WEAPON_CRAFT = {
    "Katana": {
        "graphic": 0x13FF,
        "tool": "smith",
        "category": SMITH_BLADED,
        "button": SMITH_KATANA,
        "match": "katana",
        "ingots": 8,
        "leech_max": 62,
    },
    "Double Axe": {
        "graphic": 0x0F4B,
        "tool": "smith",
        "category": 29,
        "button": 16,
        "match": "double axe",
        "ingots": 12,
        "leech_max": 81,
    },
    "Longsword": {
        "graphic": 0x0F61,
        "tool": "smith",
        "category": 22,
        "button": 51,
        "match": "longsword",
        "ingots": 12,
        "leech_max": 87,
    },
    "Broadsword": {
        "graphic": 0x0F5E,
        "tool": "smith",
        "category": 22,
        "button": 9,
        "match": "broadsword",
        "ingots": 10,
        "leech_max": 81,
    },
    "Radiant Scimitar": {
        "graphic": 0x2D33,
        "tool": "smith",
        "category": 22,
        "button": 128,
        "match": "radiant scimitar",
        "ingots": 15,
        "leech_max": 62,
    },
    "Soul Glaive": {
        "tool": "smith",
        "category": 57,
        "button": 16,
        "match": "soul glaive",
        "ingots": 9,
        "leech_max": 100,
    },
    "Composite Bow": {
        "graphic": 0x26C2,
        "tool": "fletching",
        "category": 15,
        "button": 23,
        "match": "composite bow",
        "resource": "Board",
        "amount": 7,
        "leech_max": 100,
    },
    "Bladed Whip": {
        "tool": "tinker",
        "category": 36,
        "button": 282,
        "match": "bladed whip",
        # All three craftable whips use the same material requirement.
        "ingots": 15,
        "leech_max": 81,
    },
    "Barbed Whip": {
        "tool": "tinker",
        "category": 36,
        "button": 268,
        "match": "barbed whip",
        "ingots": 15,
        "leech_max": 81,
    },
    "Spiked Whip": {
        "tool": "tinker",
        "category": 36,
        "button": 275,
        "match": "spiked whip",
        "ingots": 15,
        "leech_max": 81,
    },
}

ARMOR_CRAFT = {
    "Studded Gorget": {"graphic": 0x13D6, "tool": "tailoring", "category": 50, "button": 2, "match": "studded gorget", "resource": "Leather", "amount": 6},
    "Studded Gloves": {"graphic": 0x13D5, "tool": "tailoring", "category": 50, "button": 9, "match": "studded gloves", "resource": "Leather", "amount": 8},
    "Studded Sleeves": {"graphic": 0x13DC, "tool": "tailoring", "category": 50, "button": 16, "match": "studded sleeves", "resource": "Leather", "amount": 10},
    "Studded Leggings": {"graphic": 0x13DA, "tool": "tailoring", "category": 50, "button": 23, "match": "studded leggings", "resource": "Leather", "amount": 12},
    "Studded Tunic": {"graphic": 0x13DB, "tool": "tailoring", "category": 50, "button": 30, "match": "studded tunic", "resource": "Leather", "amount": 14},
    "Leather Gorget": {"graphic": 0x13C7, "tool": "tailoring", "category": 36, "button": 23, "match": "leather gorget", "resource": "Leather", "amount": 4},
    "Leather Cap": {"graphic": 0x1DB9, "tool": "tailoring", "category": 36, "button": 30, "match": "leather cap", "resource": "Leather", "amount": 2},
    "Leather Gloves": {"graphic": 0x13C6, "tool": "tailoring", "category": 36, "button": 37, "match": "leather gloves", "resource": "Leather", "amount": 3},
    "Leather Sleeves": {"graphic": 0x13CD, "tool": "tailoring", "category": 36, "button": 44, "match": "leather sleeves", "resource": "Leather", "amount": 4},
    "Leather Leggings": {"graphic": 0x13CB, "tool": "tailoring", "category": 36, "button": 51, "match": "leather leggings", "resource": "Leather", "amount": 10},
    "Leather Tunic": {"graphic": 0x13CC, "tool": "tailoring", "category": 36, "button": 58, "match": "leather tunic", "resource": "Leather", "amount": 12},
}

CRAFT_MATERIALS = {
    "leather": [
        ("Standard Leather", 6, "Leather", "No additional material bonus"),
        ("Spined Leather", 13, "Spined Leather", "+9 Physical Resist, +40 Luck"),
        ("Horned Leather", 20, "Horned Leather", "+2 Physical, +4 Fire, +3 Cold/Poison/Energy"),
        ("Barbed Leather", 27, "Barbed Leather", "+3 Physical/Cold/Poison, +2 Fire, +5 Energy"),
    ],
    "metal": [
        ("Iron", 6, "Iron Ingot", "No additional material bonus"),
        ("Dull Copper", 13, "Dull Copper Ingot", "Armor: +10 Physical; durability/lower requirements bonuses"),
        ("Shadow Iron", 20, "Shadow Iron Ingot", "Armor: +3 Physical, +2 Fire, +7 Energy"),
        ("Copper", 27, "Copper Ingot", "Armor: +2 Physical/Fire/Energy, +7 Poison"),
        ("Bronze", 34, "Bronze Ingot", "Armor: +3 Physical, +7 Cold, +2 Poison/Energy"),
        ("Gold", 41, "Gold Ingot", "Armor: mixed resists, +40 Luck, lower requirements"),
        ("Agapite", 48, "Agapite Ingot", "Armor: +7 Fire and balanced resist bonuses"),
        ("Verite", 55, "Verite Ingot", "Armor: strong balanced resists; weapon energy/poison"),
        ("Valorite", 62, "Valorite Ingot", "Armor: +5 Physical and +4 Cold/Poison/Energy"),
    ],
    "wood": [
        ("Wood", 6, "Board", "No additional material bonus"),
        ("Oak", 13, "Oak Board", "Weapons: +5% Damage, +40 Luck, +50 Durability"),
        ("Ash", 20, "Ash Board", "Weapons: +10% Swing Speed, -20% Requirements, -75% Weight"),
        ("Yew", 27, "Yew Board", "Weapons: +10% Damage, +5% Hit Chance"),
        ("Heartwood", 34, "Heartwood Board", "Weapons: one random Heartwood property"),
        ("Bloodwood", 41, "Bloodwood Board", "Weapons: HPR 2 and variable Hit Life Leech"),
        ("Frostwood", 48, "Frostwood Board", "Weapons: 40% Cold Damage and +12% Damage"),
    ],
}

IMBUE_ITEM = 10005
REIMBUE_LAST = 10006
IMBUE_CONFIRM = 10100
INTENSITY_UP_ONE = 10054

CAT_HIT_AREA = 10006
CAT_HIT_EFFECTS = 10007
CAT_COMBAT = 10002
CAT_SLAYER = 10009
CAT_SUPER_SLAYER = 10008
CAT_CASTING = 10001
CAT_MISC = 10003
CAT_STATS = 10005

WEAPON_RECIPE = [
    # Apply rarer/higher-weight properties first while success chance is best.
    # Special ingredients are retained on failure, but primary resources and
    # gems can be lost, making Relic Fragment-based Hit Lightning the priority.
    ("Hit Lightning", CAT_HIT_EFFECTS, 10138, 18),
    ("Hit Fireball", CAT_HIT_EFFECTS, 10137, 50),
    ("Hit Harm", CAT_HIT_EFFECTS, 10136, 50),
    ("Hit Lower Defense", CAT_HIT_EFFECTS, 10129, 45),
    ("Damage Increase", CAT_COMBAT, 10112, 50),
    # SSI must be applied before hit leeches; applying it afterward can lower
    # their weapon-speed-dependent intensities.
    ("Swing Speed Increase", CAT_COMBAT, 10113, 30),
    ("Hit Mana Leech", CAT_HIT_EFFECTS, 10127, 62),
    ("Hit Life Leech", CAT_HIT_EFFECTS, 10125, 62),
    ("Hit Cold Area", CAT_HIT_AREA, 10132, 50),
    ("Hit Fire Area", CAT_HIT_AREA, 10131, 45),
    ("Hit Energy Area", CAT_HIT_AREA, 10134, 45),
    ("Undead Slayer", CAT_SLAYER, 10221, 1),
    ("Reptile Slayer", CAT_SLAYER, 10223, 1),
    ("Repond Slayer", CAT_SLAYER, 10222, 1),
    ("Fey Slayer", CAT_SLAYER, 10227, 1),
    ("Elemental Slayer", CAT_SLAYER, 10226, 1),
    ("Demon Slayer", CAT_SLAYER, 10224, 1),
    ("Arachnid Slayer", CAT_SLAYER, 10225, 1),
    ("Poison Elemental Slayer", CAT_SUPER_SLAYER, 10217, 1),
    ("Dragon Slayer", CAT_SUPER_SLAYER, 10204, 1),
]

ARMOR_RECIPE = [
    ("Lower Mana Cost", CAT_CASTING, 10117, 8),
    ("Lower Reagent Cost", CAT_CASTING, 10118, 20),
    ("Luck", CAT_MISC, 10121, 100),
    ("Stamina Increase", CAT_STATS, 10110, 8),
    ("Hit Point Increase", CAT_STATS, 10109, 5),
    ("Mana Increase", CAT_STATS, 10111, 8),
]

ALL_PROPERTIES = WEAPON_RECIPE + ARMOR_RECIPE

PROPERTY_MAX = {
    "Hit Lightning": 50,
    "Hit Fireball": 50,
    "Hit Harm": 50,
    "Hit Lower Defense": 50,
    "Damage Increase": 50,
    "Swing Speed Increase": 30,
    "Hit Mana Leech": 62,
    "Hit Life Leech": 62,
    "Hit Cold Area": 50,
    "Hit Fire Area": 50,
    "Hit Energy Area": 50,
    "Undead Slayer": 1,
    "Reptile Slayer": 1,
    "Repond Slayer": 1,
    "Fey Slayer": 1,
    "Elemental Slayer": 1,
    "Demon Slayer": 1,
    "Arachnid Slayer": 1,
    "Poison Elemental Slayer": 1,
    "Dragon Slayer": 1,
    "Lower Reagent Cost": 20,
    "Lower Mana Cost": 8,
    "Luck": 100,
    "Stamina Increase": 8,
    "Hit Point Increase": 5,
    "Mana Increase": 8,
}

PROPERTY_RESOURCES = {
    "Hit Lightning": ("Relic Fragment", "Amethyst", "Essence of Passion"),
    "Hit Fireball": ("Enchanted Essence", "Ruby", "Fire Ruby"),
    "Hit Harm": ("Enchanted Essence", "Emerald", "Parasitic Plant"),
    "Hit Lower Defense": ("Enchanted Essence", "Tourmaline", "Parasitic Plant"),
    "Damage Increase": ("Enchanted Essence", "Citrine", "Crystal Shards"),
    "Swing Speed Increase": ("Relic Fragment", "Tourmaline", "Essence of Control"),
    "Hit Mana Leech": ("Magical Residue", "Sapphire", "Void Orb"),
    "Hit Life Leech": ("Magical Residue", "Ruby", "Void Orb"),
    "Hit Cold Area": ("Magical Residue", "Sapphire", "Raptor Teeth"),
    "Hit Fire Area": ("Magical Residue", "Ruby", "Raptor Teeth"),
    "Hit Energy Area": ("Magical Residue", "Amethyst", "Raptor Teeth"),
    "Undead Slayer": ("Relic Fragment", "Ruby", "Undying Flesh"),
    "Reptile Slayer": ("Relic Fragment", "Ruby", "Lava Serpent Crust"),
    "Repond Slayer": ("Relic Fragment", "Ruby", "Goblin Blood"),
    "Fey Slayer": ("Relic Fragment", "Ruby", "Fey Wings"),
    "Elemental Slayer": ("Relic Fragment", "Ruby", "Vial of Vitriol"),
    "Demon Slayer": ("Relic Fragment", "Ruby", "Daemon Claw"),
    "Arachnid Slayer": ("Relic Fragment", "Ruby", "Spider Carapace"),
    "Poison Elemental Slayer": ("Magical Residue", "Emerald", "White Pearl"),
    "Dragon Slayer": ("Enchanted Essence", "Emerald", "White Pearl"),
    "Lower Reagent Cost": ("Magical Residue", "Amber", "Faery Dust"),
    "Lower Mana Cost": ("Relic Fragment", "Tourmaline", "Essence of Order"),
    "Luck": ("Magical Residue", "Citrine", "Chaga Mushroom"),
    "Stamina Increase": ("Enchanted Essence", "Diamond", "Luminescent Fungi"),
    "Hit Point Increase": ("Enchanted Essence", "Ruby", "Luminescent Fungi"),
    "Mana Increase": ("Enchanted Essence", "Sapphire", "Luminescent Fungi"),
}

DEFAULT_ENABLED = {
    "Hit Lightning": True,
    "Hit Fireball": False,
    "Hit Harm": False,
    "Hit Lower Defense": False,
    "Damage Increase": False,
    "Swing Speed Increase": False,
    "Hit Mana Leech": True,
    "Hit Life Leech": True,
    "Hit Cold Area": True,
    "Hit Fire Area": False,
    "Hit Energy Area": False,
    "Undead Slayer": False,
    "Reptile Slayer": False,
    "Repond Slayer": False,
    "Fey Slayer": False,
    "Elemental Slayer": False,
    "Demon Slayer": False,
    "Arachnid Slayer": False,
    "Poison Elemental Slayer": False,
    "Dragon Slayer": False,
    "Lower Reagent Cost": True,
    "Lower Mana Cost": False,
    "Luck": False,
    "Stamina Increase": False,
    "Hit Point Increase": False,
    "Mana Increase": False,
}

PROPERTY_GROUP = {
    "Hit Lightning": "hit_spell",
    "Hit Fireball": "hit_spell",
    "Hit Harm": "hit_spell",
    "Hit Cold Area": "hit_area",
    "Hit Fire Area": "hit_area",
    "Hit Energy Area": "hit_area",
    "Undead Slayer": "slayer",
    "Reptile Slayer": "slayer",
    "Repond Slayer": "slayer",
    "Fey Slayer": "slayer",
    "Elemental Slayer": "slayer",
    "Demon Slayer": "slayer",
    "Arachnid Slayer": "slayer",
    "Poison Elemental Slayer": "slayer",
    "Dragon Slayer": "slayer",
}

PROPERTY_FIXED = {
    "Undead Slayer", "Reptile Slayer", "Repond Slayer", "Fey Slayer",
    "Elemental Slayer", "Demon Slayer", "Arachnid Slayer",
    "Poison Elemental Slayer",
    "Dragon Slayer",
}

# These properties are displayed as points, not percentages, on item tooltips.
PROPERTY_FLAT = {"Luck", "Stamina Increase", "Hit Point Increase", "Mana Increase"}

PROPERTY_MIN = {
    "Lower Mana Cost": 1,
    "Lower Reagent Cost": 1,
    "Luck": 1,
    "Stamina Increase": 1,
    "Hit Point Increase": 1,
    "Mana Increase": 1,
}


class CraftImbueManager:
    def __init__(self):
        self.ui = None
        self.screen = "select"
        self.selection_group = "weapon"
        self.selection_page = 0
        self.production_qty = 1
        self.preview_ok = False
        self.preview_lines = []
        self.template_box = None
        self.template_name_box = None
        self.template_name_draft = ""
        self.template_job_mode = False
        self.selected_template_slot = 0
        self.template_page = 0
        self.batch_page = 0
        self.batch_quantities = {}
        self.batch_preview_ok = False
        self.batch_preview_lines = []
        self.batch_material_family = ""
        self.selected_material = {
            "leather": self._load_text("JCS_CIM_Material_leather", "Standard Leather"),
            "metal": self._load_text("JCS_CIM_Material_metal", "Iron"),
            "wood": self._load_text("JCS_CIM_Material_wood", "Wood"),
        }
        old_template = self._load_text("JCS_CIM_SavedTemplate", "")
        if old_template and not self._load_text("JCS_CIM_Template_0", ""):
            self._save_text("JCS_CIM_Template_0", old_template)
        self.running = True
        self.busy = False
        self.track_batch_pulls = False
        self.batch_pull_baseline = {}
        self.batch_pulled_resources = {}
        self.item_mode = "weapon"
        saved_weapon = self._load_text("JCS_CIM_SelectedWeapon", "Katana")
        self.selected_weapon = saved_weapon if saved_weapon in WEAPON_CRAFT else "Katana"
        saved_armor = self._load_text("JCS_CIM_SelectedArmor", "Studded Gorget")
        self.selected_armor = saved_armor if saved_armor in ARMOR_CRAFT else "Studded Gorget"
        self.property_page = 0
        self.status = "Select your smith tool"
        self.smith_tool = self._load_int("JCS_CIM_SmithTool", 0)
        self.tinker_tool = self._load_int("JCS_CIM_TinkerTool", 0)
        self.fletching_tool = self._load_int("JCS_CIM_FletchingTool", 0)
        self.tailoring_tool = self._load_int("JCS_CIM_TailoringTool", 0)
        self.resource_chest = self._load_int("JCS_CIM_ResourceChest", 0)
        self.finished_container = self._load_int("JCS_CIM_FinishedContainer", 0)
        if not self._load_int("JCS_CIM_SetupComplete", 0):
            self.screen = "setup"
            self.status = "First run: save your chest and crafting tools"
        self.gump_x = self._load_int("JCS_CIM_GumpX", 120)
        self.gump_y = self._load_int("JCS_CIM_GumpY", 120)
        self.recipe_enabled = {}
        self.recipe_targets = {}
        self.target_labels = {}
        self.target_meters = {}
        for name, _category, _prop, target in ALL_PROPERTIES:
            default_enabled = 1 if DEFAULT_ENABLED.get(name, False) else 0
            self.recipe_enabled[name] = bool(
                self._load_int("JCS_CIM_Enable_" + name, default_enabled)
            )
            saved = self._load_int("JCS_CIM_Target_" + name, target)
            minimum = PROPERTY_MIN.get(name, 2)
            self.recipe_targets[name] = max(minimum, min(self._property_max(name), saved))

    def _load_int(self, key, default=0):
        try:
            return int(API.GetPersistentVar(key, str(default), API.PersistentVar.Char))
        except Exception:
            return int(default)

    def _load_text(self, key, default=""):
        try:
            return str(API.GetPersistentVar(key, str(default), API.PersistentVar.Char))
        except Exception:
            return str(default)

    def _save_text(self, key, value):
        try:
            API.SavePersistentVar(key, str(value), API.PersistentVar.Char)
        except Exception:
            pass

    def _save_int(self, key, value):
        try:
            API.SavePersistentVar(key, str(int(value)), API.PersistentVar.Char)
        except Exception:
            pass

    def _serial(self, value):
        try:
            return int(value.Serial)
        except Exception:
            try:
                return int(value)
            except Exception:
                return 0

    def _set_status(self, text, hue=68):
        self.status = str(text)
        API.SysMsg(self.status, hue)
        self.build_ui()

    def _remember_position(self):
        if not self.ui:
            return
        try:
            if self.ui.IsDisposed:
                return
            self.gump_x = int(self.ui.GetX())
            self.gump_y = int(self.ui.GetY())
        except Exception:
            return

    def save_position_now(self):
        self._remember_position()
        self._save_int("JCS_CIM_GumpX", self.gump_x)
        self._save_int("JCS_CIM_GumpY", self.gump_y)
        API.SysMsg("Artisan Workshop position saved.", 68)

    def show_screen(self, name):
        if self.busy:
            return
        self.screen = str(name)
        self.build_ui()

    def _textbox_value(self, control):
        if not control:
            return ""
        try:
            return str(control.Text or "")
        except Exception:
            try:
                return str(control.GetText() or "")
            except Exception:
                return ""

    def choose_group(self, group):
        self.selection_group = str(group)
        self.selection_page = 0
        self.build_ui()

    def choose_item(self, mode, name):
        self.item_mode = mode
        if mode == "armor":
            self.selected_armor = name
            self._save_text("JCS_CIM_SelectedArmor", name)
        else:
            self.selected_weapon = name
            self._save_text("JCS_CIM_SelectedWeapon", name)
        self.property_page = 0
        self.screen = "imbues"
        self.status = "Configure imbues for " + name
        self.build_ui()

    def copy_target_item(self):
        if self.busy:
            return
        API.SysMsg("Target the weapon or armor piece whose build you want to copy.", 68)
        target = API.RequestTarget()
        serial = self._serial(target)
        item = API.FindItem(serial) if serial else None
        text = self._item_text(item) if item else ""
        if not item or not text:
            self._set_status("Copy-item targeting cancelled or item could not be read", 33)
            return

        detected = None
        for mode, source in (("weapon", WEAPON_CRAFT), ("armor", ARMOR_CRAFT)):
            for item_name, craft in source.items():
                if craft.get("match", item_name.lower()) in text.lower():
                    detected = (mode, item_name)
                    break
            if detected:
                break
        if not detected:
            self._set_status("That item type is not supported by the crafting library yet", 33)
            return

        self.item_mode, item_name = detected
        if self.item_mode == "armor":
            self.selected_armor = item_name
            self._save_text("JCS_CIM_SelectedArmor", item_name)
        else:
            self.selected_weapon = item_name
            self._save_text("JCS_CIM_SelectedWeapon", item_name)
        self._remember_item_graphic(item)

        copied = []
        for name, _category, _prop, _default in self._current_library():
            value = self._property_value(text, name)
            enabled = value > 0
            self.recipe_enabled[name] = enabled
            self._save_int("JCS_CIM_Enable_" + name, 1 if enabled else 0)
            if enabled:
                if name in PROPERTY_FIXED:
                    target_value = 1
                else:
                    target_value = max(
                        PROPERTY_MIN.get(name, 2),
                        min(self._property_max(name), int(value)),
                    )
                self.recipe_targets[name] = target_value
                self._save_int("JCS_CIM_Target_" + name, target_value)
                copied.append("{} {}".format(name, self._value_text(name, target_value)))

        self.property_page = 0
        self.preview_ok = False
        self.batch_preview_ok = False
        self.template_job_mode = False
        self.screen = "imbues"
        if copied:
            self.status = "Copied {} supported properties from {}".format(
                len(copied), item_name
            )
            API.SysMsg(self.status + ": " + ", ".join(copied), 68)
        else:
            self.status = "Item recognized, but no supported imbues were found"
            API.SysMsg(self.status, 53)
        self.build_ui()

    def adjust_quantity(self, delta):
        self.production_qty = max(1, min(100, self.production_qty + int(delta)))
        self.preview_ok = False
        self.build_ui()

    def _template_payload(self, template_name=""):
        return {
            "v": 1,
            "name": str(template_name or (self._selected_item_name() + " Build"))[:40],
            "mode": self.item_mode,
            "item": self._selected_item_name(),
            "material": self.selected_material.get(self._material_family(), ""),
            # A saved template represents the designed final build. Test mode
            # is a temporary production choice and is intentionally not baked
            # into reusable templates.
            "enabled": [name for name, _c, _p, _d in self._current_library() if self.recipe_enabled.get(name, False)],
            "targets": dict((name, self.recipe_targets.get(name, PROPERTY_MIN.get(name, 2))) for name, _c, _p, _d in self._current_library()),
        }

    def _encode_template(self, template_name=""):
        raw = json.dumps(self._template_payload(template_name), separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    def _decode_template(self, code):
        code = re.sub(r"\s+", "", str(code or ""))
        raw = base64.urlsafe_b64decode((code + "=" * ((4 - len(code) % 4) % 4)).encode("ascii"))
        return json.loads(raw.decode("utf-8"))

    def _apply_template_code(self, code, preserve_item=False):
        try:
            data = self._decode_template(code)
            mode = data.get("mode")
            item = data.get("item")
            if preserve_item:
                if mode != self.item_mode:
                    raise ValueError("incompatible item type")
            else:
                if mode == "weapon" and item in WEAPON_CRAFT:
                    self.item_mode, self.selected_weapon = mode, item
                elif mode == "armor" and item in ARMOR_CRAFT:
                    self.item_mode, self.selected_armor = mode, item
                else:
                    raise ValueError("unknown item")
            enabled = set(data.get("enabled", []))
            family = self._material_family()
            saved_material = data.get("material", "")
            if family and any(entry[0] == saved_material for entry in CRAFT_MATERIALS.get(family, [])):
                self.selected_material[family] = saved_material
                self._save_text("JCS_CIM_Material_" + family, saved_material)
            for name, _c, _p, _d in self._current_library():
                self.recipe_enabled[name] = name in enabled
                self._save_int("JCS_CIM_Enable_" + name, 1 if name in enabled else 0)
            for name, value in data.get("targets", {}).items():
                if name in self.recipe_targets:
                    self.recipe_targets[name] = max(PROPERTY_MIN.get(name, 2), min(self._property_max(name), int(value)))
                    self._save_int("JCS_CIM_Target_" + name, self.recipe_targets[name])
            action = "Build applied to " + self._selected_item_name() if preserve_item else "Template loaded: " + item
            self._set_status(action, 68)
            return True
        except Exception:
            self._set_status("Template code is invalid or incompatible", 33)
            return False

    def save_current_template(self):
        template_name = self._textbox_value(self.template_name_box).strip()
        if not template_name:
            template_name = self._selected_item_name() + " Build"
        self.template_name_draft = template_name
        code = self._encode_template(template_name)
        slot = None
        for index in range(TEMPLATE_SLOTS):
            if not self._load_text("JCS_CIM_Template_" + str(index), ""):
                slot = index
                break
        if slot is None:
            slot = self.selected_template_slot
        self.selected_template_slot = slot
        self._save_text("JCS_CIM_Template_" + str(slot), code)
        if self.template_box:
            try:
                self.template_box.SetText(code)
            except Exception:
                pass
        API.SysMsg("Template saved in slot {} with exact intensities.".format(slot + 1), 68)
        if self.screen == "templates":
            self.template_page = slot // TEMPLATES_PER_PAGE
            self.build_ui()

    def load_saved_template(self):
        self.screen = "templates"
        self.build_ui()

    def select_template_slot(self, slot):
        self.selected_template_slot = int(slot)
        self.build_ui()

    def change_template_page(self, delta):
        typed = self._textbox_value(self.template_name_box).strip()
        if typed:
            self.template_name_draft = typed
        pages = max(1, (TEMPLATE_SLOTS + TEMPLATES_PER_PAGE - 1) // TEMPLATES_PER_PAGE)
        self.template_page = (self.template_page + int(delta)) % pages
        self.build_ui()

    def delete_template_slot(self, slot):
        self.selected_template_slot = int(slot)
        self.delete_selected_template()

    def _selected_template_code(self):
        return self._load_text("JCS_CIM_Template_" + str(self.selected_template_slot), "")

    def load_exact_template(self):
        if self._apply_template_code(self._selected_template_code(), False):
            self.screen = "imbues"
            self.build_ui()

    def apply_template_to_current_item(self):
        if self._apply_template_code(self._selected_template_code(), True):
            self.screen = "imbues"
            self.build_ui()

    def delete_selected_template(self):
        self._save_text("JCS_CIM_Template_" + str(self.selected_template_slot), "")
        self.build_ui()

    def export_selected_template(self):
        code = self._selected_template_code()
        if self.template_box:
            try:
                self.template_box.SetText(code)
            except Exception:
                pass

    def open_template_job(self, slot):
        self.selected_template_slot = int(slot)
        code = self._selected_template_code()
        if not self._apply_template_code(code, False):
            return
        self.batch_material_family = self._material_family()
        source = ARMOR_CRAFT if self.item_mode == "armor" else WEAPON_CRAFT
        compatible = [name for name, craft in source.items() if self._craft_family_for(craft) == self.batch_material_family]
        self.batch_quantities = dict((name, 0) for name in compatible)
        self.batch_quantities[self._selected_item_name()] = 1
        self.batch_page = 0
        self.batch_preview_ok = False
        self.batch_preview_lines = []
        # First show the saved imbues and intensities. The user can adjust this
        # job without silently changing the stored template.
        self.template_job_mode = True
        self.screen = "imbues"
        self.build_ui()

    def continue_template_job(self):
        self.screen = "batch"
        self.build_ui()

    def open_templates(self):
        self.template_job_mode = False
        if not self.template_name_draft:
            self.template_name_draft = self._selected_item_name() + " Build"
        self.screen = "templates"
        self.build_ui()

    def adjust_batch_quantity(self, name, delta):
        self.batch_quantities[name] = max(0, min(100, self.batch_quantities.get(name, 0) + int(delta)))
        self.batch_preview_ok = False
        self.batch_preview_lines = []
        self.build_ui()

    def _batch_selected(self):
        return [(name, qty) for name, qty in self.batch_quantities.items() if int(qty) > 0]

    def _craft_family_for(self, craft):
        kind = craft.get("tool", "smith")
        if kind == "tailoring":
            return "leather"
        if kind in ("smith", "tinker"):
            return "metal"
        if kind == "fletching":
            return "wood"
        return ""

    def preview_batch_materials(self):
        selected = self._batch_selected()
        if not selected:
            self._set_status("Select at least one item and quantity", 33)
            return
        required = {}
        missing_tools = []
        old_weapon, old_armor = self.selected_weapon, self.selected_armor
        for item_name, quantity in selected:
            if self.item_mode == "armor":
                self.selected_armor = item_name
            else:
                self.selected_weapon = item_name
            craft = self._current_craft()
            if not self._can_supply_tool(self._craft_tool_kind()):
                missing_tools.append(item_name)
            material = self._material_entry()
            resource = material[2] if material else craft.get("resource", "Iron Ingot")
            amount = int(craft.get("amount", craft.get("ingots", 0)))
            required[resource] = required.get(resource, 0) + amount * int(quantity) * 3
            for name, count in self._required_resources(
                self._active_recipe(), IMBUE_RETRY_RESERVE
            ).items():
                required[name] = required.get(name, 0) + count * int(quantity)
        self.selected_weapon, self.selected_armor = old_weapon, old_armor

        chest = self._open_resource_chest() if self.resource_chest else None
        lines = []
        all_ok = bool(chest) and not missing_tools
        if not chest:
            lines.append("MISSING: accessible resource chest")
        if missing_tools:
            lines.append("MISSING TOOLS: " + ", ".join(missing_tools))
        for name in sorted(required.keys()):
            need = required[name]
            have = self._count_resource(API.Backpack, name)
            if chest:
                have += self._count_resource(chest, name)
            ok = have >= need
            all_ok = all_ok and ok
            lines.append("{}  {}/{}{}".format(name, have, need, "" if ok else "  MISSING"))
        self.batch_preview_lines = lines
        self.batch_preview_ok = all_ok
        self.status = "Batch material check passed" if all_ok else "Batch check found missing requirements"
        API.SysMsg(self.status, 68 if all_ok else 33)
        self.screen = "batch_review"
        self.build_ui()

    def start_batch_production(self):
        if self.busy:
            return
        if not self.batch_preview_ok:
            self._set_status("Run the batch PREVIEW before production", 33)
            return
        selected = self._batch_selected()
        self.busy = True
        self.track_batch_pulls = True
        self.batch_pull_baseline = {}
        self.batch_pulled_resources = {}
        self.build_ui()
        completed = 0
        try:
            for item_name, quantity in selected:
                if self.item_mode == "armor":
                    self.selected_armor = item_name
                else:
                    self.selected_weapon = item_name
                for number in range(1, int(quantity) + 1):
                    if completed and completed % 2 == 0:
                        self._set_status(
                            "Batch recovery pause after {} pieces".format(completed),
                            53,
                        )
                        self._stabilize_client(6.0)
                    self._stabilize_client(0.75)
                    self._set_status("Batch: {} {}/{}".format(item_name, number, quantity), 68)
                    item, message = self._craft_exceptional_weapon()
                    if not item:
                        self._set_status("Stopped: " + message, 33)
                        return
                    # Crafting can leave several gump replies queued. Close the
                    # crafting menu and let the new item/tooltip settle before
                    # switching the same client into the Imbuing workflow.
                    self._stabilize_client(2.50)
                    ok, error = self._imbue_item(item)
                    if not ok:
                        self._set_status("Stopped: " + error, 33)
                        return
                    self._deposit_finished_item(item)
                    completed += 1
                    # Give the client/server queues time to settle before a new
                    # craft gump is opened. Long batches otherwise accumulate
                    # stale targets and gump replies and can eventually desync.
                    self._stabilize_client(1.50)
            self.batch_preview_ok = False
            self._set_status("Batch complete: {} finished items".format(completed), 68)
        finally:
            returned, return_errors = self._return_batch_resources()
            self.track_batch_pulls = False
            if returned:
                summary = ", ".join(
                    "{} x{}".format(name, amount)
                    for name, amount in sorted(returned.items())
                )
                API.SysMsg("Returned unused batch resources: " + summary, 68)
            if return_errors:
                API.SysMsg(
                    "Could not return: " + ", ".join(return_errors), 33
                )
            self.busy = False
            self.build_ui()

    def import_template_box(self):
        code = self._textbox_value(self.template_box)
        if self._apply_template_code(code):
            slot = None
            for index in range(TEMPLATE_SLOTS):
                if not self._load_text("JCS_CIM_Template_" + str(index), ""):
                    slot = index
                    break
            if slot is None:
                slot = self.selected_template_slot
            self._save_text("JCS_CIM_Template_" + str(slot), code)
            self.screen = "imbues"
            self.build_ui()

    def _wait_gump(self, gump_id, timeout=5.0):
        steps = max(1, int(float(timeout) / 0.10))
        for _ in range(steps):
            if API.StopRequested or not self.running:
                return False
            try:
                if API.HasGump(gump_id):
                    return True
            except Exception:
                pass
            API.ProcessCallbacks()
            API.Pause(0.10)
        return False

    def _reply(self, button, gump_id, settle=0.35):
        try:
            API.ReplyGump(int(button), int(gump_id))
            API.Pause(float(settle))
            return True
        except Exception:
            return False

    def _stabilize_client(self, settle=1.0):
        """Clear stale server UI state and allow queued packets to drain."""
        try:
            API.CancelTarget()
        except Exception:
            pass
        for gump_id in (
            SMITH_GUMP,
            IMBUE_CONFIRM_GUMP,
            IMBUE_PROPERTY_GUMP,
            IMBUE_MAIN_GUMP,
        ):
            try:
                if API.HasGump(gump_id):
                    API.CloseGump(gump_id)
            except Exception:
                pass
        steps = max(1, int(float(settle) / 0.10))
        for _ in range(steps):
            API.ProcessCallbacks()
            API.Pause(0.10)

    def _backpack_items(self):
        try:
            return list(API.ItemsInContainer(API.Backpack, True) or [])
        except Exception:
            return []

    def _backpack_serials(self):
        return set(self._serial(item) for item in self._backpack_items())

    def _item_text(self, item):
        try:
            return str(item.NameAndProps(True, 3) or "")
        except Exception:
            return ""

    def _new_selected_item(self, before):
        wanted = self._current_craft()["match"]
        candidates = []
        for item in self._backpack_items():
            serial = self._serial(item)
            if not serial or serial in before:
                continue
            text = self._item_text(item)
            if wanted in text.lower():
                candidates.append((item, text))
        return candidates

    def _wait_new_item(self, before, timeout=4.0):
        """Allow the server, backpack, and tooltip state to settle after crafting."""
        steps = max(1, int(float(timeout) / 0.20))
        for _ in range(steps):
            found = self._new_selected_item(before)
            if found:
                return found
            API.ProcessCallbacks()
            API.Pause(0.20)
        return []

    def _craft_tool_kind(self):
        return self._current_craft().get("tool", "smith")

    def _current_craft(self):
        return ARMOR_CRAFT[self.selected_armor] if self.item_mode == "armor" else WEAPON_CRAFT[self.selected_weapon]

    def _material_family(self):
        kind = self._current_craft().get("tool", "smith")
        if kind == "tailoring":
            return "leather"
        if kind in ("smith", "tinker"):
            return "metal"
        if kind == "fletching":
            return "wood"
        return ""

    def _material_entry(self):
        family = self._material_family()
        choices = CRAFT_MATERIALS.get(family, [])
        selected = self.selected_material.get(family, "")
        for entry in choices:
            if entry[0] == selected:
                return entry
        return choices[0] if choices else None

    def choose_material(self, family, name):
        self.selected_material[str(family)] = str(name)
        self._save_text("JCS_CIM_Material_" + str(family), name)
        self.preview_ok = False
        self.batch_preview_ok = False
        self.screen = "imbues"
        self._set_status("Crafting material: " + name, 68)

    def open_materials(self):
        if not self._material_family():
            self._set_status("Special material mapping is not available for this craft type yet", 33)
            return
        self.screen = "materials"
        self.build_ui()

    def _selected_item_name(self):
        return self.selected_armor if self.item_mode == "armor" else self.selected_weapon

    def _craft_tool_serial(self):
        kind = self._craft_tool_kind()
        if kind == "tinker":
            return self.tinker_tool
        if kind == "fletching":
            return self.fletching_tool
        if kind == "tailoring":
            return self.tailoring_tool
        return self.smith_tool

    def select_craft_tool(self):
        if self.busy:
            return
        kind = self._craft_tool_kind()
        if kind == "tinker":
            label = "tinkering tool"
        elif kind == "fletching":
            label = "fletcher's tools"
        elif kind == "tailoring":
            label = "sewing kit"
        else:
            label = "smith hammer/tongs"
        API.SysMsg("Target the {} used to craft.".format(label), 68)
        target = API.RequestTarget()
        serial = self._serial(target)
        if not serial:
            self._set_status("Craft tool selection cancelled", 33)
            return
        if kind == "tinker":
            self.tinker_tool = serial
            self._save_int("JCS_CIM_TinkerTool", serial)
            self._set_status("Tinkering tool saved")
        elif kind == "fletching":
            self.fletching_tool = serial
            self._save_int("JCS_CIM_FletchingTool", serial)
            self._set_status("Fletching tool saved")
        elif kind == "tailoring":
            self.tailoring_tool = serial
            self._save_int("JCS_CIM_TailoringTool", serial)
            self._set_status("Tailoring tool saved")
        else:
            self.smith_tool = serial
            self._save_int("JCS_CIM_SmithTool", serial)
            self._set_status("Smith tool saved")

    def select_resource_chest(self):
        if self.busy:
            return
        API.SysMsg("Target the secure chest holding crafting and imbuing resources.", 68)
        target = API.RequestTarget()
        serial = self._serial(target)
        if not serial:
            self._set_status("Resource chest selection cancelled", 33)
            return
        self.resource_chest = serial
        self._save_int("JCS_CIM_ResourceChest", serial)
        self._set_status("Secure resource chest saved")

    def select_finished_container(self):
        if self.busy:
            return
        API.SysMsg("Target the container for completed products.", 68)
        target = API.RequestTarget()
        serial = self._serial(target)
        if not serial:
            self._set_status("Finished-product container selection cancelled", 33)
            return
        self.finished_container = serial
        self._save_int("JCS_CIM_FinishedContainer", serial)
        self._set_status("Finished-product container saved", 68)

    def select_setup_tool(self, kind):
        if self.busy:
            return
        details = {
            "smith": ("smith hammer/tongs", "smith_tool", "JCS_CIM_SmithTool"),
            "tailoring": ("sewing kit", "tailoring_tool", "JCS_CIM_TailoringTool"),
            "tinker": ("tinkering tool", "tinker_tool", "JCS_CIM_TinkerTool"),
            "fletching": ("fletcher's tools", "fletching_tool", "JCS_CIM_FletchingTool"),
        }
        label, attribute, key = details[str(kind)]
        API.SysMsg("Target the {} used to craft.".format(label), 68)
        target = API.RequestTarget()
        serial = self._serial(target)
        if not serial:
            self._set_status("{} selection cancelled".format(label.title()), 33)
            return
        setattr(self, attribute, serial)
        self._save_int(key, serial)
        self._set_status("{} saved".format(label.title()), 68)

    def auto_detect_tools(self, announce=True):
        found = []
        missing = []
        for kind in ("tinker", "smith", "tailoring", "fletching"):
            tools = self._tool_items(kind)
            if tools:
                self._save_tool_serial(kind, self._serial(tools[0]))
                found.append(TOOL_RECIPES[kind][0])
            else:
                missing.append(TOOL_RECIPES[kind][0])
        if announce:
            if found:
                API.SysMsg("Auto-detected: " + ", ".join(found), 68)
            if missing:
                API.SysMsg("Not currently in backpack: " + ", ".join(missing), 53)
            self.status = "Detected {} of 4 crafting tool types".format(len(found))
            self.build_ui()
        return found

    def detect_setup_tool(self, kind):
        tools = self._tool_items(kind)
        if not tools:
            self._set_status(
                "No {} found in the backpack".format(TOOL_RECIPES[str(kind)][0]),
                33,
            )
            return
        self._save_tool_serial(kind, self._serial(tools[0]))
        self._set_status("Auto-detected " + TOOL_RECIPES[str(kind)][0], 68)

    def _setup_ready(self):
        tools = (
            self.smith_tool,
            self.tailoring_tool,
            self.tinker_tool,
            self.fletching_tool,
        )
        return bool(self.resource_chest and any(tools))

    def finish_setup(self):
        if not self._setup_ready():
            self._set_status(
                "Setup needs a resource chest and at least one crafting tool",
                33,
            )
            return
        self._save_int("JCS_CIM_SetupComplete", 1)
        self.screen = "select"
        self._set_status("Setup ready - choose what to craft", 68)

    def toggle_property(self, name):
        if self.busy:
            return
        enabling = not self.recipe_enabled.get(name, False)
        if enabling:
            group = PROPERTY_GROUP.get(name)
            if group:
                for other, other_group in PROPERTY_GROUP.items():
                    if other != name and other_group == group and self.recipe_enabled.get(other, False):
                        self.recipe_enabled[other] = False
                        self._save_int("JCS_CIM_Enable_" + other, 0)
            selected = sum(
                1 for entry in self._current_library()
                if self.recipe_enabled.get(entry[0], False)
            )
            limit = 4 if self.item_mode == "weapon" else 5
            if selected >= limit:
                self._set_status("This item mode allows {} selected imbues; turn one off first".format(limit), 33)
                return
        self.recipe_enabled[name] = not self.recipe_enabled.get(name, True)
        self._save_int("JCS_CIM_Enable_" + name, 1 if self.recipe_enabled[name] else 0)
        self.build_ui()

    def adjust_property(self, name, delta):
        if self.busy:
            return
        value = self.recipe_targets.get(name, 2) + int(delta)
        minimum = PROPERTY_MIN.get(name, 2)
        self.recipe_targets[name] = max(minimum, min(self._property_max(name), value))
        self._save_int("JCS_CIM_Target_" + name, self.recipe_targets[name])
        # Updating only this text control avoids closing and recreating the
        # entire gump for every single percentage click.
        label = self.target_labels.get(name)
        if label:
            try:
                label.SetText(self._value_text(name, self.recipe_targets[name]))
                meter = self.target_meters.get(name)
                if meter:
                    ratio = float(self.recipe_targets[name]) / float(self._property_max(name))
                    meter.SetRect(64, meter.GetY(), max(2, int(220 * ratio)), 3)
            except Exception:
                self.build_ui()

    def change_property_page(self, delta):
        if self.busy:
            return
        rows_per_page = 8
        library = self._current_library()
        page_count = max(1, (len(library) + rows_per_page - 1) // rows_per_page)
        self.property_page = (self.property_page + int(delta)) % page_count
        self.build_ui()

    def toggle_item_mode(self):
        if self.busy:
            return
        self.item_mode = "armor" if self.item_mode == "weapon" else "weapon"
        self.property_page = 0
        if self.item_mode == "armor":
            self._set_status("Armor recipe mode", 53)
        else:
            self._set_status("Weapon recipe mode", 53)

    def cycle_weapon(self):
        if self.busy:
            return
        if self.item_mode == "armor":
            names = list(ARMOR_CRAFT.keys())
            index = names.index(self.selected_armor) if self.selected_armor in names else 0
            self.selected_armor = names[(index + 1) % len(names)]
            self._save_text("JCS_CIM_SelectedArmor", self.selected_armor)
            self._set_status("Selected armor: " + self.selected_armor, 53)
        else:
            names = list(WEAPON_CRAFT.keys())
            index = names.index(self.selected_weapon) if self.selected_weapon in names else 0
            self.selected_weapon = names[(index + 1) % len(names)]
            self._save_text("JCS_CIM_SelectedWeapon", self.selected_weapon)
            for leech in ("Hit Mana Leech", "Hit Life Leech"):
                self.recipe_targets[leech] = min(self.recipe_targets.get(leech, 2), self._property_max(leech))
            self._set_status("Selected weapon: " + self.selected_weapon, 53)

    def _property_max(self, name):
        if self.item_mode == "weapon" and name in ("Hit Mana Leech", "Hit Life Leech"):
            return int(WEAPON_CRAFT[self.selected_weapon]["leech_max"])
        return int(PROPERTY_MAX[name])

    def _value_text(self, name, value):
        if name in PROPERTY_FIXED:
            return "YES" if int(value) else "NO"
        return str(int(value)) if name in PROPERTY_FLAT else str(int(value)) + "%"

    def _property_value(self, text, name):
        if name in PROPERTY_FIXED:
            return 1 if re.search(re.escape(name), text or "", re.IGNORECASE) else 0
        match = re.search(
            re.escape(name) + r"\s+(\d+)\s*%?",
            text or "",
            re.IGNORECASE,
        )
        return int(match.group(1)) if match else 0

    def _remember_item_graphic(self, item):
        try:
            graphic = int(item.Graphic)
        except Exception:
            return
        craft = self._current_craft()
        craft["graphic"] = graphic
        self._save_int("JCS_CIM_Icon_" + self._selected_item_name(), graphic)

    def learn_selected_icon(self):
        if self.busy:
            return
        API.SysMsg("Target a {} to learn its exact in-game icon.".format(self._selected_item_name()), 68)
        target = API.RequestTarget()
        item = API.FindItem(self._serial(target)) if target else None
        text = self._item_text(item) if item else ""
        if not item or self._current_craft()["match"] not in text.lower():
            self._set_status("That target is not a " + self._selected_item_name(), 33)
            return
        self._remember_item_graphic(item)
        self._set_status("Exact icon learned for " + self._selected_item_name(), 68)

    def _current_library(self):
        return ARMOR_RECIPE if self.item_mode == "armor" else WEAPON_RECIPE

    def _active_recipe(self):
        result = []
        for name, category, prop, _default in self._current_library():
            if not self.recipe_enabled.get(name, True):
                continue
            if name in PROPERTY_FIXED:
                target = 1
            else:
                target = min(
                    self.recipe_targets.get(name, PROPERTY_MIN.get(name, 2)),
                    self._property_max(name),
                )
            result.append((name, category, prop, target))
        return result

    def _resource_name(self, item):
        text = self._item_text(item)
        if not text:
            try:
                text = str(item.Name or "")
            except Exception:
                text = ""
        first = text.splitlines()[0].strip().lower() if text else ""
        first = re.sub(r"\s*\[\s*\d+\s*\]\s*$", "", first)
        first = re.sub(r"^\s*\d+\s+", "", first)
        return re.sub(r"\s+", " ", first).strip()

    def _resource_amount(self, item):
        try:
            return max(1, int(item.Amount or 1))
        except Exception:
            return 1

    def _resource_matches(self, item, wanted):
        name = self._resource_name(item)
        wanted = re.sub(r"\s+", " ", str(wanted).lower()).strip()
        name = name.rstrip("s")
        wanted = wanted.rstrip("s")
        # Some Legion item tooltips expose a plain iron stack as "Ingots"
        # instead of "Iron Ingots". Both names refer to the base metal stack.
        if wanted == "iron ingot" and name in ("ingot", "iron ingot"):
            return True
        if wanted == "iron ingot":
            try:
                if int(item.Graphic) == 0x1BF2 and int(item.Hue) == 0:
                    return True
            except Exception:
                pass
        if wanted == "leather" and name in ("leather", "hide"):
            return True
        if wanted == "leather":
            try:
                # 0x1081 is the stackable cut-leather resource. Hides are
                # also accepted by name when Legion exposes them that way.
                if int(item.Graphic) == 0x1081 and int(item.Hue) == 0:
                    return True
            except Exception:
                pass
        return name == wanted

    def _open_resource_chest(self):
        if not self.resource_chest:
            return None
        try:
            chest = API.FindItem(self.resource_chest)
        except Exception:
            chest = None
        if not chest:
            return None
        try:
            API.UseObject(self.resource_chest)
            API.Pause(0.60)
        except Exception:
            return None
        return chest

    def _count_resource(self, container, wanted):
        try:
            items = list(API.ItemsInContainer(container, True) or [])
        except Exception:
            items = []
        return sum(self._resource_amount(item) for item in items if self._resource_matches(item, wanted))

    def _pull_resource(self, wanted, amount):
        amount = int(amount)
        have = self._count_resource(API.Backpack, wanted)
        if self.track_batch_pulls and wanted not in self.batch_pull_baseline:
            self.batch_pull_baseline[wanted] = have
        deficit = max(0, amount - have)
        if deficit <= 0:
            return True
        chest = self._open_resource_chest()
        if not chest:
            return False

        try:
            items = list(API.ItemsInContainer(chest, True) or [])
        except Exception:
            items = []

        for item in items:
            if deficit <= 0:
                break
            if not self._resource_matches(item, wanted):
                continue
            available = self._resource_amount(item)
            move = min(deficit, available)
            try:
                # Use the source stack's actual weight to avoid staging enough
                # resources to overload the character. Keep a working margin
                # for crafted products and tools.
                free_weight = self._free_weight()
                stack_weight = float(getattr(item, "Weight", 0) or 0)
                unit_weight = stack_weight / float(max(1, available))
                if unit_weight > 0:
                    weight_limit = int(free_weight / unit_weight)
                    move = min(move, max(0, weight_limit))
                if move <= 0:
                    API.SysMsg(
                        "Weight guard: not enough carrying capacity for " + wanted,
                        33,
                    )
                    break
                before = self._count_resource(API.Backpack, wanted)
                API.MoveItem(self._serial(item), API.Backpack, move)
                API.Pause(0.35)
                after = self._count_resource(API.Backpack, wanted)
                gained = max(0, after - before)
                deficit -= gained
                if self.track_batch_pulls and gained:
                    self.batch_pulled_resources[wanted] = (
                        self.batch_pulled_resources.get(wanted, 0) + gained
                    )
            except Exception:
                pass
        return self._count_resource(API.Backpack, wanted) >= amount

    def _free_weight(self):
        try:
            current = float(API.Player.Weight or 0)
            maximum = float(API.Player.WeightMax or 0)
            if maximum > 0:
                return max(0.0, maximum - current - WEIGHT_SAFETY_MARGIN)
        except Exception:
            pass
        return 1000.0

    def _tool_items(self, kind):
        kind = str(kind)
        known_graphics = TOOL_GRAPHICS.get(kind, ())
        serial_mapping = {
            "tinker": self.tinker_tool,
            "smith": self.smith_tool,
            "tailoring": self.tailoring_tool,
            "fletching": self.fletching_tool,
        }
        saved_serial = int(serial_mapping.get(kind, 0) or 0)
        saved_graphic = self._load_int("JCS_CIM_ToolGraphic_" + kind, 0)
        saved_item = API.FindItem(saved_serial) if saved_serial else None
        if saved_item:
            try:
                saved_graphic = int(saved_item.Graphic)
                self._save_int("JCS_CIM_ToolGraphic_" + kind, saved_graphic)
            except Exception:
                pass

        found = []
        for item in self._backpack_items():
            serial = self._serial(item)
            try:
                graphic = int(item.Graphic)
            except Exception:
                graphic = 0
            if (
                serial == saved_serial
                or (saved_graphic and graphic == saved_graphic)
                or graphic in known_graphics
            ):
                found.append(item)
        return found

    def _save_tool_serial(self, kind, serial):
        mapping = {
            "tinker": ("tinker_tool", "JCS_CIM_TinkerTool"),
            "smith": ("smith_tool", "JCS_CIM_SmithTool"),
            "tailoring": ("tailoring_tool", "JCS_CIM_TailoringTool"),
            "fletching": ("fletching_tool", "JCS_CIM_FletchingTool"),
        }
        attribute, key = mapping[str(kind)]
        setattr(self, attribute, int(serial))
        self._save_int(key, serial)
        item = API.FindItem(int(serial))
        if item:
            try:
                self._save_int(
                    "JCS_CIM_ToolGraphic_" + str(kind), int(item.Graphic)
                )
            except Exception:
                pass

    def _craft_replacement_tool(self, kind):
        tinkers = self._tool_items("tinker")
        if not tinkers:
            return False
        # Keep enough ordinary iron available for any of the mapped tools.
        if not self._pull_resource("Iron Ingot", 10):
            return False
        before = self._backpack_serials()
        tinker_serial = self._serial(tinkers[0])
        try:
            API.UseObject(tinker_serial)
        except Exception:
            return False
        if not self._wait_gump(SMITH_GUMP, 5.0):
            return False
        for button in TOOL_RECIPES[str(kind)][1]:
            self._reply(button, SMITH_GUMP, 0.60)
            if not self._wait_gump(SMITH_GUMP, 5.0):
                return False
        new_items = [
            item for item in self._tool_items(kind)
            if self._serial(item) not in before
        ]
        if not new_items:
            return False
        self._save_tool_serial(kind, self._serial(new_items[0]))
        API.SysMsg("Crafted replacement {}.".format(TOOL_RECIPES[str(kind)][0]), 68)
        try:
            if API.HasGump(SMITH_GUMP):
                API.CloseGump(SMITH_GUMP)
        except Exception:
            pass
        API.Pause(1.00)
        return True

    def _ensure_tool_supply(self, needed_kind):
        tinkers = self._tool_items("tinker")
        if not tinkers:
            return False, "Keep at least one tinkering tool in the backpack to start tool upkeep"
        self._save_tool_serial("tinker", self._serial(tinkers[0]))
        while len(self._tool_items("tinker")) < 2:
            if not self._craft_replacement_tool("tinker"):
                return False, "Could not maintain the two-tool tinkering reserve"
        tools = self._tool_items(needed_kind)
        if not tools:
            if not self._craft_replacement_tool(needed_kind):
                return False, "Could not craft replacement " + TOOL_RECIPES[needed_kind][0]
            tools = self._tool_items(needed_kind)
            # Crafting another tool may consume the active tinkering tool's
            # final charge, so restore the two-tool safety reserve immediately.
            while len(self._tool_items("tinker")) < 2:
                if not self._craft_replacement_tool("tinker"):
                    return False, "Could not restore the two-tool tinkering reserve"
        if not tools:
            return False, "Replacement tool was not found in the backpack"
        self._save_tool_serial(needed_kind, self._serial(tools[0]))
        return True, ""

    def _can_supply_tool(self, kind):
        if self._tool_items(kind):
            return True
        return bool(self._tool_items("tinker"))

    def _deposit_finished_item(self, item):
        if not self.finished_container:
            return True
        container = API.FindItem(self.finished_container)
        if not container:
            API.SysMsg("Finished container is inaccessible; item kept in backpack.", 33)
            return False
        try:
            API.UseObject(self.finished_container)
            API.Pause(0.40)
            API.MoveItem(self._serial(item), self.finished_container, 1)
            API.Pause(0.50)
            return True
        except Exception:
            API.SysMsg("Could not move finished item; it remains in the backpack.", 33)
            return False

    def _return_batch_resources(self):
        """Return only unused resources pulled for this production run."""
        returned = {}
        errors = []
        if not self.batch_pulled_resources:
            return returned, errors
        chest = self._open_resource_chest()
        if not chest:
            return returned, ["resource chest inaccessible"]

        for wanted, pulled in sorted(self.batch_pulled_resources.items()):
            baseline = self.batch_pull_baseline.get(wanted, 0)
            current = self._count_resource(API.Backpack, wanted)
            remaining = min(int(pulled), max(0, current - baseline))
            to_return = remaining
            if to_return <= 0:
                continue
            try:
                items = list(API.ItemsInContainer(API.Backpack, True) or [])
            except Exception:
                items = []
            for item in items:
                if remaining <= 0:
                    break
                if not self._resource_matches(item, wanted):
                    continue
                move = min(remaining, self._resource_amount(item))
                try:
                    API.MoveItem(self._serial(item), self.resource_chest, move)
                    API.Pause(0.35)
                    remaining -= move
                except Exception:
                    pass
            moved = to_return - remaining
            if moved:
                returned[wanted] = moved
            if remaining:
                errors.append("{} x{}".format(wanted, remaining))
        return returned, errors

    def _required_resources(self, recipe, attempts=1):
        required = {}
        attempts = max(1, int(attempts))
        for name, _category, _prop, target in recipe:
            maximum = float(self._property_max(name))
            ratio = max(0.0, min(1.0, float(target) / maximum))
            primary_count = max(1, int((ratio * 5.0) + 0.999))
            gem_count = max(1, int((ratio * 10.0) + 0.999))
            primary, gem, special = PROPERTY_RESOURCES[name]
            required[primary] = required.get(primary, 0) + primary_count * attempts
            required[gem] = required.get(gem, 0) + gem_count * attempts
            if ratio > 0.90:
                special_count = max(1, int((((ratio - 0.90) / 0.10) * 10.0) + 0.999))
                required[special] = required.get(special, 0) + special_count
        return required

    def _ensure_recipe_resources(self, recipe, attempts=1):
        required = self._required_resources(recipe, attempts)
        needs_chest = any(
            self._count_resource(API.Backpack, name) < amount
            for name, amount in required.items()
        )
        if needs_chest and not self._open_resource_chest():
            return ["resource chest is inaccessible or out of range"]

        missing = []
        for name, amount in required.items():
            if not self._pull_resource(name, amount):
                missing.append("{} x{}".format(name, amount))
        return missing

    def preview_materials(self):
        """Read-only recommended-reserve check; never moves or consumes items."""
        craft = self._current_craft()
        quantity = int(self.production_qty)
        required = {}
        material = self._material_entry()
        craft_resource = material[2] if material else craft.get("resource", "Iron Ingot")
        craft_amount = int(craft.get("amount", craft.get("ingots", 0)))
        # Three craft attempts per requested exceptional item is a practical
        # reserve estimate. Production can still need more on a bad streak.
        required[craft_resource] = craft_amount * quantity * 3
        imbue_required = self._required_resources(
            self._active_recipe(), IMBUE_RETRY_RESERVE
        )
        for name, amount in imbue_required.items():
            required[name] = required.get(name, 0) + amount * quantity

        chest = self._open_resource_chest() if self.resource_chest else None
        lines = []
        all_ok = self._can_supply_tool(self._craft_tool_kind())
        if not all_ok:
            lines.append("MISSING: crafting tool")
        if not chest:
            lines.append("MISSING: accessible resource chest")
            all_ok = False
        for name in sorted(required.keys()):
            need = required[name]
            have = self._count_resource(API.Backpack, name)
            if chest:
                have += self._count_resource(chest, name)
            ok = have >= need
            all_ok = all_ok and ok
            lines.append("{}  {}/{}{}".format(name, have, need, "" if ok else "  MISSING"))
        self.preview_lines = lines
        self.preview_ok = all_ok
        self.status = "Material check passed" if all_ok else "Material check found missing requirements"
        API.SysMsg(self.status, 68 if all_ok else 33)
        self.build_ui()

    def _open_craft_menu(self):
        ok, error = self._ensure_tool_supply(self._craft_tool_kind())
        if not ok:
            API.SysMsg(error, 33)
            return False
        # Never carry the tinkering tool-production menu into the requested
        # item's crafting workflow.
        try:
            if API.HasGump(SMITH_GUMP):
                API.CloseGump(SMITH_GUMP)
                API.Pause(0.75)
        except Exception:
            pass
        tool = self._craft_tool_serial()
        if not tool or not API.FindItem(tool):
            return False
        try:
            API.UseObject(tool)
        except Exception:
            return False
        return self._wait_gump(SMITH_GUMP)

    def _craft_weapon_once(self):
        craft = self._current_craft()
        item_name = self._selected_item_name()
        material = self._material_entry()
        resource = material[2] if material else craft.get("resource", "Iron Ingot")
        amount = int(craft.get("amount", craft.get("ingots", 0)))
        if not self._pull_resource(resource, amount):
            return None, "Need {} {} in backpack or the saved resource chest".format(amount, resource)
        before = self._backpack_serials()
        if not self._open_craft_menu():
            return None, "Crafting menu did not open"

        if material:
            self._reply(7, SMITH_GUMP)
            if not self._wait_gump(SMITH_GUMP):
                return None, "Material selection page did not open"
            self._reply(material[1], SMITH_GUMP)
            if not self._wait_gump(SMITH_GUMP):
                return None, "Could not select " + material[0]

        self._reply(craft["category"], SMITH_GUMP)
        if not self._wait_gump(SMITH_GUMP):
            return None, item_name + " crafting page did not open"

        self._reply(craft["button"], SMITH_GUMP, 0.75)
        if not self._wait_gump(SMITH_GUMP):
            return None, item_name + " craft response timed out"

        found = self._wait_new_item(before)
        if not found:
            return None, "No new {} found; check resources, skill, recipe, and tool charges".format(item_name)

        item, text = found[-1]
        self._remember_item_graphic(item)
        return item, text

    def _craft_exceptional_weapon(self, max_attempts=25):
        item_name = self._selected_item_name()
        for attempt in range(1, int(max_attempts) + 1):
            self._set_status("Crafting {} {}/{}".format(item_name, attempt, max_attempts))
            item, text = self._craft_weapon_once()
            if not item:
                return None, text
            if "exceptional" in text.lower():
                return item, "Exceptional {} crafted".format(item_name)
            API.SysMsg("Normal {} kept in backpack; trying again.".format(item_name), 53)
        return None, "No exceptional {} after {} attempts".format(item_name, max_attempts)

    def _gump_text(self, gump_id):
        gump = None
        try:
            gump = API.GetGump(gump_id)
        except Exception:
            pass
        if not gump:
            # Current Legion builds expose GetGump() without an ID even though
            # HasGump/ReplyGump accept one.
            try:
                gump = API.GetGump()
            except Exception:
                return ""

        raw = getattr(gump, "PacketGumpText", "") if gump else ""
        if isinstance(raw, (list, tuple)):
            return " | ".join(str(part) for part in raw)
        return str(raw or "")

    def _new_value(self):
        text = self._gump_text(IMBUE_CONFIRM_GUMP)
        flat = re.sub(r"<[^>]+>", " ", text)
        flat = re.sub(r"\s+", " ", flat)
        patterns = [
            r"New\s*Value\s*:?\s*(\d+)\s*%",
            r"New\s*Value\D{0,80}(\d+)\s*%",
        ]
        for pattern in patterns:
            match = re.search(pattern, flat, re.IGNORECASE)
            if match:
                return int(match.group(1))
        # PacketGumpText can omit the static "New Value" label on some client
        # builds. The adjustable value is the final integer percentage before
        # the Back/Imbue controls; success chance contains a decimal and is
        # intentionally excluded here.
        values = [int(value) for value in re.findall(r"(?<![\d.])(\d+)\s*%", flat)]
        return values[-1] if values else None

    def _open_imbue_property(self, serial, category_button, property_button):
        opened = False
        for attempt in range(2):
            # A successful imbue returns to the main menu. Reuse it instead of
            # toggling the Imbuing skill again and invalidating its next target.
            try:
                main_open = bool(API.HasGump(IMBUE_MAIN_GUMP))
            except Exception:
                main_open = False

            if not main_open:
                try:
                    API.UseSkill("Imbuing")
                except Exception:
                    return False, "Could not use Imbuing"
                if not self._wait_gump(IMBUE_MAIN_GUMP, 6.0):
                    return False, "Imbuing menu did not open"

            self._reply(IMBUE_ITEM, IMBUE_MAIN_GUMP, 0.50)
            try:
                if not API.WaitForTarget("any", 3.0):
                    raise RuntimeError("No target cursor")
                API.Target(int(serial))
                API.Pause(0.60)
            except Exception:
                if attempt == 0:
                    continue
                return False, "Imbuing target cursor failed"

            if self._wait_gump(IMBUE_PROPERTY_GUMP, 6.0):
                opened = True
                break

            # Clear a stale gump before the one allowed retry.
            if attempt == 0:
                try:
                    API.CloseGump()
                except Exception:
                    pass
                API.Pause(0.35)

        if not opened:
            return False, "Property menu did not open after retry"
        self._reply(category_button, IMBUE_PROPERTY_GUMP)
        if not self._wait_gump(IMBUE_PROPERTY_GUMP):
            return False, "Property category did not open"
        self._reply(property_button, IMBUE_PROPERTY_GUMP)
        if not self._wait_gump(IMBUE_CONFIRM_GUMP):
            return False, "Imbuing confirmation did not open"
        return True, ""

    def _set_intensity(self, name, target):
        """Set intensity using the recorded +1 control.

        The confirmation gump starts imbueable hit properties at 2%. On this
        client PacketGumpText exposes the static "Intensity: 2%" field but not
        the changing New Value control, so counting the recorded +1 action is
        more reliable than trying to scrape that display.
        """
        start_value = PROPERTY_MIN.get(name, 2)
        target = int(target)
        if target < start_value:
            return False, start_value

        current = start_value
        for _ in range(target - start_value):
            if not self._reply(INTENSITY_UP_ONE, IMBUE_CONFIRM_GUMP, 0.12):
                return False, current
            if not self._wait_gump(IMBUE_CONFIRM_GUMP, 1.5):
                return False, current
            current += 1
        return True, current

    def _imbue_property(self, serial, name, category, prop, target):
        ok, error = self._open_imbue_property(serial, category, prop)
        if not ok:
            return False, error

        if name not in PROPERTY_FIXED:
            exact, reached = self._set_intensity(name, target)
            if not exact:
                return False, "{} reached {} instead of {}".format(name, reached, target)

        self._reply(IMBUE_CONFIRM, IMBUE_CONFIRM_GUMP, 1.50)
        if not self._wait_gump(IMBUE_MAIN_GUMP):
            return False, "No result after imbuing {}".format(name)

        # Success is verified from the item tooltip, not merely from the gump returning.
        applied_value = self._wait_property_value(serial, name, target)
        if applied_value < int(target):
            return False, "{} {} was not applied; check materials or the property cap".format(name, self._value_text(name, target))
        return True, ""

    def _wait_property_value(self, serial, name, target, timeout=3.0):
        """Poll the live tooltip because properties can update after the gump."""
        best = 0
        steps = max(1, int(float(timeout) / 0.15))
        for _ in range(steps):
            item = API.FindItem(int(serial))
            text = self._item_text(item) if item else ""
            best = max(best, self._property_value(text, name))
            if best >= int(target):
                return best
            API.ProcessCallbacks()
            API.Pause(0.15)
        return best

    def _reimbue_last(self, serial, name, target):
        """Repeat the last failed imbue without rebuilding its value controls."""
        if not self._wait_gump(IMBUE_MAIN_GUMP, 1.0):
            API.UseSkill("Imbuing")
            if not self._wait_gump(IMBUE_MAIN_GUMP, 5.0):
                return False, "Imbuing menu did not open for Reimbue Last"
        if not self._reply(REIMBUE_LAST, IMBUE_MAIN_GUMP, 1.50):
            return False, "Reimbue Last could not be selected"
        if not self._wait_gump(IMBUE_MAIN_GUMP, 5.0):
            return False, "No result after Reimbue Last"
        applied_value = self._wait_property_value(serial, name, target)
        if applied_value < int(target):
            return False, "{} was not applied by Reimbue Last".format(name)
        return True, ""

    def _imbue_item(self, item):
        serial = self._serial(item)
        if not serial:
            return False, "Selected item could not be found"

        recipe = self._active_recipe()
        if not recipe:
            return False, "No imbue properties are selected"

        current_item = API.FindItem(serial)
        current_text = self._item_text(current_item) if current_item else ""
        pending = []
        for entry in recipe:
            name, _category, _prop, target = entry
            existing_value = self._property_value(current_text, name)
            if existing_value >= int(target):
                API.SysMsg("Already complete: {} {}".format(name, self._value_text(name, existing_value)), 53)
            else:
                pending.append(entry)

        if not pending:
            return True, ""

        missing = self._ensure_recipe_resources(pending)
        if missing:
            return False, "Missing resources: " + ", ".join(missing)

        for name, category, prop, target in pending:
            # Safely resume a partially completed weapon without spending
            # resources on properties that are already at the recipe value.
            current_item = API.FindItem(serial)
            current_text = self._item_text(current_item) if current_item else ""
            existing_value = self._property_value(current_text, name)
            if existing_value >= int(target):
                API.SysMsg("Already complete: {} {}".format(name, self._value_text(name, existing_value)), 53)
                continue

            # Pull a block of retry consumables once, before entering the fast
            # Reimbue Last loop. This avoids a chest round trip after every
            # failed low-percentage attempt. Any unused block is returned when
            # batch production finishes or stops.
            reserve_missing = self._ensure_recipe_resources(
                [(name, category, prop, target)], IMBUE_RETRY_RESERVE
            )
            if reserve_missing:
                return False, "Missing retry reserve for {}: {}".format(
                    name, ", ".join(reserve_missing)
                )
            API.SysMsg(
                "Staged {}-attempt reserve for {}.".format(
                    IMBUE_RETRY_RESERVE, name
                ),
                68,
            )

            completed = False
            last_error = "Unknown imbuing failure"
            for attempt in range(1, MAX_IMBUE_ATTEMPTS + 1):
                # Verify the live tooltip before every retry. This catches a
                # successful imbue even when the result gump returned stale or
                # incomplete text, preventing duplicate stat attempts.
                current_item = API.FindItem(serial)
                current_text = self._item_text(current_item) if current_item else ""
                existing_value = self._property_value(current_text, name)
                if existing_value >= int(target):
                    API.SysMsg("Verified complete: {} {}".format(name, self._value_text(name, existing_value)), 68)
                    completed = True
                    break
                # Failures can consume primary resources and gems. Recount the
                # backpack and pull only the consumed deficit before retrying.
                retry_entry = [(name, category, prop, target)]
                one_attempt = self._required_resources(retry_entry)
                reserve_empty = any(
                    self._count_resource(API.Backpack, resource) < amount
                    for resource, amount in one_attempt.items()
                )
                if reserve_empty:
                    retry_block = min(
                        IMBUE_RETRY_RESERVE,
                        MAX_IMBUE_ATTEMPTS - attempt + 1,
                    )
                    retry_missing = self._ensure_recipe_resources(
                        retry_entry, retry_block
                    )
                    if retry_missing:
                        return False, "Missing resources for {}: {}".format(
                            name, ", ".join(retry_missing)
                        )
                    API.SysMsg(
                        "Restaged {} attempts for {}.".format(
                            retry_block, name
                        ),
                        68,
                    )

                self._set_status(
                    "Imbuing {} {} - attempt {}/{}".format(
                        name, self._value_text(name, target), attempt, MAX_IMBUE_ATTEMPTS
                    )
                )
                if attempt == 1:
                    ok, last_error = self._imbue_property(
                        serial, name, category, prop, target
                    )
                else:
                    ok, last_error = self._reimbue_last(
                        serial, name, target
                    )
                if ok:
                    completed = True
                    break
                if attempt < MAX_IMBUE_ATTEMPTS:
                    API.SysMsg(
                        "{} failed; replenishing ingredients and retrying.".format(name),
                        53,
                    )
                    API.Pause(0.75)

            if not completed:
                return False, "{} failed after {} attempts: {}".format(
                    name, MAX_IMBUE_ATTEMPTS, last_error
                )
        return True, ""

    def imbue_existing_item(self):
        if self.busy:
            return

        prompt = (
            "Target an exceptional armor piece in your backpack."
            if self.item_mode == "armor"
            else "Target an exceptional {} in your backpack.".format(self.selected_weapon)
        )
        API.SysMsg(prompt, 68)
        target = API.RequestTarget()
        serial = self._serial(target)
        item = API.FindItem(serial) if serial else None
        if not item:
            self._set_status("Existing item selection cancelled", 33)
            return

        text = self._item_text(item)
        wanted = self._current_craft()["match"]
        if wanted not in text.lower():
            self._set_status("The selected item is not a " + self._selected_item_name(), 33)
            return
        if "exceptional" not in text.lower():
            self._set_status("Select an exceptional item; normal ones cannot hold this recipe", 33)
            return
        self._remember_item_graphic(item)

        self.busy = True
        self.build_ui()
        try:
            ok, error = self._imbue_item(item)
            if not ok:
                self._set_status("Stopped: " + error, 33)
                return
            selected_count = len(self._active_recipe())
            self._set_status("Existing item complete: {} properties selected".format(selected_count), 68)
        finally:
            self.busy = False
            self.build_ui()

    def start_production(self):
        if self.busy:
            return
        if not self.preview_ok:
            self._set_status("Run PREVIEW & CHECK MATERIALS before starting production", 33)
            return
        if not self._can_supply_tool(self._craft_tool_kind()):
            tool_kind = self._craft_tool_kind()
            kind = "tailoring" if tool_kind == "tailoring" else ("fletching" if tool_kind == "fletching" else ("tinkering" if tool_kind == "tinker" else "smith"))
            self._set_status("Select a {} tool first".format(kind), 33)
            return

        self.busy = True
        self.build_ui()
        try:
            for number in range(1, int(self.production_qty) + 1):
                API.SysMsg("Production item {}/{}".format(number, self.production_qty), 68)
                item, message = self._craft_exceptional_weapon()
                if not item:
                    self._set_status(message, 33)
                    return
                API.SysMsg(message, 68)
                ok, error = self._imbue_item(item)
                if not ok:
                    self._set_status("Stopped: " + error, 33)
                    return
                self._deposit_finished_item(item)
            selected_count = len(self._active_recipe())
            self.preview_ok = False
            self._set_status("Production complete: {} {} with {} properties".format(self.production_qty, self._selected_item_name(), selected_count), 68)
        finally:
            self.busy = False
            self.build_ui()

    def stop(self):
        self.running = False
        if self.ui:
            try:
                self.ui.Dispose()
            except Exception:
                pass

    def _label(self, text, x, y, width, color="#FFFFFF", size=12, align="left"):
        label = API.CreateGumpTTFLabel(text, size, color, "", align, width, False)
        label.SetRect(x, y, width, 22)
        self.ui.Add(label)
        return label

    def _button(self, text, x, y, width, callback, height=28):
        button = API.CreateSimpleButton(text, width, height)
        button.SetPos(x, y)
        self.ui.Add(button)
        API.AddControlOnClick(button, callback)

    def _build_editor(self):
        old = self.ui
        if old:
            try:
                if not old.IsDisposed:
                    self._remember_position()
            except Exception:
                pass
            try:
                old.Dispose()
            except Exception:
                pass

        self.ui = API.CreateGump(True, True, True)
        self.ui.SetRect(self.gump_x, self.gump_y, 540, 526)
        bg = API.CreateGumpColorBox(0.82, "#17120D")
        bg.SetRect(0, 0, 540, 526)
        self.ui.Add(bg)

        self._label(PRODUCT_NAME, 12, 10, 350, "#E7A65B", 16)
        # Keep release text clear of the save and close buttons.
        self._label(VERSION, 378, 13, 66, "#C8CCD4", 11, "right")
        tool_kind = self._craft_tool_kind()
        tool_serial = self._craft_tool_serial()
        tool_name = "Tailoring tool" if tool_kind == "tailoring" else ("Fletching tool" if tool_kind == "fletching" else ("Tinker tool" if tool_kind == "tinker" else "Smith tool"))
        tool_state = tool_name + (": saved" if tool_serial else ": not selected")
        self._label(tool_state, 12, 44, 220, "#72E39A" if tool_serial else "#FF7A7A", 12)
        chest_state = "Resource chest: saved" if self.resource_chest else "Resource chest: not selected"
        self._label(chest_state, 280, 44, 245, "#72E39A" if self.resource_chest else "#FF7A7A", 12)
        self._label(self.status[:70], 12, 72, 513, "#FFD166", 12)

        self._label("PROPERTY", 12, 101, 230, "#E7A65B", 11)
        self._label("TARGET", 374, 101, 82, "#E7A65B", 11, "center")
        rows_per_page = 8
        library = self._current_library()
        page_count = max(1, (len(library) + rows_per_page - 1) // rows_per_page)
        self.property_page = max(0, min(self.property_page, page_count - 1))
        start = self.property_page * rows_per_page
        visible_properties = library[start:start + rows_per_page]
        self.target_labels = {}
        self.target_meters = {}
        y = 125
        for name, _category, _prop, _default in visible_properties:
            enabled = self.recipe_enabled.get(name, True)
            self._button("ON" if enabled else "OFF", 12, y, 45, lambda n=name: self.toggle_property(n), 24)
            self._label(name, 64, y + 1, 245, "#FFFFFF" if enabled else "#777777", 12)
            meter_bg = API.CreateGumpColorBox(0.75, "#3A3A3A")
            meter_bg.SetRect(64, y + 23, 220, 3)
            self.ui.Add(meter_bg)
            meter = API.CreateGumpColorBox(0.95, "#4FC3F7")
            ratio = float(self.recipe_targets.get(name, 1)) / float(self._property_max(name))
            meter.SetRect(64, y + 23, max(2, int(220 * ratio)), 3)
            self.ui.Add(meter)
            self.target_meters[name] = meter
            if name in PROPERTY_FIXED:
                self._label("FIXED", 318, y + 1, 138, "#72E39A", 12, "center")
            else:
                self._button("-", 318, y, 32, lambda n=name: self.adjust_property(n, -1), 26)
                self.target_labels[name] = self._label(
                    self._value_text(name, self.recipe_targets[name]), 354, y + 1, 66, "#72E39A", 12, "center"
                )
                self._button("+", 424, y, 32, lambda n=name: self.adjust_property(n, 1), 26)
            y += 31

        self._button("< ITEMS", 12, 379, 125, lambda: self.show_screen("select"), 28)
        item_text = self._selected_item_name()
        self._button(item_text, 143, 379, 150, self.learn_selected_icon, 28)
        self._button("<", 318, 379, 32, lambda: self.change_property_page(-1), 28)
        self._label(
            "PAGE {}/{}".format(self.property_page + 1, page_count),
            354, 382, 66, "#C8CCD4", 11, "center"
        )
        self._button(">", 424, 379, 32, lambda: self.change_property_page(1), 28)

        tool_button = "DETECT SEWING KIT" if tool_kind == "tailoring" else ("DETECT FLETCH TOOL" if tool_kind == "fletching" else ("DETECT TINKER TOOL" if tool_kind == "tinker" else "DETECT SMITH TOOL"))
        self._button(tool_button, 12, 416, 165, lambda k=tool_kind: self.detect_setup_tool(k), 30)
        self._button("RESOURCE CHEST", 183, 416, 170, self.select_resource_chest, 30)
        material = self._material_entry()
        material_text = material[0] if material else "STANDARD"
        self._button(material_text, 359, 416, 161, self.open_materials, 30)
        self._button("TEMPLATES", 12, 453, 250, self.open_templates, 30)
        next_text = "CHOOSE PIECES & QUANTITIES >" if self.template_job_mode else "REVIEW & MATERIALS >"
        next_action = self.continue_template_job if self.template_job_mode else (lambda: self.show_screen("review"))
        self._button(next_text, 268, 453, 252, next_action, 30)
        self._label("Production always uses the configured target values.", 12, 496, 508, "#72E39A", 11, "center")
        self._button("S", 458, 8, 32, self.save_position_now)
        self._button("X", 496, 8, 32, self.stop)
        API.AddGump(self.ui)
        try:
            self.ui.SetInScreen()
        except Exception:
            pass

    def _begin_simple_gump(self):
        old = self.ui
        if old:
            try:
                if not old.IsDisposed:
                    self._remember_position()
                old.Dispose()
            except Exception:
                pass
        self.ui = API.CreateGump(True, True, True)
        self.ui.SetRect(self.gump_x, self.gump_y, 540, 526)
        bg = API.CreateGumpColorBox(0.88, "#17120D")
        bg.SetRect(0, 0, 540, 526)
        self.ui.Add(bg)
        self._label(PRODUCT_NAME, 12, 10, 350, "#E7A65B", 16)
        self._label(VERSION, 378, 13, 66, "#C8CCD4", 11, "right")
        self._button("S", 458, 8, 32, self.save_position_now)
        self._button("X", 496, 8, 32, self.stop)

    def _finish_simple_gump(self):
        API.AddGump(self.ui)
        try:
            self.ui.SetInScreen()
        except Exception:
            pass

    def _build_selector(self):
        self._begin_simple_gump()
        self._label("1. CHOOSE WHAT TO CRAFT", 12, 48, 350, "#FFD166", 14)
        self._button("WEAPONS", 12, 78, 250, lambda: self.choose_group("weapon"), 32)
        self._button("ARMOR", 268, 78, 252, lambda: self.choose_group("armor"), 32)
        source = WEAPON_CRAFT if self.selection_group == "weapon" else ARMOR_CRAFT
        entries = list(source.items())
        per_page = 8
        if self.selection_group == "armor":
            families = ("Studded", "Leather")
            family = families[self.selection_page % len(families)]
            entries = [(name, craft) for name, craft in entries if name.startswith(family + " ")]
            page_count = len(families)
            self._label(family.upper() + " ARMOR", 370, 52, 150, "#72E39A", 11, "right")
        else:
            page_count = max(1, (len(entries) + per_page - 1) // per_page)
        self.selection_page = max(0, min(self.selection_page, page_count - 1))
        visible = entries if self.selection_group == "armor" else entries[self.selection_page * per_page:(self.selection_page + 1) * per_page]
        for index, (name, craft) in enumerate(visible):
            col, row = index % 2, index // 2
            x, y = 12 + col * 256, 122 + row * 78
            graphic = self._load_int("JCS_CIM_Icon_" + name, int(craft.get("graphic", 0)))
            if graphic:
                icon = API.CreateGumpItemPic(graphic, 56, 56)
                icon.SetPos(x + 4, y + 4)
                self.ui.Add(icon)
            self._button(name, x + 66, y + 5, 180, lambda m=self.selection_group, n=name: self.choose_item(m, n), 30)
            material = "{} {}".format(craft.get("amount", craft.get("ingots", 0)), craft.get("resource", "Iron Ingot"))
            self._label(material, x + 68, y + 40, 174, "#C8CCD4", 10)
        self._button("<", 180, 450, 40, lambda: self._change_selection_page(-1), 30)
        self._label("PAGE {}/{}".format(self.selection_page + 1, page_count), 225, 455, 90, "#C8CCD4", 11, "center")
        self._button(">", 320, 450, 40, lambda: self._change_selection_page(1), 30)
        self._button("SETUP", 12, 488, 100, lambda: self.show_screen("setup"), 28)
        self._button("COPY ITEM", 118, 488, 140, self.copy_target_item, 28)
        self._button("LOAD TEMPLATE", 264, 488, 256, self.load_saved_template, 28)
        self._finish_simple_gump()

    def _build_setup(self):
        self._begin_simple_gump()
        self._label("FIRST-RUN SETUP", 12, 48, 300, "#FFD166", 15)
        self._label(
            "Required: save the secure resource chest and at least one tool.",
            12, 76, 510, "#FFFFFF", 11,
        )
        self._label(
            "Add each tool type you plan to use; you can return here anytime.",
            12, 98, 510, "#C8CCD4", 10,
        )

        rows = (
            ("RESOURCE CHEST", self.resource_chest, self.select_resource_chest, "SELECT"),
            ("FINISHED PRODUCTS", self.finished_container, self.select_finished_container, "SELECT"),
            ("SMITH HAMMER / TONGS", self.smith_tool, lambda: self.detect_setup_tool("smith"), "DETECT"),
            ("SEWING KIT", self.tailoring_tool, lambda: self.detect_setup_tool("tailoring"), "DETECT"),
            ("TINKERING TOOL", self.tinker_tool, lambda: self.detect_setup_tool("tinker"), "DETECT"),
            ("FLETCHER'S TOOLS", self.fletching_tool, lambda: self.detect_setup_tool("fletching"), "DETECT"),
        )
        y = 120
        for label, serial, callback, action in rows:
            color = "#72E39A" if serial else "#FF7A7A"
            state = "SAVED" if serial else "NOT SET"
            self._label(label, 20, y + 6, 250, "#FFFFFF", 12)
            self._label(state, 274, y + 6, 90, color, 11, "center")
            button_text = ("REDETECT" if serial else "DETECT") if action == "DETECT" else ("CHANGE" if serial else "SELECT")
            self._button(button_text, 374, y, 146, callback, 30)
            y += 45

        ready = self._setup_ready()
        message = (
            "READY: setup has the minimum required selections."
            if ready else
            "NOT READY: select a chest and at least one crafting tool."
        )
        self._label(message, 12, 405, 508, "#72E39A" if ready else "#FF7A7A", 11, "center")
        self._label(self.status[:76], 12, 430, 508, "#FFD166", 10, "center")
        self._button("< BACK", 12, 468, 150, lambda: self.show_screen("select"), 32)
        self._button(
            "SAVE SETUP & CONTINUE" if ready else "SETUP INCOMPLETE",
            168, 468, 352, self.finish_setup, 32,
        )
        self._finish_simple_gump()

    def _change_selection_page(self, delta):
        source = WEAPON_CRAFT if self.selection_group == "weapon" else ARMOR_CRAFT
        pages = 2 if self.selection_group == "armor" else max(1, (len(source) + 7) // 8)
        self.selection_page = (self.selection_page + int(delta)) % pages
        self.build_ui()

    def _build_review(self):
        self._begin_simple_gump()
        self._label("3. REVIEW PRODUCTION", 12, 48, 350, "#FFD166", 14)
        material = self._material_entry()
        review_title = self._selected_item_name() + (" — " + material[0] if material else "")
        self._label(review_title, 12, 80, 310, "#FFFFFF", 13)
        self._label("Quantity", 330, 82, 75, "#C8CCD4", 11)
        self._button("-", 405, 75, 32, lambda: self.adjust_quantity(-1), 28)
        self._label(str(self.production_qty), 441, 81, 38, "#72E39A", 12, "center")
        self._button("+", 485, 75, 32, lambda: self.adjust_quantity(1), 28)
        recipe = self._active_recipe()
        configured = [
            (name, self.recipe_targets.get(name, PROPERTY_MIN.get(name, 2)))
            for name, _c, _p, _d in self._current_library()
            if self.recipe_enabled.get(name, False)
        ]
        configured_text = ", ".join(name + " " + self._value_text(name, value) for name, value in configured) or "No imbues selected"
        production_text = ", ".join(entry[0] + " " + self._value_text(entry[0], entry[3]) for entry in recipe) or "No imbues selected"
        self._label("SAVED TARGETS: " + configured_text[:88], 12, 108, 508, "#D6D6D6", 9)
        self._label("WILL PRODUCE: " + production_text[:89], 12, 127, 508, "#72E39A", 9)
        self._label("RECOMMENDED RESERVE (3 craft + 3 imbue attempts each)", 12, 151, 508, "#E7A65B", 10)
        y = 174
        for line in self.preview_lines[:8]:
            color = "#FF7A7A" if "MISSING" in line else "#72E39A"
            self._label(line, 18, y, 500, color, 10)
            y += 22
        if len(self.preview_lines) > 8:
            self._label("+ {} more resources checked".format(len(self.preview_lines) - 8), 18, y, 500, "#C8CCD4", 9)
        if not self.preview_lines:
            self._label("Press PREVIEW to check the backpack and secure chest.", 18, 176, 500, "#FFD166", 11)
        self._label("PRODUCTION WILL MATCH THE CONFIGURED TARGETS", 12, 369, 508, "#72E39A", 12, "center")
        self._button("< IMBUES", 12, 401, 100, lambda: self.show_screen("imbues"), 30)
        self._button("NAME / SAVE TEMPLATE", 118, 401, 150, self.open_templates, 30)
        self._button("PREVIEW & CHECK", 274, 401, 246, self.preview_materials, 30)
        self._button("IMBUE EXISTING ITEM", 12, 439, 250, self.imbue_existing_item, 30)
        if not self.preview_ok:
            start_text = "START LOCKED - RUN PREVIEW"
        else:
            start_text = "START CONFIGURED BUILD"
        self._button(start_text, 268, 439, 252, self.start_production, 30)
        self._label("Salvage is disabled; rejected items remain in your backpack.", 12, 481, 508, "#C8CCD4", 10)
        self._finish_simple_gump()

    def _build_templates(self):
        self._begin_simple_gump()
        self._label("TEMPLATE LIBRARY", 12, 48, 300, "#FFD166", 14)
        page_count = max(1, (TEMPLATE_SLOTS + TEMPLATES_PER_PAGE - 1) // TEMPLATES_PER_PAGE)
        self._label("Click a named template to create a multi-item production job.", 12, 73, 508, "#C8CCD4", 10)
        y = 96
        start = self.template_page * TEMPLATES_PER_PAGE
        for index in range(start, min(start + TEMPLATES_PER_PAGE, TEMPLATE_SLOTS)):
            code = self._load_text("JCS_CIM_Template_" + str(index), "")
            label = "EMPTY SLOT"
            if code:
                try:
                    data = self._decode_template(code)
                    enabled = len(data.get("enabled", []))
                    label = "{} | {} | {} | {} imbues".format(
                        data.get("name", data.get("item", "Unnamed")),
                        data.get("material", "Standard"),
                        data.get("mode", "?").upper(),
                        enabled,
                    )
                except Exception:
                    label = "INVALID TEMPLATE"
            if code:
                self._button("{}: {}".format(index + 1, label), 12, y, 460, lambda s=index: self.open_template_job(s), 27)
                self._button("X", 478, y, 42, lambda s=index: self.delete_template_slot(s), 27)
            else:
                self._label("{}: EMPTY SLOT".format(index + 1), 18, y + 4, 450, "#777777", 10)
            y += 30
        self._button("<", 180, 282, 40, lambda: self.change_template_page(-1), 28)
        self._label("PAGE {}/{}".format(self.template_page + 1, page_count), 225, 287, 90, "#C8CCD4", 10, "center")
        self._button(">", 320, 282, 40, lambda: self.change_template_page(1), 28)
        self._label("NAME CURRENT BUILD", 12, 320, 180, "#E7A65B", 10)
        default_name = self.template_name_draft or (self._selected_item_name() + " Build")
        self.template_name_box = API.CreateGumpTextBox(default_name, 330, 30, False, 12)
        self.template_name_box.SetPos(12, 342)
        self.ui.Add(self.template_name_box)
        self._button("SAVE AS NEW", 348, 342, 172, self.save_current_template, 30)
        self._label("IMPORT / EXPORT CODE", 12, 383, 250, "#E7A65B", 10)
        self.template_box = API.CreateGumpTextBox("", 508, 48, True, 10)
        self.template_box.SetPos(12, 404)
        self.ui.Add(self.template_box)
        self._button("< REVIEW", 12, 466, 120, lambda: self.show_screen("review"), 28)
        self._button("IMPORT CODE", 138, 466, 180, self.import_template_box, 28)
        self._button("EXPORT LAST", 324, 466, 196, self.export_selected_template, 28)
        self._finish_simple_gump()

    def _build_materials(self):
        self._begin_simple_gump()
        family = self._material_family()
        choices = CRAFT_MATERIALS.get(family, [])
        self._label("CHOOSE " + family.upper() + " MATERIAL", 12, 48, 400, "#FFD166", 14)
        self._label("Material bonuses are added before imbuing.", 12, 74, 508, "#C8CCD4", 10)
        y = 96
        for name, _button, _resource, bonus in choices:
            selected = self.selected_material.get(family) == name
            self._button(("> " if selected else "") + name, 12, y, 180, lambda f=family, n=name: self.choose_material(f, n), 28)
            self._label(bonus, 202, y + 5, 318, "#72E39A" if selected else "#D6D6D6", 9)
            y += 39
        if family == "metal":
            self._label("All recorded metal material buttons are verified.", 12, 475, 508, "#72E39A", 9)
        elif family == "wood":
            self._label("All recorded wood material buttons are verified.", 12, 475, 508, "#72E39A", 9)
        self._button("< BACK TO IMBUES", 12, 493, 508, lambda: self.show_screen("imbues"), 28)
        self._finish_simple_gump()

    def _change_batch_page(self, delta):
        pages = max(1, (len(self.batch_quantities) + 5) // 6)
        self.batch_page = (self.batch_page + int(delta)) % pages
        self.build_ui()

    def _build_batch(self):
        self._begin_simple_gump()
        code = self._selected_template_code()
        try:
            template_name = self._decode_template(code).get("name", "Unnamed Template")
        except Exception:
            template_name = "Unnamed Template"
        self._label("PRODUCTION JOB: " + template_name[:38], 12, 48, 508, "#FFD166", 13)
        self._label("Choose compatible pieces and a quantity for each.", 12, 74, 508, "#C8CCD4", 10)
        source = ARMOR_CRAFT if self.item_mode == "armor" else WEAPON_CRAFT
        names = [name for name in source.keys() if name in self.batch_quantities]
        per_page = 6
        page_count = max(1, (len(names) + per_page - 1) // per_page)
        visible = names[self.batch_page * per_page:(self.batch_page + 1) * per_page]
        y = 105
        for name in visible:
            qty = int(self.batch_quantities.get(name, 0))
            self._label(name, 18, y + 5, 285, "#FFFFFF" if qty else "#888888", 12)
            self._button("-", 330, y, 38, lambda n=name: self.adjust_batch_quantity(n, -1), 28)
            self._label(str(qty), 374, y + 5, 58, "#72E39A" if qty else "#777777", 12, "center")
            self._button("+", 438, y, 38, lambda n=name: self.adjust_batch_quantity(n, 1), 28)
            y += 45
        self._button("<", 180, 387, 40, lambda: self._change_batch_page(-1), 28)
        self._label("PAGE {}/{}".format(self.batch_page + 1, page_count), 225, 392, 90, "#C8CCD4", 10, "center")
        self._button(">", 320, 387, 40, lambda: self._change_batch_page(1), 28)
        total = sum(int(qty) for _name, qty in self._batch_selected())
        self._label("TOTAL ITEMS: {}".format(total), 12, 430, 220, "#FFD166", 12)
        self._button("< TEMPLATES", 12, 466, 150, self.open_templates, 28)
        self._button("PREVIEW COMPLETE JOB", 168, 466, 352, self.preview_batch_materials, 28)
        self._finish_simple_gump()

    def _build_batch_review(self):
        self._begin_simple_gump()
        self._label("BATCH PREVIEW", 12, 48, 300, "#FFD166", 14)
        selected_text = ", ".join("{} x{}".format(name, qty) for name, qty in self._batch_selected())
        self._label(selected_text[:100], 12, 78, 508, "#FFFFFF", 10)
        self._label("RECOMMENDED RESERVE", 12, 108, 300, "#E7A65B", 10)
        y = 136
        for line in self.batch_preview_lines[:11]:
            self._label(line, 18, y, 500, "#FF7A7A" if "MISSING" in line else "#72E39A", 10)
            y += 23
        if len(self.batch_preview_lines) > 11:
            self._label("+ {} more resources checked".format(len(self.batch_preview_lines) - 11), 18, y, 500, "#C8CCD4", 9)
        self._button("< EDIT QUANTITIES", 12, 430, 200, lambda: self.show_screen("batch"), 30)
        self._button("CHECK AGAIN", 218, 430, 150, self.preview_batch_materials, 30)
        start_text = "START COMPLETE JOB" if self.batch_preview_ok else "START LOCKED"
        self._button(start_text, 374, 430, 146, self.start_batch_production, 30)
        self._label("Every selected piece uses this template's exact configured imbues.", 12, 478, 508, "#72E39A", 10)
        self._finish_simple_gump()

    def build_ui(self):
        if self.screen == "setup":
            self._build_setup()
        elif self.screen == "select":
            self._build_selector()
        elif self.screen == "review":
            self._build_review()
        elif self.screen == "templates":
            self._build_templates()
        elif self.screen == "materials":
            self._build_materials()
        elif self.screen == "batch":
            self._build_batch()
        elif self.screen == "batch_review":
            self._build_batch_review()
        else:
            self._build_editor()

    def run(self):
        # Tool discovery is automatic on every startup. Containers remain
        # explicit targets because choosing the wrong chest would move items.
        self.auto_detect_tools(False)
        self.build_ui()
        API.SysMsg("J.C.S. Artisan Workshop {} loaded.".format(VERSION), 68)
        while self.running and not API.StopRequested:
            API.ProcessCallbacks()
            API.Pause(0.10)
        self._remember_position()
        self.stop()


CraftImbueManager().run()

