import pygame
import sys
from map_generator import MapGenerator
from game_state import GameState, Unit
from renderer import Renderer

class ZombieStrategyGame:
    def __init__(self):
        pygame.init()

        self.screen_width = 1800
        self.screen_height = 1000
        self.tile_size = 40
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Zombie Apocalypse Strategy")

        self.clock = pygame.time.Clock()
        self.running = True

        # Generate map
        map_gen = MapGenerator(width=50, height=50)
        map_grid = map_gen.generate()

        # Initialize game state with research lab position
        self.game_state = GameState(map_grid, map_gen.resources, map_gen.research_lab_pos)

        # Initialize renderer
        self.renderer = Renderer(self.screen_width, self.screen_height, self.tile_size)

        # Game state
        self.selected_unit = None
        self.selected_city = None
        self.selected_tile = None  # Stores (x, y) of selected tile
        self.hovered_tile = None  # Stores (x, y) of hovered tile
        self.city_name_counter = 1
        self.building_placement_mode = None  # Stores building type being placed

        # Auto-select next unit timing
        self.auto_select_timer = 0
        self.auto_select_delay = 0.25  # 0.25 seconds

        # Save/Load menu state
        self.save_menu_open = False
        self.load_menu_open = False
        self.menu_input_text = ""
        self.available_saves = []
        self.save_list_scroll_offset = 0  # Scroll position for save file list

        # Game over state
        self.game_over = False
        self.final_score = 0
        self.high_scores = []

        # Victory state
        self.game_won = False
        self.cure_leaderboard = []
        self.victory_panel_open = True  # Show victory panel initially, can be closed to view map

        # Debug mode
        self.debug_reveal_map = False

        # Exit confirmation
        self.exit_confirmation_open = False
        self.last_save_turn = 0  # Track turn number of last save
        self.has_unsaved_changes = False

        # Console message log
        self.message_log = []
        self.message_log_open = False

        # Animation state for zombie movements
        self.animating_zombies = False
        self.zombie_animations = []  # List of (unit, start_x, start_y, end_x, end_y, progress)
        self.animation_start_time = 0
        self.animation_duration = 1.0  # 1 second per tile

        # Add welcome message
        self.log_message("Welcome to Zombie Apocalypse Strategy!")
        self.log_message("Find the Research Lab and manufacture The Cure to save humanity!")

    def handle_events(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                # Handle victory screen
                if self.game_won:
                    if event.key == pygame.K_n:
                        # Start a new game
                        self.__init__()
                        return
                    elif event.key == pygame.K_ESCAPE:
                        if self.victory_panel_open:
                            self.running = False
                        else:
                            # Re-open victory panel
                            self.victory_panel_open = True
                    elif event.key == pygame.K_SPACE:
                        # Toggle victory panel to view the map
                        self.victory_panel_open = not self.victory_panel_open
                    continue

                # Handle game over screen
                if self.game_over:
                    if event.key == pygame.K_n:
                        # Start a new game
                        self.__init__()
                        return
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                    continue

                # Handle message log
                if self.message_log_open:
                    if event.key == pygame.K_ESCAPE:
                        self.message_log_open = False
                    continue

                # Handle save/load menu input
                if self.save_menu_open or self.load_menu_open:
                    if event.key == pygame.K_ESCAPE:
                        self.save_menu_open = False
                        self.load_menu_open = False
                        self.menu_input_text = ""
                    elif event.key == pygame.K_RETURN:
                        if self.save_menu_open and self.menu_input_text:
                            # Save the game
                            filename = self.menu_input_text if self.menu_input_text.endswith('.json') else f"{self.menu_input_text}.json"
                            self.game_state.save_game(filename)
                            self.last_save_turn = self.game_state.turn
                            self.has_unsaved_changes = False
                            self.save_menu_open = False
                            self.menu_input_text = ""
                        elif self.load_menu_open and self.menu_input_text:
                            # Load the game
                            filename = self.menu_input_text if self.menu_input_text.endswith('.json') else f"{self.menu_input_text}.json"
                            loaded_state = GameState.load_game(filename)
                            if loaded_state:
                                self.game_state = loaded_state
                                self.selected_unit = None
                                self.selected_city = None
                                self.selected_tile = None
                                self.building_placement_mode = None
                                # Find the highest city number to continue naming correctly
                                max_num = 0
                                for city in self.game_state.cities:
                                    if city.name.startswith("New Hope "):
                                        try:
                                            num = int(city.name.split()[-1])
                                            max_num = max(max_num, num)
                                        except:
                                            pass
                                self.city_name_counter = max_num + 1
                            self.load_menu_open = False
                            self.menu_input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.menu_input_text = self.menu_input_text[:-1]
                    else:
                        # Add character to input (only alphanumeric, underscore, hyphen)
                        if event.unicode and (event.unicode.isalnum() or event.unicode in ['_', '-', ' ']):
                            if len(self.menu_input_text) < 30:
                                self.menu_input_text += event.unicode
                    continue

                if event.key == pygame.K_ESCAPE:
                    if self.exit_confirmation_open:
                        # Close the exit confirmation dialog
                        self.exit_confirmation_open = False
                    elif self.building_placement_mode:
                        # Cancel building placement
                        self.building_placement_mode = None
                        self.log_message("Building placement cancelled")
                    else:
                        # Check if there are unsaved changes
                        if self.has_unsaved_changes or self.last_save_turn < self.game_state.turn:
                            self.exit_confirmation_open = True
                            self.log_message("ESC: Unsaved changes detected. Press Y to exit without saving, N to cancel.")
                        else:
                            self.running = False

                # Camera movement (only if Ctrl is not pressed)
                elif event.key == pygame.K_w and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.renderer.move_camera(0, -self.tile_size * 2)
                elif event.key == pygame.K_s and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.renderer.move_camera(0, self.tile_size * 2)
                elif event.key == pygame.K_a and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.renderer.move_camera(-self.tile_size * 2, 0)
                elif event.key == pygame.K_d and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.renderer.move_camera(self.tile_size * 2, 0)

                # End turn
                elif event.key == pygame.K_e:
                    if self.game_state.current_team == 'player':
                        # Player ending turn - switch to enemy and start animation
                        self.game_state.current_team = 'enemy'
                        for unit in self.game_state.units:
                            if unit.team == 'enemy':
                                unit.reset_moves()
                        # Start zombie turn with animation
                        self.start_zombie_turn_animated()
                    else:
                        # Enemy turn ending
                        self.game_state.end_turn()
                    self.selected_unit = None
                    self.has_unsaved_changes = True  # Mark that changes have been made

                # Found city
                elif event.key == pygame.K_f:
                    if self.selected_unit and self.selected_unit.team == 'player':
                        city_name = f"New Hope {self.city_name_counter}"
                        city = self.game_state.found_city(self.selected_unit.x, self.selected_unit.y, city_name)
                        if city:
                            self.city_name_counter += 1
                            # Transfer unit's inventory to the new city
                            transferred = {}
                            for resource in ['food', 'materials', 'medicine']:
                                amount = self.selected_unit.inventory[resource]
                                if amount > 0:
                                    city.resources[resource] += amount
                                    transferred[resource] = amount

                            if transferred:
                                transfer_str = ', '.join([f"{v} {k}" for k, v in transferred.items()])
                                self.log_message(f"Founded {city_name} at ({self.selected_unit.x}, {self.selected_unit.y}) with {transfer_str}")
                            else:
                                self.log_message(f"Founded {city_name} at ({self.selected_unit.x}, {self.selected_unit.y})")

                            # Consume the unit that founded the city
                            self.game_state.units.remove(self.selected_unit)
                            self.selected_unit = None
                        else:
                            self.log_message(f"Cannot found city here! Cities must be at least 3 tiles apart.")

                # Scavenge resources
                elif event.key == pygame.K_r:
                    if self.selected_unit and self.selected_unit.team == 'player':
                        pos = (self.selected_unit.x, self.selected_unit.y)
                        if pos in self.game_state.resources:
                            resources = self.game_state.resources[pos]

                            # Check if cure is present and unit is not a medic
                            if 'cure' in resources and resources.get('cure', 0) > 0:
                                if self.selected_unit.unit_type != 'medic':
                                    self.log_message("Only medics can handle The Cure!")
                                    continue

                            # Scavenge all resources
                            for resource, amount in resources.items():
                                self.selected_unit.inventory[resource] += amount
                            del self.game_state.resources[pos]
                            self.log_message(f"Scavenged: {resources} (now in unit's inventory)")

                # Deposit resources to city (T key)
                elif event.key == pygame.K_t:
                    if self.selected_unit and self.selected_unit.team == 'player':
                        city = self.game_state.get_city_at(self.selected_unit.x, self.selected_unit.y)
                        if city:
                            # Transfer all resources from unit to city
                            transferred = {}
                            for resource in ['food', 'materials', 'medicine', 'cure']:
                                amount = self.selected_unit.inventory.get(resource, 0)
                                if amount > 0:
                                    city.resources[resource] = city.resources.get(resource, 0) + amount
                                    transferred[resource] = amount
                                    self.selected_unit.inventory[resource] = 0
                            if transferred:
                                self.log_message(f"Deposited to {city.name}: {transferred}")
                            else:
                                self.log_message("Unit has no resources to deposit")
                        else:
                            self.log_message("Unit must be in a city to deposit resources")

                # Pickup resources from city (G key)
                elif event.key == pygame.K_g:
                    if self.selected_unit and self.selected_unit.team == 'player':
                        city = self.game_state.get_city_at(self.selected_unit.x, self.selected_unit.y)
                        if city:
                            # Transfer all resources from city to unit
                            transferred = {}
                            for resource in ['food', 'materials', 'medicine', 'cure']:
                                amount = city.resources.get(resource, 0)
                                if amount > 0:
                                    self.selected_unit.inventory[resource] = self.selected_unit.inventory.get(resource, 0) + amount
                                    transferred[resource] = amount
                                    city.resources[resource] = 0
                            if transferred:
                                self.log_message(f"Picked up from {city.name}: {transferred}")
                            else:
                                self.log_message("City has no resources to pick up")
                        else:
                            self.log_message("Unit must be in a city to pick up resources")

                # Heal adjacent unit (H key - medics only)
                elif event.key == pygame.K_h:
                    if self.selected_unit and self.selected_unit.team == 'player' and self.selected_unit.unit_type == 'medic':
                        if self.selected_unit.can_move():
                            # Find adjacent friendly units that need healing
                            healed = False
                            for dx in [-1, 0, 1]:
                                for dy in [-1, 0, 1]:
                                    if dx == 0 and dy == 0:
                                        continue
                                    target_x = self.selected_unit.x + dx
                                    target_y = self.selected_unit.y + dy
                                    target_unit = self.game_state.get_unit_at(target_x, target_y)
                                    if target_unit and target_unit.team == 'player' and target_unit.health < target_unit.max_health:
                                        # Heal the unit (scales with medic level: 30 + 10 per level)
                                        base_heal = 30
                                        heal_amount = base_heal + (self.selected_unit.level - 1) * 10
                                        old_health = target_unit.health
                                        target_unit.health = min(target_unit.max_health, target_unit.health + heal_amount)
                                        actual_heal = target_unit.health - old_health
                                        self.log_message(f"Medic (Lvl {self.selected_unit.level}) healed {target_unit.unit_type} for {actual_heal} HP! (Now at {target_unit.health}/{target_unit.max_health})")

                                        # Award XP to medic (1 XP per HP healed)
                                        leveled_up = self.selected_unit.gain_xp(actual_heal)
                                        self.log_message(f"Medic gained {actual_heal} XP! (Level {self.selected_unit.level}: {self.selected_unit.xp}/{self.selected_unit.xp_to_next_level} XP)")
                                        if leveled_up:
                                            self.log_message(f"LEVEL UP! Medic is now level {self.selected_unit.level}! HP: {self.selected_unit.max_health}, Attack: {self.selected_unit.attack_power}")

                                        self.selected_unit.moves_remaining -= 1
                                        healed = True
                                        break
                                if healed:
                                    break
                            if not healed:
                                self.log_message("No adjacent friendly units need healing")
                        else:
                            self.log_message("Medic has no moves remaining")
                    elif self.selected_unit and self.selected_unit.unit_type != 'medic':
                        self.log_message("Only medics can heal units")
                    else:
                        self.log_message("Select a medic to heal")

                # Enter building placement mode
                elif event.key == pygame.K_1:  # Farm
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot build during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'farm'
                        self.log_message("Select adjacent tile to place Farm (click tile or ESC to cancel)")

                elif event.key == pygame.K_2:  # Workshop
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot build during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'workshop'
                        self.log_message("Select adjacent tile to place Workshop (click tile or ESC to cancel)")

                elif event.key == pygame.K_3:  # Hospital
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot build during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'hospital'
                        self.log_message("Select adjacent tile to place Hospital (click tile or ESC to cancel)")

                elif event.key == pygame.K_4:  # Wall
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot build during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'wall'
                        self.log_message("Select tile within 6 tiles (with LOS) to place Wall (click tile or ESC to cancel)")

                elif event.key == pygame.K_5:  # Dock
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot build during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'dock'
                        self.log_message("Select water tile to place Dock (click tile or ESC to cancel)")

                elif event.key == pygame.K_6:  # Recruit Survivor
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot recruit units during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'survivor'
                        self.log_message("Recruit Survivor unit at city location")

                elif event.key == pygame.K_7:  # Recruit Scout
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot recruit units during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'scout'
                        self.log_message("Recruit Scout unit at city location")

                elif event.key == pygame.K_8:  # Recruit Soldier
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot recruit units during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'soldier'
                        self.log_message("Recruit Soldier unit at city location")

                elif event.key == pygame.K_9:  # Recruit Medic
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot recruit units during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'medic'
                        self.log_message("Recruit Medic unit at city location")

                elif event.key == pygame.K_u:  # Upgrade building
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot upgrade buildings during enemy turn!")
                    elif self.selected_city:
                        self.building_placement_mode = 'upgrade'
                        self.log_message("Click on a building to upgrade it (max level 3)")

                elif event.key == pygame.K_c:  # Manufacture Cure
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot manufacture cure during enemy turn!")
                    elif self.selected_city:
                        # Check if city has hospital and the cure
                        if 'hospital' in self.selected_city.buildings and self.selected_city.resources.get('cure', 0) > 0:
                            if self.selected_city.can_build('manufacture_cure'):
                                self.building_placement_mode = 'manufacture_cure'
                                self.log_message("🧪 Initiating cure manufacturing... Click city to confirm!")
                            else:
                                self.log_message("Not enough resources! Need 1000 food, 1000 materials, 200 medicine, and 1 cure.")
                        else:
                            if 'hospital' not in self.selected_city.buildings:
                                self.log_message("City needs a hospital to manufacture the cure!")
                            else:
                                self.log_message("No cure available! Find it at the Research Lab.")

                # Handle exit confirmation Y/N
                elif event.key == pygame.K_y:
                    if self.exit_confirmation_open:
                        # Exit without saving
                        self.log_message("Exiting without saving...")
                        self.running = False

                elif event.key == pygame.K_n:
                    if self.exit_confirmation_open:
                        # Cancel exit
                        self.exit_confirmation_open = False
                        self.log_message("Exit cancelled. Continue playing!")

                # Debug: Toggle full map reveal (F1)
                elif event.key == pygame.K_F1:
                    self.debug_reveal_map = not self.debug_reveal_map
                    if self.debug_reveal_map:
                        self.log_message("DEBUG: Full map revealed")
                    else:
                        self.log_message("DEBUG: Map visibility restored to normal")

                # Save game (Ctrl+S) - Open save menu
                elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.save_menu_open = True
                    self.load_menu_open = False
                    self.menu_input_text = ""
                    self.save_list_scroll_offset = 0
                    self.refresh_save_list()

                # Load game (Ctrl+L) - Open load menu
                elif event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.load_menu_open = True
                    self.save_menu_open = False
                    self.menu_input_text = ""
                    self.save_list_scroll_offset = 0
                    self.refresh_save_list()

            elif event.type == pygame.MOUSEWHEEL:
                # Handle mouse wheel scrolling for save/load menus
                if self.save_menu_open or self.load_menu_open:
                    # event.y is positive for scroll up, negative for scroll down
                    self.save_list_scroll_offset -= event.y
                    # Clamp scroll offset to valid range
                    max_scroll = max(0, len(self.available_saves) - 10)
                    self.save_list_scroll_offset = max(0, min(self.save_list_scroll_offset, max_scroll))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Check if click is on message box (toggle message log)
                if self.is_message_box_clicked(mouse_x, mouse_y):
                    self.message_log_open = not self.message_log_open
                    continue

                # Check if click is on mini-map (takes priority)
                if self.renderer.is_click_on_minimap(mouse_x, mouse_y):
                    map_width = len(self.game_state.map_grid[0])
                    map_height = len(self.game_state.map_grid)
                    world_coords = self.renderer.minimap_click_to_world_coords(mouse_x, mouse_y, map_width, map_height)
                    if world_coords:
                        world_x, world_y = world_coords
                        # Center camera on clicked location
                        self.renderer.center_camera_on_tile(world_x, world_y)
                        self.log_message(f"Mini-map: Centered camera on ({world_x}, {world_y})")
                    continue  # Don't process other click handlers

                # Handle clicks in save/load menu
                if self.save_menu_open or self.load_menu_open:
                    clicked_save = self.get_clicked_save_file(mouse_x, mouse_y)
                    if clicked_save:
                        if self.load_menu_open:
                            # Load the clicked save file
                            loaded_state = GameState.load_game(clicked_save)
                            if loaded_state:
                                self.game_state = loaded_state
                                self.selected_unit = None
                                self.selected_city = None
                                self.selected_tile = None
                                self.building_placement_mode = None
                                # Find the highest city number to continue naming correctly
                                max_num = 0
                                for city in self.game_state.cities:
                                    if city.name.startswith("New Hope "):
                                        try:
                                            num = int(city.name.split()[-1])
                                            max_num = max(max_num, num)
                                        except:
                                            pass
                                self.city_name_counter = max_num + 1
                            self.load_menu_open = False
                        elif self.save_menu_open:
                            # Populate input with clicked filename (without .json extension)
                            self.menu_input_text = clicked_save[:-5] if clicked_save.endswith('.json') else clicked_save
                    continue

                tile_x, tile_y = self.renderer.screen_to_tile(mouse_x, mouse_y)

                if event.button == 1:  # Left click - select unit/city OR place building
                    # If in building placement mode, try to place building
                    if self.building_placement_mode and self.selected_city:
                        building_type = self.building_placement_mode

                        # Handle upgrade mode
                        if building_type == 'upgrade':
                            building = self.game_state.get_building_at(tile_x, tile_y)
                            if building:
                                # Find which city owns this building
                                for city in self.game_state.cities:
                                    if (tile_x, tile_y) in city.building_locations:
                                        if city.can_upgrade_building(tile_x, tile_y):
                                            current_level = building['level']
                                            if city.upgrade_building(tile_x, tile_y):
                                                new_level = current_level + 1
                                                self.log_message(f"Upgraded {building['type']} to level {new_level}!")
                                            else:
                                                self.log_message("Upgrade failed!")
                                        else:
                                            current_level = building.get('level', 1)
                                            if current_level >= 3:
                                                self.log_message("Building is already at max level (3)!")
                                            else:
                                                self.log_message("Not enough resources to upgrade!")
                                        break
                            else:
                                self.log_message("No building at this location!")
                            self.building_placement_mode = None

                        # Handle cure manufacturing (special case - triggers immediately)
                        elif building_type == 'manufacture_cure':
                            if self.selected_city.can_build('manufacture_cure'):
                                result = self.selected_city.build('manufacture_cure', self.selected_city.x, self.selected_city.y, 0)
                                if result == 'cure_manufactured':
                                    self.game_state.manufacture_cure()
                                    # Save to cure leaderboard and set victory state
                                    self.cure_leaderboard = GameState.save_cure_victory(self.game_state.turn)
                                    self.game_won = True
                                    self.victory_panel_open = True
                                    self.final_score = self.game_state.turn
                                    self.log_message(f"🎉 VICTORY! Cure manufactured on turn {self.game_state.turn}!")
                            else:
                                self.log_message("Not enough resources to manufacture cure!")
                            self.building_placement_mode = None

                        # Handle unit recruitment (special case - spawns at city, no adjacency needed)
                        elif building_type in ['survivor', 'scout', 'soldier', 'medic']:
                            # Check if city tile is already occupied by a unit
                            if self.game_state.get_unit_at(self.selected_city.x, self.selected_city.y):
                                self.log_message("Cannot recruit - city tile is occupied by another unit!")
                                self.building_placement_mode = None
                            else:
                                costs = {
                                    'survivor': {'food': 20, 'materials': 10},
                                    'scout': {'food': 15, 'materials': 5},
                                    'soldier': {'food': 30, 'materials': 20},
                                    'medic': {'food': 25, 'materials': 15, 'medicine': 10}
                                }
                                cost = costs[building_type]

                                # Check city resources
                                can_afford = all(self.selected_city.resources.get(res, 0) >= amt
                                                for res, amt in cost.items())
                                if can_afford:
                                    for res, amt in cost.items():
                                        self.selected_city.resources[res] -= amt
                                    new_unit = Unit(self.selected_city.x, self.selected_city.y, building_type, 'player')
                                    self.game_state.units.append(new_unit)
                                    self.log_message(f"Recruited {building_type.capitalize()} at {self.selected_city.name}!")
                                else:
                                    cost_str = ', '.join([f"{amt} {res}" for res, amt in cost.items()])
                                    self.log_message(f"Not enough city resources! {building_type.capitalize()} costs: {cost_str}")

                                self.building_placement_mode = None
                        else:
                            # Regular building placement
                            from map_generator import TileType
                            dist = max(abs(tile_x - self.selected_city.x), abs(tile_y - self.selected_city.y))

                            # Walls have special placement rules: up to 6 tiles with line-of-sight
                            if building_type == 'wall':
                                max_dist = 6
                            else:
                                max_dist = 1  # Adjacent tile for other buildings

                            if dist <= max_dist:
                                # For walls, check line-of-sight
                                has_los = True
                                if building_type == 'wall' and dist > 1:
                                    has_los = self.game_state.visible[tile_y][tile_x]

                                if not has_los:
                                    self.log_message("Wall placement requires line-of-sight from city!")
                                    self.building_placement_mode = None
                                # Check if tile is not occupied
                                elif not self.game_state.get_unit_at(tile_x, tile_y) and \
                                   not self.game_state.get_city_at(tile_x, tile_y) and \
                                   not self.game_state.get_building_at(tile_x, tile_y):

                                    terrain = self.game_state.map_grid[tile_y][tile_x]

                                    # Special validation for dock - must be on water
                                    if building_type == 'dock' and terrain != TileType.WATER:
                                        self.log_message("Docks can only be built on water!")
                                        self.building_placement_mode = None
                                    else:
                                        # Regular building placement using city resources
                                        if self.selected_city.can_build(building_type):
                                            result = self.selected_city.build(building_type, tile_x, tile_y, terrain)

                                            # Check if cure was manufactured (special win condition)
                                            if result == 'cure_manufactured':
                                                self.game_state.manufacture_cure()
                                                # Save to cure leaderboard and set victory state
                                                self.cure_leaderboard = GameState.save_cure_victory(self.game_state.turn)
                                                self.game_won = True
                                                self.victory_panel_open = True
                                                self.final_score = self.game_state.turn
                                                self.log_message(f"🎉 VICTORY! Cure manufactured on turn {self.game_state.turn}!")
                                            else:
                                                self.log_message(f"Built {building_type} at ({tile_x}, {tile_y})!")
                                        else:
                                            self.log_message(f"Not enough city resources!")

                                        self.building_placement_mode = None
                                        self.game_state.update_visibility()
                                else:
                                    self.log_message("Cannot build here - tile is occupied!")
                            else:
                                if building_type == 'wall':
                                    self.log_message("Wall must be within 6 tiles of city!")
                                else:
                                    self.log_message("Building must be adjacent to city!")
                                self.building_placement_mode = None
                    else:
                        # Normal selection mode
                        # Check if Shift is held - if so, prioritize city selection
                        shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

                        if shift_held:
                            # Shift+Click: prioritize cities
                            city = self.game_state.get_city_at(tile_x, tile_y)
                            if city:
                                self.selected_city = city
                                self.selected_unit = None
                                self.log_message(f"Selected {city.name} - Buildings: {', '.join(city.buildings)}")
                            else:
                                # No city, check for unit
                                unit = self.game_state.get_unit_at(tile_x, tile_y)
                                if unit and unit.team == self.game_state.current_team:
                                    self.selected_unit = unit
                                    self.selected_city = None
                                else:
                                    self.selected_unit = None
                                    self.selected_city = None
                        else:
                            # Normal click: prioritize units
                            unit = self.game_state.get_unit_at(tile_x, tile_y)
                            if unit and unit.team == self.game_state.current_team:
                                self.selected_unit = unit
                                self.selected_city = None
                            else:
                                # No unit, check for city
                                city = self.game_state.get_city_at(tile_x, tile_y)
                                if city:
                                    self.selected_city = city
                                    self.selected_unit = None
                                    self.log_message(f"Selected {city.name} - Buildings: {', '.join(city.buildings)}")
                                else:
                                    self.selected_unit = None
                                    self.selected_city = None

                        # Always update selected tile
                        if 0 <= tile_x < len(self.game_state.map_grid[0]) and 0 <= tile_y < len(self.game_state.map_grid):
                            self.selected_tile = (tile_x, tile_y)

                elif event.button == 3:  # Right click - move unit
                    if self.selected_unit and self.selected_unit.team == 'player' and self.selected_unit.can_move():
                        # Calculate path (simple: move one step towards target)
                        dx = tile_x - self.selected_unit.x
                        dy = tile_y - self.selected_unit.y

                        # Normalize to single step
                        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
                        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)

                        new_x = self.selected_unit.x + step_x
                        new_y = self.selected_unit.y + step_y

                        # Check if position is valid and not occupied
                        if (0 <= new_x < len(self.game_state.map_grid[0]) and
                            0 <= new_y < len(self.game_state.map_grid)):

                            blocking_unit = self.game_state.get_unit_at(new_x, new_y)

                            if blocking_unit:
                                # Attack if enemy
                                if blocking_unit.team != self.selected_unit.team:
                                    blocking_unit.health -= self.selected_unit.attack_power
                                    self.log_message(f"Attack! {blocking_unit.unit_type} health: {blocking_unit.health}")
                                    if blocking_unit.health <= 0:
                                        # Drop inventory before removing unit
                                        self.game_state.drop_unit_inventory(blocking_unit)

                                        self.game_state.units.remove(blocking_unit)
                                        self.log_message(f"{blocking_unit.unit_type} defeated!")

                                        # Award XP to the attacker (player units only)
                                        if self.selected_unit.team == 'player':
                                            xp_gained = 50  # Base XP for defeating an enemy
                                            leveled_up = self.selected_unit.gain_xp(xp_gained)
                                            self.log_message(f"{self.selected_unit.unit_type} gained {xp_gained} XP! (Level {self.selected_unit.level}: {self.selected_unit.xp}/{self.selected_unit.xp_to_next_level} XP)")
                                            if leveled_up:
                                                self.log_message(f"LEVEL UP! {self.selected_unit.unit_type} is now level {self.selected_unit.level}! HP: {self.selected_unit.max_health}, Attack: {self.selected_unit.attack_power}")

                                        # Update fog of war when unit dies
                                        self.game_state.update_visibility()
                                    self.selected_unit.moves_remaining -= 1
                            else:
                                # Move to empty tile
                                terrain = self.game_state.map_grid[new_y][new_x]
                                self.selected_unit.move(step_x, step_y, terrain)

                                # Award XP to scouts for exploring new tiles
                                if self.selected_unit.unit_type == 'scout' and self.selected_unit.team == 'player':
                                    tile_pos = (new_x, new_y)
                                    if tile_pos not in self.selected_unit.tiles_explored:
                                        self.selected_unit.tiles_explored.add(tile_pos)
                                        xp_gained = 1  # 1 XP per new tile explored
                                        leveled_up = self.selected_unit.gain_xp(xp_gained)
                                        if leveled_up:
                                            self.log_message(f"LEVEL UP! Scout is now level {self.selected_unit.level}! HP: {self.selected_unit.max_health}, Attack: {self.selected_unit.attack_power}")

                                # Update fog of war after movement
                                self.game_state.update_visibility()

                                # If unit is out of moves, start timer to auto-select next unit
                                if not self.selected_unit.can_move():
                                    self.auto_select_timer = self.auto_select_delay

    def start_zombie_turn_animated(self):
        """Start the animated zombie turn"""
        self.animating_zombies = True
        self.animation_start_time = pygame.time.get_ticks()
        # Execute AI turn immediately, but we'll animate the display
        self.game_state.execute_ai_turn()

    def update(self):
        """Update game logic"""
        # Get delta time for timer
        dt = self.clock.get_time() / 1000.0  # Convert to seconds

        # Handle zombie animation
        if self.animating_zombies:
            elapsed = (pygame.time.get_ticks() - self.animation_start_time) / 1000.0
            if elapsed >= self.animation_duration:
                # Animation complete, end enemy turn
                self.animating_zombies = False
                # Now end enemy turn and start player turn
                self.game_state.current_team = 'player'
                self.game_state.turn += 1
                # Reset player unit moves
                for unit in self.game_state.units:
                    if unit.team == 'player':
                        unit.reset_moves()
                # Autosave at the start of player's turn
                self.game_state.autosave()
                # Produce resources in all cities
                for city in self.game_state.cities:
                    production = city.produce_resources()
                    if any(production.values()):
                        prod_str = ', '.join([f"{k}: +{v}" for k, v in production.items() if v > 0])
                        self.log_message(f"{city.name} produced: {prod_str}")
                # Spawn new zombies
                self.game_state.spawn_zombies()
                # Update fog of war
                self.game_state.update_visibility()
            return  # Skip normal updates during animation

        # Update hovered tile based on mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_x, tile_y = self.renderer.screen_to_tile(mouse_x, mouse_y)
        if 0 <= tile_x < len(self.game_state.map_grid[0]) and 0 <= tile_y < len(self.game_state.map_grid):
            self.hovered_tile = (tile_x, tile_y)
        else:
            self.hovered_tile = None

        # Auto-select next unit timer
        if self.auto_select_timer > 0:
            self.auto_select_timer -= dt
            if self.auto_select_timer <= 0:
                self.auto_select_timer = 0
                # Find next available unit with moves
                next_unit = None
                for unit in self.game_state.units:
                    if unit.team == 'player' and unit.can_move():
                        next_unit = unit
                        break

                if next_unit:
                    self.selected_unit = next_unit
                    # Center camera on the unit
                    center_x = next_unit.x * self.tile_size - self.screen_width // 2
                    center_y = next_unit.y * self.tile_size - self.screen_height // 2
                    self.renderer.camera_x = center_x
                    self.renderer.camera_y = center_y

        # Check for game over
        if not self.game_over and self.game_state.is_game_over():
            self.game_over = True
            self.final_score = self.game_state.turn
            self.high_scores = GameState.save_high_score(self.final_score)
            self.log_message(f"\n=== GAME OVER ===")
            self.log_message(f"You survived {self.final_score} turns!")
            self.log_message(f"All units and cities have been destroyed.")

    def refresh_save_list(self):
        """Get list of available save files"""
        import os
        saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
        if os.path.exists(saves_dir):
            self.available_saves = [f for f in os.listdir(saves_dir) if f.endswith('.json')]
            self.available_saves.sort(key=lambda x: os.path.getmtime(os.path.join(saves_dir, x)), reverse=True)
        else:
            self.available_saves = []

    def get_clicked_save_file(self, mouse_x, mouse_y):
        """Check if a save file was clicked in the menu"""
        menu_x = self.screen_width // 2 - 250
        menu_y = 200
        list_y = menu_y + 120

        # Calculate which saves are visible based on scroll offset
        visible_saves = self.available_saves[self.save_list_scroll_offset:self.save_list_scroll_offset + 10]

        for i, save_file in enumerate(visible_saves):
            file_y = list_y + i * 30
            if menu_x <= mouse_x <= menu_x + 500 and file_y <= mouse_y <= file_y + 25:
                return save_file
        return None

    def log_message(self, message):
        """Add a message to the console log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.message_log.append(f"[{timestamp}] {message}")
        # Keep only last 50 messages
        if len(self.message_log) > 50:
            self.message_log.pop(0)
        # Also print to console
        print(message)

    def is_message_box_clicked(self, mouse_x, mouse_y):
        """Check if the message box in top right was clicked"""
        box_width = 500
        box_height = 30
        box_x = self.screen_width - box_width - 10
        box_y = 10
        return box_x <= mouse_x <= box_x + box_width and box_y <= mouse_y <= box_y + box_height

    def render(self):
        """Render the game"""
        self.renderer.render(self.screen, self.game_state, self.selected_unit, self.selected_city, self.selected_tile, self.hovered_tile, self.building_placement_mode, self.debug_reveal_map)

        # Render victory banner if panel is closed
        if self.game_won and not self.victory_panel_open:
            banner_height = 60
            banner_rect = pygame.Rect(0, 0, self.screen_width, banner_height)
            pygame.draw.rect(self.screen, (20, 60, 20), banner_rect)
            pygame.draw.rect(self.screen, (50, 200, 50), banner_rect, 2)

            banner_font = pygame.font.Font(None, 40)
            banner_text = banner_font.render(f"🎉 VICTORY! Humanity Saved in {self.final_score} Turns! 🎉", True, (100, 255, 100))
            banner_rect_text = banner_text.get_rect(center=(self.screen_width // 2, banner_height // 2))
            self.screen.blit(banner_text, banner_rect_text)

            hint_font = pygame.font.Font(None, 18)
            hint_text = hint_font.render("Press SPACE to show victory screen | ESC to reopen", True, (180, 255, 180))
            hint_rect = hint_text.get_rect(center=(self.screen_width // 2, banner_height - 12))
            self.screen.blit(hint_text, hint_rect)

        # Render message box (always visible in top right)
        self.render_message_box()

        # Render message log if open
        if self.message_log_open:
            self.render_message_log()

        # Render save/load menu on top
        if self.save_menu_open:
            self.render_save_menu()
        elif self.load_menu_open:
            self.render_load_menu()
        elif self.exit_confirmation_open:
            self.render_exit_confirmation()
        elif self.game_won and self.victory_panel_open:
            self.render_victory()
        elif self.game_over:
            self.render_game_over()

        pygame.display.flip()

    def render_save_menu(self):
        """Render the save game menu"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Menu panel
        menu_width = 500
        menu_height = 450
        menu_x = self.screen_width // 2 - menu_width // 2
        menu_y = 150

        pygame.draw.rect(self.screen, (40, 40, 50), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (menu_x, menu_y, menu_width, menu_height), 3)

        # Title
        title_font = pygame.font.Font(None, 36)
        title = title_font.render("Save Game", True, (255, 215, 0))
        self.screen.blit(title, (menu_x + 20, menu_y + 20))

        # Input label
        label_font = pygame.font.Font(None, 24)
        label = label_font.render("Enter save name:", True, (200, 200, 200))
        self.screen.blit(label, (menu_x + 20, menu_y + 70))

        # Input box
        input_box_y = menu_y + 100
        pygame.draw.rect(self.screen, (60, 60, 70), (menu_x + 20, input_box_y, menu_width - 40, 35))
        pygame.draw.rect(self.screen, (150, 150, 200), (menu_x + 20, input_box_y, menu_width - 40, 35), 2)

        # Input text
        input_font = pygame.font.Font(None, 28)
        input_display = self.menu_input_text + "|"
        input_text = input_font.render(input_display, True, (255, 255, 255))
        self.screen.blit(input_text, (menu_x + 30, input_box_y + 8))

        # Existing saves list
        list_y = menu_y + 150
        list_label_text = f"Existing saves (click to overwrite) - {len(self.available_saves)} total:"
        list_label = label_font.render(list_label_text, True, (200, 200, 200))
        self.screen.blit(list_label, (menu_x + 20, list_y))

        # Scroll indicator
        if len(self.available_saves) > 10:
            scroll_info_font = pygame.font.Font(None, 16)
            scroll_text = f"Showing {self.save_list_scroll_offset + 1}-{min(self.save_list_scroll_offset + 10, len(self.available_saves))} (scroll with mouse wheel)"
            scroll_surface = scroll_info_font.render(scroll_text, True, (150, 200, 255))
            self.screen.blit(scroll_surface, (menu_x + 20, list_y + 22))

        # Render save files with scrolling
        file_font = pygame.font.Font(None, 20)
        visible_saves = self.available_saves[self.save_list_scroll_offset:self.save_list_scroll_offset + 10]

        for i, save_file in enumerate(visible_saves):
            file_y = list_y + 45 + i * 25
            # Highlight on hover
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if menu_x + 20 <= mouse_x <= menu_x + menu_width - 20 and file_y <= mouse_y <= file_y + 20:
                pygame.draw.rect(self.screen, (80, 80, 100), (menu_x + 20, file_y, menu_width - 40, 22))

            file_text = file_font.render(save_file, True, (180, 255, 180))
            self.screen.blit(file_text, (menu_x + 30, file_y + 2))

        # Instructions
        help_font = pygame.font.Font(None, 18)
        help_text = help_font.render("Press ENTER to save | ESC to cancel", True, (150, 150, 150))
        self.screen.blit(help_text, (menu_x + 20, menu_y + menu_height - 30))

    def render_load_menu(self):
        """Render the load game menu"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Menu panel
        menu_width = 500
        menu_height = 450
        menu_x = self.screen_width // 2 - menu_width // 2
        menu_y = 150

        pygame.draw.rect(self.screen, (40, 40, 50), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (menu_x, menu_y, menu_width, menu_height), 3)

        # Title
        title_font = pygame.font.Font(None, 36)
        title = title_font.render("Load Game", True, (255, 215, 0))
        self.screen.blit(title, (menu_x + 20, menu_y + 20))

        # Input label
        label_font = pygame.font.Font(None, 24)
        label = label_font.render("Enter save name or click below:", True, (200, 200, 200))
        self.screen.blit(label, (menu_x + 20, menu_y + 70))

        # Input box
        input_box_y = menu_y + 100
        pygame.draw.rect(self.screen, (60, 60, 70), (menu_x + 20, input_box_y, menu_width - 40, 35))
        pygame.draw.rect(self.screen, (150, 150, 200), (menu_x + 20, input_box_y, menu_width - 40, 35), 2)

        # Input text
        input_font = pygame.font.Font(None, 28)
        input_display = self.menu_input_text + "|"
        input_text = input_font.render(input_display, True, (255, 255, 255))
        self.screen.blit(input_text, (menu_x + 30, input_box_y + 8))

        # Available saves list
        list_y = menu_y + 150
        list_label_text = f"Available saves (click to load) - {len(self.available_saves)} total:"
        list_label = label_font.render(list_label_text, True, (200, 200, 200))
        self.screen.blit(list_label, (menu_x + 20, list_y))

        # Scroll indicator
        if len(self.available_saves) > 10:
            scroll_info_font = pygame.font.Font(None, 16)
            scroll_text = f"Showing {self.save_list_scroll_offset + 1}-{min(self.save_list_scroll_offset + 10, len(self.available_saves))} (scroll with mouse wheel)"
            scroll_surface = scroll_info_font.render(scroll_text, True, (150, 200, 255))
            self.screen.blit(scroll_surface, (menu_x + 20, list_y + 22))

        # Render save files with scrolling
        file_font = pygame.font.Font(None, 20)
        if not self.available_saves:
            no_saves = file_font.render("No save files found", True, (150, 150, 150))
            self.screen.blit(no_saves, (menu_x + 30, list_y + 50))
        else:
            visible_saves = self.available_saves[self.save_list_scroll_offset:self.save_list_scroll_offset + 10]

            for i, save_file in enumerate(visible_saves):
                file_y = list_y + 45 + i * 25
                # Highlight on hover
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if menu_x + 20 <= mouse_x <= menu_x + menu_width - 20 and file_y <= mouse_y <= file_y + 20:
                    pygame.draw.rect(self.screen, (80, 80, 100), (menu_x + 20, file_y, menu_width - 40, 22))

                file_text = file_font.render(save_file, True, (180, 255, 180))
                self.screen.blit(file_text, (menu_x + 30, file_y + 2))

        # Instructions
        help_font = pygame.font.Font(None, 18)
        help_text = help_font.render("Press ENTER to load | ESC to cancel", True, (150, 150, 150))
        self.screen.blit(help_text, (menu_x + 20, menu_y + menu_height - 30))

    def render_exit_confirmation(self):
        """Render the exit confirmation dialog"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dialog panel
        dialog_width = 600
        dialog_height = 250
        dialog_x = self.screen_width // 2 - dialog_width // 2
        dialog_y = self.screen_height // 2 - dialog_height // 2

        pygame.draw.rect(self.screen, (60, 40, 40), (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, (255, 200, 100), (dialog_x, dialog_y, dialog_width, dialog_height), 4)

        # Warning icon/title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("⚠ Unsaved Changes", True, (255, 200, 100))
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 50))
        self.screen.blit(title, title_rect)

        # Message
        message_font = pygame.font.Font(None, 28)
        message1 = message_font.render("You have unsaved progress!", True, (255, 255, 255))
        message2 = message_font.render("Are you sure you want to exit?", True, (255, 255, 255))

        message1_rect = message1.get_rect(center=(self.screen_width // 2, dialog_y + 110))
        message2_rect = message2.get_rect(center=(self.screen_width // 2, dialog_y + 140))

        self.screen.blit(message1, message1_rect)
        self.screen.blit(message2, message2_rect)

        # Options
        options_font = pygame.font.Font(None, 32)
        options = options_font.render("Press Y to Exit  |  Press N to Cancel  |  ESC to Cancel", True, (200, 255, 200))
        options_rect = options.get_rect(center=(self.screen_width // 2, dialog_y + 200))
        self.screen.blit(options, options_rect)

    def render_game_over(self):
        """Render the game over screen with high scores"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Menu panel
        menu_width = 600
        menu_height = 500
        menu_x = self.screen_width // 2 - menu_width // 2
        menu_y = 100

        pygame.draw.rect(self.screen, (40, 20, 20), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, (200, 50, 50), (menu_x, menu_y, menu_width, menu_height), 3)

        # Title
        title_font = pygame.font.Font(None, 56)
        title = title_font.render("GAME OVER", True, (255, 50, 50))
        title_rect = title.get_rect(center=(self.screen_width // 2, menu_y + 40))
        self.screen.blit(title, title_rect)

        # Your score
        score_font = pygame.font.Font(None, 36)
        score_text = score_font.render(f"You Survived: {self.final_score} Turns", True, (255, 200, 100))
        score_rect = score_text.get_rect(center=(self.screen_width // 2, menu_y + 100))
        self.screen.blit(score_text, score_rect)

        # High scores title
        hs_title_font = pygame.font.Font(None, 32)
        hs_title = hs_title_font.render("High Scores", True, (255, 215, 0))
        hs_title_rect = hs_title.get_rect(center=(self.screen_width // 2, menu_y + 160))
        self.screen.blit(hs_title, hs_title_rect)

        # Display high scores
        list_font = pygame.font.Font(None, 24)
        start_y = menu_y + 200
        for i, score in enumerate(self.high_scores[:10]):
            is_current_score = (score['turns'] == self.final_score and i == self.high_scores.index(score))
            color = (100, 255, 100) if is_current_score else (200, 200, 200)

            rank_text = f"#{i+1}:"
            turns_text = f"{score['turns']} turns"
            date_text = score['date']

            line = f"{rank_text:5} {turns_text:15} {date_text}"
            text = list_font.render(line, True, color)
            self.screen.blit(text, (menu_x + 50, start_y + i * 28))

        # Instructions
        help_font = pygame.font.Font(None, 20)
        help_text = help_font.render("Press ESC to exit", True, (150, 150, 150))
        help_rect = help_text.get_rect(center=(self.screen_width // 2, menu_y + menu_height - 30))
        self.screen.blit(help_text, help_rect)

    def render_victory(self):
        """Render the victory screen with cure leaderboard"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Menu panel
        menu_width = 700
        menu_height = 550
        menu_x = self.screen_width // 2 - menu_width // 2
        menu_y = 100

        pygame.draw.rect(self.screen, (20, 40, 20), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, (50, 200, 50), (menu_x, menu_y, menu_width, menu_height), 3)

        # Title
        title_font = pygame.font.Font(None, 64)
        title = title_font.render("🎉 VICTORY! 🎉", True, (100, 255, 100))
        title_rect = title.get_rect(center=(self.screen_width // 2, menu_y + 50))
        self.screen.blit(title, title_rect)

        # Victory message
        msg_font = pygame.font.Font(None, 28)
        msg1 = msg_font.render("The Cure has been manufactured!", True, (200, 255, 200))
        msg1_rect = msg1.get_rect(center=(self.screen_width // 2, menu_y + 110))
        self.screen.blit(msg1, msg1_rect)

        msg2 = msg_font.render("All zombies have been cured and humanity is saved!", True, (200, 255, 200))
        msg2_rect = msg2.get_rect(center=(self.screen_width // 2, menu_y + 140))
        self.screen.blit(msg2, msg2_rect)

        # Your score
        score_font = pygame.font.Font(None, 36)
        score_text = score_font.render(f"Turns to Victory: {self.final_score}", True, (255, 215, 0))
        score_rect = score_text.get_rect(center=(self.screen_width // 2, menu_y + 190))
        self.screen.blit(score_text, score_rect)

        # Cure leaderboard title
        lb_title_font = pygame.font.Font(None, 32)
        lb_title = lb_title_font.render("Cure Leaderboard (Fastest Victories)", True, (255, 215, 0))
        lb_title_rect = lb_title.get_rect(center=(self.screen_width // 2, menu_y + 240))
        self.screen.blit(lb_title, lb_title_rect)

        # Display cure leaderboard
        list_font = pygame.font.Font(None, 24)
        start_y = menu_y + 280
        for i, score in enumerate(self.cure_leaderboard[:10]):
            is_current_score = (score['turns'] == self.final_score and i == self.cure_leaderboard.index(score))
            color = (100, 255, 100) if is_current_score else (200, 200, 200)

            rank_text = f"#{i+1}:"
            turns_text = f"{score['turns']} turns"
            date_text = score['date']

            line = f"{rank_text:5} {turns_text:15} {date_text}"
            text = list_font.render(line, True, color)
            self.screen.blit(text, (menu_x + 50, start_y + i * 26))

        # Instructions
        help_font = pygame.font.Font(None, 20)
        help_text1 = help_font.render("Press SPACE to View Map | Press N for New Game | Press ESC to Exit", True, (150, 150, 150))
        help_rect1 = help_text1.get_rect(center=(self.screen_width // 2, menu_y + menu_height - 30))
        self.screen.blit(help_text1, help_rect1)

    def render_message_box(self):
        """Render the message box in top right corner"""
        box_width = 500
        box_height = 30
        box_x = self.screen_width - box_width - 10
        box_y = 10

        # Background
        pygame.draw.rect(self.screen, (30, 30, 40), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(self.screen, (100, 100, 120), (box_x, box_y, box_width, box_height), 2)

        # Get most recent message
        if self.message_log:
            recent_message = self.message_log[-1]
            # Strip timestamp for display in box
            if ']' in recent_message:
                display_message = recent_message.split(']', 1)[1].strip()
            else:
                display_message = recent_message

            # Truncate if too long
            msg_font = pygame.font.Font(None, 18)
            if len(display_message) > 70:
                display_message = display_message[:67] + "..."

            msg_surface = msg_font.render(display_message, True, (220, 220, 220))
            self.screen.blit(msg_surface, (box_x + 5, box_y + 8))

        # Hint text
        hint_font = pygame.font.Font(None, 14)
        hint_text = hint_font.render("(click for log)", True, (150, 150, 150))
        hint_rect = hint_text.get_rect(right=box_x + box_width - 5, centery=box_y + box_height // 2)
        self.screen.blit(hint_text, hint_rect)

    def render_message_log(self):
        """Render the message log dialog"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Log panel
        log_width = 700
        log_height = 500
        log_x = self.screen_width // 2 - log_width // 2
        log_y = self.screen_height // 2 - log_height // 2

        pygame.draw.rect(self.screen, (30, 30, 40), (log_x, log_y, log_width, log_height))
        pygame.draw.rect(self.screen, (100, 150, 200), (log_x, log_y, log_width, log_height), 3)

        # Title
        title_font = pygame.font.Font(None, 32)
        title = title_font.render("Message Log", True, (200, 220, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, log_y + 30))
        self.screen.blit(title, title_rect)

        # Display last 20 messages (newest at bottom)
        msg_font = pygame.font.Font(None, 18)
        start_y = log_y + 70
        max_messages = 20
        messages_to_show = self.message_log[-max_messages:] if len(self.message_log) > max_messages else self.message_log

        for i, message in enumerate(messages_to_show):
            msg_surface = msg_font.render(message, True, (220, 220, 220))
            self.screen.blit(msg_surface, (log_x + 15, start_y + i * 20))

        # Instructions
        help_font = pygame.font.Font(None, 20)
        help_text = help_font.render("Click message box or press ESC to close", True, (150, 150, 150))
        help_rect = help_text.get_rect(center=(self.screen_width // 2, log_y + log_height - 25))
        self.screen.blit(help_text, help_rect)

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ZombieStrategyGame()
    game.run()
