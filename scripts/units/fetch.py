"""Download one file as several HTTP range requests at once. The JRC server gives each connection about 0.1 MB/s, so a
135 MB GHS-POP tile takes about 25 minutes over one connection and about 3 minutes over eight."""
import re, subprocess

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def size(url):
    out = subprocess.run(["curl", "-sSIL", "-A", UA, "-m", "60", url], capture_output=True, text=True, check=True).stdout
    return int(re.findall(r"(?im)^content-length:\s*(\d+)", out)[-1])


def fetch_parallel(url, dest, parts=8, tries=4):
    """Write url to dest (a Path) and return dest; pieces that fail or come back short are fetched again."""
    n = size(url)
    step = -(-n // parts)
    pieces = [(dest.with_name(f"{dest.name}.part{i}"), i * step, min(n, (i + 1) * step) - 1)
              for i in range(parts) if i * step < n]
    for _ in range(tries):
        todo = [(p, a, b) for p, a, b in pieces if not p.exists() or p.stat().st_size != b - a + 1]
        if not todo:
            break
        procs = [subprocess.Popen(["curl", "-sSfL", "-A", UA, "-m", "3600", "-r", f"{a}-{b}", "-o", str(p), url])
                 for p, a, b in todo]
        for pr in procs:
            pr.wait()
    assert all(p.stat().st_size == b - a + 1 for p, a, b in pieces), url
    with open(dest, "wb") as out:
        for p, _, _ in pieces:
            out.write(p.read_bytes())
            p.unlink()
    assert dest.stat().st_size == n, (dest, n)
    return dest
