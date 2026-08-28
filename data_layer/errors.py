class DataLayerError(Exception):
    """Base Data Layer error."""


class DataLayerReadOnlyError(RuntimeError):
    def __init__(self, api_name="unknown"):
        RuntimeError.__init__(self, "DATA_LAYER_READ_ONLY")
        self.api_name = api_name


class DataCorruptedError(DataLayerError):
    def __init__(self, dataset_id, message="DATA_CORRUPTED"):
        DataLayerError.__init__(self, message)
        self.dataset_id = dataset_id


class DatasetImmutableError(DataLayerError):
    def __init__(self, dataset_id):
        DataLayerError.__init__(
            self, "dataset already frozen and cannot be overwritten: %s" % dataset_id
        )
        self.dataset_id = dataset_id


class FinalOosLockedError(DataLayerError):
    def __init__(self):
        DataLayerError.__init__(self, "FINAL_OOS_LOCKED")


class ValidationFailedError(DataLayerError):
    pass


class Mt5UnavailableError(DataLayerError):
    pass
