import random
import math

class TileType:
    GRASS = 0
    ROAD = 1
    BUILDING_RUINED = 2
    BUILDING_INTACT = 3
    RUBBLE = 4
    FOREST = 5
    WATER = 6
    RESEARCH_LAB = 7

class MapGenerator:
    def __init__(self, width, height, seed=None):
        self.width = width
        self.height = height
        self.seed = seed if seed else random.randint(0, 999999)
        random.seed(self.seed)

    def _simple_noise(self, x, y):
        """Simple noise function using sine waves"""
        # Combine multiple sine waves for pseudo-random terrain
        n = (math.sin(x * 0.1 + self.seed) *
             math.cos(y * 0.1 + self.seed) * 0.5 +
             math.sin(x * 0.05) * math.sin(y * 0.05) * 0.3 +
             math.cos(x * 0.02 + y * 0.02) * 0.2)
        return n

    def generate(self):
        """Generate a procedural zombie apocalypse map"""
        # Initialize base terrain
        map_grid = [[TileType.GRASS for _ in range(self.width)] for _ in range(self.height)]

        # Add simple noise for natural variation
        for y in range(self.height):
            for x in range(self.width):
                noise_val = self._simple_noise(x, y)

                # Determine terrain type based on noise
                if noise_val < -0.3:
                    map_grid[y][x] = TileType.WATER
                elif noise_val > 0.4:
                    map_grid[y][x] = TileType.FOREST

        # Generate ruined city clusters (scale with map size)
        # Base: 3-6 cities for 50x50 (2500 tiles)
        # Scale proportionally: larger maps get more cities
        map_area = self.width * self.height
        base_area = 50 * 50  # 2500 tiles
        scale_factor = map_area / base_area

        min_cities = max(3, int(3 * scale_factor))
        max_cities = max(6, int(6 * scale_factor))
        num_cities = random.randint(min_cities, max_cities)

        for _ in range(num_cities):
            self._generate_ruined_city(map_grid)

        # Add road network connecting cities
        self._generate_roads(map_grid)

        # Place the research lab (only one on the entire map)
        self.research_lab_pos = self._place_research_lab(map_grid)

        # Add resources and points of interest
        self.resources = self._place_resources(map_grid)

        return map_grid

    def _generate_ruined_city(self, map_grid):
        """Generate a dense cluster of ruined buildings with city-like patterns"""
        center_x = random.randint(8, self.width - 8)
        center_y = random.randint(8, self.height - 8)
        city_size = random.randint(25, 45)  # Increased from 8-15
        city_radius = random.randint(6, 10)  # Tighter clustering

        # First pass: Create a grid-like road network within the city
        for i in range(-city_radius, city_radius + 1, 5):  # Roads every 5 tiles (reduced from 3)
            for offset in range(-city_radius, city_radius + 1):
                # Horizontal roads
                x = center_x + offset
                y = center_y + i
                if 0 <= x < self.width and 0 <= y < self.height:
                    if map_grid[y][x] != TileType.WATER:
                        map_grid[y][x] = TileType.ROAD

                # Vertical roads
                x = center_x + i
                y = center_y + offset
                if 0 <= x < self.width and 0 <= y < self.height:
                    if map_grid[y][x] != TileType.WATER:
                        map_grid[y][x] = TileType.ROAD

        # Second pass: Place buildings in a denser pattern
        for _ in range(city_size):
            offset_x = random.randint(-city_radius, city_radius)
            offset_y = random.randint(-city_radius, city_radius)
            x = max(0, min(self.width - 1, center_x + offset_x))
            y = max(0, min(self.height - 1, center_y + offset_y))

            # Don't place buildings on water or roads (unless it's a corner)
            if map_grid[y][x] == TileType.WATER:
                continue
            if map_grid[y][x] == TileType.ROAD and random.random() < 0.7:
                continue

            # 60% ruined, 40% intact buildings (more intact for better resources)
            if random.random() < 0.6:
                map_grid[y][x] = TileType.BUILDING_RUINED
            else:
                map_grid[y][x] = TileType.BUILDING_INTACT

        # Third pass: Add rubble around buildings for atmosphere
        for dy in range(-city_radius - 2, city_radius + 3):
            for dx in range(-city_radius - 2, city_radius + 3):
                x = center_x + dx
                y = center_y + dy
                if (0 <= x < self.width and 0 <= y < self.height and
                    map_grid[y][x] == TileType.GRASS):
                    # Check if near a building
                    near_building = False
                    for ndy in [-1, 0, 1]:
                        for ndx in [-1, 0, 1]:
                            nx, ny = x + ndx, y + ndy
                            if (0 <= nx < self.width and 0 <= ny < self.height and
                                map_grid[ny][nx] in [TileType.BUILDING_RUINED, TileType.BUILDING_INTACT]):
                                near_building = True
                                break
                        if near_building:
                            break

                    if near_building and random.random() < 0.4:
                        map_grid[y][x] = TileType.RUBBLE

    def _generate_roads(self, map_grid):
        """Create road networks (scale with map size)"""
        # Base: 3-5 roads for 50x50 map
        # Scale proportionally with map dimensions
        map_area = self.width * self.height
        base_area = 50 * 50
        scale_factor = map_area / base_area

        min_roads = max(3, int(3 * scale_factor))
        max_roads = max(5, int(5 * scale_factor))
        num_roads = random.randint(min_roads, max_roads)

        # Simple horizontal and vertical roads
        for _ in range(num_roads):
            if random.random() < 0.5:
                # Horizontal road
                y = random.randint(0, self.height - 1)
                for x in range(self.width):
                    if map_grid[y][x] not in [TileType.BUILDING_RUINED, TileType.BUILDING_INTACT, TileType.WATER]:
                        map_grid[y][x] = TileType.ROAD
            else:
                # Vertical road
                x = random.randint(0, self.width - 1)
                for y in range(self.height):
                    if map_grid[y][x] not in [TileType.BUILDING_RUINED, TileType.BUILDING_INTACT, TileType.WATER]:
                        map_grid[y][x] = TileType.ROAD

    def _place_research_lab(self, map_grid):
        """Place a single research lab somewhere on the map"""
        # Find a suitable location (not water, not on the edge)
        attempts = 0
        while attempts < 100:
            x = random.randint(10, self.width - 10)
            y = random.randint(10, self.height - 10)

            # Make sure it's on grass or road
            if map_grid[y][x] in [TileType.GRASS, TileType.ROAD]:
                map_grid[y][x] = TileType.RESEARCH_LAB
                return (x, y)
            attempts += 1

        # Fallback if we couldn't find a good spot
        x = self.width // 2
        y = self.height // 2
        map_grid[y][x] = TileType.RESEARCH_LAB
        return (x, y)

    def _place_resources(self, map_grid):
        """Place scavengable resources on the map"""
        resources = {}

        for y in range(self.height):
            for x in range(self.width):
                tile = map_grid[y][x]

                # Buildings have higher chance of resources
                # Medicine is not found on the map - must be produced by hospitals
                if tile == TileType.BUILDING_RUINED:
                    if random.random() < 0.6:
                        resources[(x, y)] = {
                            'food': random.randint(8, 20),
                            'materials': random.randint(15, 35),
                            'medicine': 0
                        }
                elif tile == TileType.BUILDING_INTACT:
                    if random.random() < 0.8:
                        resources[(x, y)] = {
                            'food': random.randint(15, 40),
                            'materials': random.randint(20, 45),
                            'medicine': 0
                        }

        return resources
