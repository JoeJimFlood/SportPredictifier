import math

def __geodesic_distance(olat, olng, dlat, dlng):
    '''
    Returns geodesic distance in percentage of half the earth's circumference between two points on the earth's surface
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
    Gets the travel weight based on a venue, a team's home lat/long coordinates, and a reference distance
    '''
    reference_distance = __geodesic_distance(home.lat, home.lon, reference.lat, reference.lon)
    travel_distance = __geodesic_distance(home.lat, home.lon, stadium.lat, stadium.lon)
    return 1 - abs(travel_distance - reference_distance)