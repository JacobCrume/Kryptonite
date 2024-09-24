def requires_login(func):
    def wrapper(self, *args, **kwargs):
        if not self.authorization:
            raise RuntimeError("You must be logged in to use this method")
        return func(self, *args, **kwargs)
    return wrapper