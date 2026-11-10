# -*- coding: utf-8 -*-
"""把「02_按客户拆分」的 txt 转成 dialogs_all.json（截图脚本和报告都吃这个）。

用法：
  python to_dialogs.py "C:/Users/admin/Desktop/体德聊天记录汇总/02_按客户拆分"
  python to_dialogs.py <目录> --out dialogs_all.json

输入两类都支持：
  A. 带文件头（02_ 目录的标准格式）
       # 销售：体德-志恒【广州 长沙 南京 成都】
       # 客户：DBR
       ·DBR
       2026年8月27日 13:53
       我通过了你的朋友验证请求
  B. 不带文件头的原始导出（01_ 目录）
       ·体德智训-阿牛
       2026年9月14日 22:56
       正文

输出结构：
  [{"sales": "...", "cust": "...", "src": "文件名", "n": 28,
    "start": "2026年8月27日 13:53", "end": "...",
    "msgs": [{"who": "S"|"C", "t": "2026年8月27日 13:53", "x": "正文"}]}]
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TS = re.compile(r"^(\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2})$")
H_SALES = re.compile(r"^#\s*销售[：:]\s*(.+)$")
H_CUST = re.compile(r"^#\s*客户[：:]\s*(.+)$")
SALES_HINT = re.compile(r"体德|智训|学院")


def time_key(t):
    """'2026年3月8日 11:07' → (2026, 3, 8, 11, 7)，可直接排序。"""
    return tuple(int(x) for x in re.findall(r"\d+", t))


def parse_file(path):
    """返回 [{sales, cust, src, msgs}]，一个文件可能含多个客户。"""
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    sales_hint = cust_hint = None
    msgs = []

    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        m = H_SALES.match(s)
        if m:
            sales_hint = m.group(1).strip()
            i += 1
            continue
        m = H_CUST.match(s)
        if m:
            cust_hint = m.group(1).strip()
            i += 1
            continue
        if s.startswith("#"):
            i += 1
            continue
        # 消息块：·昵称 + 下一行时间 + 正文
        if s.startswith("·") and i + 1 < len(lines) and TS.match(lines[i + 1].strip()):
            name = s[1:].strip()
            t = lines[i + 1].strip()
            body, j = [], i + 2
            while j < len(lines):
                t2 = lines[j].strip()
                if t2.startswith("·") and j + 1 < len(lines) and TS.match(lines[j + 1].strip()):
                    break
                if t2:
                    body.append(t2)
                j += 1
            if body:
                msgs.append({"name": name, "t": t, "x": " / ".join(body)})
            i = j
            continue
        i += 1

    if not msgs:
        return []

    # 剔除「[聊天记录]」转发占位：它带的是转发那一刻的时间，不是对话时间。
    # 微信「合并转发」导出的 txt，首条永远是 转发人 + 转发时间 + [聊天记录]，
    # 不剔掉会把时间跨度算错（实测 3/8→5/8 的一段被算成 3/8→11/5）。
    msgs = [m for m in msgs if m["x"].strip() != "[聊天记录]"]
    if not msgs:
        return []

    src = os.path.basename(path)

    # 没有文件头时按昵称频次判断销售
    if not sales_hint:
        cnt = Counter(m["name"] for m in msgs)
        cand = [n for n in cnt if SALES_HINT.search(n)]
        sales_hint = max(cand, key=lambda n: cnt[n]) if cand else msgs[0]["name"]

    sales = sales_hint
    names = []
    for m in msgs:
        if m["name"] not in names:
            names.append(m["name"])

    # 客户：优先用文件头；否则取除销售外消息最多的昵称（剔除名片残留）
    if cust_hint:
        custs = [cust_hint] if cust_hint in names else []
        if not custs:
            custs = [cust_hint]
    else:
        rest = [n for n in names if n != sales]
        cnt = Counter(m["name"] for m in msgs)
        rest = [n for n in rest if not (SALES_HINT.search(n) and cnt[n] <= 2)]
        custs = [max(rest, key=lambda n: cnt[n])] if rest else []

    out = []
    for c in custs:
        sub = [m for m in msgs if m["name"] in (sales, c)]
        if not sub:
            continue
        out.append({
            "sales": sales,
            "cust": c,
            "src": src,
            "n": len(sub),
            "start": sub[0]["t"],
            "end": sub[-1]["t"],
            "msgs": [{"who": "S" if m["name"] == sales else "C", "t": m["t"], "x": m["x"]} for m in sub],
        })
    return out


def main():
    ap = argparse.ArgumentParser(description="txt → dialogs_all.json")
    ap.add_argument("dir", help="txt 所在目录（02_按客户拆分 或 01_原始导出文件）")
    ap.add_argument("--out", default="dialogs_all.json")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.dir, "*.txt")))
    if not files:
        print("目录里没有 .txt：%s" % a.dir)
        return 2

    all_d, bad = [], []
    for f in files:
        try:
            r = parse_file(f)
        except Exception as e:
            bad.append((os.path.basename(f), str(e)))
            continue
        if not r:
            bad.append((os.path.basename(f), "拆不出消息"))
            continue
        all_d.extend(r)

    # 同（销售,客户）跨文件合并
    merged, order = {}, []
    for d in all_d:
        k = (d["sales"], d["cust"])
        if k not in merged:
            merged[k] = d
            order.append(k)
        else:
            merged[k]["msgs"].extend(d["msgs"])
            merged[k]["src"] += " + " + d["src"]

    final = []
    for k in order:
        d = merged[k]
        seen, uniq = set(), []
        for m in d["msgs"]:
            sig = (m["who"], m["t"], m["x"])
            if sig in seen:
                continue
            seen.add(sig)
            uniq.append(m)
        # 多文件合并后必须按真实时间重排。微信导出时间是「2026年3月8日 11:07」
        # 这种不补零格式，不能直接比字符串（3月会排到11月后面），要拆成数字元组。
        uniq.sort(key=lambda m: time_key(m["t"]))
        d["msgs"] = uniq
        d["n"] = len(uniq)
        d["start"] = uniq[0]["t"]
        d["end"] = uniq[-1]["t"]
        final.append(d)

    final.sort(key=lambda z: -z["n"])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(final, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    tot = sum(d["n"] for d in final)
    print("文件 %d 个 → %d 组 / %d 条消息" % (len(files), len(final), tot))
    print("输出：%s" % os.path.abspath(a.out))
    for d in final[:15]:
        print("  %-22s %4d 条  %s" % (d["cust"][:22], d["n"], d["sales"][:24]))
    if len(final) > 15:
        print("  …… 另有 %d 组" % (len(final) - 15))
    if bad:
        print("\n跳过 %d 个文件：" % len(bad))
        for f, why in bad[:10]:
            print("  %-50s %s" % (f[:50], why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
