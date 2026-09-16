#!/usr/bin/env bash
# promover-memoria.sh — ponte entre a memória nativa do Claude (~/.claude/projects/<slug>/memory/*.md) e o
# context/overview.md do projeto: lista as memórias, pede a um runtime que PROPONHA até N fatos verificáveis
# (com fonte e data) e grava a proposta em context/propostas-memoria.md. NADA entra no overview sem --aprovar.
# Uso:
#   scripts/promover-memoria.sh <pasta-do-projeto> [--n 3] [--runtime claude|codex] [--so-listar] [--mem <pasta de memória>]
#   scripts/promover-memoria.sh <pasta-do-projeto> --aprovar <k>[,<k>...]   # move os itens k da proposta pro overview
#   scripts/promover-memoria.sh <pasta-do-projeto> --aprovar todos
set -uo pipefail
P="$(cd "${1:?pasta do projeto}" && pwd)"; shift || true
N=3; RT=claude; LIST=0; APR=""; MEMO=""
while [ $# -gt 0 ]; do case "$1" in --n) N="$2"; shift;; --runtime) RT="$2"; shift;; --so-listar) LIST=1;; --aprovar) APR="$2"; shift;; --mem) MEMO="$2"; shift;; *) echo "arg: $1"; exit 2;; esac; shift; done
slug="$(echo "$P" | sed 's|/|-|g')"; MEM="${MEMO:-$HOME/.claude/projects/$slug/memory}"
PROP="$P/context/propostas-memoria.md"; OV="$P/context/overview.md"

if [ -n "$APR" ]; then
  [ -f "$PROP" ] || { echo "sem proposta em $PROP"; exit 1; }
  [ -f "$OV" ] || { echo "sem $OV (rode init-core.sh)"; exit 1; }
  python3 - "$PROP" "$OV" "$APR" <<'EOF'
import re,sys,datetime
prop,ov,sel=sys.argv[1],sys.argv[2],sys.argv[3]
items=re.findall(r'^\s*(\d+)\.\s+(.*?)(?=^\s*\d+\.\s|\Z)',open(prop).read(),re.S|re.M)
keep=[k for k,_ in items] if sel=='todos' else sel.split(',')
chosen=[(k,t.strip()) for k,t in items if k in keep]
if not chosen: print('nenhum item selecionado'); sys.exit(1)
s=open(ov).read(); hdr='## Fatos verificados'
block='\n'.join(f'- {t.replace(chr(10)," ")} (promovido da memória em {datetime.date.today()})' for k,t in chosen)
if hdr in s: s=s.replace(hdr, hdr+'\n'+block,1)
else: s+='\n'+hdr+'\n'+block+'\n'
open(ov,'w').write(s)
rest=[(k,t) for k,t in items if k not in keep]
open(prop,'w').write('# Propostas de memória (pendentes de aprovação)\n\n'+''.join(f'{k}. {t.strip()}\n\n' for k,t in rest))
print(f'{len(chosen)} fato(s) promovido(s) para {ov}; {len(rest)} pendente(s).')
EOF
  exit $?
fi

[ -d "$MEM" ] || { echo "sem memória nativa para este projeto: $MEM"; exit 1; }
files=$(ls "$MEM"/*.md 2>/dev/null | grep -v MEMORY.md); cnt=$(echo "$files" | grep -c . || true)
echo "memórias em $MEM: $cnt arquivo(s)"
[ "$cnt" = 0 ] && exit 0
[ $LIST = 1 ] && { for f in $files; do echo "- $(basename "$f"): $(grep -m1 '^description:' "$f" | cut -c14-120)"; done; exit 0; }
PROMPT="Abaixo estão arquivos de memória de um agente sobre o projeto $(basename "$P"). Extraia até $N FATOS verificáveis e duráveis (não preferências, não hipóteses, não tarefas), cada um em UMA linha, no formato:
<k>. <fato> — fonte: <nome do arquivo de memória>; observado em: <data do arquivo ou 'sem data'>; verificar em: <arquivo/comando do projeto que confirma>
Ignore fatos que já apareçam em context/overview.md. Responda só com a lista numerada.

=== context/overview.md atual ===
$(cat "$OV" 2>/dev/null | head -80)

=== memórias ===
$(for f in $files; do echo "--- $(basename "$f") ($(date -r "$f" +%F))"; sed -n '1,60p' "$f"; done)"
mkdir -p "$P/context"
case "$RT" in
  claude) out=$(cd "$P" && claude -p "$PROMPT" 2>/dev/null) ;;
  codex)  out=$(cd "$P" && codex exec --skip-git-repo-check "$PROMPT" 2>/dev/null | grep -vE '^(hook:|tokens used|[0-9,]+)$') ;;
  *) echo "runtime inválido"; exit 2 ;;
esac
[ -n "$out" ] || { echo "runtime $RT não respondeu — não rodado"; exit 1; }
{ echo "# Propostas de memória (pendentes de aprovação)"; echo; echo "Geradas por $RT em $(date +%F) a partir de $cnt memórias. Aprovar: scripts/promover-memoria.sh $P --aprovar <k>"; echo; echo "$out" | grep -E '^\s*[0-9]+\.' ; } > "$PROP"
echo "proposta gravada em $PROP:"; grep -E '^\s*[0-9]+\.' "$PROP" | cut -c1-160
