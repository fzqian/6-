# -*- coding: utf-8 -*-
"""按「形态 / 出口 / 落点」给一张聊天截图逐句打标 —— 给销售做案例教材用。

和 shot.py 的区别：shot.py 只负责「把聊天记录画出来」，这个脚本在画完之后
给指定几段消息加三样东西，让人一眼看出「这三句话分别在干什么」：

  ① 每条被标的消息，气泡外侧一条彩色竖条（形态蓝 / 出口绿 / 落点琥珀）
  ② 气泡上方一枚同色小标签「①形态」
  ③ 每段开头一条浅色说明带，写这一段的判据（干什么、达标长什么样）

口径与 03_依据文件/判断标准.md §1.2 三条硬标准完全一致，别自己另起一套：
  形态 = 我买的是什么（3 个月线下 + 9 个月线上 + 两年复训，三件都出现）
  出口 = 买完能得到什么（就业路径 / 收入区间 / 证书去向，至少一条讲透）
  落点 = 跟我有什么关系（挂到客户自己的话或情况，且客户下一句变具体/有动作）

用法（索引就是 dialogs 里那组的 msgs 序号，从 0 开始，含首含尾）：
  python mk_stage_marks.py --cust 长生 --id mk1 \
      --mark "1|36|37|三件套一条说完" \
      --mark "2|50|51|就业两种形式" \
      --mark "3|78|85|客户说家里困难，方案改成先考证" \
      --note "同一个客户，三段各长什么样"

  # 整段画全（教材版两张长图就是这个模式）：给了 --span 就不再省略，
  # 没被 --mark 盖到的消息也照画，只是不带色条
  python mk_stage_marks.py --cust 姜彦博 --id mc2 --span "0|95" \
      --mark "3|30|35|…" --mark "1|49|51|…" --mark "2|85|91|…"

只读 dialogs_value.json，不改任何数据。
"""
import argparse
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shot  # noqa: E402  复用 clean / wrap / 字体 / 裁切逻辑

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W = 780
PAD = 16
TXTW = 392          # 气泡内文字折行宽度
CHIP_H = 21
CHIP_GAP = 5

f_title = ImageFont.truetype(shot.FONT, 22)
f_sub = ImageFont.truetype(shot.FONT, 14)
f_band = ImageFont.truetype(shot.FONT, 16)
f_chip = ImageFont.truetype(shot.FONT, 14)
f_txt = shot.f_txt
f_name = shot.f_name
f_note = shot.f_note
meas = shot.meas

# 序号, 名字, 客户心里的问题, 主色, 浅底色
STAGES = {
    "1": ("形态", "我买的是什么", "#2563EB", "#E8EFFF"),
    "2": ("出口", "买完能得到什么", "#0E9F6E", "#E6F9F1"),
    "3": ("落点", "跟我有什么关系", "#D97706", "#FFF4DF"),
}
CIRC = {"1": "\u2460", "2": "\u2461", "3": "\u2462"}

BG = "#EDEDED"

# 导出里只剩一个方括号的这两种：一是当时没解析出来的卡片/视频，二是纯图片/小程序/
# 语音/表情消息。它们不承载任何文字，画成空泡泡只会把图拉长，逐条跳过。
PLACEHOLDER = re.compile(r"^\[[^\]]{1,8}\]$")


def parse_mark(s):
    """'1|36|37|说明' → (1, 36, 37, '说明')"""
    p = s.split("|")
    if len(p) < 3:
        raise ValueError("--mark 格式应为 \"序号|起|止|说明\"：%s" % s)
    k = p[0].strip()
    if k not in STAGES:
        raise ValueError("序号只能是 1/2/3（形态/出口/落点）：%s" % s)
    a, b = int(p[1]), int(p[2])
    if a > b:
        a, b = b, a
    return k, a, b, (p[3].strip() if len(p) > 3 else "")


def short_sales(s):
    """「体德智训-子渝（广州南京长沙）」→「子渝（广州南京长沙）」→ 再长就截断，
    否则员工名会把气泡上沿撑满，标签反而挤没了。"""
    s = shot.clean(s or "")
    s = s.replace("体德智训-", "").replace("体德智训", "")
    s = s.split("-")[0].strip() or s        # 陈舒-pearrrr → 陈舒（内部备注名别画进图）
    return s if len(s) <= 10 else s[:9] + "…"


def legend_lines():
    out = []
    for k in ("1", "2", "3"):
        nm, q, c, _ = STAGES[k]
        out.append((CIRC[k] + nm, q, c))
    return out


def build(g, marks, note, title, sub, span=None, sales=None):
    """→ (elems, tagged, shown)  elems 里每项 (类型, 数据, 高度)

    span=(起, 止) 时按这个消息区间**逐条连续画**（区间外不画、区间内一句不省），
    没被 --mark 盖到的消息也照画，只是不带色条——这样图上是一段完整的聊天记录，
    标注浮在它上面。不给 span 就只画被标的那几段，段与段之间画省略线。
    """
    elems, tagged, shown = [], {}, []
    mw = W - 2 * PAD

    for l in shot.wrap(title, f_title, mw - 8):
        elems.append(("title", l, 32))
    if sub:
        for l in shot.wrap(sub, f_sub, mw - 8):
            elems.append(("sub", l, 24))
    elems.append(("legend", None, 34 + 22 * 0))

    # 哪条消息归哪一段、哪条是段首（只有段首挂标签，整段挂着会糊成一片）
    seg, head = {}, {}
    for k, a, b, desc in marks:
        head[a] = (k, desc)
        for i in range(a, b + 1):
            seg[i] = k

    if span:
        seq = list(range(span[0], span[1] + 1))
    else:
        seq = [i for _, a, b, _ in marks for i in range(a, b + 1)]

    prev = last_day = prev_who = None
    for i in seq:
        # 断档才画省略线。span 连续给进来时这里一次都不会命中
        if prev is not None and i != prev + 1:
            skip = i - prev - 1
            if skip > 0:
                elems.append(("gap", "—— 中间省略 %d 条 ——" % skip, 30))
            last_day = prev_who = None
        prev = i

        if i in head:
            k, desc = head[i]
            nm, q, color, light = STAGES[k]
            # 说明带必须在省略线之后：反过来读者会以为省略发生在这段之后
            band = "%s %s · %s" % (CIRC[k], nm, desc if desc else q)
            for l in shot.wrap(band, f_band, mw - 24):
                elems.append(("band", (l, color, light, False), 26))
            last_day = prev_who = None

        m = g["msgs"][i]
        day = m["t"].split(" ")[0]
        if day != last_day:
            elems.append(("time", m["t"].split("年", 1)[-1], 26))
            last_day = day
        txt = shot.clean(m["x"]) or "[表情]"
        if not txt.strip() or PLACEHOLDER.match(txt.strip()):
            continue
        shown.append(txt)
        lines = shot.wrap(txt, f_txt, TXTW)
        show_name = m["who"] != prev_who
        prev_who = m["who"]
        nm2 = (sales or short_sales(g["sales"])) if m["who"] == "S" else (
            short_sales(g["cust"]) or "客户")
        first = i in head
        k = seg.get(i)
        color = STAGES[k][2] if k else None
        chip_h = CHIP_H + CHIP_GAP if first else 0
        h = 20 + (24 if show_name else 6) + len(lines) * 26 + 8 + chip_h
        elems.append(("msg", (m["who"] == "S", nm2, lines, show_name, k, color,
                              first), h))
        if k:
            tagged[i] = k

    if note:
        nl = shot.wrap("【结论】" + note, f_note, mw - 24)
        elems.append(("note", nl, len(nl) * 24 + 10))
    return elems, tagged, shown


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
            # 三个色块并排，写清「哪一项回答客户心里的什么问题」
            items = legend_lines()
            gaps, x = [], PAD
            for nm, q, c in items:
                bw = d.textlength(nm, font=f_chip) + d.textlength(q, font=f_chip) + 44
                gaps.append((x, bw, nm, q, c))
                x += bw + 14
            # 居中
            total = x - 14 - PAD
            shift = (W - total) / 2 - PAD
            yy = y + 2
            for gx, bw, nm, q, c in gaps:
                gx += shift
                d.rounded_rectangle([gx, yy, gx + bw, yy + 26], 6, fill="#FFFFFF",
                                    outline=c, width=1)
                d.rounded_rectangle([gx + 6, yy + 7, gx + 18, yy + 19], 3, fill=c)
                d.text((gx + 24, yy + 4), nm, font=f_chip, fill=c)
                d.text((gx + 30 + d.textlength(nm, font=f_chip), yy + 4), q,
                       font=f_chip, fill="#666666")
        elif typ == "band":
            l, color, light, first = data
            d.rectangle([PAD, y, W - PAD, y + 24], fill=light)
            d.rectangle([PAD, y, PAD + 4, y + 24], fill=color)
            d.text((PAD + 12, y + 2), l, font=f_band, fill=color)
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
            is_s, name, lines, show_name, k, color, first = data
            bw = min(max(d.textlength(l, font=f_txt) for l in lines) + 22, 420)
            bh = 24 + len(lines) * 26 + 8
            off = 18 if show_name else 0
            nlw = d.textlength(name, font=f_name)
            # 没被标注的消息（span 里那些过渡句）不画色条，让它自然退到背景
            chip = cw = None
            if k:
                nm, q, c, _ = STAGES[k]
                chip = CIRC[k] + nm
                cw = d.textlength(chip, font=f_chip) + 16
            top = CHIP_H + CHIP_GAP if first else 0

            if is_s:
                bx = W - PAD - bw
                if show_name:
                    d.text((W - PAD - nlw, y + top), name, font=f_name, fill="#888888")
                by = y + top + off
                d.rounded_rectangle([bx, by, bx + bw, by + bh], 8, fill="#95EC69")
                # 外侧竖条
                if color:
                    d.rounded_rectangle([bx + bw - 4, by + 4, bx + bw, by + bh - 4], 2,
                                        fill=color)
                # 标签：贴气泡右上，只给这一段的第一条
                if first and chip:
                    d.rounded_rectangle([bx + bw - cw, y, bx + bw, y + CHIP_H], 5,
                                        fill=color)
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
                if color:
                    d.rounded_rectangle([PAD, by + 4, PAD + 4, by + bh - 4], 2, fill=color)
                if first and chip:
                    d.rounded_rectangle([PAD, y, PAD + cw, y + CHIP_H], 5, fill=color)
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
    for p in (os.path.join(HERE, "..", "02_过程文件", "dialogs_value.json"),
              os.path.join(HERE, "dialogs_value.json")):
        if os.path.isfile(p):
            return os.path.abspath(p)
    return "dialogs_value.json"


def main():
    ap = argparse.ArgumentParser(add_help=True, description="三段标注截图")
    ap.add_argument("--cust", required=True, help="客户昵称，与 dialogs 里完全一致")
    ap.add_argument("--data", default=None)
    ap.add_argument("--id", default="mark", help="输出文件名")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "assets", "mark"))
    ap.add_argument("--mark", action="append", default=[],
                    help="\"序号|起|止|说明\"，序号 1/2/3 = 形态/出口/落点")
    ap.add_argument("--span", default="",
                    help="\"起|止\"：整张图覆盖的消息区间，区间内逐条画全（不给就只画标注段）")
    ap.add_argument("--title", default="")
    ap.add_argument("--sub", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--sales-label", default="",
                    help="图上/标题里写哪个名字（导出里的员工昵称带内部备注，如「陈舒-pearrrr」，"
                         "对外页要换成一个干净的名字就传这里；不传就按原名缩写）")
    ap.add_argument("--cust-label", default="",
                    help="客户显示名（只写进侧写，网页/复制头用它）。导出里的昵称可能整个是 emoji，"
                         "画图时会被 clean 掉变成「客户」，传这里可以在网页上还原成 🐈 这样的昵称")
    ap.add_argument("--title-png", default="",
                    help="只给 PNG 用的标题。msyh 不含彩色 emoji，标题里有 🐈 会画成方块，"
                         "用这个参数给图换一版文字标题，网页仍用 --title")
    a = ap.parse_args()

    data = a.data or default_data()
    D = json.load(open(data, encoding="utf-8"))
    hits = [x for x in D if x["cust"] == a.cust]
    if not hits:
        near = [x["cust"] for x in D if a.cust in x["cust"] or x["cust"] in a.cust]
        sys.exit("找不到客户「%s」。相近的：%s" % (a.cust, "、".join(near[:8])))
    g = hits[0]
    marks = [parse_mark(s) for s in a.mark]
    marks.sort(key=lambda m: m[1])
    if len(g["msgs"]) <= max(b for _, _, b, _ in marks):
        sys.exit("消息索引越界：这组只有 %d 条" % len(g["msgs"]))
    span = None
    if a.span:
        p = [int(x) for x in a.span.split("|")]
        span = (min(p), max(p))
        if span[1] >= len(g["msgs"]):
            sys.exit("--span 越界：这组只有 %d 条" % len(g["msgs"]))

    sales = a.sales_label.strip() or short_sales(g["sales"])

    if a.title:
        title = a.title
    elif len({m[0] for m in marks}) == 1:
        k = marks[0][0]
        title = "客户「%s」｜%s｜%s %s" % (g["cust"], sales,
                                          CIRC[k], STAGES[k][0])
    else:
        title = "客户「%s」｜%s｜三段标注" % (g["cust"], sales)
    if a.sub:
        sub = a.sub
    elif span:
        sub = ("整段逐条画下来，一句不省（图片 / 小程序 / 表情消息略过）。"
               "色条与标签只标一件事：这句话在干什么。")
    else:
        sub = "色条与标签只标一件事：这句话在干什么。三段之间的消息已省略，用横线隔开。"
    elems, tagged, shown = build(g, marks, a.note, a.title_png or title, sub, span, sales)

    out_dir = os.path.abspath(a.out)
    png = os.path.join(out_dir, a.id + ".png")
    H = render(elems, png)

    man = {
        "id": a.id, "file": os.path.basename(png), "cust": g["cust"], "sales": g["sales"],
        "sales_label": sales,
        "cust_label": a.cust_label.strip() or short_sales(g["cust"]),
        "marks": [{"stage": k, "name": STAGES[k][0], "i": x, "j": y,
                   "n": y - x + 1, "desc": desc} for k, x, y, desc in marks],
        "note": a.note, "title": title, "texts": shown,
        "span": ([span[0], span[1]] if span else None),
        "built": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    mj = os.path.splitext(png)[0] + ".json"
    json.dump(man, open(mj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("OK %s  %dx%d  %d 条  %d 段  → %s" % (a.id, W, H, len(shown), len(marks), png))
    for k, x, y, desc in marks:
        print("   %s %-4s 第 %d-%d 条（%d 条）%s" % (CIRC[k], STAGES[k][0], x, y, y - x + 1,
                                                  ("　" + desc) if desc else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
