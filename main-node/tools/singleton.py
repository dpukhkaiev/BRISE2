class Singleton(type):
    """
            Meta class. Ensures that instances of it (regular class) has only one instance
        (using _instance field of class).
            We use it for the API between front-end and main-node
            https://sourcemaking.com/design_patterns/singleton
            https://sourcemaking.com/design_patterns/singleton/python/1
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance