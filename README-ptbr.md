# Skill ↔ Power — Kit de Migração (PT-BR)

[← Voltar ao README principal](./README.md) · [🇺🇸 EN](./README-en.md) · [🇪🇸 ES](./README-es.md)

## Visão geral

Este projeto foi construído com base em **documentação oficial** e **exemplos públicos** do ecossistema Claude Code (Anthropic) e Kiro (AWS). Ele entrega três meta-ferramentas que cobrem o ciclo completo de migração entre **Claude Code Skills** e **Kiro Powers**.

| Ferramenta | Direção | Propósito |
|------------|---------|-----------|
| [`skills/skill-to-power/`](./skills/skill-to-power/) | Skill → Power | Converte uma Skill do Claude Code em uma Power do Kiro |
| [`skills/skill-creator/`](./skills/skill-creator/) | — | Cria, avalia e otimiza Skills do Kiro (SKILL.md) |
| [`skills/power-creator/`](./skills/power-creator/) | — | Cria, avalia e otimiza Powers do Kiro do zero |

## Para quem é

Qualquer pessoa que use outra ferramenta de IA — **Claude Code, Antigravity, Cursor, Codex, GitHub Copilot** — e queira migrar para o **Kiro IDE** ou **Kiro CLI**, ou o caminho inverso.

- **Vindo do Claude Code para o Kiro?** Use `skill-to-power` (se já tem Skills) ou `power-creator` (do zero).
- **Ficando no Claude Code?** Use `skill-creator` para criar e melhorar Skills compatíveis com o Kiro.

## Estrutura de uma Skill (Claude Code)

```
my-skill/
├── SKILL.md          # Obrigatório: metadados + instruções
├── scripts/          # Opcional: código executável
├── references/       # Opcional: documentação
├── assets/           # Opcional: templates e recursos
└── ...               # Quaisquer outros arquivos ou diretórios
```

## Estrutura de uma Kiro Power

```
my-power/
├── POWER.md                # autossuficiente
├── steering/               # apenas conteúdo de aprofundamento
├── hooks/                  # 3 hooks manuais
├── scripts/                # runtime.py + 9 adaptados + 2 validadores
├── eval-viewer/            # visualizador opcional
├── examples/               # power de exemplo + eval-set
└── references/             # mesclado em steering/
```

## Mapeamento Skill ↔ Power

| Claude Skill | Kiro Power | Propósito |
|--------------|------------|-----------|
| `SKILL.md` | `POWER.md` | Documentação principal (sempre carregada) |
| `references/*.md` | `steering/*.md` | Conteúdo de aprofundamento (carregado sob demanda) |
| `.claude-plugin/marketplace.json` | frontmatter do `POWER.md` | Metadados (nome, descrição, keywords) |
| `CLAUDE.md` | `steering/contributing-guidelines.md` ou `steering/development-guide.md` ou `steering/maintenance-notes.md` | Documentação para contribuidores (opcional) |
| `README.md` | Não é necessário | Documentação para o usuário (tratada pela UI de Powers) |
| `scripts/` | `scripts/` | Scripts executáveis (copiados na íntegra) |
| `examples/` | `examples/` | Exemplos de uso (copiados na íntegra) |
| `.mcp.json` | `mcp.json` | Configuração de servidores MCP |
| `.claude/commands/` | `hooks/` (Manual Trigger) | Comandos slash → hooks manuais |
| Triggering via `available_skills` do Claude | Roteamento por descrição do Kiro | Mecanismo de ativação |
| Subagente `claude -p` | `scripts/runtime.py` (Kiro CLI / IDE adapter) | Backend de execução para evals |

## Tipos de Hook do Kiro

Hooks do Kiro disparam automações em pontos específicos:

- **Prompt Submit** — quando o usuário envia um prompt (acesso via `USER_PROMPT`)
- **Agent Stop** — quando o agente termina sua resposta
- **Pre Tool Use** / **Post Tool Use** — antes/depois de invocar uma tool (filtros: `read`, `write`, `shell`, `web`, `spec`, `*`, `@mcp`, `@powers`, `@builtin`)
- **File Create** / **File Save** / **File Delete** — por padrão de arquivo
- **Pre/Post Task Execution** — antes/depois de uma task de spec
- **Manual Trigger** — execução sob demanda

## Referências

- [A Guide for Migrating Claude Code Skills to Kiro Powers — AWS Builder](https://builder.aws.com/content/39DLiJ3W2dTp53IqbWNxsJYgcHB/a-guide-for-migrating-claude-code-skills-to-kiro-powers)
- [Repositório oficial de Skills da Anthropic](https://github.com/anthropics/skills)
- [`skill-creator` da Anthropic](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
- [`internal-comms` da Anthropic](https://github.com/anthropics/skills/tree/main/skills/internal-comms)
- [Exemplo de Power com scripts (`aidlc_power`)](https://github.com/aws-samples/sample-power-aidlc-all/tree/main/aidlc_power)
