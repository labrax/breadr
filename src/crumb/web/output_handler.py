

from pprint import pprint


class OutputConverter:
    def __init__(self):
        self.handlers = dict()
        self._init_basic()

    def _init_basic(self) -> None:
        """initialises some transformations"""
        self.handlers[int] = lambda x: str(x)
        self.handlers[str] = lambda x: x if len(x) < 32 else x[:28] + ' ...'

        def pprint_handler(x):
            if len(pprint(x)) < 32:
                return pprint(x)
            return pprint(x)[:28] + ' ...'

        self.handlers[dict] = pprint_handler
        self.handlers[list] = pprint_handler
        self.handlers[tuple] = pprint_handler

        # if pandas is installed
        try:
            import pandas as pd
            self.handlers[pd.DataFrame] = lambda x: x.head(5).to_html()
        except ImportError as ie:
            print(ie)

        # if matplotlib and mpld3 are installed
        try:
            import matplotlib
            import mpld3

            def pltfig(x):
                return mpld3.fig_to_html(x)
            self.handlers[matplotlib.figure.Figure] = pltfig
        except ImportError as ie:
            print(ie)

    def get_html(self, type, value):
        if type in self.handlers:
            return self.handlers[type](value)
        else:
            return 'not defined'
