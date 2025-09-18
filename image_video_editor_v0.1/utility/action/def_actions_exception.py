# utility/action/def_actions_exception.py
class ActionError(Exception): pass
class UndoActionError(ActionError): pass
class RedoActionError(ActionError): pass