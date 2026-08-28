"""Paid / credential adapters. Never pretend data exists."""
from __future__ import print_function

import os

from research_engine.data_sources import ENV_DATABENTO, ENV_ORATS, ENV_TE
from research_engine.data_sources.pipeline import AcquisitionBlocked


class BlockedAdapter(object):
    def __init__(self, source, env_name, reason):
        self.source = source
        self.env_name = env_name
        self.reason = reason

    def status(self, spec=None):
        if os.environ.get(self.env_name):
            return "CREDENTIAL_PRESENT_NOT_FETCHED"
        return "CREDENTIAL_REQUIRED"

    def fetch(self, spec):
        raise AcquisitionBlocked("%s:%s" % (self.source, self.reason))

    def normalize(self, raw, spec):
        raise AcquisitionBlocked(self.source)

    def timestamp(self, row, spec):
        raise AcquisitionBlocked(self.source)

    def validate(self, rows, spec):
        raise AcquisitionBlocked(self.source)


DATABENTO = BlockedAdapter(
    "databento",
    ENV_DATABENTO,
    "Need TRADEMIND_DATABENTO_API_KEY. Do not scrape. Sign up at databento.com.",
)
ORATS = BlockedAdapter(
    "orats",
    ENV_ORATS,
    "Need paid near-EOD archive or API key. GLD/USO are ETF proxies, not XAU/WTI listed options.",
)
TRADING_ECONOMICS = BlockedAdapter(
    "trading_economics",
    ENV_TE,
    "Consensus/forecast calendar is paid. Actuals alone are not surprise. Do not fabricate consensus.",
)
