
#include <array>
#include <cstdint>
#include <cmath>
#include <cfloat>
#include <iostream>
#include <iomanip>
static int sentinel=0;
float uniformRandom(float, float) {return 0;}
float GaussianRandom(float, float) {return float((sentinel++)%1000);}
    template <int Size>
    class PrecalculatedGaussian
    {
    public:
        PrecalculatedGaussian()
        {
            m_index = uniformRandom(0, Size);
            for (size_t i = 0; i < Size; i++)
                m_precalculatedTable[i] = GaussianRandom(0, 1);
        }

        float nextValue(float mean, float stdev)
        {
            m_index = (m_index + 1) % Size;
            return mean + stdev * m_precalculatedTable[m_index];
        }

    private:
        uint16_t m_index;
        std::array<float, Size> m_precalculatedTable;
    };
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
