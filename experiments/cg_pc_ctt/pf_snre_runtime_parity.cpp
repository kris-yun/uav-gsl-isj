#include <gsl_server/algorithms/PMFS/internal/PFSNREInference.hpp>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static std::vector<float> readFloats(std::ifstream& f,size_t n){std::vector<float>x(n);f.read(reinterpret_cast<char*>(x.data()),sizeof(float)*n);if(!f)throw std::runtime_error("truncated fixture");return x;}
int main(int argc,char**argv)
{
    if(argc!=3){std::cerr<<"usage: pf_snre_runtime_parity MODEL.pfsnre FIXTURE.pfsfx\n";return 2;}
    try
    {
        GSL::PMFS_internal::PFSNREInference model;model.load(argv[1]);
        std::ifstream f(argv[2],std::ios::binary);if(!f)throw std::runtime_error("fixture open failed");
        char magic[8]{};f.read(magic,8);const char expectedMagic[8]={'P','F','S','F','X','0','1','\0'};
        if(!f||!std::equal(magic,magic+8,expectedMagic))throw std::runtime_error("bad fixture magic");
        uint32_t h[2]{};f.read(reinterpret_cast<char*>(h),8);const size_t B=h[0],M=h[1];
        auto obs=readFloats(f,B*10);auto pred=readFloats(f,B*M*10);auto ctx=readFloats(f,B*6);auto candv=readFloats(f,5);float expected=0.0f;f.read(reinterpret_cast<char*>(&expected),4);if(!f)throw std::runtime_error("truncated expected logit");
        std::array<float,5> cand{};std::copy(candv.begin(),candv.end(),cand.begin());
        const float got=model.forward(obs,pred,ctx,cand,B,M);const double error=std::abs(static_cast<double>(got)-expected);
        std::cout<<"PF_SNRE_CPP_PARITY got="<<got<<" expected="<<expected<<" abs_error="<<error<<"\n";
        if(!(error<=1e-5)){std::cerr<<"PF_SNRE_CPP_PARITY FAIL\n";return 1;}std::cout<<"PF_SNRE_CPP_PARITY PASS\n";return 0;
    }
    catch(const std::exception& e){std::cerr<<"PF_SNRE_CPP_PARITY ERROR: "<<e.what()<<"\n";return 1;}
}
