from __future__ import print_function
import re
import xlrd

book = xlrd.open_workbook("D:/tmp/czce_wh.xls")
sh = book.sheet_by_index(0)
pat = re.compile(r"品种[：:]\s*(\S+?)([A-Z]{1,3})\b")
for i in range(sh.nrows):
    a = str(sh.cell_value(i, 0))
    if "品种" in a or a.startswith("总计") or a.startswith("合计") or a.startswith("小计"):
        row = [sh.cell_value(i, j) for j in range(min(7, sh.ncols))]
        if "品种" in a or a in ("总计", "合计"):
            print(i, row)
