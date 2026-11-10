# -*- coding: utf-8 -*-
"""生成「价值传递专项」单页：价值传递.html

数据：value_all.json（子渝 48 行 + 陈舒 55 行 = 103 行，其中 96 组进入价值传递）
输出：C:/Users/admin/Desktop/体德报告_子渝六阶段质检/价值传递.html
"""
import json
import io
import re
import os

# 数据目录：本脚本可能和 value_all.json 不在同一个目录（归档在 04_流水线 时会这样）
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA = "."
if not os.path.isfile(os.path.join(DATA, "value_all.json")):
    _alt = os.path.join(_HERE, "..", "02_过程文件")
    if os.path.isfile(os.path.join(_alt, "value_all.json")):
        DATA = _alt
    elif os.path.isfile(os.path.join(_HERE, "value_all.json")):
        DATA = _HERE


def data_path(name):
    return os.path.join(DATA, name)


V = json.load(open(data_path("value_all.json"), encoding="utf-8"))
ROWS = V["rows"]
META = V["meta"]
OUT = r"C:/Users/admin/Desktop/体德报告_子渝六阶段质检/价值传递.html"

n_all = len(ROWS)
skip = [r for r in ROWS if r[1] == "—"]
base = n_all - len(skip)                      # 99：真正进入价值传递的组
f3 = [r for r in ROWS if r[2] == 3]
o1 = [r for r in ROWS if r[3] >= 1]
o2 = [r for r in ROWS if r[3] >= 2]
l1 = [r for r in ROWS if r[4] == 1]
veto = [r for r in ROWS if r[5] == 1]
strict = [r for r in ROWS if r[2] == 3 and r[3] >= 1 and r[4] == 1 and r[5] == 0]
wide = [r for r in ROWS if r[2] >= 2 and r[3] >= 1 and r[4] == 1 and r[5] == 0]
# 用户指定的重点线索（第 10 位为 1），已并入同一个分母，只靠底色区分
FO = [r for r in ROWS if len(r) > 9 and r[9] == 1]


def staff_of(r):
    return r[8] if len(r) > 8 else ""


def batch_of(r):
    """三段来源：子渝批 / 陈舒批 / 重点批（另外三位老师各一组）。"""
    s = staff_of(r)
    if s == "子渝":
        return "子渝批"
    if s == "陈舒":
        return "陈舒批"
    return "重点批"


BATCHES = ["子渝批", "陈舒批", "重点批"]
BN = {b: sum(1 for r in ROWS if batch_of(r) == b and r[1] != "—") for b in BATCHES}


def rate(rows, key):
    n = len([r for r in rows if r[1] != "—"])
    if not n:
        return 0
    return round(sum(1 for r in rows if key(r) and r[1] != "—") * 100.0 / n)



def dot(n, total=3):
    return "●" * n + "○" * (total - n)


def rows_html():
    out = []
    _last = None
    _grp_style = ("background:#F3F1EB;font-size:11.5px;font-weight:800;letter-spacing:.06em;"
                  "color:#6B665C;padding:9px 12px;border-top:1px solid var(--line)")
    # 重点四组：整行琥珀底 + 左侧色条，靠颜色认出「这是你点名要跟的那四组」
    _fo_style = "background:#FDF6E3"
    _fo_cell = "box-shadow:inset 3px 0 0 var(--amber)"
    for r in ROWS:
        cust, line, f, o, l, v, concl, note = r[:8]
        staff = staff_of(r)
        fo = r[9] if len(r) > 9 else 0
        b = batch_of(r)
        if concl == "好":
            tag = '<span class="chip">好</span>'
        elif concl == "中":
            tag = '<span class="chip gray">中</span>'
        elif concl == "差":
            tag = '<span class="chip red">差</span>'
        else:
            tag = '<span class="num">—</span>'
        if v == 1:
            tag += ' <span class="chip red">否决</span>'
        if fo:
            tag = ('<span class="chip" style="background:var(--amber);'
                   'border-color:var(--amber);color:#fff">重点</span> ') + tag
        if b != _last:
            _rows = sum(1 for x in ROWS if batch_of(x) == b)
            _ok = sum(1 for x in ROWS if batch_of(x) == b and x[1] != "—")
            _tail = "　·　另外三位老师的在跟线索，琥珀底" if b == "重点批" else ""
            out.append('<tr><td colspan="8" style="%s">%s　%d 行 · %d 组进入价值传递%s</td></tr>'
                       % (_grp_style, b, _rows, _ok, _tail))
            _last = b
        out.append(
            "<tr%s><td%s>%s</td><td class='who'>%s</td><td>%s</td><td class='num'>%s</td><td class='num'>%d</td>"
            "<td class='num'>%s</td><td>%s</td><td>%s</td></tr>"
            % (' style="%s"' % _fo_style if fo else "",
               ' style="%s"' % _fo_cell if fo else "", cust, staff, line, dot(f), o,
               "✓" if l else "—", tag,
               note.replace("「", "").replace("」", "")))
    return "\n".join(out)


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>价值传递专项｜体德智训 · 子渝 + 陈舒 + 重点四组</title>
<meta name="description" content="99 组会话（子渝 41 + 陈舒 55 + 重点 3）逐组判读：形态 / 出口 / 落点三项分开算，谁做对了、谁做错了、错在哪一步；你点名的四组用琥珀底色标出。">
<link rel="stylesheet" href="assets/style.css?v=10">
</head>
<body>

<div class="prov">
  <div class="prov-in">
    <p><span class="seg"><b>价值传递专项</b>　子渝（广州 / 南京 / 长沙）＋ 陈舒　合并 <b>99 组</b></span><span class="seg"><em>结构</em>三批并成一张总盘，同一个分母、同一套三项口径</span></p>
    <p><span class="seg"><em>子渝</em>快照 <code>261109_0947_47985</code> · 48 组 / 3,267 条 <span class="nb">· 41 组进入价值传递</span></span><span class="seg"><em>陈舒</em>快照 <code>261110_0917_48110</code> · 105 组 / 7,433 条 <span class="nb">· 55 组进入价值传递</span></span></p>
    <p><span class="seg"><em>重点</em>4 组 <code>261109_1747_48051</code> / <code>261110_0932_48111</code> / <code>261110_0934_48112</code> / <code>261110_0935_48113</code> <span class="nb">· 其中姜彦博与陈舒批同一份会话，去重后新增 3 组</span></span></p>
    <p><span class="seg"><em>依据</em>《判断标准.md》§1.2 三条硬标准 · §1.3 一票否决 · §1.4 四种失败型</span><span class="seg"><em>底稿</em><a href="00_数据来源说明.md">00_数据来源说明</a><a href="02_过程文件/">02_过程文件</a><a href="01_原始导出/">01_原始导出</a><a href="04_流水线/README_质检报告流水线.md">04_流水线</a></span></p>
  </div>
</div>

<nav class="nav">
  <div class="nav-in">
    <div class="nav-brand"><i></i><span>体德智训 · 价值传递</span></div>
    <div class="nav-links">
      <a href="#rule">口径</a>
      <a href="#numbers">三个数字</a>
      <a href="#combo">缺在哪</a>
      <a href="#good">做对的</a>
      <a href="#bad">做错的</a>
      <a href="#veto">一票否决</a>
      <a href="#table" class="nav-focus">逐组对照</a>
      <a href="index.html">← 主报告</a>
    </div>
  </div>
  <div class="nav-progress"></div>
</nav>

<header class="hero">
  <div class="hero-in">
    <div class="eyebrow">Value Delivery · 2026</div>
    <h1>价值传递<br><em>专项</em>体检</h1>
    <p class="sub">只回答一件事：客户问「学这个对我有什么用」的时候，他答上来了没有。<b>三个招生批次、99 组会话</b>逐组读过，三项分开算，不合并成一个分数——因为这三项缺哪一项，客户的反应是不一样的。<b>你点名的四组也在里面</b>，不单开一节，只用琥珀底色标出来。</p>
    <div class="hero-stats">
      <div><b>__H1__</b><span>组讲全产品形态</span></div>
      <div><b>__H2__</b><span>组讲过出口</span></div>
      <div><b>__H3__</b><span>组把话落到客户身上</span></div>
      <div><b>__H4__</b><span>组三项全过</span></div>
    </div>
    <div class="hero-quote">不是不会讲，是讲的<em>东西没落在这一个人身上</em>。形态 __H1__ 组讲全、出口 __H2__ 组讲过，能把话接到客户自己说过的目的上的，只有 __H3__ 组；三项同时成立的，__H4__ 组（__H4P__%）。</div>
    <div class="hero-meta"><span>分母 __N__ 组（子渝 41 + 陈舒 55 + 重点新增 3；合计 157 组导出里，58 组没进入价值传递：内部客服、已报名学员、客户 0 条、只问 WiFi 与密码）</span><span>逐组判读，非词表命中</span></div>
  </div>
</header>

<section class="sec" id="rule">
<div class="sec-head rv"><div class="sec-no">V1 / 口径</div><h2>三件事，分开判、不合并</h2><p class="lead">这套口径来自《判断标准.md》§1.2，原本用来判「一组对话的价值传递达不达标」。这里把它拆成三项，是因为诊断时要知道<strong>断在哪一项</strong>，而不是只知道「不达标」。</p></div>

<div class="tbl-wrap rv"><table><thead><tr><th>项</th><th>客户心里的问题</th><th>怎么算过</th><th>怎么算不过</th></tr></thead><tbody>
<tr><td><b>形态</b></td><td>我买的到底是什么</td><td>3 个月线下 + 9 个月线上 + 两年复训，三件都出现过（对单考证客户：四天 / 线下 / 3500 一价含培训与考证）</td><td>只讲「三个月」→ 客户只知道要脱产三个月，不知道三个月之后还有什么</td></tr>
<tr><td><b>出口</b></td><td>买完能得到什么</td><td>就业路径（谁推荐、推荐到哪、辅导什么）、收入区间（有数字）、证书去向（谁发、什么用），至少一条讲到客户能自己判断值不值</td><td>只报名词：「就业推荐」「含金量高」——客户听完还是不知道能去哪、能拿多少</td></tr>
<tr><td><b>落点</b></td><td>跟我有什么关系</td><td>把话挂到客户自己说过的目的或处境上，<b>且客户下一句变具体或给出动作</b></td><td>挂一句「你本身有健身底子」然后继续念体系——那不是落点，是插了句称呼</td></tr>
</tbody></table></div>

<div class="judge rv"><b>一条否决　</b>客户说贵，销售只改价格、不解释贵在哪 → 这一组直接判差，不管形态讲得多全。《判断标准.md》§1.3 原文口径。</div>
<div class="judge rv"><b>一项没算　</b>「客户有没有被打动」不进这张表。那是主观判断，机器和人都容易自我说服；只记客户下一句说了什么。</div>

<div class="judge rv"><b>三批怎么并　</b>子渝 48 组、陈舒 105 组、你点名的 4 组，先各自剔掉进不了价值传递的（内部客服、已报名学员、客户不足 3 句、只问 WiFi 与密码、双方都没提课程/价格/就业），剩下 <b>41 + 55 + 3 = 99 组</b>，再按同一套三项口径逐组判。<b>合并只发生在计数这一层</b>：每一组的判读依据都留在 <code>02_过程文件/value_all.json</code> 里，谁都能挑一组回原文核。<br><span style="color:var(--ink3)">一处直说：陈舒批是按「价值段」判的（客户全部发言 + 销售讲形态/出口/价格的句子），子渝批与重点四组是逐句全读。所以数字<b>看比例、看结构</b>是可靠的，别把它当成同一精度的 99 份抽样——差别在证据密度，不在判定标准。</span></div>

<div class="focus-bar rv"><b>琥珀底色 = 重点</b><span>下面每一张卡片、逐组表里每一行，凡是<b>琥珀底</b>的都是你点名的四组：姜彦博、王永正、李小东、銀河。<b>它们不进单独的板块，也不算另一套分母</b>——和其余 95 组同一个池子、同一套口径，只是给它们留了一个能一眼认出来的颜色。四张卡里都多一块「下一步」，那是写给具体的人看的，不是方法论。</span></div>

<div class="judge rv"><b>一处去重　</b>四组里的<b>姜彦博</b>，和你之前给我的陈舒 105 组导出里那一条是<b>同一份会话</b>——96 条消息逐条相同，只是员工备注名一个是「陈舒-pearrrr」、一个是「陈舒-？」。所以 4 组并进来只增加 <b>3 组</b>，分母是 99 而不是 100。这一组的判读也按逐句细读的那一版统一了（原来记「缺落点」，细读后是三项全过），改动写在 <code>value_all.json</code> 的 note 里。</div>
</section>

<section class="sec" id="numbers">
<div class="sec-head rv"><div class="sec-no">V2 / 三个数字</div><h2>形态最容易被「看起来讲了」，落点最难</h2><p class="lead">三项的达标率差得很远，而且原因各不相同。</p></div>

<div class="funnel rv"><h3>三项各自的达标组数（分母 __N__）</h3><p class="hint">三项独立算，不互为前提；最右列是相对 __N__ 组的缺口。</p>
<div class="fn-row"><div class="fn-lbl"><b>形态</b>　三件套讲全</div><div class="fn-track"><div class="fn-fill" style="width:__W1__%">__H1__</div></div><div class="fn-drop">__D1__</div></div>
<div class="fn-row"><div class="fn-lbl"><b>出口</b>　至少一条讲透</div><div class="fn-track"><div class="fn-fill" style="width:__W2__%">__H2__</div></div><div class="fn-drop">__D2__</div></div>
<div class="fn-row"><div class="fn-lbl"><b>落点</b>　客户下一句变具体</div><div class="fn-track"><div class="fn-fill" style="width:__W3__%">__H3__</div></div><div class="fn-drop">__D3__</div></div>
<div class="fn-row last"><div class="fn-lbl"><b>三项全过</b>　且无一票否决</div><div class="fn-track"><div class="fn-fill" style="width:__W4__%">__H4__</div></div><div class="fn-drop">__D4__</div></div>
</div>

<div class="tbl-wrap rv" style="margin-top:26px"><table><thead><tr><th>项</th><th>数字</th><th>这一项的真实情况</th></tr></thead><tbody>
<tr><td>形态</td><td class="num">__H1__ / __N__</td><td>达标这件事，靠的是同一件事：<b>手里有没有一句现成的话</b>。子渝有一份「438 节课」清单，贴过去就自带九个月线上与两年复训（12 组达标里 10 组这么来的）；陈舒有一句模板「三个月线下集训＋九个月线上＋两年内一次免费复训」，同样一句话打包三件（37 组达标）。<b>没有这句话的人，就只说「三个月」——形态的差距不是讲得细不细，是有没有这一句。</b></td></tr>
<tr><td>出口</td><td class="num">__H2__ / __N__</td><td>讲到两条以上的只有 <b>__O2__ 组</b>（子渝 6：长生、R、波波、To、Zz、TK；陈舒 2：星尘、姜彦博；重点组 1：王永正）。另外 <b>__NOO__ 组一条都没讲</b>。最常见的写法是「推荐就业」四个字加一个小程序，客户听完仍然不知道能去哪、能拿多少。</td></tr>
<tr><td>落点</td><td class="num">__H3__ / __N__</td><td>这是最缺的一环，也是最便宜的一环——它不需要新话术，只需要把客户上一条消息里的词拿回来用一次。子渝那组只用了 12 个字，陈舒那组只改了一个数字（退役 → 退伍军人 1000 元）。</td></tr>
<tr><td>一票否决</td><td class="num">__VETO__ 组</td><td>Mo、李雅雯，都在子渝这批。客户喊贵之后，两组都走了同一条路：降价。李雅雯从 23800 降到 20600。陈舒 55 组和重点四组里都没有出现「只降价不解释」这种走法。</td></tr>
</tbody></table></div>

<div class="judge rv"><b>三批放在一张表里的意思　</b>不是比谁强。形态 __PF_A__% 对 __PF_B__%、落点 __PL_A__% 对 __PL_B__%——<b>形态差一倍，落点谁都不及格</b>。这说明一件事：形态是可以被教会的（一句模板就够了），落点没人教，所以每一批都在同一处掉下去。口径见 V3 末尾那张交叉表。</div>

<p class="note rv">口径提醒：形态这一项，客户要的是单考证时按单考证判（四天 / 考什么 / 通过率），不套系统班的三件套。所以沉没潮声、Terry、壹品这三组在形态上不算空白。</p>
</section>

__COMBO__

<section class="sec" id="good">
<div class="sec-head rv"><div class="sec-no">V4 / 做对的</div><h2>十一组把价值传递做成了「客户自己往下走一步」</h2><p class="lead">这十一段不是「讲得好」，是<b>客户听完之后自己动了一下</b>：说了具体数字、问了下一次、定了时间，或者当场改主意。前六组是 @@ST@@ 组三项全过里的六组（子渝 2、陈舒 4——姜彦博就是四组里唯一全过的那一组）。<br><span style="color:var(--ink3)">后面五组各有一条值得抄：出口 3 组、落点 2 组。同一项换一种做法，比只举一个例子更有用——把不同人的做法摆在一起看，才能分出哪些是「个人风格」、哪些是「岗位通用」。<b>三张琥珀底的卡是你点名的组</b>，其余八张是同一批里的对照组。</span></p></div>

<p class="note rv" style="margin-top:-4px">只想看这两块：<a href="口径与范本.html" style="color:var(--navy);text-decoration:none;border-bottom:1px solid rgba(31,58,95,.3)"><b>口径与范本（教材版）</b></a>——只留「怎么判」和「做对的」，两组从头看到尾的聊天记录整段标色，同样逐字可查，适合直接投屏讲案例。</p>

<div class="qwrap">

<div style="display:flex;align-items:center;gap:14px;margin:24px 2px -2px">
<span style="font-size:13px;font-weight:800;letter-spacing:.02em;color:var(--ink)">三项全过　形态 ●●● ｜ 出口 ≥2 条 ｜ 落点 ✓</span>
<i style="flex:1;height:1px;background:var(--line);display:block"></i>
<span style="font-size:11.5px;color:var(--ink3);font-family:var(--mono)">__N__ 组里 @@ST@@ 组</span>
</div>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-1 三项全过</span><h3>把「就业」讲到客户能自己判断值不值：五个单位、辅导面试、上岗跟进</h3><div class="qcard-meta">长生 ｜ 10.10 20:09 → 20:12 ｜ 全程 234 条 ｜ 形态● ● ● ｜ 出口 2 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户看完课程后说「<b>看完了，可以可以</b>」，销售不急着报价，先说「我现在把就业流程给你讲一下」。接下来一条消息说完两种推荐方式：按城市、单位类型、薪资要求推荐<b>五个左右</b>的就业单位，并辅导面试、上岗跟进；另一条路是推荐到集团旗下品牌。结束时客户问的是食堂、是几点起床，并让销售定个时间，说钱会按时打过来。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>出口讲的是可数的东西：五个单位、辅导面试、上岗跟进——客户能自己算这 19300 值不值，而不是被告知一句有就业推荐。</span></li>
<li><i>②</i><span>顺序对：先课程（形态）、再就业（出口），两轮之间客户自己说了「看完了，可以可以」，不是一口气倒完。</span></li>
<li><i>③</i><span>形态也没漏：三件套齐（清单含九个月线上与两年复训），客户知道三个月之后还有什么。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>就业推荐这四个字谁都会说，客户没法验证；五个单位、按你的城市和薪资要求挑、辅导面试、上岗后还跟进——这些都是可以验证的承诺——他能在脑子里过一遍：那我毕业时会发生什么。<b>客户愿意谈钱，通常发生在他知道自己会得到什么之后。</b></p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「就业流程的话，就是在毕业前会安排就业导师一对一保姆级辅导推荐就业」「根据你的需求城市、工作单位类型、薪资要求，给你推荐五个左右的优质就业单位，并且辅导面试」「就业老师就是我们给每个毕业学生提供的就业顾问」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-1 就业流程讲透 ｜ 长生｜10.10 20:09"><img src="assets/value/v1.png" alt="V-1" loading="lazy"></div><div class="qshot-cap">V-1 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-2 三项全过</span><h3>一条消息把产品形态说完，客户不用追问三个月之后怎么办</h3><div class="qcard-meta">波波📣工作版 ｜ 10.28 14:10 ｜ 全程 305 条 ｜ 形态● ● ● ｜ 出口 2 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户连着问价格、还追问两个价分别多少，销售先问了一句分叉（在职教练还是新手爱好者），然后发了一条消息，把产品拆成 <b>3 + 9 + 两年</b>：3 个月线下、9 个月线上、两年内可免费回来复训一次。<b>一条两百多字的消息，没有一句形容词。</b>这组最后走到系统班。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>形态三件一次说清，而且用「3+9+两年复训」这种可记住的结构——客户复述得出来，就说明他听懂了。</span></li>
<li><i>②</i><span>每件都带条件：入学两年之内、免费回来复训 1次、薄弱的板块针对性补学——这是把承诺说到能追责的程度。</span></li>
<li><i>③</i><span>先分叉再报形态：知道对方是在职教练还是新手爱好者，同一段话就有了落点。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>客户问价格时，脑子里真正的问题是：我花这些钱买到的是什么。先给形态再给数字，客户拿到的是一个产品；只给数字，客户拿到的是一个要还的价格。<b>这组客户后来问的已经变成课程能不能延迟、考试排到几号——她在安排自己的时间表了。</b></p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「咱们课程是独创的 3+9+两年复训 模式」「9：毕业赠送 9 个月线上配套视频，结业之后也可以持续线上巩固进阶学习」「两年复训：如果 3 个月学完，觉得身材、专业知识掌握没有达到预期，入学两年之内，可以免费回来复训 1次」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-2 3+9+两年复训 ｜ 波波｜10.28 14:10"><img src="assets/value/v2.png" alt="V-2" loading="lazy"></div><div class="qshot-cap">V-2 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-3 三项全过</span><h3>客户「十年兵刚退役」，她给的是 1000 元身份优惠，不是一句辛苦了</h3><div class="qcard-meta">星尘 ｜ 陈舒 ｜ 10.12 22:49 → 10.13 11:33 ｜ 全程 186 条 ｜ 形态● ● ● ｜ 出口 2 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户第一句就交了底：「<b>十年兵刚退役</b>」，接着问环境、课程安排、食宿与费用。她先把证书讲透（按城市挑、贵的不一定合适），再报三件套，报价后面紧跟一句身份优惠，然后把就业说成一条时间线：第四阶段教包装自己、班主任拍形象照做简历、毕业前用新生模拟体验课、按城市/证书/体型推荐、毕业后第 1、3、6 个月回访。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>落点不是一句共情，是<b>用客户给的话改一个数字</b>：退役 → 退伍军人 1000 元。客户没提钱，她自己把身份变成了减免。</span></li>
<li><i>②</i><span>出口讲成时间线，不是名词：第几个月做什么，客户能在脑子里过一遍自己毕业那年。</span></li>
<li><i>③</i><span>形态没漏，三件齐——客户知道三个月之后还有什么，才敢算这笔钱。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>退伍军人专属优惠这句话本身不值钱，值钱的是<b>它出现在报完价之后</b>：客户刚看到一个两万多的数字，下一条就收到一个只属于他的减项。顺序换过来（先讲优惠再报价），就只是促销；放在后面，是说明这个人的身份被记住了。</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「退伍军人十月有专属 1000 元身份优惠～」「就业咱是推荐就业的形式，根据咱想去的城市、证书、体型去推荐」「第一、三、六个月都会有就业老师定期地去回访」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-3 三件套 + 退伍军人 1000 元 + 就业时间线 ｜ 星尘｜10.12 23:40"><img src="assets/value/cs1.png" alt="V-3" loading="lazy"></div><div class="qshot-cap">V-3 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-4 三项全过</span><h3>客户说「我在健身房上班」，她把证书落到「宁波」这两个字上</h3><div class="qcard-meta">🐈 ｜ 陈舒 ｜ 10.26 16:02 → 17:09 ｜ 全程 46 条 ｜ 形态● ● ● ｜ 出口 1 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户只有一句「<b>我在健身房上班</b>」，她没顺着聊门店，而是把证书和<b>客户所在的城市</b>绑在一起：宁波是新一线，好单位基本都要求国际认证。随后报价 20600，把三件套和价格写进同一句。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>出口不是一句含金量高，是<b>你这个城市要哪一本</b>——客户能自己判断要不要多花那几千块。</span></li>
<li><i>②</i><span>形态和价格一句话说完：「20600，三个月线下集训＋九个月线上进阶课＋两年内一次免费复训的权益」。客户拿到的是一份报价单，不是一个要还的数字。</span></li>
<li><i>③</i><span>客户说那边对她没要求、只求能上手时，她没有顺势降价，而是先讲清这本证在她那个城市意味着什么。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>这是出口最常见也最有效的一种落点：<b>不说证书有多好，说你这个城市要哪一本</b>。它把要不要考国际认证这个判断题，变成了她以后要去的那家店认不认——客户自己能答。</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「宁波那边是新一线诶，好单位基本上都要求国际认证啦」「20600，三个月线下集训＋九个月线上进阶课＋两年内一次免费复训的权益」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-4 证书挂到「宁波」+ 报价句里带全三件套 ｜ 🐈｜10.26 16:14"><img src="assets/value/cs2.png" alt="V-4" loading="lazy"></div><div class="qshot-cap">V-4 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-5 三项全过</span><h3>客户「我最快也得 12 月才辞职」，她推的是 12.9 首班，不是先收定金</h3><div class="qcard-meta">巨巨 ｜ 陈舒 ｜ 10.29 09:55 → 20:05 ｜ 全程 284 条 ｜ 形态● ● ● ｜ 出口 1 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户把时间说得很死：「这份工作可能年底辞职」「<b>我最快也得12月才辞职</b>」，还说了等开班了要她发时间表。她的回应是把班期、优惠、吃住一次算成一张账：成都首班 12.9、优惠 1500，老校区跨年班 1200，宿舍 550 三个月 1650，餐 15×300=4500，合计六千出头。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>客户给了一个<b>未来时间点</b>，她没有把它当成拖延，而是当成排班的输入。</span></li>
<li><i>②</i><span>不劝提前、不催定金——直接给一个对得上的班期（12.9 首班），客户的时间表和她的话对上了。</span></li>
<li><i>③</i><span>把要花多少钱拆成学费 / 优惠 / 宿舍 / 餐费四行，客户能自己加减，不用问第六遍。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p><b>落点最便宜的做法，就是把客户说过的时间原样还给他</b>，再配一个能对上的班期和一个能算清的总数。客户后来说的是等这份工作结束了再看什么时候开班——他已经在用她的班期做计划了。</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「年底优惠力度最大的是成都校区，12.9 号开首班，优惠 1500」「其它校区是老校区嘛，跨年班优惠是 1200」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-5 「最快也得12月才辞职」→ 直接排 12.9 首班 ｜ 巨巨｜10.29 10:07"><img src="assets/value/cs3.png" alt="V-5" loading="lazy"></div><div class="qshot-cap">V-5 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv focus" style="background:#FFFBF0">
<div class="qcard-h"><span class="qcard-no">V-1 三项全过</span><span class="qcard-tag focus">重点</span><h3>客户说「都可以，看就业怎么样」，她把这个标准当场拆成城市、证书、体型</h3><div class="qcard-meta">姜彦博 ｜ 陈舒 ｜ 10.15 09:20 → 10.22 14:01 ｜ 全程 96 条 ｜ 形态 ● ● ● ｜ 出口 3 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户第一天就把底交了：「<b>做教练</b>」，05 年、温州、大学学的是建筑工程、自己练了快一年。10.15 一天里她把证书区别、课程大纲、班期、校区、食宿、就业全过了一遍；10.22 又回头补一句「<b>有了解过教练的薪资结构和淡旺季啵</b>」——这是想重新起话题，可惜客户没接。</p></div>
<div class="qblock"><div class="qlabel">三项分别怎么过的</div><ul class="qacts">
<li><i>①</i><span>形态<b>一句话讲全</b>：「线下系统学习课程是线下三个月集训➕九个月线上课➕两年内一次免费复训的权益」。没拆成三条消息，客户一眼能读完结构。</span></li>
<li><i>②</i><span>出口讲成<b>时间线</b>而不是名词：第四阶段教营销包装与授课转化 → 班主任拍形象照、做简历 → 毕业前用新生扮演会员做体验课、校内查漏补缺 → 按城市/证书/体型推荐 → 「第一、三、六个月都会有就业老师定期地去回访」→ 招生老师每年跟进。</span></li>
<li><i>③</i><span>落点只成立一处，但这一处立得住：客户说「<b>都可以，看就业怎么样</b>」，她答「<b>主要咱推荐就业的时候也是根据咱想去的城市、持有的证书、体型去推荐的</b>」，并且提前把价格差讲出来——「一线超一线这种城市好点的单位都会要求国际认证」「国际认证会贵一些」。<b>没等客户问，先把贵的理由给了。</b></span></li>
</ul></div>
<div class="qblock"><div class="qlabel r">但这一组是及格线，不是范本</div><p>客户说大学学的是「建筑工程」，又说「<b>有啊，实习了半年</b>」——这是转行动机最硬的一条证据。她的回应是「坏了忘了正事，光顾着唠嗑了」，紧接着直接发课程大纲，<b>最值钱的一句被自己掐断了</b>。</p><p>另一处：客户 10:08 问「费用是多少呢」，她 10:09 发的是一条（导出里是不可读的图片类消息），10:10 就转去问「弟弟之前带过人练啵」。到 10.22 结束，<b>报价始终没有以数字形式出现过一次</b>。</p></div>
<div class="qblock qnext"><div class="qlabel">下一步 · 这组该怎么接</div><ol>
<li><b>先接回那两个词，别再开新话题。</b>10.22 那句『了解行业不能只看好的一面』是又起了一个头。换成：『你说建筑实习了半年——是那半年让你想转的吗』，问完再问『你是打算留温州，还是看就业去杭州』。</li>
<li><b>把城市和薪资一起给。</b>他给过的唯一决策标准就是『看就业』，那就直接发温州、杭州两地真实的私教招聘截图（带薪资），配一句『这两个城市你挑一个，我把对应的证书和班期配给你』。</li>
<li><b>报价必须落地成数字。</b>19300 / 21800 / 24800 三档，加一句差价在哪本证上。他已经问过一次价，下次不能再让他问第二次。</li>
</ol></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「线下系统学习课程是线下三个月集训➕九个月线上课➕两年内一次免费复训的权益」「主要咱推荐就业的时候也是根据咱想去的城市、持有的证书、体型去推荐的」「一线超一线这种城市好点的单位都会要求国际认证」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-1 三件套一句话 + 就业时间线 + 落点接住「看就业怎么样」 ｜ 姜彦博｜10.15 09:29"><img src="assets/value/fz1.png" alt="V-1" loading="lazy"></div><div class="qshot-cap">V-1 原文截图，点击放大</div></div></div>
</div></article>

<div style="display:flex;align-items:center;gap:14px;margin:24px 2px -2px">
<span style="font-size:13px;font-weight:800;letter-spacing:.02em;color:var(--ink)">出口　就业路径 / 收入区间 / 证书去向，至少一条讲透</span>
<i style="flex:1;height:1px;background:var(--line);display:block"></i>
<span style="font-size:11.5px;color:var(--ink3);font-family:var(--mono)">讲到两条以上的只有 __O2__ 组，这是三种讲法</span>
</div>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-6 出口 · 就业</span><h3>客户问「邢台有吗」，他没说一句有的，他去查了就业库</h3><div class="qcard-meta">R ｜ 10.23 22:01 → 22:09 ｜ 全程 107 条 ｜ 形态● ○ ○ ｜ 出口 2 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户在河北邢台，问「<b>邢台有吗</b>」。销售没有拿一句有的打发：先说今天放假、电脑在公司，明天登录就业单位平台去查；同时给了一个诚实的判断「<b>你家乡那边肯定是有我们合作的就业单位的</b>」，随后把合作单位的小程序发过去。客户接下来问的，是多久能把学费赚回来——从你那儿有没有，进到我多久能回本。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>不编一个店名，也不含糊过去，而是说清怎么查、什么时候给答复。</span></li>
<li><i>②</i><span>先给判断再给证据：家乡肯定有合作单位（判断）→ 合作单位列表（证据）。</span></li>
<li><i>③</i><span>客户问的是我这个地方有没有，他答的是你那个城市——落点就落在这一个词上。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>客户问邢台有没有，表面问的是网点，实际问的是：我学完回老家，这钱能不能挣回来。把就业资源按客户的城市讲，等于替他把这条路先走了一遍。<b>这组的形态只讲了一件（三个月），但出口这一项拉满，客户照样往下走。</b></p></div>
<div class="qblock qopp"><div class="qlabel r">同一场景，没做到的那一面</div><p>同一个客户在 11.2 的复访：开场那句「兄弟，咱们上次不是给你介绍完了咱们的这个就业流程这些嘛，<b>你最近有没有去训练嘞</b>」是全场最好的开场之一，但三秒钟之后发的是同一份文件、同一个密码。此后 10 天没有回复。（见主报告 PART 02 · P4）</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「具体有没有，我现在不能准确的答复你，但是你家乡那边肯定是有我们合作的就业单位的」「要登录我们公司的就业单位平台，我去给你查去了」「这是我们一些就业合作单位，你可以看一下，兄弟」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-6 邢台有吗 → 查就业库 ｜ R｜10.23 22:01"><img src="assets/value/v3.png" alt="V-6" loading="lazy"></div><div class="qshot-cap">V-6 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-7 出口 · 证书</span><h3>客户问价，他把证书讲成了一件可以准备的事：四天、三项考试、两次补考</h3><div class="qcard-meta">To ｜ 10.29 17:27 → 17:37 ｜ 全程 59 条 ｜ 形态● ○ ○ ｜ 出口 2 条 ｜ 落点 ✗</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户问完费用，销售没有只丢一个数字，而是把单考证这条路整条摊开：先说自己是新国职的官方授权培训基地、校内就能考；再把考试讲成三块——体能、理论、实操，培训就围着这三块转；然后给出客户最想知道、也最容易被跳过的那几个数：<b>四天、两次补考、全国校区一次通过率 90% 以上</b>。最后说清证书的效力与出处。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>报价分开报：系统培训加考证是一个套餐，单考新国职全国统一 3500——客户拿到的是选项，不是一个要还价的数字。</span></li>
<li><i>②</i><span>把好不好过拆成可判断的东西：考什么、培训围着什么、几次补考、通过率多少。</span></li>
<li><i>③</i><span><b>主动说难在哪</b>：「我认为比较难的点，就是体能测试一分钟40个俯卧撑了」——子渝那批 41 组里只有这一组把难点摆出来。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>客户问费用，实际问的是这笔钱买到什么、好不好过。四天、两次补考、90% 通过率都是可以验证的；主动说出俯卧撑这个难点，反而让 90% 这个数字变得可信——<b>敢说难的地方，别的话才不像话术。</b></p></div>
<div class="qblock qopp"><div class="qlabel r">同一组，缺的那一项（所以它只有出口满）</div><p>全程 59 条，没有一句问过客户在哪个城市、想做什么工作、以前练过没有。出口讲得再细也没挂到人身上——客户回了两次考虑一下，第二次之后就没再出现。<b>这就是出口 26 组、落点只有 15 组的原因：讲得清不等于接得上。</b></p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「单考证书线下培训四天，新国职他的考试项目是体能＋理论＋实操考试，咱们培训就围绕这三个考试项目培训，考完后可以有两次补考机会的」「我认为比较难的点，就是体能测试一分钟40个俯卧撑了」「含金量是健身教练上岗必备的证书，目前国内健身行业都认可，由国家体育总局人力资源中心直接颁发」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-7 四天 / 三项考试 / 两次补考 ｜ To｜10.29 17:33"><img src="assets/value/vto.png" alt="V-7" loading="lazy"></div><div class="qshot-cap">V-7 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv focus" style="background:#FFFBF0">
<div class="qcard-h"><span class="qcard-no">V-1 只有出口</span><span class="qcard-tag focus">重点</span><h3>转介绍来的客户只问了「包分配不」，他一口气回了 10 条出口，没问过客户一句情况</h3><div class="qcard-meta">王永正 ｜ 邓杰均 ｜ 10.22 15:08 → 11.10 09:28 ｜ 全程 17 条 ｜ 形态 ○ ○ ○ ｜ 出口 2 条 ｜ 落点 ✗</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>这是黄老师 10.22 转介过来的客户。加上微信两分钟后，客户只发了五个字：「<b>包分配不</b>」。销售在两分钟内回了 10 条——先纠正不是包就业，再讲为什么，然后三张图、一条视频、就业分享会、免费形象照简历、两个就业方向，最后问一句「你看要不要了解一下哈」。<b>客户没有再说话。</b>19 天后（11.10 09:28），他发来的是跨年班优惠和 1200 元交通补贴。</p></div>
<div class="qblock"><div class="qlabel g">出口这一项，他讲得比多数人清楚</div><p>「包分配」是客户最容易被撩起来、也最容易失望的一个词。他没有顺着说「包」，而是把差别讲开了：<b>包 = 随便安排一个单位；推荐 = 按用人标准和双向选择去配</b>。这一段是本组唯一值得抄的东西。</p></div>
<div class="qblock"><div class="qlabel r">卡在哪</div><ul class="qacts">
<li><i>①</i><span><b>形态 0</b>：三个月、九个月、复训，一个字都没出现。客户问「包分配」，问的是这两万块花下去有没有着落、到底学些什么——他只答了前半句，后半句没碰。</span></li>
<li><i>②</i><span><b>落点 0</b>：整组 17 条，没有一句问过客户自己的情况。年龄、城市、现在做什么、为什么想转，全空。唯一的信息是备注里那行转介10.22。</span></li>
<li><i>③</i><span><b>顺序反了</b>：客户第一句问确定性，他第一句答「不是包就业」。诚实是对的，但先把客户最想要的那个词否掉，后面十条都在往回补。</span></li>
</ul></div>
<div class="qblock qnext"><div class="qlabel">下一步 · 这组该怎么接</div><ol>
<li><b>不要再发优惠。</b>11.10 那条群发是这组第二次『只发不问』。转介绍客户身上最值钱的是黄老师给的信任，不是 1200。</li>
<li><b>第一句先问人。</b>『黄老师跟我提过你——你现在在哪个城市、做什么工作？』一句话就能换回整组的落点。</li>
<li><b>把「包分配」正面接一次。</b>他要的是确定性，那就答确定性到什么程度：『给你挑 5 个单位、辅导面试、上岗后跟进』，比解释『为什么不是包』有用得多。</li>
<li><b>补形态，一句话就够。</b>三个月线下集训 + 九个月线上 + 两年内免费复训一次——他到今天还不知道这三件。</li>
</ol></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「体德是叫免费推荐就业哈」「但不是包就业，因为包就意味着随便给你安排一个就业单位」「就业呢，它是一个双向选择的，就业单位也有用自己的用人标准」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-1 客户五个字「包分配不」→ 10 条出口 ｜ 王永正｜10.22 17:15"><img src="assets/value/fz2.png" alt="V-1" loading="lazy"></div><div class="qshot-cap">V-1 原文截图，点击放大</div></div></div>
</div></article>

<div style="display:flex;align-items:center;gap:14px;margin:24px 2px -2px">
<span style="font-size:13px;font-weight:800;letter-spacing:.02em;color:var(--ink)">落点　客户下一句变具体，或直接做出动作</span>
<i style="flex:1;height:1px;background:var(--line);display:block"></i>
<span style="font-size:11.5px;color:var(--ink3);font-family:var(--mono)">__N__ 组里 __H3__ 组成立，这里两种落法</span>
</div>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-8 落点 · 换成数字</span><h3>客户说「我主要想减肥」，他答的是「减重 20 公斤」</h3><div class="qcard-meta">（杜康）问剑白玉京 ｜ 10.27 17:27 → 10.30 10:06 ｜ 全程 77 条 ｜ 形态● ● ○ ｜ 出口 1 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户把顺序讲得很清楚：「<b>我主要想减肥，健身考证那是锦上添花的事</b>」。三天后他说「我现在体重 220 想减到 170」，销售确认「只想过来减重是吧」，然后给的不是课程目录，是一句可核对的结果：「<b>你先确定好，你过来线下集训 3 个月，减重 20 公斤都是不在话下的</b>」，紧接着补上入学门槛（体脂不超过 30、BMI 不超过 30）。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>把客户的目标换成了数字：220 → 170 是 50 斤，他说的是「20 公斤」，客户可以自己对账。</span></li>
<li><i>②</i><span>给结果的同时给条件：「你要确定只是过来减重的哦，我需要特殊申请」——没有为了成单把话说满。</span></li>
<li><i>③</i><span>补上入学门槛，把能不能减下来，换成你符不符合条件，这是可以当场核实的。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>客户说想减肥，最怕听到一句我们课程也能减脂这样的顺水话。给一个具体公斤数，等于把承诺摆在桌上：达不到，你可以拿这句来找我。<b>落点之所以有效，不是因为说到了客户，是因为说得比客户自己还具体。</b></p></div>
<div class="qblock qopp"><div class="qlabel r">同一组，没做到的那一面（所以它不算「三项全过」）</div><p>客户第一句问的是「三个月培训怎么收费的，考证另外我再考虑」，销售 17:28 直接回「<b>那就报这个 19300 的课程</b>」——3500 的单考证档整组一次都没报出来。落点满分，但形态少一件、价位跳了一档。</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「你先确定好，你过来线下集训3个月，减重20公斤都是不在话下的」「但是你要确定只是过来减重的哦，我需要特殊申请」「我们入学有要求的体脂率不超过30 ，BMI不超过30」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-8 减脂客户 → 减重20公斤 ｜ 杜康｜10.30 10:06"><img src="assets/value/v4.png" alt="V-8" loading="lazy"></div><div class="qshot-cap">V-8 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv focus" style="background:#FFFBF0">
<div class="qcard-h"><span class="qcard-no">V-1 只有落点</span><span class="qcard-tag focus">重点</span><h3>客户连问三次「学完以后呢」，他回的是「我们会推荐就业的」</h3><div class="qcard-meta">李小东（UIN） ｜ 体德智训-小威 ｜ 10.02 19:25 → 10.29 15:22 ｜ 全程 53 条 ｜ 形态 ● ● ○ ｜ 出口 0 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户开场三句就把重点摆出来了：「费用多少呀」「考证做教练」「<b>学完以后呢</b>」。报价给得很干净——「咱们整体的学费是在一万九到两万六哈」「是根据选择的证书挂钩」「三个月培训加考证」。但「学完以后呢」在 19:43 和 19:45 问了两次，19:45 又追「<b>没就业上呢</b>」，拿到的是「我们会推荐就业的」和「可以免费复训的」。之后话题转到他自己的条件上，这一转，救回了这组的落点。</p></div>
<div class="qblock"><div class="qlabel g">做对了什么（落点两处，都很硬）</div><ul class="qacts">
<li><i>①</i><span>客户「我特别瘦」「178 110斤」→ 他先确认「<b>你这个身型确实太瘦了</b>」，再把三个月说成一件可执行的事：「三个月的话要看你的努力」「跟着老师安排的训练和饮食计划」；11 天后补发学员身形变化图。客户给的是自卑，他还的是一条路径。</span></li>
<li><i>②</i><span>客户「<b>我在惠州</b>」→「那离我们广州校区比较近」，紧接着把食宿讲成钱：「广州这边是850元/月和750/月」，2-4 人和 5-6 人间、包水电、食堂一餐 9~15、一日三餐打卡。<b>落点最便宜的做法，就是把客户说的地名变成一张价目表。</b></span></li>
</ul></div>
<div class="qblock"><div class="qlabel r">卡在哪</div><ul class="qacts">
<li><i>①</i><span><b>出口 0</b>：「学完以后呢」是他唯一还没拿到的决策依据，得到五个字。没有城市、没有单位、没有薪资、没有证书能干什么。</span></li>
<li><i>②</i><span><b>形态 2</b>：只说了「三个月培训加考证」，九个月线上一次没提；「可以免费复训的」是被「没就业上呢」逼出来的一句兜底，不是当权益主动讲的。</span></li>
<li><i>③</i><span><b>最贵的一句被浪费</b>：客户问「24还建议进入健身行业吗」，他答「24岁」「还这么年轻」「兄弟你担心什么」。他真正怕的是年龄，不是身材——而这一句本可以正面答掉。</span></li>
</ul></div>
<div class="qblock qnext"><div class="qlabel">下一步 · 这组该怎么接</div><ol>
<li><b>别发课程。</b>10.29 之后他没回。手上已有五条事实：惠州、178/110、零基础、24 岁、怕学完没着落。再发课程等于告诉他『你没在听』。</li>
<li><b>发三样带数字的东西。</b>广州和深圳两地真实私教招聘截图（带薪资区间）；一个条件接近的学员入行时间线（几个月入行、第一份工作在哪、现在多少）；一条『学完没找到工作怎么办』的具体流程（复训怎么用、就业老师跟多久）。</li>
<li><b>把「24 岁」正面答一次。</b>这个年龄入行意味着什么、30 岁以后靠什么涨价——他问过一次没人答，就不会再问第二次。</li>
<li><b>形态补最后一件。</b>九个月线上课至今没提，补一句就够。</li>
</ol></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「咱们整体的学费是在一万九到两万六哈」「你这个身型确实太瘦了」「跟着老师安排的训练和饮食计划」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-1「学完以后呢」问了三次 → 五个字 ｜ 李小东（UIN）｜10.02 19:45"><img src="assets/value/fz3.png" alt="V-1" loading="lazy"></div><div class="qshot-cap">V-1 原文截图，点击放大</div></div></div>
</div></article>

</div>

<div class="judge rv"><b>这十一组的共同点　</b>不是讲得更多，而是<b>讲得能核对</b>：五个单位、一条 3+9+两年的结构、一个城市、一个公斤数、四天和两次补考、一个只属于这个客户的身份、一个他说过的时间点。客户能拿走的都是可核对的东西，没有一句「很专业」「含金量高」。</div>
</section>

<section class="sec" id="bad">
<div class="sec-head rv"><div class="sec-no">V5 / 做错的</div><h2>八种错法，对应八种不同的代价</h2><p class="lead">前四种在《判断标准.md》§1.4 里都有定义；后四种是合并之后才看清的。其中最后一种是这批数据里最反直觉的一条——<b>产品讲得最完整的那一组，客户流失得最彻底</b>。每一类配一组原文。<b>差别不在「讲得少」，在于客户被推向哪个方向</b>——是被推去比价、被推去别的机构，还是被推去「等我有时间再说」。</p></div>

<div class="tbl-wrap rv"><table><thead><tr><th>类型</th><th>特征</th><th>这组怎么做的</th><th>代价</th></tr></thead><tbody>
<tr><td><b>资料包式</b></td><td>客户问一句，回清单 / 图片 / 小程序</td><td>于源：问「价格方面呢」，收到 438 节课清单 + 19300</td><td>此后客户 0 条</td></tr>
<tr><td><b>反落点</b></td><td>客户说了要什么，销售说他不要这个</td><td>睡到自然醒：要宿舍食堂健身房，回「我们是专业的健身教练培训」</td><td>9 分钟结束，客户说「那打扰了」</td></tr>
<tr><td><b>优惠替代</b></td><td>客户喊贵，只改价不解释贵在哪</td><td>李雅雯：喊贵一次，价格 23800 → 20600</td><td>降到客户不再回价，也没有回「值」</td></tr>
<tr><td><b>答非所问</b></td><td>客户问 A，回的是 B</td><td>Mo：问「1 个月有没有」，答「3 个月怎么学」；问贵，答再优惠 1000</td><td>到校参观后仍以「时间太长」退出</td></tr>
<tr><td><b>问出口、答民俗</b></td><td>客户替你把问题问出来，你答了句话，没答内容</td><td>千秋：客户说「都说好就业」，回「老辈子说嘛」</td><td>客户把需求降级成「寒假塑型一下」</td></tr>
<tr><td><b>形态缺件</b></td><td>客户要的都给了，产品只讲了三分之一</td><td>如意吉祥：位置、环境、证书都讲了，「三个月四个阶段」之外没提九个月与复训</td><td>已经走到校区门口，最后没进去</td></tr>
<tr><td><b>只答条件、不讲产品</b></td><td>每一问都答了，拼起来是一张价目表</td><td>小马：六连问全答，学什么、学多久、学完怎样一字未讲</td><td>客户改用「什么时候方便」来决定</td></tr>
<tr><td><b>产品讲满分</b></td><td>形态讲得比谁都全，出口、落点全空</td><td>銀河：3+9+两年逐项讲透，之后三次触达都是发资料、发优惠</td><td>51 天里客户只说了 5 句</td></tr>
</tbody></table></div>

<div class="qwrap">

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-9 落点 · 复述原话</span><h3>客户自己说了两件事，他把这两件事编号复述回去</h3><div class="qcard-meta">ZMBT ｜ 10.7 20:30 → 20:33 ｜ 全程 242 条 ｜ 形态● ○ ○ ｜ 出口 1 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户在两分钟里自己说了两件事：「<b>想到时候去考个健身房教练证这种</b>」「<b>然后另外的话，想去提升个人能力</b>」。三分钟后他问「大概是包括什么的？」。销售没有发课程目录，而是引用这句，回的是「<b>结合你刚刚说的这两点</b>：第一点是想提升自己健身水平。第2点是想要考这个认证，这两点在我们校区的课程内都是包含的。我们的优势就是这两点」。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>客户的两句话被编号复述——客户一眼看到自己被听懂了，这比任何开场白都快。</span></li>
<li><i>②</i><span>每一点都对到课程里到底有什么，不是一句我们都有。</span></li>
<li><i>③</i><span>顺序对：先复述需求，再展开内容。反过来就是先念目录、再说你刚才问的都有。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>客户问「包括什么」的时候，最容易被塞一份课程目录。销售给的是<b>你要的两件事、在我们这儿对应哪两块</b>——客户听到的是自己的需求清单，不是产品清单。<b>落点最便宜的地方就在这里：不用新话术，把客户刚说过的词拿回来用一次。</b></p></div>
<div class="qblock qopp"><div class="qlabel r">同一组，缺的那两项</div><p>形态只讲了 3 个月，9 个月线上与两年复训整组没提（后面出现的「线上」是报名后开通的预习课，不是毕业赠送的 9 个月配套）；出口只讲了证书。7 天后这组停在「我再看看」——<b>落点解决「听不听得懂」，不解决「值不值」。</b></p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「兄弟，结合你刚刚说的这两点：第一点是想提升自己健身水平。第2点是想要考这个认证，这两点在我们校区的课程内都是包含的。我们的优势就是这两点」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-9 结合你刚刚说的这两点 ｜ ZMBT｜10.7 20:33"><img src="assets/value/vzmbt.png" alt="V-9" loading="lazy"></div><div class="qshot-cap">V-9 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-10 落点 · 翻译方案</span><h3>客户拿着 AI 给的「方案 B」来问，他当场翻译成自己的产品</h3><div class="qcard-meta">七顿 ｜ 11.2 19:05 → 19:08 ｜ 全程 293 条 ｜ 形态● ○ ○ ｜ 出口 1 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户发了一张豆包截图，说「<b>我在豆包稍微了解了一下，大概就是方案B那种</b>」。销售没有反问方案 B 是什么，直接翻译成自家产品：「<b>那就是想要3个月系统学习，然后再学一个NASM国际认证，这样子呗</b>」，客户回「对的」。紧接着他把讲解顺序先报出来：「我就从证书开始给你讲，然后再讲到我们的课程体系，再讲一下我们的宿舍和食堂」。最后确认套餐边界：包含 3 个月基础培训、NASM 认证、住宿、吃饭。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span>客户拿别人的话说需求，他不否定、不照抄，翻译成自家产品名——客户立刻确认「对的」。</span></li>
<li><i>②</i><span>先报讲解顺序（证书 → 课程体系 → 宿舍食堂），客户知道接下来会听到什么，愿意等。</span></li>
<li><i>③</i><span>把套餐边界说清，含住宿和吃饭——这正是客户拿 AI 比价时真正在比的东西。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>客户已经用 AI 做过功课，他走进来最想确认的一句是：你家的方案 B 是不是我以为的那个。销售用一句复述把这个确认做完了，后面讲什么他都听。<b>反过来，先问一句方案 B 是什么呀，等于让客户把功课再做一遍。</b></p></div>
<div class="qblock qopp"><div class="qlabel r">同一组，缺的那两项</div><p>形态只有 3 个月 + NASM，9 个月线上和两年复训整组没提；出口只讲了证书。这组最后停在「我再考虑一下」——需求接住了，钱的价值没接住。</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「可以呀，兄弟，那就是想要3个月系统学习，然后再学一个NASM国际认证，这样子呗」「我就从证书开始给你讲，然后再讲到我们的课程体系，再讲一下我们的宿舍和食堂」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-10 豆包方案B → 3个月+NASM ｜ 七顿｜11.2 19:06"><img src="assets/value/vqd.png" alt="V-10" loading="lazy"></div><div class="qshot-cap">V-10 原文截图，点击放大</div></div></div>
</div></article>

<div style="display:flex;align-items:center;gap:14px;margin:24px 2px -2px">
<span style="font-size:13px;font-weight:800;letter-spacing:.02em;color:var(--ink)">按需拆　不讲全，只讲客户真要的那一块</span>
<i style="flex:1;height:1px;background:var(--line);display:block"></i>
<span style="font-size:11.5px;color:var(--ink3);font-family:var(--mono)">形态满分的 12 组里 10 组靠贴清单</span>
</div>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-11 按需拆</span><h3>客户不做教练，他先把考证套餐砍了，再报价格</h3><div class="qcard-meta">EAST WER-🍂 ｜ 11.3 13:22 → 13:24 ｜ 全程 138 条 ｜ 形态● ○ ○ ｜ 出口 1 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户已经自己做过功课：「<b>我要是去的话大概就是在年后3月左右 价格我也看了我大概记得是19800还有其它的什么之类的</b>」。销售没有顺着 19800 报套餐，先把用途问清，然后直接替他减配：「<b>兄弟你不做教练的话可以不用选择考证书的套餐，就学3个月系统培训课程就行了</b>」。紧接一条把减配后的价格和替代收益补上：「价格是19300元不考健身教练认证，毕业会有6个学院证书和一个急救证」。</p></div>
<div class="qblock"><div class="qlabel">做对了什么</div><ul class="qacts">
<li><i>①</i><span><b>主动砍客户不需要的部分</b>：不做教练，就别买考证套餐。子渝那批 41 组里敢这么说的只有这一组。</span></li>
<li><i>②</i><span>砍完给替代收益：6 个学院证书 + 急救证，不是简单砍掉一块。</span></li>
<li><i>③</i><span>砍完立刻给新价格（19300），客户不用再问一次。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">为什么有效</div><p>客户怕的是被推销不需要的东西。销售先替他砍，后面那个 19300 才不像话术。<b>这跟资料包式（前面于源那一组）正好相反</b>——那一组把 438 节课整套推给只想健身的人，这一组把客户不要的先拿掉。客户当天就把时间定在年后 3 月。</p></div>
<div class="qblock qopp"><div class="qlabel r">同一组，缺的那两项</div><p>形态只讲了 3 个月的四个阶段，9 个月线上与两年复训没提；出口只讲了证书。按需拆解决「别卖我不要的」，不解决「这套东西值多少」。</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「兄弟你不做教练的话可以不用选择考证书的套餐，就学3个月系统培训课程就行了」「价格是19300元不考健身教练认证，毕业会有6个学院证书和一个急救证」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-11 不做教练就不用买考证套餐 ｜ EAST WER-🍂｜11.3 13:23"><img src="assets/value/veast.png" alt="V-11" loading="lazy"></div><div class="qshot-cap">V-11 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-12 资料包式</span><h3>客户说「单纯健身」，收到的是一份 438 节课的采购清单</h3><div class="qcard-meta">于源 ｜ 10.16 09:55 → 10:25 ｜ 全程 22 条 ｜ 形态● ● ● ｜ 出口 0 条 ｜ 落点 ✗</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户第一句是「<b>单纯健身</b>」，销售确认「只过来提升健身水平嘛」，他答「对」。10:05 的回应是「那你可以了解一下我们线下 3 个月的系统培训」。客户 10:20 只问了「价格方面呢」，10:25 收到的是一条清单——三个月 438 节课、考证报名费、九个月线上、两年复训、保姆式就业推荐——末了一句「<b>价格在定金优惠完后是 19300 元</b>」。<b>此后这一组客户 0 条消息。</b></p></div>
<div class="qblock"><div class="qlabel">错在哪</div><ul class="qacts">
<li><i>①</i><span>形态其实讲全了（清单里三件都有），但讲给了一个要「单纯健身」的人——他不需要考证、不需要就业推荐。</span></li>
<li><i>②</i><span>出口 0 条：清单里「保姆式就业推荐」六个字，客户既不知道推荐到哪，也不知道能拿多少。</span></li>
<li><i>③</i><span>落点 ✗：客户「单纯健身」四个字，整组里没有被拿回来用过一次。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">代价是什么</div><p>不是客户觉得贵，是<b>客户不知道这份清单里哪一行是自己的</b>。438 节课、九个月线上、两年复训、就业推荐——四个卖点，一个也对不上「单纯健身」。所以他能问的只剩价格，而价格一出来就没有第二句话了。</p></div>
<div class="qblock qopp"><div class="qlabel r">同一场景，做对了的样子</div><p>EAST WER-🍂 也是想练身材，销售在 11.3 13:23 直接替他拆开：<b>不做教练的话可以不用选考证书的套餐，只学 3 个月系统培训就行</b>。客户当天自己定下了年后 3 月，还主动说定金近期会交。（同一逻辑见 V-6）</p></div>
<div class="qblock qreuse"><div class="qlabel g">该说而没说的那句</div><p>你要是不考证、也不做教练，就学 3 个月的系统培训就够了；19300 里那 6 个学院证书是过程认证，不是上岗证。——同一份清单，先替他划掉不需要的部分。</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-12 单纯健身 → 438 清单 ｜ 于源｜10.16 10:25"><img src="assets/prob/P1c.png" alt="V-12" loading="lazy"></div><div class="qshot-cap">V-12 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-13 反落点</span><h3>客户要「宿舍食堂健身房」，他回「我们是专业的健身教练培训」</h3><div class="qcard-meta">睡到自然醒 ｜ 11.2 21:08 → 21:19 ｜ 全程 38 条 ｜ 形态● ○ ○ ｜ 出口 1 条 ｜ 落点 ✗</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户把需求说了三遍：「<b>我不需要考证 也不需要教练 只想要这么一个环境 有这种套餐吗</b>」「<b>就是只要宿舍 食堂和健身房 我自己会练</b>」「或者需要计划表就行」，还补了一句「我练了三四年了 只是管不住嘴」。他收到的是「<b>兄弟，你说的这个是减脂营啊。我们是专业的健身教练培训呀</b>」，然后是「套餐太贵了」→「<b>我们的课程就是这样子的，兄弟，没法拆开来</b>」。两句之后客户说「我不需要」「行吧 那打扰了」，<b>从开口到结束 9 分钟</b>。</p></div>
<div class="qblock"><div class="qlabel">错在哪</div><ul class="qacts">
<li><i>①</i><span>落点不是没挂上，是<b>挂反了</b>：客户说要什么，销售说你要的不是这个。</span></li>
<li><i>②</i><span>那句「我自己会练」被完全跳过——它其实是最好接的落点：有基础、要环境、缺监督。</span></li>
<li><i>③</i><span>「没法拆开来」是这组最贵的一句：它把产品不能改，摆在了客户要什么之前。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">代价是什么</div><p>9 分钟。而且这不是价格问题——客户说的「套餐太贵了」，指的是<b>他不需要的那个套餐</b>。他真正想买的东西，这家机构其实有（宿舍、食堂、健身房都在校区里），只是没有人告诉他可以怎么用。</p></div>
<div class="qblock qopp"><div class="qlabel r">同一场景，做对了的样子</div><p>杜康 10.30 那一句：「<b>但是你要确定只是过来减重的哦，我需要特殊申请</b>」——同样是产品不能直接拆，但他先把客户要的那件事接住，再谈条件。（见 V-8）</p></div>
<div class="qblock qreuse"><div class="qlabel g">该说而没说的那句</div><p>你要的住、吃、练我们都有，但它只能挂在三个月的培训里卖，我帮你算一下这三个月你到底能拿到什么。——不承诺改产品，但先承认他要的东西在这儿。</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-13 只要环境 → 我们是教练培训 ｜ 睡到自然醒｜11.2 21:12"><img src="assets/prob/P1.png" alt="V-13" loading="lazy"></div><div class="qshot-cap">V-13 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv neg">
<div class="qcard-h"><span class="qcard-no">V-14 出口被一句话挡回去</span><h3>客户替你把出口问出来了，她回的是三个字的民俗</h3><div class="qcard-meta">千秋 ｜ 陈舒 ｜ 10.11 20:37 → 21:48 ｜ 全程 147 条 ｜ <b>形态 ● ● ●</b> ｜ <b>出口 0 条</b> ｜ 落点 ✗</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户是护理专业的学生、174/155、一开口就说想减脂，也说了自己可能没那么多时间。聊到专业时她主动递了一句：「<b>都说好就业</b>」——这是客户替销售把出口的问题问出来了。销售回的是「<b>老辈子说嘛</b>」，然后继续讲减脂塑形怎么安排。这一组三件套是全的，最后一小时客户说最近没时间，又说就想寒假塑型一下。</p></div>
<div class="qblock"><div class="qlabel">错在哪</div><ul class="qacts">
<li><i>①</i><span>客户已经把「出口」这个词递到手里，回了三个字的民俗——她答的是<b>这个说法从哪来</b>，不是<b>这个说法对不对</b>。</span></li>
<li><i>②</i><span>三件套讲全了，反而更可惜：客户知道产品是什么，就是不知道学完能怎样，于是整组只剩一个判断依据——价格。</span></li>
<li><i>③</i><span>客户说的是「都说」，等于把真假也一起问了。这里只要回一句哪几家、什么岗位、多少钱，就能接住。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">代价是什么</div><p>这一组最后停在一次寒假塑型上——客户自己把需求降级成了短期塑形。不是她不想学，是<b>没有人帮她把学完能干什么这件事说清楚</b>，她只能按最保守的方式安排自己。</p></div>
<div class="qblock qopp"><div class="qlabel r">同一场景，做对了的样子</div><p>星尘那组客户也提了「就业指导」，销售用一条消息讲完：第四阶段教什么、班主任帮拍形象照做简历、毕业前用新生模拟体验课、按城市/证书/体型推荐、毕业后第 1、3、6 个月回访。（见 V-3）</p></div>
<div class="qblock qreuse"><div class="qlabel g">该说而没说的那句</div><p>是挺好就业，但分两种：一种是健身房要你，一种是好单位要你。你现在护理专业、体能不差，走第二条更划算——我跟你讲讲这两种差在哪。</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-14 「都说好就业」→「老辈子说嘛」 ｜ 千秋｜10.11 21:39"><img src="assets/value/cs4.png" alt="V-14" loading="lazy"></div><div class="qshot-cap">V-14 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv neg">
<div class="qcard-h"><span class="qcard-no">V-15 形态少两件</span><h3>客户要位置、环境、饮食、收费，位置给了、八个证书讲了，九个月和复训没提</h3><div class="qcard-meta">如意吉祥 ｜ 陈舒 ｜ 10.11 13:46 → 10.19 09:35 ｜ 全程 52 条 ｜ <b>形态 ● ○ ○</b> ｜ 出口 1 条 ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户一口气点了四项：「<b>南京的位置发给我</b>」「包括学校环境，饮食，课程收费」，还补了一句「我没事儿过去看看」。她按客户要的发了位置和资料，证书也讲透了（八个证、按城市挑），但课程形态只说了「<b>三个月分成了四个阶段</b>」——九个月线上、两年复训这两件没有出现。</p></div>
<div class="qblock"><div class="qlabel">错在哪</div><ul class="qacts">
<li><i>①</i><span>客户的四项要求全部被满足，所以没人会觉得这里缺东西——<b>这正是形态最容易漏的原因：它不在客户的问题里。</b></span></li>
<li><i>②</i><span>出口成立（八个证书讲到能判断），落点也成立（按南京发位置），只差把产品讲全一件。</span></li>
<li><i>③</i><span>客户到校区看到的是三个月、四个阶段，四个月后他会以为课上完了。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">代价是什么</div><p>客户 10.11 说「我没事儿过去看看」，10.19 销售问她最近有没有时间参观，没有回应。<b>一个已经走到门口的人，最后没进去</b>——不是因为价格，是因为他手里那张产品清单只有三分之一。</p></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「咱们是理论跟实操并线推进滴」「三个月分成了四个阶段」「一共能拿八个证书，6个体德官方认证➕一个cpr证书（让教练证书生效）➕咱选择的教练证」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-15 客户要四项 → 只讲了「三个月四个阶段」 ｜ 如意吉祥｜10.11 13:50"><img src="assets/value/cs5.png" alt="V-15" loading="lazy"></div><div class="qshot-cap">V-15 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv neg">
<div class="qcard-h"><span class="qcard-no">V-16 答得全，不等于讲得对</span><h3>客户六连问，价格、就业、吃住都答了，产品是什么一个字没讲</h3><div class="qcard-meta">小马 ｜ 陈舒 ｜ 10.14 17:16 → 17:44 ｜ 全程 74 条 ｜ <b>形态 ○ ○ ○</b> ｜ 出口 1 条 ｜ 落点 ✗</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户在 20 分钟里连问六件：培训费多少、每个证多少钱、能不能推荐就业、有哪些校区、吃住咋算、什么时候开班。她一件一件答了，甚至把「大概能挣多少钱一个月」答成「<b>咱心理预期最好是放在3-6000，一上来马上过万还是相对比较少的</b>」——很实在。<b>但学什么、学多久、学完还有什么，一个字没有。</b></p></div>
<div class="qblock"><div class="qlabel">错在哪</div><ul class="qacts">
<li><i>①</i><span>六个问题都答了，所以这组看起来服务很好；但六个答案拼起来是一张<b>价目表</b>，不是一件产品。</span></li>
<li><i>②</i><span>客户真正要做的决定是花两万多买三个月值不值，而回答这个问题需要形态和出口——这两样恰好都没出现。</span></li>
<li><i>③</i><span>唯一一句实在话（3-6000）反而暴露了缺口：讲了收入，没讲怎么拿到这个收入。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">代价是什么</div><p>客户最后问的是开班时间，说自己想着明年去、今年不一定有时间——<b>他在给自己找时间上的理由</b>。价格答得越清楚、产品讲得越少，客户越只能用什么时候方便来决定要不要买。</p></div>
<div class="qblock qreuse"><div class="qlabel g">该说而没说的那句</div><p>费用我先给你放一放：两万多买的是三个月线下＋九个月线上＋两年内一次复训，这段时间里你会被练成能带课的人。你先听我讲完这个，再判断这两万多贵不贵。</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-16 六连问 → 六条信息，产品一字未讲 ｜ 小马｜10.14 17:17"><img src="assets/value/cs6.png" alt="V-16" loading="lazy"></div><div class="qshot-cap">V-16 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv neg focus" style="background:#FFFBF0">
<div class="qcard-h"><span class="qcard-no">V-1 产品讲满分</span><span class="qcard-tag focus">重点</span><h3>形态讲到全批最标准的一段，出口零、落点零，客户 51 天只说了 5 句</h3><div class="qcard-meta">銀河 ｜ 路梦丽 ｜ 09.19 08:41 → 11.09 17:09 ｜ 全程 23 条 ｜ 形态 ● ● ● ｜ 出口 0 条 ｜ 落点 ✗</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户第一句就是「<b>介绍一下价格吧</b>」。她发了价格表，加一段形态——先说「体德的职业培训课程是全国首创的3+9与两年的模式」，再把 3、9、两年逐项翻译成人话，最后给了使用条件：「假如说三个月觉得自己身材专业等方面没达到预期，可以在毕业两年内免费回来重新学习一次」。然后问「咱们是考虑提升自己还是有做教练的打算哈」，客户回「我就先咨询一下」「谢谢了」。</p></div>
<div class="qblock"><div class="qlabel g">做对了什么：这一段形态可以直接拿去当模板</div><p>它没停在名词上。3 = 三个月线下、分四个阶段、理论加实操；9 = 「毕业赠送9个月线上视频，毕业后也能持续进阶学习」；两年 = 一个<b>后悔权</b>，不是赠品。一句话讲完结构，一句话讲完条件，客户不用追问就能自己算出：三个月之后，还有九个月。</p></div>
<div class="qblock"><div class="qlabel r">卡在哪</div><ul class="qacts">
<li><i>①</i><span><b>出口 0</b>：就业、薪资、证书能干什么，一个字没有。价格表发了，但这两万块买完能换回什么，始终没出现。</span></li>
<li><i>②</i><span><b>落点 0</b>：「我就先咨询一下」是客户在说别急着推。她回「没事的，先了解一下嘛」「来不来学都没关系，做个了解可以对比对比哈」——这是<b>软化</b>，不是挂靠：客户是谁、想解决什么，一句没问。</span></li>
<li><i>③</i><span><b>三次触达都是发东西</b>：9.22 发《不同胚型，如何高效减脂增肌》电子书，11.9 发「提前12天订金锁班可以减现1200哦」，客户都没回。51 天里客户一共说了 5 句。</span></li>
</ul></div>
<div class="qblock qnext"><div class="qlabel">下一步 · 这组该怎么接</div><ol>
<li><b>第三次再发资料，就等于确认『这家只想卖我东西』。</b>换成一句提问：『你问完价就没往下问，是觉得贵，还是不确定学完能干嘛？』——这一问同时补出口和落点，而且它承认了客户的停顿。</li>
<li><b>如果他不回，隔一周发一份不带课程的东西。</b>他所在城市的私教岗前三个月真实收入区间 + 招聘要求，一页纸，附一句『你看完再决定要不要了解课程』。</li>
<li><b>别再发优惠。</b>他一句价都没还过，说明卡的不是钱，是值不值。</li>
<li><b>形态已经是满分，别再改了。</b>这组唯一要加的是『学完能去哪』，不是『学什么』。</li>
</ol></div>
<div class="qblock qreuse"><div class="qlabel g">可以直接抄的原话</div><p>「体德的职业培训课程是全国首创的3+9与两年的模式」「毕业赠送9个月线上视频，毕业后也能持续进阶学习」「假如说三个月觉得自己身材专业等方面没达到预期，可以在毕业两年内免费回来重新学习一次」</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-1 形态讲到最标准的一段，出口与落点全空 ｜ 銀河｜09.19 08:43"><img src="assets/value/fz4.png" alt="V-1" loading="lazy"></div><div class="qshot-cap">V-1 原文截图，点击放大</div></div></div>
</div></article>

</div>
</section>

<section class="sec" id="veto">
<div class="sec-head rv"><div class="sec-no">V6 / 一票否决</div><h2>两组：客户喊贵之后，只剩降价这一条路</h2><p class="lead">《判断标准.md》§1.3 的口径：客户说贵、销售只改价不解释贵在哪 → 直接判差，不看形态讲得多全。__N__ 组里 __VETO__ 组成立，都在子渝这批；陈舒 55 组和重点四组里都没有出现「只降价不解释」。</p></div>

<div class="qwrap">

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-17 否决</span><h3>「这么贵的吗」→ 他把话题转去了校区地址，然后降了 3200</h3><div class="qcard-meta">李雅雯 ｜ 11.4 09:51 → 11.6 16:57 ｜ 全程 90 条 ｜ 优惠词 12 次 ｜ 讲就业 0 次</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户第一句就是问普通的证书学习要多少钱，09:51 收到两档价格（19300 / 21800），外加一句双 11 还能再优惠一千。客户 09:52 回：「<b>这么贵的吗？我记得我之前去白云区看过，没有这么贵啊</b>」。销售的回答是「<b>咱们白云区没有校区的呀，你看的是哪家机构呢</b>」——把话题转去了地址。两天后价格落到 20600：<b>从 23800 一路降了 3200</b>，客户最后一句是「收到，谢谢」。</p></div>
<div class="qblock"><div class="qlabel">错在哪</div><ul class="qacts">
<li><i>①</i><span>客户问的是凭什么这个价，答的是你记错了校区——问题被移走了，不是被回答了。</span></li>
<li><i>②</i><span>接着用降价回答：1200 学费优惠 + 1000 介绍优惠 + 800 推荐费，价格自己往下走。</span></li>
<li><i>③</i><span>整组 90 条里，<b>就业、收入、学完能干什么，一次都没讲</b>——所以除了价格，没有别的东西可以谈。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">代价是什么</div><p>客户没有说不买了，她说的是「收到，谢谢」。<b>降价买到的是沉默，不是成交。</b>更贵的一笔在后面：她问的是「如果两个人一起报名，学费有没有优惠」，被答成了带朋友来可以再得 800 元推荐费——同一件事，从客户福利变成了销售提成。这句她听懂了。</p></div>
<div class="qblock qopp"><div class="qlabel r">同一场景，做对了的样子</div><p>波波那一组的客户从来没说过贵。她问最低能是多少，销售给的是「24800 元下个月的班有双十一优惠」这种有边界的答复，而不是一句我去给你申请。<b>不主动开口降价，客户就不会养成砍价的习惯。</b></p></div>
<div class="qblock qreuse"><div class="qlabel g">该说而没说的那句</div><p>贵是因为这三个月的账得这样算：438 节课的线下、9 个月线上、两年内可回来复训一次，考证报名费也在里面。——先解释价，再谈优惠；顺序反了，优惠本身就成了你也觉得贵的证据。</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-17 喊贵 → 转话题 → 降价 3200 ｜ 李雅雯｜11.4 09:51"><img src="assets/prob/P4.png" alt="V-17" loading="lazy"></div><div class="qshot-cap">V-17 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv">
<div class="qcard-h"><span class="qcard-no">V-18 否决</span><h3>她要的是一月班，被回答的是再优惠 1000</h3><div class="qcard-meta">Mo ｜ 10.26 → 11.5 ｜ 全程 210 条 ｜ 到校参观过 ｜ 形态● ● ● ｜ 落点 ✓</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>这组的形态其实是全场最全的：3 个月 + 9 个月线上 + 两年复训，一次讲清。但她从 10.26 起问的就是一月班怎么收费、有没有一个月的进阶班、自己比较赶时间。销售 10.27 主动给过替代方案（先单考国职、做一段自由教练），方向是对的。11.2 她问「<b>费用是21800?</b>」，回答里塞了两次优惠：「<b>现在预定，我去给你申请，可以再给你优惠个1000块钱左右</b>」。</p></div>
<div class="qblock"><div class="qlabel">错在哪</div><ul class="qacts">
<li><i>①</i><span>客户嫌贵，回的是再减 1200——贵在哪、这笔钱买到什么，一句没讲。</span></li>
<li><i>②</i><span>她要的是短周期产品，而这个产品不存在；不存在的东西，用优惠补不上。</span></li>
<li><i>③</i><span>到校参观（11.3）之后她仍在问时间，说明三个月太长这件事，从头到尾没被当成正题处理。</span></li>
</ul></div>
<div class="qblock"><div class="qlabel">代价是什么</div><p>11.5 13:15 她退出：「<b>我们先不过去学习了 谢谢</b>」「时间太长了」。13:25 销售才补上「<b>咱们其实也可以分阶段学习，如果觉得一次性时间太长的话哈</b>」——<b>从她说退出算起 10 分钟后</b>，而这个问题她 11.2 就提过一次。（见主报告 PART 02 · P5）</p></div>
<div class="qblock qopp"><div class="qlabel r">同一场景，做对了的样子</div><p>同一个销售在 10.27 11:41 其实说过对的话：觉得时间和预算投入太大，可以先单考一个国职证书，先做一段自由教练试试。——这句要多说三次，早说三天。</p></div>
<div class="qblock qreuse"><div class="qlabel g">该说而没说的那句</div><p>你要一个月，我们没有一个月；最接近的是单考国职：四天培训、月底考试、3500，先上岗，以后再回来补系统班。——承认产品边界，比降价诚实，也比降价有用。</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V-18 问价被塞优惠 / 退出 10 分钟后才给方案 ｜ Mo｜11.2–11.5"><img src="assets/value/v5.png" alt="V-18" loading="lazy"></div><div class="qshot-cap">V-18 原文截图，点击放大</div></div></div>
</div></article>

</div>
</section>

<section class="sec" id="table">
<div class="sec-head rv"><div class="sec-no">V7 / 逐组对照</div><h2>@@TOTAL@@ 行，一组一行</h2><p class="lead">三批并成一张表，<b>员工列</b>标出这组是谁的，<b>琥珀底的行是你点名的四组</b>。形态 ●●● = 三件套齐；出口 0-3 = 讲透几条；落点 ✓ = 客户下一句变具体或给出动作；结论只按这三项加一条否决判，不掺「客户有没有被打动」。<br><span style="color:var(--ink3)">子渝批前面 7 行是没进入价值传递的组，保留在表里但结论记「排除」，不计入 __N__ 的分母。</span></p></div>

<div class="tbl-wrap rv" style="margin-top:8px"><table><thead><tr><th>组</th><th>员工</th><th>产品线</th><th>形态</th><th>出口</th><th>落点</th><th>结论</th><th>一句话</th></tr></thead><tbody>
__ROWS__
</tbody></table></div>

<p class="note rv">怎么复核：任意一行 → 在 <code>01_原始导出/</code> 的 xlsx 里筛该客户 → 看销售侧有没有讲过对应的内容。名单里的每一句原话都在页面的卡片上配了截图，截图旁的同名 <code>.json</code> 是渲染侧写，可逐字比对。</p>
</section>

<section class="sec" id="end">
<div class="sec-head rv"><div class="sec-no">V8 / 收口</div><h2>三句可以抄，三句必须停</h2></div>

<div class="tbl-wrap rv"><table><thead><tr><th>可以抄</th><th>为什么</th></tr></thead><tbody>
<tr><td>「根据你的需求城市、工作单位类型、薪资要求，给你推荐五个左右的优质就业单位，并且辅导面试」</td><td>出口要可数：五个、按什么挑、辅导到哪一步</td></tr>
<tr><td>「咱们课程是独创的 3+9+两年复训 模式」</td><td>形态要有结构，客户复述得出来才算讲清</td></tr>
<tr><td>「你先确定好，你过来线下集训3个月，减重20公斤都是不在话下的」</td><td>落点要具体过客户自己说的目标</td></tr>
<tr><td>「退伍军人十月有专属 1000 元身份优惠～」</td><td>落点最便宜的形态：用客户给的身份，改一个数字（陈舒那批）</td></tr>
</tbody></table></div>

<div class="tbl-wrap rv" style="margin-top:22px"><table><thead><tr><th>必须停</th><th>为什么</th></tr></thead><tbody>
<tr><td>「我们的课程就是这样子的，兄弟，没法拆开来」</td><td>把「产品不能改」摆在客户需求前面，9 分钟就结束</td></tr>
<tr><td>「我是专业的健身教练培训呀」</td><td>反落点：客户说要什么，你告诉他他要的不是这个</td></tr>
<tr><td>「我去给你申请，可以再给你优惠 1000」</td><td>优惠替代价值：客户问贵在哪，你答能便宜多少</td></tr>
<tr><td>「老辈子说嘛」</td><td>客户替你把出口问出来，你答了句话、没答内容（陈舒那批）</td></tr>
</tbody></table></div>

<div class="judge rv" style="margin-top:26px"><b>一句话　</b>这批人的问题不是「不会讲产品」，是<b>讲的每一句都对，只是没有一句是给这个人的</b>。形态可以靠一句现成的话达标（49 组里绝大多数是这么来的），出口能背模板，落点骗不了人——<b>两项之间差 29 个百分点，这 29 个点才是真正需要练的部分</b>。</div>

<p class="note rv" style="margin-top:30px">本页只处理价值传递一个维度。问题点、谈单节奏、可抄片段、落地建议在主报告：<a href="index.html">回到主报告 index.html</a>。</p>
</section>

<footer class="foot">
  <div class="eyebrow">Value Delivery Audit</div>
  <p>价值传递专项 · 子渝 41 组（2026.11.09）＋ 陈舒 55 组（2026.11.10）＋ 重点 3 组（2026.11.10，姜彦博与陈舒批同一会话，去重）｜ 合并 99 组 · 逐组判读，非词表命中</p>
</footer>

<div class="lb" id="lb">
  <button class="lb-close" aria-label="关闭">×</button>
  <img id="lbImg" alt="">
  <div class="lb-cap" id="lbCap"></div>
</div>

<script src="assets/app.js?v=10"></script>
</body>
</html>
"""


# -*- coding: utf-8 -*-
def combo_html():
    R = [r for r in ROWS if r[1] != "—"]
    N = len(R)

    def key(r):
        return (1 if r[2] == 3 else 0, 1 if r[3] >= 1 else 0, 1 if r[4] == 1 else 0)

    cnt, who = {}, {}
    for r in R:
        k = key(r)
        cnt[k] = cnt.get(k, 0) + 1
        who.setdefault(k, []).append((r[0], batch_of(r)))

    LAB = {
        (1, 1, 1): ("三项全过", "#2C8B7E"),
        (1, 1, 0): ("缺落点", "#C08A2E"),
        (1, 0, 1): ("缺出口", "#C08A2E"),
        (0, 1, 1): ("缺形态", "#C08A2E"),
        (1, 0, 0): ("只有形态", "#B4553A"),
        (0, 1, 0): ("只有出口", "#B4553A"),
        (0, 0, 1): ("只有落点", "#B4553A"),
        (0, 0, 0): ("三项全无", "#8C867A"),
    }

    def mark(k):
        return "形%s 出%s 落%s" % ("○" if k[0] else "✗", "○" if k[1] else "✗", "○" if k[2] else "✗")

    order = sorted(LAB, key=lambda k: (-cnt.get(k, 0), -sum(k), k))

    rows = []
    for k in order:
        name, col = LAB[k]
        v = cnt.get(k, 0)
        pct = round(v * 100.0 / N)
        col = "#B4B2A9" if v == 0 else col
        w = v * 100.0 / N if v else 1.4
        rows.append(
            '<div class="fn-row" style="grid-template-columns:198px 1fr 100px">'
            '<div class="fn-lbl"><b>%s</b>　%s</div>'
            '<div class="fn-track" style="height:26px"><div class="fn-fill" style="width:%.1f%%;background:%s"></div></div>'
            '<div class="fn-drop" style="color:%s">%d 组 · %d%%</div></div>'
            % (name, mark(k), w, col, col, v, pct))

    miss_n = {}
    for k in order:
        m = 3 - sum(k)
        miss_n[m] = miss_n.get(m, 0) + cnt.get(k, 0)

    CARD = [
        (0, "三项都成立", "子渝 %d 组、陈舒 %d 组、重点 %d 组；其中 1 组（Mo）另踩一票否决，所以「合格」的是 %d 组"
         % tuple([sum(1 for r in R if key(r) == (1, 1, 1) and batch_of(r) == bn)
                  for bn in BATCHES] + [len(strict)])),
        (1, "只差一步", "补上那一项就全过。其中 %d 组缺的是落点——最高收益的一块" % cnt.get((1, 1, 0), 0)),
        (2, "只做对一件", "最大一块（%d 组）。形态讲全不会讲出口的 %d 组、只会讲出口的 %d 组，各占一半" % (miss_n.get(2, 0), cnt.get((1, 0, 0), 0), cnt.get((0, 1, 0), 0))),
        (3, "三项全无", "问题不在话术，还没有进入价值传递"),
    ]
    cards = []
    for m, t, d in CARD:
        v = miss_n.get(m, 0)
        cards.append(
            '<div class="card"><div class="tag">缺 %d 项</div>'
            '<div class="big">%d<s>组 · %s%%</s></div>'
            '<p>%s</p><p style="color:var(--ink3)">%s</p></div>'
            % (m, v, round(v * 100.0 / N, 1), t, d))

    def names(k, batch):
        return "、".join(n for n, s in who.get(k, []) if s == batch)

    def pair(k):
        out = []
        for bname, lab in (("子渝批", "子渝"), ("陈舒批", "陈舒"), ("重点批", "重点")):
            v = names(k, bname)
            if v:
                out.append("<span style='color:var(--ink3)'>%s</span> %s" % (lab, v))
        return "<br>".join(out) or "—"

    TBL = [
        ((0, 1, 0), "报价或介绍之后接一句「我们包就业 / 包考证」，说完就停，全程没问过客户想做什么、在哪个城市"),
        ((1, 0, 0), "贴完 438 节课清单、或发完一句「3+9+两年」就结束，出口和落点都是空的"),
        ((0, 1, 1), "出口和落点都成立，只差把产品讲全一件——这一组是收益最高的训练对象"),
        ((1, 1, 0), "产品讲全了、出口也说了，就是没落到这一个人身上；补一句话就能全过"),
    ]
    tbl = "\n".join(
        "<tr><td style=\"width:104px\"><b>%s</b><br><span style=\"font-size:11.5px;color:var(--ink3);font-family:var(--mono);white-space:nowrap\">%s</span></td>"
        "<td class=\"num\">%d</td><td>%s</td><td style=\"font-size:12.5px;color:var(--ink2)\">%s</td></tr>"
        % (LAB[k][0], mark(k), cnt.get(k, 0), d, pair(k))
        for k, d in TBL)

    f3n = sum(1 for r in R if r[2] == 3)
    f3l = sum(1 for r in R if r[2] == 3 and r[4] == 1)
    ltn = sum(1 for r in R if r[2] < 3)
    ltl = sum(1 for r in R if r[2] < 3 and r[4] == 1)

    # 两个人 × 八类：合并之后才有的交叉表
    grid = {}
    for r in R:
        b = batch_of(r)
        grid.setdefault(b, {})[key(r)] = grid.setdefault(b, {}).get(key(r), 0) + 1
    tot = {b: sum(1 for r in R if batch_of(r) == b) for b in BATCHES}
    cross = []
    for k in sorted(LAB, key=lambda k: (-cnt.get(k, 0), -sum(k), k)):
        a = grid.get("子渝批", {}).get(k, 0)
        b = grid.get("陈舒批", {}).get(k, 0)
        c = grid.get("重点批", {}).get(k, 0)
        cross.append(
            "<tr><td><b>%s</b>　<span style='color:var(--ink3);font-family:var(--mono);font-size:11.5px'>%s</span></td>"
            "<td class='num'>%d</td><td class='num'>%d / %d（%d%%）</td>"
            "<td class='num'>%d / %d（%d%%）</td><td class='num'>%d</td></tr>"
            % (LAB[k][0], mark(k), cnt.get(k, 0),
               a, tot["子渝批"], round(a * 100.0 / tot["子渝批"]),
               b, tot["陈舒批"], round(b * 100.0 / tot["陈舒批"]), c))
    cross_html = "\n".join(cross)

    html = """<section class="sec" id="combo">
<div class="sec-head rv"><div class="sec-no">V3 / 缺在哪</div><h2>补一句话能救 __M1__ 组，而「只缺出口」只有 1 组</h2><p class="lead">把 @@N@@ 组按三项达标与否分成八类。这和上一节的达标率是两个问题：达标率说<b>哪一项最弱</b>，分布说<b>哪些短板是绑在一起长出来的</b>——绑在一起的，就不能拆开练。</p></div>

<div class="funnel rv"><h3>@@N@@ 组按三项达标情况分成八类</h3><p class="hint">条长 = 占 @@N@@ 组的比例，按组数从多到少排。○ 达标 ／ ✗ 未达标。</p>
@@ROWS@@
<div class="note">形态的分布仍然是<b>断的</b>：讲到 1 件 __F1__ 组、2 件只有 __F2__ 组（杜康、李小东）、3 件 __F3B__ 组，<b>中间几乎是空的</b>。三批并进来之后这一点更清楚——不是「有人讲得细有人讲得粗」，而是<b>手里有没有那句话</b>：有就一次讲全，没有就只说「三个月系统培训」。</div>
</div>

<div class="concl rv" style="grid-template-columns:repeat(4,minmax(0,1fr))">
@@CARDS@@
</div>

<h3 class="rv" style="font-size:17px;margin:6px 0 14px;color:var(--ink)">四类典型：差别不在讲得多少，在停在哪一步</h3>
<div class="tbl-wrap rv"><table><thead><tr><th>类型</th><th>组数</th><th>标准样子</th><th>名单</th></tr></thead><tbody>
@@TBL@@
</tbody></table></div>

<h3 class="rv" style="font-size:17px;margin:32px 0 14px;color:var(--ink)">同一张表，拆到人身上：谁的问题是哪一格</h3>
<div class="tbl-wrap rv"><table><thead><tr><th>八类</th><th>合计</th><th>子渝 __N1__ 组</th><th>陈舒 __N2__ 组</th><th>重点 __N3__ 组</th></tr></thead><tbody>
__CROSS__
</tbody></table></div>

<div class="judge rv" style="margin-top:22px"><b>拆开看才有用　</b>不同批次压在<strong>不同的格子</strong>上：子渝最重的一格是「只有出口」（@@A11@@ 组），陈舒最重的一格是「缺落点」（@@B21@@ 组）。<b>前者是「讲了出口、没讲产品也没接客户」，后者是「产品讲完了、客户也接住了，就差最后一句」</b>。同一个三项口径，落到具体做法上是两种完全不同的补法——所以这张表不能只看总数。<br><span style="color:var(--ink3)">重点那 3 组只有三行、来自三位老师，<b>不做个人比率解读</b>，只用来标出「另外三位老师身上，缺口长在哪一格」。</span></div>

<p class="note rv">「缺出口」这一行只有 <b>1 组</b>，不是漏写。形态讲到三件的 @@F3@@ 组里，@@F3O@@ 组顺手就把出口带上了（438 清单里本来就写着九个月线上、两年复训、保姆式就业推荐；陈舒那句模板后面紧跟就业流程）；剩下 @@F3N@@ 组里，@@F3NB@@ 组是贴完清单就停、出口和落点一起缺。<b>「出口讲得好、只差挂客户」这种理想状态，@@N@@ 组里只出现过 1 次。</b></p>

<article class="qcard rv neg">
<div class="qcard-h"><span class="qcard-no">V3-1 只有出口</span><h3>就业讲得比谁都清楚，客户一句没回</h3><div class="qcard-meta">Zz ｜ 子渝 ｜ 10.30 16:2 → 11.2 09:56 ｜ 全程 45 条 ｜ <b>形态 ●○○</b> ｜ <b>出口 2 条</b> ｜ 落点 ✗</div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>10.30 客户问「那咱们这边费用差不多多少」，收到的是「兄弟，看一下你想考哪个证书」加一句双十一优惠 1200。两天后 11.2 上午，销售单方面发来四个小程序和两段就业说明：两种模式、按意向城市和薪资挑 3~5 个单位、或直接进集团连锁高端私教品牌。<b>从这条开始，客户再没说过一句话。</b></p></div>
<div class="qblock"><div class="qlabel">差在哪</div><p>这段就业是 @@N@@ 组里讲得最细的之一——有模式、有单位数、有城市和薪资的自选项，出口这一项它拿满分。问题在位置：它出现在客户问过价、又被隔了两天之后，而且是从头讲产品。<b>整段没有一句回到客户已经说过的目的上</b>，也没有问一句你想在哪座城市、想要什么样的健身房。出口再好，也是发给一个已经凉掉的人。</p></div>
<div class="qblock qopp"><div class="qlabel r">同一项做对了的样子（R 那一组）</div><p>R 组客户问「邢台有没有」，销售没说一句「有的」，而是去查了就业库、把邢台的岗位发过来——出口挂在一个具体城市上，客户当场就往下问了。</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V3-1 就业两种模式讲得最细的一段，但客户零回应 ｜ Zz｜11.2 09:53"><img src="assets/value/vz.png" alt="V3-1" loading="lazy"></div><div class="qshot-cap">V3-1 原文截图，点击放大</div></div></div>
</div></article>

<article class="qcard rv neg">
<div class="qcard-h"><span class="qcard-no">V3-2 只有落点</span><h3>客户都要来参观了，他还是没讲清学完能干嘛</h3><div class="qcard-meta">星辰Redamancy ｜ 子渝 ｜ 11.8 19:24 → 19:47 ｜ 全程 32 条 ｜ <b>形态 ●○○</b> ｜ <b>出口 0 条</b> ｜ 落点 <b>✓</b></div></div>
<div class="qcard-body"><div class="qcard-txt">
<div class="qblock"><div class="qlabel">发生了什么</div><p>客户第一句就是「成都有学校吗我想后面自己开健身房店」。销售接住了这个目的——「你自己开健身房的话，那你自己的专业技能还是要过硬啊」，客户随即要定位，「有时间了导航过去」。<b>到这一步落点是成立的：客户给出了动作。</b></p></div>
<div class="qblock"><div class="qlabel">差在哪</div><p>整段没有一条出口：没讲学完能去哪工作、能拿多少、证书能干什么用。销售给的理由只有技能要过硬，紧接着是一份从解剖学、营养学讲起的课程清单。<b>客户被听懂了，却不知道这条路最后通向哪里</b>——那剩下的判断依据就只有一个：价格。这 @@E@@ 组是全部类型里最可惜的，只差最后一句。</p></div>
<div class="qblock qopp"><div class="qlabel r">同一项做对了的样子（长生那一组）</div><p>长生组把「就业」讲成可以清点的东西：哪几个单位、按城市和薪资怎么挑、面试辅导什么、上岗之后谁跟进——客户听完自己算得出 19300 值不值。</p></div>
</div>
<div class="qcard-shot"><div class="inner"><div data-zoom="V3-2 落点成立（客户要定位准备参观），但整段零出口 ｜ 星辰Redamancy｜11.8 19:24"><img src="assets/value/vxc.png" alt="V3-2" loading="lazy"></div><div class="qshot-cap">V3-2 原文截图，点击放大</div></div></div>
</div></article>

<div class="judge rv"><b>最反直觉的一条　</b>形态讲到三件的 @@A@@ 组里，落点只有 @@B@@ 组成立（@@BP@@%）；形态不到三件的 @@C@@ 组里，落点成立 @@D@@ 组（@@DP@@%）。<b>讲产品讲得最全的那批人，四分之三没接住客户。</b>念得越完整，越像在输出，越不会停下来听——完达山、顺吗、人土土.、TK 都是三件套背得滚瓜烂熟，客户说还在上班、时间不行，被换成了订金、协调一下。</div>

<div class="judge rv"><b>所以先练哪个（按缺口大小，不按难易）　</b><b>P0 落点</b>（缺 @@L@@ 组）：它是唯一能让前两项生效的一项，To 出口两条、59 轮对话，落点为零，客户问完价就消失。<br><br><b>P1 形态</b>（缺 @@F@@ 组）：但教法必须是「按客户情况拆」，不能是「背完整三件套」——上面 @@BP@@% 对 @@DP@@% 就是证据，背得越熟反而越不接客户。<br><br><b>P2 出口</b>（缺 @@O@@ 组）：最容易补，模板化程度最高。但要单独拎出「只有落点」那 @@E@@ 组——客户被听懂了却不知道路怎么走，差最后一步。</div>
</section>"""

    html = html.replace("@@ROWS@@", "\n".join(rows))
    html = html.replace("@@CARDS@@", "\n".join(cards))
    html = html.replace("@@TBL@@", tbl)
    html = html.replace("__CROSS__", cross_html)
    html = html.replace("@@N@@", str(N))
    html = html.replace("__N1__", str(tot["子渝批"])).replace("__N2__", str(tot["陈舒批"]))
    f3o = sum(1 for r in R if r[2] == 3 and r[3] >= 1)
    html = html.replace("@@F3@@", str(f3n)).replace("@@F3O@@", str(f3o))
    html = html.replace("@@F3N@@", str(f3n - f3o))
    html = html.replace("@@F3NB@@", str(sum(1 for r in R if r[2] == 3 and r[3] == 0 and r[4] == 0)))
    html = html.replace("@@A@@", str(f3n)).replace("@@B@@", str(f3l))
    html = html.replace("@@C@@", str(ltn)).replace("@@D@@", str(ltl))
    html = html.replace("@@BP@@", str(round(f3l * 100.0 / f3n)))
    html = html.replace("@@DP@@", str(round(ltl * 100.0 / ltn)))
    html = html.replace("@@A11@@", str(grid.get("子渝批", {}).get((0, 1, 0), 0)))
    html = html.replace("@@B21@@", str(grid.get("陈舒批", {}).get((1, 1, 0), 0)))
    html = html.replace("@@E@@", str(cnt.get((0, 0, 1), 0)))
    html = html.replace("@@F@@", str(N - f3n))
    html = html.replace("@@L@@", str(N - sum(1 for r in R if r[4] == 1)))
    html = html.replace("@@O@@", str(N - sum(1 for r in R if r[3] >= 1)))
    html = html.replace("__M1__", str(cnt.get((1, 1, 0), 0)))
    html = html.replace("__F1__", str(sum(1 for r in R if r[2] == 1)))
    html = html.replace("__F2__", str(sum(1 for r in R if r[2] == 2)))
    html = html.replace("__F3B__", str(sum(1 for r in R if r[2] == 3)))
    html = html.replace("__N3__", str(tot["重点批"]))
    return html


html = HTML.replace("__ROWS__", rows_html())
html = html.replace("__COMBO__", combo_html())

# 反面卡片标签改红：样式在 assets/style.css 的 .qcard.neg .qcard-no 里。
# 注意这一趟必须在「重排卡号」之前跑——它认的是模板里写死的那批卡号。
NEG_IDS = set(range(9, 17))


def _tag_neg(src):
    pat = re.compile(r'<article class="qcard rv(?: neg| focus| neg focus)?(?:"[^>]*)?>.*?</article>', re.S)

    def rep(m):
        blk = m.group(0)
        if blk.startswith('<article class="qcard rv neg">'):
            return blk
        no = re.search(r'qcard-no">V-(\d+)', blk)
        if no and int(no.group(1)) in NEG_IDS:
            return blk.replace('<article class="qcard rv">', '<article class="qcard rv neg">', 1)
        return blk

    return pat.sub(rep, src)


ART = re.compile(r'<article class="qcard[^>]*>.*?</article>', re.S)


def _renumber(src):
    """按文档顺序把 V-1..V-n 重新排一遍。

    四张重点卡插进正文之后，中间那些卡号会整体后移；手改一错就是截图注和
    卡号对不上。这里两趟走：先全部换成占位符，再统一写回新号，避免新旧号互相覆盖。
    """
    blocks = [m.group(0) for m in ART.finditer(src)]
    olds = []
    for blk in blocks:
        m = re.search(r'qcard-no">V-(\d+)', blk)
        olds.append(m.group(1) if m else None)

    seq, k = {}, 0
    for i, o in enumerate(olds):
        if o is None:
            continue
        k += 1
        seq[i] = k

    out = src
    for i, o in seq.items():
        out = out.replace(blocks[i], re.sub(r'V-%s(?![0-9])' % re.escape(olds[i]),
                                            "@@VN%d@@" % i, blocks[i]), 1)
    for i, n in seq.items():
        out = out.replace("@@VN%d@@" % i, "V-%d" % n)
    assert "@@VN" not in out, "还有没换掉的卡号占位符"
    return out, k


html = _tag_neg(html)
html, NCARD = _renumber(html)

# ——— 计数类占位符 ———
_N = base
NOO = _N - len(o1)
PCT = lambda a, b: round(a * 100.0 / b) if b else 0

rows_funnel = [(len(f3), "形态"), (len(o1), "出口"), (len(l1), "落点"), (len(strict), "严")]
for i, (v, _nm) in enumerate(rows_funnel, 1):
    html = html.replace("__W%d__" % i, str(max(PCT(v, _N), 1)))
    html = html.replace("__H%d__" % i, str(v))
    html = html.replace("__D%d__" % i, "−%d" % (_N - v))

html = html.replace("__N__", str(_N))
html = html.replace("__O2__", str(len(o2)))
html = html.replace("__NOO__", str(NOO))
html = html.replace("__VETO__", str(len(veto)))
html = html.replace("__H4P__", "%.1f" % (len(strict) * 100.0 / _N))
html = html.replace("@@TOTAL@@", str(len(ROWS)))
html = html.replace("@@ST@@", str(len(strict)))

# 分人达标率（V2 结尾那句「形态 a% 对 b%、落点 c% 对 d%」）
def _batch_rate(bname, key):
    rows = [r for r in ROWS if batch_of(r) == bname and r[1] != "—"]
    if not rows:
        return 0
    return PCT(sum(1 for r in rows if key(r)), len(rows))

html = html.replace("__PF_A__", str(_batch_rate("子渝批", lambda r: r[2] == 3)))
html = html.replace("__PF_B__", str(_batch_rate("陈舒批", lambda r: r[2] == 3)))
html = html.replace("__PL_A__", str(_batch_rate("子渝批", lambda r: r[4] == 1)))
html = html.replace("__PL_B__", str(_batch_rate("陈舒批", lambda r: r[4] == 1)))

left = re.findall(r"__[A-Z0-9_]+__", html)
assert not left, "还有没替换的占位符：%s" % sorted(set(left))
left = re.findall(r"@@[A-Z0-9_]+@@", html)
assert not left, "还有没替换的占位符：%s" % sorted(set(left))

io.open(OUT, "w", encoding="utf-8", newline="").write(html)
print("写出", OUT, len(html), "字符 ｜ 卡片", NCARD, "张")
print("分母", base, "形态齐", len(f3), "出口", len(o1), "落点", len(l1),
      "严全过", len(strict), "宽全过", len(wide), "否决", len(veto), "重点", len(FO))
