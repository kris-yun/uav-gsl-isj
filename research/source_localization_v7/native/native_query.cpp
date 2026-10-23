// Read-only C++17 port of GADEN Simulation::{CheckLineOfSight,
// CalculateConcentration, ConcentrationAtCenter}. No new transport model.
// Original upstream: MAPIRlab/gaden_core; source hashes are archived separately.
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>
#ifdef _WIN32
#define API extern "C" __declspec(dllexport)
#else
#define API extern "C"
#endif
struct Vec { float x,y,z; };
static Vec add(Vec a,Vec b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
static Vec sub(Vec a,Vec b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
static Vec mul(Vec a,float b){return {a.x*b,a.y*b,a.z*b};}
static float sq(Vec a){return a.x*a.x+a.y*a.y+a.z*a.z;}
static int cell_at(Vec p,const uint8_t* grid,const int* d,Vec o,float c){
  int x=int((p.x-o.x)/c),y=int((p.y-o.y)/c),z=int((p.z-o.z)/c);
  if(x<0||y<0||z<0||x>=d[0]||y>=d[1]||z>=d[2])return 3;
  return grid[x+y*d[0]+z*d[0]*d[1]];
}
static bool los(Vec start,Vec end,const uint8_t* grid,const int* d,Vec o,float c){
  if(cell_at(start,grid,d,o,c)!=0||cell_at(end,grid,d,o,c)!=0)return false;
  Vec v=sub(end,start);float distance=std::sqrt(sq(v));
  if(distance==0)return true;
  v=mul(v,1.0f/distance);int steps=int(distance/c);
  // Native loop has no interior point when distance < cell size.
  if(steps<2)return true;
  float increment=distance/steps;
  for(int i=1;i<steps;i++)if(cell_at(add(start,mul(v,increment*i)),grid,d,o,c)!=0)return false;
  return true;
}
API int query_many(const float* fil,int n,const float* pts,int m,const uint8_t* grid,
                   const int* d,const float* origin,float cell,float moles,float air,
                   float* out,uint8_t* valid){
  if(n<0||m<0||!std::isfinite(moles)||!std::isfinite(air)||air<=0)return -1;
  Vec o={origin[0],origin[1],origin[2]};
  constexpr float pi_cubed=float(3.14159265358979323846*3.14159265358979323846*3.14159265358979323846);
  for(int j=0;j<m;j++){
    Vec p={pts[3*j],pts[3*j+1],pts[3*j+2]};
    valid[j]=(cell_at(p,grid,d,o,cell)==0);
    if(!valid[j]){out[j]=NAN;continue;}
    float concentration=0;
    for(int i=0;i<n;i++){
      Vec f={fil[4*i],fil[4*i+1],fil[4*i+2]};float sigma=fil[4*i+3];
      float distance_sqr=sq(sub(f,p)),limit=sigma*3/100.f;
      if(distance_sqr<limit*limit&&los(p,f,grid,d,o,cell)){
        float target=moles/(std::sqrt(8*pi_cubed)*sigma*sigma*sigma);
        float center=float(1e6*target/air);
        float distance_cm=100*std::sqrt(distance_sqr);
        float ppm=center*std::exp(-(distance_cm*distance_cm)/(2*sigma*sigma));
        concentration+=ppm;
      }
    }
    out[j]=concentration;
  }
  return 0;
}

// Frozen M1 inference kernels. Inputs are only the observed paired window,
// actual timestamps and frozen TRAIN parameters; no source/world identifier.
API int m1_features(const double* raw,const double* t,int n,const double* specs,int f,
                    double* even,double* odd){
  if(n<2||t[n-1]<=t[0])return -1;
  std::vector<double> L(n),R(n),tw(n);
  for(int i=0;i<n;i++){L[i]=std::log1p(std::fmax(raw[2*i],0));R[i]=std::log1p(std::fmax(raw[2*i+1],0));}
  tw[0]=(t[1]-t[0])/2;tw[n-1]=(t[n-1]-t[n-2])/2;
  for(int i=1;i<n-1;i++)tw[i]=(t[i+1]-t[i-1])/2;
  double sum=0;for(auto w:tw)sum+=w;
  *even=0;for(int i=0;i<n;i++){tw[i]/=sum;*even+=tw[i]*(L[i]+R[i])/2;}
  for(int k=0;k<f;k++){
    const double* s=specs+5*k;double lag=s[0],decay=s[1],inhibit=s[2],bias=s[3];
    if(s[4]==0){odd[k]=0;for(int i=0;i<n;i++)odd[k]+=tw[i]*(L[i]-R[i])/2;continue;}
    std::vector<double> w(n),wd(n);double sw=0,swd=0;
    for(int i=0;i<n;i++){
      double dt=(i==0)?t[1]-t[0]:t[i]-t[i-1];
      w[i]=std::exp(std::fmin((t[i]-t[n-1])/decay,0))*dt;
      wd[i]=(t[i]<=t[n-1]-lag+1e-10)?std::exp(std::fmin((t[i]-(t[n-1]-lag))/decay,0))*dt:0;
      sw+=w[i];swd+=wd[i];
    }
    if(swd==0)return -2;
    double direct=bias,mirror=bias;
    for(int i=0;i<n;i++){
      double f1=w[i]/sw-inhibit*wd[i]/swd,f2=-w[i]/sw;
      direct+=L[i]*f1+R[i]*f2;mirror+=R[i]*f1+L[i]*f2;
    }
    odd[k]=std::fmax(direct,0)-std::fmax(mirror,0);
  }
  return 0;
}
API int m1_symbol(double even,const double* odd,double theta_even,const double* theta_odd,
                   const int* selected,int k){
  int code=(even>theta_even),mul=2;
  for(int i=0;i<k;i++){
    int f=selected[i];int q=int(odd[f]>theta_odd[f])+1-int(odd[f]<-theta_odd[f]);
    code+=mul*q;mul*=3;
  }
  return code;
}
API int raw_joint_symbol(const double* raw,int n,const double* centers,int alphabet,double scale){
  int best=0;double min_distance=INFINITY;
  for(int k=0;k<alphabet;k++){
    double distance=0;
    for(int i=0;i<n;i++){double d=std::log1p(std::fmax(raw[i],0))/scale-centers[k*n+i];distance+=d*d;}
    if(distance<min_distance){min_distance=distance;best=k;}
  }
  return best;
}
API int categorical_posterior(const double* table,int sources,int alphabet,int symbol,double* posterior){
  if(symbol<0||symbol>=alphabet)return -1;
  double total=0;for(int s=0;s<sources;s++)total+=table[s*alphabet+symbol];
  if(total<=0)return -2;
  for(int s=0;s<sources;s++)posterior[s]=table[s*alphabet+symbol]/total;
  return 0;
}
