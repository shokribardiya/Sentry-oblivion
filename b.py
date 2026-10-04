"""Structure + syntax validation for the OBLIVION page (stdlib only)."""
import io, re, sys, json, subprocess, pathlib

PATH = pathlib.Path(__file__).with_name("index.html")
src = pathlib.Path(PATH, encoding="utf-8").read_text(encoding="utf-8")

VOID = {"area","base","br","col","embed","hr","img","input","link","meta",
        "param","source","track","wbr"}

# --- 1. tag balance -------------------------------------------------------
class Balance:
    def __init__(self):
        self.stack = []
        self.errors = []

b = Balance()
tag_re = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)((?:[^<>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>", re.S)
for m in tag_re.finditer(src):
    closing, name, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
    if name in ("!doctype",):
        continue
    if name == "!--" or src[m.start():m.start()+4] == "<!--":
        continue
    if closing:
        if not b.stack:
            b.errors.append(f"stray </{name}> at {m.start()}")
        elif b.stack[-1][0] != name:
            b.errors.append(f"mismatch: </{name}> but open <{b.stack[-1][0]}> at {m.start()}")
            # attempt recovery
            for i in range(len(b.stack) - 1, -1, -1):
                if b.stack[i][0] == name:
                    del b.stack[i:]
                    break
        else:
            b.stack.pop()
    else:
        if selfclose or name in VOID:
            continue
        b.stack.append((name, m.start()))

if b.errors:
    print("TAG ERRORS:")
    for e in b.errors[:40]:
        print("  ", e)
else:
    print("TAGS: balanced")

if b.stack:
    print("UNCLOSED:", [(n, src[:p].count(chr(10)) + 1) for n, p in b.stack[:20]])

# --- 2. inline script syntax ---------------------------------------------
scripts = re.findall(r"<script(?![^>]*application/ld\+json)[^>]*>(.*?)</script>", src, re.S)
print("inline scripts:", len(scripts))

node = None
for cand in ("node", "nodejs"):
    try:
        subprocess.run([cand, "--version"], capture_output=True, check=True)
        node = cand
        break
    except Exception:
        continue

for i, s in enumerate(scripts):
    if not s.strip():
        continue
    if node:
        p = subprocess.run([node, "--check", "-"], input=s.encode(), capture_output=True)
        if p.returncode != 0:
            print(f"  script[{i}] SYNTAX ERROR:\n", p.stderr.decode(errors="replace"))
        else:
            print(f"  script[{i}] js syntax OK ({len(s)} chars)")
    else:
        print(f"  script[{i}] (node unavailable, skipped) {len(s)} chars")

# --- 3. JSON-LD -----------------------------------------------------------
for i, m in enumerate(re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)):
    try:
        json.loads(m)
        print(f"  json-ld[{i}] OK")
    except Exception as e:
        print(f"  json-ld[{i}] ERROR: {e}")

# --- 4. essentials --------------------------------------------------------
for needle in [
    'action="https://formsubmit.co/oblivion330121@gmail.com"',
    'id="oblivionForm"', 'id="transmitBtn"', 'id="statusLine"',
    'AJAX_ENDPOINT', 'mailto:oblivion330121@gmail.com',
    'name="first_name"', 'name="capabilities"', 'name="personal_statement"',
    'id="received"',
]:
    print(("  OK   " if needle in src else "  MISS ") + needle)

# required form field names present exactly once (or more)
names = re.findall(r'name="([a-zA-Z_]+)"', src)
dups = {n: names.count(n) for n in set(names) if n not in ("capabilities",) and names.count(n) > 1}
print("duplicate field names:", dups or "none")
print("total fields:", len(names))

# --- 5. CSS brace balance -------------------------------------------------
style = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
print("css braces:", style.count("{"), "open /", style.count("}"), "close",
      "-> OK" if style.count("{") == style.count("}") else "-> MISMATCH")

print("file size:", len(src.encode('utf-8')), "bytes /", len(src.splitlines()), "lines")
