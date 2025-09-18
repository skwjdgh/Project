# utility/action/manage_actions.py
import logging
from .def_actions import IAction
from .def_actions_exception import UndoActionError, RedoActionError
class ActionManager:
    def __init__(self):
        self.undo_stack: list[IAction] = []
        self.redo_stack: list[IAction] = []
        logging.info("Action Manager (Undo/Redo) created.")
    def execute_action(self, action: IAction):
        action.execute()
        self.undo_stack.append(action)
        self.redo_stack.clear()
        logging.debug(f"Action executed: {action.__class__.__name__}")
    def undo(self):
        if not self.undo_stack:
            raise UndoActionError("Nothing to undo.")
        action = self.undo_stack.pop()
        action.undo()
        self.redo_stack.append(action)
        logging.debug(f"Action undone: {action.__class__.__name__}")
    def redo(self):
        if not self.redo_stack:
            raise RedoActionError("Nothing to redo.")
        action = self.redo_stack.pop()
        action.execute()
        self.undo_stack.append(action)
        logging.debug(f"Action redone: {action.__class__.__name__}")