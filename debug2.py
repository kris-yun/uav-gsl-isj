import re
f = open("/tmp/cp_sbd_exp/eprocess/verify_House01_s0_st10.log", "r", errors="replace")
c = f.read()
f.close()
print("len=", len(c))
print("MAXSTEPS-STOP in c =", "MAXSTEPS-STOP" in c)
print("final_error in c =", "final_error" in c)
