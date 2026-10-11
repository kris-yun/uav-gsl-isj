from common_n import *
plan=load(CORE/'READOUT_CONTRACT.json');c=load(CORE/'FACTORIAL_CONTRACT.json')
plan['banks']=[dict(id=j['id'],candidate=j['candidate'],replicate=j['replicate'],D=j['D'],V=j['V'],path=DATA+'/factorial/'+j['id']) for j in c['jobs']]
plan['scope']='Same engine factorial fields; not physical CFD redesign, not modified PMFS results';dump(CORE/'READOUT_CONTRACT_C.json',plan)
src=(WORK/'readout_worker.py').read_text().replace("(T/'READOUT_CONTRACT.json')","(T/'READOUT_CONTRACT_C.json')").replace("D=DATA/'readout'","D=DATA/'C_readout'")
src=src.replace("   src=Path(bank['path']);times=rows", """   src=Path(bank['path'])
   while not (src/'QUALIFICATION.json').exists():
    gl=json.loads((DATA/'factorial/GAS_LEDGER.json').read_text())
    if gl['status'].startswith('STOP'):raise RuntimeError('Related factorial bank unavailable: '+bank['id'])
    assert time.time()-P['entry_unix']<9000
    time.sleep(1)
   assert json.loads((src/'QUALIFICATION.json').read_text())['physical_qualification']=='PASS'
   times=rows""")
src=src.replace("   time.sleep(.1)", """   rss=0
   for status in Path('/proc').glob('[0-9]*/status'):
    try:
     if os.getpgid(int(status.parent.name))==p.pid:rss+=next(int(x.split()[1])*1024 for x in status.read_text().splitlines() if x.startswith('VmRSS:'))
    except (OSError,ProcessLookupError,StopIteration):pass
   if rss>1610612736:os.killpg(p.pid,signal.SIGINT);p.wait(timeout=10);raise RuntimeError('RSS_CAP')
   time.sleep(.1)""")
code=r'''import subprocess
p=subprocess.Popen(['python3',str(t/'readout_factorial_worker.py')],stdout=(t/'C_readout.stdout').open('w'),stderr=(t/'C_readout.stderr').open('w'),start_new_session=True)
print(json.dumps({'pid':p.pid,'native_readouts':60,'additional_physics_generation':0,'waits_for_qualified_banks':True}))
'''
r=json.loads(upload({'READOUT_CONTRACT_C.json':(CORE/'READOUT_CONTRACT_C.json').read_bytes(),'readout_factorial_worker.py':src.encode()},code,'start_C_readouts_qualified_banks_only',45));dump(CORE/'C_READOUT_STARTED.json',r);(CORE/'source/readout_factorial_worker.py').write_text(src,encoding='utf-8');print(json.dumps(r))
