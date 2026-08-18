# J.C.S. Lootmaster Reforged v1.6 RC1

Release-candidate testing folder for the upcoming v1.6 release.

## Script

Upload the current release candidate here as:

`JCS_Lootmaster_Reforged_v1.6_RC1.py`

This folder is intentionally separate from the current v1.5 public release so RC testing does not disturb the stable version.

## Major v1.6 additions

- Supply Manager
- Separate Supply Bag and Restock Chest
- Restock / Max supply controls
- One-button bidirectional Restock normalization
- Profile support
- Improved character-specific bag persistence
- Duplicate rule-ID repair
- Safer settings/profile file writes
- Existing Lootmaster rule engine, corpse handling, treasure-chest workflow, speed profiles, and compact UI retained

## Credits

**Dorana** created the original LootMaster for Razor Enhanced and established the rule-driven looting concept that inspired Lootmaster Reforged. Dorana also maintains a collection of useful Ultima Online scripts on GitHub.

J.C.S. Lootmaster Reforged is a separate TazUO / Legion Python implementation and is not the original LootMaster codebase.

## RC testing focus

Before promoting v1.6 to final, verify:

- Loot Bag, Supply Bag, and Restock Chest persist after restart
- Rule buttons affect the correct rule on every page
- Restock pulls shortages up to the configured Restock amount
- Restock returns excess down to the configured Restock amount
- Field looting stops collecting configured supplies at Max
- Profiles restore rules/supply configuration without replacing the current character's local bag assignments
