"""Derive isolated center-export instrumentation; original frozen CPP remains intact."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
s=(root/'research/pmfs3d_r1/oracle_forward.cpp').read_text()
s=s.replace('using Simulations::Simulations;', '''using Simulations::Simulations;
    mutable std::ofstream trajectory;
    mutable double embedZ=0;
    void emit2(const std::vector<Filament>& active,const std::vector<double>& ages) const {
        uint32_t count=active.size();trajectory.write((const char*)&count,4);
        for(size_t j=0;j<active.size();j++){
            float p[3]={active[j].position.x,active[j].position.y,float(embedZ)};
            trajectory.write((const char*)p,12);trajectory.write((const char*)&ages[j],8);
        }
    }
    void emit3(const std::vector<std::array<float,3>>& active,const std::vector<double>& ages) const {
        uint32_t count=active.size();trajectory.write((const char*)&count,4);
        for(size_t j=0;j<active.size();j++){
            trajectory.write((const char*)active[j].data(),12);trajectory.write((const char*)&ages[j],8);
        }
    }''')
old='''        simulateSourceInPosition(source,hit,true,settings.iterationsToRecord,settings.deltaTime,settings.noiseSTDev,nullptr,&rng);'''
new='''        // Exact Native loop; movement/collision helpers remain in the frozen library.
        std::vector<Filament> active,next;
        std::vector<double> ages,nextAges;
        std::vector<uint16_t> updated(hit.size(),0);uint64_t draw=0;
        const auto& meta=measuredHitProb.metadata;
        auto release=[&](){for(int j=0;j<5;j++){active.push_back({source.getPoint()});ages.push_back(0);}};
        bool stable=false;int warm=0;
        while(warm<settings.minWarmupIterations||(!stable&&warm<settings.maxWarmupIterations)){
            release();next.clear();nextAges.clear();
            for(size_t j=0;j<active.size();j++){
                auto f=active[j];auto ij=meta.coordinatesToIndices(f.position.x,f.position.y);
                moveFilament(f,ij,settings.deltaTime*2,settings.noiseSTDev,&rng,draw);
                if(filamentIsOutside(f))stable=true;
                else{next.push_back(f);nextAges.push_back(ages[j]+settings.deltaTime*2);}
            }
            active.swap(next);ages.swap(nextAges);warm++;
        }
        for(int t=1;t<=settings.iterationsToRecord;t++){
            release();emit2(active,ages);next.clear();nextAges.clear();
            for(size_t j=0;j<active.size();j++){
                auto f=active[j];auto ij=meta.coordinatesToIndices(f.position.x,f.position.y);auto index=meta.indexOf(ij);
                if(updated[index]<t){hit[index]++;updated[index]=t;}
                moveFilament(f,ij,settings.deltaTime,settings.noiseSTDev,&rng,draw);
                if(!filamentIsOutside(f)){next.push_back(f);nextAges.push_back(ages[j]+settings.deltaTime);}
            }
            active.swap(next);ages.swap(nextAges);
        }
        for(size_t i=0;i<hit.size();i++)if(measuredHitProb.occupancy[i]==Occupancy::Free)hit[i]/=settings.iterationsToRecord;'''
assert old in s;s=s.replace(old,new)
s=s.replace('using Pos=std::array<float,3>;std::vector<Pos> active,next;', 'using Pos=std::array<float,3>;std::vector<Pos> active,next;std::vector<double> ages,nextAges;')
s=s.replace('if(volume.free(p)) active.push_back(p);','if(volume.free(p)){active.push_back(p);ages.push_back(0);}')
s=s.replace('release();next.clear();','release();next.clear();nextAges.clear();')
old='for(auto p:active){advance(p,settings.deltaTime*2);auto ij=meta.coordinatesToIndices(p[0],p[1]);if(!volume.inside(p)||!meta.indicesInBounds(ij)) stable=true;else next.push_back(p);}'
new='for(size_t j=0;j<active.size();j++){auto p=active[j];advance(p,settings.deltaTime*2);auto ij=meta.coordinatesToIndices(p[0],p[1]);if(!volume.inside(p)||!meta.indicesInBounds(ij)) stable=true;else{next.push_back(p);nextAges.push_back(ages[j]+settings.deltaTime*2);}}'
assert old in s;s=s.replace(old,new)
s=s.replace('active.swap(next);warm++;','active.swap(next);ages.swap(nextAges);warm++;')
s=s.replace('for(auto p:active) {','emit3(active,ages);for(size_t j=0;j<active.size();j++) {auto p=active[j];')
s=s.replace('if(volume.inside(p)&&meta.indicesInBounds(ij)) next.push_back(p);','if(volume.inside(p)&&meta.indicesInBounds(ij)){next.push_back(p);nextAges.push_back(ages[j]+settings.deltaTime);}')
s=s.replace('}active.swap(next);','}active.swap(next);ages.swap(nextAges);')
s=s.replace('fs::create_directories(out/"maps");','fs::create_directories(out/"trajectories");fs::create_directories(out/"maps");')
s=s.replace('            auto hit=arm=="oracle3d"?', '''            replay.embedZ=num(cfg,"sensor_z");
            replay.trajectory.open(out/"trajectories"/(row.at("candidate_id")+".trajbin"),std::ios::binary);
            auto hit=arm=="oracle3d"?''')
s=s.replace('            long double logScore=0;','            replay.trajectory.close();\n            long double logScore=0;')
(root/'research/p3t_world_model_v0/center_export.cpp').write_text(s)
