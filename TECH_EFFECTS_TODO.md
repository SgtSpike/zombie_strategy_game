# Tech Effects Implementation Guide

## Implemented Effects

### UI & Core Systems
- ✅ Tech points earning (all sources working)
- ✅ Tech tree rendering
- ✅ Research interaction
- ✅ Tech points display in UI
- ✅ Save/load support

## Effects To Implement

### Units & Combat Tree

**scavenging_efficiency** (10 pts)
- Location: `main.py` line ~370 (scavenge resources)
- Effect: Multiply scavenged resources by 1.25
- Code: `if self.game_state.has_tech('scavenging_efficiency'): amount = int(amount * 1.25)`

**scout_training** (20 pts)
- Location: `game_state.py` Unit class OR update_visibility
- Effect: Scouts get +1 vision range (change from 3 to 4)
- Code: Check tech when revealing area for scouts

**combat_training** (20 pts)
- Location: Unit recruitment (main.py ~lines 540-580)
- Effect: New units spawn at level 2
- Code: After creating unit, if has_tech, call `unit.gain_xp()` until level 2

**tactical_medicine** (20 pts)
- Location: `main.py` line ~450 (medic heal)
- Effect: Medics heal +20 HP
- Code: `heal_amount += 20 if self.game_state.has_tech('tactical_medicine') else 0`

**armor_plating** (40 pts)
- Location: Unit creation (game_state.py Unit.__init__)
- Effect: All units +40 max HP
- Code: In Unit.__init__, add 40 to max_health if tech researched

**rapid_response** (40 pts)
- Location: Unit creation (game_state.py Unit.__init__)
- Effect: All units +1 movement
- Code: In Unit.__init__, add 1 to max_moves if tech researched

**advanced_weaponry** (30 pts)
- Location: Soldier creation
- Effect: Soldiers +10 attack
- Code: Check tech when creating soldiers, add to attack_power

**super_soldier_program** (40 pts)
- Location: Unit recruitment menu
- Effect: Add new "Elite Soldier" recruitment option
- Code: New elif branch in recruitment, creates unit with 150 HP, 30 attack

### City & Economy Tree

**fortification** (10 pts)
- Location: Combat calculations when unit on wall tile
- Effect: Units on walls get +50% HP bonus
- Code: Check if unit is on city with wall, apply HP modifier in combat

**advanced_farming** (10 pts)
- Location: `game_state.py` City.produce_resources() line ~380
- Effect: Farms +2 food/turn
- Code: `if game_state.has_tech('advanced_farming'): food_production += 2 * farm_count`

**industrial_workshops** (10 pts)
- Location: City.produce_resources()
- Effect: Workshops +3 materials/turn
- Code: `if game_state.has_tech('industrial_workshops'): materials_production += 3 * workshop_count`

**basic_medicine** (10 pts)
- Location: City.produce_resources()
- Effect: Hospitals +2 medicine/turn
- Code: `if game_state.has_tech('basic_medicine'): medicine_production += 2 * hospital_count`

**research_documentation** (20 pts)
- Location: Already implemented in tech_tree.py `get_tech_cost()`
- Effect: All research costs -30%
- Status: ✅ DONE

**quick_start** (20 pts)
- Location: `main.py` found_city (line ~340)
- Effect: New cities get +30 materials, +30 food
- Code: `if self.game_state.has_tech('quick_start'): city.resources['food'] += 30; city.resources['materials'] += 30`

**watchtower** (20 pts)
- Location: update_visibility for cities
- Effect: Cities +2 vision range (from 2 to 4)
- Code: Check tech when revealing area for cities

**cure_research** (20 pts)
- Location: `main.py` manufacture cure check (line ~620)
- Effect: Cure costs 700/700 instead of 1000/1000
- Code: `required_food = 700 if self.game_state.has_tech('cure_research') else 1000`

**automated_defenses** (30 pts)
- Location: game_state.py end_turn()
- Effect: Cities/buildings damage adjacent zombies
- Code: New function that damages zombies near cities each turn

**helicopter_transport** (50 pts)
- Location: New key handler (maybe H key with city selected)
- Effect: Units can teleport between cities
- Code: New interaction to select city and move unit there instantly

## Implementation Priority

1. **High Priority** (Immediately noticeable):
   - combat_training (units spawn level 2)
   - scavenging_efficiency (+25% resources)
   - cure_research (cheaper cure)
   - advanced_farming/industrial_workshops/basic_medicine (more production)

2. **Medium Priority** (Quality of life):
   - scout_training (+1 vision)
   - rapid_response (+1 movement)
   - tactical_medicine (+20 heal)
   - quick_start (new cities bonus)

3. **Low Priority** (Advanced features):
   - armor_plating, advanced_weaponry (combat bonuses)
   - super_soldier_program (new unit type)
   - automated_defenses, helicopter_transport (complex mechanics)
