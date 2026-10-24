"""Certify live ancestry and creation times, including newly spawned children."""
import psutil

def certified_owner(chain,owners):
    """Chain is child -> ancestors; no executable-name exemptions."""
    if not chain:return None
    for child,parent in zip(chain,chain[1:]):
        if child['ppid']!=parent['pid'] or child['create_time']<parent['create_time']:return None
    for node in chain:
        known=owners.get(node['pid'])
        if known and known['create_time']==node['create_time']:
            return dict(anchor_pid=node['pid'],anchor_create_time=node['create_time'],chain=chain)
    return None

def adopt_new_children(rows,owners):
    proofs=[]
    for row in rows:
        if row['pid']in owners and owners[row['pid']]['create_time']==row['create_time']:continue
        try:
            p=psutil.Process(row['pid'])
            if p.create_time()!=row['create_time']:continue
            family=[p]+p.parents()
            chain=[dict(pid=z.pid,ppid=z.ppid(),create_time=z.create_time())for z in family]
            proof=certified_owner(chain,owners)
            if proof:
                owners[p.pid]=dict(pid=p.pid,create_time=p.create_time(),name=p.name(),command=p.cmdline())
                proofs.append(proof)
        except(psutil.NoSuchProcess,psutil.ZombieProcess,psutil.AccessDenied):pass
    return proofs

def selftest():
    owners={10:dict(pid=10,create_time=100)}
    assert certified_owner([dict(pid=12,ppid=11,create_time=102),dict(pid=11,ppid=10,create_time=101),dict(pid=10,ppid=1,create_time=100)],owners)
    assert certified_owner([dict(pid=12,ppid=10,create_time=102),dict(pid=10,ppid=1,create_time=100)],owners)
    assert not certified_owner([dict(pid=12,ppid=20,create_time=102),dict(pid=20,ppid=1,create_time=99)],owners)
    assert not certified_owner([dict(pid=12,ppid=10,create_time=104),dict(pid=10,ppid=1,create_time=103)],owners),'PID reuse must remain foreign'
    assert not certified_owner([dict(pid=12,ppid=10,create_time=98),dict(pid=10,ppid=1,create_time=100)],owners)
    assert not certified_owner([dict(pid=12,ppid=20,create_time=102),dict(pid=10,ppid=1,create_time=100)],owners)
    return dict(status='PASS_NEW_CHILD_FOREIGN_PID_REUSE_AND_BROKEN_ANCESTRY_REGRESSIONS')

if __name__=='__main__':print(selftest())
