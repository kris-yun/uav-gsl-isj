from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4
import numpy as np
from scipy.optimize import linprog, brentq
from scipy.special import rel_entr
from scipy.sparse import lil_matrix
from ..m3_codebook import CorruptionChannel, binary_words


def _tv_extreme_expectation(p, values, radius, maximize=True):
    """Exact finite TV-ball expectation by moving probability mass."""
    p=np.asarray(p,float).copy(); values=np.asarray(values,float)
    signed=values if maximize else -values
    order=np.argsort(signed); low=0; high=len(order)-1; budget=float(radius)
    while low<high and budget>1e-14:
        i,j=int(order[low]),int(order[high])
        amount=min(budget,p[i],1-p[j])
        p[i]-=amount;p[j]+=amount;budget-=amount
        if p[i]<=1e-14:low+=1
        if p[j]>=1-1e-14:high-=1
    return float(p@values)


@dataclass
class RobustTest:
    phi: np.ndarray
    observed_words: np.ndarray
    neighborhoods: list
    alpha: float
    power: float
    null_risk_bound: float
    alternative_power_bound: float
    status: str
    model_version: str = "v1"

    def rejection_probability(self, word):
        word = np.asarray(word, dtype=int)
        matches = np.flatnonzero(np.all(self.observed_words == word, axis=1))
        if len(matches) != 1:
            raise ValueError("Observed word is outside the preregistered alphabet")
        return float(self.phi[matches[0]])


def solve_robust_test(null_distributions, alternative_distributions, channel=None,
                      alpha=0.05, null_radius=0.0, alternative_radius=0.0,
                      model_version="v1"):
    """Finite LP with exact corruption constraints and conservative TV bounds.

    Nulls and alternatives have shape [hypothesis,2**L]. Every declared
    mechanism is constrained, not just the most likely one. Auxiliary range
    variables make the TV bound exact for a constant randomized test. For
    general tests the range-times-TV bound is conservative: this LP does not
    claim globally optimal power over the exact TV ambiguity set. At zero
    radius the finite corruption-channel optimization is exact.
    """
    null = np.atleast_2d(np.asarray(null_distributions, float))
    alt = np.atleast_2d(np.asarray(alternative_distributions, float))
    k = null.shape[1]
    length = int(round(np.log2(k)))
    if 2**length != k or alt.shape[1] != k or len(alt) == 0:
        raise ValueError("Distribution support must be a common nonempty binary block")
    for p in (null, alt):
        if np.any(p < 0) or not np.all(np.isfinite(p)) or not np.allclose(p.sum(1),1):
            raise ValueError("Invalid hypothesis probabilities")
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    nr = np.broadcast_to(np.asarray(null_radius,float), (len(null),))
    ar = np.broadcast_to(np.asarray(alternative_radius,float), (len(alt),))
    if np.any(nr < 0) or np.any(nr > 1) or np.any(ar < 0) or np.any(ar > 1):
        raise ValueError("TV radii must lie in [0,1]")
    channel = CorruptionChannel() if channel is None else channel
    observed, neighborhoods = channel.neighborhoods(length)
    j = len(observed)
    u, v, beta = j, j+k, j+2*k
    umax, umin, vmax, vmin = beta+1, beta+2, beta+3, beta+4
    nvars = beta+5
    nrows = 2*sum(map(len,neighborhoods)) + 4*k + len(null)+len(alt)
    A = lil_matrix((nrows,nvars),dtype=float)
    b = np.zeros(nrows)
    row = 0
    for c, neighbors in enumerate(neighborhoods):
        for y in neighbors:
            A[row,y], A[row,u+c] = 1,-1
            row += 1
            A[row,v+c], A[row,y] = 1,-1
            row += 1
        A[row,u+c], A[row,umax] = 1,-1
        row += 1
        A[row,umin], A[row,u+c] = 1,-1
        row += 1
        A[row,v+c], A[row,vmax] = 1,-1
        row += 1
        A[row,vmin], A[row,v+c] = 1,-1
        row += 1
    for prob, radius in zip(null,nr):
        A[row,u:u+k] = prob
        A[row,umax], A[row,umin] = radius,-radius
        b[row] = alpha
        row += 1
    for prob, radius in zip(alt,ar):
        A[row,v:v+k] = -prob
        A[row,vmax], A[row,vmin], A[row,beta] = radius,-radius,1
        row += 1
    objective = np.zeros(nvars)
    objective[beta] = -1
    solution = linprog(objective,A_ub=A.tocsr(),b_ub=b,bounds=(0,1),method="highs")
    if not solution.success:
        raise RuntimeError(f"Counterevidence LP failed: {solution.message}")
    phi = np.clip(solution.x[:j],0,1)
    upper = np.array([phi[index].max() for index in neighborhoods])
    lower = np.array([phi[index].min() for index in neighborhoods])
    risk = max(_tv_extreme_expectation(p,upper,r) for p,r in zip(null,nr))
    power = min(_tv_extreme_expectation(p,lower,r,False) for p,r in zip(alt,ar))
    if risk > alpha+2e-7:
        raise RuntimeError("LP certificate failed independent risk recomputation")
    return RobustTest(phi,observed,neighborhoods,float(alpha),float(solution.x[beta]),
                      min(1,risk),max(0,power),"model_and_MC_bound",str(model_version))


class RiskLedger:
    """Anytime budget for one composite-source null test per committed block."""
    def __init__(self, total_alpha=0.05):
        if not 0 < total_alpha < 1:
            raise ValueError("total_alpha must lie in (0,1)")
        self.total_alpha = float(total_alpha)
        self.tests = []

    def next_alpha(self):
        t = len(self.tests)+1
        return self.total_alpha/(t*(t+1))

    def reserve(self, null_source, model_version):
        amount = self.next_alpha()
        self.tests.append({"index":len(self.tests)+1,"alpha":amount,
                           "null_source":int(null_source),"model_version":str(model_version),
                           "executed":False})
        return len(self.tests)-1,amount

    @property
    def spent(self):
        return float(sum(x["alpha"] for x in self.tests))


class RecoveryList:
    """Coverage list and evidence provenance, separate from probability mass."""
    def __init__(self, n_sources, eta=0.05):
        if not 0 <= eta < 1:
            raise ValueError("eta must be in [0,1)")
        self.n_sources,self.eta = int(n_sources),float(eta)
        self.active = set(range(n_sources))
        self.recently_recovered = set()
        self.model_version = None
        self.records = []

    def invalidate(self, model_version):
        changed = self.model_version is not None and str(model_version)!=self.model_version
        if changed:
            self.recently_recovered = set(range(self.n_sources)) - self.active
            self.active = set(range(self.n_sources))
            self.records.append({"event":"restore_on_model_change","model_version":str(model_version)})
        self.model_version = str(model_version)
        return changed

    def update(self, codebook, word, channel):
        self.invalidate(codebook.model_version)
        observed,neighborhoods = channel.neighborhoods(codebook.length)
        matches = np.flatnonzero(np.all(observed==np.asarray(word),axis=1))
        if len(matches)!=1:
            raise ValueError("Observed word is outside the declared alphabet")
        y=int(matches[0]); compatible=set()
        for s in range(self.n_sources):
            for e,p in enumerate(codebook.probabilities[s]):
                order=np.argsort(-p,kind="stable")
                # Inflate target coverage for MC error; if no nontrivial
                # certificate remains, retain the whole code support.
                required=min(1.0,1-self.eta+float(codebook.tv_radius[s,e]))
                count=min(len(p),int(np.searchsorted(np.cumsum(p[order]),required-1e-12))+1)
                selected=order[:count]
                if required>=1.0:
                    selected=np.arange(len(p))
                if any(y in neighborhoods[c] for c in selected):
                    compatible.add(s)
                    break
        # Each new block supersedes the scheduler list; this list is not a
        # repeated-test confidence set and is never a posterior mask.
        self.recently_recovered = compatible - self.active
        self.active = compatible
        self.records.append({"event":"block_list","model_version":codebook.model_version,
                             "compatible":sorted(compatible),"eta":self.eta})
        return sorted(compatible)


def _source_distribution(codebook, mechanism_posterior=None):
    p=codebook.probabilities
    n,e,_=p.shape
    if mechanism_posterior is None:
        weights=np.full((n,e),1/e)
    else:
        weights=np.asarray(mechanism_posterior,float)
        if weights.shape==(e,):
            weights=np.repeat(weights[None,:],n,axis=0)
        if weights.shape!=(n,e) or np.any(weights<0) or np.any(weights.sum(1)<=0):
            raise ValueError("Mechanism weights must have shape [E] or [N,E]")
        weights=weights/weights.sum(1,keepdims=True)
    return np.sum(p*weights[:,:,None],axis=1)


def joint_eig(codebook, source_posterior, mechanism_posterior=None):
    p=_source_distribution(codebook,mechanism_posterior)
    pi=np.asarray(source_posterior,float);pi=pi/pi.sum()
    marginal=pi@p
    return float(np.sum(pi[:,None]*rel_entr(p,np.maximum(marginal,1e-300))))


def minimax_channel_eig(codebook, source_posterior, channel, mechanism_posterior=None,
                        tolerance=1e-5, max_iterations=60000):
    """Minimize joint EIG over all permitted common corruption channels.

    The stochastic matrix T(y|c) is constrained to the same code neighborhoods
    as the NP planner. Mutual information is convex in T for fixed source
    prior/clean laws. Pairwise Frank-Wolfe transfers probability mass within a
    row simplex; a full row-simplex linear minimization oracle supplies the
    independently checked global optimality gap. No solver success flag is
    substituted for this certificate. This baseline does not claim robustness
    to physical model error.
    """
    p=_source_distribution(codebook,mechanism_posterior)
    pi=np.asarray(source_posterior,float);pi=pi/pi.sum()
    observed,neighborhoods=channel.neighborhoods(codebook.length)
    edges=[(c,int(y)) for c,neighbors in enumerate(neighborhoods) for y in neighbors]
    rows=np.array([c for c,y in edges]);cols=np.array([y for c,y in edges])
    if tolerance<=0 or max_iterations<1:
        raise ValueError("Positive robust-EIG tolerance and iteration budget required")
    groups=[np.flatnonzero(rows==c) for c in range(len(neighborhoods))]
    uniform=np.array([1/len(neighborhoods[c]) for c,y in edges])
    def objective(weights):
        transition=np.zeros((p.shape[1],len(observed)))
        transition[rows,cols]=weights
        q=p@transition;mix=pi@q
        qsafe=np.maximum(q,1e-300);msafe=np.maximum(mix,1e-300)
        logratio=np.log(qsafe)-np.log(msafe)[None,:]
        value=float(np.sum(pi[:,None]*q*logratio))
        derivative=p.T@(pi[:,None]*logratio)
        return value,derivative[rows,cols]
    weights=uniform.copy();interior_mix=1e-14
    for iteration in range(int(max_iterations)+1):
        value,gradient=objective(weights)
        vertex=np.zeros_like(weights)
        choices=[]
        for ids in groups:
            low=int(ids[np.argmin(gradient[ids])])
            vertex[low]=1.
            gains=weights[ids]*(gradient[ids]-gradient[low])
            high=int(ids[np.argmax(gains)])
            choices.append((float(np.max(gains)),high,low))
        fw_gap=max(0.,float(gradient@(weights-vertex)))
        # Convexity gives f(x)-f* <= FW gap; nonnegativity of mutual
        # information gives the independent lower bound f* >= 0.
        optimality_gap=min(max(0.,float(value)),fw_gap)
        feasibility=max(abs(float(weights[ids].sum())-1.) for ids in groups)
        if np.min(weights)<-1e-12 or feasibility>1e-9:
            raise RuntimeError("Robust EIG row-simplex feasibility certificate failed")
        if optimality_gap<=tolerance:
            return {"value":max(0.,float(value)),"iterations":iteration,
                    "channel_weights":weights,"allowed_edges":edges,
                    "status":"certified_finite_common_channel_convex_optimization",
                    "solver":"pairwise_frank_wolfe","frank_wolfe_gap":fw_gap,
                    "optimality_gap":optimality_gap,"optimality_tolerance":float(tolerance),
                    "lower_bound":max(0.,float(value)-fw_gap),
                    "feasibility_error":feasibility}
        if iteration==max_iterations:
            break
        gain,high,low=max(choices)
        direction=np.zeros_like(weights)
        direction[low]=weights[high];direction[high]-=weights[high]
        if gain<=1e-18:
            direction=vertex-weights
        # The objective is convex along this feasible segment. Use its
        # derivative rather than subtracting nearly equal objective values.
        cap=1.-interior_mix
        slope=lambda step:float(objective(weights+step*direction)[1]@direction)
        left=slope(0.)
        if left>=0:
            direction=vertex-weights
            left=slope(0.)
        if left>=0:
            raise RuntimeError("Robust EIG lost a descent direction before gap qualification")
        step=cap if slope(cap)<=0 else brentq(slope,0.,cap,xtol=1e-12,maxiter=100)
        weights+=step*direction
        # A tiny feasible interior mixture prevents artificial -inf gradients
        # at avoidable zero transitions. The full original-simplex gap above
        # remains the certificate, so this numerical safeguard cannot hide a
        # suboptimal solution of a modified constraint set.
        weights=(1-interior_mix)*weights+interior_mix*uniform
    raise RuntimeError(f"Robust EIG gap qualification failed: gap={optimality_gap:.6g}, "
                       f"tolerance={tolerance:.6g}, iterations={max_iterations}")


def _cluster_score(probabilities,threshold=0.08):
    """Mother-ASHT action-dependent response clusters and separation score.

    Greedy representative clustering is an explicit finite adaptation. It is
    not claimed to reproduce the paper's iid multi-stage error theorem.
    """
    representatives=[];clusters=[]
    for i,p in enumerate(probabilities):
        target=None
        for k,r in enumerate(representatives):
            distance=np.linalg.norm(np.sqrt(p)-np.sqrt(probabilities[r]))/np.sqrt(2)
            if distance<=threshold:
                target=k;break
        if target is None:
            representatives.append(i);clusters.append([i])
        else:
            clusters[target].append(i)
    if len(representatives)<2:
        return 0.0,clusters
    distances=[]
    for x,i in enumerate(representatives):
        for j in representatives[x+1:]:
            p=np.clip(probabilities[i],1e-10,1);q=np.clip(probabilities[j],1e-10,1)
            p/=p.sum();q/=q.sum()
            distances.append(.5*np.sum(rel_entr(p,q)+rel_entr(q,p)))
    return float(min(distances)),clusters


@dataclass
class Plan:
    actions: tuple
    codebook: object
    variant: str
    null_source: int
    challenge_indices: list
    score: float
    test: RobustTest | None
    risk_index: int | None
    independent_uniform: float | None
    reason: str
    action_index: int
    model_version: str
    clusters: list
    plan_id: str
    consumed: bool = False


class RobustCounterEvidencePlanner:
    def __init__(self,n_sources,channel=None,total_alpha=0.05,eta=0.05,
                 challenge_size=2,seed=0):
        self.n_sources=int(n_sources)
        self.channel=CorruptionChannel() if channel is None else channel
        self.risk=RiskLedger(total_alpha)
        self.recovery=RecoveryList(n_sources,eta)
        self.challenge_size=max(1,int(challenge_size))
        self.cursor=0
        self.rng=np.random.default_rng(seed)
        self.executed=set()
        self.executed_uids=set()
        self._owner_id=uuid4().hex
        self._issued_plan_ids=set()
        self._consumed_plan_ids=set()
        self._plan_counter=0

    def _challengers(self,posterior,h):
        if self.n_sources<2:
            raise ValueError("Counterevidence needs at least two legal candidates")
        selected=[]
        for _ in range(self.n_sources):
            s=self.cursor%self.n_sources
            self.cursor+=1
            if s!=h:
                selected.append(s);break
        ordered=list(map(int,np.argsort(-posterior)))
        # Slot one has global round-robin coverage. Remaining slots prioritize
        # restored and currently compatible candidates. Out-of-list candidates
        # retain the first-slot guarantee and are never permanently excluded.
        priority=([s for s in ordered if s in self.recovery.recently_recovered]
                  +[s for s in ordered if s in self.recovery.active]
                  +ordered)
        for s in priority:
            if len(selected)>=min(self.challenge_size,self.n_sources-1):
                break
            if int(s)!=h and int(s) not in selected:
                selected.append(int(s))
            if len(selected)>=min(self.challenge_size,self.n_sources-1):
                break
        self.recovery.recently_recovered.difference_update(selected)
        return selected

    def plan(self,codebooks,source_posterior,mechanism_posterior=None,variant="Bprime"):
        aliases={"A'":"Aprime","A'+B":"B","A'+B'":"Bprime","eig":"Aprime"}
        variant=aliases.get(variant,variant)
        if variant not in {"A","Aprime","B","Bprime","min_hamming","robust_eig","channel_eig"}:
            raise ValueError("Unknown planner variant")
        codebooks=list(codebooks)
        if not codebooks:
            raise ValueError("No action candidates")
        versions={str(book.model_version) for book in codebooks}
        if len(versions)!=1:
            raise ValueError("Mixed model versions in one action codebook batch")
        # Restore obsolete list exclusions BEFORE using the list to select
        # challengers. A new version cannot inherit old scheduling exclusions.
        self.recovery.invalidate(next(iter(versions)))
        pi=np.asarray(source_posterior,float)
        if pi.shape!=(self.n_sources,) or np.any(pi<0) or pi.sum()<=0:
            raise ValueError("Invalid source posterior")
        pi/=pi.sum();h=int(np.argmax(pi))
        challengers=self._challengers(pi,h)
        alpha=self.risk.next_alpha()
        scores=[];tests=[];clusters_by_action=[]
        for book in codebooks:
            p=_source_distribution(book,mechanism_posterior)
            cluster_score,clusters=_cluster_score(p)
            clusters_by_action.append(clusters)
            test=None
            if variant=="Bprime":
                test=solve_robust_test(book.probabilities[h],
                    book.probabilities[challengers].reshape(-1,p.shape[-1]),self.channel,alpha,
                    book.tv_radius[h],book.tv_radius[challengers].ravel(),book.model_version)
                score=max(0,test.alternative_power_bound-alpha)/book.cost
            elif variant=="A":
                # Exact variance part of native Eq.11 with confidence c=0;
                # native confidence-map and navigation remain external.
                mean_bits=p@binary_words(book.length)
                score=float(np.sum(pi[:,None]*(mean_bits-pi@mean_bits)**2))/book.cost
            elif variant=="Aprime":
                score=joint_eig(book,pi,mechanism_posterior)/book.cost
            elif variant=="B":
                score=cluster_score/book.cost
            elif variant=="robust_eig":
                score=minimax_channel_eig(book,pi,self.channel,mechanism_posterior)["value"]/book.cost
            elif variant=="channel_eig":
                # An additional simpler baseline: uniform permitted channel.
                observed,neighborhoods=self.channel.neighborhoods(book.length)
                transition=np.zeros((p.shape[-1],len(observed)))
                for c,ids in enumerate(neighborhoods):transition[c,ids]=1/len(ids)
                noisy=p@transition;mix=pi@noisy
                score=float(np.sum(pi[:,None]*rel_entr(noisy,np.maximum(mix,1e-300))))/book.cost
            else:
                words=binary_words(book.length)[np.argmax(p,axis=1)]
                score=float(min(np.count_nonzero(words[h]!=words[s]) for s in challengers))/book.cost
            scores.append(score);tests.append(test)
        if not scores:
            raise ValueError("No action candidates")
        best=int(np.argmax(scores))
        reason="max_score"
        if variant=="Bprime" and max(scores)<=1e-12:
            best=int(np.argmax([joint_eig(b,pi,mechanism_posterior)/b.cost for b in codebooks]))
            reason="no_certified_counterevidence_gain_joint_eig_fallback"
            # A constant-alpha randomized rejection conveys no source
            # information. Abstain instead of generating random repair events.
            tests[best]=None
        book=codebooks[best]
        risk_index=None;randomizer=None
        if variant=="Bprime" and tests[best] is not None:
            risk_index,_=self.risk.reserve(h,book.model_version)
            self.risk.tests[risk_index]["MC_failure_budget"]=float(book.confidence_failure_probability)
            randomizer=float(self.rng.random())
        self._plan_counter+=1
        plan_id=f"{self._owner_id}:{self._plan_counter}"
        self._issued_plan_ids.add(plan_id)
        return Plan(book.actions,book,variant,h,challengers,float(scores[best]),tests[best],
                    risk_index,randomizer,reason,best,book.model_version,clusters_by_action[best],plan_id)

    def observe(self,plan,observations,rng=None,model_version=None):
        if plan.plan_id not in self._issued_plan_ids:
            raise ValueError("Plan was not issued by this planner")
        if plan.consumed or plan.plan_id in self._consumed_plan_ids:
            raise ValueError("A plan cannot be consumed a second time, even with new observation IDs")
        if plan.risk_index is not None and self.risk.tests[plan.risk_index]["executed"]:
            raise ValueError("Risk reservation already executed; a second test requires a new plan")
        observations=list(observations)
        if len(observations)!=len(plan.actions):
            raise ValueError("Commit the whole planned block or invalidate and replan the test")
        for expected,observed in zip(plan.actions,observations):
            if observed.action != expected:
                raise ValueError("Executed action differs from the precommitted test block")
        if len({o.uid for o in observations})!=len(observations):
            raise ValueError("Duplicate observation inside committed block")
        # A valid execution attempt consumes the plan, including a stale
        # version outcome. Malformed/incomplete input raises before consuming
        # so the caller can supply the originally committed complete block.
        plan.consumed=True
        self._consumed_plan_ids.add(plan.plan_id)
        if plan.risk_index is not None:
            self.risk.tests[plan.risk_index]["consumed"]=True
        current=plan.model_version if model_version is None else str(model_version)
        if current!=plan.model_version:
            self.recovery.invalidate(current)
            return {"status":"stale_plan_invalidated","rejected":False,"trigger_replay":False,
                    "recovery_list":sorted(self.recovery.active)}
        key=tuple(o.uid for o in observations)
        if key in self.executed or any(uid in self.executed_uids for uid in key):
            raise ValueError("A block cannot be tested a second time as new evidence")
        self.executed.add(key)
        self.executed_uids.update(key)
        word=np.array([int(o.gas>plan.codebook.threshold) if np.isfinite(o.gas) else -1 for o in observations])
        rejected=False;probability=None
        if plan.test is not None:
            probability=plan.test.rejection_probability(word)
            rejected=bool(plan.independent_uniform<probability)
            self.risk.tests[plan.risk_index]["executed"]=True
        compatible=self.recovery.update(plan.codebook,word,self.channel)
        return {"status":"executed","rejected":rejected,"trigger_replay":rejected,
                "null_source":plan.null_source,"rejection_probability":probability,
                "recovery_list":compatible,"word":word.tolist(),
                "evidence_rule":"raw observations only; this decision is not a likelihood factor",
                "counterevidence_status":"tested" if plan.test is not None else "abstained",
                "model_version":current}
