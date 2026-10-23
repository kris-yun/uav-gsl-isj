from __future__ import annotations
from pathlib import Path
import hashlib,json
import numpy as np
from .data import SynchronousBlock


class RawObservationLedger:
    """Append only raw blocks. Derived features and audit decisions aren't data."""
    def __init__(self,directory):
        self.directory=Path(directory); self.directory.mkdir(parents=True,exist_ok=True)
        self.path=self.directory/'events.jsonl'
        self.ids=set();self.last_time=-np.inf
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                row=json.loads(line);self.ids.add(row['event_id']);self.last_time=row['end_s']

    def append(self,block:SynchronousBlock,action:int):
        if block.block_id in self.ids:raise ValueError("duplicate physical observation block")
        if float(block.times_s[0])<=self.last_time:raise ValueError("overlapping/out-of-order raw windows cannot be independently accumulated")
        if block.metadata.get('truth_included',False):raise ValueError("deployment ledger must not contain true-source labels")
        name=hashlib.sha256(block.block_id.encode()).hexdigest()[:20]+'.npz'
        target=self.directory/name;block.save_npz(target)
        row={'event_id':block.block_id,'action':int(action),'file':name,
             'start_s':float(block.times_s[0]),'end_s':float(block.times_s[-1]),
             'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        with self.path.open('a',encoding='utf8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
        self.ids.add(block.block_id);self.last_time=row['end_s']
        return row

