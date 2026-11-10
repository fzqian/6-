# -*- coding: utf-8 -*-
"""为陈舒批的 6 张卡片生成微信截图（并入主池后，卡片一律要能寻源）。

数据：02_过程文件/dialogs_cs.json
输出：assets/value/csN.png + csN.json
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"C:/Users/admin/Desktop/体德报告_子渝六阶段质检"
PIPE = os.path.join(ROOT, "04_流水线")
DATA = os.path.join(ROOT, "02_过程文件", "dialogs_cs.json")
OUT = os.path.join(ROOT, "assets", "value")

JOBS = [
    ("cs2", "🐈",
     [("我在健身房上班", "宁波那边是新一线诶，好单位基本上都要求国际认证啦"),
      ("20600，三个月线下集训", "20600，三个月线下集训")],
     "客户说在健身房上班 → 证书落到「宁波这个城市」+ 报价句里带全三件套"),
    ("cs3", "巨巨",
     [("这份工作可能年底辞职", "我最快也得12月才辞职")],
     "客户「最快也得12月才辞职」→ 直接排 12.9 首班，不劝提前"),
    ("cs4", "千秋",
     [("都说好就业", "老辈子说嘛")],
     "客户替你把出口问出来了，回的是三个字的民俗"),
    ("cs5", "如意吉祥",
     [("南京的位置发给我。", "我没事儿过去看看今日。"),
      ("咱们是理论跟实操并线推进滴", "一共能拿八个证书，6个体德官方认证➕一个cpr证书（让教练证书生效）➕咱选择的教练证")],
     "客户要位置/环境/饮食/收费，只讲了「三个月四个阶段」——九个月与复训没出现"),
    ("cs6", "小马",
     [("你们的培训费是多少啊", "多少钱啊，每个证"),
      ("咱心理预期最好是放在3-6000", "")],
     "六连问一件件答完，产品是什么一个字没讲"),
]


def main():
    for sid, cust, segs, note in JOBS:
        cmd = [sys.executable, os.path.join(PIPE, "shot.py"),
               "--data", DATA, "--cust", cust,
               "--id", sid, "--note", note, "--out", OUT]
        for a, b in segs:
            cmd += ["--seg", "%s|%s" % (a, b)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        out = (r.stdout or "") + (r.stderr or "")
        flag = "OK " if r.returncode == 0 else "FAIL"
        print("%s %-4s %-6s %s" % (flag, sid, cust, out.strip().splitlines()[-3:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
