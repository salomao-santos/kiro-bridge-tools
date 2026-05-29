# Kiro Bridge Tools

Tools that act as bridges between AI coding ecosystems and Kiro.

[← Volver al README principal](./README.md) · [🇧🇷 PT-BR](./README-ptbr.md) · [🇺🇸 EN](./README-en.md)

## Visión general

Este proyecto fue construido sobre **documentación oficial** y **ejemplos públicos** de Anthropic y Kiro (AWS). Entrega tres meta-herramientas que cubren el ciclo completo de migración entre **Skills** y **Kiro Powers**.

| Herramienta | Dirección | Propósito |
|-------------|-----------|-----------|
| [`skills/skill-to-power/`](./skills/skill-to-power/) | Skill → Power | Convierte una Skill en una Power de Kiro |
| [`skills/skill-creator/`](./skills/skill-creator/) | — | Crea, evalúa y optimiza Skills de Kiro (SKILL.md) |
| [`skills/power-creator/`](./skills/power-creator/) | — | Crea, evalúa y optimiza Powers de Kiro desde cero |

## ¿Para quién es?

Cualquiera que use otra herramienta de IA — **Antigravity, Cursor, Codex, GitHub Copilot** — y quiera migrar a **Kiro IDE** o **Kiro CLI**, o el camino inverso.

- **¿Viniendo de otra herramienta a Kiro?** Usa `skill-to-power` (si ya tienes Skills) o `power-creator` (desde cero).
- **¿Usando otra herramienta de IA?** Usa `skill-creator` para crear y mejorar Skills compatibles con Kiro.

## Estructura de una Skill

```
my-skill/
├── SKILL.md          # Obligatorio: metadatos + instrucciones
├── scripts/          # Opcional: código ejecutable
├── references/       # Opcional: documentación
├── assets/           # Opcional: plantillas y recursos
└── eval-viewer/      # Opcional: visor de evaluación
```

## Estructura de una Kiro Power

```
my-power/
├── POWER.md                # autosuficiente
├── steering/               # solo contenido de profundización
├── hooks/                  # 3 hooks manuales
├── scripts/                # runtime.py + 9 adaptados + 2 validadores
├── eval-viewer/            # visor opcional
├── examples/               # power de ejemplo + eval-set
└── references/             # fusionado en steering/
```

## Mapeo Skill ↔ Power

| Skill | Kiro Power | Propósito |
|--------------|------------|-----------|
| `SKILL.md` | `POWER.md` | Documentación principal (siempre cargada) |
| `references/*.md` | `steering/*.md` | Contenido de profundización (carga bajo demanda) |
| `.claude-plugin/marketplace.json` | frontmatter de `POWER.md` | Metadatos (nombre, descripción, keywords) |
| `CLAUDE.md` | `steering/contributing-guidelines.md` o `steering/development-guide.md` o `steering/maintenance-notes.md` | Documentación para contribuidores (opcional) |
| `README.md` | No es necesario | Documentación para el usuario (la maneja la UI de Powers) |
| `scripts/` | `scripts/` | Scripts ejecutables (copiados íntegros) |
| `examples/` | `examples/` | Ejemplos de uso (copiados íntegros) |
| `.mcp.json` | `mcp.json` | Configuración de servidores MCP |
| `.claude/commands/` | `hooks/` (Manual Trigger) | Comandos slash → hooks manuales |
| Triggering vía `available_skills` | Enrutamiento por descripción de Kiro | Mecanismo de activación |
| Subagente `claude -p` | `scripts/runtime.py` (Kiro CLI / IDE adapter) | Backend de ejecución para evals |

## Tipos de Hook de Kiro

Los hooks disparan automatizaciones en puntos específicos:

- **Prompt Submit** — cuando el usuario envía un prompt (acceso vía `USER_PROMPT`)
- **Agent Stop** — cuando el agente termina su respuesta
- **Pre Tool Use** / **Post Tool Use** — antes/después de invocar una tool (filtros: `read`, `write`, `shell`, `web`, `spec`, `*`, `@mcp`, `@powers`, `@builtin`)
- **File Create** / **File Save** / **File Delete** — por patrón de archivo
- **Pre/Post Task Execution** — antes/después de una task de spec
- **Manual Trigger** — ejecución bajo demanda

## Referencias

- [A Guide for Migrating Skills to Kiro Powers — AWS Builder](https://builder.aws.com/content/39DLiJ3W2dTp53IqbWNxsJYgcHB/a-guide-for-migrating-claude-code-skills-to-kiro-powers)
- [Repositorio oficial de Skills de Anthropic](https://github.com/anthropics/skills)
- [`skill-creator` de Anthropic](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
- [`internal-comms` de Anthropic](https://github.com/anthropics/skills/tree/main/skills/internal-comms)
- [Power de ejemplo con scripts (`aidlc_power`)](https://github.com/aws-samples/sample-power-aidlc-all/tree/main/aidlc_power)
