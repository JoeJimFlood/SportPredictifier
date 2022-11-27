class Team:

    def __init__(self, **kwargs):
        """
        Team that participates in a competition

        Attributes
        ----------
        code (str):
            Code used to identify team
        name (str):
            Team name
        stadium (SportPredictifier.Stadium):
            Team's usual home stadium
        color1 (str):
            Hex codes for team's primary color
        color2 (str):
            Hex codes for team's secondary color
        """
        self.name = kwargs["name"]
        self.stadium = kwargs["stadium"]
        self.color1 = kwargs["color1"]
        self.color2 = kwargs["color2"]

        self.stats = {}