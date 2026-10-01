"""Reuse frozen input parsing/Native scoring; evaluate saved centers only."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
s=(root/'research/pmfs3d_r1/oracle_forward.cpp').read_text()
start=s.index('class Replay: public Simulations')
end=s.index('int main(',start)
s=s[:start]+r'''
static constexpr double MASS=6.440736978853164e-06;
static constexpr double AIR=4.0894632701667424e-05;
static constexpr double SIGMA0=10.0,GAMMA=15.0,THRESHOLD=0.1;
static float single(float sigma,const std::array<float,3>& p,const std::array<float,3>& q){
    float dx=p[0]-q[0],dy=p[1]-q[1],dz=p[2]-q[2];
    float distance_cm=100*std::sqrt(dx*dx+dy*dy+dz*dz);
    constexpr float pi_cubed=M_PI*M_PI*M_PI;
    float moles=float(MASS)/(std::sqrt(8*pi_cubed)*sigma*sigma*sigma);
    float center=1e6*moles/float(AIR);
    return center*std::exp(-(distance_cm*distance_cm)/(2*sigma*sigma));
}
static bool los(const Volume& vol,const std::array<float,3>& start,const std::array<float,3>& end){
    if(!vol.free(start)||!vol.free(end))return false;
    std::array<float,3> v;float distance=0;
    for(int k=0;k<3;k++){v[k]=end[k]-start[k];distance+=v[k]*v[k];}distance=std::sqrt(distance);
    int steps=distance/float(vol.cell);
    if(steps<=1)return true; // same no-interior-query result, avoids unused division by zero
    for(int k=0;k<3;k++)v[k]/=distance;
    float increment=distance/steps;
    for(int j=1;j<steps;j++){std::array<float,3> p;for(int k=0;k<3;k++)p[k]=start[k]+v[k]*(increment*j);if(!vol.free(p))return false;}
    return true;
}
class Replay: public Simulations{
public:
    using Simulations::Simulations;
    std::vector<float> meanC,maxC,nonzeroFraction;
    uint64_t totalActive=0,maxActive=0,queryCount=0,contributionCount=0;
    std::vector<float> gaussian(const fs::path& centers,const Volume& vol,double sensorZ){
        const auto& meta=measuredHitProb.metadata;size_t n=measuredHitProb.data.size();
        std::vector<float> hit(n,0);meanC.assign(n,0);maxC.assign(n,0);nonzeroFraction.assign(n,0);
        std::vector<double> sumC(n,0);totalActive=maxActive=queryCount=contributionCount=0;
        std::ifstream in(centers,std::ios::binary);if(!in)throw std::runtime_error("missing frozen centers");
        for(int t=0;t<settings.iterationsToRecord;t++){
            uint32_t count;in.read((char*)&count,4);if(!in)throw std::runtime_error("trajectory truncated");
            totalActive+=count;maxActive=std::max(maxActive,uint64_t(count));
            std::vector<float> concentration(n,0);
            for(uint32_t j=0;j<count;j++){
                std::array<float,3> p;double age;in.read((char*)p.data(),12);in.read((char*)&age,8);
                if(!in||age<0||!std::isfinite(age))throw std::runtime_error("bad trajectory");
                float sigma=std::sqrt(SIGMA0*SIGMA0+GAMMA*age),radius=sigma*3/100.f;
                if(std::abs(float(sensorZ)-p[2])>=radius)continue;
                // Superset of all sensor-plane queries within cutoff; exact radial test follows.
                int xmin=std::max(0,int(std::floor((p[0]-radius-meta.origin.x)/meta.cellSize))-1);
                int xmax=std::min(meta.dimensions.x-1,int(std::ceil((p[0]+radius-meta.origin.x)/meta.cellSize))+1);
                int ymin=std::max(0,int(std::floor((p[1]-radius-meta.origin.y)/meta.cellSize))-1);
                int ymax=std::min(meta.dimensions.y-1,int(std::ceil((p[1]+radius-meta.origin.y)/meta.cellSize))+1);
                for(int y=ymin;y<=ymax;y++)for(int x=xmin;x<=xmax;x++){
                    auto idx=meta.indexOf({x,y});if(measuredHitProb.occupancy[idx]!=Occupancy::Free)continue;
                    auto xy=meta.indicesToCoordinates({x,y});std::array<float,3> q{xy.x,xy.y,float(sensorZ)};
                    float dx=p[0]-q[0],dy=p[1]-q[1],dz=p[2]-q[2];
                    if(dx*dx+dy*dy+dz*dz<radius*radius&&los(vol,q,p)){concentration[idx]+=single(sigma,p,q);contributionCount++;}
                }
            }
            for(size_t i=0;i<n;i++)if(measuredHitProb.occupancy[i]==Occupancy::Free){
                queryCount++;sumC[i]+=concentration[i];maxC[i]=std::max(maxC[i],concentration[i]);
                if(concentration[i]>0)nonzeroFraction[i]++;
                // Frozen D0 charter boundary; historical PMFS used strict >. Equality audited separately.
                if(concentration[i]>=THRESHOLD)hit[i]++;
            }
        }
        char extra;if(in.read(&extra,1))throw std::runtime_error("extra trajectory records");
        for(size_t i=0;i<n;i++)if(measuredHitProb.occupancy[i]==Occupancy::Free){
            hit[i]/=settings.iterationsToRecord;meanC[i]=sumC[i]/settings.iterationsToRecord;nonzeroFraction[i]/=settings.iterationsToRecord;
        }
        return hit;
    }
};
'''+s[end:]
s=s.replace('if(argc!=5)', '''if(argc==2&&std::string(argv[1])=="--selftest"){
            std::cout<<"age_s,distance_m,concentration_ppm\\n"<<std::setprecision(17);
            for(double age:{0.,0.2,1.,10.,40.})for(float d:{0.f,0.05f,0.1f,0.2f}){
                float sigma=std::sqrt(SIGMA0*SIGMA0+GAMMA*age);
                std::cout<<age<<','<<d<<','<<single(sigma,{0,0,0},{d,0,0})<<'\\n';
            }
            float tiny=1e-4f; if(!(single(tiny,{0,0,0},{0,0,0})>0&&single(tiny,{0,0,0},{0.01f,0,0})==0))throw std::runtime_error("tiny sigma support");
            return 0;
        }
        if(argc!=6)''')
s=s.replace('if(arm!="native"&&arm!="oracle2d"&&arm!="oracle3d")','if(arm!="g2"&&arm!="g3")')
a=s.index('        std::unique_ptr<CFD> cfd;');b=s.index('        SimulationSettings settings;',a)
s=s[:a]+'''        auto volume=std::make_unique<Volume>(cfg.at("occupancy3d"));
'''+s[b:]
a=s.index('            auto hit=arm=="oracle3d"?');b=s.index('            long double logScore=0;',a)
s=s[:a]+'''            auto hit=replay.gaussian(fs::path(argv[5])/"trajectories"/(row.at("candidate_id")+".trajbin"),*volume,num(cfg,"sensor_z"));
'''+s[b:]
s=s.replace('fs::create_directories(out/"maps");', '''fs::create_directories(out/"concentration");fs::create_directories(out/"maps");
        std::ofstream diagnostics(out/"gaussian_diagnostics.csv");diagnostics<<"candidate_id,total_active,max_active,query_count,contribution_count\\n";''')
s=s.replace('            scores<<row.at("candidate_id")', '''            diagnostics<<row.at("candidate_id")<<','<<replay.totalActive<<','<<replay.maxActive<<','<<replay.queryCount<<','<<replay.contributionCount<<'\\n';
            for(auto item:{std::make_pair("mean",&replay.meanC),std::make_pair("max",&replay.maxC),std::make_pair("nonzero_fraction",&replay.nonzeroFraction)}){
                std::ofstream stream(out/"concentration"/(row.at("candidate_id")+"_"+item.first+".f32"),std::ios::binary);
                stream.write((const char*)item.second->data(),item.second->size()*sizeof(float));
            }
            scores<<row.at("candidate_id")''')
(root/'research/p3t_world_model_v0/gaussian_saved_centers.cpp').write_text(s)
