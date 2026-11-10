# -*- coding: utf-8 -*-
"""教材版页面：把「口径」和「做对的」两块单独抽出来给销售讲案例用。

为什么口径是「切」不是「重写」
────────────────────────────
口径那一段每一句都是判读结论，抄第二遍就会漂——主页面改了、教材版没改，
两处口径不一致，比没有教材版更糟。所以 #rule 直接从已生成的 `价值传递.html`
切出来，一个字不动。

「做对的」这一段现在只留两组（2026-11-10 第二次改版）：
  子渝 × 长生     三项依次走完：形态 → 出口 → 落点
  陈舒 × 姜彦博   三项顺序打乱：落点 → 形态 → 出口
两张卡不再用「精选片段 + 小截图」，改成**整段聊天记录 + 三色标注的长图**
（assets/mark/mc1.png / mc2.png，由 mk_stage_marks.py --span 生成）：
色条标出哪几句是形态、哪几句是出口、哪几句是落点，读者从上往下一路看下来，
既看得到完整过程，也知道该看哪几句。

只做四件改造（相对主页面）：
  1) 编号 V1/V4 → M1/M2
  2) 卡号 M-1/M-2，每张卡挂 anchor
  3) qcard-meta 里的三项换成三色记分牌（和顶部图例一一对应）
  4) M2 开头插一张两行速查表：点一行跳一张卡

用法：python mk_manual.py
"""
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "价值传递.html")
OUT = os.path.join(ROOT, "口径与范本.html")
DATA = os.path.join(ROOT, "02_过程文件", "value_all.json")

src = io.open(SRC, encoding="utf-8").read()
ROWS = json.load(io.open(DATA, encoding="utf-8"))["rows"]
BY = {}
for r in ROWS:
    if r[1] != "—" and r[0] not in BY:
        BY[r[0]] = r


def slice_sec(s, sid):
    a = s.index('<section class="sec" id="%s">' % sid)
    b = s.index("</section>", a) + len("</section>")
    return s[a:b]


# ——— 1. 口径：原样切出来，只改编号与一处跨页引用 ———
rule = slice_sec(src, "rule")
rule = rule.replace('id="rule"', 'id="m-rule"').replace("V1 / 口径", "M1 / 口径")
rule = rule.replace("下面每一张卡片、逐组表里每一行", "下面每一张卡片、速查表里每一行")


# ——— 2. 两个案例 ———
CASES = [
    dict(
        n=1, cust="长生", staff="子渝", pat=1, tag="三项全过",
        h3="从头到尾一句不催，客户自己把付款时间定出来",
        when="10.10 18:24 → 10.11 16:59 ｜ 选段 74 条（整组 234 条）",
        img="mc1",
        zoom="M-1 长生 · 子渝 · 选段 74 条（形态 / 出口 / 落点已在图上标色）",
        shotdesc="三段依次走完：形态在 18-41、出口在 42-57、落点在 63-91",
        what="""10.10 傍晚客户先问「两万多费用是包含这些考证，还是单纯进修」，销售没直接答价，
先把证书、课程内容、438 节课清单一条条发过去；20:09 讲就业流程，20:12 客户说
「具体怎么选择，明天给答复你」。第二天 16:59 客户改口：「哎，还是先考证」「最近家里也困难」
「先去考证当教练，当出一点成绩再进修」。销售没有劝、没有降价，只回了两句：
「剩下线下到了再补尾款都可以的」「那咱们就先安心考证，先做出成绩来了」。客户回「OK OK」。""",
        acts=[
            "一句话里三件都在：三个月 438 节课系统培训、九个月线上课程、两年内免费复训——"
            "都在同一条清单里，客户不用追问三个月之后怎么办。",
            "出口讲的是可数的东西：五个左右的优质就业单位、辅导面试、上岗跟进，"
            "另一条路是推荐到集团自有品牌——客户能自己算这笔钱换回什么。",
            "客户说困难，不谈价格谈结构：尾款改到线下补，再顺着客户自己那句"
            "「当出一点成绩再进修」给一句「先安心考证」——方案是照客户的话改的，不是照价格表改的。",
        ],
        why="""客户说「最近家里也困难」，最常见的接法是降价、送东西、或者今天定有优惠。这一组
反过来：先把支付方式改软，再说一句「我能做的就提升对你的服务质量」，最后不是逼单，而是
「我们同龄，你可以跟家里说说，关键时刻需要家里帮忙说出来并不丢人」。整段没有一句在推，
客户反而被当成年纪相仿的人对待——第二天自己把方案定成「先考证」。""",
        reuse=[
            ("剩下线下到了再补尾款都可以的", "不降价，改支付节奏"),
            ("那咱们就先安心考证，先做出成绩来了", "接客户自己说的「当出一点成绩再进修」，不另起一套"),
            ("我能做的就提升对你的服务质量", "客户说困难时，不承诺优惠，只承诺服务"),
            ("我们同龄，你可以跟家里说说，关键时刻需要家里帮忙说出来并不丢人", "把决定权交回去，不逼单"),
        ],
    ),
    dict(
        n=2, cust="姜彦博", staff="陈舒", pat=1, tag="三项全过",
        h3="一句话把三件说完，把就业讲成一条时间线",
        when="10.15 09:20 → 10.22 14:07 ｜ 整组 96 条",
        img="mc2",
        zoom="M-2 姜彦博 · 陈舒 · 整组 96 条（形态 / 出口 / 落点已在图上标色）",
        shotdesc="三段顺序打乱：落点在 30-35、形态在 49-51、出口在 85-91",
        what="""10.15 早上开场，销售先问「请问咱是单纯自我提升还是有打算做教练呀」，客户说做教练、
练了快一年。之后聊到 05 年、温州、建筑工程专业、实习半年。聊到一半销售自己喊停：
「坏了忘了正事，光顾着唠嗑了」，把课程大纲发过去，一句
「线下系统学习课程是线下三个月集训➕九个月线上课➕两年内一次免费复训的权益」把三件说完。
客户问费用、问吃住、问班期，销售推长沙校区（「我跟刚哥都在这边」）。13:31 说
「对啦还有一个板块没讲」——就业，把第四阶段怎么教包装、毕业时谁帮忙做简历、
毕业后第 1/3/6 个月谁回访讲完。10.22 回访，开口问的是「有了解过教练的薪资结构和淡旺季啵」。""",
        acts=[
            "一句话三件，下一句只补两个字「组成」，不铺垫、不分三段——客户刚问完课程大纲就拿到了全部形态。",
            "出口讲成时间线：课程第四阶段就教营销包装和授课转化，毕业前班主任和就业老师拍形象照、"
            "做简历，毕业后「第一、三、六个月都会有就业老师定期地去回访」——客户能算清什么时候有人管我。",
            "客户说「都可以，看就业怎么样」，销售立刻给出推荐逻辑——"
            "「主要咱推荐就业的时候也是根据」「持有的证书、体型去推荐的」。不是一句我们就业好，是按你的情况推荐。",
        ],
        why="""落点之所以成立，是因为三个变量全是客户刚提过的：城市、证书、体型——没有一个是销售
自己加的宣传口径。这组也是三项顺序打乱还成立的最好例子：落点先来，形态在后，出口最后，
客户照样往下走。<b>但也有一处没做完</b>：客户说实习了半年建筑，这是整组最硬的一条事实
（真在工地待过、真要转行），销售却用「坏了忘了正事」把它掐断，转去发课程大纲，后面也再没
回到为什么离开建筑。整组 96 条，销售没报出过一个数字——既没有教练月薪多少，也没有五个
单位是哪些，所以出口讲得再细，客户仍然不知道值不值。这也是它出口讲到 3 条、却没有
成单闭环的原因。""",
        reuse=[
            ("线下系统学习课程是线下三个月集训➕九个月线上课➕两年内一次免费复训的权益", "三件一句话，客户不追问"),
            ("根据咱想去的城市、证书、体型去推荐", "不喊一句我们就业好，改成按你的情况推荐"),
            ("咱就业方面的帮助首先体现在课程设置上", "就业不是毕业才管，从第四阶段课程就开始了"),
            ("咱们了解行业不能只看好的一面嘛", "10.22 回访的切入点：谈薪资淡旺季之前先认账"),
        ],
    ),
]

# meta 里的三项必须与判读表一致——防止「卡片写错组」的唯一硬约束
for c in CASES:
    r = BY.get(c["cust"])
    assert r, "value_all.json 里找不到这一组：%s" % c["cust"]
    c["f"], c["o"], c["land"] = r[2], r[3], r[4]
    assert r[2] == 3 and r[4] == 1, "这组不是三项全过，不该进教材版：%s" % c["cust"]
    assert r[8] == c["staff"], "员工对不上：%s 页面写 %s，表里是 %s" % (c["cust"], c["staff"], r[8])
    png = os.path.join(ROOT, "assets", "mark", c["img"] + ".png")
    assert os.path.isfile(png), "缺图：%s（先跑 mk_stage_marks.py）" % png


# ——— 3. 三色记分牌 ———
def chip(kind, ok, text):
    cls = {1: "k1", 2: "k2", 3: "k3"}[kind] + ("" if ok else " off")
    return '<span class="mm %s">%s</span>' % (cls, text)


def board(c):
    dots = "".join("●" if k < c["f"] else "○" for k in range(3))
    return "%s%s%s" % (
        chip(1, c["f"] == 3, "形态 %s" % dots),
        chip(2, c["o"] >= 1, "出口 %d" % c["o"]),
        chip(3, c["land"], "落点 %s" % ("✓" if c["land"] else "✗")))


# ——— 4. 卡片 ———
CARD = """<article id="m{n}" class="qcard p{pat} mcase rv">
<div class="qcard-h"><span class="qcard-no">M-{n} {tag}</span><h3>{h3}</h3>
<div class="qcard-meta">{cust} ｜ {staff} ｜ {when} ｜ {board}</div></div>
<div class="mcase-body">
<div class="qblock"><div class="qlabel">发生了什么</div><p>{what}</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">{acts}</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>{why}</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><ul class="mclist">{reuse}</ul></div>
</div>
<figure class="mcase-shot">
<input type="checkbox" id="sw{n}" class="swchk">
<div class="shotbar"><span class="sbt">原文截图 · 整段聊天记录</span><span class="sbd">{shotdesc}</span>
<label class="swtoggle" for="sw{n}"><span class="t1">展开全部 ↓</span><span class="t2">收起 ↑</span></label>
<a class="shotopen" href="assets/mark/{img}.png" target="_blank" rel="noopener">新窗口看原图 ↗</a></div>
<div class="shotwin"><div data-zoom="{zoom}"><img src="assets/mark/{img}.png" alt="M-{n} {cust}" loading="lazy"></div></div>
<div class="qshot-cap">窗口内上下滚动看完整段 · 点图放大（<code>assets/mark/{img}.png</code> 是同源原图，旁边的 <code>.json</code> 记着这张图渲染了哪几条原文，可逐字比对）</div>
</figure>
</article>"""


def indent(s, pad="      "):
    s = re.sub(r"\s*\n\s*", "", s.strip())
    return s


cards = []
for c in CASES:
    acts = "".join(
        '<li><i>%s</i><span>%s</span></li>' % ("①②③"[i], indent(t))
        for i, t in enumerate(c["acts"]))
    reuse = "".join(
        '<li><b>「%s」</b><span>%s</span></li>' % (q, note) for q, note in c["reuse"])
    cards.append(CARD.format(
        n=c["n"], pat=c["pat"], tag=c["tag"], h3=c["h3"], cust=c["cust"],
        staff=c["staff"], when=c["when"], board=board(c),
        what=indent(c["what"]), acts=acts, why=indent(c["why"]), reuse=reuse,
        img=c["img"], zoom=c["zoom"], shotdesc=c["shotdesc"]))


# ——— 5. 速查表（两行）———
TYPE = {1: "三项全过", 2: "出口", 3: "落点"}
trs = []
for c in CASES:
    trs.append(
        '<tr class="qt p%d"><td><a class="qjump" href="#m%d"><b>%s</b></a></td>'
        '<td class="who">%s</td><td class="mmcell">%s</td>'
        '<td>%s</td><td>%s</td><td class="no">M-%d</td></tr>'
        % (c["pat"], c["n"], c["cust"], c["staff"], board(c),
           "形态 → 出口 → 落点" if c["n"] == 1 else "落点 → 形态 → 出口",
           c["h3"], c["n"]))

good = """<section class="sec" id="m-good">
<div class="sec-head rv"><div class="sec-no">M2 / 做对的</div>
<h2>两组从头看到尾：三段是怎么落在真实对话里的</h2>
<p class="lead">只留两组，都从第一句看到最后一句：一组是<b>子渝与长生</b>，一组是<b>陈舒与姜彦博</b>。
选它们不是因为分数最高，而是因为<b>三项在图上都能一眼指出来</b>——长生是三段依次走完
（形态 → 出口 → 落点），姜彦博是三项顺序打乱（落点先来，形态、出口在后）。
两组放在一起，正好说明一件事：<b>顺序可以变，三项不能缺</b>。<br>
<span style="color:var(--ink3)">下面每张卡右边是一整段聊天记录，不是挑出来的几句：被标色的那几句就是三项，
横线以上的每一句都在。图上色条与标签各标一件事——这句话在干什么。</span></p></div>

<div class="rv mm-intro"><h3>两组，两种走法</h3>
<p>左边三色是这组的三项成绩，中间写着<b>三段出现的先后</b>。点客户名直接跳到那张卡——
图上每个「」都能在旁边的 <code>.json</code> 里逐字找到。</p></div>
<div class="tbl-wrap rv mm-tblwrap"><table class="mm-tbl"><thead><tr>
<th>组</th><th>员工</th><th>三项</th><th>出现的顺序</th><th>这张卡看什么</th><th>卡号</th>
</tr></thead><tbody>
%s
</tbody></table></div>

%s

</section>""" % ("\n".join(trs), "\n\n".join(cards))


# ——— 6. 组装 ———
HERO_STAGE = """
    <div class="stage3">
      <div class="st s1"><span class="stn">①</span><b>形态</b>
        <span class="stk">客户心里的问题</span><p>我买的到底是什么</p>
        <span class="stq">三个月线下 + 九个月线上 + 两年复训，三件都在</span></div>
      <div class="st s2"><span class="stn">②</span><b>出口</b>
        <span class="stk">客户心里的问题</span><p>买完能得到什么</p>
        <span class="stq">就业路径 / 收入区间 / 证书去向，至少一条讲透</span></div>
      <div class="st s3"><span class="stn">③</span><b>落点</b>
        <span class="stk">客户心里的问题</span><p>跟我有什么关系</p>
        <span class="stq">挂到客户说过的话上，他下一句要变具体</span></div>
    </div>"""

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>口径与范本｜体德智训 · 价值传递</title>
<meta name="description" content="价值传递教材版：三项怎么判（形态 / 出口 / 落点）+ 两组从头看到尾的原文案例，聊天记录整段标色，逐字可查。">
<link rel="stylesheet" href="assets/style.css?v=10">
<link rel="stylesheet" href="assets/manual.css?v=2">
</head>
<body>

<div class="prov">
  <div class="prov-in">
    <p><span class="seg"><b>口径与范本</b>　给销售讲案例用，只留两块：怎么判、做对的</span><span class="seg"><em>切口</em>口径与《价值传递》同源切出，不重写一个字</span></p>
    <p><span class="seg"><em>口径</em>《判断标准.md》§1.2 三条硬标准 · §1.3 一票否决</span><span class="seg"><em>样例</em>两组完整对话，逐句读过原文</span></p>
    <p><span class="seg"><em>截图</em>整段聊天记录 + 三色标注，同名 <code>.json</code> 是渲染侧写，可逐字比对</span><span class="seg"><em>回看</em><a href="价值传递.html">完整版《价值传递》</a><a href="index.html">主报告</a></span></p>
  </div>
</div>

<nav class="nav">
  <div class="nav-in">
    <div class="nav-brand"><i></i><span>体德智训 · 口径与范本</span></div>
    <div class="nav-links">
      <a href="#m-rule">一 · 口径</a>
      <a href="#m-good">二 · 做对的</a>
      <a href="接通建联.html">阶段 1 接通建联</a>
      <a href="价值传递.html">完整版</a>
      <a href="index.html">← 主报告</a>
    </div>
  </div>
  <div class="nav-progress"></div>
</nav>

<header class="hero">
  <div class="hero-in">
    <div class="eyebrow">Value Delivery · 教材版</div>
    <h1>三段怎么判<br><em>做对的怎么讲</em></h1>
    <p class="sub">一页只讲两件事：<b>三项分开怎么判</b>，和<b>两段做对了的完整对话</b>。不讲方法论，
    讲的是这两个人当时说了哪句话、客户的下一句怎么变的。<b>聊天记录整段贴出来、按三色标好</b>，
    正文里每个「」都能在图上一句一句找到——讲案例时可以直接投屏，从上往下划。%(stage)s
    <div class="hero-meta"><span>形态＝讲的件数、出口＝讲透几条、落点＝客户下一句变没变；三项独立算，不合并成一个分数</span><span>聊天记录整段可查</span></div>
  </div>
</header>

%(rule)s

%(good)s

<footer class="foot">
  <div class="eyebrow">Value Delivery · Manual</div>
  <p>口径与范本 · 取自《价值传递》的「口径」一块，加两组从头看到尾的完整对话 ｜ 99 组（子渝 41 + 陈舒 55 + 重点 3）里三项全过 11 组，这两组是其中三段最好指认的两组 ｜ 逐句读过原文，非词表命中</p>
</footer>

<div class="lb" id="lb">
  <button class="lb-close" aria-label="关闭">×</button>
  <img id="lbImg" alt="">
  <div class="lb-cap" id="lbCap"></div>
</div>

<script src="assets/app.js?v=10"></script>
</body>
</html>
""" % dict(stage=HERO_STAGE, rule=rule, good=good)

io.open(OUT, "w", encoding="utf-8", newline="").write(HTML)

print("写出", OUT)
print("案例 %d 组｜口径段 %d 字" % (len(CASES), len(rule)))
for c in CASES:
    print("  M-%d %-6s %-4s 形%s 出%s 落%s  %s" % (
        c["n"], c["cust"], c["staff"], c["f"], c["o"],
        "✓" if c["land"] else "✗", c["img"] + ".png"))
