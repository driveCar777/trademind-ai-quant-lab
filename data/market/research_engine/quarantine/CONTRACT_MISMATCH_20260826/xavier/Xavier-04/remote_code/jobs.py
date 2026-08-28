from __future__ import print_function

from research_engine.experiments import experiment_contract, experiment_hash


def experiment_payload(fields):
    payload = {
        "experiment_id": fields["experiment_id"],
        "hypothesis_id": fields["hypothesis_id"],
        "family_id": fields["family_id"],
        "dataset_id": fields["dataset_id"],
        "dataset_sha256": fields["dataset_sha256"],
        "preregister_hash": fields["preregister_hash"],
        "protocol_hash": fields["protocol_hash"],
        "feature_registry_hash": fields["feature_registry_hash"],
        "execution_hash": fields["execution_hash"],
        "window_hash": fields["window_hash"],
        "cost_hash": fields["cost_hash"],
        "code_hash": fields["code_hash"],
        "node_assignment": fields["node_assignment"],
        "created_at": fields["created_at"],
        "status": fields.get("status", "LOCKED"),
        "seed": fields["seed"],
    }
    experiment_contract(payload)
    payload["experiment_hash"] = experiment_hash(payload)
    return payload
