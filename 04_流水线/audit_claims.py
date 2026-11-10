# -*- coding: utf-8 -*-
"""断言核查器 —— 抓「引号外的编造」。

用法：
    python audit_claims.py ../web-report/index.html --data dialogs_all.json

为什么需要它
────────────
2026-11-09 出过第二次同类事故：片段六里写「他说清了它不擅长什么（运动科学这块
讲得相对浅一点）」。这句没有引号，`check_quotes.py` 只核「」，所以一路绿灯放过去。
可完达山那组 113 条消息里从没出现过「运动科学」——那句话是从行业常识补出来的。

**带引号的错是抄错，不带引号的错是编造。** 后者更危险，因为它读起来像事实。

查什么
──────
  硬项（✗，拦交付）
    1 日期    11.2 / 10月27日   → 本组时间轴里有没有这一天
    2 时间点  09:34              → 本组时间轴里有没有这一分钟
    3 金额    19300 / 28700 …    → 本组原文里有没有这串数字
    4 外文词  NASM / ACE-APT …   → 全盘原文或客户名里有没有
  提示（?，人工看一眼）
    5 全库零重合句：整句的二字词在全盘 48 组原文里一个都找不到

不查的：条数/组数/字数/分钟这类派生统计（「回了三个字」「聊了 4 次」），
它们是算出来的，不是抄出来的；派生统计另有算法核对（见 00_数据来源说明.md）。

退出码：0 = 没有硬错；1 = 有硬错。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_quotes as CQ

# 版式里的固定字样，不是正文断言，先剔掉
BOILER = ("无 CRM ID", "体德智训-子渝（广州南京长沙）", "体德智训-子渝",
          "点开看完整对话", "点击图片可放大查看完整对话", "原文截图，点击放大",
          "点击放大", "发生了什么", "做了哪几件事", "为什么有效",
          "可以直接抄走的原话", "判定口径", "→", "片段一", "片段二", "片段三",
          "片段四", "片段五", "片段六", "案例")
# 量词：这些数字是派生统计，不做字符串级核对
UNIT = ("组", "类", "段", "张", "位", "人", "条", "次", "字", "分钟", "小时",
        "天", "秒", "倍", "成", "分", "岁", "点", "节")

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
CLOCK = re.compile(r"(\d{1,2})\s*[:：]\s*(\d{2})")
DATE = re.compile(r"(\d{1,2})\s*[.．月]\s*(\d{1,2})")
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9\-]{1,}")
UNIT_AFTER = re.compile(r"\s*(?:%s)" % "|".join(UNIT))
# 章节引用（P1…P6、PART 02）不是外文词
SECTION = re.compile(r"\b(?:P[1-6]|PART\s*\d+)\b")
# 「降了 3200」这类差额：句子里有这些词就不核该数字
DERIVED = ("降了", "降", "差", "省", "涨", "便宜", "少了", "多了")
# 「整组 90 条里一次都没」这类反面引用：数字本来就该查不到
ABSENT = ("一次都没", "一条都没", "没有提", "没提过", "从未", "查不到", "零")
CJK = re.compile(r"[\u4e00-\u9fa5]")
# 议论性补语（不是事实）：出现这些词就不核
EDIT = ("说明", "意味着", "其实", "就是", "才是", "不是", "而是", "知道", "需要",
        "应该", "值得", "证明", "在脑子里", "这一类", "换句话说", "可见")
# 括号（中英文）与破折号后的补充语
EXTRACT = re.compile(r"[（(]([^（()）]{4,60})[)）]|——([^。；]{4,60})")
# 分析/议论句的标记词：句子里有这些，就当论述不当事实，不做用词覆盖检查
SOFT_SKIP = ("说明", "意味着", "本质", "问题在", "原因是", "值得", "应该", "需要",
             "建议", "关键", "核心", "真正", "其实", "换句话说", "反过来说", "可见",
             "判断", "口径", "统计", "全盘", "整体", "这批", "并不缺", "抄走",
             "结论", "逻辑", "套路", "话术", "漏斗", "闭环", "为什么有效",
             "做了哪几件事", "可以直接抄走")
# 引述动词：只有讲到「谁说了什么」的句子才做用词覆盖检查
SAY = ("说", "问", "答", "回", "讲", "提", "发", "喊", "拒绝", "同意",
       "沉默", "没回", "提到", "表示", "承认", "反问", "复述", "补充")


# 统计用词覆盖时先剔掉的高频虚词/角色词：「客户」「销售」这类词在原文里本来就不出现
STOP = set("客户销售他她它的了是在和就都也又才还会要没有这不个次条组句字们我你您啊呀吧呢吗哦嗯"
           "时候之后然后而已经马上直接立刻当场一上下中对于把被给跟向从以因为所以但并且如果"
           "说问答回讲提发到过得地着过来去做好多想让请再又更最比较非常")


def grams(s, n=2):
    s = "".join(c for c in CQ.norm(s) if c not in STOP and CJK.match(c))
    return [s[i:i + n] for i in range(len(s) - n + 1)]


# 卡片里这些是标签/元信息，不是正文断言，取文本时整块跳过
SKIP_CLASS = {"case-meta", "qcard-meta", "qcard-no", "cid", "qlabel",
              "qshot-cap", "tbl-note", "qcount", "pmeta"}


class ClaimSplit(CQ.CardSplit):
    """在 CardSplit 基础上跳过标签/元信息，只留正文。"""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = set((a.get("class") or "").split())
        super().handle_starttag(tag, attrs)
        if tag not in CQ.VOID and cls & SKIP_CLASS:
            self.skip.append(self.depth)


def clean(text):
    for b in BOILER:
        text = text.replace(b, " ")
    return text


def split_sentences(text):
    return [p.strip() for p in re.split(r"[。！？；\n]", text)
            if len(CQ.norm(clean(p))) >= 6]


def timeline(group):
    clock, date = set(), set()
    for m in group["msgs"]:
        mm = re.search(r"(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})", m["t"])
        if mm:
            date.add("%d.%d" % (int(mm.group(1)), int(mm.group(2))))
            clock.add("%02d:%s" % (int(mm.group(3)), mm.group(4)))
    return clock, date


def audit(html_path, data_path=None):
    html_path = os.path.abspath(html_path)
    root = os.path.dirname(html_path)
    h = open(html_path, encoding="utf-8").read()
    P = ClaimSplit()
    P.feed(h)

    data_path = CQ.find_data(root, data_path)
    if not data_path:
        raise RuntimeError("找不到全量对话 json（dialogs_all.json），"
                           "请用 --data 指定，例如 "
                           "--data 02_过程文件/dialogs_W.json")
    groups, all_text, names = {}, "", set()
    for g in json.load(open(data_path, encoding="utf-8")):
        groups[g["cust"]] = g
        names.update(x.upper() for x in LATIN.findall(g["cust"]))
        all_text += "".join(m["x"] for m in g["msgs"])
    all_norm = CQ.norm(all_text)
    all_latin = " ".join(LATIN.findall(all_text)).upper() + " " + " ".join(names)
    known = len({"%d.%d" % (int(a), int(b))
                 for g in groups.values() for a, b in
                 [re.search(r"(\d{1,2})月(\d{1,2})日", m["t"]).groups()
                  for m in g["msgs"] if re.search(r"\d{1,2}月\d{1,2}日", m["t"])]})

    hard, soft = [], []
    deepest = [r for r in P.cards if not r["kids"]]
    for idx, rec in enumerate(deepest, 1):
        text, imgs = CQ.flatten(rec)
        cust = None
        for src in imgs:
            man = CQ.load_manifest(os.path.normpath(os.path.join(root, src.split("?")[0])))
            if man and man.get("cust"):
                cust = man["cust"]
                break
        if not cust or cust not in groups:
            continue
        g = groups[cust]
        corpus = CQ.norm("".join(m["x"] for m in g["msgs"]))
        # 原文（不去标点）：班期这类日期只出现在消息正文里，不在时间轴上
        rawtext = "".join(m["x"] for m in g["msgs"])
        clock, date = timeline(g)
        head = "%s#%d（%s）" % (CQ.LABEL.get(rec["cls"], rec["cls"]), idx, cust)

        for sent in split_sentences(text):
            bare = CQ.QUOTE.sub("", clean(sent))
            if not CQ.norm(bare):
                continue
            tag = "%s %s" % (head, sent[:48].replace("\n", " "))
            editor = any(w in bare for w in SOFT_SKIP)

            # 日期 / 时间点先摘出来单独核，避免被当成金额
            for a, b in DATE.findall(bare):
                key = "%d.%d" % (int(a), int(b))
                if key in date:
                    continue
                # 不在时间轴上，但正文里说过（如「12.9 号开首班」）也算有出处
                if key in rawtext or ("%d月%d" % (int(a), int(b))) in rawtext:
                    continue
                hard.append("日期 %s.%s 本组时间轴和正文里都没有（本组有 %s）｜ %s"
                            % (a, b, "、".join(sorted(date)[:5]), tag))
            bare2 = DATE.sub(" ", bare)
            for hh, mm in CLOCK.findall(bare2):
                if "%02d:%s" % (int(hh), mm) not in clock:
                    hard.append("时间点 %02d:%s 不在本组时间轴（本组有 %s）｜ %s"
                                % (int(hh), mm, "、".join(sorted(clock)[:5]), tag))
            bare2 = CLOCK.sub(" ", bare2)

            # 金额
            derived = any(w in bare2 for w in DERIVED)
            absent = any(w in bare2 for w in ABSENT)
            for num in NUM.findall(bare2):
                raw = num.replace(",", "")
                if len(raw.replace(".", "")) < 3:
                    continue
                tail = bare2[bare2.find(num) + len(num):]
                if UNIT_AFTER.match(tail):
                    continue
                if raw in corpus or derived or absent:
                    continue
                if raw in all_norm:
                    hard.append("金额 %s 在本组原文没有（全盘别组才有）｜ %s" % (raw, tag))
                else:
                    hard.append("金额 %s 全盘原文都查不到 → 像编的 ｜ %s" % (raw, tag))

            # 外文词
            for w in sorted(set(LATIN.findall(SECTION.sub(" ", bare2)))):
                if w.upper() not in all_latin:
                    hard.append("外文词 %s 全盘原文和客户名里都没有 ｜ %s" % (w, tag))

            # 括号与破折号后的补充：这些位置放的都是具体信息（原话、数字、条件、定义）
            # 是本报告出过事故的地方——「（运动科学这块讲得相对浅一点）」原文里根本没有
            for e1, e2 in EXTRACT.findall(bare2):
                ext = (e1 or e2).strip()
                is_par = bool(e1)
                if len(CQ.norm(ext)) < 4:
                    continue
                # 纯议论/纯章节引用/客户名：不核
                if any(w in ext for w in EDIT) or SECTION.search(ext):
                    continue
                if CQ.norm(ext) in {CQ.norm(n) for n in groups}:
                    continue
                # 客户名清单（「逐字与另外 5 组相同（R、Terry…）」）不是事实断言
                ex_core = "".join(c for c in ext if CJK.match(c))
                if sum(1 for n in groups
                       if len("".join(c for c in n if CJK.match(c))) >= 2
                       and "".join(c for c in n if CJK.match(c)) in ex_core) >= 2:
                    continue
                # 方法说明、派生时长、章节引用
                if any(w in ext for w in ("按规则", "见 ", "算起", "分钟后", "天后", "小时后")):
                    continue
                # 破折号后面多半是作者的解释，只有写了具体信息（数字/外文/时间）才核
                if not is_par and not (NUM.search(ext) or LATIN.search(ext) or CLOCK.search(ext)):
                    continue
                gs = [x for x in grams(ext) if CJK.search(x)]
                if not gs:
                    continue
                # 括号里说的是「这一组」的细节，只能用这一组的原文核，不能拿别组兜底
                hit = sum(1 for x in gs if x in corpus)
                cov = hit / len(gs)
                if cov < 0.34:
                    lost = [x for x in dict.fromkeys(gs) if x not in corpus][:6]
                    soft.append("括号/补语只有 %2d%% 能在原文找到（查不到：%s）｜ %s ｜ 补语原文：%s"
                                % (round(cov * 100), "、".join(lost) or "—", tag, ext[:44]))

    return hard, soft, len(deepest), known


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("-")]
    data = None
    for i, x in enumerate(sys.argv):
        if x == "--data" and i + 1 < len(sys.argv):
            data = sys.argv[i + 1]
            if data in args:
                args.remove(data)
    if not args:
        print(__doc__)
        return 2
    hard, soft, ncard, known = audit(args[0], data)
    print("核查 %d 张卡片（全盘 %d 个日期）" % (ncard, known))
    for e in hard:
        print("  ✗ %s" % e)
    for e in soft:
        print("  ? %s" % e)
    print("\n✗ 硬错 %d 处 ｜ ? 待确认 %d 处" % (len(hard), len(soft)))
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
