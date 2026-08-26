# SuitMaster RC2 Fix Note

RC2 fixes equipment-slot classification.

- Legion's reported equipment layer is now preferred whenever available.
- Fallback slot detection now uses only the actual item name, not tooltip/OPL property text.
- Removed the broad `wing = Back` fallback that could classify a **Winged Helm** as back-slot gear.
- Known back-slot artifacts such as **Dragon's Wing** remain supported explicitly.
- Ambiguous or unrecognized equipment is ignored instead of being forced into the wrong slot.
- Hit Point Regeneration and Stamina Regeneration remain supported build properties.

RC2 is intended to be a full standalone script. No loader or payload files are required.
