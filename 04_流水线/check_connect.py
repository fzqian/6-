# -*- coding: utf-8 -*-
"""接通建联页自检 —— 查的是「这一页特有的东西」，与 check.py 的 15 项分工不同。

check.py 那 15 项是给主报告写的（板块顺序、漏斗、CRM 标识），专项页对不上。
这里只查五组：

  1 板块只有两块（口径 + 做对的）
  2 没有残留：占位符、V-/M- 卡号、未替换的 %s
  3 四要件在长图上标全了，且页面声明的条数和侧写一致
  4 口径里的每一句「原文」都能在两份 docx 里逐字找到（去空格比对）
  5 卡片「可以直接抄的原话」每一句都能在同一张图的侧写里找到

第 4 组是这套校验里最要紧的一条：页面抄错了文档原话、或者文档改了页面没跟，
都会在这里断。找不到 docx 时降级为提示，不判失败（包外单独跑也能用）。

用法：python check_connect.py 接通建联.html
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "接通建联.html")
MARK = os.path.join(ROOT, "assets", "connect", "c1.json")
IMG = os.path.join(ROOT, "assets", "connect", "c1.png")
DOC_A = os.path.join(ROOT, "03_依据文件", "招生老师沟通六阶段参考场景.docx")
DOC_B = os.path.join(ROOT, "03_依据文件", "招生老师参考话术.docx")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

bad_n = 0


def ok(msg):
    print("  ✓ " + msg)


def bad(msg):
    global bad_n
    bad_n += 1
    print("  ✗ " + msg)


def squeeze(s):
    """比对原文时把空白全去掉——docx 里的换行、全角空格、页边距字符都不该算差异。"""
    return re.sub(r"\s+", "", s or "")


def docx_all(path):
    try:
        import docx
    except ImportError:
        return None
    if not os.path.isfile(path):
        return None
    d = docx.Document(path)
    parts = [p.text for p in d.paragraphs]
    for tb in d.tables:
        for row in tb.rows:
            for c in row.cells:
                parts.append(c.text)
    return squeeze("\n".join(parts))


h = io.open(SRC, encoding="utf-8").read()
print("检查 %s（%d 字节）" % (os.path.basename(SRC), len(h.encode("utf-8"))))

# ——— 1. 板块只两块 ———
print("[1] 板块")
secs = re.findall(r'<section class="sec" id="([\w-]+)"', h)
if secs == ["c-rule", "c-good"]:
    ok("板块是 %s，只有两块" % secs)
else:
    bad("板块是 %s，预期 ['c-rule', 'c-good']" % secs)

for must in ("id=\"c-rule\"", "id=\"c-good\"", "接通建联"):
    if must not in h:
        bad("缺 %s" % must)

# ——— 2. 残留 ———
print("[2] 残留")
left = re.findall(r"__[A-Z0-9_]+__|@@[A-Z0-9_]+@@|%s", h)
if left:
    bad("还有没替换的占位符：%s" % left[:5])
else:
    ok("无占位符残留")

wrong_no = re.findall(r">\s*[VM]-\d+", h)
if wrong_no:
    bad("卡号写成了 %s，这一页只有 C-1" % wrong_no[:3])
else:
    ok("无 V-/M- 卡号残留")

# ——— 3. 卡片与长图 ———
print("[3] 卡片与长图")
arts = re.findall(r'<article id="c\d+" class="qcard[^"]*"[^>]*>.*?</article>', h, re.S)
if len(arts) != 1:
    bad("卡片 %d 张，预期 1 张" % len(arts))
else:
    ok("1 张卡（C-1）")

imgs = re.findall(r'<img[^>]+src="(assets/[^"]+)"', h)
if len(imgs) != 1:
    bad("图 %d 张，预期 1 张" % len(imgs))
elif not os.path.isfile(os.path.join(ROOT, imgs[0])):
    bad("图找不到文件：%s" % imgs[0])
else:
    ok("图存在：%s" % imgs[0])
    # 量的是页面里实际引的那张，不是写死的 c1.png——否则换成别的图查不出来
    from PIL import Image
    w, hh = Image.open(os.path.join(ROOT, imgs[0])).size
    if hh < w * 4:
        bad("长图只有 %dx%d，不像整段聊天记录（高至少要 4 倍宽）" % (w, hh))
    else:
        ok("长图 %dx%d，高是宽的 %.1f 倍" % (w, hh, hh / w))
    if os.path.basename(imgs[0]) != "c1.png":
        bad("卡片引的是 %s，与侧写 c1.json 对不上" % imgs[0])

if not os.path.isfile(MARK):
    bad("缺侧写：assets/connect/c1.json")
    MAN = {}
else:
    MAN = json.load(io.open(MARK, encoding="utf-8"))
    hit = sorted(MAN.get("stages_hit", []))
    if hit != ["1", "2", "3", "4"]:
        bad("侧写里只标了 %s，四要件没标全" % hit)
    else:
        ok("侧写里四要件全标：①②③④")

    if not MAN.get("span"):
        bad("侧写没记 span，无法证明这是整段连续画下来的")
    else:
        ok("span=%s（整段连续）" % MAN["span"])

    if len(MAN.get("texts", [])) < 20:
        bad("侧写只记了 %d 条原文，太少了" % len(MAN.get("texts", [])))
    else:
        ok("%d 条原文记在侧写里" % len(MAN["texts"]))

    # 页面写的条数必须和侧写一致
    m = re.search(r"选段\s*(\d+)\s*条（整组\s*(\d+)\s*条）", h)
    if not m:
        bad("卡片上没写「选段 N 条（整组 M 条）」")
    else:
        span = MAN["span"]
        want = span[1] - span[0] + 1
        if int(m.group(1)) != want:
            bad("页面写选段 %s 条，侧写 span 是 %d 条" % (m.group(1), want))
        else:
            ok("页面的「选段 %s 条」与 span 一致" % m.group(1))

# ——— 4. 口径原文 ————
print("[4] 口径原文（对两份 docx 逐字核）")
A = docx_all(DOC_A)
B = docx_all(DOC_B)
if A is None or B is None:
    print("  ! 找不到 03_依据文件 下的两份 docx，跳过原文核对（不算失败）")
else:
    def strip_tags(s):
        return re.sub(r"<[^>]+>", "", s)

    # 关键：原文从**页面**里抽，不是拿脚本里的常量去查文档。
    # 早期版本用常量查，页面把「实质回应」改成「回应」照样全绿——查了个寂寞。
    page_quotes = []
    for m in re.finditer(r'<p class="l2q">(.*?)</p>', h, re.S):
        t = strip_tags(m.group(1)).strip()
        if t:
            page_quotes.append(("话术引用", t))
    for m in re.finditer(r'<b class="cc-q">「([^」]+)」</b>', h):
        page_quotes.append(("判据引用", m.group(1).strip()))

    if len(page_quotes) < 6:
        bad("页面里只抽到 %d 处原文引用，少了（判据 2 + 话术 4 起步）" % len(page_quotes))
    lost = []
    for kind, q in page_quotes:
        sq = squeeze(q)
        if sq in A or sq in B:
            ok("%s：%s…" % (kind, q[:18]))
        else:
            lost.append((kind, q))
            bad("%s 在 docx 里找不到：%s…" % (kind, q[:36]))

    # 禁区：只核清单本身，不扫全文——卡片正文里也会提到「还在吗」当例子，
    # 全文搜会把这个改动盖掉（早期版本就这么漏的）
    BAN = ["喂喂喂，还了解吗？", "吱一声啊", "还在吗", "说句话呀",
           "在不在？看到回一下", "怎么不说话了？还考虑吗？"]
    m_ban = re.search(r'<ul class="cc-ban">(.*?)</ul>', h, re.S)
    if not m_ban:
        bad("找不到禁区清单 .cc-ban")
    else:
        ban_page = [strip_tags(x).strip() for x in
                    re.findall(r"<li[^>]*>(.*?)</li>", m_ban.group(1), re.S)]
        ban_page = [x for x in ban_page if x]
        if len(ban_page) != len(BAN) + 1:
            bad("禁区清单 %d 条，预期 %d 条（6 句 + 一类表情）" % (len(ban_page), len(BAN) + 1))
        miss_page = [b for b in BAN if squeeze(b) not in squeeze("".join(ban_page))]
        miss_doc = [b for b in BAN if squeeze(b) not in B]
        if miss_page:
            bad("禁区清单里缺/改错了这几句：%s" % miss_page)
        elif miss_doc:
            bad("禁区这几句在 docx 里找不到：%s" % miss_doc)
        else:
            ok("禁区 6 句清单与 docx 逐字一致")

    if "去除“部分达到”的模糊界限" not in h:
        bad("页面里没写「去除部分达到」这一条——这是判据的硬约束，不能省")
    else:
        ok("页面写明了「去除部分达到」")

# ——— 5. 可抄原话回查侧写 ———
print("[5] 可抄原话回查")
reuse = re.findall(r'<li><b>「([^」]+)」</b>', h)
if not reuse:
    bad("没找到「可以直接抄的原话」")
else:
    pool = squeeze("".join(MAN.get("texts", [])))
    lost = [q for q in reuse if squeeze(q) not in pool]
    if lost:
        for q in lost:
            bad("这句在长图侧写里找不到：%s" % q[:34])
    else:
        ok("%d 句原话全部能在 c1.json 的 texts 里逐字找到" % len(reuse))

# ——— 6. 结构小项 ———
print("[6] 结构")
n_st = len(re.findall(r'class="st s[1-4]"', h))
if n_st != 4:
    bad("四要件卡 %d 张，预期 4 张" % n_st)
else:
    ok("hero 四要件卡齐")

qrows = len(re.findall(r'<tr class="qt">', h))
if qrows != len(arts):
    bad("速查表 %d 行，卡片 %d 张，对不上" % (qrows, len(arts)))
else:
    ok("速查表行数与卡片数一致（%d）" % qrows)

for kw in ("招生老师沟通六阶段参考场景", "招生老师参考话术", "414"):
    if kw not in h:
        bad("页脚/信息条缺了来源：%s" % kw)

# ——— 7. 口径整体折叠 ———
# 这一页给销售看的是那段聊天记录。口径（判据卡 + 两种线索 + 代称 + 禁区）默认折成一
# 条，进页面不会先撞上一屏解释；要查的时候点开。所以这里查四件事：折没折、默认是不
# 是收着的、该折进去的有没有漏在外面、点导航能不能直接展开。
print("[7] 口径折叠")
FOOT = ["两种线索，两种开口", "客户不报名字：代称也算称呼", "八句禁区"]
m_fold = re.search(r'<details class="cc-fold[^"]*"[^>]*id="ccFold"([^>]*)>(.*?)</details>', h, re.S)
if not m_fold:
    bad("找不到口径折叠块 <details id=\"ccFold\">")
else:
    attrs, inner = m_fold.group(1), m_fold.group(2)
    if re.search(r'(?:^|\s)open(?:\s|=|$)', attrs):
        bad("折叠块带 open，默认是展开的——进页面还是会先看到一屏口径")
    else:
        ok("默认收起（<details> 无 open）")

    m_sum = re.search(r'<summary[^>]*>(.*?)</summary>', inner, re.S)
    if not m_sum:
        bad("折叠块没有 <summary>，收起来后没有头")
    else:
        st = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", m_sum.group(1)))
        miss = [x for x in ("C1/口径", "展开看", "收起") if x not in st]
        if miss:
            bad("折叠条的头上缺：%s（现在写的是「%s」）" % (miss, st[:40]))
        else:
            ok("折叠条写了「C1 / 口径」和展开/收起两态")

    # 四要件卡不折：它要一直摆在顶部，折进去就看不见判据了
    n_in = len(re.findall(r'class="st s[1-4]"', inner))
    m_hero = re.search(r'<header class="hero[^"]*">(.*?)</header>', h, re.S)
    n_hero = len(re.findall(r'class="st s[1-4]"', m_hero.group(1))) if m_hero else 0
    if n_in:
        bad("四要件卡有 %d 张被折进去了——它要留在顶部" % n_in)
    elif n_hero != 4:
        bad("顶部四要件卡 %d 张，预期 4 张还在 hero 里" % n_hero)
    else:
        ok("四要件卡 4 张留在顶部，没被折进去")

    for t in FOOT:
        if "<h3>" + t + "</h3>" not in inner:
            bad("折叠块里找不到「%s」这一块——要么没折进去，要么这一块被改名了" % t)
    if all("<h3>" + t + "</h3>" in inner for t in FOOT):
        ok("两种线索 / 代称 / 八句禁区 都在折叠块里")

    # section 里除了这个 details 不该再有别的内容，否则折叠等于没折
    m_sec = re.search(r'<section class="sec" id="c-rule">(.*?)</section>', h, re.S)
    if m_sec:
        rest = m_sec.group(1).replace(m_fold.group(0), "")
        rest_txt = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", rest))
        if rest_txt:
            bad("口径区折叠块外面还有没折进去的内容：%s…" % rest_txt[:30])
        else:
            ok("口径区只剩折叠块，外面没有漏的段落")

    if re.search(r'location\.hash\s*===\s*[\'"]\#c-rule[\'"]', h):
        ok("点导航「一 · 口径」会自动展开")
    else:
        bad("没有 #c-rule 自动展开的脚本——点导航跳过去只看见一条收着的折叠条")

print()
if bad_n:
    print("%d 项未通过" % bad_n)
    sys.exit(1)
print("全部通过")
