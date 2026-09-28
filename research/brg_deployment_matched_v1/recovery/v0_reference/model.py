"""Clean implementation inspired by Salehi et al., Nat. Commun. 2026.

Not the authors' visual BRG architecture or a reproduction of its experiments.
Temporal recurrence is causal. 'Bidirectional' means bottom-up/top-down within
one observed event; the implementation never reads a future observation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import torch
from torch import nn

@dataclass(frozen=True)
class ModelConfig:
    hidden: int = 32
    rounds: int = 3
    variant: str = "brg"  # brg, ungated, gru
    obs_dim: int = 3
    cue_dim: int = 6
    def __post_init__(self):
        if self.hidden < 4 or self.rounds < 1 or self.variant not in {"brg", "ungated", "gru"}:
            raise ValueError("invalid model configuration")

class CandidateBRG(nn.Module):
    def __init__(self, cfg: ModelConfig = ModelConfig()):
        super().__init__(); self.cfg = cfg; h = cfg.hidden
        self.obs = nn.Sequential(nn.Linear(cfg.obs_dim,h),nn.LayerNorm(h),nn.Tanh())
        self.cue = nn.Sequential(nn.Linear(cfg.cue_dim,h),nn.LayerNorm(h),nn.Tanh())
        self.fuse = nn.Sequential(nn.Linear(4*h,h),nn.LayerNorm(h),nn.Tanh())
        self.feedback = nn.Linear(2*h,h)
        self.cell = nn.GRUCell(h,h)
        self.head = nn.Linear(h,1,bias=False)

    def initial(self, batch: int, candidates: int, device=None):
        if candidates < 2: raise ValueError("at least two candidates required")
        return torch.zeros(batch,candidates,self.cfg.hidden,
                           device=device or next(self.parameters()).device)

    def step(self, observed, cue, state, valid=None):
        """observed:[B,3], cue:[B,S,6], state:[B,S,H]; returns logits,state.

        The shared scorer has no candidate-ID embedding and no environment label.
        Its logits represent the entire prefix; DO NOT add them to old log odds.
        """
        b,s,_ = cue.shape
        if observed.shape != (b,self.cfg.obs_dim) or state.shape != (b,s,self.cfg.hidden):
            raise ValueError("shape mismatch")
        if not (torch.isfinite(observed).all() and torch.isfinite(cue).all() and torch.isfinite(state).all()):
            raise ValueError("non-finite input")
        o = self.obs(observed)[:,None,:].expand(-1,s,-1)
        v = self.cue(cue); old = state; h = state
        steps = 1 if self.cfg.variant == "gru" else self.cfg.rounds
        for _ in range(steps):
            if self.cfg.variant == "brg":
                gate = 1 + 0.5 * torch.tanh(self.feedback(torch.cat((h,v),-1)))
            else:
                gate = torch.ones_like(h)
            # The physical hypothesis modulates bottom-up evidence; no oracle cue.
            z = self.fuse(torch.cat((o*gate,v,o-v,o*v),-1))
            h = self.cell(z.reshape(b*s,-1),h.reshape(b*s,-1)).reshape(b,s,-1)
        if valid is not None:
            h = torch.where(valid[:,None,None].bool(),h,old)
        return self.head(h).squeeze(-1),h

    def forward(self, observed, cues, valid=None):
        # [B,T,O], [B,T,S,C] -> [B,T,S]
        if observed.ndim != 3 or cues.ndim != 4 or observed.shape[:2] != cues.shape[:2]:
            raise ValueError("expected batched causal trajectories")
        b,t,_ = observed.shape
        h = self.initial(b,cues.shape[2],observed.device); out=[]
        for i in range(t):
            z,h = self.step(observed[:,i],cues[:,i],h,None if valid is None else valid[:,i])
            out.append(z)
        return torch.stack(out,1)

    @property
    def parameter_count(self): return sum(p.numel() for p in self.parameters())
    @property
    def active_parameter_count(self):
        n=self.parameter_count
        return n if self.cfg.variant=='brg' else n-sum(p.numel() for p in self.feedback.parameters())

def log_posterior(logits, prior=None, temperature: float=1.):
    """Fixed positive prior applied ONCE, not once per observed event."""
    if not temperature > 0: raise ValueError("temperature must be positive")
    if prior is None:
        return torch.log_softmax(logits/temperature,-1)
    prior = torch.as_tensor(prior,device=logits.device,dtype=logits.dtype)
    if (prior <= 0).any() or not torch.isfinite(prior).all(): raise ValueError("positive prior required")
    prior = prior/prior.sum(-1,keepdim=True)
    return torch.log_softmax(logits/temperature+prior.log(),-1)

def save_checkpoint(path, model, metadata):
    torch.save({"config":asdict(model.cfg),"state_dict":model.state_dict(),"metadata":metadata},path)

def load_checkpoint(path, device="cpu"):
    ck = torch.load(path,map_location=device,weights_only=True)
    model=CandidateBRG(ModelConfig(**ck["config"])).to(device)
    model.load_state_dict(ck["state_dict"],strict=True); model.eval()
    if not all(torch.isfinite(x).all() for x in model.state_dict().values()):
        raise ValueError("non-finite checkpoint")
    return model,ck["metadata"]
