"""Export frozen forward fields only; never run skipped localization stages."""
import json

import numpy as np
import pandas as pd

from run import CFG,OUT,solve


def main():
    assert json.loads((OUT/'R0_TIBL_CONFIG.json').read_text())==CFG
    fields={};rows=[]
    for closure in CFG['closures']:
        for flux in CFG['heat_fluxes']:
            for case in CFG['cases']:
                x,z,k,_,_,c=solve(*CFG['grid'],flux,closure,case,CFG['sources_x'])
                key=closure+'_'+str(flux)+'_'+case
                fields[key+'_concentration']=c;fields[key+'_Kz']=k
                for i,sx in enumerate(CFG['sources_x']):
                    for xx in [400,700,1000]:
                        ii=int(abs(x-xx).argmin());p=c[ii,:,i]/c[ii,:,i].sum()
                        for j,zz in enumerate(z):
                            rows.append(dict(closure=closure,flux=flux,case=case,source_x=sx,
                                             requested_x=xx,actual_x=x[ii],height=zz,
                                             concentration=c[ii,j,i],normalized_cell_mass=p[j]))
    pd.DataFrame(rows).to_csv(OUT/'NORMALIZED_VERTICAL_PROFILES.csv',index=False)
    np.savez_compressed(OUT/'FROZEN_FORWARD_FIELDS.npz',x=x,z=z,source_x=CFG['sources_x'],**fields)
    print('forward diagnostic export complete')


if __name__=='__main__':main()
