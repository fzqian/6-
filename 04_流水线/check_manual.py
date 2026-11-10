# -*- coding: utf-8 -*-
"""口径与范本（教材版）交付前自检。

只查这个页面特有的东西——主报告那 15 项在 check.py 里，专项页的分母与漏斗在
audit_value.py 里，这里重复没有意义。五件事：

  1 板块  只能有两块（口径 / 做对的），多一块就说明从主页面带多了
  2 编号  不能残留 V-数字、V1/V4、「逐组表」这类只属于主页面的说法
  3 卡片  卡号 M-1..M-n 连续；每张卡三个记分牌；图都在，且都能点开放大
  4 速查表 行数 = 卡片数；点客户名能跳到对应卡；表里的三项与卡里的三项逐字一致
  5 引语  调 check_quotes：正文每个「」都能在同一张卡的截图侧写里找到

用法：python check_manual.py [口径与范本.html]
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import check_quotes  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "口径与范本.html")
DATA = os.path.join(ROOT, "02_过程文件", "dialogs_value.json")

h = io.open(SRC, encoding="utf-8").read()
fails = []


def ok(m):
    print("  \u2713 " + m)


def bad(m):
    fails.append(m)
    print("  \u2717 " + m)


print("自检：%s\n" % os.path.basename(SRC))

# ——— 1 板块 ———
print("[1] 板块")
ids = re.findall(r'<section class="sec[^"]*" id="([\w-]+)"', h)
if ids == ["m-rule", "m-good"]:
    ok("只有两块：口径 → 做对的")
elif not ids:
    bad("一个 section 都没有")
else:
    bad("板块是 %s，预期只有 m-rule / m-good 两块" % ids)

# ——— 2 编号 ———
print("[2] 编号与残留")
left = re.findall(r"__[A-Z0-9_]+__", h) + re.findall(r"@@[A-Z0-9_]+@@", h)
if left:
    bad("还有没替换的占位符：%s" % sorted(set(left)))
else:
    ok("没有残留占位符")

vno = re.findall(r"V-\d+", h)
if vno:
    bad("还留着主页面卡号：%s" % sorted(set(vno))[:6])
else:
    ok("卡号已全部换成 M-")

vs = sorted(set(re.findall(r"V[1-8] / ", h)))
if vs:
    bad("还留着主页面板块号：%s" % vs)
else:
    ok("板块号 V1..V8 已清干净")

for w in ("逐组表",):
    if w in h:
        bad("还留着只属于主页面的说法：「%s」" % w)
if "逐组表" not in h:
    ok("没有指向页面外结构的引用")

# ——— 3 卡片 ———
print("[3] 卡片")
# 注意 [^>]* ：三张 focus 卡还带 style="..."，卡在 class 上会漏掉三张
blocks = re.findall(r'<article id="m\d+" class="[^"]*"[^>]*>.*?</article>', h, re.S)
if not blocks:
    bad("一张卡都没切到")
    blocks = []

nums = [int(re.search(r'<span class="qcard-no">M-(\d+)', b).group(1))
        for b in blocks if re.search(r'<span class="qcard-no">M-(\d+)', b)]
if nums == list(range(1, len(blocks) + 1)):
    ok("%d 张卡，卡号 M-1..M-%d 连续" % (len(blocks), len(blocks)))
else:
    bad("卡号不连续：%s" % nums)

anchors = re.findall(r'<article id="(m\d+)"', h)
if anchors == ["m%d" % i for i in range(1, len(blocks) + 1)]:
    ok("%d 个 anchor 按顺序齐全" % len(anchors))
else:
    bad("anchor 不对：%s" % anchors)

nob = [i + 1 for i, b in enumerate(blocks) if len(re.findall(r'class="mm ', b)) != 3]
if nob:
    bad("这些卡的三项记分牌不是三个：%s" % nob)
else:
    ok("每张卡三个记分牌（形态 / 出口 / 落点）")

imgs = re.findall(r'<img[^>]+src="(assets/(?:value|mark)/[^"]+)"', h)
lost = [s for s in imgs if not os.path.isfile(os.path.join(ROOT, s))]
if len(imgs) != len(blocks):
    bad("图 %d 张，卡 %d 张，对不上" % (len(imgs), len(blocks)))
elif lost:
    bad("这些图找不到文件：%s" % lost)
else:
    ok("%d 张截图全部存在，一卡一图" % len(imgs))

# 每张卡必须是「整段聊天记录」而不是挑出来的几句：图要够长（长图），
# 四块分析要齐，侧写里要有三段标注
try:
    from PIL import Image as _Img
except Exception:                                    # 没装 PIL 就跳过尺寸检查
    _Img = None

need = ["发生了什么", "做对了什么", "为什么有效", "可以直接抄的原话"]
for i, b in enumerate(blocks, 1):
    labs = re.findall(r'<div class="qlabel[^"]*">(.*?)</div>', b)
    labs = [re.sub(r"<[^>]+>", "", x).strip() for x in labs]
    if labs != need:
        bad("M-%d 的分析块是 %s，预期四块：%s" % (i, labs, need))

if _Img:
    for i, s in enumerate(imgs, 1):
        p = os.path.join(ROOT, s)
        if not os.path.isfile(p):
            continue
        w, ht = _Img.open(p).size
        if ht < w * 4:
            bad("M-%d 的图只有 %dx%d，不像整段聊天记录（高至少要 4 倍宽）" % (i, w, ht))
    ok("每张卡四块分析齐全，长图都是整段")

for i, s in enumerate(imgs, 1):
    j = os.path.splitext(os.path.join(ROOT, s))[0] + ".json"
    if not os.path.isfile(j):
        bad("M-%d 的图缺同名 .json 侧写" % i)
        continue
    man = json.load(io.open(j, encoding="utf-8"))
    st = sorted(m["stage"] for m in man.get("marks", []))
    if st != ["1", "2", "3"]:
        bad("M-%d 的图只标了 %s，三项没标全" % (i, st))
    elif not man.get("span"):
        bad("M-%d 的图没记录 span（不是整段画的）" % i)
    else:
        ok("M-%d 长图 %d 条、三项各标好、span=%s"
           % (i, len(man.get("texts") or []), man["span"]))

zoom = len(re.findall(r'data-zoom="M-\d+', h))
if zoom < len(blocks):
    bad("data-zoom 只有 %d 个，%d 张卡点不开" % (zoom, len(blocks)))
else:
    ok("%d 张卡都能点开放大" % zoom)

# ——— 4 速查表 ———
print("[4] 速查表")
tb = re.search(r'<table class="mm-tbl">.*?</table>', h, re.S)
if not tb:
    bad("找不到速查表")
else:
    trs = re.findall(r'<tr class="qt[^"]*">(.*?)</tr>', tb.group(0), re.S)
    if len(trs) != len(blocks):
        bad("速查表 %d 行，卡片 %d 张" % (len(trs), len(blocks)))
    else:
        ok("%d 行，一组一行" % len(trs))

    jumped = re.findall(r'href="#(m\d+)"', tb.group(0))
    miss = [j for j in jumped if 'id="%s"' % j not in h]
    if miss:
        bad("速查表指向不存在的卡片：%s" % miss)
    elif jumped != ["m%d" % i for i in range(1, len(trs) + 1)]:
        bad("速查表跳转顺序与卡片不一致：%s" % jumped)
    else:
        ok("%d 个跳转全部命中对应卡片" % len(jumped))

    # 表里的三项必须和卡里的三项逐字一致
    diff = []
    for i, (tr, b) in enumerate(zip(trs, blocks), 1):
        mt = re.findall(r'<span class="mm [^"]*">(.*?)</span>', tr)[:3]
        mb = re.findall(r'<span class="mm [^"]*">(.*?)</span>', b)[:3]
        if mt != mb:
            diff.append((i, mt, mb))
    if diff:
        for i, mt, mb in diff:
            bad("第 %d 行与 M-%d 卡不一致：表 %s ｜ 卡 %s" % (i, i, mt, mb))
    else:
        ok("表里的三项与卡片逐字一致")

# ——— 5 引语 ———
print("[5] 引语可核对")
n, errs, ncard = check_quotes.check(SRC, DATA if os.path.exists(DATA) else None)
if errs:
    for e in errs[:20]:
        bad(e)
    bad("共 %d 处引语在图上看不到" % len(errs))
else:
    ok("%d 张卡 / %d 处引语，全部能在截图侧写里找到" % (ncard, n))

print()
if fails:
    print("未通过 %d 项，改完再交付" % len(fails))
    sys.exit(1)
print("全部通过")
