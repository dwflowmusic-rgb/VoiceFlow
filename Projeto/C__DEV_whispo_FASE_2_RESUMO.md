# FASE 2: ARQUITETURA DE COMPONENTES - RESUMO EXECUTIVO

## 1. Topologia de Alto Nível

```
Global Hotkey (OS Level)
  ↓
whispo-rs (Rust Binary) 
  ├─ rdev: captura eventos de teclado globalmente
  └─ enigo: simula digitação (keystroke synthesis)
  ↓
main/keyboard.ts (Node.js - Main Process)
  ├─ Escuta eventos via stdout do processo Rust
  ├─ Gerencia estado de gravação (isHoldingCtrlKey, timers)
  └─ Orquestra: window.ts, state.ts, tipc.ts
  ↓
Electron - Múltiplos Processos
  ├─ Main Process: orquestração, APIs, persistência
  ├─ Renderer Process: React UI com React Router v6
  ├─ Preload Bridge: expõe electronAPI via contextBridge
  └─ IPC Tipado: @egoist/tipc (type-safe RPC)
  ↓
APIs Externas (HTTP)
  ├─ Whisper: OpenAI ou Groq (transcrição)
  └─ LLM: OpenAI, Groq, Gemini (pós-processamento)
```

## 2. Componentes Principais (24 no Total)

### Main Process (Node.js) - 10 módulos

| Módulo | Responsabilidade | Padrão |
|--------|------------------|--------|
| `index.ts` | Inicializa app, registra IPC, cria janelas | Singleton Lifecycle |
| `window.ts` | Cria/gerencia 3 janelas (main, panel, setup) | Factory + Singleton |
| `keyboard.ts` | Hotkey listener → executa recording workflow | Observer (Rust IPC) |
| `config.ts` | Persiste config em JSON (appData/config.json) | Singleton Repository |
| `state.ts` | Estado global mínimo (`isRecording: boolean`) | Singleton Object |
| `tipc.ts` | Router RPC tipado (25+ procedures) | Router + Service Locator |
| `llm.ts` | Abstração LLM providers (OpenAI/Groq/Gemini) | Strategy Pattern |
| `tray.ts` | Menu sistema + ícone sincronizado com state | Singleton + Observer |
| `updater.ts` | Auto-update via electron-updater | Singleton |
| `menu.ts` | Menu padrão Electron | Configuration |

### Renderer Process (React) - 8 componentes

| Componente | Responsabilidade | Tipo |
|-----------|------------------|------|
| `App.tsx` | Root com RouterProvider + lazy Updater | Component |
| `router.tsx` | React Router v6 com lazy loading | Router Config |
| `pages/index.tsx` | Histórico de gravações | Page |
| `pages/panel.tsx` | UI de captura com visualizador | Page |
| `pages/setup.tsx` | Primeira execução + permissões | Page |
| `pages/settings-*.tsx` | Config UI (general, providers, data) | Pages |
| `lib/recorder.ts` | MediaRecorder + AudioContext + EventEmitter | Class |
| `lib/tipc-client.ts` | Cliente RPC tipado | Client |

### Rust Native - 1 executável

| Componente | Responsabilidade | Stack |
|-----------|------------------|-------|
| `whispo-rs` | CLI com 2 comandos: `listen` (hotkeys), `write` (keystroke) | Rust (rdev + enigo) |

## 3. Padrões de Design

**Observer Pattern**: Recorder emite eventos (`record-start`, `record-end`, `visualizer-data`)

**Strategy Pattern**: LLM provider selection baseado em config

**Factory Pattern**: Criação de janelas (`createMainWindow`, `createPanelWindow`, `createSetupWindow`)

**Singleton**: ConfigStore, state, tray, updater

**Type-Safe RPC**: @egoist/tipc (raro em Electron, muito desejável)

**Security Bridge**: Preload com contextBridge isola contexto

## 4. Fluxo de Dados - Gravação Simplificada

```
User holds Ctrl
  → whispo-rs (rdev) detects KeyPress
  → keyboard.ts processes event
  → showPanelWindowAndStartRecording()
  → rendererHandlers.startRecording.send() [IPC]
  → panel.tsx starts Recorder (MediaRecorder API)
  → User releases Ctrl
  → stopRecordingAndHidePanelWindow()
  → panel.tsx sends blob to tipcClient.createRecording()
  → main/tipc.ts → Whisper API (FormData with WebM)
  → response: { text: "transcribed text" }
  → postProcess with LLM (opcional)
  → clipboard.writeText() + writeText() (keystroke simulation)
  → Text appears in focused application
```

## 5. Acoplamento Analysis

**Tight Coupling**: Main↔Rust (necessário), Renderer↔Config (type-safe)

**Loose Coupling**: Recorder↔Visualizer (Observer), Sound (isolated), Config storage

**Fácil Trocar**: UI framework, HTTP client, router, state library

**Hard-coded**: Keyboard state machine, LLM provider selection (factory seria melhor)

## 6. Tech Stack

| Camada | Tecnologia |
|--------|-----------|
| **Desktop** | Electron 31 + Vite |
| **Frontend** | React 18 + React Router 6 |
| **UI** | Radix UI + Tailwind CSS |
| **IPC** | @egoist/tipc (typed RPC) |
| **State** | React Query (TanStack) |
| **Native Audio** | MediaRecorder + AudioContext (Web API) |
| **Native Hotkeys** | Rust (rdev) |
| **Native Keystroke** | Rust (enigo) |
| **Build** | electron-builder + electron-vite |
| **Language** | TypeScript 5.6 |

## 7. Decisões Arquiteturais

### Por que @egoist/tipc?
- ✅ Type safety end-to-end (raramente visto em Electron)
- ✅ Autocomplete em chamadas RPC
- ✅ Validação automática de input
- ✅ Eventos tipados

### Por que Rust para Hotkeys?
- ✅ `rdev` é maduro e cross-platform
- ✅ Performance sem GC (crítico para event loop global)
- ✅ Simplicidade: binário compilado isolado
- ⚠️ Tradeoff: complexidade de build e distribuição

### Por que Tri-Processo Electron?
- ✅ Isolamento de crashes (renderer não mata main)
- ✅ UI nunca bloqueia
- ✅ Responsabilidades claras
- ✅ Preload fornece segurança

### Por que JSON simples para config?
- ✅ Human-readable, portable, sem dependências
- ⚠️ Seria bom adicionar `zod` para schema validation

## 8. Pontos de Melhoria (Não-bloqueantes)

1. **Extrair máquina de estados** de `keyboard.ts`
   - Classe `KeyboardStateMachine` com transições explícitas

2. **Factory para LLM providers**
   - Registry pattern em vez de switch statement

3. **Validação schema com Zod**
   - Validar config.json na carga

4. **Testes unitários para Recorder**
   - Mock EventEmitter, simular audio frames

5. **Documentação de fluxo completo**
   - ✅ Feita em FASE 3

---

**Score Geral: 7.3/10** - Muito bem arquitetonado para desktop app Electron

**Próximo: FASE 3** - Fluxos de execução com diagramas de sequência detalhados
