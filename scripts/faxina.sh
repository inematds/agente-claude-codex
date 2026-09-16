#!/usr/bin/env bash
# faxina.sh — Marie Kondo do CLAUDE.md: classifica cada seção de um CLAUDE.md/AGENTS.md longo e propõe
# o que fica (regra estável), o que vira context/ (fato, runbook, histórico) e o que é resíduo do runtime.
# Só lê e imprime Markdown; não altera nada. Uso: scripts/faxina.sh <pasta-do-projeto> [arquivo] > relatorio.md
set -uo pipefail
P="${1:?pasta do projeto}"; F="${2:-}"
[ -n "$F" ] || { for c in CLAUDE.md AGENTS.md; do [ -f "$P/$c" ] && { F="$P/$c"; break; }; done; }
[ -f "$F" ] || { echo "sem CLAUDE.md/AGENTS.md em $P"; exit 1; }
python3 - "$F" <<'EOF'
import re,sys
f=sys.argv[1]; txt=open(f,encoding='utf-8',errors='replace').read(); lines=txt.splitlines()
print(f"# Faxina — {f}\n\nTotal: {len(lines)} linhas. Meta: AGENTS.md enxuto (regras estáveis, < 150 linhas); o resto vai pra `context/`.\n")
secs=[]; cur=['(preâmbulo)',[]]
for l in lines:
    if re.match(r'^#{1,3} ',l): secs.append(cur); cur=[l.strip('# ').strip(),[]]
    else: cur[1].append(l)
secs.append(cur)
RES=re.compile(r'AskUserQuestion|superpowers|context-mode|claude-mem|fable-mindset|plugin|hook|Artifact|advisor|ultrareview|/code-review',re.I)
FACT=re.compile(r'\b(20\d\d-\d\d-\d\d|porta \d+|localhost:\d+|:\d{4}\b|versão|version|v\d+\.\d+|\d+ GB|\d+GB)',re.I)
HIST=re.compile(r'corrigido em|mudou em|antes era|era \w+ até|anotado em|\(pedido em|deprecad|legado|antigo|removido em',re.I)
RUN=re.compile(r'passo a passo|runbook|como (rodar|operar|fazer)|receita|```',re.I)
RULE=re.compile(r'\b(nunca|sempre|não|obrigat|default|padrão|regra|deve|proibid)\b',re.I)
rows=[]
for name,body in secs:
    n=len(body); b='\n'.join(body)
    if n==0: continue
    if RES.search(b) and not RULE.search(b): dest,why='CLAUDE.md (resíduo)','cita ferramenta/plugin/hook do runtime'
    elif RULE.search(b) and HIST.search(b): dest,why='AGENTS.md (fica) + notas datadas → context/decisions/','regra estável com histórico embutido: manter a regra, mover as correções datadas'
    elif HIST.search(b): dest,why='context/decisions/ ou context/current-state.md','histórico/correções datadas: vira decisão registrada, não regra'
    elif RUN.search(b) and n>12: dest,why='context/ (runbook próprio)','procedimento longo; AGENTS.md só aponta o arquivo'
    elif FACT.search(b) and not RULE.search(b): dest,why='context/overview.md ou sources.md','fatos com data/porta/versão: precisam de fonte e data de observação'
    elif RULE.search(b): dest,why='AGENTS.md (fica)','regra estável'
    else: dest,why='revisar','não classificado pela heurística'
    rows.append((name[:60],n,dest,why))
print("| Seção | Linhas | Destino proposto | Motivo |\n|---|---|---|---|")
for r in rows: print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")
fica=sum(r[1] for r in rows if r[2].startswith('AGENTS'))
print(f"\nSe aplicado: AGENTS.md ficaria com ~{fica} linhas ({100*fica//max(1,len(lines))}% do atual). Heurística por regex: revisar antes de mover.")
EOF
