import json
import os

class Unit:
    def __init__(self, x, y, unit_type, team, difficulty='medium'):
        self.x = x
        self.y = y
        self.unit_type = unit_type  # 'survivor', 'scout', 'soldier', 'medic', 'zombie', 'super_zombie'
        self.team = team  # 'player' or 'enemy'
        self.inventory = {'food': 0, 'materials': 0, 'medicine': 0, 'cure': 0}

        # Determine difficulty multiplier for zombie stats
        if difficulty == 'easy':
            zombie_health_multiplier = 0.7
            zombie_attack_multiplier = 0.7
        elif difficulty == 'hard':
            zombie_health_multiplier = 1.4
            zombie_attack_multiplier = 1.4
        else:  # medium
            zombie_health_multiplier = 1.0
            zombie_attack_multiplier = 1.0

        # Set unit stats based on type
        if unit_type == 'scout':
            self.health = 75
            self.max_health = 75
            self.max_moves = 5
            self.attack_power = 8
            self.size = 1  # Normal units are 1x1
        elif unit_type == 'soldier':
            self.health = 120
            self.max_health = 120
            self.max_moves = 2
            self.attack_power = 20
            self.size = 1
        elif unit_type == 'medic':
            self.health = 80
            self.max_health = 80
            self.max_moves = 3
            self.attack_power = 5
            self.size = 1
        elif unit_type == 'zombie':
            self.health = int(100 * zombie_health_multiplier)
            self.max_health = int(100 * zombie_health_multiplier)
            self.max_moves = 2
            self.attack_power = int(10 * zombie_attack_multiplier)
            self.size = 1
        elif unit_type == 'super_zombie':
            self.health = int(200 * zombie_health_multiplier)
            self.max_health = int(200 * zombie_health_multiplier)
            self.max_moves = 2
            self.attack_power = int(50 * zombie_attack_multiplier)
            self.size = 2  # Super zombies are 2x2
        else:  # 'survivor' or default
            self.health = 100
            self.max_health = 100
            self.max_moves = 3
            self.attack_power = 10
            self.size = 1

        self.moves_remaining = self.max_moves

        # XP and leveling system
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 100  # XP needed for level 2

        # Track tiles explored by this unit (for scout XP)
        self.tiles_explored = set()

        # Track age for zombie leveling (zombies level up over time)
        self.age_in_turns = 0  # How many turns this unit has been alive

    def reset_moves(self):
        """Reset movement points at start of turn"""
        self.moves_remaining = self.max_moves

    def can_move(self):
        return self.moves_remaining > 0

    def move(self, dx, dy, terrain_type=None):
        """Move unit by offset, with terrain-based movement cost"""
        from map_generator import TileType

        if self.can_move():
            self.x += dx
            self.y += dy

            # Roads cost only 0.5 movement points
            if terrain_type == TileType.ROAD:
                self.moves_remaining -= 0.5
            else:
                self.moves_remaining -= 1
            return True
        return False

    def gain_xp(self, amount):
        """Gain XP and level up if enough XP earned"""
        self.xp += amount
        leveled_up = False

        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            leveled_up = True

            # Increase stats on level up
            # +10% HP and attack per level
            hp_boost = int(self.max_health * 0.1)
            attack_boost = int(self.attack_power * 0.1) + 1  # At least +1

            self.max_health += hp_boost
            self.health += hp_boost  # Also heal when leveling up
            self.attack_power += attack_boost

            # Increase XP needed for next level (exponential growth)
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)

        return leveled_up

    def zombie_age_level_up(self):
        """Level up zombie based on age (for enemy zombies only)"""
        if self.team != 'enemy' or self.unit_type not in ['zombie', 'super_zombie']:
            return False

        leveled_up = False
        target_level = 1

        # Determine target level based on age
        if self.age_in_turns >= 75:
            target_level = 4
        elif self.age_in_turns >= 50:
            target_level = 3
        elif self.age_in_turns >= 25:
            target_level = 2

        # Level up if needed
        while self.level < target_level:
            self.level += 1
            leveled_up = True

            # Increase stats on level up (same as XP leveling)
            hp_boost = int(self.max_health * 0.1)
            attack_boost = int(self.attack_power * 0.1) + 1

            self.max_health += hp_boost
            self.health += hp_boost  # Also heal when leveling up
            self.attack_power += attack_boost

        return leveled_up

class City:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name
        self.population = 5
        self.buildings = ['shelter']
        self.building_locations = {}  # Maps (x, y) -> {'type': str, 'terrain': TileType, 'level': int, 'health': int}
        self.resources = {'food': 0, 'materials': 0, 'medicine': 0, 'cure': 0}  # Start with zero resources
        self.level = 1
        self.health = 50
        self.max_health = 50

    def can_build(self, building_type):
        """Check if city has resources to build"""
        costs = {
            'farm': {'materials': 30},
            'workshop': {'materials': 50},
            'hospital': {'materials': 40},
            'wall': {'materials': 5},
            'dock': {'materials': 40},
            'survivor': {'food': 20, 'materials': 10},
            'scout': {'food': 15, 'materials': 5},
            'soldier': {'food': 30, 'materials': 20},
            'medic': {'food': 25, 'materials': 15, 'medicine': 10},
            'manufacture_cure': {'food': 500, 'materials': 500, 'medicine': 200, 'cure': 1}
        }

        # Special requirement: can only manufacture cure if city has a hospital
        if building_type == 'manufacture_cure':
            if 'hospital' not in self.buildings:
                return False

        if building_type not in costs:
            return False

        cost = costs[building_type]
        for resource, amount in cost.items():
            if self.resources.get(resource, 0) < amount:
                return False
        return True

    def build(self, building_type, tile_x, tile_y, terrain_type):
        """Construct a building at a specific location"""
        costs = {
            'farm': {'materials': 30},
            'workshop': {'materials': 50},
            'hospital': {'materials': 40},
            'wall': {'materials': 5},
            'dock': {'materials': 40},
            'survivor': {'food': 20, 'materials': 10},
            'scout': {'food': 15, 'materials': 5},
            'soldier': {'food': 30, 'materials': 20},
            'medic': {'food': 25, 'materials': 15, 'medicine': 10},
            'manufacture_cure': {'food': 500, 'materials': 500, 'medicine': 200, 'cure': 1}
        }

        if self.can_build(building_type):
            cost = costs.get(building_type, {})
            for resource, amount in cost.items():
                self.resources[resource] -= amount

            # Place building or recruit unit
            if building_type in ['survivor', 'scout', 'soldier', 'medic']:
                # Unit recruitment - return True to signal unit creation
                return True
            elif building_type == 'manufacture_cure':
                # Special building - triggers win condition
                return 'cure_manufactured'
            else:
                self.buildings.append(building_type)
                # Walls have 200 HP, other buildings have 20 HP
                health = 200 if building_type == 'wall' else 20
                self.building_locations[(tile_x, tile_y)] = {
                    'type': building_type,
                    'terrain': terrain_type,
                    'level': 1,
                    'health': health,
                    'max_health': health
                }

                # If building a wall at city location, double city HP
                if building_type == 'wall' and tile_x == self.x and tile_y == self.y:
                    self.max_health = 100
                    self.health = 100

                return True
        return False

    def produce_resources(self):
        """Produce resources based on buildings and their terrain each turn"""
        from map_generator import TileType

        production = {
            'food': 2,  # Base city production
            'materials': 2,  # Base city production
            'medicine': 0
        }

        # Calculate production from placed buildings with terrain bonuses
        for location, building_info in self.building_locations.items():
            building_type = building_info['type']
            terrain = building_info['terrain']
            level = building_info.get('level', 1)

            if building_type == 'farm':
                # Farm: 6 on grass, 3 on forest, 0 base
                food_production = 0
                if terrain == TileType.GRASS:
                    food_production = 6
                elif terrain == TileType.FOREST:
                    food_production = 3
                production['food'] += food_production * level

            elif building_type == 'dock':
                # Dock: 2x farm production (12 on water, equivalent to grass farm bonus)
                food_production = 12
                production['food'] += food_production * level

            elif building_type == 'workshop':
                # Workshop: 2 on rubble, 4 on ruined/road, 8 on intact, 0 base
                materials_production = 0
                if terrain == TileType.RUBBLE:
                    materials_production = 2
                elif terrain in [TileType.BUILDING_RUINED, TileType.ROAD]:
                    materials_production = 4
                elif terrain == TileType.BUILDING_INTACT:
                    materials_production = 8
                production['materials'] += materials_production * level

            elif building_type == 'hospital':
                # Hospital: 2 base, +4 on intact building
                medicine_production = 2
                if terrain == TileType.BUILDING_INTACT:
                    medicine_production += 4
                production['medicine'] += medicine_production * level

        # Add production to city resources
        for resource, amount in production.items():
            self.resources[resource] += amount

        return production

    def calculate_production(self):
        """Calculate total resource production per turn without actually producing"""
        from map_generator import TileType

        production = {
            'food': 2,  # Base city production
            'materials': 2,  # Base city production
            'medicine': 0
        }

        # Calculate production from placed buildings with terrain bonuses
        for location, building_info in self.building_locations.items():
            building_type = building_info['type']
            terrain = building_info['terrain']
            level = building_info.get('level', 1)

            if building_type == 'farm':
                food_production = 0
                if terrain == TileType.GRASS:
                    food_production = 6
                elif terrain == TileType.FOREST:
                    food_production = 3
                production['food'] += food_production * level

            elif building_type == 'dock':
                food_production = 12
                production['food'] += food_production * level

            elif building_type == 'workshop':
                materials_production = 0
                if terrain == TileType.RUBBLE:
                    materials_production = 2
                elif terrain in [TileType.BUILDING_RUINED, TileType.ROAD]:
                    materials_production = 4
                elif terrain == TileType.BUILDING_INTACT:
                    materials_production = 8
                production['materials'] += materials_production * level

            elif building_type == 'hospital':
                medicine_production = 2
                if terrain == TileType.BUILDING_INTACT:
                    medicine_production += 4
                production['medicine'] += medicine_production * level

        return production

    def can_upgrade_building(self, tile_x, tile_y):
        """Check if a building can be upgraded"""
        if (tile_x, tile_y) not in self.building_locations:
            return False

        building_info = self.building_locations[(tile_x, tile_y)]
        current_level = building_info.get('level', 1)

        # Max level is 3
        if current_level >= 3:
            return False

        # Upgrade cost scales with level (50% more than original build cost per level)
        upgrade_costs = {
            'farm': {'materials': 15 * (current_level + 1)},
            'workshop': {'materials': 25 * (current_level + 1)},
            'hospital': {'materials': 20 * (current_level + 1)},
            'wall': {'materials': 12 * (current_level + 1)},
            'dock': {'materials': 20 * (current_level + 1)}
        }

        building_type = building_info['type']
        if building_type not in upgrade_costs:
            return False

        cost = upgrade_costs[building_type]
        for resource, amount in cost.items():
            if self.resources.get(resource, 0) < amount:
                return False
        return True

    def upgrade_building(self, tile_x, tile_y):
        """Upgrade a building at the specified location"""
        if not self.can_upgrade_building(tile_x, tile_y):
            return False

        building_info = self.building_locations[(tile_x, tile_y)]
        current_level = building_info.get('level', 1)
        building_type = building_info['type']

        # Deduct upgrade cost
        upgrade_costs = {
            'farm': {'materials': 15 * (current_level + 1)},
            'workshop': {'materials': 25 * (current_level + 1)},
            'hospital': {'materials': 20 * (current_level + 1)},
            'wall': {'materials': 12 * (current_level + 1)},
            'dock': {'materials': 20 * (current_level + 1)}
        }

        cost = upgrade_costs[building_type]
        for resource, amount in cost.items():
            self.resources[resource] -= amount

        # Upgrade the building
        building_info['level'] = current_level + 1
        return True

class GameState:
    def __init__(self, map_grid, resources, research_lab_pos=None, difficulty='medium'):
        self.map_grid = map_grid
        self.resources = resources
        self.research_lab_pos = research_lab_pos
        self.turn = 0
        self.current_team = 'player'
        self.game_won = False  # Track if player has won via cure
        self.difficulty = difficulty  # 'easy', 'medium', or 'hard'

        # Difficulty settings
        if difficulty == 'easy':
            self.zombie_spawn_rate = 0.15  # 15% chance per turn
            self.zombie_spawn_count_min = 1
            self.zombie_spawn_count_max = 2
            self.starting_resources_multiplier = 1.5
        elif difficulty == 'hard':
            self.zombie_spawn_rate = 0.35  # 35% chance per turn
            self.zombie_spawn_count_min = 2
            self.zombie_spawn_count_max = 4
            self.starting_resources_multiplier = 0.7
        else:  # medium
            self.zombie_spawn_rate = 0.25  # 25% chance per turn
            self.zombie_spawn_count_min = 1
            self.zombie_spawn_count_max = 3
            self.starting_resources_multiplier = 1.0

        # Add the cure to the research lab as a resource
        if research_lab_pos:
            self.resources[research_lab_pos] = {
                'food': 0,
                'materials': 0,
                'medicine': 0,
                'cure': 1
            }

        # Fog of war - track explored tiles
        self.explored = [[False for _ in range(len(map_grid[0]))] for _ in range(len(map_grid))]
        self.visible = [[False for _ in range(len(map_grid[0]))] for _ in range(len(map_grid))]

        # Initialize player units
        self.units = []
        self.spawn_initial_units()

        # Initialize cities
        self.cities = []

        # Update initial visibility
        self.update_visibility()

    def spawn_initial_units(self):
        """Spawn starting survivors and zombies"""
        # Spawn 3 player survivors with starting resources
        for i in range(3):
            survivor = Unit(5 + i, 5, 'survivor', 'player', self.difficulty)
            # Give each survivor some starting resources (adjusted by difficulty)
            # Medicine cannot be found - must be produced by hospitals
            survivor.inventory['food'] = int(20 * self.starting_resources_multiplier)
            survivor.inventory['materials'] = int(40 * self.starting_resources_multiplier)
            survivor.inventory['medicine'] = 0
            self.units.append(survivor)

        # Spawn some zombies scattered around
        import random
        for _ in range(5):
            x = random.randint(10, len(self.map_grid[0]) - 5)
            y = random.randint(10, len(self.map_grid) - 5)
            zombie = Unit(x, y, 'zombie', 'enemy', self.difficulty)
            self.units.append(zombie)

    def spawn_zombies(self):
        """Spawn zombies at map edges, escalating with turn count and difficulty"""
        import random

        # Spawn zombies based on difficulty spawn rate
        if random.random() > self.zombie_spawn_rate:
            return  # No zombies this turn

        # Calculate base spawn count based on turn (escalating difficulty)
        # Turn 1-5: 1-2 zombies per turn
        # Turn 6-10: 2-3 zombies per turn
        # Turn 11-15: 3-4 zombies per turn
        # Turn 16-20: 4-5 zombies per turn
        # Turn 21-30: 5-7 zombies per turn
        # Turn 31-40: 7-10 zombies per turn
        # Turn 41+: 10-15 zombies per turn

        base_spawn_count = 0
        if self.turn <= 5:
            base_spawn_count = random.randint(1, 2)
        elif self.turn <= 10:
            base_spawn_count = random.randint(2, 3)
        elif self.turn <= 15:
            base_spawn_count = random.randint(3, 4)
        elif self.turn <= 20:
            base_spawn_count = random.randint(4, 5)
        elif self.turn <= 30:
            base_spawn_count = random.randint(5, 7)
        elif self.turn <= 40:
            base_spawn_count = random.randint(7, 10)
        else:
            base_spawn_count = random.randint(10, 15)

        # Apply difficulty modifier - add some randomness within difficulty range
        spawn_count = base_spawn_count + random.randint(self.zombie_spawn_count_min, self.zombie_spawn_count_max) - 1

        map_width = len(self.map_grid[0])
        map_height = len(self.map_grid)

        for _ in range(spawn_count):
            # Randomly choose which edge: 0=top, 1=right, 2=bottom, 3=left
            edge = random.randint(0, 3)

            if edge == 0:  # Top edge
                x = random.randint(0, map_width - 1)
                y = 0
            elif edge == 1:  # Right edge
                x = map_width - 1
                y = random.randint(0, map_height - 1)
            elif edge == 2:  # Bottom edge
                x = random.randint(0, map_width - 1)
                y = map_height - 1
            else:  # Left edge
                x = 0
                y = random.randint(0, map_height - 1)

            # Make sure there's not already a unit at this position
            if not self.get_unit_at(x, y):
                zombie = Unit(x, y, 'zombie', 'enemy', self.difficulty)
                self.units.append(zombie)

        if spawn_count > 0:
            print(f"⚠ {spawn_count} zombie(s) have appeared at the map edges!")

        # Spawn super zombies after turn 25 (every 3-4 turns)
        if self.turn >= 25:
            spawn_super = False
            if self.turn % 3 == 0 or self.turn % 4 == 0:
                spawn_super = True

            if spawn_super:
                # Try to spawn a super zombie at a map edge
                # Need to ensure 2x2 space is available
                edge = random.randint(0, 3)

                # For super zombies, we need to be careful about edge placement
                # Position (x,y) is top-left corner, occupies (x,y), (x+1,y), (x,y+1), (x+1,y+1)
                if edge == 0:  # Top edge
                    x = random.randint(0, map_width - 2)  # -2 to ensure room for 2x2
                    y = 0
                elif edge == 1:  # Right edge
                    x = map_width - 2  # Place at right edge with room for size
                    y = random.randint(0, map_height - 2)
                elif edge == 2:  # Bottom edge
                    x = random.randint(0, map_width - 2)
                    y = map_height - 2
                else:  # Left edge
                    x = 0
                    y = random.randint(0, map_height - 2)

                # Check if all 4 tiles are free
                tiles_free = True
                for dy in range(2):
                    for dx in range(2):
                        if self.get_unit_at(x + dx, y + dy):
                            tiles_free = False
                            break
                    if not tiles_free:
                        break

                if tiles_free:
                    super_zombie = Unit(x, y, 'super_zombie', 'enemy', self.difficulty)
                    self.units.append(super_zombie)
                    # Display stats based on difficulty
                    print(f"💀 A SUPER ZOMBIE has appeared! (HP: {super_zombie.max_health}, Attack: {super_zombie.attack_power})")

    def get_unit_at(self, x, y, exclude_unit=None):
        """Get unit at position, accounting for multi-tile units"""
        for unit in self.units:
            # Skip the excluded unit (used when checking if a unit can move to a position)
            if exclude_unit and unit == exclude_unit:
                continue

            # Check if the position is within the unit's occupied area
            if unit.size == 1:
                # Normal 1x1 unit
                if unit.x == x and unit.y == y:
                    return unit
            else:
                # Multi-tile unit (2x2 for super zombies)
                # Unit occupies (x, y) through (x+size-1, y+size-1)
                if unit.x <= x < unit.x + unit.size and unit.y <= y < unit.y + unit.size:
                    return unit
        return None

    def check_collision_for_multitile_unit(self, unit, new_x, new_y):
        """Check all tiles a multi-tile unit would occupy for collisions
        Returns tuple: (target_unit, target_city, target_building) or (None, None, None)"""
        unit_size = getattr(unit, 'size', 1)

        # Check all tiles the unit would occupy
        for dy in range(unit_size):
            for dx in range(unit_size):
                check_x = new_x + dx
                check_y = new_y + dy

                # Check for unit collision
                target_unit = self.get_unit_at(check_x, check_y, exclude_unit=unit)
                if target_unit:
                    return (target_unit, None, None)

                # Check for city collision
                target_city = self.get_city_at(check_x, check_y)
                if target_city:
                    return (None, target_city, None)

                # Check for building collision
                target_building = self.get_building_at(check_x, check_y)
                if target_building:
                    return (None, None, target_building)

        return (None, None, None)

    def get_city_at(self, x, y):
        """Get city at position"""
        for city in self.cities:
            if city.x == x and city.y == y:
                return city
        return None

    def drop_unit_inventory(self, unit):
        """Drop a unit's inventory as resources at its death location"""
        if not unit:
            return

        # Check if unit has any resources
        has_items = any(unit.inventory[res] > 0 for res in ['food', 'materials', 'medicine', 'cure'])

        if has_items:
            position = (unit.x, unit.y)

            # If there's already resources at this location, add to them
            if position in self.resources:
                for resource in ['food', 'materials', 'medicine', 'cure']:
                    self.resources[position][resource] = self.resources[position].get(resource, 0) + unit.inventory[resource]
            else:
                # Create new resource pile at this location
                self.resources[position] = {
                    'food': unit.inventory['food'],
                    'materials': unit.inventory['materials'],
                    'medicine': unit.inventory['medicine'],
                    'cure': unit.inventory['cure']
                }

            # Log what was dropped
            dropped_items = {k: v for k, v in unit.inventory.items() if v > 0}
            if dropped_items:
                print(f"💀 {unit.unit_type} dropped: {dropped_items} at ({unit.x}, {unit.y})")

    def end_turn(self):
        """End current player's turn"""
        if self.current_team == 'player':
            self.current_team = 'enemy'
            # Reset enemy unit moves
            for unit in self.units:
                if unit.team == 'enemy':
                    unit.reset_moves()
            # AI turn for zombies
            self.execute_ai_turn()
        else:
            self.current_team = 'player'
            self.turn += 1
            # Reset player unit moves
            for unit in self.units:
                if unit.team == 'player':
                    unit.reset_moves()

            # Autosave at the start of player's turn
            self.autosave()

            # Produce resources in all cities at the start of player's turn
            for city in self.cities:
                production = city.produce_resources()
                # Print production report
                if any(production.values()):
                    prod_str = ', '.join([f"{k}: +{v}" for k, v in production.items() if v > 0])
                    print(f"{city.name} produced: {prod_str}")

            # Spawn new zombies (escalating with turn count)
            self.spawn_zombies()

            # Update fog of war
            self.update_visibility()

    def get_ai_visible_targets(self):
        """Get player units visible to ANY zombie (shared vision network)"""
        visible_player_units = set()

        # Check what each zombie can see
        for zombie in self.units:
            if zombie.team == 'enemy':
                vision_range = 2  # Zombies have 2 tile vision

                # Check all player units
                for pu in self.units:
                    if pu.team == 'player':
                        # Use Chebyshev distance (max of dx, dy) for vision
                        distance = max(abs(pu.x - zombie.x), abs(pu.y - zombie.y))
                        if distance <= vision_range:
                            visible_player_units.add(pu)

        return visible_player_units

    def collect_zombie_movements(self):
        """Collect zombie movements for animation without executing them
        Returns a list of (unit, old_x, old_y, new_x, new_y, action_type, action_data)"""
        import random

        movements = []

        # Age all zombies and check for level-ups (instant, no animation needed)
        for unit in self.units:
            if unit.team == 'enemy' and (unit.unit_type == 'zombie' or unit.unit_type == 'super_zombie'):
                unit.age_in_turns += 1
                if unit.zombie_age_level_up():
                    print(f"🧟 {unit.unit_type} leveled up to level {unit.level}! (Age: {unit.age_in_turns} turns)")

        # Get shared visible targets (zombies share vision network)
        visible_player_units = self.get_ai_visible_targets()

        # Calculate map center for wandering behavior
        map_center_x = len(self.map_grid[0]) // 2
        map_center_y = len(self.map_grid) // 2

        # Collect all movements for each zombie
        for unit in self.units[:]:  # Use slice to avoid modification during iteration
            if unit.team == 'enemy' and (unit.unit_type == 'zombie' or unit.unit_type == 'super_zombie'):
                while unit.can_move():
                    old_x, old_y = unit.x, unit.y
                    movement = self._calculate_single_zombie_move(unit, visible_player_units, map_center_x, map_center_y)
                    if movement:
                        movements.append(movement)
                    else:
                        break  # No valid move found

        return movements

    def _calculate_single_zombie_move(self, unit, visible_player_units, map_center_x, map_center_y):
        """Calculate a single zombie move and return movement data
        Returns (unit, old_x, old_y, new_x, new_y, action_type, action_data) or None"""
        import random

        old_x, old_y = unit.x, unit.y
        targets = []

        # Add visible player units as targets (fog of war)
        for pu in visible_player_units:
            targets.append(('unit', pu, abs(pu.x - unit.x) + abs(pu.y - unit.y)))

        # Add cities as targets (permanent knowledge)
        for city in self.cities:
            targets.append(('city', city, abs(city.x - unit.x) + abs(city.y - unit.y)))

        # Add buildings as targets (permanent knowledge)
        # Walls are deprioritized with a large distance penalty
        for city in self.cities:
            for (bx, by), building in city.building_locations.items():
                distance = abs(bx - unit.x) + abs(by - unit.y)
                # Add large penalty to walls so they're only targeted if nothing else is available
                if building['type'] == 'wall':
                    distance += 1000
                targets.append(('building', (city, bx, by, building), distance))

        if targets:
            # Find nearest target (walls will have +1000 distance penalty)
            target_type, target_data, _ = min(targets, key=lambda t: t[2])

            if target_type == 'unit':
                target_x, target_y = target_data.x, target_data.y
            elif target_type == 'city':
                target_x, target_y = target_data.x, target_data.y
            else:  # building
                _, target_x, target_y, _ = target_data

            # Calculate preferred direction toward target
            dx = 1 if target_x > unit.x else -1 if target_x < unit.x else 0
            dy = 1 if target_y > unit.y else -1 if target_y < unit.y else 0

            # Random movement if same position
            if dx == 0 and dy == 0:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])

            # Try primary direction first, then perpendicular directions if blocked by friendly
            move_options = []

            if dx != 0 and dy != 0:
                move_options = [(dx, dy), (dx, 0), (0, dy)]
            elif dx != 0:
                move_options = [(dx, 0), (dx, 1), (dx, -1)]
            elif dy != 0:
                move_options = [(0, dy), (1, dy), (-1, dy)]
            else:
                move_options = [(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))]

            # Try each move option
            for try_dx, try_dy in move_options:
                if try_dx == 0 and try_dy == 0:
                    continue

                new_x = unit.x + try_dx
                new_y = unit.y + try_dy

                # Check bounds
                unit_size = getattr(unit, 'size', 1)
                bounds_ok = True
                if unit_size > 1:
                    for sy in range(unit_size):
                        for sx in range(unit_size):
                            if not (0 <= new_x + sx < len(self.map_grid[0]) and
                                   0 <= new_y + sy < len(self.map_grid)):
                                bounds_ok = False
                                break
                        if not bounds_ok:
                            break
                else:
                    bounds_ok = (0 <= new_x < len(self.map_grid[0]) and
                                0 <= new_y < len(self.map_grid))

                if not bounds_ok:
                    continue

                # Check what's at the target position
                if unit_size > 1:
                    target_unit, target_city, target_building = self.check_collision_for_multitile_unit(unit, new_x, new_y)
                else:
                    target_unit = self.get_unit_at(new_x, new_y, exclude_unit=unit)
                    target_city = self.get_city_at(new_x, new_y)
                    target_building = self.get_building_at(new_x, new_y)

                if target_unit and target_unit.team != unit.team:
                    # Return attack action
                    return (unit, old_x, old_y, new_x, new_y, 'attack_unit', target_unit)
                elif target_city:
                    # Return attack city action
                    return (unit, old_x, old_y, new_x, new_y, 'attack_city', target_city)
                elif target_building:
                    # Check if there's a player unit on this building (prioritize unit)
                    unit_on_building = self.get_unit_at(new_x, new_y, exclude_unit=unit)
                    if unit_on_building and unit_on_building.team == 'player':
                        return (unit, old_x, old_y, new_x, new_y, 'attack_unit_on_building', (unit_on_building, target_building))
                    else:
                        return (unit, old_x, old_y, new_x, new_y, 'attack_building', target_building)
                elif not target_unit:
                    # Check if target is a wall (impassable to zombies)
                    if target_building and target_building['type'] == 'wall':
                        continue
                    # Return move action
                    terrain = self.map_grid[new_y][new_x]
                    return (unit, old_x, old_y, new_x, new_y, 'move', terrain)

        return None  # No valid move found

    def execute_ai_turn(self):
        """AI for zombie movement with fog of war"""
        import random

        # Age all zombies and check for level-ups
        for unit in self.units:
            if unit.team == 'enemy' and (unit.unit_type == 'zombie' or unit.unit_type == 'super_zombie'):
                unit.age_in_turns += 1
                if unit.zombie_age_level_up():
                    print(f"🧟 {unit.unit_type} leveled up to level {unit.level}! (Age: {unit.age_in_turns} turns)")

        # Get shared visible targets (zombies share vision network)
        visible_player_units = self.get_ai_visible_targets()

        # Calculate map center for wandering behavior
        map_center_x = len(self.map_grid[0]) // 2
        map_center_y = len(self.map_grid) // 2

        for unit in self.units:
            if unit.team == 'enemy' and (unit.unit_type == 'zombie' or unit.unit_type == 'super_zombie'):
                while unit.can_move():
                    targets = []

                    # Add visible player units as targets (fog of war)
                    for pu in visible_player_units:
                        targets.append(('unit', pu, abs(pu.x - unit.x) + abs(pu.y - unit.y)))

                    # Add cities as targets (permanent knowledge)
                    for city in self.cities:
                        targets.append(('city', city, abs(city.x - unit.x) + abs(city.y - unit.y)))

                    # Add buildings as targets (permanent knowledge)
                    # Walls are deprioritized with a large distance penalty
                    for city in self.cities:
                        for (bx, by), building in city.building_locations.items():
                            distance = abs(bx - unit.x) + abs(by - unit.y)
                            # Add large penalty to walls so they're only targeted if nothing else is available
                            if building['type'] == 'wall':
                                distance += 1000
                            targets.append(('building', (city, bx, by, building), distance))

                    if targets:
                        # Find nearest target (walls will have +1000 distance penalty)
                        target_type, target_data, _ = min(targets, key=lambda t: t[2])

                        if target_type == 'unit':
                            target_x, target_y = target_data.x, target_data.y
                        elif target_type == 'city':
                            target_x, target_y = target_data.x, target_data.y
                        else:  # building
                            _, target_x, target_y, _ = target_data

                        # Calculate preferred direction toward target
                        dx = 1 if target_x > unit.x else -1 if target_x < unit.x else 0
                        dy = 1 if target_y > unit.y else -1 if target_y < unit.y else 0

                        # Random movement if same position
                        if dx == 0 and dy == 0:
                            dx = random.choice([-1, 0, 1])
                            dy = random.choice([-1, 0, 1])

                        # Try primary direction first, then perpendicular directions if blocked by friendly
                        # This prevents zombies from bunching in single file lines
                        move_options = []

                        # Primary diagonal move
                        if dx != 0 and dy != 0:
                            move_options = [(dx, dy), (dx, 0), (0, dy)]
                        # Primary horizontal move
                        elif dx != 0:
                            move_options = [(dx, 0), (dx, 1), (dx, -1)]
                        # Primary vertical move
                        elif dy != 0:
                            move_options = [(0, dy), (1, dy), (-1, dy)]
                        else:
                            move_options = [(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))]

                        # Try each move option until we find a valid one
                        moved = False
                        for try_dx, try_dy in move_options:
                            if try_dx == 0 and try_dy == 0:
                                continue

                            new_x = unit.x + try_dx
                            new_y = unit.y + try_dy

                            # Check bounds (for multi-tile units, check all tiles)
                            unit_size = getattr(unit, 'size', 1)
                            bounds_ok = True
                            if unit_size > 1:
                                # Check all tiles the unit would occupy
                                for sy in range(unit_size):
                                    for sx in range(unit_size):
                                        if not (0 <= new_x + sx < len(self.map_grid[0]) and
                                               0 <= new_y + sy < len(self.map_grid)):
                                            bounds_ok = False
                                            break
                                    if not bounds_ok:
                                        break
                            else:
                                bounds_ok = (0 <= new_x < len(self.map_grid[0]) and
                                            0 <= new_y < len(self.map_grid))

                            if not bounds_ok:
                                continue  # Try next move option

                            # Check what's at the target position (for multi-tile units, check ALL tiles)
                            if unit_size > 1:
                                target_unit, target_city, target_building = self.check_collision_for_multitile_unit(unit, new_x, new_y)
                            else:
                                target_unit = self.get_unit_at(new_x, new_y, exclude_unit=unit)
                                target_city = self.get_city_at(new_x, new_y)
                                target_building = self.get_building_at(new_x, new_y)

                            if target_unit and target_unit.team != unit.team:
                                # Attack the enemy unit
                                target_unit.health -= unit.attack_power
                                print(f"Zombie attacks {target_unit.unit_type}! Health: {target_unit.health}")
                                if target_unit.health <= 0:
                                    # Drop inventory before removing unit
                                    self.drop_unit_inventory(target_unit)

                                    self.units.remove(target_unit)
                                    print(f"{target_unit.unit_type} was killed by zombie!")
                                    self.update_visibility()
                                unit.moves_remaining -= 1
                                moved = True
                                break
                            elif target_city:
                                # Attack the city
                                target_city.health -= unit.attack_power
                                print(f"Zombie attacks {target_city.name}! City Health: {target_city.health}/{target_city.max_health}")
                                if target_city.health <= 0:
                                    print(f"{target_city.name} has been destroyed by zombies!")
                                    self.cities.remove(target_city)
                                    self.update_visibility()
                                unit.moves_remaining -= 1
                                moved = True
                                break
                            elif target_building:
                                # Check if there's a player unit on this building (prioritize unit)
                                unit_on_building = self.get_unit_at(new_x, new_y, exclude_unit=unit)
                                if unit_on_building and unit_on_building.team == 'player':
                                    # Attack the unit instead of the building
                                    unit_on_building.health -= unit.attack_power
                                    print(f"Zombie attacks {unit_on_building.unit_type} on {target_building['type']}! Health: {unit_on_building.health}")
                                    if unit_on_building.health <= 0:
                                        # Drop inventory before removing unit
                                        self.drop_unit_inventory(unit_on_building)
                                        self.units.remove(unit_on_building)
                                        print(f"{unit_on_building.unit_type} was killed by zombie!")
                                        self.update_visibility()
                                else:
                                    # Attack the building
                                    target_building['health'] -= unit.attack_power
                                    print(f"Zombie attacks {target_building['type']}! Building Health: {target_building['health']}/{target_building['max_health']}")
                                    if target_building['health'] <= 0:
                                        print(f"{target_building['type']} has been destroyed by zombies!")
                                        # Find and remove the building
                                        for city in self.cities:
                                            if (new_x, new_y) in city.building_locations:
                                                del city.building_locations[(new_x, new_y)]
                                                if target_building['type'] in city.buildings:
                                                    city.buildings.remove(target_building['type'])
                                                break
                                unit.moves_remaining -= 1
                                moved = True
                                break
                            elif not target_unit:
                                # Check if target is a wall (impassable to zombies)
                                if target_building and target_building['type'] == 'wall':
                                    # Walls are impassable to zombies, try next move option
                                    continue
                                # Move to empty tile
                                terrain = self.map_grid[new_y][new_x]
                                unit.move(try_dx, try_dy, terrain)
                                moved = True
                                break
                            # else: blocked by friendly unit, try next move option

                        # If no valid move found after trying all options, stop
                        if not moved:
                            break
                    else:
                        # No targets visible - wander randomly toward map center
                        # Calculate direction toward center with random variation
                        dx_to_center = 1 if map_center_x > unit.x else -1 if map_center_x < unit.x else 0
                        dy_to_center = 1 if map_center_y > unit.y else -1 if map_center_y < unit.y else 0

                        # 40% chance to move toward center, 60% random
                        if random.random() < 0.4:
                            dx = dx_to_center
                            dy = dy_to_center
                        else:
                            dx = random.choice([-1, 0, 1])
                            dy = random.choice([-1, 0, 1])

                        # Add some randomness even when moving toward center
                        if random.random() < 0.3:
                            dx = random.choice([-1, 0, 1])
                        if random.random() < 0.3:
                            dy = random.choice([-1, 0, 1])

                        # Don't stay still
                        if dx == 0 and dy == 0:
                            dx = random.choice([-1, 0, 1])
                            dy = random.choice([-1, 0, 1])

                        new_x = unit.x + dx
                        new_y = unit.y + dy

                        # Check bounds
                        unit_size = getattr(unit, 'size', 1)
                        bounds_ok = True
                        if unit_size > 1:
                            for sy in range(unit_size):
                                for sx in range(unit_size):
                                    if not (0 <= new_x + sx < len(self.map_grid[0]) and
                                           0 <= new_y + sy < len(self.map_grid)):
                                        bounds_ok = False
                                        break
                                if not bounds_ok:
                                    break
                        else:
                            bounds_ok = (0 <= new_x < len(self.map_grid[0]) and
                                        0 <= new_y < len(self.map_grid))

                        if bounds_ok:
                            # Check for collisions
                            if unit_size > 1:
                                target_unit, target_city, target_building = self.check_collision_for_multitile_unit(unit, new_x, new_y)
                            else:
                                target_unit = self.get_unit_at(new_x, new_y, exclude_unit=unit)
                                target_city = self.get_city_at(new_x, new_y)
                                target_building = self.get_building_at(new_x, new_y)

                            if not target_unit and not target_city:
                                # Check if it's a wall (impassable to zombies)
                                if target_building and target_building['type'] == 'wall':
                                    # Walls are impassable, stop moving
                                    break
                                # Move to empty tile
                                terrain = self.map_grid[new_y][new_x]
                                unit.move(dx, dy, terrain)
                            else:
                                # Blocked, stop moving
                                break
                        else:
                            # Out of bounds, stop moving
                            break

    def update_visibility(self):
        """Update which tiles are visible (and explored) based on player unit positions"""
        # Reset visibility
        for y in range(len(self.visible)):
            for x in range(len(self.visible[0])):
                self.visible[y][x] = False

        # Mark tiles visible from player units and cities
        for unit in self.units:
            if unit.team == 'player':
                # Scouts have vision range of 3, others have 2
                vision_range = 3 if unit.unit_type == 'scout' else 2
                self._reveal_area(unit.x, unit.y, vision_range)

        for city in self.cities:
            self._reveal_area(city.x, city.y, 3)

            # Buildings also provide vision
            for (bx, by), building in city.building_locations.items():
                self._reveal_area(bx, by, 3)

    def _reveal_area(self, center_x, center_y, radius):
        """Reveal tiles in a square area around a point"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x = center_x + dx
                y = center_y + dy
                if 0 <= x < len(self.map_grid[0]) and 0 <= y < len(self.map_grid):
                    self.visible[y][x] = True
                    self.explored[y][x] = True

    def can_found_city(self, x, y):
        """Check if a city can be founded at this location"""
        min_distance = 3
        for city in self.cities:
            distance = max(abs(city.x - x), abs(city.y - y))
            if distance < min_distance:
                return False
        return True

    def is_game_over(self):
        """Check if the game is over (no player units AND no cities)"""
        player_units = [u for u in self.units if u.team == 'player']
        if not player_units and not self.cities:
            return True
        return False

    def manufacture_cure(self):
        """Handle the manufacture of the cure - convert all zombies to survivors and reveal map"""
        self.game_won = True

        # Reveal entire map
        for y in range(len(self.explored)):
            for x in range(len(self.explored[0])):
                self.explored[y][x] = True
                self.visible[y][x] = True

        # Convert all zombies to player survivors
        zombies = [u for u in self.units if u.team == 'enemy']
        for zombie in zombies:
            # Convert zombie to survivor
            zombie.team = 'player'
            zombie.unit_type = 'survivor'
            # Reset stats to survivor defaults
            zombie.health = 100
            zombie.max_health = 100
            zombie.max_moves = 3
            zombie.attack_power = 10
            zombie.size = 1
            zombie.reset_moves()

        print(f"🎉 THE CURE HAS BEEN MANUFACTURED! All {len(zombies)} zombies have been cured!")
        print(f"🏆 VICTORY! You survived {self.turn} turns to save humanity!")

    def found_city(self, x, y, name):
        """Create a new city at location"""
        if not self.can_found_city(x, y):
            return None
        city = City(x, y, name)
        self.cities.append(city)
        self.update_visibility()  # Update fog of war
        return city

    def get_building_at(self, x, y):
        """Check if there's a building at this location"""
        for city in self.cities:
            if (x, y) in city.building_locations:
                return city.building_locations[(x, y)]
        return None

    def get_total_resources(self):
        """Calculate total resources across all player units and cities"""
        total = {'food': 0, 'materials': 0, 'medicine': 0, 'cure': 0}

        # Add resources from all player units
        for unit in self.units:
            if unit.team == 'player':
                for resource in total.keys():
                    total[resource] += unit.inventory.get(resource, 0)

        # Add resources from all cities
        for city in self.cities:
            for resource in total.keys():
                total[resource] += city.resources.get(resource, 0)

        return total

    def autosave(self):
        """Automatically save the game to a single autosave file"""
        # Always use the same filename for autosave
        self.save_game('autosave.json')

    def save_game(self, filename='savegame.json'):
        """Save the game state to a JSON file"""
        from map_generator import TileType

        save_data = {
            'turn': self.turn,
            'current_team': self.current_team,
            'game_won': self.game_won,
            'difficulty': self.difficulty,
            'research_lab_pos': list(self.research_lab_pos) if self.research_lab_pos else None,
            'map_grid': [[int(tile) for tile in row] for row in self.map_grid],
            'resources': {f"{x},{y}": res for (x, y), res in self.resources.items()},
            'explored': [[bool(cell) for cell in row] for row in self.explored],
            'units': [{
                'x': unit.x,
                'y': unit.y,
                'unit_type': unit.unit_type,
                'team': unit.team,
                'health': unit.health,
                'max_health': unit.max_health,
                'attack_power': unit.attack_power,
                'moves_remaining': unit.moves_remaining,
                'inventory': unit.inventory,
                'xp': unit.xp,
                'level': unit.level,
                'xp_to_next_level': unit.xp_to_next_level,
                'size': getattr(unit, 'size', 1),
                'tiles_explored': [list(tile) for tile in getattr(unit, 'tiles_explored', set())]
            } for unit in self.units],
            'cities': [{
                'x': city.x,
                'y': city.y,
                'name': city.name,
                'population': city.population,
                'buildings': city.buildings,
                'building_locations': {
                    f"{x},{y}": {
                        'type': info['type'],
                        'terrain': int(info['terrain']),
                        'level': info.get('level', 1),
                        'health': info.get('health', 20),
                        'max_health': info.get('max_health', 20)
                    } for (x, y), info in city.building_locations.items()
                },
                'resources': city.resources,
                'level': city.level,
                'health': city.health,
                'max_health': city.max_health
            } for city in self.cities]
        }

        # Save to file in the saves directory
        saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
        os.makedirs(saves_dir, exist_ok=True)
        filepath = os.path.join(saves_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)

        # Only print message if it's not an autosave
        if filename != 'autosave.json':
            print(f"Game saved to {filepath}")
        return filepath

    @staticmethod
    def load_game(filename='savegame.json'):
        """Load a game state from a JSON file"""
        from map_generator import TileType

        # Load from saves directory
        saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
        filepath = os.path.join(saves_dir, filename)

        if not os.path.exists(filepath):
            print(f"Save file not found: {filepath}")
            return None

        try:
            with open(filepath, 'r') as f:
                save_data = json.load(f)
        except Exception as e:
            print(f"Error loading save file {filepath}: {e}")
            return None

        # Validate save_data is a dictionary
        if not isinstance(save_data, dict):
            print(f"Invalid save file format: expected dictionary, got {type(save_data)}")
            return None

        # Reconstruct map_grid with TileType values
        map_grid = [[tile for tile in row] for row in save_data['map_grid']]

        # Reconstruct resources dictionary
        resources = {tuple(map(int, k.split(','))): v for k, v in save_data['resources'].items()}

        # Create game state
        game_state = GameState.__new__(GameState)
        game_state.map_grid = map_grid
        game_state.resources = resources
        game_state.turn = save_data['turn']
        game_state.current_team = save_data['current_team']
        game_state.game_won = save_data.get('game_won', False)
        game_state.difficulty = save_data.get('difficulty', 'medium')  # Default to medium if not present
        game_state.research_lab_pos = tuple(save_data['research_lab_pos']) if save_data.get('research_lab_pos') else None
        game_state.explored = [[bool(cell) for cell in row] for row in save_data['explored']]
        game_state.visible = [[False for _ in range(len(map_grid[0]))] for _ in range(len(map_grid))]

        # Re-initialize difficulty settings based on loaded difficulty
        if game_state.difficulty == 'easy':
            game_state.zombie_spawn_rate = 0.15
            game_state.zombie_spawn_count_min = 1
            game_state.zombie_spawn_count_max = 2
            game_state.starting_resources_multiplier = 1.5
        elif game_state.difficulty == 'hard':
            game_state.zombie_spawn_rate = 0.35
            game_state.zombie_spawn_count_min = 2
            game_state.zombie_spawn_count_max = 4
            game_state.starting_resources_multiplier = 0.7
        else:  # medium
            game_state.zombie_spawn_rate = 0.25
            game_state.zombie_spawn_count_min = 1
            game_state.zombie_spawn_count_max = 3
            game_state.starting_resources_multiplier = 1.0

        # Reconstruct units
        game_state.units = []
        for unit_data in save_data['units']:
            unit = Unit(unit_data['x'], unit_data['y'], unit_data['unit_type'], unit_data['team'], game_state.difficulty)
            unit.health = unit_data['health']
            unit.max_health = unit_data.get('max_health', unit.max_health)
            unit.attack_power = unit_data.get('attack_power', unit.attack_power)
            unit.moves_remaining = unit_data['moves_remaining']
            unit.inventory = unit_data['inventory']
            unit.xp = unit_data.get('xp', 0)
            unit.level = unit_data.get('level', 1)
            unit.xp_to_next_level = unit_data.get('xp_to_next_level', 100)
            unit.size = unit_data.get('size', 1)
            unit.tiles_explored = set(tuple(tile) for tile in unit_data.get('tiles_explored', []))
            game_state.units.append(unit)

        # Reconstruct cities
        game_state.cities = []
        for city_data in save_data['cities']:
            city = City(city_data['x'], city_data['y'], city_data['name'])
            city.population = city_data['population']
            city.buildings = city_data['buildings']
            city.building_locations = {
                tuple(map(int, k.split(','))): {
                    'type': info['type'],
                    'terrain': info['terrain'],
                    'level': info.get('level', 1),
                    'health': info.get('health', 20),
                    'max_health': info.get('max_health', 20)
                } for k, info in city_data['building_locations'].items()
            }
            city.resources = city_data['resources']
            city.level = city_data['level']
            city.health = city_data.get('health', 50)
            city.max_health = city_data.get('max_health', 50)
            game_state.cities.append(city)

        # Update visibility
        game_state.update_visibility()

        print(f"Game loaded from {filepath}")
        return game_state

    @staticmethod
    def save_high_score(turns_survived):
        """Save a high score to the high scores file"""
        import datetime

        scores_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
        os.makedirs(scores_dir, exist_ok=True)
        scores_file = os.path.join(scores_dir, 'highscores.json')

        # Load existing scores
        scores = []
        if os.path.exists(scores_file):
            try:
                with open(scores_file, 'r') as f:
                    scores = json.load(f)
            except:
                scores = []

        # Add new score
        new_score = {
            'turns': turns_survived,
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        scores.append(new_score)

        # Sort by turns (descending) and keep top 10
        scores.sort(key=lambda x: x['turns'], reverse=True)
        scores = scores[:10]

        # Save back to file
        with open(scores_file, 'w') as f:
            json.dump(scores, f, indent=2)

        return scores

    @staticmethod
    def load_high_scores():
        """Load high scores from file"""
        scores_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
        scores_file = os.path.join(scores_dir, 'highscores.json')

        if os.path.exists(scores_file):
            try:
                with open(scores_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    @staticmethod
    def save_cure_victory(turns_to_cure, difficulty='medium'):
        """Save a cure victory to the cure leaderboard (separate by difficulty)"""
        import datetime

        scores_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
        os.makedirs(scores_dir, exist_ok=True)
        scores_file = os.path.join(scores_dir, f'cure_leaderboard_{difficulty}.json')

        # Load existing scores
        scores = []
        if os.path.exists(scores_file):
            try:
                with open(scores_file, 'r') as f:
                    scores = json.load(f)
            except:
                scores = []

        # Add new score
        new_score = {
            'turns': turns_to_cure,
            'difficulty': difficulty,
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        scores.append(new_score)

        # Sort by turns (ascending - lower is better) and keep top 10
        scores.sort(key=lambda x: x['turns'])
        scores = scores[:10]

        # Save back to file
        with open(scores_file, 'w') as f:
            json.dump(scores, f, indent=2)

        return scores

    @staticmethod
    def load_cure_leaderboard(difficulty='medium'):
        """Load cure victories from file for a specific difficulty"""
        scores_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
        scores_file = os.path.join(scores_dir, f'cure_leaderboard_{difficulty}.json')

        if os.path.exists(scores_file):
            try:
                with open(scores_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

