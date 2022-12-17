class Team:

    def __init__(self, code, name, stadium, color1, color2):
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
        self.code = code
        self.name = name
        self.stadium = stadium
        self.color1 = color1
        self.color2 = color2

        self.stats = {}
        self.residual_stats = {}

        self.opp = None