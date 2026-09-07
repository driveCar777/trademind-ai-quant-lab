"""One-off probe. Not the contract runner."""
from __future__ import print_function

import json
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))
req = urllib.request.Request(
    "https://www.shfe.com.cn/data/tradedata/future/dailydata/20240229dailystock.dat",
    headers={"User-Agent": "Mozilla/5.0"},
)
j = json.loads(opener.open(req, timeout=20).read())
sep = "$$"
names = sorted(set(x["VARNAME"].split(sep)[0] for x in j["o_cursor"]))
eng = sorted(set((x["VARNAME"].split(sep) + [""])[1] for x in j["o_cursor"]))
print("cn", names)
print("en", eng)
print("n_rows", len(j["o_cursor"]))
# totals: rows whose warehouse name looks like a sum line
for x in j["o_cursor"][:8]:
    print(x.get("VARNAME"), x.get("WRTWGHTS"), x.get("WRTWGHTS") or x.get("WEIGHT"))
print("keys", sorted(j["o_cursor"][0].keys()))
