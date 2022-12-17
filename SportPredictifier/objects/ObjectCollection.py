import pandas as pd
from collections import OrderedDict

class ObjectCollection(OrderedDict):

    def __init__(self):
        dict(self).__init__()

    def extract_attribute(self, attr):
        return pd.Series([getattr(value, attr) for value in self.values()],
                         index = self.keys())