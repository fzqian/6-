# -*- coding: utf-8 -*-
"""报告自检器 —— 交付前跑一次，把新版式跑偏的地方指出来。

用法：
    python check.py ../web-report/index.html

检查九项，任何一项 ✗ 都别交付：
  1 五个板块 id 齐全且顺序正确
  2 顶栏导航链接与 section id 对得上
  3 引用的图片全部存在（裂图是高发事故）
  4 每个 img 外层有 data-zoom（否则点开放大失效）
  5 没有残留的占位符（【填 / {{ / TODO / XXX）
  6 style.css 与模板库逐字节一致（改了 CSS 版式就跑偏）
  7 app.js 与模板库逐字节一致
  8 style.css 与 app.js 的 ?v= 版本号一致
  9 用到的 class 在 style.css 里都有定义（防自己造 class）
 10 正文里的每一个「」，都能在同卡片右侧那张截图上找到（引语可核对）
 11 顶部概要条齐全：数据 / 依据 / 底稿链接，且链接指向的文件真实存在
 12 引号外没有编造：金额 / 日期 / 时间点 / 外文词都能在原文里找到，括号补语有出处
 13 片段漏斗的四个数字能复算，六段片段的客户都在数据里
 14 案例头的 CRM 标识：ID 有出处、意向级别与标签颜色对得上、对照表里有这一条
 15 图片放大：每张图都点了能开，灯箱节点齐、app.js 里有滚轮与拖动

第 10 项需要 shot.py 生成的同名 .json 侧写。对话原文用 --data 指定，
不指定就在报告目录 / 套件目录 / 当前目录找 dialogs_all.json。
不想查这一项加 --no-quotes。

退出码 0 = 全过；1 = 有 ✗。
"""
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

KIT = os.path.dirname(os.path.abspath(__file__))
ORDER = ["overview", "problems", "rhythm", "good", "actions"]
# 纯语义标记：没有独立样式，样式来自上级 class，不算跑偏
ALLOW = {"qwrap-val"}
LABEL = {
    "overview": "PART 01 方法",
    "problems": "PART 02 问题点",
    "rhythm": "PART 03 谈单节奏",
    "good": "PART 04 正面标杆",
    "actions": "PART 05 落地",
}

ok_n = 0
bad = []


def ok(msg):
    global ok_n
    ok_n += 1
    print("  \u2713 %s" % msg)


def fail(msg):
    bad.append(msg)
    print("  \u2717 %s" % msg)


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    argv = [x for x in sys.argv[1:]]
    no_quotes = "--no-quotes" in argv
    argv = [x for x in argv if x != "--no-quotes"]
    data = None
    if "--data" in argv:
        i = argv.index("--data")
        data = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
    if len(argv) < 2 and not argv:
        print(__doc__)
        return 2
    if not argv:
        print(__doc__)
        return 2
    src = os.path.abspath(argv[0])
    if not os.path.isfile(src):
        print("找不到文件：%s" % src)
        return 2
    root = os.path.dirname(src)
    h = open(src, encoding="utf-8").read()

    # 没给 --data 时自动找全量对话：三批合并过的 dialogs_value.json 优先，
    # 否则退回子渝批的 dialogs_W.json（第 12、13 项要靠它查原文）
    if not data or not os.path.isfile(data):
        for _p in ("02_过程文件/dialogs_value.json", "02_过程文件/dialogs_W.json"):
            _c = os.path.join(root, _p)
            if os.path.isfile(_c):
                data = _c
                break

    print("自检：%s\n" % src)

    # 1 板块顺序
    print("[1] 板块结构")
    sec_ids = re.findall(r'<section class="sec[^"]*" id="([\w-]+)"', h)
    pos = [h.find('id="%s"' % s) for s in ORDER]
    is_topic = any(p < 0 for p in pos) and len(sec_ids) >= 3
    if is_topic:
        ok("专项页（%d 个 section，非五板块结构），跳过板块顺序检查" % len(sec_ids))
    elif any(p < 0 for p in pos):
        miss = [LABEL[ORDER[i]] for i, p in enumerate(pos) if p < 0]
        fail("缺板块：%s" % "、".join(miss))
    elif pos != sorted(pos):
        fail("板块顺序被打乱，正确顺序：%s" % " → ".join(LABEL[s] for s in ORDER))
    else:
        ok("五板块齐全，顺序正确")

    # 2 导航
    print("[2] 顶栏导航")
    navs = re.findall(r'<nav[^>]*>(.*?)</nav>', h, re.S)
    if not navs:
        fail("找不到 <nav> 顶栏")
    else:
        hrefs = re.findall(r'href="#([\w-]+)"', navs[0])
        if not hrefs:
            fail("顶栏没有锚点链接")
        elif [x for x in hrefs if 'id="%s"' % x not in h]:
            fail("导航指向不存在的锚点：%s" % [x for x in hrefs if 'id="%s"' % x not in h])
        elif not is_topic and len(hrefs) != 5:
            fail("导航有 %d 个链接，应为 5 个" % len(hrefs))
        else:
            ok("%d 个导航链接全部命中页面里的 section" % len(hrefs))

    # 3 图片存在
    print("[3] 图片文件")
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', h)
    ext = [s for s in imgs if not s.startswith(("http://", "https://", "data:"))]
    lost = []
    for s in ext:
        p = os.path.normpath(os.path.join(root, s.split("?")[0]))
        if not os.path.isfile(p):
            lost.append(s)
    if not imgs:
        fail("一张图都没有 —— 报告主体就是截图，没有图等于没做完")
    elif lost:
        fail("%d 张图找不到文件（会显示裂图）：%s%s"
             % (len(lost), "、".join(lost[:6]), " …" if len(lost) > 6 else ""))
    else:
        ok("%d 张图全部存在" % len(ext))

    # 4 data-zoom
    print("[4] 点击放大")
    n_zoom = len(re.findall(r'data-zoom=', h))
    expect = len(re.findall(r'<img[^>]+src="assets/(?:prob|stage|good)/', h))
    if expect and n_zoom < expect:
        fail("案例图 %d 张，data-zoom 只有 %d 个，点击放大不生效" % (expect, n_zoom))
    elif expect:
        ok("案例图 %d 张，data-zoom %d 个" % (expect, n_zoom))
    else:
        fail("没有 assets/prob|stage|good 下的案例图，图类目录可能放错位置")

    # 5 占位符残留
    print("[5] 占位符残留")
    left = []
    for pat, name in ((r"【填", "【填…】"), (r"\{\{", "{{…}}"),
                      (r"\bTODO\b", "TODO"), (r"\bXXX\b", "XXX")):
        for m in re.finditer(pat, h):
            left.append("%s@%d" % (name, h[:m.start()].count("\n") + 1))
    if left:
        fail("还有 %d 处没填：%s" % (len(left), "、".join(left[:8])))
    else:
        ok("无残留占位符")

    # 6/7 版式文件一致
    print("[6] style.css")
    css_src = os.path.join(root, "assets", "style.css")
    css_kit = os.path.join(KIT, "assets", "style.css")
    if not os.path.isfile(css_src):
        fail("产物里没有 assets/style.css")
    elif md5(css_src) != md5(css_kit):
        fail("assets/style.css 与模板库不一致（被改过，版式必跑偏）—— 从 _report-kit/assets/ 原样覆盖")
    else:
        ok("与模板库逐字节一致")

    print("[7] app.js")
    js_src = os.path.join(root, "assets", "app.js")
    js_kit = os.path.join(KIT, "assets", "app.js")
    if not os.path.isfile(js_src):
        fail("产物里没有 assets/app.js（灯箱、折叠、进度条全失效）")
    elif md5(js_src) != md5(js_kit):
        fail("assets/app.js 与模板库不一致 —— 从 _report-kit/assets/ 原样覆盖")
    else:
        ok("与模板库逐字节一致")

    # 8 版本号
    print("[8] 资源版本号")
    vc = re.search(r'style\.css\?v=([\w.]+)', h)
    vj = re.search(r'app\.js\?v=([\w.]+)', h)
    if not vc or not vj:
        fail("缺少 ?v= 版本号，改完 CSS 用户会看到旧样式")
    elif vc.group(1) != vj.group(1):
        fail("style.css?v=%s 与 app.js?v=%s 不一致" % (vc.group(1), vj.group(1)))
    else:
        ok("版本号统一为 v=%s" % vc.group(1))

    # 9 class 覆盖
    print("[9] class 覆盖")
    if os.path.isfile(css_src):
        css = open(css_src, encoding="utf-8").read()
        used = set()
        for attr in re.findall(r'class="([^"]+)"', h):
            used.update(attr.split())
        unknown = sorted(c for c in used
                         if c and c not in ALLOW and not re.search(
                             r"\.%s(?![-\w])" % re.escape(c), css))
        if unknown:
            fail("%d 个 class 在 style.css 里没有定义（自己造了样式）：%s"
                 % (len(unknown), "、".join(unknown[:10])))
        else:
            ok("%d 个 class 全部有定义" % len(used))

    # 10 引语可核对
    print("[10] 引语可核对")
    if no_quotes:
        print("  - 已跳过（--no-quotes）")
    else:
        try:
            import check_quotes
            nq, errs, ncard = check_quotes.check(src, data)
            if errs:
                fail("%d 处引语在对应截图上找不到（正文说了客户回什么，图上没有）" % len(errs))
                for e in errs[:8]:
                    print("      %s" % e)
                if len(errs) > 8:
                    print("      … 另有 %d 处，跑 check_quotes.py 看全量" % (len(errs) - 8))
            elif nq == 0:
                fail("一张卡片都没核到引语 —— 检查 .case / .qcard / .rcase 结构")
            else:
                ok("%d 张卡片 / %d 处引语，全部能在对应截图里找到" % (ncard, nq))
        except Exception as e:
            fail("引语核对跑不起来：%s" % e)

    # 11 顶部概要条
    print("[11] 顶部概要条")
    mp = re.search(r'<div class="prov">(.*?)</div>\s*</div>', h, re.S)
    prov = mp.group(1) if mp else ""
    if not prov:
        fail("没有顶部概况条 .prov —— 交付物必须在最顶部写明 数据 / 依据 / 判别明细 / 流水线")
    else:
        need = ["数据", "依据"]
        miss = [k for k in need if k not in prov]
        links = re.findall(r'href="((?!#|https?://)[^"]+)"', prov)
        lost = [l for l in links
                if not os.path.exists(os.path.join(root, l.split("?")[0]))]
        if miss:
            fail("概要条缺段：%s（固定三段：标题 ｜ 数据 ｜ 依据，另加底稿链接）"
                 % "、".join(miss))
        elif len(links) < 2:
            fail("概要条底稿链接只有 %d 个（至少要有 数据说明 + 原始导出 两处）" % len(links))
        elif lost:
            fail("概要条指向的路径不存在（链接是假的）：%s" % "、".join(lost[:5]))
        else:
            ok("数据 / 依据齐全，%d 个底稿链接全部命中" % len(links))

    # 12 引号外的编造
    print("[12] 引号外的断言")
    try:
        import audit_claims
        hard, soft, ncard2, _ = audit_claims.audit(src, data)
        if hard:
            fail("%d 处引号外的具体信息在原文里查不到（编造风险）" % len(hard))
            for e in hard[:8]:
                print("      %s" % e)
            if len(hard) > 8:
                print("      … 另有 %d 处，跑 audit_claims.py 看全量" % (len(hard) - 8))
        elif soft:
            ok("金额 / 日期 / 时间 / 外文词全部有出处（另有 %d 处括号补语待人工确认）" % len(soft))
            for e in soft[:5]:
                print("      ? %s" % e)
        else:
            ok("金额 / 日期 / 时间 / 外文词全部有出处，括号补语也有出处")
    except Exception as e:
        fail("断言核查跑不起来：%s" % e)

    # 13 片段库漏斗
    print("[13] 片段库漏斗")
    try:
        import audit_good
        import io as _io
        import contextlib
        buf = _io.StringIO()
        _argv = sys.argv
        sys.argv = [sys.argv[0], src] + (["--data", data] if data else [])
        try:
            with contextlib.redirect_stdout(buf):
                rc = audit_good.main()
        finally:
            sys.argv = _argv
        out = buf.getvalue()
        head = [l for l in out.splitlines() if l.startswith("  ①") or l.startswith("  ②")
                or l.startswith("  ③")]
        if rc != 0:
            fail("片段漏斗与口径对不上（数字是估的或标签写错了）")
            for l in out.splitlines():
                if l.strip().startswith("-"):
                    print("      %s" % l.strip())
        else:
            _nums = []
            for _l in head:
                _m = re.match(r"\s*([①②③])\s*([^\d]*?)(\d+)", _l)
                if _m:
                    _nums.append("%s%s" % (_m.group(1), _m.group(3)))
            ok("%s 可复算，六段客户全部在数据里" % " → ".join(_nums) if _nums
               else "四个数字可复算，六段客户全部在数据里")
            for l in head:
                print("      %s" % l.strip())
    except Exception as e:
        fail("片段核查跑不起来：%s" % e)

    # 14 CRM 标识与意向级别
    print("[14] CRM 标识与意向级别")
    cids = re.findall(r'<span class="cid([^"]*)"([^>]*)>([^<]*)</span>', h)
    lvls = re.findall(r'<span class="lvl([^"]*)"([^>]*)>([^<]*)</span>', h)
    if not cids and not lvls:
        ok("本报告没有 CRM 标识（案例头未接线索表），跳过")
    else:
        bad14 = []
        filled = [c for c in cids if "none" not in c[0]]
        for cls, attr, txt in cids:
            if not txt.strip():
                bad14.append("有 .cid 是空的")
            if "none" not in cls and "title=" not in attr:
                bad14.append("ID %s 没有 title，读者核不到这条从哪来" % txt.strip())
        # 意向级别标签：data-lv 必须与文字首字母一致，且必须紧跟在 .cid 后面
        for cls, attr, txt in lvls:
            m_lv = re.search(r'data-lv="([^"]*)"', attr)
            txt = txt.strip()
            if not m_lv:
                bad14.append("意向标签「%s」没有 data-lv，颜色会退成默认" % txt)
            elif txt and not txt.startswith(m_lv.group(1)):
                bad14.append("意向标签写的是「%s」，data-lv 却是 %s" % (txt, m_lv.group(1)))
        glued = len(re.findall(r'<span class="cid[^"]*"[^>]*>[^<]*</span><span class="lvl"', h))
        if lvls and glued < len(lvls):
            bad14.append("%d 个意向标签没跟在 .cid 后面（应紧邻客户名那行）"
                         % (len(lvls) - glued))
        # 有对照表就核一遍：页面上每个 ID 都要能在表里查到
        cmap = os.path.join(root, "02_过程文件", "crm_map.csv")
        if not os.path.exists(cmap):
            cmap = os.path.join(root, "crm_map.csv")
        if os.path.exists(cmap) and filled:
            txt_csv = open(cmap, encoding="utf-8-sig").read()
            lost = [t.strip() for _, _, t in filled if t.strip() not in txt_csv]
            if lost:
                bad14.append("%d 个 ID 在 crm_map.csv 里查不到：%s"
                             % (len(lost), "、".join(lost[:5])))
        left = h.count("无 CRM ID")
        if bad14:
            fail("CRM 标识 %d 处问题" % len(bad14))
            for e in bad14[:8]:
                print("      %s" % e)
        else:
            ok("%d 处已回填 ID（%d 处意向级别），仍有 %d 处「无 CRM ID」"
               % (len(filled), len(lvls), left))

    # 15 图片放大：点了能开、能滚轮缩放、能拖动
    print("[15] 图片放大结构")
    body_imgs = [t for t in re.findall(r'<img\b[^>]*>', h) if 'id="lbImg"' not in t]
    zooms = len(re.findall(r'data-zoom=', h))
    bad15 = []
    if body_imgs and not zooms:
        bad15.append("正文 %d 张图没有一处 data-zoom——点了不会有任何反应" % len(body_imgs))
    if zooms:
        for need, why in (('id="lb"', "灯箱容器"), ('id="lbImg"', "灯箱图片"),
                          ('id="lbCap"', "底部图注")):
            if need not in h:
                bad15.append("有 data-zoom 但缺 %s（%s），app.js 取不到节点，整套缩放失效" % (need, why))
        if 'app.js' not in h:
            bad15.append("有 data-zoom 但没引 app.js，点了没反应")
        else:
            js_path = os.path.join(root, "assets", "app.js")
            if not os.path.exists(js_path):
                bad15.append("找不到 assets/app.js")
            else:
                js = open(js_path, encoding="utf-8").read()
                for kw, tip in (("'wheel'", "滚轮缩放"), ("pointerdown", "鼠标拖动"),
                                ("zoomAt", "缩放函数"), ("data-zoom", "点击绑定")):
                    if kw not in js:
                        bad15.append("app.js 里找不到 %s，%s会失效" % (kw, tip))
        if len(body_imgs) != zooms:
            bad15.append("正文图 %d 张，data-zoom 只有 %d 处——有图点不开"
                         % (len(body_imgs), zooms))
    if bad15:
        fail("图片放大链路有 %d 处问题" % len(bad15))
        for e in bad15[:6]:
            print("      %s" % e)
    elif zooms:
        ok("%d 张图都能点开，灯箱节点齐，滚轮缩放与拖动都在" % zooms)
    else:
        ok("本页没有图片，跳过")

    print("\n" + "=" * 46)
    if bad:
        print("✗ %d 项未通过，逐条改完再交付" % len(bad))
        return 1
    print("✓ %d 项全部通过，可以交付" % ok_n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
