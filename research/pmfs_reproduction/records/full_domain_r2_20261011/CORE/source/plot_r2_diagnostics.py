from common_r2 import *
import numpy as np,csv,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc');plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'svg.fonttype':'none','figure.dpi':130})
dest=CORE/'figures';dest.mkdir();data=list(csv.DictReader((CORE/'FUTURE_READOUT_PAIRED_EFFECTS.csv').open()));end=[r for r in data if r['blocks']=='50'];x=np.arange(6)
fig,axs=plt.subplots(1,2,figsize=(10,3.5),layout='constrained')
for ax,ka,kb,title,yl in [(axs[0],'NLL_O0','NLL_O1','源区域概率评分改善','真源区域负对数损失（越小越好）'),(axs[1],'top5_O0','top5_O1','坐标精度未稳定改善','原生 Top-5% 误差（米）')]:
 ax.plot(x,[float(r[ka]) for r in end],'o-',label='中心占据 O0',color='#bd5b27');ax.plot(x,[float(r[kb]) for r in end],'s-',label='PID 读出 O1',color='#2366a4');ax.set_xticks(x,[r['oid'] for r in end]);ax.set_title(title);ax.set_ylabel(yl);ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('预注册六份新观测：32个粗源区域，R01，同一原生评分头');fig.savefig(dest/'FUTURE6_SOURCE_LOSS_AND_DISTANCE.png',dpi=160);fig.savefig(dest/'FUTURE6_SOURCE_LOSS_AND_DISTANCE.svg');plt.close(fig)
ids=np.load(CORE/'SOURCE_CELL_TO_REGION.npy');cat=load(CORE/'SOURCE_CATALOG_AND_COVERAGE.json')['catalog'];a=np.load(CORE/'development_inference/FULL_SOURCE_POSTERIORS.npz');b=np.load(CORE/'future_inference/FULL_SOURCE_POSTERIORS.npz');tr=load(CORE/'evaluation_only/DEVELOPMENT_TRUTH.json');tr.update(load(CORE/'evaluation_only/FUTURE_TRUTH.json'));fig,axs=plt.subplots(2,3,figsize=(10,8),layout='constrained');extent=[-7.55,-7.55+34*.25,-7.88,-7.88+45*.25]
for row,oid,arr in [(0,'B4',a),(1,'Z04',b)]:
 for col,m in enumerate(['N_POINT_ALL','P3-O0','P3-O1']):
  z=arr[f'{oid}__R01__{m}__50_posterior'].reshape(45,34);masked=np.ma.masked_where(ids.reshape(45,34)<0,z);ax=axs[row,col];im=ax.imshow(masked,origin='lower',extent=extent,vmin=0,cmap='viridis');gt=tr[oid]['source_xyz'];ax.plot(gt[0],gt[1],'r*',ms=10);ax.set_aspect('equal');ax.set_title(f'{oid} / {m}');ax.set_xlabel('世界 x（米）');ax.set_ylabel('世界 y（米）');fig.colorbar(im,ax=ax,shrink=.65,label='每细格概率')
fig.suptitle('冻结50块后验；红星仅作审计真值标记，粗区内常值不代表细格已模拟');fig.savefig(dest/'B4_AND_Z04_MATCHED_SOURCE_POSTERIORS.png',dpi=160);fig.savefig(dest/'B4_AND_Z04_MATCHED_SOURCE_POSTERIORS.svg');plt.close(fig)
print(json.dumps({'figures':4,'plot_data':'Saved fullposteriors/pairCSV only; no recomputation or physics'}))
