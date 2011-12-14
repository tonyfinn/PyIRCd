import json

class Config:
    def __init__(self, filename):
        """Create a new config object from a given filename.

        Throws a IOError if it cannot open the filename.

        """
        with open(filename, encoding='utf-8') as config_file:
            self.__dict__['props'] = json.load(config_file)

    def __getattr__(self, name):
        if name in self.props:
            return self.props[name]
        else:
            raise AttributeError()

    def __setattr__(self, name, value):
        self.props[name] = value
