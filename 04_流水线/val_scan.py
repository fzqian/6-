# -*- coding: utf-8 -*-
"""价值传递专项：48 组逐组抽证据，供人判读（脚本不判定）。

只看 48 组客户对话（排除内部同事），按 facts.json 的顺序。
客户侧：只留带需求/价格/疑问/决策的句子。
销售侧：只留命中形态 / 出口 / 落点 / 价格四类词的消息（同类去重）。

用法：python val_scan.py [起] [止]
"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = {g["cust"]: g for g in json.load(open("dialogs_W.json", encoding="utf-8"))}
F = json.load(open("facts.json", encoding="utf-8"))
ORDER = [f["cust"] for f in F]

CUST_KEY = re.compile(r"钱|费|价|多少钱|贵|便宜|学什么|教什么|课程|证书|考|就业|工作|"
                      r"时间|上班|基础|零|想|打算|准备|可以|能不能|有没有|怎么样|"
                      r"什么时候|哪里|哪个|多久|几个月|住宿|宿舍|吃|住")
FORM = re.compile(r"三个月|3个月|线上|九个月|9个月|复训|四个阶段|课程体系|解剖|营养|"
                  r"动作模式|体态|周期|理论|实操|体能|线下培训")
EXIT = re.compile(r"就业|上岗|门店|推荐|月薪|薪资|工资|收入|起薪|面试|用人单位|"
                  r"发证|颁发|认证|人社局|体育总局|含金量|认可|包")
LAND = re.compile(r"你说|你的情况|你的目标|你想|你要|你刚|按你|结合你|你是|你的基础|适合你")
MONEY = re.compile(r"\d{4,5}|优惠|减免|订金|定金|便宜|折扣|双十一")


def short(s, n=88):
    s = re.sub(r"\s+", " ", s.replace("\n", " ")).strip()
    return s if len(s) <= n else s[:n] + "…"


def main():
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    for k, cust in enumerate(ORDER[a:b], start=a + 1):
        g = D[cust]
        ms = g["msgs"]
        print("\n" + "=" * 76)
        print("[%02d] %s ｜ %d 条" % (k, cust, g["n"]))
        cs = [m for m in ms if m["who"] == "C" and len(m["x"]) >= 2]
        keep = [m for m in cs if CUST_KEY.search(m["x"])]
        if len(keep) < 4:
            keep = cs[:6]
        if len(keep) > 14:
            step = len(keep) / 14.0
            keep = [keep[int(i * step)] for i in range(14)]
        print(" C:", " ／ ".join(short(m["x"], 46) for m in keep))
        seen = set()
        rows = []
        for m in ms:
            if m["who"] != "S":
                continue
            tg = ""
            if FORM.search(m["x"]):
                tg += "形"
            if EXIT.search(m["x"]):
                tg += "出"
            if LAND.search(m["x"]):
                tg += "落"
            if MONEY.search(m["x"]):
                tg += "价"
            if not tg:
                continue
            key = short(m["x"], 30)
            if key in seen:
                continue
            seen.add(key)
            rows.append("  %-4s %s ｜ %s" % (tg, m["t"][-11:], short(m["x"], 100)))
        if len(rows) > 20:
            step = len(rows) / 20.0
            rows = [rows[int(i * step)] for i in range(20)]
        print(" S:")
        for r in rows:
            print(r)


if __name__ == "__main__":
    main()
