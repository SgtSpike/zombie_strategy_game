import pygame
import os
from map_generator import TileType

class Renderer:
    def __init__(self, screen_width, screen_height, tile_size):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size
        self.camera_x = 0
        self.camera_y = 0

        # Define colors for each tile type
        self.tile_colors = {
            TileType.GRASS: (100, 180, 100),
            TileType.ROAD: (80, 80, 80),
            TileType.BUILDING_RUINED: (120, 60, 60),
            TileType.BUILDING_INTACT: (150, 150, 150),
            TileType.RUBBLE: (90, 90, 80),
            TileType.FOREST: (34, 139, 34),
            TileType.WATER: (65, 105, 225),
            TileType.RESEARCH_LAB: (200, 150, 255)  # Purple/pink for research lab
        }

        # Unit colors (fallback if sprites don't load)
        self.unit_colors = {
            'survivor': (0, 200, 255),      # Blue
            'scout': (100, 255, 100),       # Green
            'soldier': (255, 150, 0),       # Orange
            'medic': (255, 255, 255),       # White
            'zombie': (200, 50, 50),        # Red
            'super_zombie': (150, 0, 0),    # Dark red
            'builder': (255, 200, 0)        # Yellow
        }

        # Load unit sprites
        self.unit_sprites = self._load_sprites()
        # Load terrain sprites
        self.terrain_sprites = self._load_terrain_sprites()

    def _load_sprites(self):
        """Load unit sprites from PNG files"""
        sprites = {}
        sprite_dir = os.path.join(os.path.dirname(__file__), 'sprites')

        sprite_files = {
            'survivor': 'survivor.png',
            'scout': 'scout.png',
            'soldier': 'soldier.png',
            'medic': 'medic.png',
            'zombie': 'zombie.png',
            'super_zombie': 'super_zombie.png'
        }

        for unit_type, filename in sprite_files.items():
            filepath = os.path.join(sprite_dir, filename)
            try:
                sprite = pygame.image.load(filepath).convert_alpha()
                # Scale sprites to tile size (except super_zombie which is 2x2)
                if unit_type == 'super_zombie':
                    scaled_sprite = pygame.transform.scale(sprite, (self.tile_size * 2, self.tile_size * 2))
                else:
                    scaled_sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
                sprites[unit_type] = scaled_sprite
                print(f"Loaded sprite: {unit_type}")
            except Exception as e:
                print(f"Warning: Could not load sprite for {unit_type}: {e}")
                sprites[unit_type] = None

        return sprites

    def _load_terrain_sprites(self):
        """Load terrain and building sprites from PNG files"""
        sprites = {}
        sprite_dir = os.path.join(os.path.dirname(__file__), 'sprites')

        sprite_files = {
            'city': 'city.png',
            'research_lab': 'research_lab.png',
            'road': 'road.png',
            'rubble': 'rubble.png',
            'building_ruined': 'building_ruined.png',
            'building_intact': 'building_intact.png'
        }

        for terrain_type, filename in sprite_files.items():
            filepath = os.path.join(sprite_dir, filename)
            try:
                sprite = pygame.image.load(filepath).convert_alpha()
                # Scale sprites to tile size
                scaled_sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
                sprites[terrain_type] = scaled_sprite
                print(f"Loaded terrain sprite: {terrain_type}")
            except Exception as e:
                print(f"Warning: Could not load terrain sprite for {terrain_type}: {e}")
                sprites[terrain_type] = None

        return sprites

    def render(self, screen, game_state, selected_unit=None, selected_city=None, selected_tile=None, hovered_tile=None, building_placement_mode=None, debug_reveal_map=False, game_instance=None):
        """Render the game world"""
        screen.fill((0, 0, 0))

        # Calculate visible tiles
        start_col = max(0, self.camera_x // self.tile_size)
        end_col = min(len(game_state.map_grid[0]), (self.camera_x + self.screen_width) // self.tile_size + 1)
        start_row = max(0, self.camera_y // self.tile_size)
        end_row = min(len(game_state.map_grid), (self.camera_y + self.screen_height) // self.tile_size + 1)

        # Render tiles
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                x = col * self.tile_size - self.camera_x
                y = row * self.tile_size - self.camera_y

                # Check fog of war status (debug mode reveals all)
                is_visible = game_state.visible[row][col] or debug_reveal_map
                is_explored = game_state.explored[row][col] or debug_reveal_map

                if is_explored:
                    # Show terrain for explored tiles
                    tile_type = game_state.map_grid[row][col]

                    # Map tile types to sprite names
                    tile_sprite_map = {
                        TileType.ROAD: 'road',
                        TileType.BUILDING_RUINED: 'building_ruined',
                        TileType.BUILDING_INTACT: 'building_intact',
                        TileType.RUBBLE: 'rubble',
                        TileType.RESEARCH_LAB: 'research_lab'
                    }

                    # Try to use sprite if available, otherwise use colored rectangle
                    sprite_name = tile_sprite_map.get(tile_type)
                    sprite = self.terrain_sprites.get(sprite_name) if sprite_name else None

                    if sprite and is_visible:
                        # Special handling for roads - rotate based on orientation
                        if tile_type == TileType.ROAD:
                            # Check adjacent tiles to determine orientation
                            is_horizontal = False
                            # Check left and right neighbors
                            if col > 0 and col < len(game_state.map_grid[0]) - 1:
                                left_tile = game_state.map_grid[row][col - 1]
                                right_tile = game_state.map_grid[row][col + 1]
                                # If neighboring tiles horizontally are roads, this is a horizontal road
                                if left_tile == TileType.ROAD or right_tile == TileType.ROAD:
                                    # Also check vertically to see if this is a crossroads
                                    top_tile = game_state.map_grid[row - 1][col] if row > 0 else None
                                    bottom_tile = game_state.map_grid[row + 1][col] if row < len(game_state.map_grid) - 1 else None
                                    # If there are no vertical road connections, it's purely horizontal
                                    if top_tile != TileType.ROAD and bottom_tile != TileType.ROAD:
                                        is_horizontal = True

                            if is_horizontal:
                                rotated_sprite = pygame.transform.rotate(sprite, 90)
                                screen.blit(rotated_sprite, (x, y))
                            else:
                                screen.blit(sprite, (x, y))
                        else:
                            # Draw sprite at full brightness
                            screen.blit(sprite, (x, y))
                    elif sprite and not is_visible:
                        # Draw darkened sprite for fog of war
                        if tile_type == TileType.ROAD:
                            # Apply same rotation logic for darkened roads
                            is_horizontal = False
                            if col > 0 and col < len(game_state.map_grid[0]) - 1:
                                left_tile = game_state.map_grid[row][col - 1]
                                right_tile = game_state.map_grid[row][col + 1]
                                if left_tile == TileType.ROAD or right_tile == TileType.ROAD:
                                    top_tile = game_state.map_grid[row - 1][col] if row > 0 else None
                                    bottom_tile = game_state.map_grid[row + 1][col] if row < len(game_state.map_grid) - 1 else None
                                    if top_tile != TileType.ROAD and bottom_tile != TileType.ROAD:
                                        is_horizontal = True

                            if is_horizontal:
                                darkened = pygame.transform.rotate(sprite, 90)
                            else:
                                darkened = sprite.copy()
                            darkened.fill((128, 128, 128, 0), special_flags=pygame.BLEND_MULT)
                            screen.blit(darkened, (x, y))
                        else:
                            darkened = sprite.copy()
                            darkened.fill((128, 128, 128, 0), special_flags=pygame.BLEND_MULT)
                            screen.blit(darkened, (x, y))
                    else:
                        # Fallback to colored rectangle for grass, forest, water
                        color = self.tile_colors.get(tile_type, (100, 100, 100))

                        # Darken if not currently visible
                        if not is_visible:
                            color = tuple(int(c * 0.5) for c in color)

                        pygame.draw.rect(screen, color, (x, y, self.tile_size, self.tile_size))

                    # Draw grid lines
                    pygame.draw.rect(screen, (50, 50, 50), (x, y, self.tile_size, self.tile_size), 1)

                    # Only draw resource indicators on visible tiles
                    if is_visible and (col, row) in game_state.resources:
                        pygame.draw.circle(screen, (255, 215, 0),
                                         (x + self.tile_size // 2, y + self.tile_size // 2),
                                         5)
                else:
                    # Unexplored - pure black
                    pygame.draw.rect(screen, (0, 0, 0), (x, y, self.tile_size, self.tile_size))
                    pygame.draw.rect(screen, (30, 30, 30), (x, y, self.tile_size, self.tile_size), 1)

        # Highlight selected tile
        if selected_tile and not building_placement_mode:
            tile_x, tile_y = selected_tile
            if game_state.explored[tile_y][tile_x]:
                x = tile_x * self.tile_size - self.camera_x
                y = tile_y * self.tile_size - self.camera_y
                # Draw bright border around selected tile
                pygame.draw.rect(screen, (255, 255, 0), (x, y, self.tile_size, self.tile_size), 3)

        # Highlight hovered tile during building placement
        if hovered_tile and building_placement_mode and building_placement_mode not in ['survivor', 'scout', 'soldier', 'medic', 'upgrade']:
            tile_x, tile_y = hovered_tile
            if 0 <= tile_y < len(game_state.explored) and 0 <= tile_x < len(game_state.explored[0]):
                if game_state.explored[tile_y][tile_x]:
                    x = tile_x * self.tile_size - self.camera_x
                    y = tile_y * self.tile_size - self.camera_y
                    # Draw semi-transparent preview border
                    pygame.draw.rect(screen, (100, 255, 100), (x, y, self.tile_size, self.tile_size), 2)

        # Render placed buildings
        for city in game_state.cities:
            for (bx, by), building_info in city.building_locations.items():
                if game_state.visible[by][bx]:
                    x = bx * self.tile_size - self.camera_x
                    y = by * self.tile_size - self.camera_y

                    # Different colors for different buildings
                    building_colors = {
                        'farm': (100, 200, 100),
                        'workshop': (150, 150, 150),
                        'hospital': (200, 100, 100),
                        'wall': (80, 80, 80),
                        'dock': (100, 150, 200)
                    }
                    color = building_colors.get(building_info['type'], (150, 150, 150))
                    pygame.draw.rect(screen, color, (x, y, self.tile_size, self.tile_size))
                    pygame.draw.rect(screen, (255, 255, 255), (x, y, self.tile_size, self.tile_size), 2)

                    # Draw building initial
                    small_font = pygame.font.Font(None, 24)
                    initial = building_info['type'][0].upper()
                    text = small_font.render(initial, True, (255, 255, 255))
                    text_rect = text.get_rect(center=(x + self.tile_size//2, y + self.tile_size//2))
                    screen.blit(text, text_rect)

                    # Draw building level in top-right corner
                    level = building_info.get('level', 1)
                    if level > 1:
                        level_font = pygame.font.Font(None, 18)
                        level_text = level_font.render(f"L{level}", True, (255, 255, 0))
                        screen.blit(level_text, (x + self.tile_size - 18, y + 2))

                    # Draw health bar if building is damaged
                    building_health = building_info.get('health', 20)
                    building_max_health = building_info.get('max_health', 20)
                    if building_health < building_max_health:
                        bar_width = self.tile_size
                        bar_height = 4
                        bar_x = x
                        bar_y = y + self.tile_size + 2

                        # Background (red)
                        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))

                        # Foreground (green) - proportional to health
                        health_ratio = building_health / building_max_health
                        filled_width = int(bar_width * health_ratio)
                        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, filled_width, bar_height))

        # Render cities (only if visible)
        for city in game_state.cities:
            if game_state.visible[city.y][city.x]:
                x = city.x * self.tile_size - self.camera_x
                y = city.y * self.tile_size - self.camera_y

                # Try to use city sprite, fallback to colored rectangle
                city_sprite = self.terrain_sprites.get('city')
                if city_sprite:
                    screen.blit(city_sprite, (x, y))
                else:
                    pygame.draw.rect(screen, (255, 215, 0), (x, y, self.tile_size, self.tile_size))

                # Highlight selected city
                if selected_city == city:
                    pygame.draw.rect(screen, (255, 255, 0), (x, y, self.tile_size, self.tile_size), 4)
                else:
                    pygame.draw.rect(screen, (200, 180, 0), (x, y, self.tile_size, self.tile_size), 3)

                # Draw city name
                font = pygame.font.Font(None, 20)
                text = font.render(city.name, True, (255, 255, 255))
                screen.blit(text, (x + 2, y - 15))

                # Draw health bar if city is damaged
                if city.health < city.max_health:
                    bar_width = self.tile_size
                    bar_height = 4
                    bar_x = x
                    bar_y = y + self.tile_size + 2

                    # Background (red)
                    pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))

                    # Foreground (green) - proportional to health
                    health_ratio = city.health / city.max_health
                    filled_width = int(bar_width * health_ratio)
                    pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, filled_width, bar_height))

        # Render units (only if visible or in debug mode)
        for unit in game_state.units:
            # For multi-tile units, check if ANY tile is visible
            unit_size = getattr(unit, 'size', 1)
            is_visible = False

            if debug_reveal_map or unit.team == 'player':
                is_visible = True
            else:
                # Check all tiles the unit occupies
                for dy in range(unit_size):
                    for dx in range(unit_size):
                        check_x = unit.x + dx
                        check_y = unit.y + dy
                        if (0 <= check_y < len(game_state.visible) and
                            0 <= check_x < len(game_state.visible[0]) and
                            game_state.visible[check_y][check_x]):
                            is_visible = True
                            break
                    if is_visible:
                        break

            if is_visible:
                # Get render position (handles animation if active)
                if game_instance:
                    render_x, render_y = game_instance.get_unit_render_position(unit)
                else:
                    render_x, render_y = unit.x, unit.y

                x = render_x * self.tile_size - self.camera_x
                y = render_y * self.tile_size - self.camera_y

                # Determine size of unit
                unit_size = getattr(unit, 'size', 1)

                # Try to use sprite, fallback to colored circle
                sprite = self.unit_sprites.get(unit.unit_type)

                if unit_size == 1:
                    # Draw normal 1x1 unit
                    if sprite:
                        # Draw sprite
                        screen.blit(sprite, (x, y))
                    else:
                        # Fallback to colored circle
                        color = self.unit_colors.get(unit.unit_type, (255, 255, 255))
                        pygame.draw.circle(screen, color,
                                         (x + self.tile_size // 2, y + self.tile_size // 2),
                                         self.tile_size // 3)

                    # Draw selection highlight
                    if selected_unit == unit:
                        pygame.draw.rect(screen, (255, 255, 0), (x, y, self.tile_size, self.tile_size), 3)

                    # Draw health bar
                    health_bar_width = self.tile_size - 4
                    health_ratio = unit.health / unit.max_health
                    pygame.draw.rect(screen, (255, 0, 0),
                                   (x + 2, y + self.tile_size - 6, health_bar_width, 4))
                    pygame.draw.rect(screen, (0, 255, 0),
                                   (x + 2, y + self.tile_size - 6, int(health_bar_width * health_ratio), 4))
                else:
                    # Draw 2x2 super zombie
                    rect_width = self.tile_size * unit_size
                    rect_height = self.tile_size * unit_size

                    if sprite:
                        # Draw sprite
                        screen.blit(sprite, (x, y))
                    else:
                        # Fallback to colored rectangle
                        color = self.unit_colors.get(unit.unit_type, (255, 255, 255))
                        pygame.draw.rect(screen, color, (x, y, rect_width, rect_height))
                        pygame.draw.rect(screen, (255, 255, 255), (x, y, rect_width, rect_height), 3)

                        # Draw "SZ" text in center (only for fallback)
                        font = pygame.font.Font(None, 48)
                        text = font.render("SZ", True, (255, 255, 255))
                        text_rect = text.get_rect(center=(x + rect_width // 2, y + rect_height // 2))
                        screen.blit(text, text_rect)

                    # Draw selection highlight
                    if selected_unit == unit:
                        pygame.draw.rect(screen, (255, 255, 0), (x, y, rect_width, rect_height), 5)

                    # Draw health bar (wider for 2x2 unit)
                    health_bar_width = rect_width - 4
                    health_ratio = unit.health / unit.max_health
                    bar_y = y + rect_height + 2
                    pygame.draw.rect(screen, (255, 0, 0),
                                   (x + 2, bar_y, health_bar_width, 6))
                    pygame.draw.rect(screen, (0, 255, 0),
                                   (x + 2, bar_y, int(health_bar_width * health_ratio), 6))

                # Draw movement indicator for player units
                if unit.team == 'player' and unit.can_move():
                    # Draw a small green dot in the top-right corner
                    pygame.draw.circle(screen, (0, 255, 0),
                                     (x + self.tile_size - 6, y + 6),
                                     4)

                # Draw level indicator for all units with level > 1
                if unit.level > 1:
                    # Choose position based on unit size
                    if unit_size == 1:
                        level_x = x + 4
                        level_y = y + 4
                        font_size = 16
                    else:
                        # For 2x2 units, position in top-left
                        level_x = x + 6
                        level_y = y + 6
                        font_size = 24

                    # Background circle for visibility
                    circle_radius = 10 if unit_size == 1 else 15
                    pygame.draw.circle(screen, (0, 0, 0), (level_x + 8, level_y + 8), circle_radius)

                    # Level number with color coding
                    level_font = pygame.font.Font(None, font_size)
                    # Color based on level: white (2), yellow (3), orange (4+)
                    if unit.level == 2:
                        level_color = (255, 255, 255)  # White
                    elif unit.level == 3:
                        level_color = (255, 255, 0)  # Yellow
                    else:
                        level_color = (255, 128, 0)  # Orange

                    level_text = level_font.render(str(unit.level), True, level_color)
                    level_rect = level_text.get_rect(center=(level_x + 8, level_y + 8))
                    screen.blit(level_text, level_rect)

        # Render UI
        self.render_ui(screen, game_state, selected_unit, selected_city, selected_tile, hovered_tile, building_placement_mode)

        # Render mini-map
        self.render_minimap(screen, game_state)

    def render_minimap(self, screen, game_state):
        """Render a clickable mini-map in the bottom-right corner"""
        # Mini-map configuration
        minimap_size = 200  # Size of the mini-map (square)
        minimap_padding = 10
        minimap_x = self.screen_width - minimap_size - minimap_padding
        minimap_y = self.screen_height - minimap_size - minimap_padding

        # Store mini-map bounds for click detection
        self.minimap_bounds = (minimap_x, minimap_y, minimap_size, minimap_size)

        # Calculate scale factor
        map_width = len(game_state.map_grid[0])
        map_height = len(game_state.map_grid)
        scale_x = minimap_size / map_width
        scale_y = minimap_size / map_height

        # Draw background
        pygame.draw.rect(screen, (0, 0, 0), (minimap_x, minimap_y, minimap_size, minimap_size))
        pygame.draw.rect(screen, (100, 100, 100), (minimap_x, minimap_y, minimap_size, minimap_size), 2)

        # Draw explored terrain
        for row in range(map_height):
            for col in range(map_width):
                if game_state.explored[row][col]:
                    tile_type = game_state.map_grid[row][col]

                    # Simplified colors for mini-map
                    color = (50, 50, 50)  # Default dark gray
                    if tile_type == TileType.WATER:
                        color = (30, 50, 100)
                    elif tile_type == TileType.FOREST:
                        color = (20, 60, 20)
                    elif tile_type == TileType.RESEARCH_LAB:
                        color = (150, 100, 200)  # Purple for research lab
                    elif tile_type in [TileType.BUILDING_INTACT, TileType.BUILDING_RUINED]:
                        color = (80, 80, 80)

                    pixel_x = minimap_x + int(col * scale_x)
                    pixel_y = minimap_y + int(row * scale_y)
                    pixel_width = max(1, int(scale_x))
                    pixel_height = max(1, int(scale_y))

                    pygame.draw.rect(screen, color, (pixel_x, pixel_y, pixel_width, pixel_height))

        # Draw cities
        for city in game_state.cities:
            if game_state.explored[city.y][city.x]:
                pixel_x = minimap_x + int(city.x * scale_x)
                pixel_y = minimap_y + int(city.y * scale_y)
                pygame.draw.circle(screen, (255, 255, 0), (pixel_x, pixel_y), 3)

        # Draw research lab
        if game_state.research_lab_pos:
            lab_x, lab_y = game_state.research_lab_pos
            if game_state.explored[lab_y][lab_x]:
                pixel_x = minimap_x + int(lab_x * scale_x)
                pixel_y = minimap_y + int(lab_y * scale_y)
                pygame.draw.circle(screen, (200, 150, 255), (pixel_x, pixel_y), 4)

        # Draw units (player = blue, enemy = red)
        for unit in game_state.units:
            if game_state.visible[unit.y][unit.x]:
                pixel_x = minimap_x + int(unit.x * scale_x)
                pixel_y = minimap_y + int(unit.y * scale_y)
                color = (100, 200, 255) if unit.team == 'player' else (200, 50, 50)
                size = 2 if unit.size == 1 else 3  # Super zombies slightly larger
                pygame.draw.circle(screen, color, (pixel_x, pixel_y), size)

        # Draw camera viewport indicator
        tiles_visible_x = self.screen_width // self.tile_size
        tiles_visible_y = self.screen_height // self.tile_size
        viewport_start_x = self.camera_x // self.tile_size
        viewport_start_y = self.camera_y // self.tile_size

        viewport_pixel_x = minimap_x + int(viewport_start_x * scale_x)
        viewport_pixel_y = minimap_y + int(viewport_start_y * scale_y)
        viewport_pixel_w = int(tiles_visible_x * scale_x)
        viewport_pixel_h = int(tiles_visible_y * scale_y)

        pygame.draw.rect(screen, (255, 255, 255),
                        (viewport_pixel_x, viewport_pixel_y, viewport_pixel_w, viewport_pixel_h), 1)

        # Draw mini-map label
        label_font = pygame.font.Font(None, 18)
        label_text = label_font.render("Mini-Map (Click to Navigate)", True, (200, 200, 200))
        screen.blit(label_text, (minimap_x, minimap_y - 20))

    def is_click_on_minimap(self, mouse_x, mouse_y):
        """Check if a mouse click is within the mini-map bounds"""
        if not hasattr(self, 'minimap_bounds'):
            return False

        minimap_x, minimap_y, minimap_size, _ = self.minimap_bounds
        return (minimap_x <= mouse_x <= minimap_x + minimap_size and
                minimap_y <= mouse_y <= minimap_y + minimap_size)

    def minimap_click_to_world_coords(self, mouse_x, mouse_y, map_width, map_height):
        """Convert mini-map click coordinates to world tile coordinates"""
        if not hasattr(self, 'minimap_bounds'):
            return None

        minimap_x, minimap_y, minimap_size, _ = self.minimap_bounds

        # Calculate position within mini-map
        relative_x = mouse_x - minimap_x
        relative_y = mouse_y - minimap_y

        # Convert to world coordinates
        scale_x = minimap_size / map_width
        scale_y = minimap_size / map_height

        world_x = int(relative_x / scale_x)
        world_y = int(relative_y / scale_y)

        # Clamp to map bounds
        world_x = max(0, min(map_width - 1, world_x))
        world_y = max(0, min(map_height - 1, world_y))

        return (world_x, world_y)

    def center_camera_on_tile(self, tile_x, tile_y):
        """Center the camera on a specific tile"""
        # Calculate camera position to center on the tile
        tiles_visible_x = self.screen_width // self.tile_size
        tiles_visible_y = self.screen_height // self.tile_size

        # Center the camera
        self.camera_x = (tile_x * self.tile_size) - (tiles_visible_x * self.tile_size // 2)
        self.camera_y = (tile_y * self.tile_size) - (tiles_visible_y * self.tile_size // 2)

        # Clamp camera to prevent going off the map (will be done in main.py if needed)

    def get_tile_name(self, tile_type):
        """Convert TileType enum to readable name"""
        tile_names = {
            TileType.GRASS: "Grass",
            TileType.ROAD: "Road",
            TileType.BUILDING_RUINED: "Ruined Building",
            TileType.BUILDING_INTACT: "Intact Building",
            TileType.RUBBLE: "Rubble",
            TileType.FOREST: "Forest",
            TileType.WATER: "Water",
            TileType.RESEARCH_LAB: "Research Lab"
        }
        return tile_names.get(tile_type, "Unknown")

    def render_ui(self, screen, game_state, selected_unit, selected_city, selected_tile, hovered_tile=None, building_placement_mode=None):
        """Render UI elements"""
        font = pygame.font.Font(None, 24)

        # Prominent turn indicator with colored background
        turn_panel_width = 350
        turn_panel_height = 60
        turn_panel_x = 10
        turn_panel_y = 10

        # Different colors for player and enemy turns
        if game_state.current_team == 'player':
            bg_color = (20, 60, 20)  # Dark green for player
            border_color = (50, 200, 50)  # Bright green
            text_color = (100, 255, 100)  # Light green
        else:
            bg_color = (60, 20, 20)  # Dark red for enemy
            border_color = (200, 50, 50)  # Bright red
            text_color = (255, 100, 100)  # Light red

        # Draw turn panel
        pygame.draw.rect(screen, bg_color, (turn_panel_x, turn_panel_y, turn_panel_width, turn_panel_height))
        pygame.draw.rect(screen, border_color, (turn_panel_x, turn_panel_y, turn_panel_width, turn_panel_height), 3)

        # Turn counter and zombie count
        zombie_count = len([u for u in game_state.units if u.team == 'enemy' and u.unit_type == 'zombie'])

        # Large, prominent turn indicator
        turn_font = pygame.font.Font(None, 32)
        turn_text = turn_font.render(f"{game_state.current_team.upper()} TURN", True, text_color)
        screen.blit(turn_text, (turn_panel_x + 10, turn_panel_y + 8))

        # Turn number and zombie count below
        info_font = pygame.font.Font(None, 20)
        info_text = info_font.render(f"Turn {game_state.turn} | {zombie_count} Zombies", True, (220, 220, 220))
        screen.blit(info_text, (turn_panel_x + 10, turn_panel_y + 38))

        # Total resources across all units and cities (positioned to the right of turn panel)
        total_resources = game_state.get_total_resources()
        resources_text = f"Total Resources - Food: {total_resources['food']} | Materials: {total_resources['materials']} | Medicine: {total_resources['medicine']} | Cure: {total_resources.get('cure', 0)}"
        res_surface = font.render(resources_text, True, (255, 255, 255))
        screen.blit(res_surface, (turn_panel_x + turn_panel_width + 20, turn_panel_y + 20))  # To the right of turn panel

        # Selected unit info (positioned higher to avoid overlap with instructions)
        if selected_unit:
            # Unit info - properly spaced to avoid overlaps
            # Instructions can go up to screen_height - 136 (3 lines at -100, -118, -136)
            # So unit info needs to end before that, leaving at least 10px gap
            info_text = f"Unit: {selected_unit.unit_type} | HP: {selected_unit.health}/{selected_unit.max_health} | Attack: {selected_unit.attack_power} | Moves: {selected_unit.moves_remaining}/{selected_unit.max_moves}"
            info_surface = font.render(info_text, True, (255, 255, 255))
            screen.blit(info_surface, (10, self.screen_height - 215))

            # Unit level and XP - 25px spacing from above
            xp_text = f"Level: {selected_unit.level} | XP: {selected_unit.xp}/{selected_unit.xp_to_next_level}"
            xp_surface = font.render(xp_text, True, (255, 215, 0))
            screen.blit(xp_surface, (10, self.screen_height - 190))

            # Unit inventory - 25px spacing from above
            cure_count = selected_unit.inventory.get('cure', 0)
            inv_text = f"Carrying - Food: {selected_unit.inventory['food']} | Materials: {selected_unit.inventory['materials']} | Med: {selected_unit.inventory['medicine']} | Cure: {cure_count}"
            # Highlight cure in gold if carrying it
            inv_color = (255, 215, 0) if cure_count > 0 else (200, 200, 255)
            inv_surface = font.render(inv_text, True, inv_color)
            screen.blit(inv_surface, (10, self.screen_height - 165))

        # Selected city info and building menu
        if selected_city:
            panel_x = self.screen_width - 420
            panel_y = 80
            panel_width = 410
            panel_height = 350

            # Draw panel background
            pygame.draw.rect(screen, (40, 40, 40), (panel_x, panel_y, panel_width, panel_height))
            pygame.draw.rect(screen, (200, 200, 200), (panel_x, panel_y, panel_width, panel_height), 2)

            # City title
            title_font = pygame.font.Font(None, 28)
            title = title_font.render(f"{selected_city.name}", True, (255, 215, 0))
            screen.blit(title, (panel_x + 10, panel_y + 10))

            # City stats
            stats_font = pygame.font.Font(None, 20)
            stats = [
                f"Population: {selected_city.population} | Level: {selected_city.level}",
                f"City Resources - Food: {selected_city.resources['food']} | Materials: {selected_city.resources['materials']} | Med: {selected_city.resources['medicine']} | Cure: {selected_city.resources.get('cure', 0)}",
                f"Buildings: {', '.join(selected_city.buildings)}"
            ]
            for i, stat in enumerate(stats):
                stat_surface = stats_font.render(stat, True, (220, 220, 220))
                screen.blit(stat_surface, (panel_x + 10, panel_y + 45 + i * 22))

            # Production display
            production = selected_city.calculate_production()
            prod_font = pygame.font.Font(None, 20)
            prod_text = f"Production/turn: +{production['food']} food, +{production['materials']} materials, +{production['medicine']} medicine"
            prod_surface = prod_font.render(prod_text, True, (150, 255, 150))
            screen.blit(prod_surface, (panel_x + 10, panel_y + 112))

            # Building menu
            menu_font = pygame.font.Font(None, 22)
            menu_y = panel_y + 142
            menu_title = menu_font.render("Build:", True, (255, 255, 255))
            screen.blit(menu_title, (panel_x + 10, menu_y))

            help_small = pygame.font.Font(None, 16)
            help_text = help_small.render("Buildings use city resources | Units use city resources", True, (180, 180, 180))
            screen.blit(help_text, (panel_x + 10, menu_y + 22))

            buildings = [
                ("1: Farm", "30 mat (place on tile)"),
                ("2: Workshop", "50 mat (place on tile)"),
                ("3: Hospital", "40 mat (place on tile)"),
                ("4: Wall", "5 mat (place on tile)"),
                ("5: Dock", "40 mat (place on water)"),
                ("6: Survivor", "20 food, 10 mat"),
                ("7: Scout", "15 food, 5 mat (fast)"),
                ("8: Soldier", "30 food, 20 mat (strong)"),
                ("9: Medic", "25 food, 15 mat, 10 med"),
                ("U: Upgrade", "Click building to upgrade")
            ]

            # Add cure manufacturing option if city has hospital and the cure
            if selected_city and 'hospital' in selected_city.buildings and selected_city.resources.get('cure', 0) > 0:
                buildings.append(("C: MANUFACTURE CURE", "500 food, 500 mat, 200 med, 1 cure"))

            option_font = pygame.font.Font(None, 16)
            for i, (name, cost) in enumerate(buildings):
                # Highlight cure option in gold
                if "MANUFACTURE CURE" in name:
                    option_text = option_font.render(f"{name} - {cost}", True, (255, 215, 0))
                else:
                    option_text = option_font.render(f"{name} - {cost}", True, (180, 255, 180))
                screen.blit(option_text, (panel_x + 15, menu_y + 45 + i * 20))

        # Instructions
        help_font = pygame.font.Font(None, 17)
        if selected_city:
            instructions = [
                "1-5: Buildings (click tile) | 6-9: Recruit units | U: Upgrade (click building) | ESC: Cancel",
                "T/G: Transfer resources | E: End turn"
            ]
        else:
            instructions = [
                "WASD: Camera | Click: Select unit | Shift+Click: Select city | E: End turn",
                "F: Found city (3+ tiles apart) | R: Scavenge | T/G: Transfer | H: Heal (medic)",
                "Ctrl+S: Save | Ctrl+L: Load | ESC: Quit"
            ]
        for i, instruction in enumerate(instructions):
            help_surface = help_font.render(instruction, True, (200, 200, 200))
            screen.blit(help_surface, (10, self.screen_height - 100 - i * 18))

        # Tile information panel (use hovered tile during building placement or upgrade, otherwise selected tile)
        display_tile = hovered_tile if (hovered_tile and building_placement_mode and building_placement_mode not in ['survivor', 'scout', 'soldier', 'medic']) else selected_tile
        if display_tile:
            tile_x, tile_y = display_tile
            # Only show if tile is explored
            if 0 <= tile_y < len(game_state.explored) and 0 <= tile_x < len(game_state.explored[0]) and game_state.explored[tile_y][tile_x]:
                panel_x = 10
                panel_y = 75
                panel_width = 350
                panel_height = 120

                # Draw panel background
                pygame.draw.rect(screen, (30, 30, 30), (panel_x, panel_y, panel_width, panel_height))
                pygame.draw.rect(screen, (150, 150, 150), (panel_x, panel_y, panel_width, panel_height), 2)

                # Get tile type
                tile_type = game_state.map_grid[tile_y][tile_x]
                tile_name = self.get_tile_name(tile_type)

                # Tile title
                info_font = pygame.font.Font(None, 22)
                title = info_font.render(f"Selected Tile: {tile_name} ({tile_x}, {tile_y})", True, (255, 255, 100))
                screen.blit(title, (panel_x + 10, panel_y + 10))

                # Movement cost
                movement_cost = 0.5 if tile_type == TileType.ROAD else 1.0
                move_text = info_font.render(f"Movement Cost: {movement_cost}", True, (200, 200, 200))
                screen.blit(move_text, (panel_x + 10, panel_y + 35))

                # Building bonuses
                bonus_font = pygame.font.Font(None, 20)
                y_offset = 60

                # Check for farm bonuses
                if tile_type == TileType.GRASS:
                    farm_bonus = bonus_font.render("Farm: 6 food", True, (100, 255, 100))
                    screen.blit(farm_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20
                elif tile_type == TileType.FOREST:
                    farm_bonus = bonus_font.render("Farm: 3 food", True, (150, 200, 150))
                    screen.blit(farm_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20
                else:
                    farm_bonus = bonus_font.render("Farm: 0 food (poor terrain)", True, (180, 180, 180))
                    screen.blit(farm_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20

                # Check for workshop bonuses
                if tile_type == TileType.BUILDING_INTACT:
                    workshop_bonus = bonus_font.render("Workshop: 8 materials", True, (100, 255, 100))
                    screen.blit(workshop_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20
                elif tile_type in [TileType.ROAD, TileType.BUILDING_RUINED]:
                    workshop_bonus = bonus_font.render("Workshop: 4 materials", True, (150, 200, 150))
                    screen.blit(workshop_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20
                elif tile_type == TileType.RUBBLE:
                    workshop_bonus = bonus_font.render("Workshop: 2 materials", True, (200, 200, 150))
                    screen.blit(workshop_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20
                else:
                    workshop_bonus = bonus_font.render("Workshop: 0 materials", True, (180, 180, 180))
                    screen.blit(workshop_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20

                # Check for hospital bonuses
                if tile_type == TileType.BUILDING_INTACT:
                    hospital_bonus = bonus_font.render("Hospital: 6 medicine", True, (100, 255, 100))
                    screen.blit(hospital_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20
                else:
                    hospital_bonus = bonus_font.render("Hospital: 2 medicine", True, (180, 180, 180))
                    screen.blit(hospital_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20

                # Check for dock
                if tile_type == TileType.WATER:
                    dock_bonus = bonus_font.render("Dock: 12 food", True, (100, 255, 255))
                    screen.blit(dock_bonus, (panel_x + 10, panel_y + y_offset))
                    y_offset += 20

                # Show building placement preview if in placement mode
                if building_placement_mode and building_placement_mode not in ['survivor', 'scout', 'soldier', 'medic', 'upgrade'] and display_tile == hovered_tile:
                    preview_font = pygame.font.Font(None, 22)
                    preview_building = building_placement_mode

                    # Calculate what production would be if built here
                    if preview_building == 'farm':
                        prod = 0
                        if tile_type == TileType.GRASS:
                            prod = 6
                        elif tile_type == TileType.FOREST:
                            prod = 3
                        if prod > 0:
                            preview_text = preview_font.render(f"PREVIEW: {preview_building.capitalize()} would produce {prod} food/turn", True, (100, 255, 100))
                        else:
                            preview_text = preview_font.render(f"PREVIEW: {preview_building.capitalize()} - poor location (0 food)", True, (255, 100, 100))
                        screen.blit(preview_text, (panel_x + 10, panel_y + y_offset))
                    elif preview_building == 'dock':
                        if tile_type == TileType.WATER:
                            preview_text = preview_font.render(f"PREVIEW: {preview_building.capitalize()} would produce 12 food/turn", True, (100, 255, 100))
                        else:
                            preview_text = preview_font.render(f"PREVIEW: Docks must be on water!", True, (255, 100, 100))
                        screen.blit(preview_text, (panel_x + 10, panel_y + y_offset))
                    elif preview_building == 'workshop':
                        prod = 0
                        if tile_type == TileType.RUBBLE:
                            prod = 2
                        elif tile_type in [TileType.BUILDING_RUINED, TileType.ROAD]:
                            prod = 4
                        elif tile_type == TileType.BUILDING_INTACT:
                            prod = 8
                        if prod > 0:
                            preview_text = preview_font.render(f"PREVIEW: {preview_building.capitalize()} would produce {prod} materials/turn", True, (100, 255, 100))
                        else:
                            preview_text = preview_font.render(f"PREVIEW: {preview_building.capitalize()} - poor location (0 materials)", True, (255, 100, 100))
                        screen.blit(preview_text, (panel_x + 10, panel_y + y_offset))
                    elif preview_building == 'hospital':
                        prod = 2
                        if tile_type == TileType.BUILDING_INTACT:
                            prod += 4
                        preview_text = preview_font.render(f"PREVIEW: {preview_building.capitalize()} would produce {prod} medicine/turn", True, (100, 255, 100))
                        screen.blit(preview_text, (panel_x + 10, panel_y + y_offset))
                    elif preview_building == 'wall':
                        preview_text = preview_font.render(f"PREVIEW: {preview_building.capitalize()} (defensive structure)", True, (100, 255, 100))
                        screen.blit(preview_text, (panel_x + 10, panel_y + y_offset))

                # Show upgrade preview in upgrade mode
                elif building_placement_mode == 'upgrade' and display_tile == hovered_tile:
                    building = game_state.get_building_at(tile_x, tile_y)
                    if building:
                        building_type = building['type']
                        terrain = building['terrain']
                        current_level = building.get('level', 1)
                        preview_font = pygame.font.Font(None, 22)

                        if current_level < 3:
                            next_level = current_level + 1
                            upgrade_cost = 20 * current_level  # Cost increases per level

                            # Calculate current and next production
                            if building_type == 'farm':
                                current_prod = 0
                                if terrain == TileType.GRASS:
                                    current_prod = 6
                                elif terrain == TileType.FOREST:
                                    current_prod = 3
                                current_prod *= current_level
                                next_prod = current_prod // current_level * next_level if current_level > 0 else 0

                                upgrade_text = preview_font.render(f"UPGRADE: {building_type.capitalize()} L{current_level} → L{next_level}", True, (100, 255, 255))
                                screen.blit(upgrade_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                cost_text = preview_font.render(f"Cost: {upgrade_cost} materials", True, (255, 200, 100))
                                screen.blit(cost_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                prod_text = preview_font.render(f"Production: {current_prod} → {next_prod} food/turn", True, (100, 255, 100))
                                screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))

                            elif building_type == 'dock':
                                current_prod = 12 * current_level
                                next_prod = 12 * next_level

                                upgrade_text = preview_font.render(f"UPGRADE: {building_type.capitalize()} L{current_level} → L{next_level}", True, (100, 255, 255))
                                screen.blit(upgrade_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                cost_text = preview_font.render(f"Cost: {upgrade_cost} materials", True, (255, 200, 100))
                                screen.blit(cost_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                prod_text = preview_font.render(f"Production: {current_prod} → {next_prod} food/turn", True, (100, 255, 100))
                                screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))

                            elif building_type == 'workshop':
                                current_prod = 0
                                if terrain == TileType.RUBBLE:
                                    current_prod = 2
                                elif terrain in [TileType.BUILDING_RUINED, TileType.ROAD]:
                                    current_prod = 4
                                elif terrain == TileType.BUILDING_INTACT:
                                    current_prod = 8
                                current_prod *= current_level
                                next_prod = current_prod // current_level * next_level if current_level > 0 else 0

                                upgrade_text = preview_font.render(f"UPGRADE: {building_type.capitalize()} L{current_level} → L{next_level}", True, (100, 255, 255))
                                screen.blit(upgrade_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                cost_text = preview_font.render(f"Cost: {upgrade_cost} materials", True, (255, 200, 100))
                                screen.blit(cost_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                prod_text = preview_font.render(f"Production: {current_prod} → {next_prod} materials/turn", True, (100, 255, 100))
                                screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))

                            elif building_type == 'hospital':
                                current_prod = 2
                                if terrain == TileType.BUILDING_INTACT:
                                    current_prod += 4
                                current_prod *= current_level
                                next_prod = current_prod // current_level * next_level if current_level > 0 else 0

                                upgrade_text = preview_font.render(f"UPGRADE: {building_type.capitalize()} L{current_level} → L{next_level}", True, (100, 255, 255))
                                screen.blit(upgrade_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                cost_text = preview_font.render(f"Cost: {upgrade_cost} materials", True, (255, 200, 100))
                                screen.blit(cost_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                prod_text = preview_font.render(f"Production: {current_prod} → {next_prod} medicine/turn", True, (100, 255, 100))
                                screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))

                            elif building_type == 'wall':
                                upgrade_text = preview_font.render(f"UPGRADE: {building_type.capitalize()} L{current_level} → L{next_level}", True, (100, 255, 255))
                                screen.blit(upgrade_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                cost_text = preview_font.render(f"Cost: {upgrade_cost} materials", True, (255, 200, 100))
                                screen.blit(cost_text, (panel_x + 10, panel_y + y_offset))
                                y_offset += 20
                                prod_text = preview_font.render(f"Effect: Increased defensive bonus", True, (100, 255, 100))
                                screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))
                        else:
                            max_text = preview_font.render(f"{building_type.capitalize()} is at MAX LEVEL", True, (255, 100, 100))
                            screen.blit(max_text, (panel_x + 10, panel_y + y_offset))

                # Show current building production if there's a building here
                elif not building_placement_mode:
                    building = game_state.get_building_at(tile_x, tile_y)
                    if building:
                        building_type = building['type']
                        terrain = building['terrain']
                        level = building.get('level', 1)

                        # Calculate production for this building
                        if building_type == 'farm':
                            prod = 0
                            if terrain == TileType.GRASS:
                                prod = 6
                            elif terrain == TileType.FOREST:
                                prod = 3
                            prod *= level
                            prod_text = bonus_font.render(f"Current: {building_type.capitalize()} L{level} producing {prod} food/turn", True, (255, 255, 100))
                            screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))
                        elif building_type == 'dock':
                            prod = 12 * level
                            prod_text = bonus_font.render(f"Current: {building_type.capitalize()} L{level} producing {prod} food/turn", True, (255, 255, 100))
                            screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))
                        elif building_type == 'workshop':
                            prod = 0
                            if terrain == TileType.RUBBLE:
                                prod = 2
                            elif terrain in [TileType.BUILDING_RUINED, TileType.ROAD]:
                                prod = 4
                            elif terrain == TileType.BUILDING_INTACT:
                                prod = 8
                            prod *= level
                            prod_text = bonus_font.render(f"Current: {building_type.capitalize()} L{level} producing {prod} materials/turn", True, (255, 255, 100))
                            screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))
                        elif building_type == 'hospital':
                            prod = 2
                            if terrain == TileType.BUILDING_INTACT:
                                prod += 4
                            prod *= level
                            prod_text = bonus_font.render(f"Current: {building_type.capitalize()} L{level} producing {prod} medicine/turn", True, (255, 255, 100))
                            screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))
                        elif building_type == 'wall':
                            prod_text = bonus_font.render(f"Current: {building_type.capitalize()} L{level} (defensive structure)", True, (255, 255, 100))
                            screen.blit(prod_text, (panel_x + 10, panel_y + y_offset))

    def move_camera(self, dx, dy):
        """Move the camera"""
        self.camera_x += dx
        self.camera_y += dy

    def screen_to_tile(self, screen_x, screen_y):
        """Convert screen coordinates to tile coordinates"""
        tile_x = (screen_x + self.camera_x) // self.tile_size
        tile_y = (screen_y + self.camera_y) // self.tile_size
        return tile_x, tile_y
