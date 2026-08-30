"""Frozen model families. No hyperparameter search."""
from __future__ import print_function

from research_engine.v10_model import V10_SEED


def _np():
    import numpy

    return numpy


def fit_predict(model_id, x_train, y_train, x_all):
    numpy = _np()
    xt = numpy.asarray(x_train, dtype=float)
    yt = numpy.asarray(y_train, dtype=int)
    xa = numpy.asarray(x_all, dtype=float)
    if model_id == "M0":
        pos = int((yt == 1).sum())
        n = int(yt.size)
        p = pos / float(n) if n else 0.5
        majority = 1 if pos >= (n - pos) else 0
        proba = numpy.full(len(xa), p, dtype=float)
        pred = numpy.full(len(xa), majority, dtype=int)
        return {
            "proba": proba.tolist(),
            "pred": pred.tolist(),
            "base_rate": p,
            "majority": majority,
            "importance": {},
        }
    if model_id == "M1":
        from sklearn.linear_model import LogisticRegression

        clf = LogisticRegression(C=1.0, max_iter=200, solver="lbfgs", random_state=V10_SEED)
        clf.fit(xt, yt)
        proba = clf.predict_proba(xa)[:, 1]
        pred = (proba >= 0.5).astype(int)
        coef = clf.coef_[0].tolist() if getattr(clf, "coef_", None) is not None else []
        return {
            "proba": proba.tolist(),
            "pred": pred.tolist(),
            "importance": {"kind": "abs_coef", "values": [abs(c) for c in coef]},
        }
    if model_id == "M2":
        from sklearn.tree import DecisionTreeClassifier

        clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=20, random_state=V10_SEED)
        clf.fit(xt, yt)
        proba = clf.predict_proba(xa)[:, 1]
        pred = (proba >= 0.5).astype(int)
        return {
            "proba": proba.tolist(),
            "pred": pred.tolist(),
            "importance": {"kind": "gini", "values": clf.feature_importances_.tolist()},
        }
    if model_id == "M3":
        from sklearn.ensemble import RandomForestClassifier

        clf = RandomForestClassifier(
            n_estimators=20,
            max_depth=3,
            min_samples_leaf=20,
            random_state=V10_SEED,
            n_jobs=1,
        )
        clf.fit(xt, yt)
        proba = clf.predict_proba(xa)[:, 1]
        pred = (proba >= 0.5).astype(int)
        return {
            "proba": proba.tolist(),
            "pred": pred.tolist(),
            "importance": {"kind": "gini", "values": clf.feature_importances_.tolist()},
        }
    raise ValueError("UNKNOWN_MODEL")
