from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

start = s.find('  function onFrame() {')
end = s.find('  function onScroll() {')
print('start', start, 'end', end)
if start < 0 or end < 0 or end < start:
    print('ABORT: markers not found')
    raise SystemExit(1)

new = """  function paint() {
    var doc = document.documentElement;
    var top = doc.scrollTop || document.body.scrollTop || 0;
    var max = (doc.scrollHeight || doc.body.scrollHeight) - doc.clientHeight;
    var p = max > 0 ? Math.min(1, Math.max(0, top / max)) : 0;
    if (fill) fill.style.height = (p * 100).toFixed(2) + '%';
    if (header) header.classList.toggle('stuck', top > 24);
    checkReveals();
  }
  function onFrame() { ticking = false; paint(); }
"""

s = s[:start] + new + s[end:]

# --- safety net: guarantee counters reach their final value even if
#     requestAnimationFrame never runs (hidden/background documents).
needle = "      if (t < 1) window.requestAnimationFrame(step);\n    })(start);"
if needle in s:
    s = s.replace(
        needle,
        "      if (t < 1) window.requestAnimationFrame(step);\n"
        "    })(start);\n"
        "    // rAF can be suspended in hidden tabs: guarantee the final value.\n"
        "    window.setTimeout(function () { el.textContent = String(target); }, dur + 120);",
        1,
    )
    print('counter net added')
else:
    print('WARN: counter needle not found')

p.write_text(s, encoding='utf-8')
print('written', len(s))
