# config/work_log/def_worklog_exception.py
class WorkLogError(Exception): pass
class WorkLogSaveError(WorkLogError): pass
class WorkLogLoadError(WorkLogError): pass