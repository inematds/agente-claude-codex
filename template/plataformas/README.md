# Um contexto, várias plataformas

Este repositório é a **camada de contexto portátil**: o contexto mora aqui (num GitHub **privado** que é seu)
e cada IA só ganha acesso, instruções e um teste. Trocou de IA? O contexto continua.

```
  Claude.ai · Claude Code · ChatGPT · Codex · Gemini     ← onde a IA trabalha (troca quando quiser)
                    │ git / conector GitHub / MCP          ← a ponte
  AGENTS.md · context/ · tasks/ · handoffs/ · skills      ← o contexto que você controla (este repo)
```

## O que viaja e o que não viaja

| Viaja (está no repo) | Não viaja (refaz em cada app) |
|---|---|
| AGENTS.md, context/, decisões, skills, tarefas, handoffs | histórico de chat, memória do app, escolha de modelo |

## Ligar cada plataforma (3 passos: acesso, instruções, teste)

| Plataforma | Acesso | Instruções | Teste |
|---|---|---|---|
| **Claude Code / Codex CLI** (computador) | `git clone` do repo | lê `AGENTS.md` sozinho (o Claude via `CLAUDE.md` → `@AGENTS.md`) | "leia o contexto e diga o objetivo do projeto" |
| **Gemini CLI** | `git clone` | `GEMINI.md` → `@AGENTS.md` | o mesmo |
| **Claude.ai — Projeto** | Personalizar → Conectores → GitHub (integração + MCP, dois sinais verdes) | colar `instrucoes-projeto.md` nas instruções do projeto | pedir para ler `context/overview.md` e editar uma linha de teste |
| **ChatGPT — Projeto** | Configurações → Conectores → GitHub | colar o mesmo bloco nas instruções do projeto | pedir para criar `context/teste.md` |
| **Codex na nuvem** | ambiente com o repo selecionado | `AGENTS.md` já está no repo; o bloco vai nas instruções do ambiente | pedir uma edição e conferir o commit |

**Prova de que funciona:** crie um arquivo por uma plataforma (ex.: ChatGPT) e peça para a outra (ex.: Claude) ler e
editar. Os dois commits aparecem no histórico do GitHub. Depois apague o arquivo de teste.

## Onde guardar o quê

- **Documentos** (negócio, voz, clientes, ofertas, decisões, skills): este repo, em markdown.
- **Dados que mudam toda hora** (tarefas da equipe, pedidos, status): um banco (ex.: Supabase), não o repo.
- **Equipe sem Git:** Notion funciona como lar de documentos; Google Drive hoje lê mas não edita markdown bem.

## Cuidados

1. Repositório **privado**, sempre.
2. Nada de senha ou chave aqui (use o cofre/variáveis de cada plataforma).
3. O que a IA aprender vira regra (AGENTS.md), skill (.agents/skills/) ou fato (context/), nunca só memória do app.
4. Sessão terminou? Grave o handoff (`handoffs/history/<UTC>.md` + `handoffs/latest.md`): a próxima IA,
   qualquer que seja, continua dali.
