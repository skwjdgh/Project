# -*- coding: utf-8 -*-

class ExperimentError(Exception):
    pass

class DataLoadError(ExperimentError):
    pass

class TranscribeError(ExperimentError):
    pass

class TokenizerInitWarning(Warning):
    pass
