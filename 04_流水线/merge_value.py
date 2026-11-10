# -*- coding: utf-8 -*-
"""把三批判读合并成一个总盘 value_all.json。

批次：
  A 子渝批   48 行 / 41 有效（value.json）
  B 陈舒批   55 行 / 55 有效（value_cs.json）
  C 重点批    4 行 /  3 新增（value_focus.json）——四人指定重点，已按同一口径并入
字段：cust, line, f, o, l, v, concl, note, staff, focus
  staff 在第 9 位、focus 在第 10 位（放最后，前 8 位与三份原件完全一致）
  focus = 1 表示这一组是用户指定的重点线索

合并规则
--------
1. 只在「值」层面并，不改任何一组的判读；
2. 子渝批里 7 行「—」（没进入价值传递）保留在表里，staff 记为「子渝」，不计入分母；
3. 重点批的 4 组里有 1 组（姜彦博）与陈舒批是**同一份会话的两次导出**——
   96 条消息逐条相同，只是员工备注名不同（陈舒-pearrrr / 陈舒-？）。
   这一组只算 1 组：位置留在陈舒批，打上 focus 标记，不重复计入分母。
4. 姜彦博这一组两批判读不一致（陈舒批记 f3/o1/l0「缺落点」，重点批逐句读过记
   f3/o3/l1「三项全过」）。合并时以逐句细读的那一版为准，并在 note 里写明依据——
   这一处是「统一判读」，不是「挑一个对自己有利的」。
"""
import io
import json
import os

D = r"C:/Users/admin/Desktop/体德报告_子渝六阶段质检/02_过程文件"
OUT = os.path.join(D, "value_all.json")

A = json.load(open(os.path.join(D, "value.json"), encoding="utf-8"))["rows"]
B = json.load(open(os.path.join(D, "value_cs.json"), encoding="utf-8"))["rows"]
F = json.load(open(os.path.join(D, "value_focus.json"), encoding="utf-8"))["rows"]

# 重点批里已经存在于前两批的，按昵称去重
FOCUS_CUST = {r["cust"]: r for r in F}
DUP_IN_POOL = {"姜彦博"}          # 与陈舒批同一份会话，见文件头第 3 条

rows = []
for r in A:
    cust, line, f, o, l, v, concl, note = r[:8]
    rows.append([cust, line, f, o, l, v, concl, note, "子渝", 0])

for r in B:
    cust, line, f, o, l, v, concl, note = r[:8]
    if cust in DUP_IN_POOL:
        fr = FOCUS_CUST[cust]
        rows.append([cust, line, fr["f"], fr["o"], fr["l"], fr["veto"], "好", fr["note"], "陈舒", 1])
    else:
        rows.append([cust, line, f, o, l, v, concl, note, "陈舒", 0])

# 重点批里前两批没有的，作为新增行追在最后
# 会话里的昵称与报告里的写法不完全一样（导出侧写是「王永正  转介10.22」「UIN」），这里统一
NAME_OF_FOCUS = {"王永正  转介10.22": "王永正", "UIN": "李小东（UIN）", "銀河": "銀河"}
staff_of_focus = {"王永正": "邓杰均", "李小东（UIN）": "体德智训-小威", "銀河": "路梦丽"}
line_of_focus = {"王永正": "未定", "李小东（UIN）": "系统班", "銀河": "系统班"}
concl_of_focus = {"王永正": "差", "李小东（UIN）": "中", "銀河": "中"}
for fr in F:
    name = NAME_OF_FOCUS.get(fr["cust"], fr["cust"])
    if name in DUP_IN_POOL or any(name == x[0] for x in rows):
        continue
    rows.append([name, line_of_focus[name], fr["f"], fr["o"], fr["l"], fr["veto"],
                 concl_of_focus[name], fr["note"], staff_of_focus[name], 1])

# 重名检查：昵称撞车会让引语核对指错人
seen, dup = {}, []
for r in rows:
    k = r[0].strip()
    if k in seen:
        dup.append((k, seen[k], r[8]))
    seen[k] = r[8]

valid = [r for r in rows if r[1] != "—"]
n = len(valid)
f3 = sum(1 for r in valid if r[2] == 3)
o1 = sum(1 for r in valid if r[3] >= 1)
o2 = sum(1 for r in valid if r[3] >= 2)
l1 = sum(1 for r in valid if r[4] == 1)
st = sum(1 for r in valid if r[2] == 3 and r[3] >= 1 and r[4] == 1 and r[5] == 0)
vt = sum(1 for r in valid if r[5] == 1)
fo = sum(1 for r in valid if len(r) > 9 and r[9] == 1)

meta = {
    "n": n,
    "rows": len(rows),
    "f3": f3, "o1": o1, "o2": o2, "l1": l1, "strict": st, "veto": vt,
    "focus": fo,
    "by_staff": {
        "子渝": sum(1 for r in valid if r[8] == "子渝"),
        "陈舒": sum(1 for r in valid if r[8] == "陈舒"),
        "邓杰均": sum(1 for r in valid if r[8] == "邓杰均"),
        "体德智训-小威": sum(1 for r in valid if r[8] == "体德智训-小威"),
        "路梦丽": sum(1 for r in valid if r[8] == "路梦丽"),
    },
    "source": ["value.json（子渝 48 行 / 41 有效）",
               "value_cs.json（陈舒 55 行 / 55 有效）",
               "value_focus.json（重点 4 组，其中姜彦博与陈舒批同一份会话，去重后新增 3 组）"],
}

json.dump({"meta": meta, "rows": rows}, open(OUT, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("写出", OUT)
print("总行 %d ｜ 有效 %d（子渝 %d + 陈舒 %d + 新增重点 %d）"
      % (len(rows), n, meta["by_staff"]["子渝"], meta["by_staff"]["陈舒"],
         n - meta["by_staff"]["子渝"] - meta["by_staff"]["陈舒"]))
print("形态 %d ｜ 出口 %d（≥2 条 %d）｜ 落点 %d ｜ 三项全过 %d ｜ 否决 %d ｜ 重点 %d"
      % (f3, o1, o2, l1, st, vt, fo))
print("撞名：", dup if dup else "无")
