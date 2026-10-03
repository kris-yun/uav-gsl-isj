from pathlib import Path
import json, shutil, hashlib, csv
import pandas as pd
ROOT=Path(r'C:\work\SVALBARD_BOREHOLE_REAL_DATA_20261003')
REPO=Path(r'C:\work\LAKESHORE_OBSERVABILITY_EXEC_20261003')
OUT=REPO/'evidence/public_data_first_20261003/van_hove'
scriptdir=REPO/'experiments/public_data_first/van_hove'
for name in ['portability_patches.json','preprocess_stdout.log','preprocess_stderr.log','inversion_stdout.log','inversion_stderr.log']:
    shutil.copy2(ROOT/'processed'/name,OUT/name)
inventory=[]
for p in sorted((ROOT/'raw/active/drone_data/remote_control').glob('*/*aircraft.csv')):
    d=pd.read_csv(p,sep=';',usecols=['CUSTOM.date [local]','CUSTOM.updateTime [local]','OSD.flyTime [s]','OSD.height [m]'],dtype=str)
    inventory.append(dict(path=str(p.relative_to(ROOT)).replace('\\','/'),records=len(d),first_local=d['CUSTOM.date [local]'].iloc[0]+' '+d['CUSTOM.updateTime [local]'].iloc[0],last_local=d['CUSTOM.date [local]'].iloc[-1]+' '+d['CUSTOM.updateTime [local]'].iloc[-1],max_relative_altitude_m=float(pd.to_numeric(d['OSD.height [m]'].str.replace(',','.')).max())))
pd.DataFrame(inventory).to_csv(OUT/'REMOTE_CONTROLLER_INVENTORY.csv',index=False)
rows=[]
for setting in ['', 'sensitivity/background205','sensitivity/background213','sensitivity/sigma030']:
    d=pd.read_csv(OUT/setting/'SOURCE_INVERSION_RESULTS.csv');d['setting']=setting.split('/')[-1] or 'base';rows.append(d)
pd.concat(rows).to_csv(OUT/'SENSITIVITY_SUMMARY.csv',index=False)
links=dict(paper_url='https://www.cambridge.org/core/journals/environmental-data-science/article/actively-inferring-methane-sources-with-drones/B9636E970B3888E7503464A41633719E',paper_doi='10.1017/eds.2026.10029',preprint_doi='10.5281/zenodo.17108543',repo_url='https://github.com/AlouetteUiO/active',commit='2aec1667f10648c4be2ccc15ab2b385ec80305b7',download_method='git clone; all tracked files (not just drone_data)',download_root=str(ROOT),publisher_checksum_available=False,checksum_note='MD5/SHA256 computed locally; no author-provided file MD5 located',publisher_article_sha256=hashlib.sha256((ROOT/'raw/publisher_article.html').read_bytes()).hexdigest())
(OUT/'DOWNLOAD_PROVENANCE.json').write_text(json.dumps(links,indent=2))
external=[]
for p in sorted((ROOT/'raw').glob('publisher_article*')):
    b=p.read_bytes();external.append(dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=len(b),md5=hashlib.md5(b).hexdigest(),sha256=hashlib.sha256(b).hexdigest()))
pd.DataFrame(external).to_csv(OUT/'EXTERNAL_SOURCE_MANIFEST.csv',index=False)
report='''# Svalbard borehole：公开现场观测资格与固定轨迹源反演审计

判定：`SVALBARD_GO_FIXED_PATH_POINT_SOURCE_WITH_LIMITATIONS`。真实 `drone_data` 可以直接用于固定轨迹源位置反演，不只是 synthetic nature run 标定。但公开论文的主动策略主结果属于合成实验，不能直接作为真实无人机盲搜索性能。

数据独立保存于 `C:\\work\\SVALBARD_BOREHOLE_REAL_DATA_20261003`。官方仓库固定在 `2aec1667f10648c4be2ccc15ab2b385ec80305b7`，95个tracked文件共115,006,114字节，其中drone_data共86,491,651字节。已下载完整代码、数据及官方论文HTML。MD5与SHA256均为本地计算，官方未提供逐文件校验值；原件未被改写。`RAW_MANIFEST.csv`覆盖仓库全部tracked文件。

## 资格与复现范围

源坐标由官方 `05_coordinate_system.py` 明确给出78.17495 N、15.9839 E。源是历史煤炭勘探钻孔的地质甲烷泄漏；现场人员钻开5个浅冰孔释放积气，因此应标为“地质气体、人工干预出气”，而不是完全未干预的天然点源。源坐标的独立测量误差未另行给出。

有4个遥控日志文件；作者选取3个连续高度/时间phase，标称2/4/6m。4个日志不等于4个独立完整重复实验。单场地、单日期，源已知后设计围绕源的lawnmower。它适用于给定观测路径的逆问题，不支持未知源自主搜索评价，也不支持将高度差与时间变化分开归因。

严格执行官方01至08步骤。只有输入路径、跳过readme.txt、pandas对整数/空值的兼容处理作了移植补丁；执行后的脚本及中间CSV在dataset的processed目录。01遥控时间Europe/Oslo→UTC；02甲烷GPS Unix秒→UTC；03 sonic按作者给定固定时移−2h18m，以pitch/roll对齐作为出处，先1s平均后精确时间合并；04完整姿态旋转并加减无人机运动速度；05投影EPSG:25833；06固定时间窗和相对起飞高度±0.2m选phase，观测z使用VPS高度；07ppm换算；08背景直方图。没有擅自估计新的CH4 sensor lag。论文标称甲烷1Hz、sonic20Hz；处理后是1s记录。

3126个phase内路径记录，2989个有CH4的完整记录，10s重采样得到314个真实观测。phase1/2/3分别81/119/114个10s观测。没有填补缺测气体，没有生成新羽流。

## 代码合同发现

官方 `nature_run/get_proposal.py` 将源固定为原点，估计Q/V/Phi，且导入当前仓库未包含的`bayesian_inference_github`模块。论文现场Q=2.2±0.6kg/h因此不能当现场未知位置定位成功。pinned nature_run配置仍有0..1000g/h的释放率先验、500000粒子，与最终论文现场量级/1000内粒子说明不完全一致。不能声称原版field PF逐位复现。

官方风预处理写`phi=(180-atan2(U,V))%360`，后续用`(x,y)=(-north,east)`，forward模型平流项`dx*cos(phi)-dy*sin(phi)`。代数合成给出east=-U、north=V。实测east反号剩余误差最大1.20e-14m/s，而east错误RMS=4.165m/s；north未变。此为源码约定不一致，不是已证实的真实气象机制。保留官方as-written输出，并单独提供向量一致计算。35个数值比较表明一致ENU形式与原作者forward类的最大差小于1e-12ppm，见`FORWARD_PARITY.json`。

## 实际执行的Bayesian STE

采用论文/源码相同的稳态Vergassola镜像浓度模型、log浓度高斯似然，条件给定风，边缘积分Q并估计水平源位置。它是“最近的published fixed-path模型”基线，不是联合估计V/Phi的作者粒子滤波。背景2.09ppm、K=1m²/s、logσ=0.15、T=273.95K、P=102000Pa。source-z=0。Q均匀0..10000g/h、81点；位置2.5m网格，范围完全由受体GPS矩形包络向四边扩展30m决定。GPS中位数为原点，真源在所有posterior完成并保存后才读入评价，`INVERSION_BEFORE_TRUTH.json`可核查。

Published nuisance参数来自同一已知源现场的标定，尤其K与误差模型不是完全独立的训练场景；本轮是透明的现场固定路径诊断，不能称为严格无任何场景先验的blind benchmark。无用定位误差挑超参数，也未用truth坐标限定候选域。

| phase | flight-mean误差m | mobile/local误差m | 有效解释 |
|---|---:|---:|---|
| 2m | 62.95 | 7.87 | 气体增强充足；局地风表征明显改善此条件模型的定位 |
| 4m | 17.01 | 6.47 | 同方向改善 |
| 全phase | 11.51 | 6.47 | 共享Q可能受实际源非稳态影响 |
| 6m | 81.12 | 215.59 | 不可辨识；不要把不可靠MAP误差当算法优劣证据 |

6m的CH4中位数2.08617ppm低于设定背景2.09ppm；local条件MAP释放率0、95%后验面积约69006m²，位置高度依赖prior/Q积分。因此本轮将6m当“源信息不足”，而不是强行解释为高层失效。95%区域是模型条件可信域，未在独立重复上校准覆盖率，不能作为实际测量不确定度保证。

单phase中height-mean与flight-mean必然相同，不能当两种独立baseline；只有合并三phase时两者不同。官方角度as-written另外报告，与真实局地向量差混杂了坐标约定，应从科学风表征主比较排除。

背景预先取2.05/2.13ppm时，2m、4m与合并phase的两主baseline MAP位置保持不变。logσ加倍至0.30时2m仍62.95→7.87m，4m17.01→8.15m，合并phase仍11.51→6.47m；可信域明显扩大。敏感性不是独立飞行复现。

## 可以与不能进入主表的终点

可以：已知路径下水平点源误差、条件后验面积、观测路径浓度支持、不同风表征的配对逆问题敏感性。必须注明源坐标精度未单独量化、source-informed route、一个site/date、phase高度和时间混杂。

不能：现场未知源自主搜索、本文RL真实飞行优越性、完整3D羽流真值、单靠这三个phase归因高度机制、同一场地三个高度当三个独立真实数据集、把作者代码frame反号当大气动力失效。

目前支持的候选科学问题是“当前观测路径的平均风与移动局地风，在实测气体固定路径反演中给出不同且可能稳定的定位偏差”。单此dataset不足以升级为跨数据集共同机制；还需独立Mackenzie测量的同方向信号。瞬时受体风不是源到受体整段传播风，本轮也未验证运输记忆或历史信息优于瞬时信息。

官方来源：[已发表论文，Sections2.4/3.1](https://doi.org/10.1017/eds.2026.10029)、[固定版本处理代码](https://github.com/AlouetteUiO/active/tree/2aec1667f10648c4be2ccc15ab2b385ec80305b7/nature_run/preprocess_drone_data)、[field calibration脚本](https://github.com/AlouetteUiO/active/blob/2aec1667f10648c4be2ccc15ab2b385ec80305b7/nature_run/get_proposal.py)。仓库LICENSE为GPL-3.0，未发现独立raw-data许可说明；文章CC BY。
'''
(OUT/'REPORT_zh.md').write_text(report,encoding='utf8')
(scriptdir/'README.md').write_text('''# Track C reproducibility
Pinned upstream: https://github.com/AlouetteUiO/active/tree/2aec1667f10648c4be2ccc15ab2b385ec80305b7
Raw clone isolated at C:/work/SVALBARD_BOREHOLE_REAL_DATA_20261003/raw/active.
Run preprocess.py, forward_parity.py, audit_and_invert.py. Then run the same inverter with --background 2.05 --sensitivity-label background205; --background 2.13 --sensitivity-label background213; --sigma 0.30 --sensitivity-label sigma030. Finally run finalize.py.
Only pyproj 3.8.0 and shapely 2.1.2 were installed into dataset-local dependencies with pip --target --no-deps. Existing Python/pandas/scipy/matplotlib/pytest environment reused; no House/VM/global environment changed.
The inference is conditional-wind Bayesian grid STE; do not call it reproduction of the missing field calibration PF. The explicit source coordinate is used only after every posterior is saved, for evaluation. Published frame discrepancy is independently checked.
''',encoding='utf8')
reports=ROOT/'reports';reports.mkdir(exist_ok=True)
shutil.copytree(OUT,reports/'audit',dirs_exist_ok=True)
shutil.copy2(OUT/'REPORT_zh.md',reports/'REPORT_zh.md')
