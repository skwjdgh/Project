class ExperimentError(Exception):
    """Custom exception class for specific errors during the experiment."""
    def __init__(self, message="An error occurred during the experiment."):
        self.message = message
        super().__init__(self.message)

