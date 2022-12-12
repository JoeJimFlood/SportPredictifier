class ScoreSettings:
    '''
    Settings for different ways to score and characteristics of them

    Attributes
    ----------
    code (str):
        Code used to identify score type
    description (str):
        Description of score type
    points (numeric):
        Number of points scored
    prob (bool):
        If true, the score will be probabilistic on a condition (such as conversions after scores in tackle forms of football). If false a number of scores will be simulated.
    opp_effect (bool):
        Indicates whether or not the opposition has an effect on this score
    base (bool):
        Base probability for probabilistic scoring
    condition (bool):
        Condition for when the probabilistic scoring should be run based on score types defined earlier
    '''
    def __init__(self, code, description, points, prob, opp_effect, base, condition):
        self.code = code
        self.description = description
        self.points = points
        self.prob = prob
        self.opp_effect = opp_effect
        self.base = base
        self.condition = condition