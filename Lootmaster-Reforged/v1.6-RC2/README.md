# J.C.S. LootMaster Reforged v1.6-RC2

Native TazUO / Legion automated looting system.

## Highlights in RC2

- Multi-target exact-item rules: add many targeted items to one rule.
- Exact target lists use Graphic + Hue internally but show real item names in the editor.
- Large target lists support paging, individual removal, and duplicate protection.
- Exact-target rules no longer get blocked by old identity filters.
- Imbue Salvage now has a persistent ON/OFF switch.
- Imbue Salvage keeps its bag and max-weight settings while disabled.
- Imbue Salvage still runs only as a fallback after normal loot rules.
- Supply Manager supports Restock and Max field limits.
- Restock can pull needed supplies and deposit extras.
- Persistent rules, bags, UI settings, profiles, and portable JSON backup/import.
- Corpse display modes: Normal / Color / Hide.
- Integrated treasure-chest lockpick / Remove Trap / loot workflow.
- Loot speed profiles: Fast / Balanced / Safe.

## Setup

1. Run the script in TazUO Legion.
2. Set a Loot Bag.
3. Review or create loot rules.
4. Turn AUTO ON when ready.
5. Optional: configure Supply Manager and Imbue Salvage.

## Exact Item Target Rules

Open a rule and use **ADD TARGET** repeatedly. Each target is stored as an exact item type using its Graphic + Hue pair. The editor displays the actual item name for readability. This is useful for categories such as Imbuing Resources, crafting materials, special drops, and shard-specific items.

## Imbue Salvage

The IMBUE SALVAGE row has an ON/OFF switch. OFF completely bypasses the salvage fallback without clearing the saved salvage bag or max-weight setting.

## Platform

TazUO Legion Scripting Engine. This is not a Razor Enhanced script.

## Upgrade Notes

Existing v1.6 settings are designed to remain compatible. Keep your normal LootMaster settings/profile files if you want to preserve existing configuration.
