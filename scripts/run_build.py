import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

_html = (ROOT / 'Wive.html').read_text(encoding='utf-8')
if 'const sb=supabase' in _html and "const LS='wive_v2'" not in _html:
    _out = ROOT / 'public'
    _out.mkdir(exist_ok=True)
    (_out / 'index.html').write_text(_html, encoding='utf-8')
    print('OK: copiado a public/index.html')
    sys.exit(0)

TARGET = HERE / 'build.py'
src = TARGET.read_text(encoding='utf-8')

def unmoji(text):
    out = bytearray()
    for ch in text:
        o = ord(ch)
        if o < 128:
            out.append(o); continue
        try:
            out += ch.encode('cp1252')
        except UnicodeEncodeError:
            out.append(o) if o < 256 else out.extend(ch.encode('utf-8'))
    return out.decode('utf-8')

if '\u00c3' in src:
    try:
        src = unmoji(src)
    except UnicodeDecodeError:
        pass
exec(compile(src, str(TARGET), 'exec'), {'__file__': str(TARGET), '__name__': '__main__'})
