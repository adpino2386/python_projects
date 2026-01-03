"""
Park Factors and Weather Factors
Park factors adjust run scoring expectations based on ballpark characteristics
"""

# Park Factors Database
# Values > 1.0 favor hitters (more runs), < 1.0 favor pitchers (fewer runs)
# Based on historical run scoring data
PARK_FACTORS = {
    # Coors Field - Highest elevation, extreme hitter's park
    "Coors Field": {
        "park_factor": 1.35,  # 35% more runs than average
        "home_run_factor": 1.30,
        "hits_factor": 1.25
    },
    # Other extreme hitter's parks
    "Yankee Stadium": {
        "park_factor": 1.12,
        "home_run_factor": 1.15,
        "hits_factor": 1.08
    },
    "Fenway Park": {
        "park_factor": 1.10,
        "home_run_factor": 1.05,
        "hits_factor": 1.15
    },
    "Great American Ball Park": {
        "park_factor": 1.15,
        "home_run_factor": 1.20,
        "hits_factor": 1.10
    },
    "Oriole Park at Camden Yards": {
        "park_factor": 1.08,
        "home_run_factor": 1.12,
        "hits_factor": 1.05
    },
    # Extreme pitcher's parks
    "Petco Park": {
        "park_factor": 0.85,  # 15% fewer runs than average
        "home_run_factor": 0.80,
        "hits_factor": 0.88
    },
    "T-Mobile Park": {
        "park_factor": 0.88,
        "home_run_factor": 0.85,
        "hits_factor": 0.90
    },
    "Oracle Park": {
        "park_factor": 0.90,
        "home_run_factor": 0.82,
        "hits_factor": 0.95
    },
    # Default/neutral parks (1.0 = neutral)
    "default": {
        "park_factor": 1.0,
        "home_run_factor": 1.0,
        "hits_factor": 1.0
    }
}

# Team to Stadium mapping (common names)
TEAM_STADIUMS = {
    "Rockies": "Coors Field",
    "Yankees": "Yankee Stadium",
    "Red Sox": "Fenway Park",
    "Reds": "Great American Ball Park",
    "Orioles": "Oriole Park at Camden Yards",
    "Padres": "Petco Park",
    "Mariners": "T-Mobile Park",
    "Giants": "Oracle Park",
    "Dodgers": "Dodger Stadium",
    "Astros": "Minute Maid Park",
    "Rangers": "Globe Life Field",
    "Angels": "Angel Stadium",
    "Athletics": "Oakland Coliseum",
    "Braves": "Truist Park",
    "Marlins": "loanDepot park",
    "Mets": "Citi Field",
    "Nationals": "Nationals Park",
    "Phillies": "Citizens Bank Park",
    "Cubs": "Wrigley Field",
    "Brewers": "American Family Field",
    "Pirates": "PNC Park",
    "Cardinals": "Busch Stadium",
    "Diamondbacks": "Chase Field",
    "Rays": "Tropicana Field",
    "Blue Jays": "Rogers Centre",
    "Guardians": "Progressive Field",
    "Tigers": "Comerica Park",
    "Royals": "Kauffman Stadium",
    "Twins": "Target Field",
    "White Sox": "Guaranteed Rate Field",
    # Add more as needed
}

# Weather Impact Factors
# Multipliers that adjust run scoring based on weather conditions
WEATHER_FACTORS = {
    "wind_out_to_center": {
        "park_factor_multiplier": 1.15,  # Wind blowing out increases HRs
        "home_run_multiplier": 1.20,
        "description": "Wind blowing out (home to center) favors hitters"
    },
    "wind_in_from_center": {
        "park_factor_multiplier": 0.90,  # Wind blowing in reduces HRs
        "home_run_multiplier": 0.85,
        "description": "Wind blowing in (center to home) favors pitchers"
    },
    "rain": {
        "park_factor_multiplier": 0.85,  # Rain reduces offense
        "home_run_multiplier": 0.80,
        "description": "Rain/Precipitation reduces offensive production"
    },
    "hot_temperature": {
        "park_factor_multiplier": 1.08,  # Hot weather helps balls carry
        "home_run_multiplier": 1.10,
        "description": "Hot weather (>85°F) helps balls carry further"
    },
    "cold_temperature": {
        "park_factor_multiplier": 0.92,  # Cold weather reduces offense
        "home_run_multiplier": 0.90,
        "description": "Cold weather (<60°F) reduces offensive production"
    },
    "neutral": {
        "park_factor_multiplier": 1.0,
        "home_run_multiplier": 1.0,
        "description": "Neutral weather conditions"
    }
}


def get_park_factor(stadium_name: str = None, team_name: str = None) -> dict:
    """
    Get park factor for a given stadium or team.
    
    Args:
        stadium_name: Name of the stadium
        team_name: Name of the team (will look up stadium)
    
    Returns:
        Dictionary with park factors
    """
    # Try to get stadium name from team if not provided
    if not stadium_name and team_name:
        stadium_name = TEAM_STADIUMS.get(team_name)
    
    if stadium_name and stadium_name in PARK_FACTORS:
        return PARK_FACTORS[stadium_name]
    
    # Return default/neutral park factors
    return PARK_FACTORS["default"]


def get_weather_factor(weather_conditions: str = None) -> dict:
    """
    Get weather impact factors.
    
    Args:
        weather_conditions: Weather condition key (e.g., 'wind_out_to_center', 'rain')
    
    Returns:
        Dictionary with weather multipliers
    """
    if weather_conditions and weather_conditions in WEATHER_FACTORS:
        return WEATHER_FACTORS[weather_conditions]
    
    return WEATHER_FACTORS["neutral"]


def combine_park_and_weather_factors(park_factor: float, weather_multiplier: float) -> float:
    """
    Combine park and weather factors to get total adjustment.
    
    Args:
        park_factor: Base park factor
        weather_multiplier: Weather multiplier
    
    Returns:
        Combined factor
    """
    return park_factor * weather_multiplier

