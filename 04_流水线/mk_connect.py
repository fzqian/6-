# -*- coding: utf-8 -*-
"""生成「接通建联.html」——阶段 1 的教材页，只留两块：口径 + 做对的。

口径的每一句都有出处：03_依据文件/接通建联口径.md 里逐条标了 [原文] / [解读]，
本文的 constants 与之逐字对齐，check_connect.py 会拿它去核（口径漂了要报错）。

「做对的」只有一组：黄荣庆 × 黄小姐，配一张整段聊天记录 + 四要件标注的长图
（assets/connect/c1.png，由 mk_connect_marks.py --span 生成）。

用法：python mk_connect.py
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "接通建联.html")
DATA = os.path.join(ROOT, "02_过程文件", "dialogs_connect.json")
MARK = os.path.join(ROOT, "assets", "connect", "c1.json")

D = json.load(io.open(DATA, encoding="utf-8"))
G = D[0]
MAN = json.load(io.open(MARK, encoding="utf-8"))

# 图片侧写里必须四个要件都在，否则页面写「四要件全过」就是假的
assert sorted(MAN["stages_hit"]) == ["1", "2", "3", "4"], \
    "侧写里只标到 %s，四要件没标全" % MAN["stages_hit"]
assert os.path.isfile(os.path.join(ROOT, "assets", "connect", "c1.png")), \
    "缺图：先跑 mk_connect_marks.py"

# ——— 四要件：名字、颜色、判什么，与长图完全同一套 ———
STAGES = [
    ("1", "自我介绍", "#2563EB", "我是谁", "姓名或称呼 + 身份来路，能被验证"),
    ("2", "称呼客户", "#7C3AED", "怎么叫他", "客户说了姓什么，下一句就用上"),
    ("3", "说明来意", "#0E9F6E", "谈什么", "接住线索里已有的信息，不重问一遍"),
    ("4", "客户回应", "#D97706", "他有没有接", "给信息、提问题、确认到具体点"),
]

# ——— 口径原文（逐字，改一个字都是改口径）———
Q_STD = "达到标准：有自我介绍 + 称呼客户 + 说明来意，客户有实质回应。"
Q_NO_HALF = ("符合下方要求则为“达到标准”，其余均为不达标，去除“部分达到”的模糊界限；")
Q_DIRECT = ("哈喽，你好！我是体德从业7年的健身教练x老师，有一线带训+健身房管理经验，"
            "国职+NASM双认证教练，怎么称呼你啊 同学？")
Q_DIRECT2 = ("哈喽，你好！我是体德智训负责招生+就业指导的x老师，看到你有咨询意向，"
             "咱们主要是想了解这边的环境、课程内容、证书区别、价格、吃住安排、还是就业方面呢？"
             "我先挑你感兴趣的讲。")
Q_TRANS = ("先看转接前的聊天记录。顺着用户原有意向承接沟通，不要重复问用户已经说过的信息，"
           "不从头开始打招呼问好，有前端沟通的铺垫可直入主题。")
Q_MUTE = ("如果您暂时比较忙也没关系，我先把校区排期/课程内容简单发您，您有空可以看下，"
          "有疑问随时找我/随时滴滴我。")
Q_ONCE = "一次询问不回复，直接输出价值信息，比如课程资料等。"
BANNED = ["喂喂喂，还了解吗？", "吱一声啊", "还在吗", "说句话呀",
          "在不在？看到回一下", "怎么不说话了？还考虑吗？"]

# ——— 判据表 ———
CRIT = [
    ("①", "自我介绍", "有没有报「我是谁」——姓名/称呼 + 身份来路",
     "只发一个你好；只报工号；开场白里没有自己是谁",
     "第 1 句：从业 4 年认证教练、6 年团队管理"),
    ("②", "称呼客户", "有没有给客户一个称呼，并且在客户说自己姓什么之后用上",
     "全程叫「同学」「亲」；客户说了姓，下一句还叫同学",
     "第 1 句问「怎么称呼你呀」，第 3 句「好滴黄小姐」"),
    ("③", "说明来意", "有没有讲清这通对话要谈什么，并且接住线索里已有的信息",
     "开口就问「你想了解什么」——客户已经说过一遍了",
     "第 3 句把留言三条一次复述"),
    ("④", "客户回应", "客户有没有给出信息、提出问题、或确认到具体点",
     "只回「嗯」「哦」「在忙」；全程没回",
     "第 4 句「是的呢」，第 6 句自己抛问题"),
]

# ——— 这一条会话 ———
CASE = dict(
    n=1, cust="黄小姐", staff="黄荣庆", tag="四要件全过",
    h3="一句话办两件事，四句就把线接通了",
    when="2026-09-29 11:44 起 ｜ 选段 39 条（整组 414 条）",
    img="c1",
    zoom="C-1 黄小姐 · 黄荣庆 · 第 0-38 条（四要件已在图上标色）",
    shotdesc="①第 1 条 ②第 1-3 条 ③第 3-4 条 ④第 6 条",
    what="""9 月 29 日上午 11:44，客户从官抖短视频进来，第一句只有三个字：你好啊。
黄荣庆回的第一句同时办了两件事——报了名字和资历（从业 4 年认证教练、6 年团队管理），
末尾挂一句「怎么称呼你呀」。客户答「姓黄 你可以叫我黄小姐」。下一句他没有继续叫同学：
先说「好滴黄小姐」，紧接着把客服留言里的三条一次读回去——人在河源、想了解国内国际认证区别、
目前零基础想学健身教练。客户只回了「是的呢」，但第四句就自己抛出问题：
「你们从零基础到拿证需要多久」。建联到这里结束，后面 30 多条是发资料、问健身习惯、问年龄，
属于需求沟通，不是这一阶段的判据。""",
    acts=[
        "自我介绍给的是<b>资历</b>不是头衔：从业 4 年、认证教练、6 年团队管理——客户第一眼要知道的是"
        "「你凭什么教我」，这三样都能被验证，也正好对应话术文档里那条示范句的写法。",
        "称呼<b>先问再叫</b>：不是全程「同学」「亲」，而是问「怎么称呼你呀」；客户说姓黄，"
        "下一句立刻「好滴黄小姐」。这一个来回就把陌生感削掉了一半。",
        "说明来意靠<b>复述</b>不靠发问：他把客服留言里的三条读回去，客户只需要回一个字确认。"
        "这正是话术文档对私域转接线索的要求——不重复问客户已经说过的信息。",
        "客户回应的判定不是「回了字」，是「提了问题」：从「你好啊」到「是的呢」到"
        "「你们从零基础到拿证需要多久」，第三句已经是主动要信息，接通了。",
    ],
    why="""这一条最值得讲的地方是：他把「我已经知道你什么」讲出来了。客户从短视频进来，
客服留言里已经留着她的情况和诉求，如果开口还是「你想了解什么」，客户就得重讲一遍——
这是私域转接最容易掉的分。他没问，他读回去，客户只需要确认。所以第四句就进正题了。<br><br>
另一处：全篇 414 条，<b>零禁区话术</b>——没有「还在吗」「在不在」「吱一声」，也没有催回复。
发完资料（第 27 条「内容比较多 你看完跟我说哈~」）客户回「好嘞」，他接着聊的是
「你今天应该上班吧」，不是「看了吗」。这对应文档里那条：一次询问不回复，直接输出价值信息。<br><br>
<b>要写清楚的一点</b>：这条会话最后没有成单（10 月 1 日客户说明年来不了，10 月 22 日转交给邓老师）。
但那是后面几个阶段的事，不影响这一阶段的判读——阶段 1 只判接通没接通，不判有没有成交。""",
    reuse=[
        ("哈喽哈喽，同学你好~ 我是体德从业4年的认证教练黄老师，有6年团队管理经验，怎么称呼你呀？",
         "一句里报完资历 + 要称呼，第 1 条就把 ①② 同时办掉"),
        ("哈哈哈 好滴黄小姐", "客户给了姓，下一句就用上——不是记下来下次再叫"),
        ("咱们客服这边留言信息 是人在河源 想了解国内国际认证区别 目前是零基础想学健身教练~",
         "把已知信息读回去，客户只需确认，不用重讲"),
        ("内容比较多 你看完跟我说哈~", "发完资料留一个出口，不追问「看了吗」"),
    ],
)

# ——— 记分牌 ———
def mm(k, text):
    return '<span class="mm c%s">%s</span>' % (k, text)


BOARD = "".join(mm(k, "%s%s" % ("①②③④"[i], nm)) for i, (k, nm, _c, _q, _s) in enumerate(STAGES))


# ——— hero 四卡 ———
HERO_STAGE = """
    <div class="stage4">%s
    </div>""" % "\n".join(
    """      <div class="st s{k}"><span class="stn">{circ}</span><b>{nm}</b>
        <span class="stk">{kind}</span><p>{q}</p>
        <span class="stq">{s}</span></div>""".format(
        k=k, circ="①②③④"[i], nm=nm, kind=("判销售的行动" if k != "4" else "判客户的动作"),
        q=q, s=s)
    for i, (k, nm, _c, q, s) in enumerate(STAGES))


# ——— C1 口径 ———
crit_rows = "\n".join(
    '<tr><td class="cno">%s</td><td><b>%s</b></td><td>%s</td><td class="cno2">%s</td>'
    '<td class="chit">%s</td></tr>' % (circ, nm, what, bad, hit)
    for circ, nm, what, bad, hit in CRIT)

ban_items = "\n".join('    <li>%s</li>' % b for b in BANNED)

RULE = """<section class="sec" id="c-rule">
<div class="sec-head rv"><div class="sec-no">C1 / 口径</div>
<h2>一条判据，四件事，全有才算</h2>
<p class="lead">阶段 1 只有一条标准，写在《招生老师沟通六阶段参考场景》里，原文是：
<b class="cc-q">「%s」</b><br>
四件事里 ①②③ 是销售的动作，④ 是客户的动作。把 ④ 也算进判据，是因为这一阶段的目的是
<b>接通</b>，不是<b>说完</b>——销售自言自语四句、客户一个字没回，仍然不达标。</p></div>

<div class="tbl-wrap rv cc-tblwrap"><table class="cc-tbl"><thead><tr>
<th>#</th><th>要件</th><th>判的是</th><th>不算（常见误判）</th><th>这条会话里</th>
</tr></thead><tbody>
%s
</tbody></table></div>

<div class="rv cc-notes">
  <div class="cn"><h4>没有「部分达到」</h4>
    <p>文档的统一标准第一条写得很硬：<b class="cc-q">「%s」</b></p>
    <p>落成两条执行规则：<b>不做 0.5 分</b>——三个要件齐、客户没回，是不达标，不是基本达标；
    <b>不按聊得久加分</b>——跟聊 3 句还是 30 句无关，一句话把四件办完也算达标。</p></div>

  <div class="cn"><h4>这一阶段不判内容质量</h4>
    <p>有没有讲价格、讲得专不专业、客户有没有被打动，都<b>不影响</b>阶段 1 的达标与否——
    那些属于后面的阶段。把这条守住，阶段之间才不会互相污染：不能因为后面谈崩了，
    回头把开头判成不达标。</p></div>

  <div class="cn"><h4>到哪里算结束</h4>
    <p>文档只写了怎么算达标，没写什么时候算完。这里定一条能用的边界：
    <b>客户开始主动提问、或开始给自己的生活信息，阶段 1 就结束了。</b>
    这条是本文自定的，文档没有，用处只有一个：判建联时只看建联那一段，
    不拿后面的表现倒推前面。</p></div>
</div>

<div class="rv cc-part">
  <h3>两种线索，两种开口</h3>
  <p>两类线索的差别只有一处：<b>开口时「已知信息」的多少</b>。用错类型最典型的症状，
  就是客户已经说过三遍的信息被问第四遍。</p>

  <div class="cc-lead2">
    <div class="l2"><span class="l2t">直接线索 · 陌生</span>
      <p class="l2q">%s</p>
      <p class="l2q">%s</p>
      <p class="l2n">自我介绍带资历 + 问称呼 + 给选项让客户挑切入点，①②③ 全靠这一句立起来。</p></div>
    <div class="l2 l2b"><span class="l2t">私域转接 · 已聊过</span>
      <p class="l2q">%s</p>
      <p class="l2n">③ 的重点变成<b>复述已知 + 确认</b>，不是问一遍。两类都要说明来意，
      但说什么算说明来意不一样。</p></div>
  </div>
</div>

<div class="rv cc-part">
  <h3>八句禁区</h3>
  <p>文档原话：这类话术带有催促、质问感，容易给陌生客户造成压迫感，引发反感、拉黑，
  新人尤其注意避开。开场与客户沉默唤醒，都要规避。</p>
  <ul class="cc-ban">
%s
    <li class="b2">发 无语 / 流汗 / 狗头 等不礼貌的表情</li>
  </ul>
  <p class="cc-fine">原文列了 6 句 + 一类表情。判违规看的是<b>意图</b>不是原句——
  「在吗」「哈喽？」「？？」这类追问同一件事的，都属于同一类。这一条是<b>一票否决</b>性质：
  四要件全齐但用了禁区话术，不算做得好。</p>
</div>

<div class="rv cc-part">
  <h3>客户不回的时候</h3>
  <p class="l2q">%s</p>
  <p>文档给的操作只有一句：<b class="cc-q">「%s」</b></p>
  <p>关键在<b>一次</b>：问一次不回，第二次就不要再问了，改成发东西。发完之后也不要追问
  看了吗——这条在下面那张卡里体现得很清楚。</p>
</div>

</section>""" % (Q_STD, crit_rows, Q_NO_HALF, Q_DIRECT, Q_DIRECT2, Q_TRANS, ban_items, Q_MUTE, Q_ONCE)


# ——— C2 做对的 ———
acts_html = "".join(
    '<li><i>%s</i><span>%s</span></li>' % ("①②③④"[i], t) for i, t in enumerate(CASE["acts"]))
reuse_html = "".join(
    '<li><b>「%s」</b><span>%s</span></li>' % (q, note) for q, note in CASE["reuse"])

CARD = """<article id="c{n}" class="qcard cc-case rv">
<div class="qcard-h"><span class="qcard-no">C-{n} {tag}</span><h3>{h3}</h3>
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
<a class="shotopen" href="assets/connect/{img}.png" target="_blank" rel="noopener">新窗口看原图 ↗</a></div>
<div class="shotwin"><div data-zoom="{zoom}"><img src="assets/connect/{img}.png" alt="C-{n} {cust}" loading="lazy"></div></div>
<div class="qshot-cap">窗口内上下滚动看完整段 · 点图放大（<code>assets/connect/{img}.png</code> 是同源原图，旁边的 <code>.json</code> 记着这张图渲染了哪几条原文、每条归哪个要件，可逐字比对）</div>
</figure>
</article>"""


def flat(s):
    import re
    return re.sub(r"\s*\n\s*", "", s.strip())


card = CARD.format(n=1, tag=CASE["tag"], h3=CASE["h3"], cust=CASE["cust"],
                   staff=CASE["staff"], when=CASE["when"], board=BOARD,
                   what=flat(CASE["what"]), acts=acts_html, why=flat(CASE["why"]),
                   reuse=reuse_html, img=CASE["img"], zoom=CASE["zoom"],
                   shotdesc=CASE["shotdesc"])

GOOD = """<section class="sec" id="c-good">
<div class="sec-head rv"><div class="sec-no">C2 / 做对的</div>
<h2>四句之内把线接通，客户自己开始问</h2>
<p class="lead">只留这一组：<b>黄荣庆与黄小姐</b>。选它不是因为它成单了——它没有成单。
选它是因为<b>四要件在图上都能一眼指出来，而且落在最关键的那一处</b>：客户从短视频进来，
客服留言里已经留着她的情况，他没有重问一遍。<br>
<span style="color:var(--ink3)">下面是一整段聊天记录，不是挑出来的几句。被标色的那几句就是四要件，
其余每一句都在。图上色条与标签只标一件事——这句话在完成哪个要件；一句话同时办两件事的，
色条就画两色。</span></p></div>

<div class="rv mm-intro"><h3>一组，四要件</h3>
<p>四色是四个要件，和顶部图例一一对应。第 1 条同时挂 ①②，第 3 条同时挂 ②③——
图上色条上下一分为二，标签写「②③」。点客户名直接跳到卡片。</p></div>
<div class="tbl-wrap rv mm-tblwrap"><table class="mm-tbl cc-quick"><thead><tr>
<th>组</th><th>员工</th><th>四要件</th><th>四件事落在哪一句</th><th>卡号</th>
</tr></thead><tbody>
<tr class="qt"><td><a class="qjump" href="#c1"><b>%s</b></a></td>
<td class="who">%s</td><td class="mmcell">%s</td>
<td>%s</td><td class="no">C-1</td></tr>
</tbody></table></div>

%s

</section>""" % (CASE["cust"], CASE["staff"], BOARD, CASE["shotdesc"], card)


# ——— 组装 ———
HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>接通建联｜体德智训 · 阶段 1</title>
<meta name="description" content="接通建联教材版：四要件怎么判（自我介绍 / 称呼客户 / 说明来意 / 客户回应）+ 一组从头看到尾的原文案例，聊天记录整段标色，逐字可查。">
<link rel="stylesheet" href="assets/style.css?v=10">
<link rel="stylesheet" href="assets/manual.css?v=2">
<link rel="stylesheet" href="assets/connect.css?v=1">
</head>
<body>

<div class="prov">
  <div class="prov-in">
    <p><span class="seg"><b>接通建联</b>　阶段 1 教材页，只留两块：怎么判、做对的</span><span class="seg"><em>口径</em>《招生老师沟通六阶段参考场景》阶段 1 + 《招生老师参考话术》</span></p>
    <p><span class="seg"><em>判据</em>自我介绍 + 称呼客户 + 说明来意 + 客户有实质回应，四项全有</span><span class="seg"><em>样例</em>黄荣庆 × 黄小姐，414 条逐句读过</span></p>
    <p><span class="seg"><em>截图</em>整段聊天记录 + 四要件标注，同名 <code>.json</code> 是渲染侧写</span><span class="seg"><em>回看</em><a href="口径与范本.html">价值传递教材版</a><a href="index.html">主报告</a></span></p>
  </div>
</div>

<nav class="nav">
  <div class="nav-in">
    <div class="nav-brand"><i></i><span>体德智训 · 接通建联</span></div>
    <div class="nav-links">
      <a href="#c-rule">一 · 口径</a>
      <a href="#c-good">二 · 做对的</a>
      <a href="口径与范本.html">价值传递教材版</a>
      <a href="index.html">← 主报告</a>
    </div>
  </div>
  <div class="nav-progress"></div>
</nav>

<header class="hero">
  <div class="hero-in">
    <div class="eyebrow">Stage 1 · 接通建联</div>
    <h1>第一次接触<br><em>四件事做完才算接通</em></h1>
    <p class="sub">这是六阶段的第一关，也是唯一一关<b>客户的动作也算进判据</b>：销售说完了不算，
    客户接了才算。这一页只讲两件事——<b>四要件怎么判</b>，和<b>一条做对了的完整对话</b>。
    不讲方法论，讲这个人当时说了哪句话、客户的下一句怎么变的。<b>聊天记录整段贴出来、按四色标好</b>，
    正文里每个「」都能在图上一句一句找到——讲案例时可以直接投屏，从上往下划。%(stage)s
    <div class="hero-meta"><span>口径逐字来自两份招生培训文档，标了 [原文] 的不改动一个字</span><span>聊天记录整段可查</span></div>
  </div>
</header>

%(rule)s

%(good)s

<footer class="foot">
  <div class="eyebrow">Stage 1 · Connect</div>
  <p>接通建联 · 判据取自《招生老师沟通六阶段参考场景》阶段 1、《招生老师参考话术》§一 破冰话术 ｜ 样例：黄荣庆 × 黄小姐（官抖短视频线索），414 条，2026-09-29 至 10-22 ｜ 逐句读过原文，非词表命中</p>
</footer>

<div class="lb" id="lb">
  <button class="lb-close" aria-label="关闭">×</button>
  <img id="lbImg" alt="">
  <div class="lb-cap" id="lbCap"></div>
</div>

<script src="assets/app.js?v=10"></script>
</body>
</html>
""" % dict(stage=HERO_STAGE, rule=RULE, good=GOOD)

io.open(OUT, "w", encoding="utf-8", newline="").write(HTML)

print("写出", OUT)
print("口径段 %d 字 ｜ 案例 1 组 ｜ 四要件 %s" % (len(RULE), BOARD.replace("<span class=\"mm ", "").split(">")[0]))
print("  C-1 %s × %s  %s" % (CASE["staff"], CASE["cust"], CASE["img"] + ".png"))
