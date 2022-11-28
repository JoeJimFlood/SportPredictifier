class Stadium:

    def __init__(self, **kwargs):
        """
        Stadium where a game can be played

        Attributes
        ----------
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
        self.code = kwargs["code"]
        self.name = kwargs["name"]
        self.location = kwargs["location"]
        self.lat = kwargs["lat"]
        self.lon = kwargs["lon"]