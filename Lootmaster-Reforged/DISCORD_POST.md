# Discord Post Draft

**J.C.S. Lootmaster Reforged — TazUO Legion — Public RC1**

I’ve been working on a Legion-native rebuild inspired by the original **Lootmaster**, and I’m opening the first public release candidate for testing.

**Lootmaster Reforged** automatically scans nearby corpses and checks loot against an ordered list of rules. The first matching enabled rule determines what gets looted and which bag it goes to.

**Current features include:**
- automatic corpse looting
- default + per-rule loot bags
- name / graphic / hue / OPL / regex matching
- armor, jewelry, weapon and shield filtering
- rarity filters
- property matching with All / Any / At least X
- property blacklists
- slayer / elemental / skill-property presets
- manual container looting
- integrated treasure chest handler: pathfind → lockpick → Remove Trap → open → rule-based loot
- overweight protection
- Fast / Balanced / Safe loot speeds
- corpse display: Normal / Color / Hide
- automatic pause while dead
- automatic skip of corpses you don’t have loot rights to
- persistent settings between updates

**Quick start:** run the script, click **DEFAULT** and target your loot bag, review the starter rules, then turn **AUTO** on.

This is written for **TazUO Legion** and is **not a Razor Enhanced script**.

**Credit:** Reforged was built in homage to the original Lootmaster and carries forward the rule-driven looting concept in a new Legion-native implementation.

This is an **RC**, so if you test it and find something weird, please send the error/message plus what the corpse/item was doing. Different shard journal wording and timing are the two things I especially want feedback on.

GitHub: https://github.com/XXCAPTAINXX/JCS-TazUO-Legion-Scripts/tree/main/Lootmaster-Reforged
