import json
import os
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DataLayerLogger(object):
    def __init__(self, log_path):
        self.log_path = log_path
        directory = os.path.dirname(log_path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)

    def emit(self, event, **fields):
        record = {"event": event, "logged_at_utc": utc_now()}
        record.update(fields)
        line = json.dumps(record, ensure_ascii=True, sort_keys=True)
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        print(line)
        return record
