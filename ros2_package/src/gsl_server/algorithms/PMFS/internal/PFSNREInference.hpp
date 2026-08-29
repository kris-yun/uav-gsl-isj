#pragma once
// Dependency-free forward pass for the frozen PF-SNRE V2-exact topology.
// This class performs neural arithmetic only. Candidate physics acquisition,
// measured-sensor forward propagation and PMFS posterior adaptation are separate
// contracts so shadow tests can isolate side effects.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace GSL::PMFS_internal
{
    class PFSNREInference
    {
      public:
        void load(const std::string& path)
        {
            std::ifstream f(path, std::ios::binary);
            if (!f) throw std::runtime_error("PF-SNRE model open failed: " + path);
            char magic[8]{}; f.read(magic,8);
            const char expected[8]={'P','F','S','N','R','E','1','\0'};
            if (!f || !std::equal(magic,magic+8,expected)) throw std::runtime_error("PF-SNRE bad model magic");
            uint32_t h[6]{}; f.read(reinterpret_cast<char*>(h),sizeof(h));
            if (!f || h[0]!=1 || h[1]!=5 || h[2]!=6 || h[3]!=32 || h[4]!=14 || h[5]!=3301)
                throw std::runtime_error("PF-SNRE model header/architecture drift");
            static const std::array<std::vector<uint32_t>,14> shapes={
                std::vector<uint32_t>{32,40},{32},{32,32},{32},{64,143},{64},{32,64},{32},
                {64,134},{64},{32,64},{32},{1,32},{1}};
            tensors_.clear(); tensors_.reserve(shapes.size());
            for (const auto& want:shapes)
            {
                uint32_t ndim=0; f.read(reinterpret_cast<char*>(&ndim),4);
                if (!f || ndim!=want.size()) throw std::runtime_error("PF-SNRE tensor rank drift");
                std::vector<uint32_t> got(ndim); f.read(reinterpret_cast<char*>(got.data()),4*ndim);
                if (!f || got!=want) throw std::runtime_error("PF-SNRE tensor shape drift");
                size_t count=1; for(uint32_t d:got) count*=d;
                std::vector<float> x(count); f.read(reinterpret_cast<char*>(x.data()),sizeof(float)*count);
                if (!f) throw std::runtime_error("PF-SNRE truncated model tensor");
                for(float v:x) if(!std::isfinite(v)) throw std::runtime_error("PF-SNRE nonfinite weight");
                tensors_.push_back(std::move(x));
            }
            char extra=0; if(f.read(&extra,1)) throw std::runtime_error("PF-SNRE model has trailing bytes");
            loaded_=true;
        }

        float forward(const std::vector<float>& observation,      // [B,10]
                      const std::vector<float>& prediction,       // [B,M,10]
                      const std::vector<float>& blockContext,     // [B,6]
                      const std::array<float,5>& candidate,
                      size_t blocks, size_t members) const
        {
            if(!loaded_) throw std::runtime_error("PF-SNRE model not loaded");
            if(blocks==0 || members<2 || observation.size()!=blocks*10 ||
               prediction.size()!=blocks*members*10 || blockContext.size()!=blocks*6)
                throw std::invalid_argument("PF-SNRE runtime input shape mismatch");
            std::vector<float> blockEncoded(blocks*32);
            std::vector<float> memberEncoded(members*32);
            std::array<float,40> memberInput{};
            std::array<float,143> blockInput{};
            for(size_t b=0;b<blocks;++b)
            {
                for(size_t m=0;m<members;++m)
                {
                    for(size_t k=0;k<10;++k)
                    {
                        const float o=observation[b*10+k];
                        const float p=prediction[(b*members+m)*10+k];
                        memberInput[k]=o; memberInput[10+k]=p; memberInput[20+k]=o-p; memberInput[30+k]=std::abs(o-p);
                    }
                    auto z=dense(memberInput.data(),40,tensors_[0],tensors_[1],32,true);
                    z=dense(z.data(),32,tensors_[2],tensors_[3],32,true);
                    std::copy(z.begin(),z.end(),memberEncoded.begin()+m*32);
                }
                const auto mp=moments(memberEncoded,members,32);
                size_t q=0; for(float v:mp) blockInput[q++]=v;
                float mean=0.0f; for(size_t k=0;k<10;++k) mean+=observation[b*10+k]; mean/=10.0f;
                float var=0.0f,maxv=-std::numeric_limits<float>::infinity();
                for(size_t k=0;k<10;++k){const float v=observation[b*10+k];const float d=v-mean;var+=d*d;maxv=std::max(maxv,v);} var/=10.0f;
                blockInput[q++]=mean; blockInput[q++]=std::sqrt(std::max(var,0.0f));
                blockInput[q++]=(observation[b*10+9]-observation[b*10])/9.0f; blockInput[q++]=maxv;
                for(size_t k=0;k<6;++k) blockInput[q++]=blockContext[b*6+k];
                for(float v:candidate) blockInput[q++]=v;
                if(q!=blockInput.size()) throw std::runtime_error("PF-SNRE internal block feature count drift");
                auto z=dense(blockInput.data(),143,tensors_[4],tensors_[5],64,true);
                z=dense(z.data(),64,tensors_[6],tensors_[7],32,true);
                std::copy(z.begin(),z.end(),blockEncoded.begin()+b*32);
            }
            const auto bp=moments(blockEncoded,blocks,32);
            std::array<float,134> head{}; size_t q=0; for(float v:bp) head[q++]=v;
            head[q++]=std::log1p(static_cast<float>(blocks)); for(float v:candidate) head[q++]=v;
            if(q!=head.size()) throw std::runtime_error("PF-SNRE internal head feature count drift");
            auto z=dense(head.data(),134,tensors_[8],tensors_[9],64,true);
            z=dense(z.data(),64,tensors_[10],tensors_[11],32,true);
            z=dense(z.data(),32,tensors_[12],tensors_[13],1,false);
            if(!std::isfinite(z[0])) throw std::runtime_error("PF-SNRE nonfinite logit");
            return z[0];
        }

      private:
        std::vector<std::vector<float>> tensors_;
        bool loaded_=false;
        static float silu(float x)
        {
            if(x>=0.0f) return x/(1.0f+std::exp(-x));
            const float e=std::exp(x); return x*e/(1.0f+e);
        }
        static std::vector<float> dense(const float* x,size_t in,const std::vector<float>& w,
                                        const std::vector<float>& bias,size_t out,bool activation)
        {
            if(w.size()!=out*in || bias.size()!=out) throw std::runtime_error("PF-SNRE dense shape mismatch");
            std::vector<float> y(out);
            for(size_t o=0;o<out;++o)
            {
                float v=bias[o]; const float* row=w.data()+o*in;
                for(size_t i=0;i<in;++i) v+=row[i]*x[i];
                y[o]=activation?silu(v):v;
            }
            return y;
        }
        static std::vector<float> moments(const std::vector<float>& x,size_t count,size_t dim)
        {
            if(count==0 || x.size()!=count*dim) throw std::runtime_error("PF-SNRE moment shape mismatch");
            std::vector<float> out(4*dim); const float root=std::sqrt(static_cast<float>(count));
            for(size_t d=0;d<dim;++d)
            {
                float sum=0.0f,mx=-std::numeric_limits<float>::infinity();
                for(size_t n=0;n<count;++n){const float v=x[n*dim+d];sum+=v;mx=std::max(mx,v);} const float mean=sum/static_cast<float>(count);
                float var=0.0f;for(size_t n=0;n<count;++n){const float z=x[n*dim+d]-mean;var+=z*z;}var/=static_cast<float>(count);
                out[d]=mean;out[dim+d]=mx;out[2*dim+d]=std::sqrt(std::max(var,0.0f)+1e-8f);out[3*dim+d]=sum/root;
            }
            return out;
        }
    };
}
