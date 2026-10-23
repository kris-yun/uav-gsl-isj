import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {Presentation, PresentationFile, FileBlob} from '@oai/artifact-tool';
import {GlobalFonts} from '@napi-rs/canvas';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const build=path.resolve(process.env.PPTX_BUILD_DIR ?? path.join(root,'runs/presentation_build'));
const output=path.resolve(process.env.PPTX_OUTPUT_DIR ?? path.join(root,'docs'));
const original=path.resolve(process.env.PMFS_ORIGINAL_PPTX ?? path.join(root,'docs/source/PMFS_ORIGINAL.pptx'));
await fs.mkdir(build,{recursive:true});
const fontPath=process.env.PPTX_CJK_FONT;
if(!fontPath)throw Error('Set PPTX_CJK_FONT to a local NotoSansCJKsc-Regular.otf; see METHOD_FRAMEWORK_V1_notes.md.');
GlobalFonts.registerFromPath(fontPath,'Noto Sans CJK SC');
const {FontLibrary}=await import(pathToFileURL(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'@oai/artifact-tool/node_modules/skia-canvas/lib/index.mjs')).href);
FontLibrary.use('Noto Sans CJK SC',fontPath);
const p=await PresentationFile.importPptx(await FileBlob.load(original));
const s=p.slides.items[0];
const C={ink:'#233440',grey:'#596975',greybg:'#F2F4F6',blue:'#2E70A2',bluebg:'#EDF4FA',green:'#237B62',greenbg:'#EDF6F1',orange:'#B36A20',orangebg:'#FCF4EA',line:'#CCD6DC'};
const FONT='Noto Sans CJK SC';
const byName=new Map(s.shapes.items.map(x=>[x.name,x]));
const canonical=new Map((await p.inspect({select:'$.slides[0].elements[*]',include:['id','name']})).records.map(x=>[x.name,x.id]));
function old(name){const x=byName.get(name);if(!x)throw Error('missing '+name);return x;}
function set(name,txt,opts={}){const x=old(name);x.text=txt;x.text.style={typeface:FONT,fontSize:opts.fontSize??27,color:opts.color??C.ink,bold:opts.bold??false,alignment:opts.align??'left',verticalAlignment:'middle',wrap:'word',autoFit:'none',insets:0};if(opts.pos)x.position=opts.pos;return x;}
function box(slide,name,x,y,w,h,fill,line=C.line){return slide.shapes.add({geometry:'roundRect',name,position:{left:x,top:y,width:w,height:h},fill,line:{style:'solid',fill:line,width:1.3},borderRadius:12});}
function txt(slide,name,text,x,y,w,h,size=26,color=C.ink,bold=false,align='left'){const z=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{style:'solid',fill:'none',width:0}});z.text=text;z.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,verticalAlignment:'middle',wrap:'word',autoFit:'none',insets:0};return z;}
function arrow(slide,a,b,color=C.grey,from='right',to='left',style='solid'){const z=slide.shapes.connect(a,b,{kind:'straight',fromSide:from,toSide:to,line:{style,fill:color,width:2.2},tail:{type:'arrow',width:'med',length:'med'}});z.bringToFront();return z;}
function erase(names){for(const name of names){const id=canonical.get(name);if(id)p.delete(id);}}

// Edit imported slide and retain its four original regions and native maps.
set('00_TITLE__title','源证据恢复：竞争源判别与主动纠错闭环',{fontSize:39,bold:true,align:'center'});
txt(s,'V5_SUBTITLE','保留二维源概率地图与主动定位任务；以联合响应、证据回放和反证规划重构内部计算',160,81,1280,26,21,C.grey,false,'center');
old('01_REGIONS__measured_panel').fill=C.greybg;
old('01_REGIONS__prediction_panel').fill=C.bluebg;
old('01_REGIONS__compare_panel').fill=C.greenbg;
old('01_REGIONS__sampling_panel').fill=C.orangebg;

set('02_MEASURED__measured_letter','a',{fontSize:30,color:C.grey,bold:true});
set('02_MEASURED__measured_heading','原始输入与历史账本',{fontSize:31,bold:true});
set('02_MEASURED__gas_label','历史气体观测',{fontSize:28,bold:true});
set('02_MEASURED__events_label','气体事件',{fontSize:23,color:C.grey});
set('02_MEASURED__pose_label','无人机状态 / 动作历史',{fontSize:22,bold:true});
set('02_MEASURED__observed_map_title','几何 / 障碍 / 候选源',{fontSize:25,color:C.grey,bold:true});
set('02_MEASURED__f_observed','历史局地风 U₁:ₜ',{fontSize:26,color:C.grey,align:'center'});
set('02_MEASURED__confidence_title','Hₜ = {aₖ, Uₖ, Yₖ, 唯一 ID}',{fontSize:24,pos:{left:66,top:493,width:520,height:38}});
for(const [name,x] of byName){if(name.startsWith('02_MEASURED__confidence')&&name!=='02_MEASURED__confidence_title')p.delete(canonical.get(name));}
txt(s,'V5_LEDGER_POLICY','原始观测只入账一次，保留完整候选源集合',66,533,520,25,20,C.grey);

set('03_PREDICTIONS__prediction_letter','M1',{fontSize:29,color:C.blue,bold:true,pos:{left:677,top:130,width:55,height:37}});
set('03_PREDICTIONS__prediction_heading','源证据微分监督的联合观测生成器',{fontSize:31,bold:true,pos:{left:740,top:130,width:798,height:37}});
set('03_PREDICTIONS__wind_inputs','局地风 / 几何条件',{fontSize:26,bold:true});
set('03_PREDICTIONS__wind_field','风保持约束  Jᵤv = 0',{fontSize:25,color:C.blue});
set('03_PREDICTIONS__filament_title','物理教师与生成器',{fontSize:26,bold:true});
set('03_PREDICTIONS__stochastic','源证据导数  ∂ₛ log qθ',{fontSize:24,color:C.blue});
set('03_PREDICTIONS__predicted_title','源条件联合响应',{fontSize:26,color:C.blue,bold:true});
set('03_PREDICTIONS__predicted_formula','历史联合似然 / 未来联合采样',{fontSize:20,color:C.blue,pos:{left:1237,top:475,width:310,height:46},align:'center'});
set('03_PREDICTIONS__refine_title','训练：NLL + 微分弱监督 + 分支补偿',{fontSize:23,color:C.blue,pos:{left:680,top:505,width:560,height:34}});
set('03_PREDICTIONS__source1_label','s₁',{fontSize:25});set('03_PREDICTIONS__source2_label','s₂',{fontSize:25});
// Recolor the imported forward-model illustrations, without rasterizing them.
for(const [name,x] of byName){
 if(name.startsWith('03_PREDICTIONS__')&&(/refin|coarse|fine/.test(name))&&name!=='03_PREDICTIONS__refine_title')p.delete(canonical.get(name));
}
// The original wind-to-mapping route becomes an input-to-generator route.
erase([...byName.keys()].filter(n=>n.startsWith('08_ROUTES__context_to_mapping')));
const ip=txt(s,'V5_INPUT_PORT','',618,300,1,1,1);const gp=txt(s,'V5_GENERATOR_PORT','',654,300,1,1,1);arrow(s,ip,gp,C.blue);

set('04_COMPARISON__compare_letter','M2',{fontSize:29,color:C.green,bold:true,pos:{left:62,top:629,width:55,height:37}});
set('04_COMPARISON__compare_heading','机制差分诊断与可撤销证据回放',{fontSize:30,bold:true,pos:{left:123,top:629,width:860,height:37}});
set('04_COMPARISON__match_observed_label','实际观测',{fontSize:24,color:C.green,bold:true});
set('04_COMPARISON__match_predicted_label','名义参考',{fontSize:24,color:C.blue,bold:true});
set('04_COMPARISON__cell_comparison','诊断源与机制解释的冲突',{fontSize:23,color:C.green});
set('04_COMPARISON__agreement_title','撤销旧后缀贡献',{fontSize:25,color:C.green,bold:true});
set('04_COMPARISON__agreement_equation','按新机制回放并替换',{fontSize:24,color:C.green,pos:{left:456,top:722,width:245,height:37}});
set('04_COMPARISON__product','联合后验 P(s,e | Hₜ)',{fontSize:23,color:C.green});
set('04_COMPARISON__source_probability','二维源位置概率图',{fontSize:24,color:C.grey,bold:true,align:'center'});
set('04_COMPARISON__distribution_symbol','P(s | Hₜ) = Σₑ P(s,e | Hₜ)',{fontSize:21,color:C.grey,pos:{left:717,top:866,width:285,height:29},align:'center'});
txt(s,'V5_DIAGNOSIS_NOTE','诊断仅提出机制，不作为第二份观测证据',66,842,655,31,21,C.green);

set('05_SAMPLING__sampling_letter','M3',{fontSize:29,color:C.orange,bold:true,pos:{left:1072,top:629,width:55,height:37}});
set('05_SAMPLING__sampling_heading','容错反证主动观测规划',{fontSize:27,bold:true,pos:{left:1137,top:629,width:400,height:37}});
set('05_SAMPLING__disagreement','软联合码本',{fontSize:26,bold:true,color:C.orange});
set('05_SAMPLING__weighted','误拒风险 ≤ α',{fontSize:24});
set('05_SAMPLING__unobserved','最坏反证功效 β',{fontSize:24});
set('05_SAMPLING__exploration','可恢复候选列表',{fontSize:24,color:C.orange});
set('05_SAMPLING__planning_equation','输出：下一观测动作 / 航线 Q*',{fontSize:26,color:C.orange,pos:{left:1073,top:839,width:465,height:39}});
set('09_LEGEND__feedback_label','执行观测块，采集气体与局地风，按唯一 ID 回流历史账本',{fontSize:24,pos:{left:300,top:909,width:980,height:34},align:'center'});
set('09_LEGEND__disclosure','灰：保留任务与二维地图    蓝：M1 主创新    绿：M2 辅助创新    橙：M3 主动闭环',{fontSize:22,color:C.grey,pos:{left:40,top:962,width:1520,height:32},align:'center'});
erase(['09_LEGEND__wall_legend','09_LEGEND__wall_label','09_LEGEND__position_legend','09_LEGEND__position_label']);
s.speakerNotes.text='依据用户原始 pmfs原方法图.pptx 导入编辑，保留 1600×1000 尺寸、四分区、原生地图/障碍/路径图形、输入—预测—比较—选点闭环布局。SHA256:95cb24f31f63a7003d598f20896c1207d95eb14f77a378dc80915c9491984af6。全部为可编辑 PPT 原生对象。图中地图仅为示意，非实验结果。PMFS: https://arxiv.org/html/2304.08879v3 。M1 母算法：ICML 2025 Conditioning Diffusions Using Malliavin Calculus, https://proceedings.mlr.press/v267/pidstrigach25a.html ; SIGGRAPH Asia 2025 Automatic Sampling for Discontinuities in Differentiable Shaders, https://yashbelhe.github.io/asd/index.html 。M2: ICML 2025 Identifying Biological Perturbation Targets through Causal Differential Networks, https://proceedings.mlr.press/v267/wu25v.html 。M3: IEEE ISIT 2025 Multi-Stage Active Sequential Hypothesis Testing with Clustered Hypotheses, https://arxiv.org/html/2501.11459v2 。实际原生模拟器教师与冻结 House 泛化实验状态见 IMPLEMENTATION_AUDIT.md。';

// Add an editable second slide with the same rounded-region vocabulary.
const s2=p.slides.add();s2.background.fill='#FFFFFF';
txt(s2,'V5_DETAIL_TITLE','三模块接口与在线闭环',40,27,1520,54,39,C.ink,true,'center');
txt(s2,'V5_DETAIL_SUBTITLE','统一模型输出历史联合似然与未来联合观测；原始观测是唯一证据入口',100,86,1400,32,25,C.grey,false,'center');
const columns=[{x:40,c:C.blue,bg:C.bluebg,name:'M1  源证据微分监督',sub:'借鉴：随机分析 + 可微渲染'}, {x:565,c:C.green,bg:C.greenbg,name:'M2  机制诊断与回放',sub:'借鉴：计算生物学因果差分网络'}, {x:1090,c:C.orange,bg:C.orangebg,name:'M3  容错反证与列表恢复',sub:'借鉴：主动序贯检验 + 编码理论'}];
const boxes=[];
for(const col of columns){box(s2,'detail_'+col.x,col.x,145,470,624,col.bg,col.c);txt(s2,'heading_'+col.x,col.name,col.x+22,162,426,44,28,col.c,true);txt(s2,'mother_'+col.x,col.sub,col.x+22,212,426,33,22,col.c);}
function stage(i,idx,title,body){const col=columns[i],y=270+idx*150;const b=box(s2,'stage_'+i+'_'+idx,col.x+25,y,420,118,'#FFFFFF',col.c);txt(s2,'stage_title_'+i+'_'+idx,title,col.x+43,y+10,384,32,25,col.c,true);txt(s2,'stage_body_'+i+'_'+idx,body,col.x+43,y+48,384,62,23,C.ink);if(idx>0)arrow(s2,boxes[i][idx-1],b,col.c,'bottom','top');boxes[i]??=[];boxes[i][idx]=b;return b;}
stage(0,0,'源条件物理教师','输入：几何 G、源 s、随机种子 ξ\n风保持提升 + 硬分支边界补偿');
stage(0,1,'联合观测生成器 qθ','输入：历史 Hₜ、动作块 Q、机制 e\n目标：NLL + 源证据微分弱监督');
stage(0,2,'两个标准输出接口','历史：log qθ(Hₜ | s,e)\n未来：qθ(Oₜ₊₁:ₜ₊ᴸ | Hₜ,Q,s,e)');
stage(1,0,'源—机制差分诊断','输入：Hₜ + M1 源条件名义参考\n输出：机制类型 / 起点 / 持续时间');
stage(1,1,'后缀回放与替换','log L新 = log L旧 − 旧后缀 + 新后缀\n重算所有受影响的后续状态');
stage(1,2,'源—机制联合后验','固定先验；精确枚举或 π(e)/q(e) 校正\nP(s | Hₜ) = Σₑ P(s,e | Hₜ)');
stage(2,0,'联合软码本与挑战列表','输入：M1 联合分布 + M2 联合后验\n采样合法动作块，覆盖低后验候选');
stage(2,1,'风险约束反证测试','max β；对所有合法机制误拒率 ≤ α\n软译码同时覆盖翻转 / 擦除 / 突发错');
stage(2,2,'执行、译码与恢复','整块执行；观测回流 M2 重估机制\n机制版本变化则恢复旧排除候选');
// Explicit inter-module data flow, through dedicated lower lanes.
txt(s2,'M1_M2_LINK','似然',512,600,50,25,19,C.green,false,'center');
txt(s2,'M2_M3_LINK','后验',1037,600,50,25,19,C.orange,false,'center');
arrow(s2,boxes[0][2],boxes[1][2],C.green);
arrow(s2,boxes[1][2],boxes[2][2],C.orange);
const ledger=box(s2,'detail_ledger',40,815,470,90,C.greybg,C.grey);txt(s2,'detail_ledger_text','唯一观测账本 Hₜ\n气体、局地风、动作、时间、观测 ID',62,826,426,66,24,C.grey,true,'center');
const out=box(s2,'detail_map',565,815,470,90,C.greybg,C.grey);txt(s2,'detail_map_text','保留 PMFS 输出目标\n二维源概率地图 + 竞争源 / 机制后验',587,826,426,66,24,C.grey,true,'center');
const act=box(s2,'detail_action',1090,815,470,90,C.orangebg,C.orange);txt(s2,'detail_action_text','主动定位闭环\n下一动作块 / 航线 + 新观测',1112,826,426,66,24,C.orange,true,'center');
arrow(s2,boxes[1][2],out,C.green,'bottom','top');arrow(s2,boxes[2][2],act,C.orange,'bottom','top');
const hp1=txt(s2,'history_port1','',20,860,1,1,1),hp2=txt(s2,'history_port2','',20,479,1,1,1);
arrow(s2,ledger,hp1,C.grey,'left','right');arrow(s2,hp1,hp2,C.grey,'top','bottom');arrow(s2,hp2,boxes[0][1],C.grey,'right','left');
const p1=txt(s2,'feedback_port1','',1325,938,1,1,1),p2=txt(s2,'feedback_port2','',275,938,1,1,1);
arrow(s2,act,p1,C.orange,'bottom','top');arrow(s2,p1,p2,C.orange);arrow(s2,p2,ledger,C.orange,'top','bottom');
txt(s2,'detail_loop_label','动作执行后的原始观测回流；反证判决不重复计入似然',440,912,720,31,23,C.grey,false,'center');
txt(s2,'detail_footer','替换 PMFS：前向响应 / 派生地图比较 / 高置信错误后的更新 / 下一测点价值函数',40,963,1520,30,22,C.grey,false,'center');
s2.speakerNotes.text='M1 的高维原生 GADEN 教师接口不应与受控后端验证混淆。M2 诊断输出只用于机制提议与计算调度，不可作为独立观测再次相乘。M3 的风险保证依赖预测分布、机制支持与扰动集合有效；蒙特卡洛概率需要置信修正。固定整个测试动作块后执行，避免中途重规划破坏条件风险预算。M1 未来联合分布直接服务 M3，历史似然直接服务 M2；本页横向底部连线以接口标签说明。三个模块均可独立替换为标准基线进行消融。文献链接见第 1 页备注与 THEORY_AND_PROOFS.md。';

await fs.mkdir(output,{recursive:true});
for(let i=0;i<p.slides.items.length;i++){
 const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1.25});
 await fs.writeFile(path.join(build,`revised_${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const snap=await p.inspect({select:'$.slides[*]',include:['id','index','elements.id','elements.name','elements.text','elements.position']});
await fs.writeFile(path.join(build,'revised_snapshot.ndjson'),snap.ndjson);
await fs.writeFile(path.join(build,'revised_proto.json'),JSON.stringify(p.toProto()));
const candidate=path.join(build,'candidate.pptx');await (await PresentationFile.exportPptx(p)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL('/root/.codex/skills/builtins/presentations/container_tools/artifact_tool_utils.mjs').href);
const finalPath=path.join(output,process.env.PPTX_NAME??'METHOD_FRAMEWORK_V1.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,explicitTotalSlideCount:2,pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,integrityValidatorPath:'/root/.codex/skills/builtins/presentations/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:'/root/.codex/skills/builtins/presentations/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','15240000,9525000','--validate-bullet-geometry','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Arial',FONT],scriptFonts:{ea:FONT}},verifyArtifactToolImport:true,receiptPath:path.join(build,path.basename(finalPath)+'.validation.json')});
console.log(JSON.stringify(result));
