#!/usr/bin/env bash
# test-sync-skills.sh — testa o 'install' do scripts/sync-skills.sh num HOME temporário.
# Sem dependências além de bash + coreutils + diff/find. Nunca toca ~/.claude, ~/.agents nem ~/.codex reais.
# Uso: tests/test-sync-skills.sh   (exit 0 = todos passaram)
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; SYNC="$REPO/scripts/sync-skills.sh"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
pass=0; fail=0
ok()   { echo "[passou] $1"; pass=$((pass+1)); }
bad()  { echo "[FALHOU] $1"; fail=$((fail+1)); }
check(){ if eval "$2"; then ok "$1"; else bad "$1"; fi; }

reset() { # HOME falso com destinos claude/codex vazios e uma skill 'demo' já "buildada"
  rm -rf "$T/h" "$T/src"; mkdir -p "$T/h/.claude/skills" "$T/h/.agents/skills"
  for rt in claude codex; do mkdir -p "$T/src/demo/dist/$rt/demo"; echo "demo $rt v1" > "$T/src/demo/dist/$rt/demo/SKILL.md"; done
}
run() { HOME="$T/h" SKILLS_SRC_DIR="$T/src" DSH_SKILLS_DIR="$T/dsh" V3_SKILLS_DIR="$T/v3" bash "$SYNC" install demo "$@" > "$T/out" 2>&1; }
C="$T/h/.claude/skills/demo"; X="$T/h/.agents/skills/demo"

# 1. prévia não grava nada
reset; run; rc=$?
check "prévia (sem --apply) sai 0" "[ $rc = 0 ]"
check "prévia não cria destino" "[ ! -e '$C' ] && [ ! -e '$X' ]"
check "prévia mostra CREATE para claude e codex" "[ \$(grep -c '^CREATE' '$T/out') = 2 ]"

# 2. --apply instala nos dois
run --apply; rc=$?
check "--apply sai 0" "[ $rc = 0 ]"
check "--apply grava claude e codex" "diff -q '$C/SKILL.md' '$T/src/demo/dist/claude/demo/SKILL.md' >/dev/null && diff -q '$X/SKILL.md' '$T/src/demo/dist/codex/demo/SKILL.md' >/dev/null"

# 3. idempotente: segundo --apply não muda nada
m1="$(stat -c %Y.%i "$C/SKILL.md" "$X/SKILL.md")"; sleep 1; run --apply; rc=$?
m2="$(stat -c %Y.%i "$C/SKILL.md" "$X/SKILL.md")"
check "segundo --apply sai 0 e marca UNCHANGED" "[ $rc = 0 ] && [ \$(grep -c '^UNCHANGED' '$T/out') = 2 ]"
check "segundo --apply não regrava (mtime/inode iguais)" "[ '$m1' = '$m2' ]"

# 4. skill existente diferente = recusa, e nada parcial (codex não pode ser criado)
reset; mkdir -p "$C"; echo "skill privada" > "$C/SKILL.md"; run --apply; rc=$?
check "CONFLICT recusa com exit != 0" "[ $rc != 0 ] && grep -q '^CONFLICT' '$T/out'"
check "CONFLICT preserva a skill existente" "[ \"\$(cat '$C/SKILL.md')\" = 'skill privada' ]"
check "CONFLICT não instala parcialmente no codex" "[ ! -e '$X' ]"

# 5. --replace faz backup e troca
run --apply --replace; rc=$?
check "--replace sai 0" "[ $rc = 0 ]"
check "--replace grava a versão nova" "[ \"\$(cat '$C/SKILL.md')\" = 'demo claude v1' ]"
check "--replace guarda backup fora de skills/" "grep -rqx 'skill privada' '$T/h/.claude/skills-backup'"

# 6. destino symlink = recusa (mesmo com --replace)
reset; mkdir -p "$T/fora"; ln -s "$T/fora" "$C"; run --apply --replace; rc=$?
check "symlink recusado com exit != 0" "[ $rc != 0 ] && grep -q '^SYMLINK' '$T/out'"
check "nada escrito através do symlink" "[ -z \"\$(ls -A '$T/fora')\" ] && [ ! -e '$X' ]"

# 7. symlink pendurado também é recusado
reset; ln -s "$T/nao-existe" "$X"; run --apply; rc=$?
check "symlink pendurado recusado" "[ $rc != 0 ] && [ ! -e '$C' ]"

# 8. symlink DENTRO de skill existente = recusa
reset; mkdir -p "$C"; ln -s /etc/hostname "$C/SKILL.md"; run --apply --replace; rc=$?
check "symlink interno recusado" "[ $rc != 0 ] && [ -L '$C/SKILL.md' ]"

# 9. destino ausente = SKIP (não cria a pasta do runtime)
reset; run --dsh --apply; rc=$?
check "runtime sem pasta = SKIP e não cria" "[ $rc = 0 ] && grep -q '^SKIP' '$T/out' && [ ! -e '$T/dsh' ]"

# 10. opção desconhecida e nome inválido
reset; run --aplly; rc=$?
check "opção desconhecida recusada" "[ $rc != 0 ] && [ ! -e '$C' ]"
HOME="$T/h" SKILLS_SRC_DIR="$T/src" bash "$SYNC" install ../demo --apply >/dev/null 2>&1; rc=$?
check "nome com / ou .. recusado" "[ $rc != 0 ]"

echo; echo "resultado: $pass passaram, $fail falharam"
[ $fail = 0 ]
