# J.C.S. Ultimate Combat Bar

**Version 1.6 RC15 — Release Candidate**  
For **TazUO Legion / LegionPy**

The J.C.S. Ultimate Combat Bar combines combat automation, Slayer weapon selection, automatic AOE switching, shield enforcement, target learning, durability monitoring, Enchanted Apple access, and Bag of Sending support in one standalone Legion script.

> This is a **TazUO Legion Python script**. It is not a Razor Enhanced script.

## Current File

Use only:

`JCS_Ultimate_Combat_Bar_v1.6_RC15.py`

RC15 is standalone. No companion Python file is required.

## RC15 — Buff Detection / Consecrate Fix

RC15 replaces the old fixed-duration guesses for maintained combat buffs with live Legion buff-state tracking.

- Registers Legion `OnBuffAdded` / `OnBuffRemoved` callbacks.
- Maintains a local active-buff registry for immediate state changes.
- Uses `ActiveBuffs()` as a synchronization fallback if an event is missed.
- Uses `BuffExists()` as a final compatibility fallback.
- Consecrate Weapon no longer waits on the old 11.25-second guessed duration.
- Divine Fury, Curse Weapon, and Counter Attack also use active buff state instead of long guessed refresh timers.
- A short 1.25-second cast-attempt throttle remains to prevent repeated failed casts from spamming the client/server.

The practical result is that Consecrate Weapon can be recast shortly after the actual buff disappears instead of waiting for an arbitrary timer.

## RC14 Compatibility Work Retained

RC14 removed legacy `API.Gumps.*` calls and converted the bar to the current top-level Legion custom-gump API. RC15 retains that compatibility work.

## Public Test / RC Status

The main combat, Slayer, weapon-switching, AOE, Consecrate/buff tracking, durability, apple, and Bag of Sending portions are the primary features under active use.

**Shield Bash / Basher support remains BETA.** It is intended for characters using Parry Mastery and still needs broader in-game testing.

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
- Live buff-state tracking for maintained combat buffs
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

Assign physical weapons to profiles in **Setup**. During combat, the bar chooses the appropriate assigned weapon automatically.

## First-Time Setup

1. Put `JCS_Ultimate_Combat_Bar_v1.6_RC15.py` in your Legion scripts folder.
2. Run the script.
3. Click **Setup**.
4. Click **Weapon Bag** and target the container holding your combat weapons.
5. Click **Shield** and target the shield you want maintained.
6. Assign weapons under **Weapon Assignments**.
7. Enable or disable the combat abilities you want.
8. Optionally configure a Bag of Sending and durability warning threshold.
9. Close Setup and begin combat.

Settings and weapon assignments are stored with Legion per-character persistent variables.

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

A marked profile in Setup indicates that an assignment is saved.

## Automatic Slayer Selection

With **Slayer Auto** enabled, the bar classifies the current target and selects the best available weapon profile.

Classification can come from:

1. A manually taught monster
2. A learned body/graphic ID
3. Built-in known-monster mappings
4. Monster-name keyword matching
5. General Single Target fallback

The main bar displays both the detected Slayer category and the weapon profile currently in use.

### Poison Elementals

Poison Elemental has a dedicated category and is checked separately from the broader Elemental profile so a dedicated Poison Elemental Slayer can be assigned.

## Teaching Unknown Monsters

Some creatures, especially Doom bosses or shard-specific monsters, may not classify correctly by name alone.

1. Open **Setup**.
2. Click **Target Mob** and target the creature.
3. Under **Teach Target Slayer Type**, choose the correct category.
4. The bar stores the monster name and body/graphic when available.

Use **Forget Learned Target** to clear the learned classification for the current target.

## Automatic AOE

With **Auto AOE** enabled, the bar checks hostile creatures within **2 tiles**.

- Enters automatic AOE at **3 or more** nearby hostiles.
- Leaves automatic AOE when the count falls to **1 or fewer**.
- Uses the matching Slayer weapon when that assigned Slayer weapon is an AOE-capable Bladed Whip.
- Otherwise switches to the **General AOE** weapon.
- Returns to the correct Slayer or Single Target weapon when the crowd clears.

The separate enter/exit thresholds reduce rapid weapon swapping as enemy counts fluctuate.

### Manual AOE

Click **AOE** on the main bar to force General AOE mode. Manual AOE overrides normal automatic weapon selection until switched off.

## Shield Enforcement

Use **Setup → Shield** to target the shield you want maintained.

The bar displays:

- **Equipped** — configured shield is equipped
- **Missing** — configured shield is not equipped
- **Not Set** — no shield is configured

The script periodically checks and attempts to restore the configured shield.

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

### Maintained Buffs

RC15 checks live buff state before recasting maintained abilities. This is especially important for **Consecrate Weapon**: while the buff is present, the bar does not recast it; after Legion reports the buff gone, it becomes eligible again subject only to the short anti-spam throttle and normal mana/casting restrictions.

### Enemy of One

Enemy of One is tracked by creature type rather than only by one monster serial. This reduces unnecessary cancel/recast behavior while fighting multiple creatures of the same type.

### Shield Bash / Basher

**Shield Bash remains BETA.** It is intended for Parry Mastery/Basher testing and should not yet be considered as mature as the normal Slayer and weapon-switching logic.

## Target Button

**Target** manually selects the current enemy. It is useful for teaching monsters, bosses, testing Slayer assignments, and unusual shard-specific creatures.

## Durability Monitoring

The bar scans equipped gear and warns when durability falls below the configured percentage.

In Setup:

- **Warn -** lowers the threshold by 5%
- The percentage button displays the current threshold
- **Warn +** raises the threshold by 5%
- **Check Now** performs an immediate durability scan

The main gump displays **OK** or **LOW x#**.

## Enchanted Apples

The bar automatically searches your backpack for Enchanted Apples.

- The main bar shows **Apple [count]**
- Clicking it uses an apple
- The minimized bar shows apple access and count when available

No manual apple serial setup is required.

## Bag of Sending / Bank Gold

Use **Setup → Set Send Bag** and target your Bag of Sending.

The script attempts to read remaining charges from item properties.

- **Bank Gold** sends eligible backpack gold through the configured Bag of Sending
- Remaining charges are displayed when readable
- `?` means the bag is configured but the charge property could not be parsed reliably

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

- Current target
- Detected Slayer/profile classification
- Classification source
- Active weapon profile
- Manual AOE / Auto AOE / Auto Slayer mode
- Nearby hostile count
- Shield status
- Current enemy body/graphic ID
- Durability state and warning threshold
- ACTIVE / PAUSED state

## Minimized Bar

Compact mode includes script state, current combat mode/profile, durability access, Enchanted Apple information, Bag of Sending information, **Open**, and **Stop**.

Full and minimized positions are remembered independently.

## Pause vs. Stop

**Pause** temporarily suspends combat processing while keeping the bar open.

**Stop** ends the script and clears active weapon abilities. Run RC15 again to reopen it.

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
- The script can only equip or use items/actions that the client and shard permit at that moment.
- RC15 depends on current Legion buff APIs for the improved maintained-buff behavior, but retains `ActiveBuffs()` / `BuffExists()` fallback handling.

## Troubleshooting

### Consecrate Weapon is not recasting

Confirm **Consecrate** is enabled in Setup and that the character has enough mana. RC15 waits while Legion reports the buff active, then allows a new cast after the buff is actually removed.

### `AttributeError: 'API' object has no attribute 'Gumps'`

That was the older RC13 compatibility issue. RC15 uses the current top-level Legion gump API.

### Wrong Slayer weapon

Target the creature manually, check **Detected**, and teach the proper Slayer type if necessary.

### AOE switches too often

Automatic AOE enters at 3 nearby hostiles and exits at 1 to provide hysteresis and reduce rapid switching.

### Shield shows Missing

Confirm the saved shield still exists and **Setup → Shield** points to the correct item.

### Bag of Sending shows `?`

The bag may still work. `?` only means the remaining charge count could not be parsed confidently.

### Apples show zero

Confirm Enchanted Apples are inside your backpack and accessible to Legion.

## Feedback

Useful reports should include the creature being fought, detected Slayer profile, equipped weapon, Auto/Manual AOE state, enabled combat options, whether Shield Bash was enabled, and the complete Legion error text or screenshot.