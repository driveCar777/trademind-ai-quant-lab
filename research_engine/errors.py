class ResearchEngineError(Exception):
    pass


class HypothesisRejected(ResearchEngineError):
    pass


class PreregistrationLocked(ResearchEngineError):
    pass


class FinalOosAccessDenied(ResearchEngineError):
    def __init__(self, detail="FINAL_OOS_ACCESS_DENIED"):
        ResearchEngineError.__init__(self, detail)


class ResultImmutableError(ResearchEngineError):
    pass


class ResultInvalid(ResearchEngineError):
    pass


class DeterminismFailure(ResearchEngineError):
    pass


class MutationBlocked(ResearchEngineError):
    pass


class ExperimentBlocked(ResearchEngineError):
    pass


class ContractMismatch(ResearchEngineError):
    def __init__(self, detail="CONTRACT_MISMATCH"):
        ResearchEngineError.__init__(self, detail)
        self.detail = detail
