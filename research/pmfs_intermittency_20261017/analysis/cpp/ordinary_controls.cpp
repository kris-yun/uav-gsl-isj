// Ordinary baselines only. No claimed new algorithm; no access to source truth.
#include <cmath>
#include <fstream>
#include <vector>
#include <cstdint>
int main(int argc,char**argv){if(argc!=5)return 2;std::ifstream meta(argv[1]),in(argv[2],std::ios::binary);std::ofstream out(argv[3],std::ios::binary);int nw,nf;double prior;meta>>nw>>nf>>prior;std::vector<double>H(nf),W(nf),B_H(nf),B_W(nf),B_C(nf),curH(nf),curW(nf),curC(nf);int last=-1,count=0;
for(int k=0;k<nw;++k){int stop,hit;meta>>stop>>hit;if(!meta)return 3;if(stop!=last){if(count)for(int i=0;i<nf;++i){B_H[i]+=curH[i]/count;B_W[i]+=curW[i]/count;B_C[i]+=curC[i]/count;curH[i]=curW[i]=curC[i]=0;}last=stop;count=0;}++count;
for(int i=0;i<nf;++i){double raw[4];in.read((char*)raw,sizeof(raw));if(!in)return 4;double w=raw[2],c=raw[3];H[i]+=hit*w;W[i]+=w;curH[i]+=hit*w;curW[i]+=w;curC[i]+=c;double sigma=std::stod(argv[4]);double v[]={W[i]>0?H[i]/W[i]:prior,(prior+H[i])/(1+W[i]),(prior+B_H[i]+curH[i]/count)/(1+B_W[i]+curW[i]/count),1-std::exp(-(B_C[i]+curC[i]/count)/(sigma*sigma))};out.write((char*)v,sizeof(v));}}
return out?0:5;}
