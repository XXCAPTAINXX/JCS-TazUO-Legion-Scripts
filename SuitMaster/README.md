# J.C.S. SuitMaster

**Current public build: RC1 (2.2l-RC1)**

J.C.S. SuitMaster is a TazUO Legion equipment optimizer designed for Ultima Online and developed/tested around InsaneUO.

Instead of judging one item at a time, SuitMaster evaluates complete equipment combinations. Set the build requirements and priorities that matter to you, scan your equipment storage, and SuitMaster will search the available gear and present up to **3 complete suit options**.

## Video Demo

https://youtu.be/XYPHopI-9fw

## Important: Download the Whole SuitMaster Folder

The RC1 source is packaged as a small loader plus a three-part payload because of repository upload-size limitations in the publishing tool used for this release.

Keep these together exactly as they appear in the repository:

- `JCS_SuitMaster_RC1.py`
- `RC1_payload/part00.txt`
- `RC1_payload/part01.txt`
- `RC1_payload/part02.txt`

**Do not download only the `.py` file.** Clone/download the complete `SuitMaster` folder. The loader reconstructs and runs the full 2.2l-RC1 source locally when launched in TazUO Legion.

Full reconstructed-source SHA-256:

`e0be602df65f1fb5569a49f83a0a3168bddba86ccaf05a6d22989bab0f0d9154`

## RC1 Features

- Scan multiple equipment storage chests
- Built-in profiles for melee, caster, luck, tamer, and hybrid builds
- Custom profile editor
- **Scan My Build** to create a starting profile from your current character
- Flexible equipment **+skill point budgeting** rather than forcing one exact skill distribution
- **Inspect Player** to import another player's visible equipment/build philosophy
- Compact on-the-go Inspect bar
- Up to **3 ranked suit options**
- Whole-suit minimums, targets, and 0-5 stat priorities
- Lock specific equipment pieces into a build
- Pull a selected suit into your bag
- Return pulled equipment afterward
- Share/import profile codes
- LootMaster Wanted-file integration to help identify missing stats/items
- Saved gump positions
- Build-search safety limits to prevent runaway searches

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
4. Press **BUILD SUIT**.
5. SuitMaster returns up to the best **3 unique complete suits** it can construct from the scanned equipment.

Three results are a maximum, not a requirement. If only one or two valid unique suits can be constructed, SuitMaster will return those instead.

## RC1 Status

This is a **Release Candidate / public test build**. Large equipment collections, unusual shard-specific item properties, and complex custom profiles may expose edge cases.

When reporting a problem, please include:

- SuitMaster RC1
- the profile/build being used
- what happened after pressing BUILD SUIT
- exact error text, if any
- screenshots when useful
- whether the issue happens with a smaller equipment pool

## Compatibility

- TazUO Legion scripting
- Developed/tested around InsaneUO
- Not a Razor Enhanced script
