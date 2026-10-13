# Instruções do projeto (colar igual em todas as plataformas)

> Copie o bloco abaixo, troque `<dono>/<repo>` pelo seu repositório e cole **o mesmo texto** em cada plataforma:
> Projeto do Claude.ai (Instruções do projeto), Projeto do ChatGPT (Instruções), ambiente do Codex na nuvem
> (instruções do ambiente / AGENTS.md já está no repo) e qualquer outra IA que aceite instruções fixas.
> Se o texto mudar, mude aqui primeiro e cole de novo nas outras: este arquivo é a fonte.

```text
CONTEXTO DO PROJETO — FONTE DA VERDADE
O repositório GitHub <dono>/<repo> (privado) é a única fonte da verdade sobre este projeto/negócio.
Você acessa por conector (GitHub) ou, se estiver rodando no computador, pela pasta clonada.

LER (antes de qualquer tarefa)
1. Pegue a versão mais nova da branch main (no computador: git pull origin main), mesmo que já tenha uma cópia.
2. Leia nesta ordem: AGENTS.md → context/overview.md → context/current-state.md → tasks/current.md → handoffs/latest.md.
3. Se a sua memória ou o chat discordar do repositório, vale o repositório. Avise a diferença.

ESCREVER
- Só altere um arquivo de contexto quando eu pedir, ou quando a tarefa produzir uma decisão ou fato durável.
- Depois de alterar: commit na main com mensagem curta dizendo o que mudou e por quê, e push na hora.
- Se o push for recusado: pegue a main de novo, resolva o conflito e envie. Se resolver exigir julgamento
  (dois textos diferentes para a mesma coisa), pare e me pergunte.
- Ao terminar, diga quais arquivos mudou, em uma linha cada.

NÃO FAZER
- Não apagar nem renomear arquivos sem eu pedir.
- Não guardar senhas, chaves de API ou dados pessoais de clientes no repositório.
- Não deixar o que aprendeu só na memória do app: se for regra, vira linha no AGENTS.md;
  se for procedimento, vira skill em .agents/skills/; se for fato, vai para context/.
```
