import pygame
import sys
import math
import random
from map_generator import MapGenerator
from game_state import GameState, Unit
from renderer import Renderer

class ZombieStrategyGame:
    def __init__(self):
        pygame.init()

        self.screen_width = 1800
        self.screen_height = 1000
        self.tile_size = 40
        self.fullscreen = False
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Zombie Apocalypse Strategy")

        self.clock = pygame.time.Clock()
        self.running = True

        # Difficulty configuration
        self.difficulty_dialog_open = True
        self.difficulty = None  # Will be set to 'easy', 'medium', or 'hard'
        self.selected_difficulty_button = None  # No default selection
        self.selected_map_size = 60  # Default map size: 40, 60, or 100

        # Map and game state will be initialized after difficulty selection
        self.game_state = None
        self.renderer = None
        self.map_gen = None

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

        # Standard notification dialog
        self.notification_dialog_open = False
        self.notification_dialog_data = {
            'title': '',
            'messages': [],
            'type': 'info',  # 'info' or 'confirm'
            'callback': None  # Function to call on confirmation
        }

        # Tech tree UI
        self.tech_tree_open = False
        self.selected_tech = None  # Currently hovered/selected tech

        # Console message log
        self.message_log = []
        self.message_log_open = False

        # Help panel
        self.help_panel_open = False

        # Helicopter transport menu
        self.helicopter_menu_open = False
        self.teleporting_unit = None

        # Animation state for zombie movements
        self.animating_zombies = False
        self.zombie_animations = {}  # Dict: unit -> {'type': 'move'/'attack', 'start': (x,y), 'end': (x,y), 'attack_count': int}
        self.animation_start_time = 0
        self.animation_duration = 1.0  # 1 second total for all movements
        self.zombie_positions_snapshot = {}  # Dict: unit -> (x, y) before AI turn
        self.zombie_action_log = {}  # Dict: unit -> list of actions taken during turn

    def initialize_game(self, difficulty):
        """Initialize the game with the selected difficulty"""
        self.difficulty = difficulty
        self.difficulty_dialog_open = False

        # Generate map with selected size
        self.map_gen = MapGenerator(width=self.selected_map_size, height=self.selected_map_size)
        map_grid = self.map_gen.generate()

        # Initialize game state with research lab position and difficulty
        self.game_state = GameState(map_grid, self.map_gen.resources, self.map_gen.research_lab_pos, difficulty)

        # Initialize renderer
        self.renderer = Renderer(self.screen_width, self.screen_height, self.tile_size)

        # Center camera on first player unit (survivor)
        player_units = [u for u in self.game_state.units if u.team == 'player']
        if player_units:
            first_unit = player_units[0]
            self.renderer.center_camera_on_tile(first_unit.x, first_unit.y)

        # Add welcome message
        self.log_message("Welcome to Zombie Apocalypse Strategy!")
        self.log_message(f"Difficulty: {difficulty.upper()}")
        self.log_message("Find the Research Lab and manufacture The Cure to save humanity!")

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            # Get actual fullscreen resolution
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            self.log_message(f"Fullscreen mode enabled ({self.screen_width}x{self.screen_height})")
        else:
            self.screen_width = 1800
            self.screen_height = 1000
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
            self.log_message("Windowed mode enabled")

        # Update renderer if it exists
        if self.renderer:
            self.renderer.screen_width = self.screen_width
            self.renderer.screen_height = self.screen_height

    def confirm_end_turn(self):
        """Actually end the player's turn (called after confirmation or if no units have moves)"""
        # Player ending turn - switch to enemy and start animation
        self.game_state.current_team = 'enemy'
        for unit in self.game_state.units:
            if unit.team == 'enemy':
                unit.reset_moves()
        # Start zombie turn with animation
        self.start_zombie_turn_animated()
        self.selected_unit = None
        self.has_unsaved_changes = True  # Mark that changes have been made

    def handle_events(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize
                self.screen_width = event.w
                self.screen_height = event.h
                self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                # Update renderer if it exists
                if self.renderer:
                    self.renderer.screen_width = self.screen_width
                    self.renderer.screen_height = self.screen_height

            elif event.type == pygame.KEYDOWN:
                # Toggle fullscreen with F11
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue

                # Handle notification dialog (highest priority)
                if self.notification_dialog_open:
                    if self.notification_dialog_data['type'] == 'info':
                        # Info dialog - close on SPACE or ESC
                        if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                            self.notification_dialog_open = False
                    elif self.notification_dialog_data['type'] == 'confirm':
                        # Confirm dialog - Y to confirm, N or ESC to cancel
                        if event.key == pygame.K_y:
                            if self.notification_dialog_data['callback']:
                                self.notification_dialog_data['callback']()
                            self.notification_dialog_open = False
                        elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                            self.notification_dialog_open = False
                    continue

                # Handle difficulty selection dialog
                if self.difficulty_dialog_open:
                    # Allow load menu from difficulty dialog
                    if event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.load_menu_open = True
                        self.save_menu_open = False
                        self.menu_input_text = ""
                        self.save_list_scroll_offset = 0
                        self.refresh_save_list()
                        continue
                    elif event.key == pygame.K_1 or event.key == pygame.K_e:
                        self.initialize_game('easy')
                    elif event.key == pygame.K_2 or event.key == pygame.K_m:
                        self.initialize_game('medium')
                    elif event.key == pygame.K_3 or event.key == pygame.K_h:
                        self.initialize_game('hard')
                    elif event.key == pygame.K_UP:
                        difficulties = ['easy', 'medium', 'hard']
                        if self.selected_difficulty_button is None:
                            self.selected_difficulty_button = 'hard'  # Wrap to last
                        else:
                            idx = difficulties.index(self.selected_difficulty_button)
                            self.selected_difficulty_button = difficulties[(idx - 1) % 3]
                    elif event.key == pygame.K_DOWN:
                        difficulties = ['easy', 'medium', 'hard']
                        if self.selected_difficulty_button is None:
                            self.selected_difficulty_button = 'easy'  # Start at first
                        else:
                            idx = difficulties.index(self.selected_difficulty_button)
                            self.selected_difficulty_button = difficulties[(idx + 1) % 3]
                    elif event.key == pygame.K_RETURN:
                        if self.selected_difficulty_button is not None:
                            self.initialize_game(self.selected_difficulty_button)
                    continue

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

                # Handle helicopter menu
                if self.helicopter_menu_open:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        self.helicopter_menu_open = False
                        self.teleporting_unit = None
                        self.log_message("Helicopter transport cancelled")
                    continue

                # Handle tech tree
                if self.tech_tree_open:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_TAB:
                        self.tech_tree_open = False
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
                            self.game_state.save_game(filename, self.renderer.camera_x, self.renderer.camera_y)
                            self.last_save_turn = self.game_state.turn
                            self.has_unsaved_changes = False
                            self.save_menu_open = False
                            self.menu_input_text = ""
                        elif self.load_menu_open and self.menu_input_text:
                            # Load the game
                            filename = self.menu_input_text if self.menu_input_text.endswith('.json') else f"{self.menu_input_text}.json"
                            result = GameState.load_game(filename)
                            if result:
                                loaded_state, camera_x, camera_y = result
                                self.game_state = loaded_state
                                self.renderer.camera_x = camera_x
                                self.renderer.camera_y = camera_y
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

                # Handle help panel
                if self.help_panel_open:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_k:
                        self.help_panel_open = False
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

                # End turn
                elif event.key == pygame.K_e:
                    if self.game_state.current_team == 'player':
                        # Check if any player units have moves remaining
                        units_with_moves = [u for u in self.game_state.units if u.team == 'player' and u.moves_remaining > 0]

                        if units_with_moves:
                            # Show confirmation dialog
                            unit_count = len(units_with_moves)
                            self.notification_dialog_data = {
                                'title': '⚠ Units Have Moves Remaining',
                                'messages': [
                                    f'{unit_count} unit(s) still have movement points.',
                                    '',
                                    'Are you sure you want to end your turn?'
                                ],
                                'type': 'confirm',
                                'callback': self.confirm_end_turn
                            }
                            self.notification_dialog_open = True
                        else:
                            # No units with moves, end turn normally
                            self.confirm_end_turn()
                    else:
                        # Enemy turn ending
                        self.game_state.end_turn()
                        self.selected_unit = None
                        self.has_unsaved_changes = True

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
                            scavenged = {}
                            for resource, amount in resources.items():
                                # Apply scavenging efficiency tech bonus
                                if self.game_state.has_tech('scavenging_efficiency'):
                                    amount = int(amount * 1.25)
                                self.selected_unit.inventory[resource] += amount
                                scavenged[resource] = amount
                            del self.game_state.resources[pos]

                            # Small chance (10%) to find a survivor when scavenging
                            found_survivor = False
                            if random.random() < 0.10:
                                # Try to spawn survivor on adjacent tile
                                adjacent_positions = [
                                    (self.selected_unit.x + dx, self.selected_unit.y + dy)
                                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                                ]
                                # Filter valid positions (within bounds, not water, no units)
                                from map_generator import TileType
                                map_width = len(self.game_state.map_grid[0])
                                map_height = len(self.game_state.map_grid)
                                valid_positions = [
                                    (x, y) for x, y in adjacent_positions
                                    if (0 <= x < map_width and
                                        0 <= y < map_height and
                                        self.game_state.map_grid[y][x] != TileType.WATER and
                                        not any(u.x == x and u.y == y for u in self.game_state.units))
                                ]

                                if valid_positions:
                                    spawn_x, spawn_y = random.choice(valid_positions)
                                    new_survivor = Unit(spawn_x, spawn_y, 'survivor', 'player', self.game_state.difficulty)
                                    self.game_state.units.append(new_survivor)
                                    found_survivor = True
                                    self.log_message(f"Found a survivor! They joined your group at ({spawn_x}, {spawn_y})")

                            # Show notification dialog with scavenged resources
                            resource_lines = [f"{resource.capitalize()}: +{amount}" for resource, amount in scavenged.items()]
                            messages = ['Successfully scavenged:'] + resource_lines + ['', 'Resources added to unit inventory.']
                            if found_survivor:
                                messages.append('')
                                messages.append('BONUS: Found a survivor!')
                                messages.append('A survivor has joined your group!')

                            self.notification_dialog_data = {
                                'title': '✓ Resources Scavenged',
                                'messages': messages,
                                'type': 'info',
                                'callback': None
                            }
                            self.notification_dialog_open = True
                            self.log_message(f"Scavenged: {scavenged} (now in unit's inventory)")

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
                                        # Apply tactical_medicine tech for +20 healing
                                        if self.game_state.has_tech('tactical_medicine'):
                                            base_heal += 20
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

                # Triangulate lab signals (Q key - scouts only)
                elif event.key == pygame.K_q:
                    if self.selected_unit and self.selected_unit.team == 'player' and self.selected_unit.unit_type == 'scout':
                        if self.selected_unit.moves_remaining >= self.selected_unit.max_moves:
                            if self.game_state.triangulation_level < 4:
                                # Use the scout's turn
                                self.selected_unit.moves_remaining = 0
                                self.game_state.triangulation_level += 1

                                # Generate random offset for the circle (lab must still be inside)
                                # The offset is in tile coordinates, will be scaled when rendering
                                # Radius percentages match renderer: Level 1: 50%, Level 2: 30%, Level 3: 15%
                                # Map these to approximate tile radii based on map size
                                map_width = len(self.game_state.map_grid[0])
                                map_height = len(self.game_state.map_grid)
                                radius_percentages = {1: 0.50, 2: 0.30, 3: 0.15, 4: 0}
                                # Calculate max offset (circle radius in tiles, minus some margin)
                                circle_radius_tiles = min(map_width, map_height) * radius_percentages.get(self.game_state.triangulation_level, 0) * 0.5
                                # Random offset within 70% of the radius so lab is comfortably inside
                                max_offset = circle_radius_tiles * 0.7
                                if max_offset > 0:
                                    angle = random.uniform(0, 2 * math.pi)
                                    distance = random.uniform(0, max_offset)
                                    offset_x = distance * math.cos(angle)
                                    offset_y = distance * math.sin(angle)
                                    self.game_state.triangulation_circle_offset = (offset_x, offset_y)
                                else:
                                    self.game_state.triangulation_circle_offset = (0, 0)

                                level_messages = {
                                    1: "Scout detected faint radio signals from the lab. Area marked on minimap (very large radius).",
                                    2: "Scout triangulated signals more precisely. Search area narrowed (large radius).",
                                    3: "Scout is closing in on the signal source. Area significantly reduced (medium radius).",
                                    4: "Scout pinpointed the exact lab location! Marked on minimap."
                                }
                                self.log_message(level_messages[self.game_state.triangulation_level])
                                self.has_unsaved_changes = True
                            else:
                                self.log_message("Lab location already revealed!")
                        else:
                            self.log_message("Scout needs full movement points to triangulate signals")
                    elif self.selected_unit and self.selected_unit.unit_type != 'scout':
                        self.log_message("Only scouts can triangulate lab signals")
                    else:
                        self.log_message("Select a scout to triangulate")

                # Helicopter transport (P key)
                elif event.key == pygame.K_p:
                    if self.game_state and self.game_state.has_tech('helicopter_transport'):
                        if self.selected_unit and self.selected_unit.team == 'player':
                            # Check if unit is on a city tile
                            city = self.game_state.get_city_at(self.selected_unit.x, self.selected_unit.y)
                            if city:
                                # Open helicopter menu
                                self.helicopter_menu_open = True
                                self.teleporting_unit = self.selected_unit
                                self.log_message(f"Select destination city for {self.selected_unit.unit_type}")
                            else:
                                self.log_message("Unit must be on a city tile to use helicopter transport")
                        else:
                            self.log_message("Select a unit to use helicopter transport")
                    elif self.game_state:
                        self.log_message("Helicopter Transport technology required")

                # Open tech tree (TAB key)
                elif event.key == pygame.K_TAB:
                    if self.game_state:
                        self.tech_tree_open = not self.tech_tree_open

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

                elif event.key == pygame.K_0:  # Recruit Super Soldier (requires tech)
                    if self.game_state.current_team != 'player':
                        self.log_message("Cannot recruit units during enemy turn!")
                    elif self.selected_city:
                        if self.game_state.has_tech('super_soldier_program'):
                            self.building_placement_mode = 'super_soldier'
                            self.log_message("Recruit Super Soldier unit at city location (elite)")
                        else:
                            self.log_message("Research Super Soldier Program first!")

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
                            if self.selected_city.can_build('manufacture_cure', self.game_state):
                                self.building_placement_mode = 'manufacture_cure'
                                self.log_message("🧪 Initiating cure manufacturing... Click city to confirm!")
                            else:
                                # Show dynamic cost based on tech
                                food_cost = 350 if self.game_state.has_tech('cure_research') else 500
                                materials_cost = 350 if self.game_state.has_tech('cure_research') else 500
                                self.log_message(f"Not enough resources! Need {food_cost} food, {materials_cost} materials, 200 medicine, and 1 cure.")
                        else:
                            if 'hospital' not in self.selected_city.buildings:
                                self.log_message("City needs a hospital to manufacture the cure!")
                            else:
                                self.log_message("No cure available! Find it at the Research Lab.")

                # Handle exit confirmation Y/N/K
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

                elif event.key == pygame.K_k:
                    if self.exit_confirmation_open:
                        # Open help panel from exit confirmation
                        self.exit_confirmation_open = False
                        self.help_panel_open = True
                    else:
                        # Open help panel directly
                        self.help_panel_open = True

                # Debug: Toggle full map reveal (F1)
                elif event.key == pygame.K_F1:
                    self.debug_reveal_map = not self.debug_reveal_map
                    if self.debug_reveal_map:
                        self.log_message("DEBUG: Full map revealed")
                    else:
                        self.log_message("DEBUG: Map visibility restored to normal")

                # Debug: Give resources and tech points (F2)
                elif event.key == pygame.K_F2:
                    if self.selected_unit and self.selected_unit.team == 'player':
                        self.selected_unit.inventory['food'] += 1000
                        self.selected_unit.inventory['materials'] += 1000
                        self.selected_unit.inventory['medicine'] += 1000
                        self.selected_unit.inventory['cure'] = self.selected_unit.inventory.get('cure', 0) + 1
                        self.game_state.tech_points += 1000
                        self.log_message("DEBUG: Added 1000 resources, 1 cure, and 1000 tech points to unit")
                    else:
                        self.log_message("DEBUG: Select a player unit first!")

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

                # Handle helicopter menu clicks
                if self.helicopter_menu_open and event.button == 1:
                    # Convert mouse position to tile coordinates
                    tile_x, tile_y = self.renderer.screen_to_tile(mouse_x, mouse_y)

                    # Check if clicked on a city
                    destination_city = self.game_state.get_city_at(tile_x, tile_y)
                    if destination_city and self.teleporting_unit:
                        # Get source city
                        source_city = self.game_state.get_city_at(self.teleporting_unit.x, self.teleporting_unit.y)

                        if destination_city == source_city:
                            self.log_message("Already at this city!")
                        else:
                            # Teleport the unit
                            self.teleporting_unit.x = destination_city.x
                            self.teleporting_unit.y = destination_city.y
                            self.teleporting_unit.moves_remaining = 0  # Use up movement
                            self.log_message(f"🚁 {self.teleporting_unit.unit_type} teleported to {destination_city.name}!")
                            self.has_unsaved_changes = True

                            # Update fog of war
                            self.game_state.update_visibility()

                            # Close menu
                            self.helicopter_menu_open = False
                            self.teleporting_unit = None
                    continue  # Don't process other click handlers

                # Handle tech tree clicks
                if self.tech_tree_open and event.button == 1:
                    from tech_tree import TECH_TREE, can_research, get_tech_cost
                    # Check if any tech was clicked
                    if hasattr(self, 'tech_positions'):
                        for tech_id, (tx, ty, tw, th) in self.tech_positions.items():
                            if tx <= mouse_x <= tx + tw and ty <= mouse_y <= ty + th:
                                # Check if can research
                                if tech_id not in self.game_state.researched_techs:
                                    can_afford = can_research(tech_id, self.game_state.researched_techs)
                                    tech_cost = get_tech_cost(tech_id, self.game_state.researched_techs)
                                    if can_afford and self.game_state.tech_points >= tech_cost:
                                        # Research the tech!
                                        self.game_state.tech_points -= tech_cost
                                        self.game_state.researched_techs.add(tech_id)
                                        self.log_message(f"Researched: {TECH_TREE[tech_id]['name']}!")
                                        self.has_unsaved_changes = True

                                        # Apply immediate effects for vision-related techs
                                        if tech_id in ['scout_training', 'watchtower']:
                                            self.game_state.update_visibility()

                                        # Apply immediate effects for advanced_weaponry
                                        if tech_id == 'advanced_weaponry':
                                            for unit in self.game_state.units:
                                                if unit.team == 'player' and unit.unit_type == 'soldier':
                                                    unit.attack_power += 10
                                                    self.log_message(f"Soldier at ({unit.x}, {unit.y}) attack increased to {unit.attack_power}!")

                                        # Apply immediate effects for armor_plating
                                        if tech_id == 'armor_plating':
                                            for unit in self.game_state.units:
                                                if unit.team == 'player':
                                                    unit.max_health += 40
                                                    unit.health += 40
                                            self.log_message("All player units gained +40 max HP!")

                                        # Apply immediate effects for rapid_response
                                        if tech_id == 'rapid_response':
                                            for unit in self.game_state.units:
                                                if unit.team == 'player':
                                                    unit.max_moves += 1
                                                    unit.moves_remaining += 1
                                            self.log_message("All player units gained +1 movement!")
                                break
                    continue

                # Handle difficulty dialog clicks (only if load menu is not open)
                if self.difficulty_dialog_open and not self.load_menu_open:
                    # Only handle left clicks in difficulty dialog
                    if event.button == 1:
                        difficulty_clicked = self.get_difficulty_button_clicked(mouse_x, mouse_y)
                        if difficulty_clicked:
                            self.initialize_game(difficulty_clicked)
                    continue

                # Check if click is on message box (toggle message log)
                if self.is_message_box_clicked(mouse_x, mouse_y):
                    self.message_log_open = not self.message_log_open
                    continue

                # Check if click is on mini-map (takes priority)
                if self.game_state and self.renderer and self.renderer.is_click_on_minimap(mouse_x, mouse_y):
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
                            result = GameState.load_game(clicked_save)
                            if result:
                                loaded_state, camera_x, camera_y = result
                                self.game_state = loaded_state
                                self.difficulty = loaded_state.difficulty  # Update main game difficulty
                                self.difficulty_dialog_open = False  # Game is now started

                                # Initialize renderer if not already done
                                if not self.renderer:
                                    self.renderer = Renderer(self.screen_width, self.screen_height, self.tile_size)

                                self.renderer.camera_x = camera_x
                                self.renderer.camera_y = camera_y
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
                            print(f"DEBUG: manufacture_cure clicked, can_build={self.selected_city.can_build('manufacture_cure', self.game_state)}")
                            if self.selected_city.can_build('manufacture_cure', self.game_state):
                                result = self.selected_city.build('manufacture_cure', self.selected_city.x, self.selected_city.y, 0, self.game_state)
                                print(f"DEBUG: build() returned: {result}")
                                if result == 'cure_manufactured':
                                    # Start the cure manufacturing process
                                    self.game_state.start_cure_manufacturing(self.selected_city)
                                    turns_needed = self.game_state.cure_manufacturing_turns_required[self.game_state.difficulty]
                                    self.log_message(f"🧪 Cure manufacturing started! {turns_needed} turns remaining. ALL ZOMBIES are now attracted to this city!")
                            else:
                                self.log_message("Not enough resources to manufacture cure!")
                            self.building_placement_mode = None

                        # Handle unit recruitment (special case - spawns at city, no adjacency needed)
                        elif building_type in ['survivor', 'scout', 'soldier', 'medic', 'super_soldier']:
                            # Check if city tile is already occupied by a unit
                            if self.game_state.get_unit_at(self.selected_city.x, self.selected_city.y):
                                self.log_message("Cannot recruit - city tile is occupied by another unit!")
                                self.building_placement_mode = None
                            else:
                                costs = {
                                    'survivor': {'food': 20, 'materials': 10},
                                    'scout': {'food': 15, 'materials': 5},
                                    'soldier': {'food': 30, 'materials': 20},
                                    'medic': {'food': 25, 'materials': 15, 'medicine': 10},
                                    'super_soldier': {'food': 50, 'materials': 40}
                                }
                                cost = costs[building_type]

                                # Check city resources
                                can_afford = all(self.selected_city.resources.get(res, 0) >= amt
                                                for res, amt in cost.items())
                                if can_afford:
                                    for res, amt in cost.items():
                                        self.selected_city.resources[res] -= amt
                                    new_unit = Unit(self.selected_city.x, self.selected_city.y, building_type, 'player', self.difficulty, self.game_state)

                                    # Apply combat_training tech - new units spawn at level 2
                                    if self.game_state.has_tech('combat_training'):
                                        # Level units up to level 2 (which requires 10 XP)
                                        while new_unit.level < 2:
                                            new_unit.gain_xp(10)  # Give enough XP to level up

                                    self.game_state.units.append(new_unit)
                                    self.log_message(f"Recruited {building_type.replace('_', ' ').title()} at {self.selected_city.name}!")
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
                                # Check if tile is not occupied by city, building, or enemy unit
                                else:
                                    unit_at_tile = self.game_state.get_unit_at(tile_x, tile_y)
                                    enemy_unit_blocking = unit_at_tile and unit_at_tile.team != 'player'

                                    if not enemy_unit_blocking and \
                                       not self.game_state.get_city_at(tile_x, tile_y) and \
                                       not self.game_state.get_building_at(tile_x, tile_y):

                                        terrain = self.game_state.map_grid[tile_y][tile_x]

                                        # Special validation for dock - must be on water
                                        if building_type == 'dock' and terrain != TileType.WATER:
                                            self.log_message("Docks can only be built on water!")
                                            self.building_placement_mode = None
                                        else:
                                            # Regular building placement using city resources
                                            if self.selected_city.can_build(building_type, self.game_state):
                                                result = self.selected_city.build(building_type, tile_x, tile_y, terrain, self.game_state)

                                                # Check if cure was manufactured (special win condition)
                                                if result == 'cure_manufactured':
                                                    # Start the cure manufacturing process
                                                    self.game_state.start_cure_manufacturing(self.selected_city)
                                                    turns_needed = self.game_state.cure_manufacturing_turns_required[self.game_state.difficulty]
                                                    self.log_message(f"🧪 Cure manufacturing started! {turns_needed} turns remaining. ALL ZOMBIES are now attracted to this city!")
                                                else:
                                                    self.log_message(f"Built {building_type} at ({tile_x}, {tile_y})!")
                                            else:
                                                self.log_message(f"Not enough city resources!")

                                            self.building_placement_mode = None
                                            self.game_state.update_visibility()
                                    else:
                                        if enemy_unit_blocking:
                                            self.log_message("Cannot build here - enemy unit in the way!")
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
                                # No city, check for unit (allow selecting any unit)
                                unit = self.game_state.get_unit_at(tile_x, tile_y)
                                if unit:
                                    self.selected_unit = unit
                                    self.selected_city = None
                                    if unit.team != self.game_state.current_team:
                                        self.log_message(f"Selected enemy {unit.unit_type} - HP: {unit.health}/{unit.max_health}, Attack: {unit.attack_power}")
                                else:
                                    self.selected_unit = None
                                    self.selected_city = None
                        else:
                            # Normal click: prioritize units (allow selecting any unit)
                            unit = self.game_state.get_unit_at(tile_x, tile_y)
                            if unit:
                                self.selected_unit = unit
                                self.selected_city = None
                                if unit.team != self.game_state.current_team:
                                    self.log_message(f"Selected enemy {unit.unit_type} - HP: {unit.health}/{unit.max_health}, Attack: {unit.attack_power}")
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

                                        # Award tech points for killing enemies (player only)
                                        if self.selected_unit.team == 'player' and blocking_unit.team == 'enemy':
                                            tech_points = 20 if blocking_unit.size > 1 else 5  # 20 for super zombies, 5 for regular
                                            self.game_state.tech_points += tech_points
                                            self.game_state.zombies_killed_count += 1

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
                                from map_generator import TileType
                                terrain = self.game_state.map_grid[new_y][new_x]

                                # Block movement into water
                                if terrain == TileType.WATER:
                                    self.log_message("Cannot move into water!")
                                else:
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
        # Capture all zombie positions and moves before AI turn
        self.zombie_positions_snapshot = {}
        self.zombie_action_log = {}

        for unit in self.game_state.units:
            if unit.team == 'enemy' and (unit.unit_type == 'zombie' or unit.unit_type == 'super_zombie'):
                self.zombie_positions_snapshot[unit] = (unit.x, unit.y)
                # Track initial moves to count attacks
                self.zombie_action_log[unit] = {'start_moves': unit.max_moves, 'actions': []}

        # Execute AI turn - zombies will move to new positions
        self.game_state.execute_ai_turn()

        # Build animation dict with start and end positions, and count actions
        self.zombie_animations = {}
        for unit in self.game_state.units:
            if unit.team == 'enemy' and (unit.unit_type == 'zombie' or unit.unit_type == 'super_zombie'):
                if unit in self.zombie_positions_snapshot:
                    start_x, start_y = self.zombie_positions_snapshot[unit]
                    end_x, end_y = unit.x, unit.y

                    # Calculate how many moves were used
                    if unit in self.zombie_action_log:
                        moves_used = self.zombie_action_log[unit]['start_moves'] - unit.moves_remaining
                    else:
                        moves_used = 0

                    # Calculate distance moved (Chebyshev distance)
                    distance_moved = max(abs(end_x - start_x), abs(end_y - start_y))

                    # If moves used exceeds distance moved, zombie attacked
                    attacks_made = max(0, moves_used - distance_moved)

                    # Determine animation type
                    if distance_moved > 0 and attacks_made == 0:
                        # Pure movement - show moving to final position
                        self.zombie_animations[unit] = {
                            'type': 'move',
                            'start': (start_x, start_y),
                            'end': (end_x, end_y),
                            'attack_count': 0
                        }
                    elif distance_moved > 0 and attacks_made > 0:
                        # Moved and attacked - show move then attack from final position
                        attack_target = self._find_nearest_target_for_attack_animation(unit)
                        if attack_target:
                            self.zombie_animations[unit] = {
                                'type': 'move_attack',
                                'start': (start_x, start_y),
                                'end': (end_x, end_y),
                                'attack_target': attack_target,
                                'attack_count': attacks_made
                            }
                        else:
                            # No target found, just show movement
                            self.zombie_animations[unit] = {
                                'type': 'move',
                                'start': (start_x, start_y),
                                'end': (end_x, end_y),
                                'attack_count': 0
                            }
                    elif distance_moved == 0 and attacks_made > 0:
                        # Pure attack - no movement
                        attack_target = self._find_nearest_target_for_attack_animation(unit)
                        if attack_target:
                            self.zombie_animations[unit] = {
                                'type': 'attack',
                                'start': (end_x, end_y),
                                'end': attack_target,
                                'attack_count': attacks_made
                            }

        # Start animation
        self.animating_zombies = True
        self.animation_start_time = pygame.time.get_ticks()

    def _find_nearest_target_for_attack_animation(self, zombie):
        """Find the actual target tile for attack animation"""
        # Use the recorded attack target if available
        if hasattr(zombie, 'last_attack_target') and zombie.last_attack_target:
            return zombie.last_attack_target

        # Fallback: check all adjacent tiles for units, cities, or buildings
        # (This shouldn't happen if the zombie attacked, but provides backward compatibility)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                check_x = zombie.x + dx
                check_y = zombie.y + dy

                # Check if there's a unit, city, or building there
                target_unit = self.game_state.get_unit_at(check_x, check_y)
                if target_unit and target_unit.team != zombie.team:
                    return (check_x, check_y)

                target_city = self.game_state.get_city_at(check_x, check_y)
                if target_city:
                    return (check_x, check_y)

                target_building = self.game_state.get_building_at(check_x, check_y)
                if target_building:
                    return (check_x, check_y)

        return None

    def get_unit_render_position(self, unit):
        """Get the position where a unit should be rendered (handles animation)"""
        if self.animating_zombies and unit in self.zombie_animations:
            elapsed = (pygame.time.get_ticks() - self.animation_start_time) / 1000.0
            progress = min(1.0, elapsed / self.animation_duration)

            anim = self.zombie_animations[unit]

            if anim['type'] == 'move':
                # Linear interpolation for movement
                start_x, start_y = anim['start']
                end_x, end_y = anim['end']
                render_x = start_x + (end_x - start_x) * progress
                render_y = start_y + (end_y - start_y) * progress
                return (render_x, render_y)

            elif anim['type'] == 'attack':
                # Bumping animation for attacks
                start_x, start_y = anim['start']
                end_x, end_y = anim['end']
                attack_count = anim['attack_count']
                # Each attack gets equal time in the 1-second duration
                time_per_attack = 1.0 / max(1, attack_count)
                # Progress within current attack cycle (0 to 1)
                cycle_progress = (progress % time_per_attack) / time_per_attack

                # Bump 30% toward target, then return (sine wave for smooth motion)
                bump_amount = 0.3 * math.sin(cycle_progress * math.pi)
                render_x = start_x + (end_x - start_x) * bump_amount
                render_y = start_y + (end_y - start_y) * bump_amount
                return (render_x, render_y)

            elif anim['type'] == 'move_attack':
                # Combined movement and attack animation
                # First half: move to final position
                # Second half: attack from final position
                start_x, start_y = anim['start']
                end_x, end_y = anim['end']
                attack_target_x, attack_target_y = anim['attack_target']
                attack_count = anim['attack_count']

                if progress < 0.5:
                    # First half: movement (0 to 0.5 progress maps to 0 to 1 movement)
                    move_progress = progress * 2.0
                    render_x = start_x + (end_x - start_x) * move_progress
                    render_y = start_y + (end_y - start_y) * move_progress
                    return (render_x, render_y)
                else:
                    # Second half: attack animation (0.5 to 1.0 progress maps to attack cycle)
                    attack_progress = (progress - 0.5) * 2.0  # Normalize to 0-1
                    time_per_attack = 1.0 / max(1, attack_count)
                    cycle_progress = (attack_progress % time_per_attack) / time_per_attack

                    # Bump 30% toward target, then return
                    bump_amount = 0.3 * math.sin(cycle_progress * math.pi)
                    render_x = end_x + (attack_target_x - end_x) * bump_amount
                    render_y = end_y + (attack_target_y - end_y) * bump_amount
                    return (render_x, render_y)
        else:
            return (unit.x, unit.y)

    def update(self):
        """Update game logic"""
        # Skip updates if difficulty dialog is open
        if self.difficulty_dialog_open:
            return

        # Get delta time for timer
        dt = self.clock.get_time() / 1000.0  # Convert to seconds

        # Handle continuous camera scrolling (WASD keys held down)
        keys = pygame.key.get_pressed()
        ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        # Only scroll if Ctrl is not pressed
        if not ctrl_pressed:
            scroll_speed = 15  # pixels per frame at 60 FPS
            if keys[pygame.K_w]:
                self.renderer.move_camera(0, -scroll_speed)
            if keys[pygame.K_s]:
                self.renderer.move_camera(0, scroll_speed)
            if keys[pygame.K_a]:
                self.renderer.move_camera(-scroll_speed, 0)
            if keys[pygame.K_d]:
                self.renderer.move_camera(scroll_speed, 0)

        # Handle zombie animation
        if self.animating_zombies:
            elapsed = (pygame.time.get_ticks() - self.animation_start_time) / 1000.0
            if elapsed >= self.animation_duration:
                # Animation complete, end enemy turn
                self.animating_zombies = False
                self.zombie_animations = {}

                # Clear last_attack_target from all zombies
                for unit in self.game_state.units:
                    if unit.team == 'enemy' and hasattr(unit, 'last_attack_target'):
                        unit.last_attack_target = None

                # Now end enemy turn and start player turn
                self.game_state.current_team = 'player'
                self.game_state.turn += 1
                # Reset player unit moves
                for unit in self.game_state.units:
                    if unit.team == 'player':
                        unit.reset_moves()

                # Handle cure manufacturing progress
                if self.game_state.cure_manufacturing_city:
                    self.game_state.cure_manufacturing_turns_remaining -= 1
                    self.log_message(f"🧪 Cure manufacturing: {self.game_state.cure_manufacturing_turns_remaining} turns remaining!")
                    if self.game_state.cure_manufacturing_turns_remaining <= 0:
                        # Cure is complete!
                        self.game_state.manufacture_cure()
                        self.log_message(f"🎉 CURE COMPLETE! The city survived the onslaught!")

                # Autosave at the start of player's turn
                self.game_state.autosave(self.renderer.camera_x, self.renderer.camera_y)
                # Produce resources in all cities
                for city in self.game_state.cities:
                    production = city.produce_resources(self.game_state)
                    if any(production.values()):
                        prod_str = ', '.join([f"{k}: +{v}" for k, v in production.items() if v > 0])
                        self.log_message(f"{city.name} produced: {prod_str}")
                # Check for cure manufacturing completion
                if self.game_state.game_won:
                    self.cure_leaderboard = GameState.save_cure_victory(self.game_state.turn, self.game_state.difficulty)
                    self.game_won = True
                    self.victory_panel_open = True
                    self.final_score = self.game_state.turn
                    self.log_message(f"🎉 VICTORY! Cure manufactured on turn {self.game_state.turn}!")

                # Check if cure manufacturing city was destroyed
                if self.game_state.cure_manufacturing_city:
                    if self.game_state.cure_manufacturing_city not in self.game_state.cities:
                        self.log_message(f"💀 GAME OVER! The city manufacturing the cure was destroyed!")
                        self.game_over = True
                        self.game_state.cure_manufacturing_city = None
                        self.game_state.cure_manufacturing_turns_remaining = 0

                # Apply automated defenses damage to adjacent zombies
                defense_results = self.game_state.apply_automated_defenses()
                if defense_results['damaged'] > 0 or defense_results['killed'] > 0:
                    killed = defense_results['killed']
                    damaged = defense_results['damaged'] - killed  # Subtract killed from total damaged
                    if killed > 0 and damaged > 0:
                        self.log_message(f"⚡ Automated Defenses: {killed} zombie(s) destroyed, {damaged} damaged!")
                    elif killed > 0:
                        self.log_message(f"⚡ Automated Defenses: {killed} zombie(s) destroyed!")
                    elif damaged > 0:
                        self.log_message(f"⚡ Automated Defenses: {damaged} zombie(s) damaged!")
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
        menu_width = 500
        menu_x = self.screen_width // 2 - menu_width // 2
        menu_y = 150  # Match render_load_menu
        list_y = menu_y + 150

        # Calculate which saves are visible based on scroll offset
        visible_saves = self.available_saves[self.save_list_scroll_offset:self.save_list_scroll_offset + 10]

        for i, save_file in enumerate(visible_saves):
            file_y = list_y + 45 + i * 25  # Match render_load_menu spacing
            if menu_x + 20 <= mouse_x <= menu_x + menu_width - 20 and file_y <= mouse_y <= file_y + 22:
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

    def get_difficulty_button_clicked(self, mouse_x, mouse_y):
        """Check if a difficulty button was clicked and return the difficulty level"""
        dialog_width = 650
        dialog_height = 650
        dialog_x = self.screen_width // 2 - dialog_width // 2
        dialog_y = self.screen_height // 2 - dialog_height // 2

        # Button dimensions
        button_width = 400
        button_height = 60
        button_x = dialog_x + (dialog_width - button_width) // 2

        # Check each difficulty button
        difficulties = ['easy', 'medium', 'hard']
        for i, diff in enumerate(difficulties):
            button_y = dialog_y + 120 + i * 80
            if button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height:
                self.selected_difficulty_button = diff
                return None  # Don't start immediately, wait for START button

        # Check map size buttons
        map_sizes = [40, 60, 100]
        small_button_width = 180
        small_button_height = 70
        spacing = 20
        total_width = small_button_width * 3 + spacing * 2
        start_x = dialog_x + (dialog_width - total_width) // 2
        map_button_y = dialog_y + 430

        for i, size in enumerate(map_sizes):
            map_button_x = start_x + i * (small_button_width + spacing)
            if map_button_x <= mouse_x <= map_button_x + small_button_width and map_button_y <= mouse_y <= map_button_y + small_button_height:
                self.selected_map_size = size
                return None  # Don't start immediately, wait for START button

        # Check START button
        start_button_width = 200
        start_button_height = 50
        start_button_x = dialog_x + (dialog_width - start_button_width) // 2
        start_button_y = dialog_y + dialog_height - 70

        if start_button_x <= mouse_x <= start_button_x + start_button_width and start_button_y <= mouse_y <= start_button_y + start_button_height:
            return self.selected_difficulty_button  # Start the game with selected settings

        return None

    def is_message_box_clicked(self, mouse_x, mouse_y):
        """Check if the message box in top right was clicked"""
        box_width = 500
        box_height = 30
        box_x = self.screen_width - box_width - 10
        box_y = 10
        return box_x <= mouse_x <= box_x + box_width and box_y <= mouse_y <= box_y + box_height

    def render(self):
        """Render the game"""
        # Show difficulty dialog if game not started
        if self.difficulty_dialog_open:
            self.render_difficulty_dialog()
            # Also render load menu if open
            if self.load_menu_open:
                self.render_load_menu()
            pygame.display.flip()
            return

        # Normal game rendering
        self.renderer.render(self.screen, self.game_state, self.selected_unit, self.selected_city, self.selected_tile, self.hovered_tile, self.building_placement_mode, self.debug_reveal_map, self)

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

        # Render notification dialog on top of everything
        if self.notification_dialog_open:
            self.render_notification_dialog()

        # Render tech tree on top of everything
        if self.tech_tree_open:
            self.render_tech_tree()

        # Render help panel on top of everything
        if self.help_panel_open:
            self.render_help_panel()

        # Render helicopter menu on top of everything
        if self.helicopter_menu_open:
            self.render_helicopter_menu()

        pygame.display.flip()

    def render_difficulty_dialog(self):
        """Render the difficulty selection dialog"""
        # Black background
        self.screen.fill((20, 20, 30))

        # Dialog panel (larger to fit map size options)
        dialog_width = 650
        dialog_height = 650
        dialog_x = self.screen_width // 2 - dialog_width // 2
        dialog_y = self.screen_height // 2 - dialog_height // 2

        pygame.draw.rect(self.screen, (40, 40, 60), (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, (100, 150, 200), (dialog_x, dialog_y, dialog_width, dialog_height), 4)

        # Title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("New Game Setup", True, (150, 200, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 40))
        self.screen.blit(title, title_rect)

        # Difficulty section title
        section_font = pygame.font.Font(None, 32)
        diff_title = section_font.render("Difficulty", True, (200, 200, 200))
        diff_title_rect = diff_title.get_rect(center=(self.screen_width // 2, dialog_y + 85))
        self.screen.blit(diff_title, diff_title_rect)

        # Button dimensions
        button_width = 400
        button_height = 60
        button_x = dialog_x + (dialog_width - button_width) // 2

        # Difficulty descriptions
        descriptions = {
            'easy': 'Fewer zombies, more resources',
            'medium': 'Balanced gameplay',
            'hard': 'More zombies, fewer resources'
        }

        # Render difficulty buttons
        difficulties = ['easy', 'medium', 'hard']
        button_colors = {
            'easy': (50, 150, 50),
            'medium': (150, 150, 50),
            'hard': (150, 50, 50)
        }

        mouse_x, mouse_y = pygame.mouse.get_pos()

        for i, diff in enumerate(difficulties):
            button_y = dialog_y + 120 + i * 80

            # Check if mouse is hovering or if it's selected
            is_hovering = button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height
            is_selected = self.selected_difficulty_button == diff

            # Button background
            if is_hovering or is_selected:
                pygame.draw.rect(self.screen, button_colors[diff], (button_x, button_y, button_width, button_height))
                pygame.draw.rect(self.screen, (200, 200, 200), (button_x, button_y, button_width, button_height), 3)
            else:
                color = tuple(c // 2 for c in button_colors[diff])
                pygame.draw.rect(self.screen, color, (button_x, button_y, button_width, button_height))
                pygame.draw.rect(self.screen, (100, 100, 100), (button_x, button_y, button_width, button_height), 2)

            # Button text
            button_font = pygame.font.Font(None, 36)
            button_text = button_font.render(diff.upper(), True, (255, 255, 255))
            button_text_rect = button_text.get_rect(center=(button_x + button_width // 2, button_y + 20))
            self.screen.blit(button_text, button_text_rect)

            # Description
            desc_font = pygame.font.Font(None, 20)
            desc_text = desc_font.render(descriptions[diff], True, (180, 180, 180))
            desc_rect = desc_text.get_rect(center=(button_x + button_width // 2, button_y + 45))
            self.screen.blit(desc_text, desc_rect)

        # Map Size section
        map_title = section_font.render("Map Size", True, (200, 200, 200))
        map_title_rect = map_title.get_rect(center=(self.screen_width // 2, dialog_y + 390))
        self.screen.blit(map_title, map_title_rect)

        # Map size buttons (horizontal layout)
        map_sizes = [40, 60, 100]
        map_descriptions = {
            40: 'Small - Quick games',
            60: 'Medium - Balanced',
            100: 'Large - Epic battles'
        }

        small_button_width = 180
        small_button_height = 70
        spacing = 20
        total_width = small_button_width * 3 + spacing * 2
        start_x = dialog_x + (dialog_width - total_width) // 2
        map_button_y = dialog_y + 430

        for i, size in enumerate(map_sizes):
            map_button_x = start_x + i * (small_button_width + spacing)

            # Check if hovering or selected
            is_hovering = map_button_x <= mouse_x <= map_button_x + small_button_width and map_button_y <= mouse_y <= map_button_y + small_button_height
            is_selected = self.selected_map_size == size

            # Button background
            button_color = (80, 100, 150) if (is_hovering or is_selected) else (40, 50, 80)
            border_color = (200, 200, 200) if (is_hovering or is_selected) else (100, 100, 100)
            border_width = 3 if (is_hovering or is_selected) else 2

            pygame.draw.rect(self.screen, button_color, (map_button_x, map_button_y, small_button_width, small_button_height))
            pygame.draw.rect(self.screen, border_color, (map_button_x, map_button_y, small_button_width, small_button_height), border_width)

            # Button text
            size_font = pygame.font.Font(None, 32)
            size_text = size_font.render(f"{size}x{size}", True, (255, 255, 255))
            size_rect = size_text.get_rect(center=(map_button_x + small_button_width // 2, map_button_y + 25))
            self.screen.blit(size_text, size_rect)

            # Description
            desc_small_font = pygame.font.Font(None, 16)
            desc_small_text = desc_small_font.render(map_descriptions[size], True, (180, 180, 180))
            desc_small_rect = desc_small_text.get_rect(center=(map_button_x + small_button_width // 2, map_button_y + 50))
            self.screen.blit(desc_small_text, desc_small_rect)

        # Instructions
        inst_font = pygame.font.Font(None, 20)
        inst_text = inst_font.render("Select difficulty and map size, then click START or press Enter", True, (150, 150, 150))
        inst_rect = inst_text.get_rect(center=(self.screen_width // 2, dialog_y + dialog_height - 100))
        self.screen.blit(inst_text, inst_rect)

        # Start button
        start_button_width = 200
        start_button_height = 50
        start_button_x = dialog_x + (dialog_width - start_button_width) // 2
        start_button_y = dialog_y + dialog_height - 70

        is_start_hovering = start_button_x <= mouse_x <= start_button_x + start_button_width and start_button_y <= mouse_y <= start_button_y + start_button_height
        start_color = (50, 200, 50) if is_start_hovering else (30, 120, 30)

        pygame.draw.rect(self.screen, start_color, (start_button_x, start_button_y, start_button_width, start_button_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (start_button_x, start_button_y, start_button_width, start_button_height), 3)

        start_font = pygame.font.Font(None, 36)
        start_text = start_font.render("START", True, (255, 255, 255))
        start_rect = start_text.get_rect(center=(start_button_x + start_button_width // 2, start_button_y + start_button_height // 2))
        self.screen.blit(start_text, start_rect)

        # Load game hint (below START button)
        load_font = pygame.font.Font(None, 18)
        load_text = load_font.render("Or press Ctrl+L to load a saved game", True, (120, 120, 150))
        load_rect = load_text.get_rect(center=(self.screen_width // 2, dialog_y + dialog_height - 15))
        self.screen.blit(load_text, load_rect)

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
        options_font = pygame.font.Font(None, 28)
        options1 = options_font.render("Y - Exit  |  N - Cancel  |  K - Shortcut Keys  |  ESC - Cancel", True, (200, 255, 200))
        options1_rect = options1.get_rect(center=(self.screen_width // 2, dialog_y + 200))
        self.screen.blit(options1, options1_rect)

    def render_help_panel(self):
        """Render the keyboard shortcuts help panel"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dialog panel
        panel_width = 900
        panel_height = 700
        panel_x = self.screen_width // 2 - panel_width // 2
        panel_y = self.screen_height // 2 - panel_height // 2

        pygame.draw.rect(self.screen, (40, 50, 60), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, (100, 200, 255), (panel_x, panel_y, panel_width, panel_height), 4)

        # Title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("Keyboard Shortcuts", True, (100, 200, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, panel_y + 40))
        self.screen.blit(title, title_rect)

        # Define shortcuts in categories
        shortcuts = [
            ("CAMERA", [
                ("W/A/S/D", "Move camera (Ctrl not pressed)"),
                ("Mini-Map Click", "Jump to location"),
            ]),
            ("UNIT CONTROL", [
                ("Left Click", "Select unit / Select tile"),
                ("Shift + Click", "Select city"),
                ("Right Click", "Move unit / Attack / Heal"),
                ("E", "End turn"),
            ]),
            ("CITY MANAGEMENT (City Selected)", [
                ("1/2/3", "Build Farm/Workshop/Hospital"),
                ("4/5", "Build Wall/Dock"),
                ("6/7/8/9", "Recruit Survivor/Scout/Soldier/Medic"),
                ("U", "Upgrade building"),
                ("C", "Manufacture The Cure"),
            ]),
            ("UNIT ACTIONS", [
                ("F", "Found new city"),
                ("R", "Scavenge resources"),
                ("T", "Transfer resources to city"),
                ("G", "Gather resources from city"),
                ("Q", "Triangulate lab (scouts only)"),
                ("P", "Helicopter transport (if researched)"),
            ]),
            ("SYSTEM", [
                ("Ctrl+S", "Save game"),
                ("Ctrl+L", "Load game"),
                ("TAB", "Tech tree"),
                ("ESC", "Exit (shows warning if unsaved)"),
            ]),
        ]

        # Render shortcuts
        y_offset = panel_y + 90
        section_font = pygame.font.Font(None, 28)
        key_font = pygame.font.Font(None, 24)
        desc_font = pygame.font.Font(None, 24)

        left_column_x = panel_x + 40
        right_column_x = panel_x + panel_width // 2 + 20
        column_width = panel_width // 2 - 60

        current_column = 0
        column_y = y_offset

        for category, items in shortcuts:
            # Determine which column to use
            if current_column == 0:
                x_pos = left_column_x
            else:
                x_pos = right_column_x

            # Section header
            section_text = section_font.render(category, True, (255, 200, 100))
            self.screen.blit(section_text, (x_pos, column_y))
            column_y += 35

            # Shortcuts
            for key, description in items:
                # Key (in yellow/gold)
                key_text = key_font.render(key, True, (255, 255, 150))
                self.screen.blit(key_text, (x_pos + 10, column_y))

                # Description (in white)
                desc_text = desc_font.render(description, True, (200, 200, 200))
                self.screen.blit(desc_text, (x_pos + 180, column_y))

                column_y += 28

            column_y += 15  # Extra space after section

            # Switch to right column after 2 sections
            if current_column == 0 and category == "CITY MANAGEMENT (City Selected)":
                current_column = 1
                column_y = y_offset

        # Close instruction at bottom
        close_font = pygame.font.Font(None, 32)
        close_text = close_font.render("Press ESC or K to close", True, (150, 255, 150))
        close_rect = close_text.get_rect(center=(self.screen_width // 2, panel_y + panel_height - 40))
        self.screen.blit(close_text, close_rect)

    def render_notification_dialog(self):
        """Render a standard notification dialog box"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Calculate dialog size based on content
        num_messages = len(self.notification_dialog_data['messages'])
        base_height = 200
        message_height = num_messages * 35
        dialog_height = base_height + message_height

        dialog_width = 650
        dialog_x = self.screen_width // 2 - dialog_width // 2
        dialog_y = self.screen_height // 2 - dialog_height // 2

        # Color scheme based on type
        if self.notification_dialog_data['type'] == 'confirm':
            bg_color = (60, 50, 40)
            border_color = (255, 200, 100)
            title_color = (255, 200, 100)
        else:  # info
            bg_color = (40, 50, 60)
            border_color = (100, 150, 255)
            title_color = (150, 200, 255)

        # Dialog panel
        pygame.draw.rect(self.screen, bg_color, (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, border_color, (dialog_x, dialog_y, dialog_width, dialog_height), 4)

        # Title
        title_font = pygame.font.Font(None, 42)
        title = title_font.render(self.notification_dialog_data['title'], True, title_color)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 40))
        self.screen.blit(title, title_rect)

        # Messages
        message_font = pygame.font.Font(None, 26)
        y_offset = dialog_y + 90
        for msg in self.notification_dialog_data['messages']:
            message_text = message_font.render(msg, True, (255, 255, 255))
            message_rect = message_text.get_rect(center=(self.screen_width // 2, y_offset))
            self.screen.blit(message_text, message_rect)
            y_offset += 35

        # Controls based on type
        controls_font = pygame.font.Font(None, 28)
        if self.notification_dialog_data['type'] == 'confirm':
            controls_text = "Press Y to Confirm  |  Press N or ESC to Cancel"
            controls_color = (200, 255, 200)
        else:  # info
            controls_text = "Press SPACE or ESC to Close"
            controls_color = (200, 200, 255)

        controls = controls_font.render(controls_text, True, controls_color)
        controls_rect = controls.get_rect(center=(self.screen_width // 2, dialog_y + dialog_height - 40))
        self.screen.blit(controls, controls_rect)

    def render_tech_tree(self):
        """Render the tech tree interface"""
        from tech_tree import TECH_TREE, can_research, get_tech_cost

        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Main panel
        panel_width = 1400
        panel_height = 850
        panel_x = self.screen_width // 2 - panel_width // 2
        panel_y = self.screen_height // 2 - panel_height // 2

        pygame.draw.rect(self.screen, (30, 30, 40), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, (100, 150, 200), (panel_x, panel_y, panel_width, panel_height), 4)

        # Title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("🔬 Technology Tree", True, (150, 200, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, panel_y + 35))
        self.screen.blit(title, title_rect)

        # Tech points display
        points_font = pygame.font.Font(None, 36)
        points_text = points_font.render(f"Tech Points: {self.game_state.tech_points}", True, (255, 255, 100))
        points_rect = points_text.get_rect(center=(self.screen_width // 2, panel_y + 80))
        self.screen.blit(points_text, points_rect)

        # Categories
        cat_y = panel_y + 130
        cat_font = pygame.font.Font(None, 32)

        # Units category
        units_title = cat_font.render("UNITS & COMBAT", True, (255, 200, 100))
        self.screen.blit(units_title, (panel_x + 50, cat_y))

        # City category
        city_title = cat_font.render("CITIES & ECONOMY", True, (100, 255, 200))
        self.screen.blit(city_title, (panel_x + 750, cat_y))

        # Render tech boxes
        tech_font = pygame.font.Font(None, 20)
        cost_font = pygame.font.Font(None, 18)
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Define tech positions (manual layout for clarity)
        tech_positions = {
            # Units tree (left side)
            'scavenging_efficiency': (panel_x + 80, cat_y + 50),
            'scout_training': (panel_x + 80, cat_y + 140),
            'combat_training': (panel_x + 80, cat_y + 230),
            'tactical_medicine': (panel_x + 300, cat_y + 50),
            'rapid_response': (panel_x + 300, cat_y + 140),
            'armor_plating': (panel_x + 300, cat_y + 230),
            'advanced_weaponry': (panel_x + 300, cat_y + 320),
            'super_soldier_program': (panel_x + 520, cat_y + 320),

            # City tree (right side)
            'fortification': (panel_x + 780, cat_y + 50),
            'advanced_farming': (panel_x + 780, cat_y + 140),
            'industrial_workshops': (panel_x + 780, cat_y + 230),
            'basic_medicine': (panel_x + 780, cat_y + 320),
            'research_documentation': (panel_x + 1000, cat_y + 50),
            'quick_start': (panel_x + 1000, cat_y + 140),
            'watchtower': (panel_x + 1000, cat_y + 230),
            'cure_research': (panel_x + 1000, cat_y + 320),
            'automated_defenses': (panel_x + 1000, cat_y + 410),
            'helicopter_transport': (panel_x + 1000, cat_y + 500),
        }

        # Draw prerequisite lines first
        for tech_id, pos in tech_positions.items():
            tech = TECH_TREE[tech_id]
            for prereq in tech['prerequisites']:
                if prereq in tech_positions:
                    prereq_pos = tech_positions[prereq]
                    # Draw line from prereq to tech
                    start_x = prereq_pos[0] + 100  # Right edge of prereq box
                    start_y = prereq_pos[1] + 20   # Middle of prereq box
                    end_x = pos[0]                 # Left edge of tech box
                    end_y = pos[1] + 20            # Middle of tech box
                    pygame.draw.line(self.screen, (80, 80, 100), (start_x, start_y), (end_x, end_y), 2)

        # Draw tech boxes
        for tech_id, pos in tech_positions.items():
            tech = TECH_TREE[tech_id]
            box_width = 200
            box_height = 70

            # Determine tech state
            is_researched = tech_id in self.game_state.researched_techs
            can_afford = can_research(tech_id, self.game_state.researched_techs)
            tech_cost = get_tech_cost(tech_id, self.game_state.researched_techs)
            has_points = self.game_state.tech_points >= tech_cost

            # Check if mouse is hovering
            is_hovering = (pos[0] <= mouse_x <= pos[0] + box_width and
                          pos[1] <= mouse_y <= pos[1] + box_height)

            # Set colors based on state
            if is_researched:
                box_color = (50, 100, 50)
                border_color = (100, 200, 100)
                text_color = (200, 255, 200)
            elif can_afford and has_points:
                box_color = (70, 70, 100) if not is_hovering else (90, 90, 130)
                border_color = (150, 200, 255)
                text_color = (255, 255, 255)
            elif can_afford:
                box_color = (60, 60, 80)
                border_color = (120, 120, 150)
                text_color = (200, 200, 200)
            else:
                box_color = (40, 40, 50)
                border_color = (80, 80, 90)
                text_color = (120, 120, 130)

            # Draw box
            pygame.draw.rect(self.screen, box_color, (pos[0], pos[1], box_width, box_height))
            pygame.draw.rect(self.screen, border_color, (pos[0], pos[1], box_width, box_height), 2)

            # Draw tech name
            name_text = tech_font.render(tech['name'], True, text_color)
            name_rect = name_text.get_rect(center=(pos[0] + box_width // 2, pos[1] + 18))
            self.screen.blit(name_text, name_rect)

            # Draw cost
            cost_text = cost_font.render(f"Cost: {tech_cost} pts", True, text_color)
            cost_rect = cost_text.get_rect(center=(pos[0] + box_width // 2, pos[1] + 38))
            self.screen.blit(cost_text, cost_rect)

            # Draw status
            if is_researched:
                status_text = cost_font.render("✓ RESEARCHED", True, (150, 255, 150))
            elif can_afford and has_points:
                status_text = cost_font.render("Click to Research", True, (255, 255, 150))
            elif can_afford:
                status_text = cost_font.render("Need points", True, (255, 150, 100))
            else:
                status_text = cost_font.render("Locked", True, (150, 150, 150))

            status_rect = status_text.get_rect(center=(pos[0] + box_width // 2, pos[1] + 55))
            self.screen.blit(status_text, status_rect)

            # Store position for click detection
            if not hasattr(self, 'tech_positions'):
                self.tech_positions = {}
            self.tech_positions[tech_id] = (pos[0], pos[1], box_width, box_height)

            # Draw tooltip on hover
            if is_hovering:
                self.hovered_tech = tech_id

        # Draw tooltip for hovered tech
        if hasattr(self, 'hovered_tech') and self.hovered_tech:
            tech_id = self.hovered_tech
            if tech_id in tech_positions:
                tech = TECH_TREE[tech_id]
                tooltip_width = 450
                tooltip_height = 80

                # Position tooltip to the right of the mouse, but keep it on screen
                tooltip_x = min(mouse_x + 20, self.screen_width - tooltip_width - 10)
                tooltip_y = min(mouse_y + 10, self.screen_height - tooltip_height - 10)

                # Draw tooltip background
                pygame.draw.rect(self.screen, (20, 25, 35), (tooltip_x, tooltip_y, tooltip_width, tooltip_height))
                pygame.draw.rect(self.screen, (150, 200, 255), (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 3)

                # Draw tech name
                tooltip_font = pygame.font.Font(None, 24)
                name_text = tooltip_font.render(tech['name'], True, (255, 255, 150))
                self.screen.blit(name_text, (tooltip_x + 10, tooltip_y + 10))

                # Draw description (word wrap)
                desc_font = pygame.font.Font(None, 20)
                desc_text = tech['description']
                words = desc_text.split(' ')
                lines = []
                current_line = ''

                for word in words:
                    test_line = current_line + word + ' '
                    if desc_font.size(test_line)[0] < tooltip_width - 20:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word + ' '
                if current_line:
                    lines.append(current_line)

                for i, line in enumerate(lines[:2]):  # Max 2 lines
                    desc_surface = desc_font.render(line.strip(), True, (220, 220, 255))
                    self.screen.blit(desc_surface, (tooltip_x + 10, tooltip_y + 38 + i * 20))

        # Reset hovered tech for next frame
        self.hovered_tech = None

        # Instructions
        instructions_font = pygame.font.Font(None, 24)
        instructions = instructions_font.render("Hover for details  |  Click available tech to research  |  Press TAB or ESC to close", True, (200, 200, 200))
        instructions_rect = instructions.get_rect(center=(self.screen_width // 2, panel_y + panel_height - 30))
        self.screen.blit(instructions, instructions_rect)

    def render_helicopter_menu(self):
        """Render the helicopter transport menu"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Instruction panel
        panel_width = 600
        panel_height = 150
        panel_x = self.screen_width // 2 - panel_width // 2
        panel_y = 50

        pygame.draw.rect(self.screen, (20, 40, 60), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, (100, 150, 200), (panel_x, panel_y, panel_width, panel_height), 3)

        # Title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("🚁 Helicopter Transport", True, (150, 200, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, panel_y + 35))
        self.screen.blit(title, title_rect)

        # Instructions
        inst_font = pygame.font.Font(None, 24)
        inst1 = inst_font.render("Click on any city to teleport", True, (200, 220, 255))
        inst1_rect = inst1.get_rect(center=(self.screen_width // 2, panel_y + 80))
        self.screen.blit(inst1, inst1_rect)

        inst2 = inst_font.render("Press P or ESC to cancel", True, (180, 200, 230))
        inst2_rect = inst2.get_rect(center=(self.screen_width // 2, panel_y + 110))
        self.screen.blit(inst2, inst2_rect)

        # Highlight all cities on the map
        for city in self.game_state.cities:
            # Convert tile coordinates to screen coordinates
            screen_x = city.x * self.renderer.tile_size - self.renderer.camera_x + self.renderer.tile_size // 2
            screen_y = city.y * self.renderer.tile_size - self.renderer.camera_y + self.renderer.tile_size // 2

            # Check if city is visible on screen
            if 0 <= screen_x < self.screen_width and 0 <= screen_y < self.screen_height:
                # Draw pulsing highlight circle
                import math
                pulse = abs(math.sin(pygame.time.get_ticks() / 300.0))
                radius = int(20 + pulse * 10)
                pygame.draw.circle(self.screen, (150, 200, 255, 180), (screen_x, screen_y), radius, 3)

                # Draw city name
                name_font = pygame.font.Font(None, 20)
                name_text = name_font.render(city.name, True, (200, 230, 255))
                name_rect = name_text.get_rect(center=(screen_x, screen_y - radius - 10))

                # Draw background for text
                bg_rect = name_rect.inflate(10, 4)
                pygame.draw.rect(self.screen, (20, 40, 60), bg_rect)
                pygame.draw.rect(self.screen, (100, 150, 200), bg_rect, 1)

                self.screen.blit(name_text, name_rect)

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
        score_rect = score_text.get_rect(center=(self.screen_width // 2, menu_y + 180))
        self.screen.blit(score_text, score_rect)

        # Difficulty display
        diff_font = pygame.font.Font(None, 28)
        diff_color = {'easy': (50, 200, 50), 'medium': (200, 200, 50), 'hard': (200, 50, 50)}.get(self.game_state.difficulty, (200, 200, 200))
        diff_text = diff_font.render(f"Difficulty: {self.game_state.difficulty.upper()}", True, diff_color)
        diff_rect = diff_text.get_rect(center=(self.screen_width // 2, menu_y + 215))
        self.screen.blit(diff_text, diff_rect)

        # Cure leaderboard title
        lb_title_font = pygame.font.Font(None, 32)
        lb_title = lb_title_font.render(f"Cure Leaderboard - {self.game_state.difficulty.capitalize()}", True, (255, 215, 0))
        lb_title_rect = lb_title.get_rect(center=(self.screen_width // 2, menu_y + 250))
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
