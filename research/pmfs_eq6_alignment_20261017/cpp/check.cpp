#include "extracted_native.hpp"
using namespace GSL;
static double stableLogScore(const Grid2D<HitProbability>&grid,const std::vector<float>&map,double power){
    double score=0;
    for(size_t i=0;i<map.size();++i)if(grid.occupancy[i]==Occupancy::Free){
        double p=Utils::logOddsToProbability(grid.data[i].logOdds);
        double v=Utils::lerp(1,1-std::abs(p-double(map[i]))*power,grid.data[i].confidence);
        if(!(v>0&&v<=1))throw std::runtime_error("invalid scoring factor");
        score+=std::log(v);
    }
    return score;
}
int main(int argc,char**argv){try{
    std::cout<<std::setprecision(17);
    if(argc==2&&std::string(argv[1])=="--unit"){
        int checks=0;double maxError=0;
        for(double w:{0.5,1.,2.})for(double omega:{0.,1e-9,0.3989422804014327,0.7978845608028654,1.,1.9947114020071635,10.}){
            HitProbability a,b;a.omega=b.omega=omega;HitProbabilitySettings s;s.confidenceMeasurementWeight=w;
            native::updateConfidence(a,s);eq6::updateConfidence(b,s);
            long double expected=-std::expm1(-((long double)omega*omega)/((long double)w*w));
            double err=std::abs(b.confidence-double(expected));maxError=std::max(maxError,err);
            if(err>2e-14||a.confidence<0||a.confidence>1||b.confidence<0||b.confidence>1)return 10;
            if(omega==1&&a.confidence!=b.confidence)return 11;
            ++checks;
        }
        HitProbability a,b;HitProbabilitySettings s;
        std::cout<<"step,omega,native_alpha,paper_eq6_alpha\n";
        for(int k=1;k<=5;++k){a.omega+=Utils::evaluate1DGaussian(0,1);b.omega=a.omega;native::updateConfidence(a,s);eq6::updateConfidence(b,s);std::cout<<k<<','<<a.omega<<','<<a.confidence<<','<<b.confidence<<'\n';}
        std::cerr<<"{\"status\":\"PASS\",\"equation_checks\":"<<checks<<",\"max_abs_error\":"<<std::setprecision(17)<<maxError<<"}\n";
        return 0;
    }
    if(argc!=3)return 2;
    std::string root=argv[1];std::ifstream req(root+"/request.txt");size_t n,m;double weight,power;req>>n>>m>>weight>>power;
    Grid2D<HitProbability>a,b;a.data.resize(n);a.occupancy.resize(n);HitProbabilitySettings settings;settings.confidenceMeasurementWeight=weight;
    double maxConfidenceError=0;
    for(size_t i=0;i<n;++i){int occ;double alpha;req>>occ>>a.data[i].logOdds>>a.data[i].omega>>alpha;a.occupancy[i]=occ==1?Occupancy::Free:Occupancy::Obstacle;
        if(occ==1){native::updateConfidence(a.data[i],settings);maxConfidenceError=std::max(maxConfidenceError,std::abs(a.data[i].confidence-alpha));}
        else a.data[i].confidence=alpha;
    }
    b=a;for(size_t i=0;i<n;++i)if(b.occupancy[i]==Occupancy::Free)eq6::updateConfidence(b.data[i],settings);
    std::ofstream out(argv[2]);out<<std::setprecision(17)<<"serial,native_product,paper_eq6_product,native_logscore,paper_eq6_logscore\n";
    PMFS_internal::Simulations sim;sim.settings.sourceDiscriminationPower=power;
    for(size_t k=0;k<m;++k){int serial;std::string path;req>>serial>>path;std::ifstream f(root+"/"+path,std::ios::binary);std::vector<float>map(n);f.read((char*)map.data(),n*sizeof(float));if(!f||!req)throw std::runtime_error("fixture read failure");
        double p0=sim.sourceProbFromMaps(a,map),p1=sim.sourceProbFromMaps(b,map),l0=stableLogScore(a,map,power),l1=stableLogScore(b,map,power);
        if(std::abs(p0-std::exp(l0))>2e-14||std::abs(p1-std::exp(l1))>2e-14)throw std::runtime_error("native product/log identity failure");
        out<<serial<<','<<p0<<','<<p1<<','<<l0<<','<<l1<<'\n';
    }
    std::cerr<<"{\"status\":\"PASS\",\"candidates\":"<<m<<",\"max_native_confidence_error\":"<<std::setprecision(17)<<maxConfidenceError<<"}\n";
    return maxConfidenceError<=2e-14?0:12;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 99;}}
