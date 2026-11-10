# -*- coding: utf-8 -*-
"""价值传递专项页核查：页面上的数字、名单、逐组表，能不能从数据里复算出来。

用法：python audit_value.py 价值传递.html [--data 02_过程文件/value_all.json]
      不传 --data 时，优先用 value_all.json（三批合并后的总盘），没有才退回 value.json
"""
import json
import os
import re
import sys


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "价值传递.html"
    cand = ["02_过程文件/value_all.json", "value_all.json",
            "02_过程文件/value.json", "value.json"]
    data = next((p for p in cand if os.path.exists(p)), "02_过程文件/value_all.json")
    if "--data" in sys.argv:
        data = sys.argv[sys.argv.index("--data") + 1]
    h = open(src, encoding="utf-8").read()
    V = json.load(open(data, encoding="utf-8"))
    if isinstance(V, list) or "rows" not in V:
        sys.exit("!! %s 里没有 rows：这是对话原文（dialogs_*.json），不是逐组判读表。\n"
                 "   请改用 02_过程文件/value_all.json（三批合并后的总盘）。" % data)
    R = V["rows"]

    base = len([r for r in R if r[1] != "—"])
    f3 = len([r for r in R if r[2] == 3])
    o1 = len([r for r in R if r[3] >= 1])
    l1 = len([r for r in R if r[4] == 1])
    strict = len([r for r in R if r[2] == 3 and r[3] >= 1 and r[4] == 1 and r[5] == 0])
    veto = len([r for r in R if r[5] == 1])

    bad = []

    # 1. hero 四个数字
    hero = h[h.find('class="hero-stats"'):h.find('class="hero-quote"')]
    nums = re.findall(r"<b>(\d+)</b>", hero)
    want = [str(f3), str(o1), str(l1), str(strict)]
    if nums != want:
        bad.append("hero 四个数字是 %s，复算是 %s" % (nums, want))

    # 2. 漏斗三个数
    fun = h[h.find('class="funnel'):h.find('</section>', h.find('class="funnel'))]
    fn = re.findall(r'fn-fill" style="width:\d+%">(\d+)<', fun)
    if fn[:3] != [str(f3), str(o1), str(l1)]:
        bad.append("漏斗是 %s，复算是 %s" % (fn[:3], [f3, o1, l1]))

    # 3. 表格 48 行，且客户名齐全
    _stops = [x for x in (h.find('id="focus"'), h.find('id="end"')) if x > 0]
    tb = h[h.find('id="table"'):(min(_stops) if _stops else len(h))]
    rows = re.findall(r"<tr[^>]*><td[^>]*>([^<]+)</td><td class='who'>([^<]*)</td>", tb)
    if len(rows) != len(R):
        bad.append("表格 %d 行，value.json 有 %d 组" % (len(rows), len(R)))
    names = [x[0] for x in rows]
    miss = [r[0] for r in R if r[0] not in names]
    if miss:
        bad.append("表里少了：%s" % "、".join(miss))
    # 员工列必须与数据一致（合并后两批靠这一列区分）
    staff_of = {r[0]: (r[8] if len(r) > 8 else "") for r in R}
    wrong = [(n, st, staff_of.get(n)) for n, st in rows if n in staff_of and st != staff_of[n]]
    if wrong:
        bad.append("表格员工列错了 %d 行：%s" % (len(wrong), wrong[:4]))

    # 4. 排除组不进分母
    note = h[h.find('class="hero-meta"'):h.find('</header>')]
    note = re.sub(r"<[^>]+>", "", note)
    if str(base) not in note:
        bad.append("页首没写分母 %d（应写「分母 %d 组」）" % (base, base))

    # 5. 一票否决名单
    if veto:
        for name in [r[0] for r in R if r[5] == 1]:
            if name not in h:
                bad.append("否决名单里的 %s 在页面上找不到" % name)

    # 6. 八类分布（V3 / 缺在哪）
    if 'id="combo"' in h:
        seg = h[h.find('id="combo"'):h.find('id="good"')]
        LAB = {(1, 1, 1): "三项全过", (1, 1, 0): "缺落点", (1, 0, 1): "缺出口",
               (0, 1, 1): "缺形态", (1, 0, 0): "只有形态", (0, 1, 0): "只有出口",
               (0, 0, 1): "只有落点", (0, 0, 0): "三项全无"}
        want, miss = {}, {}
        for r in R:
            if r[1] == "—":
                continue
            k = (1 if r[2] == 3 else 0, 1 if r[3] >= 1 else 0, 1 if r[4] == 1 else 0)
            want[LAB[k]] = want.get(LAB[k], 0) + 1
            miss[3 - sum(k)] = miss.get(3 - sum(k), 0) + 1
        got = {}
        for m in re.finditer(r'<div class="fn-lbl"><b>([^<]+)</b>[^<]*</div>.{0,400}?fn-drop"[^>]*>(\d+) 组', seg, re.S):
            got[m.group(1)] = int(m.group(2))
        if len(got) != 8:
            bad.append("八类分布只解析到 %d 行（应为 8 行）" % len(got))
        diff = ["%s 页面 %d / 复算 %d" % (k, got.get(k, -1), v)
                for k, v in want.items() if got.get(k, -1) != v]
        if diff:
            bad.append("八类分布对不上：" + "；".join(diff))
        # 缺 n 项四张卡
        cards = re.findall(r'<div class="tag">缺 (\d) 项</div>\s*<div class="big">(\d+)<', seg)
        cmap = {int(a): int(b) for a, b in cards}
        if len(cmap) != 4:
            bad.append("「缺 n 项」只有 %d 张卡（应为 4 张）" % len(cmap))
        cdiff = ["缺 %d 项 页面 %s / 复算 %d" % (k, cmap.get(k, -1), v)
                 for k, v in miss.items() if cmap.get(k, -1) != v]
        if cdiff:
            bad.append("缺项汇总对不上：" + "；".join(cdiff))
        print("八类分布：%s ｜ 缺 0/1/2/3 项：%s" % (
            " ".join("%s%d" % (LAB[k], want.get(LAB[k], 0)) for k in
                     sorted(LAB, key=lambda x: -want.get(LAB[x], 0))),
            "/".join(str(miss.get(i, 0)) for i in range(4))))

    # 7. 重点四组：已并入同一个分母，靠底色与卡片识别
    FO = [r for r in R if len(r) > 9 and r[9] == 1]
    if 'id="focus"' in h:
        bad.append("页面还有 id=\"focus\" 板块——重点四组应并入正文，不再单开一节")
    if len(FO) != 4:
        bad.append("value_all.json 里 focus=1 的有 %d 组（应为 4 组）" % len(FO))
    # 7a 逐组表：琥珀底的行，必须正好是这四组
    tb_focus = re.findall(r"<tr style=\"background:#FDF6E3[^\"]*\"><td[^>]*>([^<]+)</td>", tb)
    if sorted(tb_focus) != sorted(r[0] for r in FO):
        bad.append("逐组表里琥珀底的行是 %s，应为 %s" % (tb_focus, [r[0] for r in FO]))
    # 7b 这四组不能重复计数：分母 = 各组有效行之和
    valid_staff = {}
    for r in R:
        if r[1] != "—":
            valid_staff[r[8]] = valid_staff.get(r[8], 0) + 1
    if sum(valid_staff.values()) != base:
        bad.append("按员工汇总 %d ≠ 分母 %d（有重复计数）" % (sum(valid_staff.values()), base))
    # 7c 四张卡：都在正文里、都带重点标识、都配了截图和「下一步」
    cards = re.findall(r'<article class="qcard rv[^"]*focus[^"]*"[^>]*>(.*?)</article>', h, re.S)
    if len(cards) != 4:
        bad.append("带 focus 的卡片 %d 张（应为 4 张）" % len(cards))
    ntag = sum(1 for c in cards if 'class="qcard-tag focus"' in c)
    nnext = sum(1 for c in cards if 'class="qblock qnext"' in c)
    nshot = sum(1 for c in cards if re.search(r'<img src="assets/value/[a-z0-9]+\.png"', c))
    if cards and (ntag != 4 or nnext != 4 or nshot != 4):
        bad.append("重点卡标识不全：标识 %d / 下一步 %d / 截图 %d（都应为 4）" % (ntag, nnext, nshot))
    names_on_cards = []
    for c in cards:
        m = re.search(r'qcard-meta">([^｜]+)｜', c)
        if m:
            names_on_cards.append(m.group(1).strip())
    if cards and sorted(names_on_cards) != sorted(r[0] for r in FO):
        bad.append("四张重点卡的客户是 %s，应为 %s" % (names_on_cards, [r[0] for r in FO]))
    print("重点四组：%d 组已并入 ｜ 表内琥珀行 %d ｜ 卡片 %d（标识 %d / 下一步 %d / 截图 %d）"
          % (len(FO), len(tb_focus), len(cards), ntag, nnext, nshot))

    print("复算：分母 %d ｜ 形态 %d ｜ 出口 %d ｜ 落点 %d ｜ 三项全过 %d ｜ 否决 %d"
          % (base, f3, o1, l1, strict, veto))
    print("=" * 46)
    if bad:
        print("✗ 页面与 value.json 对不上：")
        for b in bad:
            print("   - %s" % b)
        return 1
    print("✓ 四个数字 / 漏斗 / 逐组表 / 八类分布 / 否决名单，全部可复算")
    return 0


if __name__ == "__main__":
    sys.exit(main())
