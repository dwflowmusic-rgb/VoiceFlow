
# **FASE 1: RECONHECIMENTO INICIAL**

**Whispo** é uma ferramenta Electron de ditado de voz alimentada por IA que captura áudio através de teclas de atalho, transcreve usando Whisper (OpenAI ou Groq), e insere o texto transcrito em aplicações ativas no SO. O sistema integra suporte a pós-processamento com LLMs e armazena dados localmente. Construído em TypeScript com React no frontend, arquitetura padrão Electron com componente Rust isolado (whispo-rs).

## **ARQUIVOS E PASTAS DISPONÍVEIS**

### Raiz

- `.editorconfig`, `.gitignore`, `.npmrc`, `.prettierignore`, `.prettierrc` — Configurações de tooling
- `package.json`, `pnpm-lock.yaml` — Gerenciamento de dependências (pnpm)
- `tsconfig.json`, `tsconfig.node.json`, `tsconfig.web.json` — Configuração TypeScript
- `electron.vite.config.ts`, `electron-builder.config.cjs` — Build Electron/Vite
- `tailwind.config.js`, `postcss.config.js`, `components.json` — Styling (Tailwind + Radix)
- `README.md`, `LICENSE` (AGPL-3.0)

### Diretórios Críticos

- **`src/main/`** — Processo principal Electron (13 arquivos)
    
    - `index.ts`, `config.ts`, `state.ts`, `window.ts` — Lifecycle e configuração
    - `keyboard.ts`, `tray.ts` — Integração SO (hotkeys, system tray)
    - `llm.ts` — Integração com LLMs (OpenAI, Groq, Gemini)
    - `renderer-handlers.ts`, `tipc.ts` — Comunicação com renderer
    - `updater.ts` — Auto-update
- **`src/renderer/`** — Processo de renderização (React)
    
    - `src/App.tsx`, `src/main.tsx` — Raiz React
    - `src/pages/` — Rotas (setup, settings, panel)
    - `src/components/` — Componentes React (UI radix-based)
    - `src/lib/` — Utilitários (recorder, sound, tipc-client, query-client)
- **`src/preload/`** — Bridge de segurança Electron
    
- **`src/shared/`** — Tipos e constantes compartilhadas
    
- **`whispo-rs/`** — Componente Rust (probável gravação de áudio low-level)
    
- **`.github/`** — Workflows CI/CD
    
- **`scripts/`**, **`build/`**, **`resources/`** — Build artifacts e scripts
    

## **TECH STACK IDENTIFICADO**

|Aspecto|Tecnologia|
|---|---|
|**Desktop**|Electron 31 + Vite|
|**Frontend**|React 18 + React Router 6|
|**UI**|Radix UI + Tailwind CSS 3.4|
|**Backend/IPC**|@egoist/tipc (typed inter-process communication)|
|**LLM**|@google/generative-ai + OpenAI/Groq (via API)|
|**Estado**|React Query (TanStack)|
|**Áudio**|Gravação nativa + Rust (whispo-rs)|
|**Build**|electron-builder + electron-vite|
|**Linguagem**|TypeScript 5.6|
|**Gestão de Pacotes**|pnpm 9.12|

---

## **PRÓXIMOS PASSOS**

✅ **Contexto suficiente para análise detalhada?** SIM

Pronto para prosseguir para:

1. **FASE 2** — Arquitetura de componentes (diagrama Mermaid)
2. **FASE 3** — Fluxos críticos (gravação → transcrição → inserção)
3. **FASE 4** — Regras de negócio
4. **FASE 5** — Interfaces/contratos (IPC, APIs)
5. **FASE 6** — Especificação Antigravity

**Qual análise você deseja?**

- `análise completa` — todas as 6 fases sequencialmente
- `fase específica` — forneça número/nome
- `fluxo específico` — ex: "gravação de áudio → transcrição"