# config/input_output/def_io_exception.py
class IOError(Exception): pass
class ExportError(IOError): pass
class ImportError(IOError): pass