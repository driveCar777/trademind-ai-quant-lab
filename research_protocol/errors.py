class ResearchProtocolError(Exception):
    pass


class FutureDataAccess(ResearchProtocolError):
    def __init__(self, detail="FUTURE_DATA_ACCESS"):
        ResearchProtocolError.__init__(self, detail)


class ExperimentBlocked(ResearchProtocolError):
    def __init__(self, reason):
        ResearchProtocolError.__init__(self, "EXPERIMENT_BLOCKED: %s" % reason)
        self.reason = reason


class FeatureUnavailable(ResearchProtocolError):
    def __init__(self, feature_id, reason):
        ResearchProtocolError.__init__(self, "FEATURE_UNAVAILABLE: %s (%s)" % (feature_id, reason))


class ExperimentImmutableError(ResearchProtocolError):
    pass
