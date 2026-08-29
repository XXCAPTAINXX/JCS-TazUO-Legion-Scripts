# J.C.S. SuitMaster RC5

RC5 is based on the public RC4 build and preserves RC4's optimizer, UI, profile, shield, and safety changes.

## New in RC5

- Added a toggleable **Keep Suit Medable** option to the Profile Editor.
- When enabled, SuitMaster filters incompatible armor before suit scoring.
- Normal leather armor is allowed.
- Armor with the **Mage Armor** property is allowed regardless of base material.
- Bone armor is treated as non-medable unless it has Mage Armor.
- Studded, plate, chain, ring, stone, woodland, dragon, and unknown body armor are conservatively excluded unless Mage Armor makes them meditation-compatible.
- Cloth-style headwear remains eligible.
- The medable setting saves with profiles and is included in profile share/import codes.
- If the available equipment cannot form a complete medable suit, SuitMaster reports the missing valid slots instead of silently using incompatible armor.

## Shield Support

RC5 keeps RC4's existing shield support intact. Shield remains an available equipment slot, and profiles such as Basher can require one.

## Packaging

`JCS_SuitMaster_RC5.py` reconstructs the verified RC5 source from the preserved RC4 source in the neighboring `RC4` folder, then runs the reconstructed RC5 build. Download the complete `SuitMaster` folder so RC4 and RC5 remain together.

RC4 base SHA-256: `58a701669f6902701c7d846a2f0aefcd21201b0b7b4b862b51e25cc93f2863a6`

Reconstructed RC5 SHA-256: `83414487314d03f42879894a984053a5950a00d1092095e681ab43bab70691ac`
