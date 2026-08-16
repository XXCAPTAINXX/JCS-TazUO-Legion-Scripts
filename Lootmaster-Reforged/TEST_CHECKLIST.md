# Lootmaster Reforged RC1 Test Checklist

## Completed static checks
- [x] Python syntax/compile check
- [x] Existing settings filename preserved
- [x] Existing rule format preserved
- [x] Existing v1.4 source left untouched
- [x] First-run safety added
- [x] Loot speed persistence added
- [x] Dead-player pause added using Legion `API.Player.IsDead`
- [x] No-loot-right journal handling added
- [x] Two-click Starter Rules reset added
- [x] Corpse Normal / Color / Hide retained
- [x] Chest handler retained

## In-game smoke test before final v1.0
- [ ] Fresh character / no JSON settings file
- [ ] No default bag configured
- [ ] Set default bag and enable AUTO
- [ ] Gold
- [ ] Gems
- [ ] Reagents
- [ ] Armor rule
- [ ] Jewelry rule
- [ ] Weapon rule
- [ ] Multiple stacked corpses
- [ ] Corpse with no matching loot
- [ ] Overweight behavior
- [ ] Corpse with no loot rights
- [ ] Die while AUTO is enabled
- [ ] Resurrect and verify looting resumes
- [ ] Fast speed
- [ ] Balanced speed
- [ ] Safe speed
- [ ] Corpse display Normal
- [ ] Corpse display Color
- [ ] Corpse display Hide
- [ ] Manual container
- [ ] Chest with lock + trap
- [ ] Already unlocked chest
- [ ] Already untrapped chest
- [ ] No lockpicks
- [ ] Restart script and verify settings survive
- [ ] Starter reset requires two clicks and keeps default bag
