#include "../ros2_package/src/gsl_server/algorithms/PMFS/CTPIOnlineCoreV2.hpp"
#include <iostream>
#include <iomanip>
#include <string>
using namespace GSL::ctpi_v2;

void check(bool ok,const char* label) { if(!ok) throw std::runtime_error(label); }
template<class F> void rejects(F f) { bool caught=false; try { f(); } catch(const std::invalid_argument&) { caught=true; } check(caught,"expected rejection"); }
double l1(const std::vector<double>&a,const std::vector<double>&b) { double sum=0;for(size_t i=0;i<a.size();++i)sum+=std::abs(a[i]-b[i]);return sum; }
int main(int argc,char**argv)
{
    if(argc==2&&std::string(argv[1])=="sensor")
    {
        Fopdt s; double dt,input;
        std::cout<<std::setprecision(17);
        while(std::cin>>dt>>input) std::cout<<s.step(input,dt)<<'\n';
        return 0;
    }
    std::vector<unsigned char> free(81,1);
    Transport t(9,9,.3,.01,free);
    std::vector<double> c(81),u(81,.15),v(81,.15); c[40]=1.;
    const auto audit=t.advance(c,u,v,1.,20);
    check(audit.substeps==2&&std::abs(audit.finalSum-2.)<1e-12&&audit.minimum>=0,"mass/nonnegative");
    std::vector<double> zero(81),still(81);
    t.advance(zero,still,still,1.,20,0.);
    check(l1(zero,still)==0.,"zero stays zero");
    // A complete wall separates two components; no transport crosses it.
    for(size_t y=0;y<9;++y)free[4+y*9]=0;
    Transport wall(9,9,.3,.01,free); c.assign(81,0.);
    for(int i=0;i<50;++i)wall.advance(c,u,v,.2,2+4*9);
    for(size_t y=0;y<9;++y)for(size_t x=4;x<9;++x)check(c[x+y*9]==0.,"wall leakage");
    // One-dimensional pure advection with Courant=1 translates one cell.
    Transport advection(9,1,.3,0.,std::vector<unsigned char>(9,1));
    std::vector<double> p(9),wu(9,.3),wv(9);p[3]=1;
    advection.advance(p,wu,wv,1.,0,0.);
    check(std::abs(p[4]-1.)<1e-12,"advection displacement");
    // Temporal refinement at fixed grid must approach a common solution.
    auto solve=[&](double dt) { std::vector<double>a(81),b(81);a[40]=1.; for(int i=0;i<int(std::round(1./dt));++i)t.advance(a,b,b,dt,20,0.);return a; };
    const auto a=solve(.2),b=solve(.1),d=solve(.05),reference=solve(.00625);
    check(l1(d,reference)<l1(b,reference)&&l1(b,reference)<l1(a,reference),"time convergence");
    rejects([&]{t.advance(c,u,v,-1.,20);});
    u[0]=std::numeric_limits<double>::quiet_NaN();
    rejects([&]{t.advance(c,u,v,.2,20);});
    ObservationStream stream(2);
    rejects([&]{stream.predict(10.,0,{1,2});});
    rejects([&]{stream.observe(0,true);});
    rejects([&]{stream.predict(.2,.1,{1,2});});
    for(int i=1;i<=20;++i) { auto pred=stream.predict(i*.2,0,{1,2}); stream.observe(pred[0],i>10); }
    const auto block=stream.finishBlock();
    check(block.samples==10&&std::abs(block.observedMean-block.predictedMean[0])<1e-14,"sensor block identity");
    check(std::abs(block.predictedMean[1]-2*block.predictedMean[0])<1e-13,"source scaling");
    rejects([&]{stream.finishBlock();});
    rejects([&]{stream.predict(4.,0,{1,2});});
    rejects([&]{stream.predict(4.4,0,{1,2});});
    stream.predict(4.2,0,{1,2});
    rejects([&]{stream.predict(4.4,0,{1,2});});
    stream.observe(1.,true);
    check(stream.finishBlock().samples==1,"no duplicate block evidence");
    std::cout<<"CTPI_ONLINE_CORE_V2_SELFTEST=PASS\n";
    std::cout<<"counterexample_new_sum="<<audit.finalSum<<" substeps="<<audit.substeps<<"\n";
}
