# -*- coding: utf-8 -*-
"""按「接通建联」四要件给一张聊天截图逐句打标 —— 给销售讲第一次接触怎么做。

和 mk_stage_marks.py 的区别有三处，其余（画图、折行、字体）全部复用 shot.py：

1. 标的是**四要件**不是三项：①自我介绍 ②称呼客户 ③说明来意 ④客户有实质回应
   口径见 03_依据文件/接通建联口径.md，逐字来自两份 docx，不自己加。
2. **一条消息可以同时属于两个要件**。样例第 3 条
   「哈哈哈 好滴黄小姐 咱们客服这边留言信息 是人在河源 想了解国内国际认证区别…」
   前半句是称呼落地、后半句是说明来意，硬拆成两句是假的，所以色条画双色、标签写「②③」。
3. 图例只有名字，不写「客户心里的问题」——四要件不是客户的问题，是销售的动作。

用法（索引就是 dialogs 里那组的 msgs 序号，从 0 开始，含首含尾）：
  python mk_connect_marks.py --cust "B26.9.29官抖-短视频 黄小姐" --id c1 --span "0|38" \
      --mark "1|1|1|姓名 + 资历一起给" \
      --mark "2|1|3|先问怎么称呼，客户答完下一句用上" \
      --mark "3|3|4|把留言三条一次复述，客户只需确认" \
      --mark "4|6|6|确认之后自己抛问题"

只读 dialogs_connect.json，不改任何数据。
"""
import argparse
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shot  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W = 780
PAD = 16
TXTW = 392
CHIP_H = 21
CHIP_GAP = 5

f_title = ImageFont.truetype(shot.FONT, 22)
f_sub = ImageFont.truetype(shot.FONT, 14)
f_band = ImageFont.truetype(shot.FONT, 16)
f_chip = ImageFont.truetype(shot.FONT, 14)
f_txt = shot.f_txt
f_name = shot.f_name
f_note = shot.f_note

# 序号, 名字, 主色, 浅底色
STAGES = {
    "1": ("自我介绍", "#2563EB", "#E8EFFF"),
    "2": ("称呼客户", "#7C3AED", "#F2EBFE"),
    "3": ("说明来意", "#0E9F6E", "#E6F9F1"),
    "4": ("客户回应", "#D97706", "#FFF4DF"),
}
CIRC = {"1": "\u2460", "2": "\u2461", "3": "\u2462", "4": "\u2463"}
ORDER = ("1", "2", "3", "4")

BG = "#EDEDED"

# 纯占位消息（[图片] [小程序] [语音] [动画表情]）不承载文字，画出来只是空泡泡
PLACEHOLDER = re.compile(r"^\[[^\]]{1,8}\]$")


def parse_mark(s):
    """'1|36|37|说明' → ('1', 36, 37, '说明')"""
    p = s.split("|")
    if len(p) < 3:
        raise ValueError('--mark 格式应为 "序号|起|止|说明"：%s' % s)
    k = p[0].strip()
    if k not in STAGES:
        raise ValueError("序号只能是 1/2/3/4（自我介绍/称呼客户/说明来意/客户回应）：%s" % s)
    a, b = int(p[1]), int(p[2])
    if a > b:
        a, b = b, a
    return k, a, b, (p[3].strip() if len(p) > 3 else "")


def short_sales(s):
    s = shot.clean(s or "")
    s = s.replace("体德智训-", "").replace("体德智训", "")
    s = s.split("-")[0].strip() or s
    return s if len(s) <= 10 else s[:9] + "…"


def short_cust(s):
    """线索备注名往往带批次号：「B26.9.29官抖-短视频 黄小姐」直接截断会变成
    「B26.9.29官抖」，画在气泡上认不出是谁。有空格就取后半段。"""
    s = shot.clean(s or "")
    if " " in s:
        tail = s.rsplit(" ", 1)[-1].strip()
        if tail and len(tail) <= 10:
            return tail
    return s if len(s) <= 10 else s[:9] + "…"


def count_skipped(g, span):
    """区间里有多少条是纯占位消息（图上不画）——副标题要写实数，不能拍脑袋。"""
    n = 0
    for i in range(span[0], span[1] + 1):
        t = shot.clean(g["msgs"][i]["x"]) or ""
        if not t.strip() or PLACEHOLDER.match(t.strip()):
            n += 1
    return n


def legend_items():
    """四块并排：色块 + 要件名。四要件是销售动作，不是客户问题，所以不挂副标。"""
    return [(CIRC[k] + STAGES[k][0], STAGES[k][1]) for k in ORDER]


def build(g, marks, note, title, sub, span=None):
    """→ (elems, tagged, shown)；tagged 是 [(msg 序号, [要件...]), ...]"""
    elems, tagged, shown = [], [], []
    mw = W - 2 * PAD

    for l in shot.wrap(title, f_title, mw - 8):
        elems.append(("title", l, 32))
    if sub:
        for l in shot.wrap(sub, f_sub, mw - 8):
            elems.append(("sub", l, 24))
    elems.append(("legend", None, 34))

    # 一条消息可以同时归两个要件：seg 存列表，heads 存这一句开头要写的所有说明
    seg, heads = {}, {}
    for k, a, b, desc in marks:
        heads.setdefault(a, []).append((k, desc))
        for i in range(a, b + 1):
            if k not in seg.setdefault(i, []):
                seg[i].append(k)
    for i in seg:
        seg[i].sort(key=ORDER.index)

    if span:
        seq = list(range(span[0], span[1] + 1))
    else:
        seq = sorted({i for _, a, b, _ in marks for i in range(a, b + 1)})

    prev = last_day = prev_who = None
    for i in seq:
        if prev is not None and i != prev + 1:
            skip = i - prev - 1
            if skip > 0:
                elems.append(("gap", "—— 中间省略 %d 条 ——" % skip, 30))
            last_day = prev_who = None
        prev = i

        if i in heads:
            # 一句挂两个要件时画两条说明带，不合成一条长带：合成后一条带要折两行，
            # 左色条一半蓝一半紫，读者反而看不出哪半句对应哪个要件。
            for k, desc in heads[i]:
                nh = STAGES[k][0]
                band = "%s %s%s" % (CIRC[k], nh, ("：" + desc) if desc else "")
                for l in shot.wrap(band, f_band, mw - 24):
                    elems.append(("band", (l, [STAGES[k][1]], STAGES[k][2], False), 26))
            last_day = prev_who = None

        m = g["msgs"][i]
        day = m["t"].split(" ")[0]
        if day != last_day:
            elems.append(("time", m["t"].split("年", 1)[-1], 26))
            last_day = day
        txt = shot.clean(m["x"]) or ""
        if not txt.strip() or PLACEHOLDER.match(txt.strip()):
            continue
        shown.append(txt)
        lines = shot.wrap(txt, f_txt, TXTW)
        show_name = m["who"] != prev_who
        prev_who = m["who"]
        nm2 = (short_sales(g["sales"]) if m["who"] == "S" else short_cust(g["cust"])) or (
            "销售" if m["who"] == "S" else "客户")
        ks = seg.get(i, [])
        first = i in heads
        chip_h = CHIP_H + CHIP_GAP if first else 0
        h = 20 + (24 if show_name else 6) + len(lines) * 26 + 8 + chip_h
        elems.append(("msg", (m["who"] == "S", nm2, lines, show_name, ks,
                              [STAGES[k][1] for k in ks], first), h))
        if ks:
            tagged.append((i, ks))

    if note:
        nl = shot.wrap("【结论】" + note, f_note, mw - 24)
        elems.append(("note", nl, len(nl) * 24 + 10))
    return elems, tagged, shown


def _bar(d, x0, y0, y1, colors, wd=4):
    """气泡外侧色条：一个要件一整条，两个要件上下各一半。"""
    if not colors:
        return
    if len(colors) == 1:
        d.rounded_rectangle([x0, y0 + 4, x0 + wd, y1 - 4], 2, fill=colors[0])
        return
    mid = (y0 + y1) // 2
    for idx, c in enumerate(colors[:2]):
        top = y0 + 4 if idx == 0 else mid
        bot = mid if idx == 0 else y1 - 4
        d.rounded_rectangle([x0, top, x0 + wd, bot], 2, fill=c)


def render(elems, path):
    H = PAD + sum(e[2] + 8 for e in elems) + PAD
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = PAD
    mw = W - 2 * PAD

    for typ, data, h in elems:
        if typ == "title":
            lw = d.textlength(data, font=f_title)
            d.text(((W - lw) / 2, y + 2), data, font=f_title, fill="#111111")
        elif typ == "sub":
            lw = d.textlength(data, font=f_sub)
            d.text(((W - lw) / 2, y), data, font=f_sub, fill="#777777")
        elif typ == "legend":
            items = legend_items()
            gaps, x = [], PAD
            for nm, c in items:
                bw = d.textlength(nm, font=f_chip) + 44
                gaps.append((x, bw, nm, c))
                x += bw + 12
            total = x - 12 - PAD
            shift = (W - total) / 2 - PAD
            yy = y + 2
            for gx, bw, nm, c in gaps:
                gx += shift
                d.rounded_rectangle([gx, yy, gx + bw, yy + 26], 6, fill="#FFFFFF",
                                    outline=c, width=1)
                d.rounded_rectangle([gx + 6, yy + 7, gx + 18, yy + 19], 3, fill=c)
                d.text((gx + 24, yy + 4), nm, font=f_chip, fill=c)
        elif typ == "band":
            l, colors, light, first = data
            d.rectangle([PAD, y, W - PAD, y + 24], fill=light)
            _bar(d, PAD, y, y + 24, colors)
            d.text((PAD + 12, y + 2), l, font=f_band, fill=colors[0])
        elif typ == "gap":
            tw = d.textlength(data, font=f_name)
            d.line([PAD + 10, y + 12, (W - tw) / 2 - 14, y + 12], fill="#BBBBBB")
            d.line([(W + tw) / 2 + 14, y + 12, W - PAD - 10, y + 12], fill="#BBBBBB")
            d.text(((W - tw) / 2, y + 2), data, font=f_name, fill="#999999")
        elif typ == "time":
            tw = d.textlength(data, font=f_name)
            d.rounded_rectangle([(W - tw) / 2 - 10, y + 2, (W + tw) / 2 + 10, y + 21],
                                6, fill="#DADADA")
            d.text(((W - tw) / 2, y + 3), data, font=f_name, fill="#666666")
        elif typ == "note":
            lines = data
            bw = min(mw, max(d.textlength(l, font=f_note) for l in lines) + 20)
            d.rounded_rectangle([PAD, y, PAD + bw, y + h - 2], 6, fill="#FFF3D6")
            ty = y + 4
            for l in lines:
                d.text((PAD + 10, ty), l, font=f_note, fill="#B45309")
                ty += 24
        else:
            is_s, name, lines, show_name, ks, colors, first = data
            bw = min(max(d.textlength(l, font=f_txt) for l in lines) + 22, 420)
            bh = 24 + len(lines) * 26 + 8
            off = 18 if show_name else 0
            nlw = d.textlength(name, font=f_name)
            chip = "".join(CIRC[k] for k in ks) if ks else None
            cw = (d.textlength(chip, font=f_chip) + 16) if chip else 0
            top = CHIP_H + CHIP_GAP if first else 0

            if is_s:
                bx = W - PAD - bw
                if show_name:
                    d.text((W - PAD - nlw, y + top), name, font=f_name, fill="#888888")
                by = y + top + off
                d.rounded_rectangle([bx, by, bx + bw, by + bh], 8, fill="#95EC69")
                _bar(d, bx + bw - 4, by, by + bh, colors)
                if first and chip:
                    d.rounded_rectangle([bx + bw - cw, y, bx + bw, y + CHIP_H], 5,
                                        fill=colors[0])
                    d.text((bx + bw - cw + 8, y + 2), chip, font=f_chip, fill="#FFFFFF")
                ty = by + 7
                for l in lines:
                    d.text((bx + 11, ty), l, font=f_txt, fill="#111111")
                    ty += 26
            else:
                if show_name:
                    d.text((PAD, y + top), name, font=f_name, fill="#888888")
                by = y + top + off
                d.rounded_rectangle([PAD, by, PAD + bw, by + bh], 8, fill="#FFFFFF",
                                    outline="#DDDDDD")
                _bar(d, PAD, by, by + bh, colors)
                if first and chip:
                    d.rounded_rectangle([PAD, y, PAD + cw, y + CHIP_H], 5, fill=colors[0])
                    d.text((PAD + 8, y + 2), chip, font=f_chip, fill="#FFFFFF")
                ty = by + 7
                for l in lines:
                    d.text((PAD + 11, ty), l, font=f_txt, fill="#111111")
                    ty += 26
        y += h + 8

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)
    return H


def default_data():
    for p in (os.path.join(HERE, "..", "02_过程文件", "dialogs_connect.json"),
              os.path.join(HERE, "dialogs_connect.json")):
        if os.path.isfile(p):
            return os.path.abspath(p)
    return "dialogs_connect.json"


def main():
    ap = argparse.ArgumentParser(add_help=True, description="接通建联四要件标注")
    ap.add_argument("--cust", required=True, help="客户昵称，与 dialogs 里完全一致")
    ap.add_argument("--data", default=None)
    ap.add_argument("--id", default="c1", help="输出文件名")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "assets", "connect"))
    ap.add_argument("--mark", action="append", default=[],
                    help='"序号|起|止|说明"，序号 1/2/3/4 = 自我介绍/称呼客户/说明来意/客户回应')
    ap.add_argument("--span", default="", help='"起|止"：整张图覆盖的消息区间，区间内逐条画全')
    ap.add_argument("--title", default="")
    ap.add_argument("--sub", default="")
    ap.add_argument("--note", default="")
    a = ap.parse_args()

    data = a.data or default_data()
    D = json.load(open(data, encoding="utf-8"))
    hits = [x for x in D if x["cust"] == a.cust]
    if not hits:
        near = [x["cust"] for x in D if a.cust in x["cust"] or x["cust"] in a.cust]
        sys.exit("找不到客户「%s」。相近的：%s" % (a.cust, "、".join(near[:8])))
    g = hits[0]
    marks = [parse_mark(s) for s in a.mark]
    marks.sort(key=lambda m: (m[1], ORDER.index(m[0])))
    if not marks:
        sys.exit("至少要给一条 --mark")
    if len(g["msgs"]) <= max(b for _, _, b, _ in marks):
        sys.exit("消息索引越界：这组只有 %d 条" % len(g["msgs"]))
    span = None
    if a.span:
        p = [int(x) for x in a.span.split("|")]
        span = (min(p), max(p))
        if span[1] >= len(g["msgs"]):
            sys.exit("--span 越界：这组只有 %d 条" % len(g["msgs"]))

    title = a.title or "客户「%s」｜%s｜接通建联" % (short_cust(g["cust"]), short_sales(g["sales"]))
    if a.sub:
        sub = a.sub
    elif span:
        n_span = span[1] - span[0] + 1
        sub = ("这一段共 %d 条，图片与表情消息 %d 条略过，其余逐条画下来。"
               "色条与标签只标一件事：这句话在完成哪个要件。"
               % (n_span, count_skipped(g, span)))
    else:
        sub = "色条与标签只标一件事：这句话在完成哪个要件。段与段之间的消息已省略。"
    elems, tagged, shown = build(g, marks, a.note, title, sub, span)

    out_dir = os.path.abspath(a.out)
    png = os.path.join(out_dir, a.id + ".png")
    H = render(elems, png)

    got = sorted({k for _, ks in tagged for k in ks})
    man = {
        "id": a.id, "file": os.path.basename(png), "cust": g["cust"], "sales": g["sales"],
        "marks": [{"stage": k, "name": STAGES[k][0], "i": x, "j": y,
                   "n": y - x + 1, "desc": desc} for k, x, y, desc in marks],
        "stages_hit": got,
        "note": a.note, "title": title, "texts": shown,
        "span": ([span[0], span[1]] if span else None),
        "built": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    json.dump(man, open(os.path.splitext(png)[0] + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("OK %s  %dx%d  %d 条  %d 段  → %s" % (a.id, W, H, len(shown), len(marks), png))
    for k, x, y, desc in marks:
        print("   %s %-4s 第 %d-%d 条（%d 条）%s" % (CIRC[k], STAGES[k][0], x, y,
                                                  y - x + 1, ("　" + desc) if desc else ""))
    miss = [k for k in ORDER if k not in got]
    if miss:
        print("   ⚠ 缺要件：%s" % "、".join(CIRC[k] + STAGES[k][0] for k in miss))
    return 0


if __name__ == "__main__":
    sys.exit(main())
