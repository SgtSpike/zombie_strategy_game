import pygame
import os

def create_sprites():
    """Generate pixelated sprites for all unit types"""
    sprite_size = 32  # 32x32 pixels for each sprite
    sprites = {}
    
    # Survivor - Blue humanoid
    survivor = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Head
    pygame.draw.rect(survivor, (100, 150, 255), (12, 8, 8, 8))
    # Body
    pygame.draw.rect(survivor, (80, 120, 200), (10, 16, 12, 10))
    # Arms
    pygame.draw.rect(survivor, (80, 120, 200), (8, 18, 4, 8))
    pygame.draw.rect(survivor, (80, 120, 200), (20, 18, 4, 8))
    # Legs
    pygame.draw.rect(survivor, (60, 100, 180), (11, 26, 4, 6))
    pygame.draw.rect(survivor, (60, 100, 180), (17, 26, 4, 6))
    sprites['survivor'] = survivor
    
    # Scout - Green humanoid with hat
    scout = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Hat
    pygame.draw.rect(scout, (40, 120, 40), (10, 6, 12, 3))
    # Head
    pygame.draw.rect(scout, (100, 200, 100), (12, 9, 8, 7))
    # Body
    pygame.draw.rect(scout, (70, 160, 70), (10, 16, 12, 10))
    # Arms
    pygame.draw.rect(scout, (70, 160, 70), (8, 18, 4, 8))
    pygame.draw.rect(scout, (70, 160, 70), (20, 18, 4, 8))
    # Legs
    pygame.draw.rect(scout, (50, 130, 50), (11, 26, 4, 6))
    pygame.draw.rect(scout, (50, 130, 50), (17, 26, 4, 6))
    sprites['scout'] = scout
    
    # Soldier - Orange humanoid with armor
    soldier = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Helmet
    pygame.draw.rect(soldier, (200, 100, 0), (11, 7, 10, 10))
    # Body armor
    pygame.draw.rect(soldier, (255, 150, 0), (9, 16, 14, 11))
    # Arms
    pygame.draw.rect(soldier, (255, 150, 0), (7, 18, 5, 9))
    pygame.draw.rect(soldier, (255, 150, 0), (20, 18, 5, 9))
    # Legs
    pygame.draw.rect(soldier, (200, 100, 0), (11, 27, 4, 5))
    pygame.draw.rect(soldier, (200, 100, 0), (17, 27, 4, 5))
    # Weapon
    pygame.draw.rect(soldier, (100, 100, 100), (24, 16, 2, 10))
    sprites['soldier'] = soldier
    
    # Medic - White/red humanoid with cross
    medic = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Head
    pygame.draw.rect(medic, (255, 220, 200), (12, 8, 8, 8))
    # Body (white coat)
    pygame.draw.rect(medic, (240, 240, 240), (10, 16, 12, 10))
    # Red cross
    pygame.draw.rect(medic, (255, 50, 50), (15, 18, 2, 6))
    pygame.draw.rect(medic, (255, 50, 50), (13, 20, 6, 2))
    # Arms
    pygame.draw.rect(medic, (240, 240, 240), (8, 18, 4, 8))
    pygame.draw.rect(medic, (240, 240, 240), (20, 18, 4, 8))
    # Legs
    pygame.draw.rect(medic, (200, 200, 200), (11, 26, 4, 6))
    pygame.draw.rect(medic, (200, 200, 200), (17, 26, 4, 6))
    sprites['medic'] = medic
    
    # Zombie - Red/brown humanoid
    zombie = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Head
    pygame.draw.rect(zombie, (150, 80, 80), (12, 8, 8, 8))
    # Body
    pygame.draw.rect(zombie, (180, 60, 60), (10, 16, 12, 10))
    # Arms (reaching out)
    pygame.draw.rect(zombie, (180, 60, 60), (6, 16, 5, 10))
    pygame.draw.rect(zombie, (180, 60, 60), (21, 16, 5, 10))
    # Legs
    pygame.draw.rect(zombie, (140, 50, 50), (11, 26, 4, 6))
    pygame.draw.rect(zombie, (140, 50, 50), (17, 26, 4, 6))
    sprites['zombie'] = zombie
    
    # Super Zombie - Large red/purple creature (64x64)
    super_zombie = pygame.Surface((64, 64), pygame.SRCALPHA)
    # Head
    pygame.draw.rect(super_zombie, (150, 50, 100), (24, 12, 16, 16))
    # Eyes
    pygame.draw.rect(super_zombie, (255, 0, 0), (26, 16, 4, 4))
    pygame.draw.rect(super_zombie, (255, 0, 0), (34, 16, 4, 4))
    # Body
    pygame.draw.rect(super_zombie, (180, 40, 80), (18, 28, 28, 22))
    # Arms
    pygame.draw.rect(super_zombie, (180, 40, 80), (10, 30, 10, 20))
    pygame.draw.rect(super_zombie, (180, 40, 80), (44, 30, 10, 20))
    # Legs
    pygame.draw.rect(super_zombie, (140, 30, 60), (20, 50, 10, 14))
    pygame.draw.rect(super_zombie, (140, 30, 60), (34, 50, 10, 14))
    # Spikes/details
    pygame.draw.rect(super_zombie, (100, 20, 40), (24, 8, 4, 6))
    pygame.draw.rect(super_zombie, (100, 20, 40), (36, 8, 4, 6))
    sprites['super_zombie'] = super_zombie

    return sprites

def create_terrain_sprites():
    """Generate pixelated sprites for terrain and buildings"""
    sprite_size = 40  # 40x40 pixels to match tile size
    sprites = {}

    # City - Collection of buildings with walls
    city = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Base (ground)
    pygame.draw.rect(city, (100, 80, 60), (0, 0, sprite_size, sprite_size))
    # Main building
    pygame.draw.rect(city, (180, 160, 140), (8, 10, 24, 20))
    # Windows
    pygame.draw.rect(city, (100, 120, 150), (12, 14, 4, 4))
    pygame.draw.rect(city, (100, 120, 150), (20, 14, 4, 4))
    pygame.draw.rect(city, (100, 120, 150), (12, 22, 4, 4))
    pygame.draw.rect(city, (100, 120, 150), (20, 22, 4, 4))
    # Door
    pygame.draw.rect(city, (80, 60, 40), (16, 26, 8, 4))
    # Flag on top
    pygame.draw.rect(city, (100, 100, 100), (19, 6, 2, 6))
    pygame.draw.rect(city, (50, 150, 255), (21, 6, 6, 4))
    sprites['city'] = city

    # Research Lab - Purple/pink building with science equipment
    lab = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Base
    pygame.draw.rect(lab, (140, 100, 180), (4, 8, 32, 28))
    # Door
    pygame.draw.rect(lab, (100, 60, 140), (16, 28, 8, 8))
    # Windows with purple glow
    pygame.draw.rect(lab, (200, 150, 255), (8, 12, 6, 6))
    pygame.draw.rect(lab, (200, 150, 255), (26, 12, 6, 6))
    pygame.draw.rect(lab, (200, 150, 255), (8, 22, 6, 6))
    pygame.draw.rect(lab, (200, 150, 255), (26, 22, 6, 6))
    # Antenna/equipment on top
    pygame.draw.rect(lab, (180, 140, 200), (18, 2, 4, 8))
    pygame.draw.circle(lab, (255, 150, 255), (20, 2), 3)
    # "LAB" text
    font = pygame.font.Font(None, 12)
    lab_text = font.render("LAB", True, (255, 255, 255))
    lab.blit(lab_text, (14, 15))
    sprites['research_lab'] = lab

    # Road - Asphalt with lane markings
    road = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Asphalt base
    pygame.draw.rect(road, (80, 80, 80), (0, 0, sprite_size, sprite_size))
    # Lane markings (dashed lines)
    for i in range(0, sprite_size, 10):
        pygame.draw.rect(road, (200, 200, 100), (18, i, 4, 5))
    sprites['road'] = road

    # Rubble - Scattered debris and rocks
    rubble = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Background
    pygame.draw.rect(rubble, (90, 90, 80), (0, 0, sprite_size, sprite_size))
    # Random rubble pieces
    pygame.draw.rect(rubble, (110, 100, 90), (5, 8, 8, 6))
    pygame.draw.rect(rubble, (100, 90, 80), (20, 12, 10, 8))
    pygame.draw.rect(rubble, (105, 95, 85), (8, 22, 6, 5))
    pygame.draw.rect(rubble, (95, 85, 75), (25, 25, 9, 7))
    pygame.draw.rect(rubble, (115, 105, 95), (14, 30, 7, 6))
    sprites['rubble'] = rubble

    # Ruined Building - Damaged structure with broken walls
    ruined = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Damaged walls (irregular)
    pygame.draw.rect(ruined, (120, 60, 60), (4, 12, 14, 24))
    pygame.draw.rect(ruined, (120, 60, 60), (22, 10, 14, 26))
    # Broken sections (gaps)
    pygame.draw.rect(ruined, (80, 40, 40), (6, 14, 4, 8))
    pygame.draw.rect(ruined, (80, 40, 40), (24, 16, 4, 10))
    # Rubble at base
    pygame.draw.rect(ruined, (100, 50, 50), (4, 32, 32, 4))
    # Broken window
    pygame.draw.rect(ruined, (40, 20, 20), (10, 16, 6, 6))
    sprites['building_ruined'] = ruined

    # Intact Building - Pristine structure
    intact = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    # Main structure
    pygame.draw.rect(intact, (150, 150, 150), (6, 8, 28, 28))
    # Roof
    pygame.draw.polygon(intact, (120, 120, 120), [(6, 8), (20, 2), (34, 8)])
    # Windows (intact)
    pygame.draw.rect(intact, (100, 150, 200), (10, 12, 6, 6))
    pygame.draw.rect(intact, (100, 150, 200), (24, 12, 6, 6))
    pygame.draw.rect(intact, (100, 150, 200), (10, 22, 6, 6))
    pygame.draw.rect(intact, (100, 150, 200), (24, 22, 6, 6))
    # Door
    pygame.draw.rect(intact, (80, 60, 40), (16, 28, 8, 8))
    # Door knob
    pygame.draw.circle(intact, (200, 180, 100), (22, 32), 1)
    sprites['building_intact'] = intact

    return sprites

def create_all_sprites():
    """Create both unit and terrain sprites"""
    all_sprites = {}
    all_sprites.update(create_sprites())
    all_sprites.update(create_terrain_sprites())
    return all_sprites

def save_sprites(sprites, output_dir='sprites'):
    """Save sprites to PNG files"""
    # Create sprites directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for name, sprite in sprites.items():
        filepath = os.path.join(output_dir, f"{name}.png")
        pygame.image.save(sprite, filepath)
        print(f"Saved {filepath}")

if __name__ == "__main__":
    pygame.init()
    sprites = create_all_sprites()

    # Save to files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sprites_dir = os.path.join(script_dir, 'sprites')
    save_sprites(sprites, sprites_dir)

    print(f"\nGenerated {len(sprites)} sprites!")
    print("\nUnit sprites (32x32):")
    for name in ['survivor', 'scout', 'soldier', 'medic', 'zombie']:
        if name in sprites:
            print(f"  {name}: {sprites[name].get_size()}")
    print(f"  super_zombie: {sprites['super_zombie'].get_size()}")

    print("\nTerrain sprites (40x40):")
    for name in ['city', 'research_lab', 'road', 'rubble', 'building_ruined', 'building_intact']:
        if name in sprites:
            print(f"  {name}: {sprites[name].get_size()}")
