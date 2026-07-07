with open("/tmp/run_baselines.sh", "rb") as f:
    data = f.read()
data = data.replace(b"\xef\xbb\xbf", b"").replace(b"\r\n", b"\n")
with open("/tmp/run_baselines.sh", "wb") as f:
    f.write(data)
print("Fixed")