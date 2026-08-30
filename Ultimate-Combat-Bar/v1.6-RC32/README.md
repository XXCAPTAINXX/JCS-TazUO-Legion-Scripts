# J.C.S. Ultimate Combat Bar — v1.6 RC32 CS1

Native TazUO / Legion combat automation bar for InsaneUO.

## Release file

Place the standalone script in this folder as:

`JCS_CombatBar_RC32_CS1.py`

No loader, payload, helper script, or external dependency is required.

## RC32 highlights

- Reworked Enemy of One tracking and creature-type switching.
- When Enemy of One is already active and a new creature type is engaged, Combat Bar performs the required two-cast handoff: dismiss the old type, confirm the buff clears, then cast again for the new type.
- Enemy of One state is reconciled during combat instead of relying only on the first target event.
- Shield Bash / Basher mastery-lane protection prevents Onslaught from firing when Bash mode owns the mastery lane.
- CS1 synchronization with LootMaster gives Combat Bar equipment swaps priority between LootMaster item moves.
- Weapon and shield watchdogs restore assigned combat equipment when displaced while respecting casting/targeting safety.
- Pack-aware AOE and slayer switching logic.
- Persistent learned creature/slayer mappings.
- Durability monitoring and Repair All support.
- Auto Honor safety and throttling improvements.
- Protected Auto Gold Send behavior.
- Character-isolated settings, persistent gump positions, compact combat controls, diagnostics, enchanted-apple support, and equipment safety improvements.

## Platform

- TazUO
- Legion scripting engine
- InsaneUO-oriented logic

This is not a Razor Enhanced script.

## Installation

1. Download `JCS_CombatBar_RC32_CS1.py` from this release folder.
2. Place it in your Legion scripts folder.
3. Run it through TazUO / Legion.
4. Open Setup and assign the equipment/options needed for your build.

For Basher mode, make sure the intended shield is assigned in Combat Bar setup. Shield Bash requires the saved shield state to be valid.

## Notes

RC32 uses the `CS1` coordination protocol shared with compatible LootMaster builds. Both scripts can still run independently, but using matching CS1-capable builds provides safer equipment-vs-loot item movement coordination.

Older releases are preserved in their own version folders for reference and rollback.
