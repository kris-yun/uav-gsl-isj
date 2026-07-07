with open("/tmp/run_10seeds.sh", "rb") as f:
    data = f.read()
if data[:3] == b"\xef\xbb\xbf":
    data = data[3:]
data = data.replace(b"\r\n", b"\n")
with open("/tmp/run_10seeds.sh", "wb") as f:
    f.write(data)
print("Fixed")