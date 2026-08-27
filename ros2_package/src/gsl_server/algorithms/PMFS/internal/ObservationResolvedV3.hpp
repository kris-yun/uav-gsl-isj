#pragma once

// Header-only runtime core for
// CG-PC-CTT V3 Observation-Resolved Reversible Update.
//
// This module is deliberately independent of ROS, PMFS posterior state and
// source truth.  The Simulations.cpp adapter supplies only:
//   probability[source][keyed_member][completed_event]
//   observed hit/miss, completed block ids
//   geometry-only persistent-carrier rectangles
//   fixed geometry/design prior mass.
//
// First four members calibrate observation resolution. Last four score the
// observed outcome. No online p-value, learned temperature, bridge artifact,
// House-specific threshold, or same-window native posterior is accepted.

#include <Eigen/Dense>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace GSL::PMFS_internal::v3_orr
{
    inline constexpr int kCalibrationMembers = 4;
    inline constexpr double kEmpiricalProbabilityEps = 0.5 / 201.0; // T=200 frequency resolution

    struct Result
    {
        bool released = false;
        std::string reason;
        std::vector<long double> candidateMass;
        std::vector<int> componentId;
        int resolutionCells = 0;
        int resolvedEdges = 0;
        int unresolvedEdges = 0;
        int nuisanceRank = 0;
        double nuisanceTolerance = 0.0;
        int evenEvents = 0;
        int evenHits = 0;
        int oddEvents = 0;
        int oddHits = 0;
    };

    inline double normalQuantile(double probability)
    {
        const double p = std::clamp(probability, 1e-12, 1.0 - 1e-12);
        constexpr double a1=-3.969683028665376e+01,a2=2.209460984245205e+02,a3=-2.759285104469687e+02;
        constexpr double a4=1.383577518672690e+02,a5=-3.066479806614716e+01,a6=2.506628277459239e+00;
        constexpr double b1=-5.447609879822406e+01,b2=1.615858368580409e+02,b3=-1.556989798598866e+02;
        constexpr double b4=6.680131188771972e+01,b5=-1.328068155288572e+01;
        constexpr double c1=-7.784894002430293e-03,c2=-3.223964580411365e-01,c3=-2.400758277161838e+00;
        constexpr double c4=-2.549732539343734e+00,c5=4.374664141464968e+00,c6=2.938163982698783e+00;
        constexpr double d1=7.784695709041462e-03,d2=3.224671290700398e-01,d3=2.445134137142996e+00,d4=3.754408661907416e+00;
        constexpr double low=0.02425, high=1.0-low;
        if (p < low)
        {
            const double q=std::sqrt(-2.0*std::log(p));
            return (((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6)/((((d1*q+d2)*q+d3)*q+d4)*q+1.0);
        }
        if (p > high)
        {
            const double q=std::sqrt(-2.0*std::log(1.0-p));
            return -(((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6)/((((d1*q+d2)*q+d3)*q+d4)*q+1.0);
        }
        const double q=p-0.5, r=q*q;
        return (((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+a6)*q/(((((b1*r+b2)*r+b3)*r+b4)*r+b5)*r+1.0);
    }

    inline double logMeanExp(const std::vector<double>& values)
    {
        if (values.empty()) throw std::invalid_argument("empty logMeanExp");
        const double maximum=*std::max_element(values.begin(),values.end());
        if (!std::isfinite(maximum)) return maximum;
        double sum=0.0;
        for (double v:values) sum += std::exp(v-maximum);
        return maximum + std::log(sum/static_cast<double>(values.size()));
    }

    inline std::vector<double> normalMidRanks(const std::vector<double>& values)
    {
        const size_t n=values.size();
        if (n<2) throw std::invalid_argument("need >=2 rank values");
        for (double v:values) if (!std::isfinite(v)) throw std::invalid_argument("nonfinite rank value");
        std::vector<size_t> order(n); std::iota(order.begin(),order.end(),0);
        std::stable_sort(order.begin(),order.end(),[&](size_t a,size_t b){return values[a]>values[b];});
        std::vector<double> rank(n,0.0), result(n,0.0);
        size_t begin=0;
        while (begin<n)
        {
            size_t end=begin+1;
            while (end<n && std::abs(values[order[end]]-values[order[begin]]) <=
                    1e-12*(1.0+std::abs(values[order[begin]]))) ++end;
            const double mid=0.5*(static_cast<double>(begin+1)+static_cast<double>(end));
            for (size_t k=begin;k<end;++k) rank[order[k]]=mid;
            begin=end;
        }
        for (size_t i=0;i<n;++i)
        {
            const double p=1.0-(rank[i]-0.5)/static_cast<double>(n);
            result[i]=normalQuantile(p);
        }
        return result;
    }

    inline bool adjacent(const std::array<int,4>& a,const std::array<int,4>& b)
    {
        const int ax1=a[0]+a[2], ay1=a[1]+a[3], bx1=b[0]+b[2], by1=b[1]+b[3];
        const int dx=std::max({b[0]-ax1,a[0]-bx1,0});
        const int dy=std::max({b[1]-ay1,a[1]-by1,0});
        return dx==0 && dy==0;
    }

    class DisjointSet
    {
        std::vector<int> parent;
    public:
        explicit DisjointSet(int n):parent(static_cast<size_t>(n)){std::iota(parent.begin(),parent.end(),0);}
        int find(int a){while(parent[a]!=a){parent[a]=parent[parent[a]];a=parent[a];}return a;}
        void unite(int a,int b){a=find(a);b=find(b);if(a!=b)parent[b]=a;}
    };

    inline Eigen::MatrixXd nuisancePrecision(
        const std::vector<std::vector<std::vector<double>>>& p,
        int memberCount,double& tolerance,int& rank)
    {
        const int S=static_cast<int>(p.size());
        if (S<=0 || memberCount<3) throw std::invalid_argument("invalid calibration ensemble");
        const int E=static_cast<int>(p[0][0].size());
        Eigen::MatrixXd cov=Eigen::MatrixXd::Zero(E,E);
        long long count=0;
        for (int s=0;s<S;++s)
            for (int m=0;m<memberCount;++m)
                for (int h=m+1;h<memberCount;++h)
                {
                    Eigen::VectorXd d(E);
                    for (int e=0;e<E;++e) d(e)=p[s][m][e]-p[s][h][e];
                    cov.noalias() += 0.5*(d*d.transpose());
                    ++count;
                }
        cov/=static_cast<double>(std::max<long long>(count,1)); cov=0.5*(cov+cov.transpose());
        Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> solver(cov);
        if (solver.info()!=Eigen::Success) throw std::runtime_error("V3 nuisance eigensolver failed");
        const auto val=solver.eigenvalues(); const auto vec=solver.eigenvectors();
        const double lmax=std::max(val(E-1),0.0);
        tolerance=static_cast<double>(std::max(E,1))*std::numeric_limits<double>::epsilon()*std::max(lmax,1.0)*100.0;
        Eigen::VectorXd inv=Eigen::VectorXd::Zero(E); rank=0;
        for (int i=0;i<E;++i) if (val(i)>tolerance){inv(i)=1.0/val(i);++rank;}
        Eigen::MatrixXd precision=vec*inv.asDiagonal()*vec.transpose();
        return 0.5*(precision+precision.transpose());
    }

    inline std::pair<double,double> pairCross(
        const std::vector<std::vector<double>>& d,const Eigen::MatrixXd& precision)
    {
        const int M=static_cast<int>(d.size()), E=static_cast<int>(d[0].size());
        auto calc=[&](int omitted)
        {
            int mm=0; Eigen::VectorXd total=Eigen::VectorXd::Zero(E); double self=0.0;
            for (int m=0;m<M;++m) if (m!=omitted)
            {
                Eigen::Map<const Eigen::VectorXd> v(d[m].data(),E);
                total+=v; self+=v.dot(precision*v); ++mm;
            }
            if (mm<2) throw std::runtime_error("V3 pair LOO has <2 members");
            return (total.dot(precision*total)-self)/static_cast<double>(mm*(mm-1));
        };
        const double observed=calc(-1); double loo=std::numeric_limits<double>::infinity();
        for (int r=0;r<M;++r) loo=std::min(loo,calc(r));
        return {observed,loo};
    }

    inline void projectToComponents(std::vector<double>& values,const std::vector<int>& component,
                                    const std::vector<long double>& prior)
    {
        const int S=static_cast<int>(values.size());
        const int maxComponent=*std::max_element(component.begin(),component.end());
        for (int c=0;c<=maxComponent;++c)
        {
            long double mass=0.0L, weighted=0.0L;
            for (int s=0;s<S;++s) if (component[s]==c){mass+=prior[s];weighted+=prior[s]*values[s];}
            if (!(mass>0.0L)) throw std::runtime_error("V3 zero-mass resolution cell");
            const double mean=static_cast<double>(weighted/mass);
            for (int s=0;s<S;++s) if (component[s]==c) values[s]=mean;
        }
    }

    inline Result compute(const std::vector<std::vector<std::vector<double>>>& probability,
                          const std::vector<unsigned char>& observedHit,
                          const std::vector<std::uint64_t>& blockId,
                          const std::vector<std::array<int,4>>& rectangles,
                          std::vector<long double> priorMass)
    {
        Result out;
        const int S=static_cast<int>(probability.size());
        if (S<2) throw std::invalid_argument("V3 requires >=2 sources");
        const int M=static_cast<int>(probability[0].size());
        const int E=static_cast<int>(probability[0][0].size());
        if (M<8) throw std::invalid_argument("V3 direct contract requires >=8 keyed members");
        if (static_cast<int>(observedHit.size())!=E || static_cast<int>(blockId.size())!=E ||
            static_cast<int>(rectangles.size())!=S || static_cast<int>(priorMass.size())!=S)
            throw std::invalid_argument("V3 input shape mismatch");
        long double priorTotal=0.0L;
        for (auto q:priorMass){if (!(q>=0.0L) || !std::isfinite(static_cast<double>(q))) throw std::invalid_argument("invalid prior"); priorTotal+=q;}
        if (!(priorTotal>0.0L)) throw std::invalid_argument("empty prior");
        for (auto& q:priorMass) q/=priorTotal;

        double covTol=0.0; int nuisanceRank=0;
        const Eigen::MatrixXd precision=nuisancePrecision(probability,kCalibrationMembers,covTol,nuisanceRank);
        out.nuisanceRank=nuisanceRank; out.nuisanceTolerance=covTol;

        DisjointSet dsu(S);
        for (int i=0;i<S;++i) for (int j=i+1;j<S;++j)
        {
            if (!adjacent(rectangles[i],rectangles[j])) continue;
            std::vector<std::vector<double>> d(static_cast<size_t>(kCalibrationMembers),std::vector<double>(static_cast<size_t>(E),0.0));
            for (int m=0;m<kCalibrationMembers;++m) for (int e=0;e<E;++e)
                d[m][e]=probability[i][m][e]-probability[j][m][e];
            const auto [strength,loo]=pairCross(d,precision);
            const double numericalTol=64.0*std::numeric_limits<double>::epsilon()*(1.0+std::abs(strength)+std::abs(loo));
            if (strength>numericalTol && loo>numericalTol) ++out.resolvedEdges;
            else {++out.unresolvedEdges; dsu.unite(i,j);}
        }
        std::vector<int> root(S), labels; labels.reserve(S); out.componentId.resize(S);
        for (int s=0;s<S;++s)
        {
            root[s]=dsu.find(s); auto it=std::find(labels.begin(),labels.end(),root[s]);
            if (it==labels.end()){labels.push_back(root[s]);out.componentId[s]=static_cast<int>(labels.size()-1);}
            else out.componentId[s]=static_cast<int>(std::distance(labels.begin(),it));
        }
        out.resolutionCells=static_cast<int>(labels.size());

        std::array<std::vector<double>,2> foldZ;
        for (int parity=0;parity<2;++parity)
        {
            std::vector<int> event; int hits=0;
            for (int e=0;e<E;++e) if (static_cast<int>(blockId[e]%2U)==parity){event.push_back(e);hits+=observedHit[e]?1:0;}
            if (parity==0){out.evenEvents=static_cast<int>(event.size());out.evenHits=hits;}
            else {out.oddEvents=static_cast<int>(event.size());out.oddHits=hits;}
            if (event.size()<2){out.reason="NEED_BOTH_FOLDS";return out;}
            if (hits==0 || hits==static_cast<int>(event.size())){out.reason="NON_IDENTIFYING_FOLD";return out;}
            std::vector<double> score(static_cast<size_t>(S),0.0);
            for (int s=0;s<S;++s)
            {
                std::vector<double> member;
                for (int m=kCalibrationMembers;m<M;++m)
                {
                    double ll=0.0;
                    for (int e:event)
                    {
                        const double p=std::clamp(probability[s][m][e],kEmpiricalProbabilityEps,1.0-kEmpiricalProbabilityEps);
                        ll += observedHit[e] ? std::log(p) : std::log1p(-p);
                    }
                    member.push_back(ll);
                }
                score[s]=logMeanExp(member);
            }
            projectToComponents(score,out.componentId,priorMass);
            foldZ[parity]=normalMidRanks(score);
        }

        std::vector<double> evidence(static_cast<size_t>(S),0.0);
        for (int s=0;s<S;++s) evidence[s]=(foldZ[0][s]+foldZ[1][s])/std::sqrt(2.0);
        projectToComponents(evidence,out.componentId,priorMass);
        std::vector<double> logMass(static_cast<size_t>(S),0.0); double maximum=-INFINITY;
        for (int s=0;s<S;++s)
        {
            logMass[s]=std::log(std::max(priorMass[s],std::numeric_limits<long double>::min()))+evidence[s];
            maximum=std::max(maximum,logMass[s]);
        }
        long double total=0.0L; out.candidateMass.assign(static_cast<size_t>(S),0.0L);
        for (int s=0;s<S;++s){out.candidateMass[s]=std::exp(logMass[s]-maximum);total+=out.candidateMass[s];}
        if (!(total>0.0L) || !std::isfinite(static_cast<double>(total))) throw std::runtime_error("V3 posterior normalization failed");
        for (auto& q:out.candidateMass) q/=total;
        out.released=true; out.reason="accepted";
        return out;
    }
}
