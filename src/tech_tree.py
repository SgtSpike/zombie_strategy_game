# Tech Tree Definitions

TECH_TREE = {
    # Units Tree
    'scavenging_efficiency': {
        'name': 'Scavenging Efficiency',
        'cost': 10,
        'description': '+25% resources from scavenging',
        'prerequisites': [],
        'category': 'units'
    },
    'scout_training': {
        'name': 'Scout Training',
        'cost': 20,
        'description': 'Scouts gain +1 vision range',
        'prerequisites': [],
        'category': 'units'
    },
    'combat_training': {
        'name': 'Combat Training',
        'cost': 20,
        'description': 'All units spawn as level 2',
        'prerequisites': [],
        'category': 'units'
    },
    'tactical_medicine': {
        'name': 'Tactical Medicine',
        'cost': 20,
        'description': 'Medics heal +20 HP per action',
        'prerequisites': ['basic_medicine'],
        'category': 'units'
    },
    'armor_plating': {
        'name': 'Armor Plating',
        'cost': 40,
        'description': 'All units gain +40 max HP',
        'prerequisites': ['combat_training'],
        'category': 'units'
    },
    'rapid_response': {
        'name': 'Rapid Response',
        'cost': 40,
        'description': 'Units gain +1 movement point',
        'prerequisites': ['scout_training'],
        'category': 'units'
    },
    'advanced_weaponry': {
        'name': 'Advanced Weaponry',
        'cost': 30,
        'description': 'Soldiers gain +10 attack',
        'prerequisites': ['combat_training'],
        'category': 'units'
    },
    'super_soldier_program': {
        'name': 'Super Soldier Program',
        'cost': 40,
        'description': 'Recruit elite units (150 HP, 30 attack)',
        'prerequisites': ['advanced_weaponry'],
        'category': 'units'
    },

    # City Tree
    'fortification': {
        'name': 'Fortification',
        'cost': 10,
        'description': 'Units on walls take 50% less damage from attacks',
        'prerequisites': [],
        'category': 'city'
    },
    'advanced_farming': {
        'name': 'Advanced Farming',
        'cost': 10,
        'description': 'Farms produce +2 food/turn',
        'prerequisites': [],
        'category': 'city'
    },
    'industrial_workshops': {
        'name': 'Industrial Workshops',
        'cost': 10,
        'description': 'Workshops produce +3 materials/turn',
        'prerequisites': [],
        'category': 'city'
    },
    'basic_medicine': {
        'name': 'Basic Medicine',
        'cost': 10,
        'description': 'Hospitals produce +2 medicine/turn',
        'prerequisites': [],
        'category': 'city'
    },
    'research_documentation': {
        'name': 'Research Documentation',
        'cost': 20,
        'description': 'All research costs reduced by 30%',
        'prerequisites': [],
        'category': 'city'
    },
    'quick_start': {
        'name': 'Quick Start',
        'cost': 20,
        'description': 'New cities start with +30 materials, +30 food',
        'prerequisites': ['fortification'],
        'category': 'city'
    },
    'watchtower': {
        'name': 'Watchtower',
        'cost': 20,
        'description': '+2 vision range for cities',
        'prerequisites': ['scout_training'],
        'category': 'city'
    },
    'cure_research': {
        'name': 'Cure Research',
        'cost': 20,
        'description': 'Reduces cure manufacturing cost by 30%',
        'prerequisites': ['tactical_medicine'],
        'category': 'city'
    },
    'automated_defenses': {
        'name': 'Automated Defenses',
        'cost': 30,
        'description': 'Cities/buildings damage adjacent zombies',
        'prerequisites': ['fortification'],
        'category': 'city'
    },
    'helicopter_transport': {
        'name': 'Helicopter Transport',
        'cost': 50,
        'description': 'Units can teleport between cities',
        'prerequisites': ['automated_defenses'],
        'category': 'city'
    }
}

def can_research(tech_id, researched_techs):
    """Check if a tech can be researched (prerequisites met)"""
    tech = TECH_TREE[tech_id]
    for prereq in tech['prerequisites']:
        if prereq not in researched_techs:
            return False
    return True

def get_tech_cost(tech_id, researched_techs):
    """Get the cost of a tech (possibly reduced by Research Documentation)"""
    base_cost = TECH_TREE[tech_id]['cost']
    if 'research_documentation' in researched_techs:
        return int(base_cost * 0.7)  # 30% discount
    return base_cost
