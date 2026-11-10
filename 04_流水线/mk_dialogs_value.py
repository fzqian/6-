# -*- coding: utf-8 -*-
"""把三批对话并成一份 dialogs_value.json，专供价值传递页做核对。

为什么需要它：页面现在同时引用了子渝批、陈舒批、重点四组三批人的原话。
check.py 的第 12 项（引号外断言）和第 13 项（片段库漏斗）都要拿原文核对，
只喂 subyev 那一批，就会把「王永正」「李小东」判成「数据里找不到」。

顺带把会话里的昵称统一成页面上的写法（导出侧写是「王永正  转介10.22」「UIN」）。
"""
import json
import os
import sys

D = r"C:/Users/admin/Desktop/体德报告_子渝六阶段质检/02_过程文件"
SRC = ["dialogs_W.json", "dialogs_cs.json", "dialogs_focus.json"]
OUT = os.path.join(D, "dialogs_value.json")

RENAME = {"王永正  转介10.22": "王永正", "UIN": "李小东（UIN）"}

out, seen = [], {}
for fn in SRC:
    for g in json.load(open(os.path.join(D, fn), encoding="utf-8")):
        name = RENAME.get(g["cust"], g["cust"])
        if name in seen:
            # 同名多次导出：留消息更多的那一份
            if len(g["msgs"]) > len(seen[name]["msgs"]):
                out[out.index(seen[name])] = g
                seen[name] = g
            continue
        seen[name] = g
        out.append(g)

for g in out:
    g["cust"] = RENAME.get(g["cust"], g["cust"])

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("写出", OUT, "｜ 会话", len(out), "组 ｜ 条数",
      sum(len(g["msgs"]) for g in out))
