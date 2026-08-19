# J.C.S. Ultimate Combat Bar

**Version 1.6 RC14 — Public Test**  
For **TazUO Legion / LegionPy**

The J.C.S. Ultimate Combat Bar combines combat ability automation, Slayer weapon selection, automatic AOE switching, shield enforcement, target learning, durability monitoring, Enchanted Apple access, and Bag of Sending support into one compact combat gump.

> This is a **TazUO Legion Python script**. It is not a Razor Enhanced script.

## RC14 Compatibility Fix

RC13 used a nested `API.Gumps.*` namespace that is not available on current public Legion builds. RC14 permanently converts the custom-gump calls to Legion's current top-level `API.*` functions.

**RC14 is completely standalone. Only one Python file is required.**

Use:

`JCS_Ultimate_Combat_Bar_v1.6_RC14_Public_Test.py`

Do not keep or run the superseded RC13 script.

## Public Test Notice

This is still an RC/public-test build. The normal combat, Slayer, weapon-switching, and AOE portions are the primary tested features.

**Shield Bash / Basher support remains BETA.** It is intended for characters using Parry Mastery and still needs wider in-game testing on different builds and shard conditions.

## Main Features

- Automatic target tracking and classification
- Automatic Slayer weapon switching
- Automatic AOE switching when surrounded
- Manual AOE override
- General single-target and General AOE weapon profiles
- Slayer profiles for Arachnid, Demon, Dragon, Elemental, Poison Elemental, Fey, Repond, Reptile, and Undead
- Per-character weapon assignments
- Learned monster names and body/graphic IDs
- Doom-oriented target learning for creatures with unusual or changing names
- Shield enforcement
- Configurable combat abilities
- Equipment durability warnings
- Enchanted Apple counter and quick-use
- Bag of Sending charge display and gold sending
- Persistent full/minimized gump positions
- Compact minimized combat bar
- Per-character persistent settings

## Supported Weapon Types

The current build recognizes:

- Double Axe
- Longsword
- Broadsword
- Bladed Whip
- Radiant Scimitar
- Composite Bow
- Soul Glaive

You do not manually choose a weapon during combat. Assign the physical weapons to profiles in **Setup**, and the bar handles switching.

## First-Time Setup

1. Put `JCS_Ultimate_Combat_Bar_v1.6_RC14_Public_Test.py` in your Legion scripts folder.
2. Run that single script.
3. Click **Setup**.
4. Click **Weapon Bag** and target the container holding your combat weapons.
5. Click **Shield** and target the shield you want maintained.
6. Assign weapons under **Weapon Assignments**.
7. Enable or disable the abilities you want under **Combat Options**.
8. Optionally configure your Bag of Sending and durability warning threshold.
9. Close Setup and begin combat.

Settings and assignments are stored through Legion per-character persistent variables, so normal setup should only be required once per character.

## Weapon Assignments

Each profile can have one weapon assigned:

- **Single Target** — normal non-Slayer single-target weapon
- **General AOE** — normal area-damage weapon
- **Arachnid**
- **Demon**
- **Dragon**
- **Elemental**
- **Poison Elemental**
- **Fey**
- **Repond**
- **Reptile**
- **Undead**

Click a profile in Setup and target the desired weapon. A marked profile indicates a saved assignment.

## Automatic Slayer Selection

With **Slayer Auto** enabled, the bar examines the current enemy and determines the best available profile.

Classification can come from:

1. A manually taught monster
2. A learned body/graphic ID
3. Built-in known-monster mappings
4. Monster-name keyword matching
5. General Single Target fallback

The selected category appears under **Detected** and the weapon profile currently equipped appears under **Weapon**.

### Poison Elementals

Poison Elemental has its own profile and is checked separately from the broader Elemental category so a dedicated Poison Elemental Slayer can be used when assigned.

## Teaching Unknown Monsters

Some creatures, especially Doom bosses or shard-specific monsters, may not classify correctly by name alone.

1. Open **Setup**.
2. Click **Target Mob** and target the creature.
3. Under **Teach Target Slayer Type**, click the correct category.
4. The bar remembers the monster name and body/graphic when available.

Use **Forget Learned Target** to erase the learned classification for the current target.

This is especially useful for creatures with random names but consistent body IDs.

## Automatic AOE

With **Auto AOE** enabled, the bar checks hostile creatures within **2 tiles**.

RC14 behavior:

- Enters automatic AOE at **3 or more** nearby hostiles
- Leaves automatic AOE when the count falls to **1 or fewer**
- Uses the matching Slayer weapon if that assigned weapon is an AOE-capable Bladed Whip
- Otherwise switches to the **General AOE** weapon
- Returns to the appropriate Slayer or Single Target profile afterward

The separate enter/exit thresholds reduce rapid weapon swapping when the nearby count fluctuates.

### Manual AOE

Click **AOE** on the main bar to force General AOE mode. Manual AOE overrides normal automatic weapon selection until switched off.

## Shield Enforcement

Use **Setup → Shield** to target the shield you want maintained.

The main bar shows:

- **Equipped** — configured shield is equipped
- **Missing** — configured shield is not equipped
- **Not Set** — no shield is configured

The bar periodically checks and attempts to restore the configured shield.

## Combat Options

Each ability can be toggled independently:

- **Enemy of One**
- **Divine Fury**
- **Consecrate Weapon**
- **Honor**
- **Counter Attack**
- **Momentum Strike**
- **Lightning Strike**
- **Onslaught**
- **Curse Weapon**
- **Shield Bash BETA**

The script manages its own reuse timing rather than blindly firing every enabled action continuously.

### Enemy of One

Enemy of One is tracked by creature type rather than only one monster serial. This reduces unnecessary cancel/recast behavior while fighting several creatures of the same type.

### Shield Bash / Basher

**Shield Bash remains BETA.** It is intended for Parry Mastery/Basher testing and should not yet be considered as mature as the normal Slayer and weapon-switching logic.

## Target Button

**Target** manually selects the current enemy. It is useful for teaching monsters, testing Slayer assignments, bosses, and unusual shard-specific creatures.

## Durability Monitoring

The bar scans equipped gear and warns when durability falls below the configured percentage.

In Setup:

- **Warn -** lowers the threshold by 5%
- The percentage button displays the current threshold
- **Warn +** raises it by 5%
- **Check Now** performs an immediate durability scan

The main gump displays **OK** or **LOW x#**.

## Enchanted Apples

The bar automatically searches your backpack for Enchanted Apples.

- The main bar shows **Apple [count]**
- Clicking it uses an apple
- The minimized bar can display the apple graphic plus the current count

No manual apple serial setup is required.

## Bag of Sending / Bank Gold

Use **Setup → Set Send Bag** and target your Bag of Sending.

The script attempts to read remaining charges from the bag's displayed item properties.

- **Bank Gold** sends eligible backpack gold through the configured Bag of Sending
- The remaining charge count is displayed when readable
- `?` means the bag is configured but the property text could not be reliably parsed

## Main Bar Buttons

- **Pause / Resume** — pause or resume automated combat processing
- **AOE / AOE ON** — manual General AOE override
- **Target** — manually select an enemy
- **Bank Gold [charges]** — send backpack gold with the configured Bag of Sending
- **Apple [count]** — use an Enchanted Apple
- **Setup** — configuration and learning controls
- **Min** — switch to compact mode
- **Stop** — stop the script and clear active weapon abilities

## Main Status Display

The full bar shows:

- **Target** — current enemy name
- **Detected** — target Slayer/profile classification
- Classification source
- **Weapon** — currently active weapon profile
- **Mode** — Manual AOE, Auto AOE, or Auto Slayer
- **Near** — hostile count in the AOE radius
- **Shield** — configured shield state
- **Body** — current enemy body/graphic ID
- **Dura** — durability state and warning threshold
- **ACTIVE / PAUSED** — script state

## Minimized Bar

Compact mode includes the script title, running/paused state, current mode/profile, durability check, Enchanted Apple information, Bag of Sending information, **Open**, and **Stop**.

The full and minimized positions are remembered independently.

## Pause vs. Stop

**Pause** temporarily suspends combat processing while keeping the script open.

**Stop** ends the script and clears active weapon abilities. Run RC14 again to reopen it.

## Persistent Settings

Per-character persistent data includes:

- Gump positions
- Weapon bag
- Shield
- Bag of Sending
- Durability threshold
- Slayer weapon assignments
- Assigned weapon types
- Ability toggles
- Slayer Auto / Auto AOE settings
- Learned monster names
- Learned monster graphics/body IDs

## Known Limitations / Testing Notes

- **Shield Bash / Basher support is BETA.**
- Shard-specific spells, masteries, item properties, and journal behavior can differ.
- Bag of Sending charge detection depends on the wording exposed in item properties.
- Custom monsters may require manual teaching.
- The script can only equip and use items/actions that the client and shard permit at that moment.

## Troubleshooting

### `AttributeError: 'API' object has no attribute 'Gumps'`

That was the RC13 compatibility problem. Delete RC13 and use the standalone RC14 file. RC14 uses the current top-level Legion gump API.

### Wrong Slayer weapon

Target the creature manually, check **Detected**, and teach the proper Slayer type if necessary.

### AOE switches too often

RC14 enters at 3 nearby hostiles and exits at 1 to provide hysteresis and reduce rapid switching.

### Shield shows Missing

Confirm the original shield still exists and **Setup → Shield** points to the correct item.

### Bag of Sending shows `?`

The bag may still work. `?` only means the script could not confidently parse the remaining charge count.

### Apples show zero

Confirm Enchanted Apples are inside your backpack and accessible to Legion.

## Feedback for the Public Test

Useful reports should include the creature being fought, detected Slayer profile, equipped weapon, Auto/Manual AOE state, enabled combat options, whether Shield Bash was enabled, and the complete Legion error text or screenshot.