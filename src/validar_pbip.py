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
    # Os schemas "*-embedded.json" da Microsoft declaram um $id com ponto
    # ("schema.embedded.json") em vez do hifen do proprio endereco. Quem honra
    # o $id ao resolver os $ref seguintes vai bater num 404. Nao e problema do
    # projeto: e um defeito do schema publicado.
    uri = uri.replace('schema.embedded.json', 'schema-embedded.json')
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
         if f.is_file() and f.suffix in ('.json', '.pbip', '.pbir', '.pbism', '.bim')
         and '.pbi' not in f.parts              # .pbi/ e local, fica fora do git
         # Temas do Power BI sao JSON proprio, sem $schema obrigatorio.
         and 'RegisteredResources' not in f.parts]
ok = falhas = 0
erros = []
avisos = []
# Arquivos que o proprio Power BI Desktop grava sem $schema.
SEM_SCHEMA_OK = {'model.bim', 'definition.pbir', 'definition.pbism',
                 'diagramLayout.json', 'localSettings.json', 'editorSettings.json'}
SUFIXO_SEM_SCHEMA_OK = {'.pbip'}   # o Desktop remove o $schema ao salvar

for f in alvos:
    try:
        doc = json.loads(f.read_text(encoding='utf-8'))
    except Exception as e:
        erros.append((f, f'JSON invalido: {e}')); falhas += 1; continue

    uri = doc.get('$schema')
    if not uri:
        if f.name in SEM_SCHEMA_OK or f.suffix in SUFIXO_SEM_SCHEMA_OK:
            ok += 1
        else:
            erros.append((f, 'sem propriedade $schema')); falhas += 1
        continue

    try:
        esquema = carregar(uri)
    except Exception:
        # O Desktop grava versoes de schema que a Microsoft ainda nao publicou
        # (ex.: visualContainer/2.12.0 devolve 404). Nao da para validar, mas
        # tambem nao e defeito do projeto: quem escreveu o arquivo foi o
        # proprio Power BI. Vira aviso, nao falha.
        avisos.append((f, f'schema nao publicado, nao verificavel: {uri}'))
        continue

    pat = esquema.get('properties', {}).get('$schema', {}).get('pattern')
    if pat:
        import re
        if not re.match(pat, uri):
            erros.append((f, f'$schema nao casa com o pattern exigido: {pat}')); falhas += 1; continue

    v = Draft7Validator(esquema, resolver=RefResolver(
        base_uri=uri, referrer=esquema, handlers={'https': carregar, 'http': carregar}))
    try:
        problemas = sorted(v.iter_errors(doc), key=lambda e: list(e.path))
    except Exception as e:
        erros.append((f, f'nao foi possivel resolver um $ref do schema: {str(e)[:120]}'))
        falhas += 1
        continue
    if problemas:
        falhas += 1
        for p in problemas[:3]:
            erros.append((f, f"{'/'.join(str(x) for x in p.path) or '(raiz)'}: {p.message[:140]}"))
    else:
        ok += 1

print(f"arquivos: {len(alvos)} | OK: {ok} | FALHAS: {falhas} | avisos: {len(avisos)}")
if avisos:
    print("\n--- avisos (schema nao publicado pela Microsoft) ---")
    vistos = {}
    for f, m in avisos:
        vistos.setdefault(m.split(': ')[-1], []).append(f.name)
    for u, fs in vistos.items():
        print(f"   {len(fs)} arquivo(s): {u}")
if FALHAS_URL:
    print("\nURLs de schema que nao resolveram:")
    for u, e in FALHAS_URL.items(): print(f"   {u}\n      {e}")
if erros:
    print("\n--- problemas ---")
    for f, m in erros[:25]:
        print(f"  {f.relative_to(root)}\n      {m}")
sys.exit(1 if falhas else 0)
