# -*- coding: utf-8 -*-
"""把线索表里的 CRM ID / 意向级别 回填进报告的案例头

报告卡片头长这样（骨架.html 里就是这么写的）：

    <span class="case-who">销售全名 → <b>客户昵称</b></span><span class="cid none">无 CRM ID</span>

本脚本按客户昵称去线索表里找对应的人，把 `无 CRM ID` 换成真 ID，并在后面补一个
意向级别小标签：

    <span class="cid" title="线索 ID 165541 ｜ 落入 2026-11-02 ｜ 官抖-短视频（广州）">165541</span>
    <span class="lvl" data-lv="C" title="意向级别 ｜ 1个月内未转化">C-意向较弱</span>

用法：

    python match_crm.py --xlsx "线索信息导出-20261109141615.xlsx" --html ../index.html --dry
    python match_crm.py --xlsx "线索信息导出-20261109141615.xlsx" --html ../index.html

    # 昵称和线索表姓名写法不同的，先写一张对照表再跑
    python match_crm.py --xlsx a.xlsx --html ../index.html --overrides overrides.json

    # 顺带导出人工复核用的对照表
    python match_crm.py --xlsx a.xlsx --html ../index.html --csv 02_过程文件/crm_map.csv

匹配顺序（先严后宽，宽的那步只对 ≥2 字的昵称生效）：

    1  --overrides 里人工指定的别名
    2  姓名归一化后精确相等（去空格 / 全半角 / 标点，英文转大写）
    3  微信列精确相等
    4  姓名互相包含且唯一命中（「波波📣工作版」↔「波波」这种）

匹配不上的**保持「无 CRM ID」不动**，脚本只把命中结果打出来。宁可空着，不要认错人——
ID 是给读者点开 CRM 核对的，认错等于把读者带到另一个人身上。

幂等：重跑会先拆掉上一轮写入的 `.lvl`、把带 title 的 `.cid` 复位成「无 CRM ID」，再重算。
"""
import argparse
import io
import json
import os
import re
import sys
import unicodedata

try:
    import openpyxl
except ImportError:
    sys.exit("缺 openpyxl：pip install openpyxl")

# ---- 页面结构 ----
META = re.compile(
    r'(?P<open><span class="case-who"[^>]*>)(?P<who>.*?)<b>(?P<name>.*?)</b></span>'
    r'(?P<cid><span class="cid[^"]*"(?:\s+title="[^"]*")?>[^<]*</span>)',
    re.S,
)
STALE_LVL = re.compile(r'<span class="lvl"[^>]*>[^<]*</span>')
FILLED_CID = re.compile(r'<span class="cid(?: warn)?"(?:\s+title="[^"]*")?>([^<]+)</span>')

PUNCT = re.compile(r"[\s\u3000，,。.、！!？?()（）\[\]【】<>《》\"'“”‘’~\-—_/\\|]+")
LV_KEY = re.compile(r"^([ABCD])")


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    return PUNCT.sub("", s).upper()


def load_rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        sys.exit("线索表是空的：%s" % path)
    hdr = [str(c).strip() if c else "" for c in rows[0]]
    need = [h for h in ("ID", "姓名") if h not in hdr]
    if need:
        sys.exit("线索表缺少列：%s（现有列：%s）" % ("、".join(need), " / ".join(hdr)))
    out = []
    for r in rows[1:]:
        d = dict(zip(hdr, r))
        for k in ("ID", "姓名", "微信", "意向级别", "线索落入日期", "线索来源", "跟进状态", "责任人"):
            v = d.get(k)
            d[k] = str(v).strip() if v is not None else ""
        if d["ID"]:
            out.append(d)
    return out


def build_index(rows):
    by_name, by_wx = {}, {}
    for d in rows:
        if d["姓名"]:
            by_name.setdefault(norm(d["姓名"]), []).append(d)
        wx = d["微信"]
        if wx and not wx.startswith("http") and not wx.endswith((".jpg", ".png")):
            by_wx.setdefault(norm(wx), []).append(d)
    return by_name, by_wx


def match(name, by_name, by_wx, overrides):
    raw = overrides.get(name, name)
    n = norm(raw)
    if n in by_name:
        return by_name[n][0], ("人工指定" if name in overrides else "姓名精确")
    if n in by_wx:
        return by_wx[n][0], "微信精确"
    if len(n) >= 2:
        cand = [k for k in by_name if k and len(k) >= 2 and (k in n or n in k)]
        if len(cand) == 1:
            return by_name[cand[0]][0], "姓名包含"
        if len(cand) > 1:
            return None, "多个候选（%s），请写 overrides" % "、".join(cand[:4])
    return None, "未命中"


def tag(rec, warn=False):
    lv = rec["意向级别"]
    key = LV_KEY.match(lv).group(1) if LV_KEY.match(lv) else ""
    title = "线索 ID %s" % rec["ID"]
    for label, val in (("落入", rec["线索落入日期"]), ("来源", rec["线索来源"])):
        if val:
            title += " ｜ %s %s" % (label, val)
    if warn:
        title = "线索表姓名记为「%s」，与报告昵称不同，按同日落入判定为同一人 ｜ %s" % (
            rec["姓名"], title)
    out = '<span class="cid%s" title="%s">%s</span>' % (" warn" if warn else "", title, rec["ID"])
    if key:
        out += '<span class="lvl" data-lv="%s" title="意向级别%s">%s</span>' % (
            key, (" ｜ " + rec["跟进状态"]) if rec["跟进状态"] else "", lv)
    return out


def run(args):
    if not os.path.isfile(args.xlsx):
        sys.exit("找不到线索表：%s\n  用法：--xlsx \"线索信息导出-20261109141615.xlsx\"" % args.xlsx)
    if not os.path.isfile(args.html):
        sys.exit("找不到报告：%s\n  用法：--html ../index.html" % args.html)
    if args.overrides and not os.path.isfile(args.overrides):
        sys.exit("找不到别名表：%s" % args.overrides)
    rows = load_rows(args.xlsx)
    by_name, by_wx = build_index(rows)
    overrides = {}
    if args.overrides:
        overrides = json.load(io.open(args.overrides, encoding="utf-8"))
        print("别名表：%s（%d 条）" % (args.overrides, len(overrides)))

    html = io.open(args.html, encoding="utf-8").read()
    # 幂等：先拆掉上一轮的标签
    html = STALE_LVL.sub("", html)
    html = FILLED_CID.sub('<span class="cid none">无 CRM ID</span>', html)

    stat, miss = {}, {}

    def repl(m):
        name = m.group("name")
        rec, how = match(name, by_name, by_wx, overrides)
        if not rec:
            key = "%s（%s）" % (name, how)
            miss[key] = miss.get(key, 0) + 1
            return m.group(0)
        stat[name] = (rec["ID"], rec["意向级别"], how)
        return "%s%s<b>%s</b></span>%s" % (
            m.group("open"), m.group("who"), name,
            tag(rec, warn=name in set(args.warn or [])))

    new = META.sub(repl, html)
    total = len(META.findall(html))
    left = len(re.findall(r'<span class="cid none">', new))

    print("案例头 %d 个 ｜ 回填 %d 处（%d 个客户）｜ 仍是「无 CRM ID」%d 处" % (
        total, total - left, len(stat), left))
    for name, (cid, lv, how) in sorted(stat.items(), key=lambda kv: kv[1][2]):
        print("  %-16s → %-8s %-10s %s" % (name, cid, lv or "（无线索级别）", how))
    if miss:
        print("未匹配（保持「无 CRM ID」）：")
        for k, c in miss.items():
            print("  %s ×%d" % (k, c))

    if args.csv and stat:
        lines = ["报告昵称,CRM ID,意向级别,匹配方式,线索落入日期,线索来源,跟进状态"]
        by_id = {d["ID"]: d for d in rows}
        for name, (cid, lv, how) in sorted(stat.items(), key=lambda kv: kv[1][0]):
            d = by_id.get(cid, {})
            lines.append(",".join(['"%s"' % name, cid, lv, how,
                                   d.get("线索落入日期", ""), '"%s"' % d.get("线索来源", ""),
                                   d.get("跟进状态", "")]))
        io.open(args.csv, "w", encoding="utf-8-sig", newline="").write("\n".join(lines) + "\n")
        print("对照表 → %s" % args.csv)

    if args.dry:
        print("--dry：没有写回文件")
        return 0
    if not stat:
        print("一条都没匹配上，不写文件。先检查 --xlsx 是不是这批数据的线索表。")
        return 1
    if args.backup:
        io.open(args.html + ".bak", "w", encoding="utf-8", newline="").write(
            io.open(args.html, encoding="utf-8").read())
        print("备份 → %s.bak" % args.html)
    io.open(args.html, "w", encoding="utf-8", newline="").write(new)
    print("已写回 %s（改 %d 处）" % (args.html, len(stat)))
    return 0


def main():
    ap = argparse.ArgumentParser(description="回填 CRM ID 与意向级别")
    ap.add_argument("--xlsx", required=True, help="线索信息导出-*.xlsx")
    ap.add_argument("--html", required=True, help="要改的报告 html（就地改写）")
    ap.add_argument("--overrides", help="别名 JSON：{\"报告昵称\": \"线索表姓名\"}")
    ap.add_argument("--csv", help="导出对照表 CSV 的路径")
    ap.add_argument("--warn", nargs="*", default=[], help="ID 用虚线框标出、提示人工确认的昵称")
    ap.add_argument("--backup", action="store_true", help="写回前留一份 .bak")
    ap.add_argument("--dry", action="store_true", help="只打印结果，不改文件")
    raise SystemExit(run(ap.parse_args()))


if __name__ == "__main__":
    main()
