# Zombie Apocalypse Strategy Game

A turn-based, tile-based strategy game where you rebuild civilization while fighting escalating zombie hordes and searching for **The Cure** to save humanity.

## Game Concept

After the zombie apocalypse, you lead a small group of survivors who must:
- Scavenge resources from ruined cities
- Found new settlements and rebuild civilization
- Fight off increasingly dangerous zombie hordes
- Level up your units through combat and exploration
- Find the Research Lab and manufacture The Cure to win
- Survive as long as possible if you can't find the cure

## Installation

1. Install Python 3.8 or higher (but not higher than 3.11, as versions beyond this are not yet supported by pygame)
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the game:
```bash
cd src
python main.py
```

## Controls

### Camera
- **W/A/S/D** - Move camera (only when Ctrl is NOT pressed)
- **Mini-Map** - Click anywhere on the mini-map (bottom-right) to instantly jump to that location

### Unit Control
- **Left Click** - Select unit / Select tile
- **Shift + Click** - Select city
- **Right Click** - Move selected unit / Attack enemy / Heal ally (medic)
- **E** - End turn

### City Management
When a city is selected:
- **1** - Build Farm (30 materials)
- **2** - Build Workshop (50 materials)
- **3** - Build Hospital (40 materials)
- **4** - Build Wall (5 materials)
- **5** - Build Dock (40 materials, must be on water)
- **6** - Recruit Survivor (20 food, 10 materials)
- **7** - Recruit Scout (15 food, 5 materials)
- **8** - Recruit Soldier (30 food, 20 materials)
- **9** - Recruit Medic (25 food, 15 materials, 10 medicine)
- **U** - Upgrade building (click on building after pressing U)
- **C** - Manufacture The Cure (requires hospital, 1000 food, 1000 materials, 1 cure)

### Unit Actions
- **F** - Found a new city at selected unit's location
- **R** - Scavenge resources from current tile
- **T** - Transfer resources from unit to city (when on city tile)
- **G** - Gather resources from city to unit (when on city tile)
- **Q** - Triangulate lab signals (scouts only, requires full movement points)

### System
- **Ctrl+S** - Open save menu
- **Ctrl+L** - Open load menu
- **TAB** - Open/close Tech Tree
- **F1** - Debug: Toggle full map reveal
- **ESC** - Exit game (shows warning if unsaved changes)

## Tech Tree

The tech tree allows you to research technologies that provide permanent gameplay bonuses. Access it by pressing **Y** during your turn.

### Earning Tech Points

Tech points are earned automatically from:
- **2 points per turn** - Passive income each turn
- **1 point per 10 tiles explored** - Reward for exploration
- **5 points per zombie killed** - Combat rewards
- **20 points per super zombie killed** - Major combat rewards
- **1 point per 100 resources produced** - Economic rewards from city production

### Technologies

**Units & Combat Tree:**

1. **Scavenging Efficiency** (10 pts) - Scavenged resources +25%
2. **Scout Training** (20 pts) - Scouts get +1 vision range (4 instead of 3)
3. **Combat Training** (20 pts) - New units spawn at level 2
4. **Tactical Medicine** (20 pts) - Medics heal +20 HP
5. **Rapid Response** (40 pts) - All units get +1 movement
6. **Armor Plating** (40 pts) - All units get +40 max HP
7. **Advanced Weaponry** (30 pts, requires Combat Training) - Soldiers get +10 attack
8. **Super Soldier Program** (40 pts, requires Advanced Weaponry) - Unlock elite soldier recruitment

**Cities & Economy Tree:**

1. **Fortification** (10 pts) - Units on walls get +50% HP bonus
2. **Advanced Farming** (10 pts) - Farms produce +2 food/turn
3. **Industrial Workshops** (10 pts) - Workshops produce +3 materials/turn
4. **Basic Medicine** (10 pts) - Hospitals produce +2 medicine/turn
5. **Research Documentation** (20 pts, requires any 3 techs) - All research costs -30%
6. **Quick Start** (20 pts, requires Fortification) - New cities start with +30 food and +30 materials
7. **Watchtower** (20 pts, requires Fortification) - Cities get +2 vision range (5 instead of 3)
8. **Cure Research** (20 pts, requires Basic Medicine) - Cure costs reduced to 350/350 (from 500/500)
9. **Automated Defenses** (30 pts, requires Watchtower) - Cities damage adjacent zombies each turn
10. **Helicopter Transport** (50 pts, requires Watchtower) - Units can teleport between cities

### Tech Tree Strategy

- **Early Game**: Prioritize economic techs (Advanced Farming, Industrial Workshops, Scavenging Efficiency) for faster resource generation
- **Mid Game**: Invest in combat techs (Combat Training, Scout Training) to strengthen your forces
- **Late Game**: Research Cure Research to make manufacturing the cure more affordable
- **Research Documentation**: Very valuable if unlocked early, reduces the cost of all future research by 30%

## Gameplay

### Starting the Game
- You begin with 3 survivor units, each carrying starting resources
- 5 zombies are scattered across the map
- Ruined cities contain valuable resources
- One Research Lab exists somewhere on the map with **The Cure**

### Turn-Based Strategy
- Each turn belongs to either the player or enemies
- Units have movement points (varies by unit type)
- Press **E** to end your turn and let zombies move
- Zombies spawn at map edges with escalating numbers

### Resource Management
Your survivors can collect four types of resources:
- **Food** - Sustains your population and recruits units
- **Materials** - Used for construction
- **Medicine** - Recruits medics and heals units
- **Cure** - Found at the Research Lab, needed to win the game

### Unit Types

**Survivor** (Default)
- Health: 100 HP
- Movement: 3 tiles/turn
- Attack: 10 damage
- Role: General purpose unit

**Scout** (Fast Explorer)
- Health: 75 HP
- Movement: 5 tiles/turn
- Attack: 8 damage
- Vision: 3 tiles (vs 2 for others)
- XP Gain: 1 XP per new tile explored
- Special Ability: Triangulate lab signals (Press Q)
- Role: Map exploration and reconnaissance

**Soldier** (Combat Specialist)
- Health: 120 HP
- Movement: 2 tiles/turn
- Attack: 20 damage
- XP Gain: 50 XP per enemy killed
- Role: Front-line combat

**Medic** (Support)
- Health: 80 HP
- Movement: 3 tiles/turn
- Attack: 5 damage
- Ability: Heal adjacent ally for 30 HP (scales with level: 30 + 10×level)
- XP Gain: 1 XP per HP healed
- Role: Unit support and healing

### Experience & Leveling System

All units gain experience and level up:
- **Per Level:** +10% HP and Attack
- **XP Requirements:** Increase by 1.5× each level
- Units fully heal when leveling up
- Combat units: 50 XP per kill
- Medics: 1 XP per HP healed
- Scouts: 1 XP per new tile explored

### Enemy Types

**Zombie** (Standard)
- Health: 100 HP
- Movement: 2 tiles/turn
- Attack: 10 damage
- Spawning: Escalating numbers each turn

**Super Zombie** (Boss)
- Health: 200 HP
- Size: 2×2 tiles (occupies 4 map tiles)
- Movement: 2 tiles/turn
- Attack: 50 damage
- Spawning: Starts appearing after turn 25 (every 3-4 turns)
- Appears as "SZ" on the map

### Zombie Spawn Rates (Escalating Difficulty)

- **Turn 1-5:** 1-2 zombies/turn
- **Turn 6-10:** 2-3 zombies/turn
- **Turn 11-15:** 3-4 zombies/turn
- **Turn 16-20:** 4-5 zombies/turn
- **Turn 21-30:** 5-7 zombies/turn
- **Turn 31-40:** 7-10 zombies/turn
- **Turn 41+:** 10-15 zombies/turn
- **Super Zombies:** 1 every 3-4 turns (starts turn 25)

### Scavenging
1. Move a unit to a tile with a gold circle (resource marker)
2. Press **R** to scavenge
3. Resources are added to unit's inventory
4. Transfer to cities using **T** when standing on city tile

### Building Cities
1. Move a survivor to a strategic location
2. Press **F** to found a new city
3. Cities must be at least 3 tiles apart
4. Units automatically transfer their inventory to the new city
5. Cities can be attacked and destroyed by zombies

### City Health & Defense

**City HP:**
- Base: 50 HP
- With Wall: 100 HP (doubles health)

**Building HP:**
- All buildings: 20 HP
- Can be destroyed by zombies

**Zombies can attack:**
- Cities (to destroy them)
- Buildings (to eliminate production)
- Units (standard combat)

### Constructing Buildings

Buildings are placed on adjacent tiles to cities and provide production bonuses based on terrain:

**Farm** (30 materials)
- Grass: 6 food/turn
- Forest: 3 food/turn
- Other: 0 food/turn

**Workshop** (50 materials)
- Intact Building: 8 materials/turn
- Road/Ruined Building: 4 materials/turn
- Rubble: 2 materials/turn
- Other: 0 materials/turn

**Hospital** (40 materials)
- Intact Building: 6 medicine/turn
- Other: 2 medicine/turn

**Wall** (5 materials)
- When built on city tile: Doubles city HP to 100
- Provides defensive bonus

**Dock** (40 materials)
- Must be built on water
- Produces: 12 food/turn

**Building Upgrades:**
- Press **U** then click on a building
- Max level: 3
- Cost: 50 materials per level
- Effect: Increases production based on level

### Combat
- Right-click on an adjacent enemy unit to attack
- Damage dealt = Unit's attack power
- Medics can heal adjacent allies (right-click on friendly unit)
- Health bars appear above damaged units
- XP is awarded for defeating enemies

### Fog of War
- Only explored tiles are visible
- Currently visible tiles show active units
- Cities have vision range of 2 tiles
- Scouts have vision range of 3 tiles
- Other units have vision range of 2 tiles

### Finding the Research Lab

**Lab Triangulation (Scout Special Ability):**

Scouts can use their turn to triangulate radio signals from the Research Lab, progressively narrowing down its location on the minimap:

1. **Select a scout** with full movement points (hasn't moved this turn)
2. **Press Q** to "Triangulate signals from lab"
3. The scout uses their entire turn (movement set to 0)
4. A circle appears on the minimap showing the possible lab location

**Triangulation Levels:**
- **Level 1:** Very large search area (50% of minimap)
- **Level 2:** Large search area (30% of minimap)
- **Level 3:** Medium search area (15% of minimap)
- **Level 4:** Exact location revealed on minimap

**Strategy:**
- Use 4 scout triangulations to find the lab without exploring
- Each triangulation narrows the search area significantly
- The circle size scales with map size (larger on 100×100 maps)
- Once found, you can plan your route to the lab efficiently
- Balances the challenge of finding the lab on large maps

### Map Features

**Terrain Types:**
- 🟩 **Grass** - Open terrain, good for farms
- 🟫 **Road** - Faster movement (0.5 move cost), good for workshops
- 🟦 **Water** - Cannot cross, required for docks
- 🟢 **Forest** - Natural cover, moderate for farms
- 🔴 **Ruined Buildings** - Resource potential (60% chance), moderate for workshops
- ⬜ **Intact Buildings** - High resource potential (80% chance), best for hospitals/workshops
- 🟤 **Rubble** - Debris, poor for workshops
- 🟣 **Research Lab** - Contains The Cure (only one per map)

### Victory Conditions

**Cure Victory (Main Objective):**
1. Find the Research Lab (purple tile marked "LAB")
2. Scavenge The Cure from the lab
3. Transfer cure to a city with a hospital
4. Accumulate 1000 food and 1000 materials
5. Press **C** to Manufacture The Cure
6. **Result:** All zombies convert to survivors, map revealed, victory!
7. Score saved to Cure Leaderboard (lower turns = better)

**Survival Mode:**
- If you can't manufacture the cure, survive as long as possible
- Game Over when: No player units AND no cities remain
- Score: Number of turns survived
- Saved to High Score Leaderboard (higher = better)

### Mini-Map

Located in bottom-right corner (200×200 pixels):

**Display:**
- Explored terrain (simplified colors)
- Cities (yellow circles)
- Research Lab (purple circle)
- Player units (blue dots)
- Enemy units (red dots, visible only when in sight)
- Current viewport (white rectangle)

**Interaction:**
- Click anywhere on mini-map to instantly jump camera to that location
- Real-time updates as you explore

### Save/Load System

**Saving:**
- Press **Ctrl+S** to open save menu
- Enter filename or select existing save
- Saves all game state (units, cities, resources, XP, explored map, etc.)

**Loading:**
- Press **Ctrl+L** to open load menu
- Enter filename or click on saved game
- Completely restores game state

**Exit Protection:**
- Pressing **ESC** checks for unsaved changes
- Warning dialog appears if progress since last save
- Options: Exit anyway (Y), Cancel (N), or ESC to cancel

### Leaderboards

**High Scores** (Survival)
- Top 10 longest survival runs
- Measured in turns survived
- Saved to: `saves/highscores.json`

**Cure Leaderboard** (Victory)
- Top 10 fastest cure manufactures
- Measured in turns to victory (lower = better)
- Saved to: `saves/cure_leaderboard.json`

## Game Strategy

### Early Game (Turns 1-10)
1. Scavenge nearby ruined buildings for resources
2. Recruit scouts and use triangulation (Q key) to locate the Research Lab
3. Found your first city in a defensible location
4. Build farms to ensure food supply
5. Scout the map systematically to reveal terrain
6. **Research early techs**: Scavenging Efficiency, Advanced Farming, Industrial Workshops

### Mid Game (Turns 11-25)
1. Build multiple cities for resource production
2. Construct workshops for steady material income
3. Train soldiers to fight zombies
4. Level up units through combat
5. Establish resource networks between cities
6. Build hospitals in preparation for cure manufacturing
7. **Research combat techs**: Combat Training, Scout Training, Tactical Medicine

### Late Game (Turn 25+)
1. Super zombies appear - very dangerous!
2. Protect cities with walls
3. Accumulate resources for cure (reduced to 350/350 with Cure Research tech)
4. Transfer The Cure to a city with hospital
5. Manufacture The Cure to win!
6. **Research end-game techs**: Armor Plating, Rapid Response, Cure Research
7. OR continue surviving the endless hordes

### Pro Tips

**Unit Management:**
- Level up scouts early by exploring
- Medics become more valuable as they level (better healing)
- Soldiers excel in late-game when zombies swarm
- Use right-click to heal allies with medics

**Economy:**
- Place farms on grass for maximum food
- Place workshops on intact buildings for materials
- Build hospitals on intact buildings for medicine
- Docks provide excellent food but require water

**Tech Tree:**
- Press Y to open the tech tree at any time during your turn
- Hover over technologies to see detailed descriptions
- Economic techs (farms/workshops/hospitals bonuses) pay off quickly
- Research Documentation reduces all future tech costs by 30%
- Combat Training is extremely valuable - all new units start at level 2
- Cure Research saves 300 resources when manufacturing the cure

**Combat:**
- Super zombies deal 50 damage - avoid until you have leveled soldiers
- Focus fire on super zombies with multiple units
- Heal damaged units before they die
- Cities and buildings can be destroyed - protect them!

**Cure Route:**
- Use scout triangulation (Q key) to find Research Lab quickly
- Four triangulations reveal exact location without exploring
- Build hospitals in multiple cities as backup
- Stockpile resources in preparation
- Super zombies make late-game harder - manufacture cure sooner!

**Draw Zombies Away**
- Utilize scouts to draw zombies away from cities or other units.
- Zombies have sight distance of 2 tiles and share knowledge.
- Zombies will head towards the closest known player unit.

## Technical Details

### Procedural Generation
- Maps are 50×50 tiles
- Noise-based terrain generation
- Random city placement (3-6 ruined cities per map)
- Road networks connecting major locations
- One Research Lab per map
- Resource distribution based on building types

### AI Behavior
- Zombies move toward nearest player unit or city
- Can attack units, cities, and buildings
- Super zombies use special pathfinding for 2×2 movement
- Smart targeting system prioritizes threats

### Multi-Tile Unit System
- Super zombies occupy 2×2 grid
- Collision detection checks all occupied tiles
- Visibility checks all tiles for fog of war
- Movement validates entire footprint

## Project Structure

```
zombie_strategy_game/
├── src/
│   ├── main.py           # Main game loop, event handling, UI
│   ├── map_generator.py  # Procedural map generation, Research Lab
│   ├── game_state.py     # Game logic, units, cities, AI, save/load
│   └── renderer.py       # Graphics, UI rendering, mini-map
├── saves/                # Save files and leaderboards
│   ├── *.json           # Individual save games
│   ├── highscores.json  # Survival high scores
│   └── cure_leaderboard.json  # Cure victory times
├── requirements.txt      # Python dependencies (pygame)
└── README.md            # This file
```
