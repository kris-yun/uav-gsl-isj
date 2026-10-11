"""Post-freeze descriptive plots of every heldout task; never selects/model-fits."""
import csv,json,pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
def main():
    with (OUT/'R4_B0_B1_B2_SOURCE_OUTPUT.csv').open(encoding='utf-8') as f:r=list(csv.DictReader(f))
    methods=['B0_FIXED','B1_TRANSIENT','B2_JOINT_PF','WIND_ORACLE'];colors=['#b65f31','#247ea0','#418556','#777777'];fig,axes=plt.subplots(1,3,figsize=(13.5,3.6),constrained_layout=True)
    for j,regime in enumerate(['constant','slow','fast']):
        ax=axes[j]
        for i,(m,col) in enumerate(zip(methods,colors)):
            y=[float(x['main_distance_m']) for x in r if x['split']=='heldout' and x['events']=='50' and x['regime']==regime and x['method']==m]
            ax.bar(i,np.mean(y),color=col,alpha=.6);ax.scatter(i+np.linspace(-.12,.12,len(y)),y,s=16,color=col,zorder=3)
        ax.set_xticks(range(4),['B0 fixed','B1 transient','B2 joint','Wind oracle'],rotation=30,ha='right');ax.set_title(regime+' mean wind');ax.set_ylabel('Source distance (m), common medoid');ax.grid(axis='y',alpha=.2);ax.set_ylim(0,10)
    fig.suptitle('18 heldout tasks: every independent realization shown; 25-point source support')
    fig.savefig(OUT/'R4_HELDOUT_SOURCE_DISTANCE.png',dpi=170);fig.savefig(OUT/'R4_HELDOUT_SOURCE_DISTANCE.svg');plt.close(fig)
    d=json.loads((OUT/'R4_PREREGISTRATION_REV1.json').read_text());task='T34';t=next(x for x in d['tasks'] if x['task_id']==task);truth=np.load(OUT/f'raw/evaluation_only/{task}.npz');src=d['inference']['source_support'][t['true_source_id']]
    fig,axes=plt.subplots(1,4,figsize=(12,3),constrained_layout=True)
    for ax,m in zip(axes,methods):
        a=np.load(OUT/f'raw/inference/{task}__{m}.npz');p=a['source_posterior'][-1].reshape(5,5)
        im=ax.imshow(p,origin='lower',extent=(1.25,11.25,1.25,11.25),vmin=0,vmax=1,cmap='viridis');ax.scatter(src['x_m'],src['y_m'],marker='x',s=100,color='red',linewidths=2);ax.set_title(m);ax.set_xlabel('source x (m)');ax.set_ylabel('source y (m)')
    fig.colorbar(im,ax=axes,label='Atomic candidate probability',fraction=.03)
    fig.suptitle('Fixed audit case T34 (fast wind): final posterior; red cross = evaluation truth')
    fig.savefig(OUT/'R4_FIXED_T34_SOURCE_POSTERIORS.png',dpi=170);fig.savefig(OUT/'R4_FIXED_T34_SOURCE_POSTERIORS.svg');plt.close(fig)
if __name__=='__main__':main()
