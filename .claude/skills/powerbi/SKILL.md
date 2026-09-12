---
name: powerbi
description: Author Power BI dashboards as files (PBIP/PBIR/TMSL) without opening Power BI Desktop. Use when creating, restyling or debugging a .pbip project, writing DAX measures into a model, building report pages/visuals/bookmarks as JSON, applying a custom theme, or when Power BI opens a project with an empty Report View.
---

# Authoring Power BI as files

Power BI Desktop is a Windows GUI app with no CLI and no export command, so it
cannot be driven programmatically. But a report **can** be authored as text:
the PBIP project format stores the model as TMSL/TMDL and the report as PBIR
JSON. You write files; the user opens Desktop once to render and export.

**You cannot verify rendering.** You can verify *structure* — do that
rigorously, because every round trip costs the user a manual open.

## Project layout

```
Projeto.pbip                       ← ponteiro; artifacts → pasta .Report
Projeto.SemanticModel/
  definition.pbism                 ← version "4.x"
  model.bim                        ← TMSL: tabelas, colunas, medidas, partições
Projeto.Report/
  definition.pbir                  ← datasetReference byPath → ../*.SemanticModel
  definition/
    version.json                   ← version "2.0.0"  (ver armadilha abaixo)
    report.json                    ← themeCollection, resourcePackages
    pages/pages.json               ← pageOrder, activePageName
    pages/<pagina>/page.json
    pages/<pagina>/visuals/<v>/visual.json
    bookmarks/<b>.bookmark.json    ← opcional
    bookmarks/bookmarks.json
```

## The trap that costs a whole round trip

**A PBIR definition declaring the 1.0.0 schema family is silently ignored.**
Power BI opens the model, shows an **empty Report View**, and does not rewrite
or complain about a single report file. It looks like your JSON was rejected;
it was never read.

Those 1.0.0 schemas exist and validate perfectly. They are simply a superseded
revision. Use the current family:

| Ficheiro | Errado | Certo |
|---|---|---|
| `version.json` (campo `version`) | `1.0.0` | **`2.0.0`** |
| `page.json` | `page/1.0.0` | **`page/2.0.0`** |
| `visual.json` | `visualContainer/1.0.0` | **`visualContainer/2.2.0`** |
| `report.json` | `report/1.0.0` | **`report/3.0.0`** |

Diagnostic: if Report View is empty **and `git status` on the project is
clean**, Desktop never read the definition. If it had read and disliked it, it
would name the offending file in a blocking error.

`report/3.0.0` also drops `layoutOptimization` and makes `reportVersionAtImport`
an **object** (`{visual, page, report}`). Microsoft's own documentation example
still shows the superseded string form — don't copy it.

After Desktop saves, it upgrades files to versions Microsoft has not published
(e.g. `visualContainer/2.12.0` → 404). That is normal. Don't "fix" them, and
don't let a validator fail on them.

## Ground truth beats documentation

The docs lag and third-party "skills marketplace" pages are often model-written
and wrong. One claimed `queryState` was a flat `projections` array with
`source`/`kind` fields; the real schema keys it by **role name**. Verify against:

- the published schemas at
  `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/<nome>/<versao>/schema.json`
- real projects: **`FabricTools/pbir-samples`** on GitHub
- whatever Desktop itself wrote after it opened your project — the most
  authoritative source available. Commit that normalization, then edit on top
  of it rather than regenerating over it.

Also: the `*-embedded.json` schemas declare `$id` with a **dot**
(`schema.embedded.json`) instead of the hyphen in their own URL. Any resolver
honouring `$id` chases a 404. Rewrite the dot to a hyphen when fetching.

## visual.json

```json
{
  "$schema": ".../visualContainer/2.2.0/schema.json",
  "name": "valor_por_ano",
  "position": {"x": 16, "y": 112, "z": 0, "width": 412, "height": 290},
  "visual": {
    "visualType": "clusteredColumnChart",
    "query": {"queryState": {
      "Category": {"projections": [{
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": "dCalendario"}}, "Property": "Ano"}},
        "queryRef": "dCalendario.Ano", "active": true}]},
      "Y": {"projections": [{
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "fBPS"}}, "Property": "Valor Total"}},
        "queryRef": "fBPS.Valor Total"}]}
    }},
    "objects": {},
    "visualContainerObjects": {}
  }
}
```

`queryState` keys are **data roles**, which vary by visual: `Category`/`Y` for
bar, column and line; `Values` for card, slicer and table; `Rows`/`Values` for
matrix. **`visualType` is an unconstrained string in the schema** — a wrong
name passes validation and renders blank. This is the one thing structure
checking cannot catch.

### Formatting expressions

Values are always wrapped; `objects` is per-visual, `visualContainerObjects`
is the frame (title, background, border).

```jsonc
{"expr": {"Literal": {"Value": "'texto'"}}}   // texto: aspas simples internas
{"expr": {"Literal": {"Value": "12D"}}}        // número: sufixo D
{"expr": {"Literal": {"Value": "true"}}}       // booleano
{"solid": {"color": {"expr": {"Literal": {"Value": "'#2A78D6'"}}}}}   // cor
```

Gradient (conditional formatting by measure):

```json
{"solid": {"color": {"expr": {"FillRule": {
  "Input": {"Measure": {"Expression": {"SourceRef": {"Entity": "fBPS"}}, "Property": "Valor Total"}},
  "FillRule": {"linearGradient2": {
    "min": {"color": {"Literal": {"Value": "'#CDE2FB'"}}},
    "max": {"color": {"Literal": {"Value": "'#104281'"}}}}}}}}}}
```

### Top N filter

No `Top` option exists on the visual query. Top N is a `filterConfig` entry of
type `TopN`: a subquery in `From` exposed as an expression table (`Type: 2`),
ordered by the measure and cut with `Top`, then an `In` in `Where` restricting
the category to it.

## model.bim (TMSL)

TMSL is a single JSON file, is the default (no preview flag), and is far safer
to hand-author than TMDL folders.

**The mistake that silently corrupts every number:** the culture argument of
`Table.TransformColumnTypes`. If the CSV was written by pandas (dot decimals,
ISO dates), pass **`"en-US"`**. Under `pt-BR`, `4.5` is read as forty-five and
the whole base inflates.

```json
{"name": "Projeto", "compatibilityLevel": 1567,
 "model": {"culture": "pt-BR",
   "tables": [{"name": "fBPS",
     "columns": [{"name": "uf", "dataType": "string", "sourceColumn": "uf", "summarizeBy": "none"}],
     "measures": [{"name": "Valor Total", "expression": "SUM(fBPS[preco_total])", "formatString": "\"R$\" #,0"}],
     "partitions": [{"name": "p", "mode": "import",
       "source": {"type": "m", "expression": ["let", "...", "in", "    Tipado"]}}]}],
   "relationships": [{"name": "r1", "fromTable": "fBPS", "fromColumn": "compra",
                      "toTable": "dCalendario", "toColumn": "Date"}]}}
```

A calculated table is a partition with `"source": {"type": "calculated", "expression": "<DAX>"}`;
a calculated column adds `"type": "calculated"` plus `"expression"`.

## Custom theme

Theme JSON uses **raw values**, not the wrapped expressions of `visual.json`:

```json
{"name": "MeuTema", "dataColors": ["#2A78D6", "#1BAF7A"],
 "background": "#FFFFFF", "foreground": "#1A1A19",
 "visualStyles": {"*": {"*": {"categoryAxis": [{"showAxisTitle": false}]}}}}
```

The file goes in `StaticResources/RegisteredResources/`, and **must** be
registered in `report.json` under `resourcePackages` plus referenced from
`themeCollection.customTheme`. Microsoft documents RegisteredResources editing
as unsupported in preview for resources not already loaded, so treat a
hand-added theme as unverified. Per-visual `objects` always work and are the
reliable fallback.

`Dashboard-Design/Power-BI-Design-Files` on GitHub has a `Theme .JSON Files`
folder of working real-world themes to copy structure from.

## Single canvas with navigation

"Tabs inside one page" = bookmarks + buttons, not pages:

1. Group the visuals of each view (`visualGroup`, or a shared
   `parentGroupName`).
2. One `bookmarks/<nome>.bookmark.json` per view; `explorationState` records
   which groups are visible.
3. Buttons are visuals with `visualType: "actionButton"` whose action targets
   the bookmark.
4. List every bookmark in `bookmarks/bookmarks.json`.

## Validate before handing over

Every unverified file is a manual open the user pays for. A validator must:

- treat an **unresolvable `$schema` as a failure**, never as "no schema" — that
  blind spot is exactly how a wrong `.pbip` URL ships;
- check the URL against the `pattern` the schema declares for itself, which is
  what Desktop enforces;
- accept files Desktop writes without `$schema` (`.pbip` after saving,
  `definition.pbir`, `definition.pbism`, `model.bim`, `diagramLayout.json`);
- skip `.pbi/` (local, gitignored);
- downgrade *unpublished* Desktop versions to warnings — and to check those
  files anyway, copy them with the version rewritten to the newest published
  one and validate the copy.

`jsonschema` with a `RefResolver` whose handler rewrites the embedded-`$id` bug
resolves the whole graph, including `semanticQuery`, which does validate the
`queryState` of every visual.
