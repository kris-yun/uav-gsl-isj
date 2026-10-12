#include "C1A_StateBridge.hpp"
#include <iostream>
#include <fstream>
#include <chrono>
#include <limits>
#include <algorithm>
int main(int argc,char**argv){
 using namespace C1A;Grid g;std::ifstream in(argv[1]);int x;while(in>>x)g.free.push_back(x);g.maskHash=argv[3];if(g.free.size()!=1530||std::count(g.free.begin(),g.free.end(),1)!=447)return 2;
 Context c;c.grid=g;Packet p;p.grid=g;p.sourceProbability.assign(1530,0);p.varianceOfHitProb.assign(1530,0);std::vector<int> active;for(int i=0;i<1530;++i)if(g.free[i]){active.push_back(i);p.sourceProbability[i]=1./447;}
 std::vector<double> mass(447,1./447);std::vector<std::vector<double>> h(447,std::vector<double>(447));for(int s=0;s<447;++s)for(int r=0;r<447;++r)h[s][r]=double((s*17+r*13)%101)/100;
 auto begin=std::chrono::steady_clock::now();std::vector<double> variance;for(int k=0;k<100;++k)variance=candidateHitVariance(mass,h);double duration=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
 for(int i=0;i<447;++i)p.varianceOfHitProb[active[i]]=variance[i];Fields f;applyFixture(p,c,f);if(f.sourceProbability!=p.sourceProbability||f.varianceOfHitProb!=p.varianceOfHitProb)return 3;
 int rejected=0;auto bad=[&](Packet q){try{validate(q,c);}catch(std::exception const&){++rejected;}};
 auto q=p;q.stateNs=3000;bad(q);q=p;q.lastObservationNs=1100;bad(q);q=p;q.epoch="old";bad(q);q=p;q.frame="sensor";bad(q);q=p;q.unit="mg/m3";bad(q);q=p;q.grid.maskHash="wrong";bad(q);q=p;q.sourceProbability[active[0]]=-.1;bad(q);q=p;q.sourceProbability[active[0]]=std::numeric_limits<double>::quiet_NaN();bad(q);q=p;q.sourceProbability[active[0]]+=.1;bad(q);q=p;q.varianceOfHitProb[active[0]]=.5;bad(q);q=p;for(int i=0;i<1530;++i)if(!g.free[i]){q.sourceProbability[i]=.01;break;}bad(q);q=p;q.sourceProbability.pop_back();bad(q);q=p;q.stateNs=999;bad(q);
 bool certificateRejected=false;Fields production;Context real;real.grid=g;try{applyProduction(p,real,production,{});}catch(std::exception const&){certificateRejected=true;}
 if(rejected!=13||!certificateRejected||!production.sourceProbability.empty())return 4;
 std::ofstream csv(argv[2]);csv.precision(17);csv<<"receptor,variance\n";for(int r=0;r<447;++r)csv<<r<<","<<variance[r]<<"\n";
 std::cout<<"{\"status\":\"PASS_ENGINEERING_ONLY\",\"support_cells\":447,\"rejected_invalid_packets\":"<<rejected<<",\"unqualified_physics_rejected\":true,\"production_unchanged\":true,\"scale_100x447x447_seconds\":"<<duration<<",\"native_PMFS_consumer_tested\":false,\"goals\":0,\"physical_forward_calls\":0}"<<std::endl;
}
