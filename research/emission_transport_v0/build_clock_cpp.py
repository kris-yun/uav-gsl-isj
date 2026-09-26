"""Compile the original cyclic-table class with deterministic sentinel input.

This creates no GADEN RNG samples/trajectories. The stubs deliberately replace
GaussianRandom with 0,1,...,999 solely to test original indexing and reuse.
"""
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument("--mathutils", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
a = p.parse_args()
source = a.mathutils.read_text()
start = source.index("    template <int Size>")
end = source.index("    };", start) + len("    };")
cls = source[start:end]
prefix = r'''
#include <array>
#include <cstdint>
#include <cmath>
#include <cfloat>
#include <iostream>
#include <iomanip>
static int sentinel=0;
float uniformRandom(float, float) {return 0;}
float GaussianRandom(float, float) {return float((sentinel++)%1000);}
'''
suffix = r'''
int main(){
    PrecalculatedGaussian<1000> clock;
    std::array<float,1003> draws;
    for(auto &v:draws) v=clock.nextValue(0,1);
    bool reuse=true;
    for(int k=0;k<3;k++) reuse &= draws[k]==draws[1000+k];
    float current=0, lastSave=-FLT_MAX, lastWind=0, release=0;
    int snap=0, step=0, wind=0, births=0, firstStep=0, lastStep=0;
    float first=0,last=0;
    while(current<300.f){
        release += 7.f*.1f; births += std::floor(release);
        release -= std::floor(release);
        if(current>lastSave+.5f){
            if(snap==100){first=current;firstStep=step;}
            if(snap==550){last=current;lastStep=step;}
            snap++;lastSave=current;
        }
        if(current>lastWind+1.f){wind++;if(wind>10)wind=1;lastWind=current;}
        current+=.1f;step++;
    }
    float sigma=10;
    for(int i=0;i<3000;i++)sigma+=15.f/(2*sigma)*.1f;
    std::cout<<std::setprecision(17)
      <<"{\"purpose\":\"DETERMINISTIC_SENTINEL_NO_GADEN_SAMPLE\","
      <<"\"original_template_period_1000\":"<<(reuse?"true":"false")<<","
      <<"\"snapshot_count\":"<<snap<<",\"first_seconds\":"<<first
      <<",\"last_seconds\":"<<last<<",\"first_step\":"<<firstStep
      <<",\"last_step\":"<<lastStep<<",\"births\":"<<births
      <<",\"sigma_after_3000_moves_cm\":"<<sigma<<"}"<<std::endl;
    return reuse && snap==566 ? 0 : 1;
}
'''
a.out.write_text(prefix + cls + suffix, encoding="utf-8", newline="\n")
