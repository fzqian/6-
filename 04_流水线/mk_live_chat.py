# -*- coding: utf-8 -*-
"""把「聊天记录长图」换成网页里的真文字版 —— 同一份原文、同一套标注，但每个字都能选、能复制。

为什么要有这个：长图是 PIL 画出来的像素，字选不中、复制不了。要在教材页里
「直接在图上复制」，只能把画图之前的那一层（同样的气泡、时间条、标注带）
用 DOM 再排一遍。所以这里不重写文案、不重挑消息，一律以长图的侧写
`assets/**/xx.json` 为准，逐条照着排；排完必须和侧写里的 texts 逐字相同，否则报错退出。

两种标注体系：
  connect 四要件  ①自我介绍 ②称呼客户 ③说明来意 ④客户回应（一条可挂两个）
  value   三段    ①形态 ②出口 ③落点（一条只挂一段）
看侧写里有没有 stages_hit 判断用哪套，不靠猜。

数据来源：侧写 .json + 02_过程文件/dialogs_*.json（自动挑 texts 对得上的那一份）。

用法：
  python mk_live_chat.py --page "../接通建联(可用于案例分享).html" \
                         --page "../价值传递(可用于案例分享).html" [--dry]
改页面之前自动备份成 xxx.html.bak（同目录）。
"""
import argparse
import glob
import html as _html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import shot  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORDER4 = ("1", "2", "3", "4")
ORDER3 = ("1", "2", "3")
CIRC = {"1": "\u2460", "2": "\u2461", "3": "\u2462", "4": "\u2463"}

# 序号: (名字, 客户心里的问题, 主色, 浅底色) —— 与 mk_connect_marks.py / mk_stage_marks.py 完全同一套
SETS = {
    "connect": {
        "order": ORDER4,
        "stages": {
            "1": ("自我介绍", "", "#2563EB", "#E8EFFF"),
            "2": ("称呼客户", "", "#7C3AED", "#F2EBFE"),
            "3": ("说明来意", "", "#0E9F6E", "#E6F9F1"),
            "4": ("客户回应", "", "#D97706", "#FFF4DF"),
        },
        "title": "接通建联",
        # 图上：① 自我介绍：说明　　条首标签只写圈号
        "band": "%s %s：%s",
        "chip": "%s",   # 条首标签只写圈号
    },
    "value": {
        "order": ORDER3,
        "stages": {
            "1": ("形态", "我买的是什么", "#2563EB", "#E8EFFF"),
            "2": ("出口", "买完能得到什么", "#0E9F6E", "#E6F9F1"),
            "3": ("落点", "跟我有什么关系", "#D97706", "#FFF4DF"),
        },
        "title": "价值传递",
        # 图上：① 形态 · 说明　　条首标签写「①形态」
        "band": "%s %s \u00b7 %s",
        "chip": "%s%s",  # 条首标签写「①形态」
    },
}

PLACEHOLDER = re.compile(r"^\[[^\]]{1,8}\]$")


def esc(s):
    return _html.escape(s or "", quote=False)


def short_sales(s):
    """与出图脚本同一套缩写：去掉「体德智训-」，在「-」处断开（内部备注名不画进图）。"""
    s = shot.clean(s or "")
    s = s.replace("体德智训-", "").replace("体德智训", "")
    s = s.split("-")[0].strip() or s
    return s if len(s) <= 10 else s[:9] + "\u2026"


def short_cust(s):
    """线索备注名常带批次号：「B26.9.29官抖-短视频 黄小姐」直接截断会变成
    「B26.9.29官抖」，粘出去不知道是谁。有空格就取后半段。"""
    s = shot.clean(s or "")
    if " " in s:
        tail = s.rsplit(" ", 1)[-1].strip()
        if tail and len(tail) <= 10:
            return tail
    return s if len(s) <= 10 else s[:9] + "\u2026"


def chip_text(mode, k):
    """条首标签：四要件只写圈号（①），三段写「①形态」（与长图一致）。"""
    return CIRC[k] + (SETS[mode]["stages"][k][0] if mode == "value" else "")


def sales_of(man):
    """页面上销售叫什么。侧写里给了 sales_label 就以它为准（导出的员工名是
    「陈舒-pearrrr」「体德智训-子渝（广州南京长沙）」这种内部备注名，直接上页面
    既长又露内部信息），没给才按老规矩缩写。"""
    return (man.get("sales_label") or "").strip() or short_sales(man["sales"])


def cust_of(man):
    """客户叫什么。客户昵称可能整个是 emoji（🐈），画图时会被 clean 成空，
    侧写里用 cust_label 记着原样，网页和复制头认它。"""
    return (man.get("cust_label") or "").strip() or short_cust(man["cust"]) or "客户"


def load_group(cust, texts):
    """在 02_过程文件 里挑出这个人、且区间逐字对得上的那一组对话。

    同名客户可能同时出现在 dialogs_value.json（价值传递那批）和 dialogs_W.json（主报告
    那批），消息条数不一样。只认同一条标准：按侧写重排出来的文字必须与侧写 texts 完全相同。
    """
    cands = []
    for p in sorted(glob.glob(os.path.join(ROOT, "02_过程文件", "dialogs_*.json"))):
        try:
            D = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(D, list):
            continue
        for g in D:
            if g.get("cust") == cust:
                cands.append((os.path.basename(p), g))
    if not cands:
        sys.exit("02_过程文件 里找不到客户「%s」" % cust)
    return cands


def rebuild(g, man, mode):
    """按侧写把消息排成行：band / time / gap / msg / note。不读图，只读数据。"""
    cfg = SETS[mode]
    order = cfg["order"]
    marks = [(str(m["stage"]), int(m["i"]), int(m["j"]), m.get("desc") or "") for m in man["marks"]]
    marks.sort(key=lambda m: (m[1], order.index(m[0]) if m[0] in order else 9))

    rows = []
    if mode == "connect":
        # 一条消息可以同时归两个要件 → heads 存列表
        heads, seg = {}, {}
        for k, a, b, desc in marks:
            heads.setdefault(a, []).append((k, desc))
            for i in range(a, b + 1):
                if k not in seg.setdefault(i, []):
                    seg[i].append(k)
        for i in seg:
            seg[i].sort(key=order.index)
    else:
        heads, seg = {}, {}
        for k, a, b, desc in marks:
            heads[a] = (k, desc)
            for i in range(a, b + 1):
                seg[i] = k

    span = man["span"]
    seq = list(range(span[0], span[1] + 1))
    # 说明带不算「打断」：图上是插了带子就重画时间条，网页里那样会连着出现
    # 三个一模一样的「9月29日 11:44」，读起来像渲染出错。这里只按真实时间/发言变化画。
    prev = last_day = prev_who = None
    drawn = []

    for i in seq:
        if prev is not None and i != prev + 1:
            rows.append(("gap", i - prev - 1))
            last_day = prev_who = None
        prev = i

        if i in heads:
            if mode == "connect":
                for k, desc in heads[i]:
                    rows.append(("band", k, cfg["band"] % (CIRC[k], SETS[mode]["stages"][k][0], desc)))
            else:
                k, desc = heads[i]
                nm, q, _c, _l = cfg["stages"][k]
                rows.append(("band", k, cfg["band"] % (CIRC[k], nm, desc or q)))

        m = g["msgs"][i]
        day = m["t"].split(" ")[0]
        if day != last_day:
            rows.append(("time", m["t"].split("\u5e74", 1)[-1]))
            last_day = day

        txt = shot.clean(m["x"]) or "[\u8868\u60c5]"
        if not txt.strip() or PLACEHOLDER.match(txt.strip()):
            continue
        drawn.append(txt)

        show_name = m["who"] != prev_who
        prev_who = m["who"]
        name = sales_of(man) if m["who"] == "S" else cust_of(man)
        ks = (seg.get(i) or []) if mode == "connect" else ([seg[i]] if i in seg else [])
        rows.append(("msg", m["who"], name, txt, ks, show_name, i in heads))

    if man.get("note"):
        rows.append(("note", man["note"]))
    return rows, drawn


def fix_title(t, cust, sales):
    """侧写 title 是「客户「🐈」｜陈舒心｜整段 46 条 · 三段标注」：第 2 段是销售。
    标题、气泡上的名字、复制头必须一个叫法——侧写改了 sales_label 而标题没跟，
    同一段对话会出现两个名字，所以这里一律按 man 里的显示名重写。"""
    p = (t or "").split("\uff5c")
    if len(p) >= 3:
        p[1] = sales
        if cust and p[0].startswith("\u5ba2\u6237\u300c"):
            p[0] = "\u5ba2\u6237\u300c%s\u300d" % cust
    return "\uff5c".join(p)


def head_text(man, mode, n_c, cust, sales):
    cfg = SETS[mode]
    span = man["span"]
    legend = "\uff0f".join(cfg["stages"][k][0] for k in cfg["order"])
    circs = "".join(CIRC[k] for k in cfg["order"])
    return ("%s \u00d7 %s\uff5c%s \u00b7 \u7b2c %d-%d \u6761\uff08%d \u6761\u539f\u6587\uff09\n"
            "\u3014%s = %s\u3015" % (sales, cust, cfg["title"], span[0], span[1], n_c, circs, legend))


def body_html(rows, mode):
    """把行排成 DOM。完整版和要点版共用这一套，两边的标号、色条、气泡才会一模一样。"""
    stages = SETS[mode]["stages"]
    body = []
    for r in rows:
        t = r[0]
        if t == "band":
            _t, k, text = r
            _nm, _q, c, light = stages[k]
            body.append('<div class="cl-band" style="background:%s;border-left-color:%s;color:%s">%s</div>'
                        % (light, c, c, esc(text)))
        elif t == "time":
            body.append('<div class="cl-time"><span>%s</span></div>' % esc(r[1]))
        elif t == "gap":
            body.append('<div class="cl-gap"><i></i><span>\u4e2d\u95f4\u7701\u7565 %d \u6761</span><i></i></div>' % r[1])
        elif t == "note":
            body.append('<div class="cl-note">\u3010\u7ed3\u8bba\u3011%s</div>' % esc(r[1]))
        else:
            _t, who, name, txt, ks, show_name, first = r
            side = "s" if who == "S" else "c"
            seg = ['<div class="cl-msg %s" data-who="%s" data-k="%s">' % (side, esc(name), "".join(ks))]
            if first and ks:
                chips = "".join(
                    '<span class="cl-chip" style="background:%s">%s</span>'
                    % (stages[k][2], chip_text(mode, k))
                    for k in ks)
                seg.append('<div class="cl-chips">%s</div>' % chips)
            if show_name:
                seg.append('<div class="cl-nm">%s</div>' % esc(name))
            # 色条：一个要件一整条，两个要件上下各一半（图上就是这么画的）
            cols = [stages[k][2] for k in ks]
            if len(cols) >= 2:
                bar = "linear-gradient(%s 0 50%%,%s 50%% 100%%)" % (cols[0], cols[1])
            elif cols:
                bar = cols[0]
            else:
                bar = "transparent"
            seg.append('<div class="cl-bub"><i class="cl-bar" style="background:%s"></i>'
                       '<span class="cl-txt">%s</span></div>' % (bar, esc(txt)))
            seg.append("</div>")
            body.append("".join(seg))
    return "\n".join(body)


def slim_rows(rows):
    """要点版的行：只留被色条标过的句子，加上它那一段开头的说明带。

    中间怎么聊、客户怎么回、省掉几条，全不要 —— 销售要的是「照着这几句说」，
    不是再读一遍 40 条。时间条也不带：整段是一天里 40 分钟的事，抽出来的 8 条
    挂一个「16:02」的戳，读起来像这几句从 16:02 才开始说，反而不准。
    结论条（cl-note）同样不进：那是解读，不是对话。
    """
    out, prev_who = [], None
    for r in rows:
        if r[0] == "time":
            continue
        if r[0] == "band":
            out.append(r)
            continue
        if r[0] == "msg":
            _t, who, name, txt, ks, _sn, first = r
            if not ks:
                continue
            # 名字跟着「上一句要点是谁说的」重算：完整版里两人交替，筛完可能连着
            # 三条都是销售，中间那条原本不写名字，照搬会变成没头没尾的一段话
            out.append(("msg", who, name, txt, ks, who != prev_who, first))
            prev_who = who
    return out


def render(rows, man, mode, idx):
    """→ (figure_html, n_msg, copy_head)"""
    cfg = SETS[mode]
    stages = cfg["stages"]
    cust = cust_of(man)
    sales = sales_of(man)
    n_msg = sum(1 for r in rows if r[0] == "msg")
    head = head_text(man, mode, n_msg, cust, sales)

    # 图例：色块 + 圈号名字（value 再挂一句客户心里的问题）
    lg = []
    for k in cfg["order"]:
        nm, q, c, _l = stages[k]
        if q:
            lg.append('<span class="cl-lg"><i style="background:%s"></i><b style="color:%s">%s%s</b>'
                      '<em>%s</em></span>' % (c, c, CIRC[k], nm, esc(q)))
        else:
            lg.append('<span class="cl-lg"><i style="background:%s"></i>'
                      '<b style="color:%s">%s%s</b></span>' % (c, c, CIRC[k], nm))
    legend = '<div class="cl-legend">%s</div>' % "".join(lg)

    span = man["span"]
    sub = ("\u8fd9\u4e00\u6bb5\u5171 %d \u6761\uff0c\u56fe\u7247\u4e0e\u8868\u60c5\u6d88\u606f %d \u6761\u7565\u8fc7\uff0c\u5176\u4f59\u9010\u6761\u6392\u4e0b\u6765\u3002"
           "\u8272\u6761\u4e0e\u6807\u7b7e\u53ea\u6807\u4e00\u4ef6\u4e8b\uff1a\u8fd9\u53e5\u8bdd\u5728\u5b8c\u6210\u54ea\u4e00\u9879\u3002"
           % (span[1] - span[0] + 1, span[1] - span[0] + 1 - n_msg))
    title_txt = fix_title(man.get("title"), cust, sales)
    body = body_html(rows, mode)

    if mode != "value":
        # 四要件那一套（接通建联）几乎每条消息都挂着要件，切两版看不出差别，
        # 所以只排一版；tab 与双 pane 只给三段这页（价值传递）用。
        fig = """<figure class="mcase-shot cclive" id="live{n}">
<input type="checkbox" id="sw{n}" class="swchk">
<div class="shotbar"><span class="sbt">原文 · 整段聊天记录</span><span class="sbd">{sbd}</span>
<a class="shotopen" href="{img}" target="_blank" rel="noopener">看原图 PNG ↗</a>
<div class="cl-tools">
<button type="button" class="lcb lcb1" data-lc="chat{n}">复制全文</button>
<button type="button" class="lcb" data-lcsel="chat{n}">全选</button>
<label class="swtoggle" for="sw{n}"><span class="t1">展开全部 ↓</span><span class="t2">收起 ↑</span></label>
</div></div>
<div class="cl-wrap"><div class="shotwin"><div class="cl-chat" id="chat{n}" data-cc-head="{head}">
<div class="cl-title">{title}</div>
<div class="cl-sub">{sub}</div>
{legend}
<div class="cl-body">
{body}
</div>
</div></div><i class="cl-fade" aria-hidden="true"></i></div>
<div class="qshot-cap">字是<b>真文字</b>，直接拖选就能复制；也可点右上「复制全文」，一次带走 {n_msg} 条（带说话人和要件标号）。
内容与 <code>{img}</code> 是同一份原文，旁边的 <code>{side}</code> 记着这张图排了哪几条、每条归哪一项，可逐字比对。</div>
</figure>""".format(n=idx, sbd=man.get("_sbd", ""), img=man["_img"],
                   head=esc(head).replace("\n", "&#10;"), title=esc(title_txt), sub=esc(sub),
                   legend=legend, body=body, n_msg=n_msg, side=os.path.basename(man["_json"]))
        return fig, n_msg, head

    # ---- 三段（价值传递）：一页两版 ----
    sl = slim_rows(rows)
    n_sl = sum(1 for r in sl if r[0] == "msg")
    slim_head = "%s \u00d7 %s\uff5c%s \u00b7 \u8981\u70b9\u7248\uff08%d \u6761\uff09" % (
        sales, cust, cfg["title"], n_sl)
    slim_title = "\u5ba2\u6237\u300c%s\u300d\uff5c%s\uff5c\u53ea\u770b\u8981\u70b9 \u00b7 %d \u6761" % (cust, sales, n_sl)
    slim_sub = ("\u53ea\u7559\u88ab\u8272\u6761\u6807\u8fc7\u7684 %d \u6761\uff0c\u6bcf\u6bb5\u5f00\u5934\u90a3\u4e00\u884c\u662f\u8fd9\u4e00\u6bb5\u5728\u505a\u4ec0\u4e48\uff0c"
                "\u5176\u4f59\u5bf9\u8bdd\u7701\u6389\u3002\u8981\u770b\u5ba2\u6237\u600e\u4e48\u95ee\u3001\u4e2d\u95f4\u600e\u4e48\u63a5\u7684\uff0c\u70b9\u4e0a\u9762\u300c\u5b8c\u6574\u7248\u300d\u3002"
                % n_sl)

    fig = """<figure class="mcase-shot cclive" id="live{n}">
<input type="checkbox" id="sw{n}" class="swchk">
<div class="shotbar"><span class="sbt">原文 · 整段聊天记录</span><span class="sbd">{sbd}</span>
<a class="shotopen" href="{img}" target="_blank" rel="noopener">看原图 PNG ↗</a>
<div class="cl-tools">
<button type="button" class="lcb lcb1" data-lc="chat{n}" data-lcgrp="{n}" data-lbl-slim="复制要点" data-lbl-full="复制全文">复制要点</button>
<button type="button" class="lcb" data-lcsel="chat{n}" data-lcgrp="{n}">全选</button>
<label class="swtoggle" for="sw{n}"><span class="t1">展开全部 ↓</span><span class="t2">收起 ↑</span></label>
</div></div>
<div class="cl-wrap"><div class="shotwin">
<div class="cl-tabs"><button type="button" class="cl-tab on" data-clgrp="{n}" data-pane="chat{n}k">要点版<b>{n_sl}</b>条</button><button type="button" class="cl-tab" data-clgrp="{n}" data-pane="chat{n}">完整版<b>{n_msg}</b>条</button></div>
<div class="cl-chat cl-pane" id="chat{n}k" data-clgrp="{n}" data-cc-plain="1" data-cc-head="{slim_head}">
<div class="cl-title">{slim_title}</div>
<div class="cl-sub">{slim_sub}</div>
{legend}
<div class="cl-body">
{slim_body}
</div>
</div>
<div class="cl-chat cl-pane" id="chat{n}" data-clgrp="{n}" data-cc-head="{head}" hidden>
<div class="cl-title">{title}</div>
<div class="cl-sub">{sub}</div>
{legend}
<div class="cl-body">
{body}
</div>
</div>
</div><i class="cl-fade" aria-hidden="true"></i></div>
<div class="qshot-cap">字是<b>真文字</b>。「要点版」是被色条标过的 {n_sl} 条，点「复制要点」一次带走；「完整版」是 {n_msg} 条全量，带结论。
两版是同一份原文，旁边的 <code>{side}</code> 记着排了哪几条、每条归哪一项，可逐字比对。</div>
</figure>""".format(n=idx, sbd=man.get("_sbd", ""), img=man["_img"],
                   head=esc(head).replace("\n", "&#10;"), title=esc(title_txt), sub=esc(sub),
                   legend=legend, body=body, n_msg=n_msg, side=os.path.basename(man["_json"]),
                   n_sl=n_sl, slim_head=esc(slim_head), slim_title=esc(slim_title),
                   slim_sub=esc(slim_sub), slim_body=body_html(sl, mode))
    return fig, n_msg, head


def inject_tags(page):
    """补一行 CSS、一行 JS 引用；已经补过就不动（脚本可反复跑）。"""
    VER = 5
    css = '<link rel="stylesheet" href="assets/livechat.css?v=%d">' % VER
    js = '<script src="assets/livechat.js?v=%d"></script>' % VER
    # 已经引过就只把版本号升上去（改了样式不升，浏览器会拿旧缓存）
    page = re.sub(r"assets/livechat\.css\?v=\d+", "assets/livechat.css?v=%d" % VER, page)
    page = re.sub(r"assets/livechat\.js\?v=\d+", "assets/livechat.js?v=%d" % VER, page)
    if "assets/livechat.css" not in page:
        m = re.search(r'<link rel="stylesheet" href="assets/manual\.css[^"]*">\n?', page)
        if not m:
            sys.exit("页面里找不到 manual.css 的引用，不知道把新样式插哪")
        page = page[:m.end()] + css + "\n" + page[m.end():]
    if "assets/livechat.js" not in page:
        i = page.rfind("</body>")
        page = page[:i] + js + "\n" + page[i:]
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", action="append", required=True)
    ap.add_argument("--dry", action="store_true", help="只报会改什么，不写文件")
    a = ap.parse_args()

    total = 0
    for rel in a.page:
        path = os.path.abspath(os.path.join(HERE, rel)) if not os.path.isabs(rel) else rel
        page = io.open(path, encoding="utf-8").read()
        print("\n== %s" % os.path.basename(path))

        # 两种块都认：还没换过的长图块，和已经换过一次的文字块。
        # 认后者是为了能重跑——改了侧写（换客户、换显示名、改标注）之后，
        # 得让页面跟着侧写重排一遍，否则脚本只能跑一次，改一次就得手工改 HTML。
        figs = list(re.finditer(r'<figure class="mcase-shot(?: cclive)?"[^>]*>.*?</figure>',
                                page, re.S))
        if not figs:
            print("  ! 页面上没有 mcase-shot 块（长图版、文字版都算），是不是选错页面了")
            continue

        new_blocks, idx = [], 0
        for m in figs:
            blk = m.group(0)
            # 长图块用 <img>，已经换过的块只剩「看原图 PNG」那条链接，两处都要认
            mi = (re.search(r'<img[^>]+src="(assets/[^"]+\.png)"', blk)
                  or re.search(r'class="shotopen"[^>]+href="(assets/[^"]+\.png)"', blk))
            if not mi:
                print("  - 跳过一块：既没有 <img> 也没有原图链接（不是聊天长图）")
                new_blocks.append(blk)
                continue
            img_rel = mi.group(1)
            js_rel = os.path.splitext(img_rel)[0] + ".json"
            jpath = os.path.join(ROOT, js_rel)
            if not os.path.isfile(jpath):
                print("  - 跳过 %s：找不到同名侧写 %s" % (img_rel, js_rel))
                new_blocks.append(blk)
                continue
            man = json.load(io.open(jpath, encoding="utf-8"))
            mode = "connect" if "stages_hit" in man else "value"
            man["_img"], man["_json"] = img_rel, jpath
            # 原 figure 里的那行小字照样留着，别丢信息
            ms = re.search(r'<span class="sbd">(.*?)</span>', blk, re.S)
            man["_sbd"] = ms.group(1).strip() if ms else ""

            # 自动认数据源：哪个 dialogs 文件重排出来与侧写逐字相符，就用哪个
            picked = None
            for src, g in load_group(man["cust"], man.get("texts")):
                if len(g["msgs"]) <= man["span"][1]:
                    continue
                rows, drawn = rebuild(g, man, mode)
                if drawn == man["texts"]:
                    picked = (src, g, rows)
                    break
            if not picked:
                sys.exit("  ✗ %s：没有一个 dialogs 文件能重排出与侧写逐字相同的文字，先查数据" % img_rel)
            src, g, rows = picked

            idx += 1
            fig, n_msg, head = render(rows, man, mode, idx)
            new_blocks.append(fig)
            total += 1
            print("  ✓ %s（%s 模式，%d 条，源 %s）" % (img_rel, mode, n_msg, src))
            print("      标注带 %d 条 · 时间条 %d 条 · 复制头：%s"
                  % (sum(1 for r in rows if r[0] == "band"),
                     sum(1 for r in rows if r[0] == "time"),
                     head.split("\n")[0]))

        out = page
        for m, nb in zip(reversed(figs), reversed(new_blocks)):
            out = out[:m.start()] + nb + out[m.end():]
        out = inject_tags(out)

        if a.dry:
            print("  （--dry，未写文件）")
            continue
        bak = path + ".bak"
        if not os.path.exists(bak):
            io.open(bak, "w", encoding="utf-8", newline="").write(page)
            print("  备份 → %s" % os.path.basename(bak))
        io.open(path, "w", encoding="utf-8", newline="").write(out)
        print("  写出 %s（%d 字节）" % (os.path.basename(path), len(out.encode("utf-8"))))

    print("\n共替换 %d 块" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
