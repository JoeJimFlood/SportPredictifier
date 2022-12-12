class Stadium:

    def __init__(self, code, name, location, lat, lon, elev):
        """
        Stadium where a game can be played

        Attributes
        ----------
        code (str):
            Code used for identifying team name
        name (str):
            Stadium name
        location (str):
            Stadium location
        lat (float):
            Latitude of stadium
        lon (float):
            Longitude of stadium
        elev (float):
            Elevation (in meters) of stadium
        """
        self.code = code
        self.name = name
        self.location = location
        self.lat = lat
        self.lon = lon
        self.elev = elev