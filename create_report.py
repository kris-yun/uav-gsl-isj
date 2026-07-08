import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

# Set default font
style = doc.styles['Normal']
font = style.font
font.name = '宋体'
font.size = Pt(12)

# Title
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('论文进展汇报')
run.font.size = Pt(22)
run.font.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('面向低风速室内环境的无人机气体源定位研究')
run.font.size = Pt(14)
run.font.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('2026年7月9日')
run.font.size = Pt(12)

doc.add_paragraph()

# Section 1
doc.add_heading('一、我做的是什么？', level=1)
doc.add_paragraph(
    '简单说：用无人机在室内找气体泄漏源在哪。'
)
doc.add_paragraph(
    '场景是这样的——工厂或灾后室内有毒气体泄漏了，我们需要派一架无人机进去，'
    '带着气体传感器和风速计，自动找到气体是从哪里泄漏出来的。'
)
doc.add_paragraph(
    '这个问题的难点在于：室内风速很低（不到0.1米/秒），气体不是均匀扩散的，'
    '而是一团一团地飘过来（叫"丝状体"），传感器经常检测不到气体，偶尔突然检测到一下。'
    '就像你在大雾天找一个喷烟的烟囱，但烟是断断续续的，你经常看不到烟。'
)

# Section 2
doc.add_heading('二、现有方法有什么问题？', level=1)
doc.add_paragraph(
    '现在主流的三种方法都有硬伤：'
)
p = doc.add_paragraph('1. SurgeCast（2025年RA-L）：', style='List Bullet')
p.add_run('顺着风往回找。问题：一旦丢了气体信号就迷路，成功率只有30%。')
p = doc.add_paragraph('2. GrGSL（2025年RA-L）：', style='List Bullet')
p.add_run('用高斯回归建浓度地图。问题：假设气体是均匀扩散的，但实际是一团一团的，模型不对。')
p = doc.add_paragraph('3. PMFS（2023年TRO）：', style='List Bullet')
p.add_run('用粒子模拟扩散。问题：需要风场数据，但室内风速太低测不准，直接失效（成功率0%）。')

doc.add_paragraph(
    '总结：现有方法有两个根本问题——①用的数学模型跟实际气体扩散不匹配（模型误设），'
    '②不知道什么时候该停（没有停止准则）。'
)

# Section 3
doc.add_heading('三、我用什么方法解决？', level=1)
doc.add_paragraph(
    '我的方法叫"鲁棒估计-决策协同框架"，名字听着复杂，其实就是两件事一起干：'
)

doc.add_heading('创新点1：用"宽容的"贝叶斯推理替代"死板的"贝叶斯推理', level=2)
doc.add_paragraph(
    '打个比方：标准贝叶斯推理就像一个特别较真的人，模型说气体应该这样分布，'
    '实际不是，它就推导出错误结论还很自信。'
    '我用的GBI（广义贝叶斯推理）就像一个"知道自己的模型不完美"的人，'
    '会根据风场是否稳定来决定"这次观测值不值得信任"：'
)
p = doc.add_paragraph('• 检测到气体 + 风向稳定 → 高信任（η=0.6~0.9，强更新）', style='List Bullet')
p = doc.add_paragraph('• 没检测到气体 + 风向混乱 → 低信任（η=0.15~0.5，弱更新）', style='List Bullet')
doc.add_paragraph(
    '这个"信任度"不是我拍脑袋调的参数，而是由风场置信度自动计算的。'
    '论文里证明了这样做后验会以指数速度收敛到正确位置。'
)

doc.add_heading('创新点2：知道什么时候该停', level=2)
doc.add_paragraph(
    '以前的方法不知道什么时候该停——跑够300秒就停，或者靠经验。'
    '我设计了两个"裁判"同时监督：'
)
p = doc.add_paragraph('• 裁判1（e-process）：数学上保证，如果我说"找到了"，出错概率不超过5%。', style='List Bullet')
p = doc.add_paragraph('• 裁判2（DDM）：像大脑做决定一样，证据积累够了就停。', style='List Bullet')
doc.add_paragraph('两个裁判任意一个说"可以停了"就停，保证又快又准。')

doc.add_heading('创新点3：更好的气体检测模型', level=2)
doc.add_paragraph(
    '以前用指数衰减模型（离源越远检测概率指数下降），但实际室内气体是"近距离容易检测、'
    '远距离很难检测、中间有个陡变"的S形。我用logistic函数建模，更符合实际。'
)

doc.add_heading('创新点4：无人机自动选高度', level=2)
doc.add_paragraph(
    '气体源可能在地面也可能在空中。地面机器人只能在地面找，找空中源就废了。'
    '无人机可以飞，我用高斯过程模型自动学习"哪个高度气体浓度高"，'
    '飞到最可能有气体的高度去采样。'
)

# Section 4
doc.add_heading('四、实验结果', level=1)
doc.add_paragraph('在GADEN仿真器上跑了4个场景，每个场景每个方法跑10次（共160次实验）：')

table = doc.add_table(rows=5, cols=3)
table.style = 'Light Grid Accent 1'
table.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ['方法', '平均误差', '成功率']
for i, h in enumerate(headers):
    table.rows[0].cells[i].text = h
data = [
    ['GBI-GSL（本文）', '1.62米', '92.5%'],
    ['SurgeCast', '2.74米', '30.0%'],
    ['GrGSL', '4.86米', '12.5%'],
    ['PMFS', '6.44米', '0.0%'],
]
for ri, row_data in enumerate(data):
    for ci, val in enumerate(row_data):
        table.rows[ri+1].cells[ci].text = val

doc.add_paragraph()
doc.add_paragraph(
    '简单说：我的方法比最好的对手误差低41%，成功率是它的3倍。'
    '特别是在"源在空中"的场景，其他方法全废（0%成功率），我还能保持90%+。'
)

# Section 5
doc.add_heading('五、论文状态', level=1)
p = doc.add_paragraph('已完成：', style='List Bullet')
p.add_run('理论框架、算法实现、160次基准实验、定理证明、论文初稿（中文8页/英文9页）')
p = doc.add_paragraph('待完成：', style='List Bullet')
p.add_run('消融实验（验证每个模块的贡献）、统计显著性检验、论文润色')
p = doc.add_paragraph('预计投稿时间：', style='List Bullet')
p.add_run('2026年8月')
p = doc.add_paragraph('目标期刊：', style='List Bullet')
p.add_run('IEEE Sensors Journal (IF ≈ 3.4)')

# Section 6
doc.add_heading('六、代码与数据', level=1)
doc.add_paragraph('• 代码仓库：https://github.com/kris-yun/cp-sbd-gsl (私有)')
doc.add_paragraph('• 实验数据：160次完整基准测试结果已保存')
doc.add_paragraph('• 仿真环境：GADEN丝状体气体扩散仿真器 + ROS2 Humble')
doc.add_paragraph('• 运行平台：本地VM (zyc@192.168.111.128)')

doc.save(r"D:\ZYC\A-gas\ASCi\论文进展汇报_20260709.docx")
print("Word报告已生成")
