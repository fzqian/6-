# -*- coding: utf-8 -*-
"""给「重点四组」出截图（并入总盘后，这四张卡一样要能逐字寻源）。

数据：02_过程文件/dialogs_focus.json
输出：assets/value/fz1.png ~ fz4.png + 同名 .json 侧写

为什么单独一个脚本：shot.py 一次只能出一张图，四组共 12 段，手敲命令容易错位；
这里把「哪张卡配哪几段」写成表，重跑一次就同步。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"C:/Users/admin/Desktop/体德报告_子渝六阶段质检"
PIPE = os.path.join(ROOT, "04_流水线")
DATA = os.path.join(ROOT, "02_过程文件", "dialogs_focus.json")
OUT = os.path.join(ROOT, "assets", "value")

# (id, 会话里的客户名, [(起始, 结束), ...], 图注)
JOBS = [
    ("fz1", "姜彦博",
     [("做教练", "了解一下基础"),
      ("都可以，看就业怎么样", "持有的证书、体型去推荐的"),
      ("弟弟大学学滴啥专业呀", "弟弟之前带过人练啵"),
      ("对啦还有一个板块没讲", "招生老师每年都会跟进自己的学生"),
      ("哈喽哈喽下午好呀弟弟", "咱们了解行业不能只看好的一面嘛")],
     "三件套一句话讲全 + 就业时间线 + 落点接住「看就业怎么样」"),

    ("fz2", "王永正  转介10.22",
     [("我是体德从业健身8年", "你看要不要了解一下哈"),
      ("嗨咯同学，跨年班优惠活动出来啦", "嗨咯同学，跨年班优惠活动出来啦")],
     "客户只问「包分配不」，回了 15 条出口；19 天后补发的还是优惠"),

    ("fz3", "UIN",
     [("费用多少呀", "这个是不同证书对应的学费"),
      ("学完以后呢", "没就业上呢"),
      ("178 110斤", "跟着老师安排的训练和饮食计划"),
      ("吃住呢", "一日三餐都会需要打卡")],
     "「学完以后呢」问了三次，得到五个字；落点靠「太瘦」「惠州」救回来"),

    ("fz4", "銀河",
     [("介绍一下价格吧", "咱们是考虑提升自己还是有做教练的打算哈"),
      ("我就先咨询一下", "来不来学都没关系，做个了解可以对比对比哈"),
      ("发给咱们的课程内容有看不", "给咱们发送一些资料，可以了解一下"),
      ("哈喽，同学，跨年活动出来啦", "哈喽，同学，跨年活动出来啦")],
     "形态讲到全批最标准的一段；出口 0、落点 0，51 天客户只说了 5 句"),
]


def main():
    rc = 0
    for sid, cust, segs, note in JOBS:
        cmd = [sys.executable, os.path.join(PIPE, "shot.py"),
               "--data", DATA, "--cust", cust,
               "--id", sid, "--note", note, "--out", OUT]
        for a, b in segs:
            cmd += ["--seg", "%s|%s" % (a, b)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        flag = "OK " if r.returncode == 0 else "FAIL"
        if r.returncode != 0:
            rc = 1
        print("%s %-4s %s" % (flag, sid, out.splitlines()[-1] if out else ""))
        if r.returncode != 0:
            print(out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
