# M0 E0＋E1：8 条 U0 baseline 资格证据

**判决：`M0_E1_BASELINE_QUALIFIED`。** 本轮实际 U0 simulations=8、wrong-wind simulations=0、OpenFOAM=0、PMFS=0。完成后停止。E2 sentinel 和剩余 32 条 intervention 均未授权、未运行；尚无 M0_PASS/PRIMARY_GO 或 matched-error scientific verdict。

执行依据为 handoff review `dacb4dd68e16417d01c224a088e3c67c76995cd0` 中的 `M0_R0_DESIGN_REVIEW_20261007.md` 和用户本轮 E0＋E1 授权。原 R0 commit `742c80aa53fda6f47a2d0028b98f9c7dfae2de83` 的39份冻结内容未修改，旧 W0C HOLD 保留。新执行记录位于独立 `codex/m0-e0-e1-20261007`。

## E0 实际资格

- 5个 native wind assets 从冻结数学代码生成；逐个经 **实际 libgaden decoder**复读，44,236,808-byte modern数据的 SHA256 均与冻结预期逐字节相同。Free-domain和ROI的matched-RMSE、finite、speed、divergence门均通过。
- 原生 occupancy parser检查240×160×96全体cell：3,534,776 Free、151,624 Outlet；六面outer shell为Outlet，无内部obstacle；min/max坐标、0.25 m cell size和源合法性通过。Airflow disturbance初始化全零。
- Generator=`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`；libgaden=`d7fe2a08b3df6ddd3c39518f9e5ef75bd394c32509e0402b410db445cb008ee3`。关键原生源码逐项hash与R0快照相同；实际动态依赖的resolved path/bytes/SHA256另存。无原生源码或binary重编。
- 找到原生generator旧ROS参数入口的可复现绑定错误：temperature和pressure均从`wind_time_step`读取。此次通过同一generator已有的 **native project/YAML入口**设置冻结参数；native parser复核8份effective configs实际为298 K、1 atm、gas12、PointSource、10 filaments/s、σ0=10 cm、γ=15 cm²/s、noise=0.01、dt=0.1、save=0.5、wind_dt=1、loop=false、precalculate=false。原binary/source hash保持不变，未改科学参数。
- 实际argv使用`projectPath`＋`simulationID`，sim_time=140；OMP单thread，四个冻结seeds，隔离ROS_DOMAIN_ID=228；output在`/home/zyc/ros2_ws/m0_clean_support_r0_20261007/projects/U0/simulations/<frozen_run_id>/result`，每个result leaf执行前不存在。Native constructor的删除动作只作用于该不存在leaf，未重用或覆盖历史数据。
- E0仅运行native readback/parameter/noise-table审计，gas simulation=0。E0 helper与E1只读playback helper源码、build argv、binary hash分别保留。

## E1 门逐条结果

所有run严格对应frozen runlist前8行，未换源、route、seed、gas、20–120 s窗口或0.1 ppm threshold。

| U0 run | 每record最小3σ净距 / m | Pair A on mean | off mean | detectable / 51 |
|---|---:|---:|---:|---:|
| S0 r1 | 6.623 | 0.986511 | 3.82e−15 | 5 |
| S0 r2 | 7.499 | 0.966017 | 0 | 6 |
| S0 r3 | 7.041 | 0.984380 | 6.50e−17 | 5 |
| S0 r4 | 7.531 | 0.967377 | 0 | 6 |
| S1 r1 | 6.623 | 0.977723 | 6.15e−6 | 7 |
| S1 r2 | 7.499 | 0.986968 | 1.12e−8 | 10 |
| S1 r3 | 7.041 | 0.980988 | 2.42e−6 | 8 |
| S1 r4 | 7.531 | 0.986271 | 4.13e−8 | 9 |

六simulation面的1 m并集带mean/q95在主float64 CDF差分实现中均为数值0，满足0.05/0.10门。这不是“Gaussian尾部物理质量恰好等于0”的主张：独立稳定erfc复算给出window mean上界最大5.285e−69、window q95上界最大1.880e−71；全saved frames最大上界6.982e−57。见`INDEPENDENT_E1_VERIFICATION.json`。

所有1,968个native saved records的3σ最小outlet margin≥6.623 m，超过1 m门；centroid最小clearance≥10.189 m；source clearance=10.75 m，满足10 m。两源各4/4通过。Pair-A on mean最小0.966>0.30；off mean最大6.15e−6<0.01，off q95最大3.91e−5<0.05；另存逐record和halo overlap。该oracle plume检查只是固定mask的实验资格，不传入未来GSL算法。

每源4/4至少2个detectable samples，实际5–10个。U0 LORO中测试seed从**两个候选源模板**均排除，每fold只用其他3 seeds。HIT_FORWARD与LOG_GAUSSIAN各8/8正确；每源每family均4/4的p_true≥0.60，超过预设3/4门。两类likelihood采用冻结的独立点近似；这些分数只用于preflight，不支持概率校准、原生PMFS或闭环结果主张。

Native concentration parity每run 51×(25固定点＋25非零点)=2,550次，合计20,400次，absolute difference全部0。连续route读取保持冻结CSV；ROI column数据只用于冻结前向诊断，每frame另保存ppm·m数组，不替代direct support gate。

## 实际时钟、删除和RNG证书

每run 246份记录：record index 0…245，内部保存时间0…139.799332 s。评分请求20,22,…,120全部用最近不晚于请求的record，最大lag=0.501221 s≤0.61。八条output clock、record-index、wind-index序列相同，wind index全0。

Native float32 `while currentTime < 140` 实际执行1,401 ticks，最后currentTime=140.09934997558594 s。这是原生浮点步进首次越过140的终止结果；未手动extend、clamp或重写时钟，20–120评分窗原样。最后saved record后的0.300018 s尾段也纳入无删除证明。

Native release固定每tick一个filament。每个saved record的实际count等于累积release count；每record完整filament σ序列逐字节等于固定γ/dt的age递推，并遵循出生顺序；所有8条σ序列hash一致。原生log无位置/更新异常。删除数为**证书确认的0**，不是新加的逐tick counter：

1. 核对每saved record的release deficit=0；
2. 用原生seeded 1000-entry Gaussian table的实际max及wind/CO-buoyancy上界，控制所有record间隔和终止尾段；最大保守轴向位移0.2852 m，远小于snapshot支撑净距；
3. PointSource.Emit确定、不重试，六面支撑安全、无obstacle和异常，故原生控制流没有隐藏exit/delete，也没有额外RNG分支。

因此单OMP worker下每live filament每tick三次draw的call-assignment控制流证书成立，累计2,946,303次。相同seed两源的clock/count/σ order相同。**跨wrong-wind arms的真实CRN仍未测**，只能留待授权后的E2 sentinel；不能把E1证书说成E2通过。

## 资源、完整性和下一步

八条simulation＋native extraction campaign wall=13.452 s；single run simulation 0.816–1.003 s，extraction 0.350–0.395 s。最大RSS=127,578,112 bytes（约121.7 MiB）。此为当前box实测，不外推成FSR/CFD成本。

按冻结资源公式，后32条投影含3×q95安全倍数和30 min余量共约1,940 s，现有input/output 533,726,228 bytes，含后32条投影约714 MB；均低于3 h/5 GiB。执行后磁盘free=27,804,160,000 bytes，RAM available=5,766,455,296 bytes，仍通过12/3 GiB门。完整逐run raw/extraction/metadata bytes清单、实际time/RSS、argv、env、input/output/source/runtime SHA256随包保存；精确artifact计数另存。

Native raw包包含8条全部iterations、filament state dump、route samples、native parity、ROI columns、timelines、原生源码快照、实际assets和decoder readback，2,551个文件hash已复核。Archive SHA256：`54efd99fc21f7aedfd7ee2da62b00dd395df517609d55f4d18a5285a26f2b803`。原R0包39份hash再次通过。

独立复核使用稳定erfc及手工两候选odds/variance：margin max diff=0，PairA mean max diff=5.997e−19，posterior max diff=8.882e−16；无新增模拟。外置`verify_r0_portable.py`解决跨平台provenance basename核查，不修改R0；原`freeze_design.py --verify`仍为跨平台archive check。

**已停止，等待E1审查。** 若后续明确授权E2，预登记sentinel为S0/r1的四个wrong-wind arms，均属于原32行；本轮没有调用它们。E1资格通过只说明这个box可承载已定义的baseline实验，不能宣布transport-anisotropy机制、M0_PASS或PRIMARY_GO。
