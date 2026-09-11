"""Valida um projeto PBIP contra os schemas oficiais da Microsoft.

Um schema que nao resolve e tratado como FALHA, nunca como "sem schema":
foi exatamente esse ponto cego que deixou passar um $schema com URL errada
no arquivo .pbip, que so apareceu quando o Power BI recusou abrir o projeto.
"""
import json, sys, urllib.request, urllib.error
from pathlib import Path
from jsonschema import Draft7Validator, RefResolver
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CACHE = Path(sys.argv[2]); CACHE.mkdir(parents=True, exist_ok=True)
FALHAS_URL = {}

def carregar(uri):
    nome = uri.replace('https://developer.microsoft.com/json-schemas/', '').replace('/', '_')
    p = CACHE / nome
    if not p.exists():
        try:
            dados = urllib.request.urlopen(uri, timeout=25).read()
            json.loads(dados)
            p.write_bytes(dados)
        except Exception as e:
            FALHAS_URL[uri] = str(e)[:90]
            raise
    return json.loads(p.read_text(encoding='utf-8'))

root = Path(sys.argv[1])
alvos = [f for f in sorted(root.rglob('*'))
         if f.is_file() and f.suffix in ('.json', '.pbip', '.pbir', '.pbism', '.bim')]
ok = falhas = 0
erros = []
SEM_SCHEMA_OK = {'model.bim'}

for f in alvos:
    try:
        doc = json.loads(f.read_text(encoding='utf-8'))
    except Exception as e:
        erros.append((f, f'JSON invalido: {e}')); falhas += 1; continue

    uri = doc.get('$schema')
    if not uri:
        if f.name in SEM_SCHEMA_OK:
            ok += 1
        else:
            erros.append((f, 'sem propriedade $schema')); falhas += 1
        continue

    try:
        esquema = carregar(uri)
    except Exception:
        erros.append((f, f'$schema NAO RESOLVE (404/erro): {uri}')); falhas += 1; continue

    pat = esquema.get('properties', {}).get('$schema', {}).get('pattern')
    if pat:
        import re
        if not re.match(pat, uri):
            erros.append((f, f'$schema nao casa com o pattern exigido: {pat}')); falhas += 1; continue

    v = Draft7Validator(esquema, resolver=RefResolver(
        base_uri=uri, referrer=esquema, handlers={'https': carregar, 'http': carregar}))
    problemas = sorted(v.iter_errors(doc), key=lambda e: list(e.path))
    if problemas:
        falhas += 1
        for p in problemas[:3]:
            erros.append((f, f"{'/'.join(str(x) for x in p.path) or '(raiz)'}: {p.message[:140]}"))
    else:
        ok += 1

print(f"arquivos: {len(alvos)} | OK: {ok} | FALHAS: {falhas}")
if FALHAS_URL:
    print("\nURLs de schema que nao resolveram:")
    for u, e in FALHAS_URL.items(): print(f"   {u}\n      {e}")
if erros:
    print("\n--- problemas ---")
    for f, m in erros[:25]:
        print(f"  {f.relative_to(root)}\n      {m}")
sys.exit(1 if falhas else 0)
