# J.C.S. Ultimate Combat Bar v1.6-RC16

Native TazUO / Legion combat assistant with build-aware ability logic, slayer switching, equipment enforcement, and compact combat controls.

## Highlights in RC16

- Per-character persistence isolation using the live character serial.
- Shield Bash / Basher safety: Basher is blocked below 90.0 Parrying while normal combat logic continues.
- Pack-aware AOE weapon logic:
  - Homogeneous nearby packs hold the matching AOE-capable slayer weapon.
  - Mixed or unknown packs use the configured General AOE weapon.
  - Single targets continue to use normal slayer selection.
- Honor targeting improvements:
  - Does not steal an existing manual target cursor.
  - Longer lag-friendly Honor target window.
  - Global Honor throttle prevents target churn from spamming Virtue targeting.
  - Late Honor cursors are consumed/cancelled safely.
- Equipment watchdog restores the expected weapon and shield.
- Weapon/shield restoration yields during casting, recovery, and target cursors.
- Manual gump-position save button in full and minimized views.
- Dragon Slayer and Poison Elemental Slayer support.
- Whip and broadsword weapon logic.
- Compact/minimized combat bar.
- Auto Enemy of One toggle support.
- Durability checking and gold Bag of Sending support.
- Learned mob/slayer mappings, including Doom-oriented handling.

## Supported Builds

- Sampire
- Blood Knight
- Basher / Shield Bash setup
- Customizable skill/mastery combinations supported by the Combat Bar setup

## Basic Setup

1. Run the script in TazUO Legion.
2. Open Setup.
3. Assign your normal, slayer, AOE, and shield equipment as appropriate.
4. Choose your build and enabled combat abilities.
5. Save setup.
6. Minimize the bar for normal combat use.

## Basher Note

Shield Bash requires at least 90.0 Parrying in this release. If Parrying is below that threshold, Shield Bash is locked out but the rest of the Combat Bar continues to operate.

## Platform

TazUO Legion Scripting Engine. This is not a Razor Enhanced script.
