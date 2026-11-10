# -*- coding: utf-8 -*-
"""企业微信会话导出 xlsx → dialogs_all.json

与 to_dialogs.py（微信「合并转发」txt）的区别：这份是企微后台/工具导出的表格，
一条消息一行，字段干净、时间到秒，但有三处必须处理：

1. 行序是倒的（最新在最上）
2. 时间格式 "2026-11-08 20:45:41"，渲染器要 "2026年11月8日 20:45"（不补零）
3. 引用回复被拼进正文：``“李雅雯：\\n原话”\\n------\\n回复``

用法：
  python xlsx2dialogs.py --xlsx "C:/.../会话消息.xlsx" --out dialogs_all.json
  python xlsx2dialogs.py --xlsx a.xlsx --xlsx b.xlsx --out dialogs_all.json   # 多份合并
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

import openpyxl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 列名候选：不同导出版本叫法略有差异
COLS = {
    "who": ("发送人身份", "发送人角色", "身份"),
    "name": ("发送人", "发送者", "昵称"),
    "text": ("会话内容", "消息内容", "内容"),
    "time": ("发送时间", "时间", "消息时间"),
    "cust": ("客户备注名", "客户昵称"),
    "sales": ("会话信息",),
}
EMP = ("员工", "销售", "客服", "企业成员", "内部")
# 企微的 [表情] 映射成微信写法的 [动画表情]，复用渲染器的跳过规则
NORMALIZE = {
    "[表情]": "[动画表情]",
    "[动画表情]": "[动画表情]",
    "[图片]": "[图片]",
    "[语音]": "[语音]",
}
QUOTE = re.compile(r'^[“"]([^\n：:]{1,60})[：:]\s*\n(.*?)[”"]\s*\n-{3,}\s*\n?(.*)$', re.S)


def pick(header, key):
    for c in COLS[key]:
        if c in header:
            return header.index(c)
    return None


def fmt_time(t):
    """'2026-11-08 20:45:41' / datetime → '2026年11月8日 20:45'（不补零，与微信导出一致）"""
    if isinstance(t, datetime):
        return "%d年%d月%d日 %02d:%02d" % (t.year, t.month, t.day, t.hour, t.minute)
    s = str(t).strip()
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})[ T](\d{1,2}):(\d{2})", s)
    if m:
        y, mo, d, h, mi = (int(x) for x in m.groups())
        return "%d年%d月%d日 %02d:%02d" % (y, mo, d, h, mi)
    return s


def time_key(t):
    return tuple(int(x) for x in re.findall(r"\d+", t))


def unquote(text):
    """把「引用 + 回复」压成一条：'（引“下午过去”）好的，大概下午几点过来呢'
    不写发言人——气泡颜色已经标明是谁说的；只留被引用的那句，超过 24 字截断。"""
    m = QUOTE.match(text.strip())
    if not m:
        return text
    quoted, body = m.group(2).strip(), m.group(3).strip()
    quoted = re.sub(r"\[[^\]]{1,8}\]", " ", quoted)          # 去掉 [小程序] 这类前缀
    quoted = re.sub(r"\s+", " ", quoted).strip()
    if len(quoted) > 24:
        quoted = quoted[:24] + "…"
    return ("（引“%s”）%s" % (quoted, body)) if quoted else body


def read_one(path):
    """读一份 xlsx，返回 [(group, dropped), ...]。
    一个文件里可能有多位客户（企微后台按员工导出时会打包全部会话），
    所以按「会话信息」列拆分；拆不出来就退回单组。"""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise SystemExit("空表：%s" % path)
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    ix = {k: pick(header, k) for k in COLS}
    miss = [k for k in ("who", "text", "time") if ix[k] is None]
    if miss:
        raise SystemExit("缺关键列 %s，实际表头：%s" % (miss, header))

    body = rows[1:]
    # 表是倒序的，先转正序；同秒的消息靠原顺序保证不乱
    body = list(reversed(body))
    # 按原始时间戳排序（原始列是零补齐的，或至少能拆出数字元组）；
    # 绝不能按 fmt_time 后的字符串排——"10月"会排到"9月"前面
    body.sort(key=lambda r: time_key(str(r[ix["time"]] or "")))

    # 销售名：发送人里身份为员工的、出现次数最多的那个
    sales = None
    if ix["sales"] is not None:
        c = {}
        for r in body:
            if str(r[ix["who"]] or "").strip() in EMP and r[ix["sales"]]:
                c[str(r[ix["sales"]]).strip()] = c.get(str(r[ix["sales"]]).strip(), 0) + 1
        if c:
            sales = max(c, key=c.get)
    if sales and sales.count("-") >= 2:
        # "体德智训-子渝（广州南京长沙）-李雅雯" → 只留销售那两段
        sales = "-".join(sales.split("-")[:2])

    # 按会话拆桶（保持已排好的时间顺序）
    buckets = {}
    order = []
    for r in body:
        sess = str(r[ix["sales"]] or "").strip() if ix["sales"] is not None else ""
        k = sess or "__all__"
        if k not in buckets:
            buckets[k] = []
            order.append(k)
        buckets[k].append(r)

    out = []
    for k in order:
        msgs, dropped = [], {"空内容": 0, "撤回": 0}
        cust = None
        for r in buckets[k]:
            txt = "" if r[ix["text"]] is None else str(r[ix["text"]]).strip()
            if ix["cust"] is not None and not cust and r[ix["cust"]]:
                cust = str(r[ix["cust"]]).strip()
            if not txt:
                dropped["空内容"] += 1
                continue
            if "撤回了一条消息" in txt:
                dropped["撤回"] += 1
                continue
            ident = str(r[ix["who"]] or "").strip()
            msgs.append({
                "who": "S" if ident in EMP else "C",
                "t": fmt_time(r[ix["time"]]),
                "x": NORMALIZE.get(txt, unquote(txt)),
            })
        if not msgs:
            continue
        msgs.sort(key=lambda m: time_key(m["t"]))
        # 客户名优先用会话信息里销售名之后的那一段（最准），再退回备注名列
        name = None
        if sales and k.startswith(sales + "-"):
            name = k[len(sales) + 1:].strip()
        name = name or cust or "客户"
        out.append(({
            "sales": sales or "未知销售",
            "cust": name,
            "src": os.path.basename(path),
            "n": len(msgs),
            "start": msgs[0]["t"],
            "end": msgs[-1]["t"],
            "msgs": msgs,
        }, dropped))
    return out


def main():
    ap = argparse.ArgumentParser(description="企微会话 xlsx → dialogs_all.json")
    ap.add_argument("--xlsx", action="append", required=True, help="xlsx 路径，可重复")
    ap.add_argument("--out", default="dialogs_all.json")
    ap.add_argument("--cust", default=None, help="强制指定客户名（默认取「客户备注名」列）")
    a = ap.parse_args()

    groups = []
    for p in a.xlsx:
        gs = read_one(p)
        dt = {"空内容": 0, "撤回": 0}
        for g, dropped in gs:
            if a.cust:
                g["cust"] = a.cust
            for k2 in dt:
                dt[k2] += dropped[k2]
        print("✓ %s" % os.path.basename(p))
        print("   %d 个会话 ｜ %d 条消息 ｜ 丢弃 %s"
              % (len(gs), sum(g["n"] for g, _ in gs), dt))
        for g, _ in gs:
            print("     %-14s %4d 条  %s → %s" % (g["cust"][:14], g["n"], g["start"][:11], g["end"][:11]))
        groups += [g for g, _ in gs]

    # 同一客户多份文件合并
    merged = {}
    for g in groups:
        k = g["cust"]
        if k in merged:
            merged[k]["msgs"] += g["msgs"]
            merged[k]["msgs"].sort(key=lambda m: time_key(m["t"]))
            merged[k]["n"] = len(merged[k]["msgs"])
            merged[k]["start"] = merged[k]["msgs"][0]["t"]
            merged[k]["end"] = merged[k]["msgs"][-1]["t"]
        else:
            merged[k] = g

    out = list(merged.values())
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n写出 %s：%d 组" % (a.out, len(out)))
    for g in out:
        print("   %-14s %4d 条  %s" % (g["cust"], g["n"], g["sales"][:26]))


if __name__ == "__main__":
    main()
