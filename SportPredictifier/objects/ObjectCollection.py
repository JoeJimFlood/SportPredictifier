import pandas as pd
from collections import OrderedDict

class ObjectCollection(OrderedDict):
    '''
    An `ObjectCollection` is an object build on the `collections.OrderedDict` object with an additional function to extract the same attribute for every object in it,
    (a la returning a column of a data frame)
    '''
    def __init__(self):
        dict(self).__init__()

    def extract_attribute(self, attr):
        '''
        Extracts the same attribute for every object in the `ObjectCollection` and returns it as a `pandas.Series` with the keys as the index

        Parameters
        ----------
        attr (str):
            Attribute to return for each object in the collection

        Returns
        -------
        series (pandas.Series):
            Series with the value of each attribute of each object. The index is the keys of the `ObjectCollection`
        '''
        return pd.Series([getattr(value, attr) for value in self.values()],
                         index = self.keys())