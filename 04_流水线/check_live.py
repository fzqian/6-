# -*- coding: utf-8 -*-
"""案例分享页自检 —— 查「聊天记录文字版」有没有跟数据走偏。

页面上那块聊天记录不是图了，是 DOM。好处是能选能复制，坏处是它变成了
「可以随手改坏的文字」：改一个字、删一条、把某个 ①②③ 挪到别的句子上，
页面照样好看，但讲案例时就是错的。所以这里拿侧写 .json 和 02_过程文件
重排一遍，跟页面逐条对。

九组：
  1 每个 cclive 块都能配到同名侧写（.json 与 .png 都在）
  2 页面的条数 / 逐字 / 说话人 / 要件标号 == 从数据重排出来的
  3 复制头：条数与实际条数一致，且带 ①②③④ 图例（粘出去别人看得懂）
  4 复制按钮在、livechat.js 引入且有 file:// 兜底（execCommand）
  5 聊天区不在 [data-zoom] 灯箱触发区里（点字弹图就选不中了）
  6 聊天区里没有禁区话术（页面自己写了「零禁区」这条要成立）
  7 结构小项：标题/图例/说明带的数量
  8 口径补充段「客户不报名字，代称也算称呼」在，且代称清单与
    03_依据文件/接通建联口径.md 一致（只在有口径分区的页面上查）
  9 销售名没漏出导出里的内部昵称（pearrrr / 体德智训- / …），
    只认侧写里的 sales_label
 10 一页两版：要点版 == 完整版里带色条的那几条（逐字、顺序、条数），
    说明带留、结论与省略行不收；标签两个且默认停在要点版

用法：python check_live.py
"""
import html as _html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mk_live_chat as L  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 默认查这两页；也可以传路径进来（负向测试就是这么用的）
PAGES = ([os.path.abspath(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else
         [os.path.join(ROOT, "接通建联(可用于案例分享).html"),
          os.path.join(ROOT, "价值传递(可用于案例分享).html")])

BAN6 = ["喂喂喂，还了解吗？", "吱一声啊", "还在吗", "说句话呀",
        "在不在？看到回一下", "怎么不说话了？还考虑吗？"]

bad_n = 0


def ok(m):
    print("  ✓ " + m)


def bad(m):
    global bad_n
    bad_n += 1
    print("  ✗ " + m)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def alias_terms():
    """口径文档里的代称清单才是准的：页面少一个、多一个，都算页面走偏了。"""
    p = os.path.join(ROOT, "03_依据文件", "接通建联口径.md")
    if not os.path.isfile(p):
        return []
    for line in io.open(p, encoding="utf-8"):
        if line.startswith("代称清单"):
            body = line.split("：", 1)[-1]
            return [x.strip() for x in re.split(r"[/、，,]", body) if x.strip()]
    return []


# 导出里的员工名是内部备注名（「陈舒-pearrrr」「体德智训-子渝（广州南京长沙）」
# 「黄荣庆-Hᴗang·小姐ᔆᩚ」），案例页对外，这些既长又露内部信息，一律不许露。
# 侧写 .json 里保留原名用于溯源，页面上只认 sales_label。
LEAK = ["pearrrr", "体德智训-", "子渝", "\u9648\u8212-", "\u5c0f\u59d0\u1d57\u1a69"]


MSG_RE = (r'<div class="cl-msg ([sc])" data-who="([^"]*)" data-k="([^"]*)">'
          r'(.*?)<span class="cl-txt">(.*?)</span>')


def msgs_of(pane):
    """一个 pane 里的消息行 → [(左右侧, 说话人, (要件号…), 文字)]"""
    return [(s, _html.unescape(w), tuple(k), _html.unescape(t))
            for s, w, k, _mid, t in
            (mo.groups() for mo in re.finditer(MSG_RE, pane, re.S))]


def panes_of(blk):
    """把一块切成若干 pane。一页两版时这里有「要点版」「完整版」两个；
    接通建联那块仍是一个。按 pane 边界切，后面扫消息才不会串。

    按 id 认版别（要点版 `chat{n}k`、完整版 `chat{n}`），不拿 data-cc-plain 认 ——
    那个标记本身要单独查：页面上漏了它，该报「要点版没标 plain」，
    而不是报「完整版容器 2 个」，后者会把人引去改结构。
    """
    parts = re.split(r'(?=<div class="cl-chat(?: cl-pane)?")', blk)[1:]
    slim = [p for p in parts if re.search(r'id="chat\d+"(?=[ >])', p[:400]) is None
            and re.search(r'id="chat\d+k"', p[:400])]
    full = [p for p in parts if re.search(r'id="chat\d+"(?=[ >])', p[:400])]
    return full, slim


def check_page(path):
    print("\n== %s" % os.path.basename(path))
    h = io.open(path, encoding="utf-8").read()

    blocks = re.findall(r'<figure class="mcase-shot cclive".*?</figure>', h, re.S)
    if not blocks:
        bad("页面里没有 cclive 块，是不是还没跑 mk_live_chat.py")
        return
    ok("%d 块聊天记录文字版" % len(blocks))

    for bi, blk in enumerate(blocks, 1):
        pint = "  [块%d] " % bi
        mi = re.search(r'href="(assets/[^"]+\.png)"', blk)
        if not mi:
            bad(pint + "没有原图链接（新窗口看原图那条）")
            continue
        img = mi.group(1)
        js = os.path.splitext(img)[0] + ".json"
        if not os.path.isfile(os.path.join(ROOT, img)):
            bad(pint + "原图不存在：%s" % img)
        if not os.path.isfile(os.path.join(ROOT, js)):
            bad(pint + "侧写不存在：%s" % js)
            continue
        man = json.load(io.open(os.path.join(ROOT, js), encoding="utf-8"))
        mode = "connect" if "stages_hit" in man else "value"

        full_l, slim_l = panes_of(blk)
        if len(full_l) != 1:
            bad(pint + "完整版容器 %d 个，应该正好 1 个" % len(full_l))
            continue
        full = full_l[0]

        # ---- 2. 与数据重排的结果逐条对 ----
        picked = None
        for src, g in L.load_group(man["cust"], man.get("texts")):
            if len(g["msgs"]) <= man["span"][1]:
                continue
            rows, drawn = L.rebuild(g, man, mode)
            if drawn == man["texts"]:
                picked = (src, rows)
                break
        if not picked:
            bad(pint + "数据源变了：没有一个 dialogs 文件能重排出侧写的文字")
            continue
        src, rows = picked
        # rebuild 的行是 ("msg", who, name, txt, ks, show_name, first)，
        # 页面上的类是 s/c，这里统一成同一套再比
        want = [("s" if r[1] == "S" else "c", r[2], tuple(r[4]))
                for r in rows if r[0] == "msg"]
        got = [(s, w, k) for s, w, k, _t in msgs_of(full)]

        if len(got) != len(want):
            bad(pint + "完整版 %d 条，数据 %d 条" % (len(got), len(want)))
        else:
            ok(pint + "完整版 %d 条，条数与数据一致（源 %s）" % (len(got), src))

        txt_x = [t for _s, _w, _k, t in msgs_of(full)]
        diff_x = [i for i, t in enumerate(txt_x) if i >= len(man["texts"]) or t != man["texts"][i]]
        if diff_x:
            bad(pint + "这几条的文字与侧写不一致：第 %s 条" % [x + 1 for x in diff_x[:6]])
        else:
            ok(pint + "逐字与侧写一致（%d 条）" % len(txt_x))
        diff_who = [i for i, (g1, w1) in enumerate(zip(got, want))
                    if g1[0] != w1[0] or g1[1] != w1[1]]
        if diff_who:
            bad(pint + "这几条的说话人/左右侧位对不上：第 %s 条" % [x + 1 for x in diff_who[:6]])
        else:
            ok(pint + "说话人与左右侧位一致")
        diff_k = [i for i, (g1, w1) in enumerate(zip(got, want)) if g1[2] != w1[2]]
        if diff_k:
            bad(pint + "这几条的要件标号与数据不一致：第 %s 条" % [x + 1 for x in diff_k[:6]])
        else:
            ok(pint + "要件标号一致")

        # ---- 3. 复制头（只看完整版那个 pane：要点版的头是另一套） ----
        mh = re.search(r'data-cc-head="([^"]*)"', full)
        if not mh:
            bad(pint + "完整版没有 data-cc-head，复制出去没有抬头")
        else:
            head = _html.unescape(mh.group(1))
            mm = re.search(r"（(\d+) 条原文）", head)
            if not mm or int(mm.group(1)) != len(want):
                bad(pint + "复制头的条数不对：%s" % head.replace("\n", " ")[:40])
            elif "〔" not in head or "①" not in head:
                bad(pint + "复制头没有 ①②③ 图例，粘出去别人看不懂标号")
            else:
                ok(pint + "复制头写了「%s 条原文」并带图例" % mm.group(1))

        # ---- 4. 按钮与脚本 ----
        if not re.search(r'data-lc="chat\d+"', blk) or not re.search(r'data-lcsel="chat\d+"', blk):
            bad(pint + "缺「复制」或「全选」按钮")
        else:
            ok(pint + "复制 / 全选 按钮都在")

        # ---- 5. 灯箱 ----
        if "data-zoom" in blk:
            bad(pint + "聊天区套了 data-zoom，点一下就弹图，选不中字")
        else:
            ok(pint + "不在灯箱触发区内")

        # ---- 6. 禁区话术 ----
        # 只拼消息正文与说话人：pane 段里还带着下面的说明文字，整段 strip_tags
        # 会把 caption 里的字也扫进来，报错时报到跟聊天无关的地方去
        plain = " ".join([t for _s, _w, _k, t in msgs_of(full)] +
                         [w for _s, w, _k, _t in msgs_of(full)])
        hit = [b for b in BAN6 if b in plain]
        if hit:
            bad(pint + "聊天记录里出现禁区话术：%s" % hit)
        else:
            ok(pint + "没有禁区话术")

        # ---- 7. 结构小项（两版都要有说明带，图例都齐） ----
        n_mark = len({(m["stage"], int(m["i"])) for m in man["marks"]}) if mode == "connect" \
            else len(man["marks"])
        n_band = len(re.findall(r'<div class="cl-band"', full))
        if n_band != n_mark:
            bad(pint + "完整版说明带 %d 条，标注 %d 处" % (n_band, n_mark))
        else:
            ok(pint + "完整版说明带 %d 条，与标注对齐" % n_band)
        if not re.search(r'<div class="cl-title">[^<]+</div>', full):
            bad(pint + "完整版缺标题行")
        if len(re.findall(r'class="cl-lg"', full)) != len(L.SETS[mode]["order"]):
            bad(pint + "完整版图例数量与要件数不一致")
        else:
            ok(pint + "图例 %d 项齐" % len(L.SETS[mode]["order"]))

        # ---- 10. 两版：要点版 == 完整版里带色条的那些条（2026-11-10） ----
        # 销售拿走的精简版就靠这一组兜底：条数少了、顺序串了、文字被顺手改了，
        # 页面照样好看，但对着念就是错的。
        if mode == "value":
            if not slim_l:
                bad(pint + "没有「要点版」容器——销售要的那份精简版没了")
            else:
                slim = slim_l[0]
                if slim.find('data-cc-plain="1"') < 0:
                    bad(pint + "要点版没标 data-cc-plain，复制出去会带〔②〕，不是纯对话")
                got_s = msgs_of(slim)
                want_s = [(("s" if r[1] == "S" else "c"), r[2], tuple(r[4]), r[3])
                          for r in rows if r[0] == "msg" and r[4]]
                if len(got_s) != len(want_s):
                    bad(pint + "要点版 %d 条，带色条的 %d 条" % (len(got_s), len(want_s)))
                elif [(a[0], a[1], a[2]) for a in got_s] != [(b[0], b[1], b[2]) for b in want_s]:
                    bad(pint + "要点版的侧位/说话人/要件号与完整版筛出来的对不上")
                elif [a[3] for a in got_s] != [b[3] for b in want_s]:
                    bad(pint + "要点版的文字与完整版筛出来的不一致")
                else:
                    ok(pint + "要点版 %d 条，正是完整版里带色条的那几条（逐字一致）" % len(got_s))

                if len(re.findall(r'<div class="cl-band"', slim)) != n_mark:
                    bad(pint + "要点版说明带 %d 条，应该 %d 条（每段开头那行要留着）"
                        % (len(re.findall(r'<div class="cl-band"', slim)), n_mark))
                else:
                    ok(pint + "要点版说明带 %d 条齐" % n_mark)
                if 'class="cl-note"' in slim:
                    bad(pint + "要点版里混进了结论条——那一版只放对话，结论留在完整版")
                if 'class="cl-gap"' in slim:
                    bad(pint + "要点版里混进了「中间省略 N 条」——精简版不该有这行")

                ms = re.search(r'data-cc-head="([^"]*)"', slim)
                sh = _html.unescape(ms.group(1)) if ms else ""
                mms = re.search(r"要点版（(\d+) 条）", sh)
                if not mms:
                    bad(pint + "要点版复制头没写「要点版（N 条）」：%s" % sh.replace("\n", " ")[:40])
                elif int(mms.group(1)) != len(got_s):
                    bad(pint + "要点版复制头条数不对：写 %s，实际 %d" % (mms.group(1), len(got_s)))
                else:
                    ok(pint + "要点版复制头写了「要点版（%s 条）」" % mms.group(1))

            # tab：两个、数字对得上、默认停在要点版
            tabs = re.findall(r'<button type="button" class="cl-tab[^"]*"[^>]*data-pane="(chat\d+k?)">'
                              r'[^<]*<b>(\d+)</b>', blk)
            n_slim_pg = len(msgs_of(slim_l[0])) if slim_l else -1
            n_full_pg = len(msgs_of(full))
            if len(tabs) != 2:
                bad(pint + "切换标签 %d 个，应该「要点版 / 完整版」两个" % len(tabs))
            else:
                d = dict(tabs)
                if d.get("chat%dk" % bi) != str(n_slim_pg) or d.get("chat%d" % bi) != str(n_full_pg):
                    bad(pint + "标签上写的条数与实际不符：%s（实际 %d / %d）"
                        % (tabs, n_slim_pg, n_full_pg))
                else:
                    ok(pint + "标签两个，条数都对（要点 %s / 完整 %s）"
                       % (d.get("chat%dk" % bi), d.get("chat%d" % bi)))
            if not re.search(r'class="cl-tab on"[^>]*data-pane="chat%dk"' % bi, blk):
                bad(pint + "默认没停在「要点版」——销售第一眼该看到精简版")
            else:
                ok(pint + "默认停在要点版")
            if len(re.findall(r'class="cl-chat cl-pane" id="chat\d+"[^>]* hidden>', blk)) != 1:
                bad(pint + "完整版没设 hidden，两版会同时铺在页面上")
            else:
                ok(pint + "同一时刻只露一版")
            if not re.search(r'data-lc="chat%d" data-lcgrp="%d"' % (bi, bi), blk):
                bad(pint + "复制按钮没绑 lcgrp，点了只会复制完整版")
            else:
                ok(pint + "复制按钮跟着当前这一版走")
        elif slim_l:
            bad(pint + "四要件那块不该拆两版（每条都挂着要件，切了看不出差别）")

    # 页面级：脚本引入 + 兜底
    if "assets/livechat.js" not in h:
        bad("页面没引 livechat.js，按钮点了没反应")
    else:
        jst = io.open(os.path.join(ROOT, "assets", "livechat.js"), encoding="utf-8").read()
        if "execCommand" not in jst:
            bad("livechat.js 没有 execCommand 兜底——双击本地打开（file://）复制会静默失败")
        elif "data-clgrp" not in jst:
            bad("livechat.js 没有切换逻辑，两个标签点了不动")
        else:
            ok("livechat.js 已引入，且带 file:// 兜底与切版逻辑")

    if "assets/livechat.css" not in h:
        bad("页面没引 livechat.css，聊天区会是一堆没样式的 div")

    # ---- 8. 口径补充段：客户不报名字，代称也算称呼（2026-11-10 确认） ----
    # 只查带口径分区的页面（接通建联）。代称清单以 03_依据文件/接通建联口径.md 为准：
    # 文档加了词页面没跟、页面自己改词、整段被删，三种都拦。
    if 'id="c-rule"' in h:
        terms = alias_terms()
        m_alias = re.search(r'<ul class="cc-alias">(.*?)</ul>', h, re.S)
        if not terms:
            bad("口径文档里找不到「代称清单」这一行，代称段无从核对")
        elif not m_alias:
            bad("缺「客户不报名字：代称也算称呼」这一段——客户不说名字时代称同样算 ②")
        else:
            got_a = [strip_tags(x).strip()
                     for x in re.findall(r"<li>(.*?)</li>", m_alias.group(1), re.S)]
            miss = [t for t in terms if t not in got_a]
            extra = [t for t in got_a if t not in terms]
            if miss or extra:
                bad("代称清单与口径文档不一致：缺 %s，多 %s" % (miss or "无", extra or "无"))
            else:
                ok("代称清单 %d 个，与口径文档逐项一致" % len(terms))
            if len(re.findall(r'class="vs vs-[yn]"', h)) != 2:
                bad("「算 / 不算」两栏对照不全——少了那一栏，边界就说不清")
            else:
                ok("算 / 不算 两栏对照齐")
            if "客户没说" not in h:
                bad("缺边界句：代称只在客户没给过名字时顶替，说过了就必须用上")
            else:
                ok("边界句在：说过了就必须用上")

    # ---- 9. 销售名不许露内部昵称（2026-11-10） ----
    # 导出的员工名是「陈舒-pearrrr」「体德智训-子渝（广州南京长沙）」这种内部备注名，
    # 案例页对外，只认侧写里的 sales_label。改侧写没重跑页面、或者手工改了标题，
    # 都会把内部名漏回来，这里拦一道。
    hit = [w for w in LEAK if w in h]
    if hit:
        bad("页面上出现了导出里的内部昵称：%s（应统一成 sales_label）" % hit)
    else:
        ok("销售名没有漏出内部昵称")


for p in PAGES:
    if os.path.isfile(p):
        check_page(p)
    else:
        bad("页面不存在：%s" % p)

print()
if bad_n:
    print("%d 项未通过" % bad_n)
    sys.exit(1)
print("全部通过")
