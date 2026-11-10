# -*- coding: utf-8 -*-
"""PART 04 片段库核查：漏斗四个数字能不能复算，六段片段是不是真出自这批数据。

为什么要这个脚本：片段库的「48 → 31 → 20 → 6」写在页面上，读者会当作事实。
只要有一个数字是估的、或者标签跟算法对不上，整套「有出处」的可信度就没了。
（2026-11-09 就出过一次：页面上写「15 组讲清了形态和出口」，实际 15 是
「报了数字且形态两件以上」的组数，出口根本不在这个口径里。）

用法：
    python audit_good.py index.html --data dialogs_W.json [--facts facts.json]
    python audit_good.py            # 只看数，不比对 HTML
"""
import json
import os
import re
import sys

# ---------- 口径（改这里必须同步改页面上的标签） ----------
PRICE = re.compile(r"多少钱|费用|价格|学费|收费|报价|多少|贵")          # 客户主动问价
COURSE = re.compile(r"学什么|课程|教什么|都教|考什么|学哪些|证书|内容")   # 客户问课程（只做参考）
FORM3 = re.compile(r"三个月|3个月")                                    # 形态第一件：时长
FORM2 = re.compile(r"线上|九个月|9个月|复训|四个阶段")                  # 形态第二件：线上或复训
JOB = re.compile(r"就业|上岗|推荐.{0,6}(门店|工作|就业)|安排.{0,4}工作|面试")
PAY = re.compile(r"月薪|薪资|工资|收入|起薪|\d{4,5}\s*[-~到]\s*\d{4,5}")
CERT = re.compile(r"颁发|发证|国家.{0,4}认证|人社|体育总局|证书.{0,6}(认可|通用|查询)")


def load(data, facts):
    D = json.load(open(data, encoding="utf-8"))
    D = {g["cust"]: g for g in D}
    F = {f["cust"]: f for f in json.load(open(facts, encoding="utf-8"))}
    return D, F


def side(g, who):
    return " ".join(m["x"] for m in g["msgs"] if m["who"] == who)


def funnel(D, F):
    """四步：全部 → 客户问过价 → 报了数字且讲了形态或出口 → 人工入选。

    第三步是前两步的子集；第四步（6）是人工挑的，脚本只能核「这几组在不在池子里」。
    """
    allg = list(F)
    s2 = [n for n in allg if PRICE.search(side(D[n], "C"))]
    s3 = [n for n in s2 if F[n]["amt"]
          and ((FORM3.search(side(D[n], "S")) and FORM2.search(side(D[n], "S")))
               or JOB.search(side(D[n], "S")) or PAY.search(side(D[n], "S"))
               or CERT.search(side(D[n], "S")))]
    form2 = [n for n in s3
             if FORM3.search(side(D[n], "S")) and FORM2.search(side(D[n], "S"))]
    course_only = [n for n in allg if COURSE.search(side(D[n], "C"))]
    return allg, s2, s3, form2, course_only


def parse_qfun(h):
    """从 HTML 里切出 .qfun 那一段，取四个 (数字, 标签)。"""
    i = h.find('class="qfun')
    if i < 0:
        return [], []
    j = h.find('<p class="lead', i)
    block = h[i:j if j > 0 else i + 2000]
    pairs = re.findall(r"<b>\s*([^<]+?)\s*</b>\s*<span>([^<]*)</span>", block)
    return [a for a, _ in pairs], [b.strip() for _, b in pairs]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    data = "dialogs_value.json" if os.path.exists("dialogs_value.json") else "dialogs_W.json"
    facts = "facts.json"
    if "--data" in sys.argv:
        data = sys.argv[sys.argv.index("--data") + 1]
    if "--facts" in sys.argv:
        facts = sys.argv[sys.argv.index("--facts") + 1]
    if not os.path.exists(data):
        _base = os.path.dirname(os.path.abspath(src or "."))
        for _n in ("dialogs_value.json", "dialogs_W.json"):
            _c = os.path.join(_base, "02_过程文件", _n)
            if os.path.isfile(_c):
                data = _c
                break
        else:
            data = os.path.join(_base, "02_过程文件", "dialogs_value.json")
    if not os.path.exists(facts):
        facts = os.path.join(os.path.dirname(data), "facts.json")

    D, F = load(data, facts)

    # 第二个人（陈舒批）：片段卡来自另一份导出，单独取原文与判读结果来核
    CS, CSV = {}, {}
    _d = os.path.dirname(os.path.abspath(data))
    _p = os.path.join(_d, "dialogs_cs.json")
    _v = os.path.join(_d, "value_cs.json")
    if os.path.isfile(_p):
        CS = {g["cust"]: g for g in json.load(open(_p, encoding="utf-8"))}
    if os.path.isfile(_v):
        CSV = {r[0]: r for r in json.load(open(_v, encoding="utf-8"))["rows"]}

    # 重点四组：卡片头的「形态 ● ● ● ｜ 出口 N 条 ｜ 落点 ✓」必须等于 value_focus.json
    FOC = {}
    _fv = os.path.join(_d, "value_focus.json")
    if os.path.isfile(_fv):
        FOC = {r["cust"]: {"staff": r["staff"], "f": r["f"], "o": r["o"], "l": r["l"]}
               for r in json.load(open(_fv, encoding="utf-8"))["rows"]}
        # 导出侧写的昵称和页面写法不一致（王永正  转介10.22 / UIN），按页面名再挂一份
        FOC["王永正"] = FOC.get("王永正  转介10.22", FOC.get("王永正"))
        FOC["李小东（UIN）"] = FOC.get("UIN", FOC.get("李小东（UIN）"))
        FOC = {k: v for k, v in FOC.items() if v}
    allg, s2, s3, form2, course_only = funnel(D, F)

    print("口径复算（%s 组）" % len(allg))
    print("  ① 全部通读              %2d" % len(allg))
    print("  ② 客户主动问过价        %2d" % len(s2))
    print("  ③ 报了数字且讲形态/出口 %2d  （其中形态两件以上 %d）" % (len(s3), len(form2)))
    print("  参考：客户问过课程/证书 %2d（与②并集 %d）"
          % (len(course_only), len(set(s2) | set(course_only))))

    if not src:
        return 0

    h = open(src, encoding="utf-8").read()
    pnums, plabels = parse_qfun(h)
    print("\n页面 .qfun 实际写的：")
    for n, l in zip(pnums, plabels):
        print("  %-4s %s" % (n, l))

    want = [str(len(allg)), str(len(s2)), str(len(s3)), None]
    bad = []
    for i in range(3):
        if i < len(pnums) and pnums[i] != want[i]:
            bad.append("第 %d 步写的是 %s，复算是 %s" % (i + 1, pnums[i], want[i]))

    # 标签与口径是否对得上（这几个词是各自算法的指纹）
    if plabels:
        if "课程" in plabels[1] and len(s2) != len(set(s2) | set(course_only)):
            bad.append("第二步标签写了「或课程」，但数字只是问价的组数（问价+课程并集是 %d）"
                       % len(set(s2) | set(course_only)))
        if "出口" in plabels[2] and pnums[2] == str(len(form2)):
            bad.append("第三步标签写了「形态和出口」，数字其实是形态两件以上的 %d 组" % len(form2))

    # 六段片段：客户名必须在数据里，且必须落在第三步的池子里
    _g, _b = h.find('id="good"'), h.find('id="bad"')
    _window = h[_g:_b] if _g > 0 and _b > _g else h     # 只数 V4「做对的」那一段
    six = re.findall(r'<div class="qcard-meta">([^｜<]+)｜', _window)
    print("\n六段片段出自：")
    for i, cust in enumerate([c.strip() for c in six], 1):
        cust = re.sub(r"\s+", "", cust)
        hit = next((n for n in D if re.sub(r"\s+", "", n) == cust), None)
        if not hit:
            csh = next((n for n in CS if re.sub(r"\s+", "", n) == cust), None)
            if csh:
                print("  片段%-2d %-12s %2d 条  池内（陈舒批，已并入 99 组）"
                      % (i, csh, CS[csh]["n"]))
                continue
            bad.append("片段%d 的客户「%s」在数据里找不到" % (i, cust))
            continue
        if hit in s3:
            p = "池内"
        elif hit not in F:
            p = "池内（其他批，已并入 99 组）"
        else:
            p = "池外（单考证/其他场景，需在页面上说明）"
        print("  片段%-2d %-12s %2d 条  %s" % (i, hit, len(D[hit]["msgs"]), p))

    # 陈舒批卡片的三个标签（形态● ● ● / 出口 N 条 / 落点 ✓）必须与 value_cs.json 一致
    if CSV:
        for m in re.finditer(r'<div class="qcard-meta">([^｜<]+)｜[^<]*?形态([●○ ]+)｜\s*出口\s*(\d+)\s*条'
                             r'｜\s*落点\s*(✓|✗)', h):
            nm = re.sub(r"\s+", "", m.group(1))
            row = next((r for k, r in CSV.items() if re.sub(r"\s+", "", k) == nm), None)
            if not row:
                continue
            dots = m.group(2).count("●")
            if dots != row[2] or int(m.group(3)) != row[3] or (m.group(4) == "✓") != bool(row[4]):
                bad.append("陈舒批「%s」卡片标签与 value_cs.json 不一致（页 %d/%s/%s，数据 %d/%d/%d）"
                           % (nm, dots, m.group(3), m.group(4), row[2], row[3], row[4]))

    # 重点四组卡片标签：客户名 + 形态点数 + 出口条数 + 落点，四项齐对
    if FOC:
        for m in re.finditer(r'<div class="qcard-meta">([^｜<]+)｜([^｜<]+)｜[^<]*?形态([●○ ]+)'
                             r'｜\s*出口\s*(\d+)\s*条｜\s*落点\s*(✓|✗)', h):
            nm = re.sub(r"\s+", "", m.group(1))
            if nm not in FOC:
                continue
            r = FOC[nm]
            if r["staff"] not in m.group(2):
                bad.append("重点四组「%s」卡片员工写的是「%s」，数据是「%s」"
                           % (nm, m.group(2).strip(), r["staff"]))
            if m.group(3).count("●") != r["f"] or int(m.group(4)) != r["o"] \
                    or (m.group(5) == "✓") != bool(r["l"]):
                bad.append("重点四组「%s」卡片标签与 value_focus.json 不一致（页 %d/%s/%s，数据 %d/%d/%d）"
                           % (nm, m.group(3).count("●"), m.group(4), m.group(5), r["f"], r["o"], r["l"]))
        print("  重点四组：%d 张卡片的标签已与 value_focus.json 对齐" % len(FOC))

    print("\n" + "=" * 46)
    if bad:
        print("✗ 片段漏斗对不上：")
        for b in bad:
            print("   - %s" % b)
        return 1
    print("✓ 漏斗四个数字可复算，六段客户都在数据里")
    return 0


if __name__ == "__main__":
    sys.exit(main())
