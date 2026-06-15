from typing import Generic, TypeVar
import gc

T = TypeVar("T")

class Effector(Generic[T]):
    """Store the effector method for the variablity point along with additional information.
    Allow to call the method with a new description and therefore configure the variability point."""

    instances = []

    def __init__(self, vp:str, instance, func, identifiers:list, args:dict, full_description:bool):
        self.vp = vp
        self._instance = instance
        self._func = func
        self.identifiers = identifiers
        self.args = args
        self.full_description = full_description

        # Make sure nothing gets added multiple times
        if self not in self.instances:
            Effector.instances.append(self)

    def __del__(self):
        #print("Deleted effector", self)
        pass

    def change(self, description):
        """Calls the effector function with the given description"""
        if self.args is not None:
            self._func(self._instance, description, **self.args)
            return

        self._func(self._instance, description)
    
    def effector(vp:str, identifiers:str=None, full_description:bool=False):
        """Decorator to register a function as an effector.

        :param identifiers: name of the variable of the class instance the decorator is used on"""
        def effector(func):
            def inner(self, *args, vp=vp, **kwargs):

                # Use dynamic vp
                if "vpoint" in kwargs is not None:
                    vp = kwargs["vpoint"]

                # Create the new effector instance
                found_identifier = getattr(self, identifiers) if identifiers is not None else []
                if not isinstance(found_identifier, list):
                    found_identifier = [found_identifier]

                Effector(vp, self, func, found_identifier,
                         args=kwargs,
                         full_description=full_description)

                return func(self, *args, **kwargs)
            return inner
        return effector
    
    def __eq__(self, value):
        return self.vp == value.vp and self._func == value._func and self.identifiers == value.identifiers and self.args == value.args and self._instance == value._instance
    
    @classmethod
    def get_all(cls):
        """Return all effector instances"""
        return cls.instances
    
    @classmethod
    def cleanup(cls):
        """Remove all effector instances that are not referenced anymore.

        This needs to be done after a component is changed that itself uses effectors!"""
        for e in list(cls.instances):
            if len(gc.get_referrers(e._instance)) > 1:
                continue
            
            cls.instances.remove(e)

    @classmethod
    def clear_all(cls):
        """Clears all saved instances. Relevant for unit tests"""
        cls.instances.clear()