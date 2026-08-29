# J.C.S. SuitMaster

**Current public build: RC5**

J.C.S. SuitMaster is a TazUO Legion equipment optimizer designed for Ultima Online and developed/tested around InsaneUO.

Instead of judging one item at a time, SuitMaster evaluates complete equipment combinations. Set the build requirements and priorities that matter to you, scan your equipment storage, and SuitMaster will search the available gear and present up to **3 complete suit options**.

## Video Demo

https://youtu.be/XYPHopI-9fw

## Important: Download the Whole SuitMaster Folder

RC5 uses the preserved RC4 source as its verified base. The RC5 loader reconstructs the merged RC5 source in memory and checks its SHA-256 before running it.

Keep the repository folder structure intact, especially:

- `RC4/JCS_SuitMaster_RC4.py`
- `RC5/JCS_SuitMaster_RC5.py`

**Do not download only the RC5 `.py` file.** Download/clone the complete `SuitMaster` folder so the RC4 base remains available to RC5.

Reconstructed RC5 SHA-256:

`83414487314d03f42879894a984053a5950a00d1092095e681ab43bab70691ac`

## RC5 Features

- Scan multiple equipment storage chests
- Built-in profiles for melee, caster, luck, tamer, and hybrid builds
- Custom profile editor
- **Keep Suit Medable** toggle
- **Scan My Build** to create a starting profile from your current character
- Flexible equipment **+skill point budgeting** rather than forcing one exact skill distribution
- **Inspect Player** to import another player's visible equipment/build philosophy
- Compact on-the-go Inspect bar
- Up to **3 ranked suit options**
- Whole-suit minimums, targets, and 0-5 stat priorities
- Shield support, including required-shield profiles such as Basher
- Lock specific equipment pieces into a build
- Pull a selected suit into your bag
- Return pulled equipment afterward
- Share/import profile codes
- LootMaster Wanted-file integration to help identify missing stats/items
- Saved gump positions
- Build-search safety limits to prevent runaway searches

## Keep Suit Medable

The Profile Editor includes a toggleable **Keep Suit Medable** constraint.

When enabled, incompatible armor is removed from consideration **before optimization/scoring**:

- Normal leather armor is allowed.
- Armor carrying **Mage Armor** is allowed regardless of base material.
- Bone armor requires Mage Armor.
- Studded, plate, chain, ring, stone, woodland, dragon, and other non-medable body armor are excluded unless Mage Armor makes the piece compatible.
- Cloth-style headwear remains eligible.

The setting is saved with the profile and included in profile share/import codes. If SuitMaster cannot build a complete meditation-compatible suit, it reports the missing valid slots instead of substituting incompatible armor.

## Profile Priorities

In the Profile Editor:

- **Minimum** = the suit must reach this value
- **Target** = a useful cap/goal for scoring
- **Priority 0** = ignore this property
- **Priority 5** = highest importance

The optimizer considers the **whole suit**, so an item does not automatically win just because it has one strong property or happens to be a named artifact.

## Scan My Build

`SCAN MY BUILD` reads the current character's supported stats and skills and creates a custom starting profile. Equipment skill contribution is treated as a flexible skill-point budget where possible, allowing SuitMaster to find different gear combinations without requiring the exact same +skill distribution as the currently worn suit.

## Inspect Player

The compact Inspect bar is intended for use while actively playing. `INSPECT` lets you target another visible player and imports the equipment properties SuitMaster can read from their visible gear.

This does **not** reveal another player's hidden/base skill table. Imported profiles therefore represent visible equipment/build information only.

## Building a Suit

1. Set one or more equipment storage chests.
2. Scan the equipment.
3. Select a built-in profile or create/edit a custom profile.
4. Enable **Keep Suit Medable** if the build needs Meditation-compatible armor.
5. Press **BUILD SUIT**.
6. SuitMaster returns up to the best **3 unique complete suits** it can construct from the scanned equipment.

Three results are a maximum, not a requirement. If only one or two valid unique suits can be constructed, SuitMaster will return those instead.

## RC5 Status

This is a **Release Candidate / public test build**. Large equipment collections, unusual shard-specific item properties, and complex custom profiles may expose edge cases.

When reporting a problem, please include:

- SuitMaster RC5
- the profile/build being used
- whether **Keep Suit Medable** was enabled
- what happened after pressing BUILD SUIT
- exact error text, if any
- screenshots when useful
- whether the issue happens with a smaller equipment pool

## Compatibility

- TazUO Legion scripting
- Developed/tested around InsaneUO
- Not a Razor Enhanced script
