# -*- coding: utf-8 -*-
"""通用聊天截图生成器 —— 微信气泡风格 PNG，供网页报告 / Word 文档使用。

依赖：Pillow、微软雅黑 C:/Windows/Fonts/msyh.ttc
数据：dialogs_all.json  [{sales, cust, msgs:[{who:"S"|"C", t, x}]}]

────────────────────────────────────────────────────────
用法一 · 截一段（最常用）
  python shot.py --cust "@平静" --start "想去看看" --end "今天不来" \
      --id C30_P1 --note "客户主动要到长沙校区，销售只回「你跟我说时间就好」" \
      --out ../web-report/assets/prob

用法二 · 截多段（段与段之间自动出现「—— 间隔 N 天 ——」）
  python shot.py --cust "Atopos" \
      --seg "一万九到两位六区间|看看在不在的预算范围内" \
      --seg "如果超出预算的话选择一个最基础的新国职|这个是无价的" \
      --id C38_P3 --out ../web-report/assets/prob

用法三 · 先看有哪些客户可截
  python shot.py --list

其它参数
  --lead   起始句之前补几条上下文。默认 auto = 向上最多找 3 条，命中第一条客户消息就停
           （解决「图里只有销售的回复、看不到客户问了什么」）。--lead 0 关闭
  --data   指定 dialogs_all.json（默认自动找 ../brief-compose/dialogs_all.json）
  --maxn   单段最多截几条，防止一次截 200 条出巨图
  --exact  start/end 必须整条完全相等才命中（避免「杨博」误中「杨博 17743153800」）
  --width  图宽，默认 600
────────────────────────────────────────────────────────

注意：本脚本只读 dialogs_all.json，不改任何数据。图片是本地渲染，不上传、不联网。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FONT = "C:/Windows/Fonts/msyh.ttc"
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2190-\u21FF\u2B00-\u2BFF"
    "\u3030\u303D\u3297\u3299\u200d\U0001F1E6-\U0001F1FF]"
)
SKIP = re.compile(r"^\[(动画表情|呲牙|破涕为笑|旺柴|捂脸|裂开|皱眉|得意|拥抱|抱拳|微笑)\]?$")

W = 600
PAD = 12

f_txt = ImageFont.truetype(FONT, 19)
f_name = ImageFont.truetype(FONT, 14)
f_note = ImageFont.truetype(FONT, 16)
f_head = ImageFont.truetype(FONT, 15)
meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))


# ---------------- 文本处理 ----------------
# 数学类 emoji 不能直接丢：丢了之后「23600➕4650➕450🟰28700」会粘成
# 「23600465045028700」，图的数字和正文的数字对不上。先换成全角符号再渲染。
MATH = {"\u2795": "\uff0b", "\U0001F7F0": "\uff1d", "\u2796": "\uff0d",
        "\u2797": "\u00f7", "\u2716": "\u00d7", "\u2716\ufe0f": "\u00d7",
        "\u2200": "\u00d7"}


def clean(t):
    """去 emoji、去链接、压空白。msyh 不含彩色 emoji，留着会渲染成方块。"""
    for k, v in MATH.items():
        t = t.replace(k, v)
    t = EMOJI.sub("", t)
    t = re.sub(r"\s*https?://\S+", "", t)
    return re.sub(r"[ \t]+", " ", t).strip()


NO_HEAD = "。，、；：？！）」』】》%”’"


def wrap(text, font, maxw):
    """按像素宽折行。
    - 显式换行（\\n）先切段，段内再折行 —— 企微导出的多行消息靠这个还原
    - 英文/数字整词不拆（nasm 不会断成 nas / m）
    - 标点不能出现在行首，溢出的标点连同前一个字一起挪到下一行
    """
    out = []
    for para in str(text).split("\n"):
        toks = re.findall(r"[A-Za-z0-9.]+|\s+|.", para)
        lines, cur = [], ""
        for tk in toks:
            if meas.textlength(cur + tk, font=font) <= maxw:
                cur += tk
            elif len(tk) == 1 and tk in NO_HEAD and len(cur) > 1:
                lines.append(cur[:-1])
                cur = cur[-1] + tk
            else:
                lines.append(cur.rstrip())
                cur = tk.lstrip()
        if cur.strip():
            lines.append(cur.rstrip())
        out.extend([l for l in lines if l] or [""])
    return out or [""]


def compact(msgs, a, b):
    """连续纯图片合并成「[图片] ×N」，纯表情跳过——压高度又不丢「连发」这个事实。"""
    out, i = [], a
    while i <= b:
        x = msgs[i]["x"]
        base = x.split(" ")[0].strip()
        if SKIP.match(base):
            i += 1
            continue
        if base == "[图片]":
            j = i
            while j + 1 <= b and msgs[j + 1]["x"].split(" ")[0].strip() == "[图片]":
                j += 1
            n = j - i + 1
            m = dict(msgs[i])
            m["x"] = "[图片]" if n == 1 else "[图片] ×%d" % n
            out.append(m)
            i = j + 1
            continue
        out.append(msgs[i])
        i += 1
    return out


# ---------------- 定位 ----------------
def dlg(D, cust):
    hits = [x for x in D if x["cust"] == cust]
    if not hits:
        near = [x["cust"] for x in D if cust in x["cust"] or x["cust"] in cust]
        raise KeyError(
            "找不到客户「%s」。%s"
            % (cust, ("相近的有：" + "、".join(near[:8])) if near else "用 --list 看全部客户名")
        )
    return hits[0]


def find(D, cust, txt, exact=False):
    d = dlg(D, cust)
    for i, m in enumerate(d["msgs"]):
        if (m["x"].strip() == txt) if exact else (txt in m["x"]):
            return d, i
    raise KeyError("「%s」里找不到这句：%s" % (cust, txt[:40]))


def span(D, cust, s_txt, e_txt=None, exact=False, maxn=None):
    d, i = find(D, cust, s_txt, exact)
    if e_txt is None:
        return d, i, i
    j = i
    while not ((d["msgs"][j]["x"].strip() == e_txt) if exact else (e_txt in d["msgs"][j]["x"])):
        j += 1
        if j >= len(d["msgs"]):
            raise KeyError("「%s」里找不到结束句：%s" % (cust, e_txt[:40]))
        if maxn and j - i + 1 >= maxn:
            j = i + maxn - 1
            break
    if maxn:
        j = min(j, i + maxn - 1)
    return d, i, j


# ---------------- 补前因 ----------------
def lead_back(msgs, i, lead):
    """把截图起点往前挪，补上「客户为什么要问这一句」。

    只从销售那句开始截，读者就看不到「客户问了什么」，因果链断掉。
    auto：向上最多 3 条，命中第一条客户消息就停（连带它上面连续的客户消息）
    数字：固定向上取 N 条
    返回新的起点下标；没找到客户消息就保持原位。
    """
    if lead == "auto":
        # 起点本身就是客户说的，前因已经在图里，不再往前堆
        if msgs[i]["who"] == "C":
            return i
        cap = 3
        hit = -1
        for k in range(i - 1, max(-1, i - 1 - cap), -1):
            if msgs[k]["who"] == "C":
                hit = k
                break
        if hit < 0:
            return i
        while hit - 1 >= 0 and msgs[hit - 1]["who"] == "C" and (i - (hit - 1)) < cap:
            hit -= 1
        return hit
    n = int(lead)
    return max(0, i - n) if n > 0 else i


# ---------------- 渲染 ----------------
def build(d, segs, note, title, max_w, pre=False):
    elems = []
    shown = []          # 图上真正出现的消息原文（写 manifest，供 check_quotes.py 核对）
    for l in wrap(title, f_head, max_w - 2 * PAD - 16):
        elems.append(("head", l, 21))
    if pre:
        # 顶部说明「上面还有」，避免读者以为对话从这里开始
        elems.append(("gap", "—— 以上省略 ——", 26))

    def daykey(t):
        m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", t)
        return datetime(*map(int, m.groups())) if m else None

    def fullkey(t):
        """'2026年10月13日 22:52' → datetime（含时分，用来算段间真实间隔）"""
        m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})", t)
        return datetime(*map(int, m.groups())) if m else None

    def gap_label(t0, t1):
        d0, d1 = fullkey(t0), fullkey(t1)
        if not (d0 and d1) or d1 < d0:
            return "——"
        sec = (d1 - d0).total_seconds()
        if sec >= 86400:
            return "—— 间隔 %d 天 ——" % int(sec // 86400)
        if sec >= 3600:
            return "—— %d 小时后 ——" % int(sec // 3600)
        if sec >= 60:
            return "—— %d 分钟后 ——" % int(sec // 60)
        return "——"

    last_day = None
    for si, (a, b) in enumerate(segs):
        if si > 0:
            elems.append(("gap", gap_label(d["msgs"][segs[si - 1][1]]["t"],
                                           d["msgs"][a]["t"]), 26))
            last_day = None
        prev_who = None
        for m in compact(d["msgs"], a, b):
            day = m["t"].split(" ")[0]
            if day != last_day:
                # 不能写死切片："2026年10月27日 11:34" 与 "2026年3月8日 11:07"
                # 长度差 1，[5:16] 会把两位数月份的时间戳吃掉最后一位
                elems.append(("time", m["t"].split("年", 1)[-1], 24))
                last_day = day
            txt = clean(m["x"]) or "[表情]"
            shown.append(txt)
            lines = wrap(txt, f_txt, 376)
            show_name = m["who"] != prev_who
            prev_who = m["who"]
            nm = clean(d["sales"] if m["who"] == "S" else d["cust"]) or ("销售" if m["who"] == "S" else "客户")
            elems.append(
                ("msg", (m["who"] == "S", nm, lines, show_name),
                 20 + (24 if show_name else 6) + len(lines) * 26 + 8)
            )
    if note:
        nl = wrap("【标注】" + note, f_note, max_w - 2 * PAD - 16)
        elems.append(("note", nl, len(nl) * 24 + 8))
    return elems, shown


def render(elems, path, max_w):
    H = PAD + sum(e[2] + 7 for e in elems) + PAD
    img = Image.new("RGB", (max_w, H), "#EDEDED")
    d = ImageDraw.Draw(img)
    y = PAD
    for typ, data, h in elems:
        if typ == "head":
            d.rounded_rectangle([PAD, y, max_w - PAD, y + h], 6, fill="#D9D9D9")
            lw = d.textlength(data, font=f_head)
            d.text(((max_w - lw) / 2, y + 3), data, font=f_head, fill="#333")
        elif typ == "time":
            tw = d.textlength(data, font=f_name)
            d.rounded_rectangle([(max_w - tw) / 2 - 10, y, (max_w + tw) / 2 + 10, y + 19], 6, fill="#DADADA")
            d.text(((max_w - tw) / 2, y + 1), data, font=f_name, fill="#666")
        elif typ == "gap":
            tw = d.textlength(data, font=f_name)
            d.line([PAD + 8, y + 10, (max_w - tw) / 2 - 14, y + 10], fill="#BBB")
            d.line([(max_w + tw) / 2 + 14, y + 10, max_w - PAD - 8, y + 10], fill="#BBB")
            d.text(((max_w - tw) / 2, y), data, font=f_name, fill="#999")
        elif typ == "note":
            lines = data
            bw = min(max_w - 2 * PAD,
                     max(d.textlength(l, font=f_note) for l in lines) + 16)
            d.rounded_rectangle([PAD, y, PAD + bw, y + h - 2], 5, fill="#FFF3D6")
            ty = y + 3
            for l in lines:
                d.text((PAD + 8, ty), l, font=f_note, fill="#B45309")
                ty += 24
        else:
            is_s, name, lines, show_name = data
            bw = min(max(d.textlength(l, font=f_txt) for l in lines) + 22, 400)
            bh = 24 + len(lines) * 26 + 8
            off = 18 if show_name else 0
            nlw = d.textlength(name, font=f_name)
            if is_s:
                bx = max_w - PAD - bw
                if show_name:
                    d.text((max_w - PAD - nlw, y), name, font=f_name, fill="#888")
                by = y + off
                d.rounded_rectangle([bx, by, bx + bw, by + bh], 8, fill="#95EC69")
                ty = by + 7
                for l in lines:
                    d.text((bx + 11, ty), l, font=f_txt, fill="#111")
                    ty += 26
            else:
                if show_name:
                    d.text((PAD, y), name, font=f_name, fill="#888")
                by = y + off
                d.rounded_rectangle([PAD, by, PAD + bw, by + bh], 8, fill="#FFFFFF", outline="#DDD")
                ty = by + 7
                for l in lines:
                    d.text((PAD + 11, ty), l, font=f_txt, fill="#111")
                    ty += 26
        y += h + 7
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)
    return H


# ---------------- 侧写：这张图里到底有什么 ----------------
def write_manifest(path_png, sid, d, segs, shown, note, title):
    """把「这张图实际渲染了哪几条原文」写成同名 .json，供 check_quotes.py 核对。

    报告正文里的每一句引号，都必须能在对应图的 manifest 里找到——这是防
    「正文说客户回了 X，图上却没有 X」的唯一机器手段。参数名、路径、段号都在里面，
    改图之后重跑一遍就同步了，不需要人工维护对照表。
    """
    p = os.path.splitext(path_png)[0] + ".json"
    m = {
        "id": sid,
        "file": os.path.basename(path_png),
        "sales": d["sales"],
        "cust": d["cust"],
        "segs": [{"i": a, "j": b, "n": b - a + 1} for a, b in segs],
        "note": note,
        "title": title,
        "texts": shown,
        "built": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    return p


# ---------------- 入口 ----------------
def default_data():
    """优先用本目录刚生成的 dialogs_all.json；退回旧批次数据时给出警告。"""
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (
        os.path.join(here, "dialogs_all.json"),
        os.path.join(here, "..", "brief-compose", "dialogs_all.json"),
    ):
        if os.path.isfile(p):
            return os.path.abspath(p)
    return None


def main():
    ap = argparse.ArgumentParser(add_help=True, description="聊天记录截图生成器")
    ap.add_argument("--cust", help="客户昵称，与 dialogs_all.json 的 cust 完全一致")
    ap.add_argument("--start", help="起始消息关键词")
    ap.add_argument("--end", help="结束消息关键词，省略则只截一条")
    ap.add_argument("--seg", action="append", default=[], help="多段：\"起始|结束\"，可重复")
    ap.add_argument("--id", dest="sid", default="shot", help="图片名/标题，如 C30_P1")
    ap.add_argument("--note", default="", help="图底部琥珀色标注")
    ap.add_argument("--out", default=".", help="输出目录，或直接给 .png 路径")
    ap.add_argument("--data", default=None, help="dialogs_all.json 路径")
    ap.add_argument("--maxn", type=int, default=None, help="单段最多几条")
    ap.add_argument("--exact", action="store_true", help="整条完全相等才命中")
    ap.add_argument("--lead", default="auto",
                    help="起始句前补几条上下文：auto(默认，回溯到上一条客户消息) / 0 / 数字")
    ap.add_argument("--width", type=int, default=600, help="图宽，默认 600")
    ap.add_argument("--no-manifest", action="store_true",
                    help="不写同名 .json 侧写（默认写，check_quotes.py 靠它核对引语）")
    ap.add_argument("--list", action="store_true", help="列出全部客户")
    a = ap.parse_args()

    dp = a.data or default_data()
    if not dp or not os.path.isfile(dp):
        print("找不到 dialogs_all.json，用 --data 指定路径")
        return 2
    D = json.load(open(dp, encoding="utf-8"))
    _mt = datetime.fromtimestamp(os.path.getmtime(dp)).strftime("%Y-%m-%d %H:%M")
    print("数据：%s（%d 组，生成于 %s）" % (dp, len(D), _mt))
    if "brief-compose" in dp.replace("\\", "/"):
        print("⚠ 这是上一批的旧数据（brief-compose）。本批请先跑 to_dialogs.py --out dialogs_all.json，")
        print("  或显式加 --data <本批 json>，否则截出来的图是旧对话。")

    if a.list:
        for x in sorted(D, key=lambda z: -len(z["msgs"])):
            print("  %-28s %4d 条  %s" % (x["cust"], len(x["msgs"]), x["sales"][:22]))
        return 0

    if not a.cust:
        print("缺 --cust，或先用 --list 看有哪些客户")
        return 2

    pairs = []
    for s in a.seg:
        if "|" not in s:
            print("--seg 格式应为 \"起始|结束\"：%s" % s)
            return 2
        p, q = s.split("|", 1)
        pairs.append((p.strip(), q.strip() or None))
    if not pairs:
        if not a.start:
            print("缺 --start，或用 --seg \"起始|结束\"")
            return 2
        pairs.append((a.start, a.end))

    segs = []
    d = None
    for s_txt, e_txt in pairs:
        try:
            d, i, j = span(D, a.cust, s_txt, e_txt, a.exact, a.maxn)
        except KeyError as e:
            print("\u2717 %s" % str(e).strip("'\""))
            print("  关键词必须是对话里的原话（标点、空格、表情都要对得上）。")
            print("  排查：python shot.py --list  确认客户名；--data  确认数据源是本批。")
            sug = []
            for x in D:
                if x["cust"] == a.cust:
                    for m in x["msgs"]:
                        if any(k in m["x"] for k in ("价", "钱", "费", "多少", "预算")):
                            sug.append("    %s %s：%s" % (m["t"][:10],
                                                         "客" if m["who"] == "C" else "销",
                                                         m["x"][:46]))
            if sug:
                print("  这位客户提到价格/预算的原话，挑一句当关键词：")
                for s in sug[:8]:
                    print(s)
            else:
                print("  这位客户全程没提过价格、钱、费用、多少、预算。")
            return 1
        segs.append((i, j))

    # 只给第一段补前因。后续段之间有「间隔 N 天」分隔，本来就有上下文
    pre = False
    a0, b0 = segs[0]
    st = lead_back(d["msgs"], a0, a.lead)
    if st < a0:
        segs[0] = (st, b0)
        pre = True

    title = "%s · %s → %s" % (a.sid, d["sales"], d["cust"])
    elems, shown = build(d, segs, a.note, title, a.width, pre)
    out = a.out if a.out.lower().endswith(".png") else os.path.join(a.out, a.sid + ".png")
    H = render(elems, out, a.width)
    if not a.no_manifest:
        write_manifest(out, a.sid, d, segs, shown, a.note, title)

    n = sum(b - a2 + 1 for a2, b in segs)
    print("OK  %s" % out)
    print("    %d 段 / %d 条 / %d×%d px / %.1f KB" % (len(segs), n, a.width, H, os.path.getsize(out) / 1024))
    if not a.no_manifest:
        print("    侧写 %s.json（%d 条原文，供 check_quotes.py 核对引语）" % (a.sid, len(shown)))
    cmsg = sum(1 for x, y in segs for m in d["msgs"][x:y + 1] if m["who"] == "C")
    if cmsg == 0:
        print("    ! 这张图里一条客户消息都没有，读者看不到「客户问了什么」。")
        print("      加 --lead 3 往前补，或把 --start 换成客户那句原话。")
    elif pre:
        print("    已向前补 %d 条（含客户原话），顶部标注「以上省略」" % (a0 - st))
    return 0


if __name__ == "__main__":
    sys.exit(main())
