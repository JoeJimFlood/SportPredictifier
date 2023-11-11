import math

def __geodesic_distance(olat, olng, dlat, dlng):
    '''
    Returns geodesic distance in percentage of half the earth's circumference between two points on the earth's surface

    Parameters
    ----------
    olat (float):
        Origin latitude in degrees relative to the Equator (positive is north, negative is south)
    olng (float):
        Origin longitude in degrees relative to the Prime Meridian (positive is east, negative is west)
    dlat (float):
        Destination latitude in degrees relative to the Equator (positive is north, negative is south)
    dlng (float):
        Destination longitude in degrees relative to the Prime Meridian (positive is east, negative is west)
    '''
    scale = math.tau/360
    olat *= scale
    olng *= scale
    dlat *= scale
    dlng *= scale

    delta_lat = (dlat - olat)
    delta_lng = (dlng - olng)

    a = math.sin(delta_lat/2)**2 + math.cos(olat)*math.cos(dlat)*math.sin(delta_lng/2)**2
    return 4*math.atan2(math.sqrt(a), math.sqrt(1-a))/math.tau

def get_spatial_weight(stadium, home, reference):
    '''
    Gets the travel weight based on a venue, a team's home lat/long coordinates, and a reference location.
    The weight is equal to 1 if the distance from the team's home location to the stadium's location is the same as the distance from the home location
    to the reference location, and 0 if they are antipodal.

    As an example, if a team is based in Seattle and they're playing a game in San Diego (1700 km), a past game they played in Denver (1650 km) will be weighted
    more in calculating expected scores than a past game they played in New York (3875 km) or at home (0 km).

    In this scenario, the following weights would be applied to the score table using San Diego as the reference location:

    Location |Distance (km)|Proportion of half of Earth's circumference|Reference|Difference|Weight|
    ---------|-------------|-------------------------------------------|---------|----------|------|
    Denver   |         1650|                                      0.082|    0.085|    -0.002| 0.998|
    New York |         3875|                                      0.193|    0.085|     0.109| 0.891|
    Seattle  |            0|                                      0.000|    0.085|    -0.085| 0.915|
    Perth    |        14900|                                      0.744|    0.085|     0.659| 0.341|

    Parameters
    ----------
    stadium (SportPredictifier.Stadium):
        Stadium where the game is to be played at
    home (SportPredictifier.Stadium):
        Team's home stadium
    reference (SportPredictifier.Stadium):
        Stadium to use as a reference location
    '''
    reference_distance = __geodesic_distance(home.lat, home.lon, reference.lat, reference.lon)
    travel_distance = __geodesic_distance(home.lat, home.lon, stadium.lat, stadium.lon)
    return 1 - abs(travel_distance - reference_distance)