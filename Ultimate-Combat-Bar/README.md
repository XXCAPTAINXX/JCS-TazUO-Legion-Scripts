# J.C.S. Ultimate Combat Bar

**Version 1.6 RC13 — Public Test**  
For **TazUO Legion / LegionPy**

The J.C.S. Ultimate Combat Bar combines combat ability automation, slayer weapon selection, automatic AOE switching, shield enforcement, target learning, durability monitoring, Enchanted Apple access, and Bag of Sending support into one compact combat gump.

> This is a **TazUO Legion Python script**. It is not a Razor Enhanced script.

## Public Test Notice

This is an RC/public-test build. The normal sword/slayer/AOE portions are the primary tested features.

**Shield Bash / Basher support is BETA.** It is intended for characters using Parry Mastery and still needs wider in-game testing on different builds and shard conditions.

## Main Features

- Automatic target tracking and target classification
- Automatic Slayer weapon switching
- Automatic AOE weapon switching when surrounded
- Manual AOE override
- General single-target and General AOE weapon profiles
- Slayer profiles for:
  - Arachnid
  - Demon
  - Dragon
  - Elemental
  - Poison Elemental
  - Fey
  - Repond
  - Reptile
  - Undead
- Weapon assignments are remembered per character
- Learned monster names and body/graphic IDs
- Doom-oriented target learning for creatures with unusual or changing names
- Shield enforcement
- Configurable combat abilities
- Equipment durability warnings
- Enchanted Apple counter and quick-use button
- Bag of Sending charge display and gold sending
- Persistent gump position
- Compact/minimized combat bar
- Per-character persistent settings

## Supported Weapon Types

The current build recognizes these weapon families when identifying assigned weapons:

- Double Axe
- Longsword
- Broadsword
- Bladed Whip
- Radiant Scimitar
- Composite Bow
- Soul Glaive

You do not need to manually choose a weapon button during combat. Assign the physical weapons to the appropriate profiles in **Setup**, and the bar handles switching.

## First-Time Setup

1. Place `JCS_Ultimate_Combat_Bar_v1.6_RC13_Public_Test.py` in your Legion scripts folder.
2. Run the script.
3. Click **Setup**.
4. Click **Weapon Bag** and target the container holding your combat weapons.
5. Click **Shield** and target the shield you want the bar to keep equipped.
6. Assign your weapons under **Weapon Assignments**.
7. Enable or disable the combat abilities you want under **Combat Options**.
8. Optionally set your Bag of Sending and durability warning threshold.
9. Close Setup and begin combat.

Settings and assignments are stored per character through Legion persistent variables, so normal setup should only be required once per character.

## Weapon Assignments

Each profile can have one specific weapon assigned to it.

Available profiles are:

- **Single Target** — your normal non-slayer single-target weapon
- **General AOE** — your normal area-damage weapon
- **Arachnid**
- **Demon**
- **Dragon**
- **Elemental**
- **Poison Elemental**
- **Fey**
- **Repond**
- **Reptile**
- **Undead**

To assign a weapon, click its profile in Setup and target the desired weapon.

A marked profile indicates that a weapon has already been assigned.

## Automatic Slayer Selection

With **Slayer Auto** enabled, the bar examines the current enemy and determines the best available profile.

Classification can come from:

1. A monster you manually taught the bar
2. A learned body/graphic ID
3. Built-in known-monster mappings
4. Monster-name keyword matching
5. General Single Target fallback

The selected profile appears on the main gump under **Detected** and the equipped profile appears under **Weapon**.

### Poison Elementals

Poison Elemental has its own profile and is checked separately from the broader Elemental category so a dedicated Poison Elemental Slayer can be used when assigned.

## Teaching Unknown Monsters

Some creatures—especially Doom bosses or shard-specific monsters—may not classify correctly by name alone.

To teach one:

1. Open **Setup**.
2. Click **Target Mob** and target the creature.
3. Under **Teach Target Slayer Type**, click the correct category.
4. The bar remembers both the monster name and body/graphic when available.

Use **Forget Learned Target** to erase the learned classification for the currently targeted monster.

This is particularly useful for monsters with random names but consistent body IDs.

## Automatic AOE

With **Auto AOE** enabled, the bar checks hostile creatures within **2 tiles**.

Current RC13 behavior:

- Enters automatic AOE mode at **3 or more** nearby hostiles
- Leaves automatic AOE mode when the count drops to **1 or fewer**
- Uses the **General AOE** assigned weapon while automatic AOE is active
- Returns to the appropriate Slayer or Single Target profile afterward

The different enter/exit counts prevent rapid weapon swapping when the nearby enemy count fluctuates.

### Manual AOE

Click **AOE** on the main bar to force General AOE mode.

While manual AOE is active, it overrides normal automatic weapon selection. Click it again to return to automatic behavior.

## Shield Enforcement

Use **Setup → Shield** to target the shield you want the script to maintain.

The main bar displays:

- **Equipped** — configured shield is currently equipped
- **Missing** — configured shield is not currently equipped
- **Not Set** — no shield has been configured

The bar periodically checks the shield and attempts to restore it when appropriate.

## Combat Options

Each ability can be toggled ON or OFF independently in Setup.

Available options:

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

The script manages timing internally rather than repeatedly firing every enabled ability without regard to its normal reuse behavior.

### Enemy of One

Enemy of One is tracked by creature type rather than only by one monster serial. This prevents needless cancel/recast behavior when fighting several creatures of the same type.

### Shield Bash / Basher

**Shield Bash is currently BETA.** It is intended for Parry Mastery/Basher testing and should not yet be considered as mature as the normal Slayer and weapon-switching logic.

If you are testing this portion, pay special attention to ability timing, mastery state, shield behavior, and whether normal combat actions remain responsive.

## Target Button

**Target** lets you manually choose the current enemy.

This is useful when:

- Automatic acquisition has not selected the creature you want
- Teaching a monster
- Testing a Slayer assignment
- Fighting bosses or unusual shard-specific creatures

## Durability Monitoring

The bar scans equipped gear and warns when durability falls below the configured percentage.

In Setup:

- **Warn -** lowers the warning threshold by 5%
- The percentage button shows the current threshold
- **Warn +** raises the threshold by 5%
- **Check Now** immediately performs a durability scan

The main gump shows **OK** or **LOW x#**.

The minimized bar provides a compact durability control and, when supported by Legion, can display the graphic of the lowest-durability equipped item.

## Enchanted Apples

The bar automatically searches your backpack for Enchanted Apples.

- The main bar displays **Apple [count]**
- Clicking it uses an apple
- The minimized bar displays the apple graphic when Legion can render it, plus the current count

No manual apple serial setup is required.

## Bag of Sending / Bank Gold

Use **Setup → Set Send Bag** and target your Bag of Sending.

The script reads the bag's displayed properties to determine remaining charges when the shard exposes them in a recognizable format.

- **Bank Gold** sends eligible backpack gold through the configured Bag of Sending
- The charge count is shown beside the button when readable
- A `?` means the bag is configured but the charge count could not be reliably read

The script understands common property formats such as `Charges: 25`, `Charges 25`, or `25 Charges`.

## Main Bar Buttons

- **Pause / Resume** — pauses or resumes automated combat processing
- **AOE / AOE ON** — toggles manual General AOE mode
- **Target** — manually select the current enemy
- **Bank Gold [charges]** — use the configured Bag of Sending on backpack gold
- **Apple [count]** — use an Enchanted Apple
- **Setup** — open configuration and learning controls
- **Min** — switch to the compact combat bar
- **Stop** — stop the script and clear active weapon abilities

## Main Status Display

The full bar shows:

- **Target** — current enemy name
- **Detected** — Slayer/profile classification for that enemy
- Classification source
- **Weapon** — profile currently being used
- **Mode** — Manual AOE, Auto AOE, or Auto Slayer
- **Near** — hostile count in the AOE detection radius
- **Shield** — configured shield state
- **Body** — current enemy body/graphic ID
- **Dura** — durability status and warning threshold
- **ACTIVE / PAUSED** — script state

## Minimized Bar

The compact bar is intended to preserve screen space during combat.

It includes:

- Script title
- RUNNING / PAUSED state
- Current mode/profile
- Durability quick check
- Enchanted Apple graphic/count
- Bag of Sending graphic/charges
- **Open** to restore the full gump
- **Stop** to stop the script

The minimized and full gump positions are remembered independently.

## Pause vs. Stop

**Pause** temporarily suspends combat processing without closing the script. Resume when ready.

**Stop** ends the script's run loop and clears active weapon abilities. Run the script again to reopen it.

## Persistent Settings

The bar stores configuration using Legion per-character persistent variables, including:

- Gump positions
- Weapon bag
- Shield
- Bag of Sending
- Durability threshold
- Assigned Slayer weapons
- Assigned weapon types
- Ability toggles
- Slayer Auto / Auto AOE settings
- Learned monster names
- Learned monster graphics/body IDs

Because the data is character-specific, different characters can maintain different combat setups.

## Known Limitations / Testing Notes

- **Shield Bash / Basher support is BETA.**
- Shard-specific spell, mastery, item-property, or journal behavior can differ.
- Bag of Sending charge detection depends on the wording exposed in item properties.
- Custom monsters may require manual teaching before Slayer switching can be accurate.
- The script can only equip and use items/actions that the client and shard permit at that moment.

## Troubleshooting

### Wrong Slayer weapon is selected

Target the creature manually, confirm the **Detected** profile, then teach it the proper Slayer type from Setup if necessary.

### AOE switches too often

RC13 uses a built-in hysteresis rule: it enters at 3 nearby hostiles and exits at 1. If a shard's combat spacing behaves unusually, this may need shard-specific tuning in a later build.

### Shield shows Missing

Confirm the original shield still exists and that **Setup → Shield** points to the correct item.

### Bag of Sending shows `?`

The bag may still work. `?` only means the script could not confidently parse the remaining charge count from the item's properties.

### Apples show zero

Confirm Enchanted Apples are inside your backpack and accessible to Legion.

### A monster is classified incorrectly every time

Use **Teach Target Slayer Type** to override automatic name-based classification for that creature.

## Feedback for the Public Test

Useful reports should include:

- What creature you were fighting
- What Slayer profile the bar detected
- What weapon it equipped
- Whether Auto AOE or manual AOE was active
- Which combat options were enabled
- Whether you were testing Shield Bash / Parry Mastery
- Any Legion console or journal error text

That information makes it much easier to separate a classification problem, weapon-assignment problem, shard timing issue, or Legion API issue.