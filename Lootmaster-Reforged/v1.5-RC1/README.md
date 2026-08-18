# J.C.S. Lootmaster Reforged

**Public Release Candidate 1 — v1.5-RC1**

A native **TazUO Legion** automated looting system inspired by and built in homage to the original **Lootmaster**.

Reforged scans nearby corpses, evaluates items against an ordered list of user-defined rules, and moves matching loot into a default or rule-specific destination bag. It also includes property-based item filtering, presets, manual container looting, an integrated treasure-chest handler, persistent settings, and post-loot corpse display options.

> This is a TazUO Legion Python script. It is **not** a Razor Enhanced script.

## Credit

The original Lootmaster established the rule-driven looting model that inspired Reforged: ordered rules, per-rule bags, item/property matching, rarity filtering, starter rules, alerts, and configurable looting behavior.

**Lootmaster Reforged is a new Legion-native implementation and is not the original Lootmaster codebase.**

TazUO and the Legion scripting engine are separate projects and are not maintained by this script's author.

## Main Features

- Automatic nearby-corpse looting
- Ordered rules; the **first matching enabled rule wins**
- Default loot bag plus per-rule destination bags
- Item name, OPL text, graphic, hue and regex matching
- Equipment categories such as armor, jewelry, weapons and shields
- Minimum/maximum rarity filtering
- Property rules using **All / Any / At least X**
- Property blacklist support
- Slayers, elemental damage, skill bonuses and build-oriented presets
- Gold fast-path
- Manual targeted-container looting
- Treasure-chest workflow: pathfind, lockpick, Remove Trap, open and rule-loot
- Corpse display modes: **Normal / Color / Hide**
- Configurable corpse hue
- Loot speed profiles: **Fast / Balanced / Safe**
- Overweight protection
- Automatic skip for corpses you do not have loot rights to
- Automatic pause while dead
- Persistent JSON settings between script revisions
- Compact gump mode

## Quick Setup

1. Put `JCS_Lootmaster_Reforged.py` in your Legion scripts folder.
2. Run it.
3. On first run, auto-loot stays **OFF** until a default bag is configured.
4. Click **DEFAULT** and target the bag where most loot should go.
5. Review the included starter rules; disable anything you do not want.
6. Click **E** beside a rule to edit it, or **+ RULE** to create a new rule.
7. Enable **AUTO** when ready.

### Rule Priority

Rules are checked from top to bottom.

**The first matching enabled rule wins.**

Use the up/down controls to change priority. A rule can use the global Default Bag or its own custom destination bag.

## Buttons

- **AUTO** — enable/disable automatic corpse looting.
- **PAUSE** — temporarily pause processing.
- **MANUAL** — target a container and run Reforged rules on it.
- **CHEST** — target a treasure chest; Reforged approaches it, lockpicks it, removes traps, opens it, then loots it with your rules.
- **+ RULE** — create a custom rule.
- **DEFAULT** — target the default destination bag.
- **IMPORT / EXPORT** — load/save the portable settings file.
- **SMALL** — compact gump.
- **STARTER** — restore starter rules. Requires a second click within 8 seconds to confirm. Your default bag is kept.
- **FAST / BALANCED / SAFE** — click to cycle loot timing profiles.

## Corpse Display

After a corpse is processed:

- **Normal** — leave the corpse visually unchanged.
- **Color** — recolor the corpse client-side.
- **Hide** — remove the corpse from your local client.

Hide is client-side only. A corpse may reappear if the client/server recreates it after you leave and return to the area.

## Loot Speed

- **Fast** — intended for responsive shards/connections.
- **Balanced** — more conservative waits.
- **Safe** — longest waits; use if items or OPL properties occasionally arrive late.

If you experience missed items, use Balanced or Safe before reporting a rule problem.

## Settings

Settings are stored in:

`JCS_Lootmaster_Settings.json`

Back this file up if you have built a large custom rule set.

## Treasure Chest Notes

The chest handler expects lockpicks in your backpack and uses the shard journal to determine lockpick and Remove Trap success. Journal wording can vary between shards.

## Release Candidate

RC1 has passed Python syntax/compile checks and static integration checks. It still needs normal in-game smoke testing on fresh characters and different connection/shard conditions before being labeled the final public v1.0.
