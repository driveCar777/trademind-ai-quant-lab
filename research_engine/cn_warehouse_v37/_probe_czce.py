"""Parse one CZCE warehouse xls. Not the runner."""
from __future__ import print_function

import ssl
import urllib.request

import xlrd

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))
url = "https://www.czce.com.cn/cn/DFSStaticFiles/Future/2024/20240902/FutureDataWhsheet.xls"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.czce.com.cn/"})
raw = opener.open(req, timeout=20).read()
path = "D:/tmp/czce_wh.xls"
open(path, "wb").write(raw)
book = xlrd.open_workbook(path)
print("sheets", book.sheet_names())
for name in book.sheet_names()[:6]:
    sh = book.sheet_by_name(name)
    print("SHEET", name, sh.nrows, sh.ncols)
    for i in range(min(12, sh.nrows)):
        print(i, [sh.cell_value(i, j) for j in range(min(8, sh.ncols))])
