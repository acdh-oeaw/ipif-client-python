from munch import Munch as Bunch

"""
Hacks Bunch to stop a really trivial sorting glitch crashing the whole thing
"""


class Bunch(Bunch):
    def __init__(self, varname, *args, **kwargs):
        self.__var_name = varname
        super().__init__(*args, **kwargs)

    def __repr__(self):
        keys = self.keys()

        # keys.sort()
        args = ", ".join(
            [
                "%s=%r" % (key, self[key])
                for key in keys
                if not key.startswith("_Bunch__")
            ]
        )
        return "%s: %s" % (self.__var_name, args)
