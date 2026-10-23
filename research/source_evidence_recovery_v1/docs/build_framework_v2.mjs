import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
// Imports use the primary runtime, without a repo-local dependency tree.
const runtime=process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES;
if(!runtime)throw new Error('CODEX_PRIMARY_RUNTIME_NODE_MODULES is required');
const {PresentationFile,FileBlob}=await import(pathToFileURL(path.join(runtime,'@oai/artifact-tool/dist/artifact_tool.mjs')).href).catch(async()=>await import('@oai/artifact-tool'));
const {GlobalFonts}=await import(pathToFileURL(path.join(runtime,'@napi-rs/canvas/index.js')).href);
const {FontLibrary}=await import(pathToFileURL(path.join(runtime,'@oai/artifact-tool/node_modules/skia-canvas/lib/index.mjs')).href);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const build=path.resolve(process.env.PPTX_BUILD_DIR??path.join(root,'runs/presentation_v2'));
const output=path.resolve(process.env.PPTX_OUTPUT_DIR??path.join(root,'docs'));
const source=path.join(root,'docs/METHOD_FRAMEWORK_V1.pptx');
const font=process.env.PPTX_CJK_FONT;
if(!font)throw new Error('PPTX_CJK_FONT must name NotoSansCJKsc-Regular.otf');
await fs.mkdir(build,{recursive:true});await fs.mkdir(output,{recursive:true});
GlobalFonts.registerFromPath(font,'Noto Sans CJK SC');FontLibrary.use('Noto Sans CJK SC',font);
const FONT='Noto Sans CJK SC';
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const s=p.slides.items[0],details=p.slides.items[1];
const C={ink:'#233440',grey:'#596975',greybg:'#F2F4F6',blue:'#2E70A2',bluebg:'#EDF4FA',green:'#237B62',greenbg:'#EDF6F1',orange:'#B36A20',orangebg:'#FCF4EA',line:'#CCD6DC'};
function names(slide){return new Map(slide.shapes.items.map(x=>[x.name,x]));}
function set(slide,name,text,opt={}){const x=names(slide).get(name);if(!x)throw new Error('Missing imported shape '+name);x.text=text;x.text.style={typeface:FONT,fontSize:opt.size??24,color:opt.color??C.ink,bold:opt.bold??false,alignment:opt.align??'left',verticalAlignment:'middle',wrap:'word',autoFit:'none',insets:0};if(opt.pos)x.position=opt.pos;return x;}
function text(slide,name,value,x,y,w,h,size=24,color=C.ink,bold=false,align='left'){const e=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});e.text=value;e.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,verticalAlignment:'middle',wrap:'word',autoFit:'none',insets:0};return e;}
function box(slide,name,x,y,w,h,fill,color=C.line){return slide.shapes.add({geometry:'roundRect',name,position:{left:x,top:y,width:w,height:h},fill,line:{style:'solid',fill:color,width:1.3},borderRadius:12});}
function arrow(slide,a,b,color=C.grey,from='right',to='left',style='solid'){const e=slide.shapes.connect(a,b,{kind:'straight',fromSide:from,toSide:to,line:{style,fill:color,width:2.2},tail:{type:'arrow',width:'med',length:'med'}});e.bringToFront();return e;}

// First page: focused edits of the imported V1 diagram preserve its native maps,
// four panels, historical PMFS layout, connectors, masters and 1600x1000 canvas.
set(s,'00_TITLE__title','源证据恢复 V2：竞争源判别与主动纠错闭环',{size:37,bold:true,align:'center',pos:{left:40,top:27,width:1520,height:54}});
set(s,'V5_SUBTITLE','保留二维源概率地图和主动选点闭环，共用合法历史条件下的联合观测模型',{size:22,color:C.grey,align:'center'});
set(s,'03_PREDICTIONS__prediction_heading','合法历史投影的源证据蒸馏',{size:31,bold:true});
set(s,'03_PREDICTIONS__wind_inputs','外生物理状态库（仅训练）',{size:23,bold:true});
set(s,'03_PREDICTIONS__wind_field','三维风 / 传播状态 z',{size:24,color:C.blue});
set(s,'03_PREDICTIONS__filament_title','按候选源过滤历史',{size:25,bold:true});
set(s,'03_PREDICTIONS__stochastic','bₛ(z | Hₜ)，保留多解',{size:23,color:C.blue});
set(s,'03_PREDICTIONS__predicted_title','源条件联合证据',{size:26,color:C.blue,bold:true});
set(s,'03_PREDICTIONS__predicted_formula','历史联合似然 / 未来联合采样',{size:20,color:C.blue,align:'center'});
set(s,'03_PREDICTIONS__refine_title','教师：log p(H,Y | s) − log p(H | s)\n学生：合法历史 + 相对几何 + 混合 GRU',{size:22,color:C.blue,pos:{left:680,top:490,width:560,height:66}});
set(s,'04_COMPARISON__product','联合后验 P(s,m | Hₜ)',{size:23,color:C.green});
set(s,'04_COMPARISON__distribution_symbol','P(s | Hₜ) = Σₘ P(s,m | Hₜ)',{size:21,color:C.grey,align:'center'});
set(s,'05_SAMPLING__unobserved','反证功效与风险界',{size:23});
set(s,'05_SAMPLING__weighted','模型内误拒风险 ≤ α',{size:22});
set(s,'V5_LEDGER_POLICY','原始观测只入账一次，保留合法低概率候选',{size:20,color:C.grey});
set(s,'09_LEGEND__disclosure','灰：保留任务与二维地图    蓝：M1 主创新候选    绿：M2 辅助候选    橙：M3 主动闭环',{size:21,color:C.grey,align:'center'});
s.speakerNotes.text='V2直接导入并编辑METHOD_FRAMEWORK_V1.pptx。V1由用户PMFS原方法图PPTX编辑形成，原图SHA256=95cb24f31f63a7003d598f20896c1207d95eb14f77a378dc80915c9491984af6。保持1600×1000尺寸、四分区和原生地图/障碍/箭头。图中地图是方法示意，不是实验结果。M1新目标：对每源历史进行过滤后，以完整历史与过去历史的边缘log-evidence差构成条件联合预测；先积分再取log及源微分，不能复制单个真状态oracle。Fisher identity、条件积分和Bayes归一化为已知结构，不算单独创新。二次创新候选是源条件过滤、连续源/边界处理、传感器readout和源对联合证据蒸馏的完整方法。现有实现和原生teacher资格以IMPLEMENTATION_AUDIT.md为准。M2原始观测只计一次，诊断只作机制提议。M3反证风险界依赖模型及扰动集合的有效性。PMFS:https://arxiv.org/html/2304.08879v3 。M1:https://proceedings.mlr.press/v267/pidstrigach25a.html ; https://yashbelhe.github.io/asd/index.html ; https://proceedings.mlr.press/v306/feng26aa.html 。M2:https://proceedings.mlr.press/v267/wu25v.html 。M3:https://arxiv.org/html/2501.11459v2 。';

// Second page: added between the two imported slides using the same template.
const {slide:train}=p.slides.insert({after:s});train.background.fill='#FFFFFF';
text(train,'V2_TRAIN_TITLE','训练期物理特权与部署期源证据',40,27,1520,54,39,C.ink,true,'center');
text(train,'V2_TRAIN_SUBTITLE','教师目标先投影到学生可见历史，再监督联合观测与竞争源证据',100,88,1400,32,25,C.grey,false,'center');
box(train,'V2_TEACHER_PANEL',40,145,910,420,C.greybg,C.grey);
box(train,'V2_STUDENT_PANEL',990,145,570,420,C.bluebg,C.blue);
text(train,'V2_TEACHER_HEAD','仅训练：物理教师与信息投影',65,165,860,45,30,C.grey,true);
text(train,'V2_STUDENT_HEAD','部署：归一化混合 GRU 学生',1015,165,520,45,29,C.blue,true);
const stages=[
 ['物理状态与源条件','物理风场和传播状态 z\n几何 G 与连续源坐标 s'],
 ['按每个候选源过滤','bₛ(z | Hₜ)\n历史气体与历史局地风'],
 ['保留源对证据','联合分布先积分再取 log\n源对 Λₐᵦ 与合法方向 gₛ']
];
const sb=[];
for(let i=0;i<3;i++){
const x=65+i*295;sb.push(box(train,'V2_TEACHER_STEP_'+i,x,240,270,155,'#FFFFFF',C.grey));
text(train,'V2_TEACHER_STEP_H_'+i,stages[i][0],x+15,253,240,34,25,C.grey,true);
text(train,'V2_TEACHER_STEP_B_'+i,stages[i][1],x+15,300,240,76,21,C.ink);
if(i)arrow(train,sb[i-1],sb[i],C.grey);
}
text(train,'V2_MARGINAL_EVIDENCE','ℓₛ(Y | H,Q) = log ∫ pₛ(H,Y,z | Q) dz − log ∫ pₛ(H,z) dz',65,425,860,47,26,C.blue,false,'center');
text(train,'V2_GRADIENT_TARGET','gₛ = ∇ₛ log pₛ(H,Y | Q) − ∇ₛ log pₛ(H)',65,481,860,40,27,C.blue,false,'center');
text(train,'V2_GRADIENT_CONDITION','连续导数仅在教师可微且支持条件有效时启用',65,529,860,25,21,C.grey,false,'center');
const inStudent=box(train,'V2_STUDENT_INPUT',1015,230,520,95,'#FFFFFF',C.blue);
text(train,'V2_STUDENT_INPUT_TEXT','合法历史 Hₜ + 相对源 / 障碍几何\n候选动作 Q + 机制 m',1035,243,480,67,24,C.ink,false,'center');
const arStudent=box(train,'V2_STUDENT_AR',1015,368,520,102,'#FFFFFF',C.blue);
text(train,'V2_STUDENT_AR_TEXT','因果 GRU + 轨迹级混合潜变量\nNLL 锚点 + 投影后的源对证据监督',1035,381,480,75,24,C.blue,true,'center');
arrow(train,inStudent,arStudent,C.blue,'bottom','top');
const teacherPort=text(train,'V2_TEACHER_PORT','',950,420,1,1,1);arrow(train,teacherPort,arStudent,C.blue,'right','left','dash');
text(train,'V2_DISTILL_LABEL','蒸馏',951,373,64,30,20,C.blue,false,'center');
text(train,'V2_STUDENT_OUTPUT','气体—局地风联合分布\nlog_prob / sample_future',1015,485,520,62,24,C.blue,false,'center');
text(train,'V2_BOUNDARY_NOTE','训练使用仿真特权与源标签，部署仅使用合法历史、地图和候选动作',55,589,1490,38,25,C.ink,false,'center');
text(train,'V2_VALIDATION_HEAD','House 与湖岸 S2 的分阶段资格验证',60,660,1480,45,31,C.ink,true);
const road=[
 ['House：分层离线验证','House02：无风、记录序列\n仅离线联通，禁止原生主动部署'],
 ['S2：独立物理场景','不同几何与传播统计\n冻结后测迁移与主动闭环'],
 ['原生系统与飞行','ROS / GADEN 接口与时间对齐\n验证概率定位及错误恢复']
];
const r=[];
for(let i=0;i<3;i++){
const x=60+i*505;r.push(box(train,'V2_ROAD_'+i,x,728,470,143,i===2?C.orangebg:C.greybg,i===2?C.orange:C.grey));
text(train,'V2_ROAD_H_'+i,road[i][0],x+19,740,432,38,27,i===2?C.orange:C.grey,true);
text(train,'V2_ROAD_B_'+i,road[i][1],x+19,791,432,63,23,C.ink);
if(i)arrow(train,r[i-1],r[i],C.grey);
}
text(train,'V2_NATIVE_STATUS','原生 3D 教师训练资格：BLOCKED\nHouse02 仅离线；S2 与主动定位收益待验证',60,903,1480,75,25,C.orange,true,'center');
train.speakerNotes.text='训练信息与部署信息必须严格分离。物理教师可在训练期访问仿真3D风/羽流状态及源标签，先形成每源的合法历史过滤b_s(z|H)，再计算联合未来观测的条件分布。学生只读取历史传感器数据、动作、地图和候选源坐标。因果GRU或混合分布本身是标准架构，创新候选是投影后的源证据监督链及与错误恢复/反证规划的配合。Fisher identity和logsumexp为标准运算。教师梯度需要common support、可交换微分积分、源扰动边界项合格；不满足时仅启用端点证据版本。House与S2需真实不同场景、独立realization、冻结未见源/风及几何划分。原生bank未资格，不得将受控数据测试写成native效益。来源：HIB https://proceedings.mlr.press/v270/he25a.html (CoRL2024，2025出版，作者代码尚未核实发布)；MIST-WM https://proceedings.mlr.press/v306/feng26aa.html ；NeurIPS2024 PI POMDP https://proceedings.neurips.cc/paper_files/paper/2024/hash/74d188c51d97fcfbc0269f584d6a53b7-Abstract-Conference.html ；TWIST https://twist-sim2real.github.io/ (ICRA2024)；LANO https://ojs.aaai.org/index.php/AAAI/article/view/37001 。';

// Third page: retain and edit the original V1 interface diagram in place.
set(details,'V5_DETAIL_TITLE','三模块接口与在线闭环',{size:39,bold:true,align:'center'});
set(details,'V5_DETAIL_SUBTITLE','M1 输出气体—局地风联合分布，M2 回放历史证据，M3 选择反证观测',{size:24,color:C.grey,align:'center'});
set(details,'heading_40','M1  合法历史上的源证据',{size:27,color:C.blue,bold:true});
set(details,'mother_40','来源：特权 POMDP / 组合 SBI',{size:21,color:C.blue});
set(details,'stage_title_0_0','合法历史编码',{size:25,color:C.blue,bold:true});
set(details,'stage_body_0_0','局地气体 / 风历史 + 相对几何\n保留多模态传播不确定性',{size:22});
set(details,'stage_title_0_1','归一化联合生成',{size:25,color:C.blue,bold:true});
set(details,'stage_body_0_1','轨迹级潜状态保持时序相关\n气体与局地风逐步联合采样',{size:22});
set(details,'stage_body_0_2','历史：log pθ(Hₜ | s,m)\n未来：pθ(Yₜ₊₁:ₜ₊ᴸ | Hₜ,Q,s,m)',{size:21});
set(details,'stage_body_1_2','固定先验，机制提议须校正\nP(s | Hₜ) = Σₘ P(s,m | Hₜ)',{size:22});
set(details,'stage_body_2_1','max β，模型条件下误拒风险 ≤ α\n联合软译码保留时序相关错误',{size:22});
set(details,'stage_body_2_2','按承诺动作块执行并回流原始观测\n机制版本变化时恢复排除候选',{size:22});
set(details,'detail_loop_label','新观测进入唯一账本，反证判决只触发诊断和规划',{size:23,color:C.grey,align:'center'});
set(details,'detail_footer','独立消融：同容量 NLL / 直接蒸馏 / 投影源证据，M2 回放开关，M3 同模型联合 EIG',{size:21,color:C.grey,align:'center'});
// Dedicated M1->M3 route outside the panels, so the direct predictive interface is explicit.
const m1port=text(details,'V2_JOINT_PORT1','',510,746,1,1,1),m3port=text(details,'V2_JOINT_PORT2','',1090,746,1,1,1);
arrow(details,m1port,m3port,C.blue,'right','left');
text(details,'V2_JOINT_LABEL','M1 未来联合分布',568,705,220,30,22,C.blue,false,'center');
details.speakerNotes.text='本页是V1第二页原对象编辑，移到V2第三页。三个模块的母算法出处：M1合法历史投影借NeurIPS2024特权POMDP的belief加权，以及ICLR2025 Compositional SBI的有条件/先验校正score组合。后者原范围明确不含HMM；本项目使用源条件有限latentbank的完整历史与过去历史两项边缘，不声称照搬原Markov分解。ICML2026 MIST-WM只作任务动机/强基线，未实现其完整mask+InfoNCE。连续源teacher仍保留ICML2025 Malliavin/BEL与SIGGRAPH Asia2025分支边界采样路线，但native C状态须据审计。M2 ICML2025 causal differential networks只作机制提议，不重复当作观测证据。M3 ISIT2025 clustered hypothesis sequential testing结合联合软码本。M1历史log_prob和未来sample_future必须同模型一致，不能用额外pair classifier自由打分。M3反证功效需在同一M1下与普通联合EIG比较。M2回放须撤销旧后缀再按新机制重算所有受影响状态。所有创新均为待真实数据验证的候选。';

// Render all slides; export through required finalizer; re-import final output
// for previews and a native-editability evidence receipt.
for(let i=0;i<p.slides.items.length;i++){
 const b=await p.export({slide:p.slides.items[i],format:'png',scale:1.25});
 await fs.writeFile(path.join(build,`draft_slide_${i+1}.png`),new Uint8Array(await b.arrayBuffer()));
 const l=await p.slides.items[i].export({format:'layout'});await fs.writeFile(path.join(build,`draft_slide_${i+1}.layout.json`),await l.text());
}
const snap=await p.inspect({select:'$.slides[*]',include:['id','index','elements.id','elements.name','elements.text','elements.position']});
await fs.writeFile(path.join(build,'v2_snapshot.ndjson'),snap.ndjson);
const candidate=path.join(build,'candidate_v2.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const finalPath=path.join(output,process.env.PPTX_NAME??'METHOD_FRAMEWORK_V2.pptx');
const {finalizePresentation}=await import(pathToFileURL('/root/.codex/skills/builtins/presentations/container_tools/artifact_tool_utils.mjs').href);
const sha=crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,explicitTotalSlideCount:3,pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,integrityValidatorPath:'/root/.codex/skills/builtins/presentations/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:'/root/.codex/skills/builtins/presentations/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','15240000,9525000','--validate-bullet-geometry','--validate-heading-fit'],fontPolicy:{basis:'reference',families:['Arial',FONT],referencePath:source,referenceSha256:sha,scriptFonts:{ea:FONT}},verifyArtifactToolImport:true,receiptPath:path.join(build,path.basename(finalPath)+'.validation.json')});
console.log(JSON.stringify(result));
const final=await PresentationFile.importPptx(await FileBlob.load(finalPath));
const previews=['METHOD_FRAMEWORK_V2_preview.png','METHOD_FRAMEWORK_V2_training_preview.png','METHOD_FRAMEWORK_V2_interfaces_preview.png'];
for(let i=0;i<final.slides.items.length;i++){
const b=await final.export({slide:final.slides.items[i],format:'png',scale:1.25});await fs.writeFile(path.join(output,previews[i]),new Uint8Array(await b.arrayBuffer()));}
await fs.writeFile(path.join(build,'v2_final_proto.json'),JSON.stringify(final.toProto()));
