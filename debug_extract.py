import re
f = open("/tmp/cp_sbd_exp/eprocess/FixedSteps_House01_s0_st10.log", "r", errors="replace")
c = f.read()
f.close()
print("len=", len(c))
print("MAXSTEPS-STOP in c =", "MAXSTEPS-STOP" in c)
print("final_error in c =", "final_error" in c)
m = re.search(r"MAXSTEPS-STOP", c)
print("re search MAXSTEPS=", m)
m2 = re.search(r"final_error=([\d.]+)", c)
print("re search final_error=", m2)
idx = c.find("MAXSTEPS")
if idx >= 0:
    print("Found MAXSTEPS at index", idx)
    print("context:", repr(c[idx:idx+80]))
else:
    print("MAXSTEPS not found by find()")
