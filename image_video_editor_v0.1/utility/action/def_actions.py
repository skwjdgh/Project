# utility/action/def_actions.py
from abc import ABC, abstractmethod
class IAction(ABC):
    @abstractmethod
    def execute(self): pass
    @abstractmethod
    def undo(self): pass