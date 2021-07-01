class Statements(list):
    def has_property(self, property):
        items = []
        for item in self:
            try:
                if getattr(item, property):
                    items.append(item)
            except AttributeError:
                pass

        return __class__(items)
