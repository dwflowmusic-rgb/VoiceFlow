# VoiceFlow Transcriber — Briefing & PDR Master (End-to-End)

**Documento de Referência Master**  
**Versão:** 1.0  
**Data:** 09/01/2026  
**Status:** Production Ready (Fase 4 Concluída)

---

# 📋 PARTE I: BRIEFING EXECUTIVO

## 1. Visão do Produto

**VoiceFlow Transcriber** é uma ferramenta de produtividade que elimina a barreira entre pensamento e texto escrito. Diferente de ditadores comuns, o VoiceFlow não apenas transcreve — ele **compreende**, **corrige** e **entrega** o texto exatamente onde você precisa, sem interromper seu fluxo de trabalho.

### Proposta de Valor

> **"Transforme sua voz em escrita profissional, exatamente onde você precisa, com apenas um botão."**

Enquanto ferramentas tradicionais exigem que você:

1. Ative um gravador
2. Fale
3. Aguarde processamento
4. Copie o resultado
5. Abra o destino
6. Cole e corrija

O VoiceFlow reduz isso a:

1. **Segure CapsLock**
2. **Fale**
3. **Solte**

O texto surge automaticamente no cursor, já polido e formatado.

## 2. Problema Resolvido

### 2.1 Cenário Atual (Sem VoiceFlow)

**Profissionais de conhecimento enfrentam 3 gargalos:**

| Gargalo | Impacto | Custo Estimado |
|---------|---------|----------------|
| **Velocidade de Digitação** | Pensamento flui a 150 palavras/min, dedos digitam a 40 palavras/min | **73% de produtividade perdida** |
| **Contexto Switching** | Abrir/fechar apps de transcrição quebra o flow | **23 minutos** para recuperar foco (Estudo UC Irvine) |
| **Qualidade de Escrita Sob Pressão** | Textos apressados têm erros de concordância, pontuação | **Retrabalho de 15-30%** do tempo |

### 2.2 Solução Existentes (Limitações)

| Ferramenta | Problema |
|------------|----------|
| **Google Docs Voice Typing** | Requer Chrome aberto + clicar para ativar. Não cola automaticamente. |
| **Windows Speech Recognition** | Precisão baixa, não funciona em todos os apps. |
| **Transcrição Manual (Otter.ai, etc)** | Upload de arquivo, espera, cópia manual. Latência de 30s+. |

**Nenhuma ferramenta combina:**
✅ Ativação instantânea (sem sair do teclado)  
✅ Transcrição de qualidade (Whisper)  
✅ Polimento por IA (Gemini)  
✅ Colagem automática no contexto  

## 3. Público-Alvo

### Persona Primária: **Paulo, o Gestor de Projetos**

- **Idade:** 32 anos
- **Rotina:** 8+ reuniões/dia, precisa documentar decisões rapidamente
- **Dor:** Perde 40min/dia reescrevendo notas de reunião
- **Ganho com VoiceFlow:** Grava observações durante a reunião, texto limpo surge no relatório instantaneamente

### Persona Secundária: **Ana, a Desenvolvedora Full-Stack**

- **Idade:** 28 anos
- **Rotina:** Documenta código, escreve issues técnicas
- **Dor:** Typing speed limita documentação (prefere programar a escrever)
- **Ganho com VoiceFlow:** Explica função verbalmente enquanto codifica, documentação surge no docstring

## 4. Diferencial Competitivo

### 4.1 Matriz de Comparação

| Feature | VoiceFlow | Google Docs Voice | Whisper Desktop | Otter.ai |
|---------|-----------|-------------------|-----------------|----------|
| **Ativação sem mouse** | ✅ CapsLock | ❌ Requer clique | ❌ Requer interface | ❌ Upload manual |
| **Colagem auto no contexto** | ✅ | ❌ | ❌ | ❌ |
| **Polimento por IA** | ✅ Gemini | ❌ | ❌ | ⚠️ Básico |
| **Offline (transcrição)** | ❌ API Groq | ✅ | ✅ | ❌ |
| **Custo** | $0.006/min* | Grátis** | Grátis | $8.33/mês |
| **Latência média** | 2-4s | 1-2s | 5-10s | 30s+ |

*Baseado em Groq Whisper + Gemini Flash  
**Limitado a Google Workspace

### 4.2 Moat Técnico

1. **Colagem Inteligente (Smart Paste):** Detecta se você mudou de janela — se sim, mantém no clipboard; se não, cola automaticamente. Nenhuma ferramenta comercial faz isso.
2. **Anti-Alucinação em Silêncio:** Filtros específicos evitam que o Whisper invente textos quando você não fala (problema comum em transcrições).
3. **CapsLock Transparente:** Hook de teclado que suprime o toggle do LED quando usado como gravador, mas preserva o comportamento normal em taps rápidos.

---

# 🛠️ PARTE II: PDR (PLANO DE DESENVOLVIMENTO DE REQUISITOS)

## 1. Requisitos Funcionais

### RF-001: Gravação de Áudio via Hotkey

**Prioridade:** Crítica  
**Descrição:** O sistema DEVE capturar áudio do microfone quando o usuário segurar a tecla CapsLock por >500ms.  
**Critério de Aceitação:**

- Latência de detecção < 50ms
- Arquivo WAV temporário criado em `%TEMP%`
- Duração mínima de 0.5s para evitar cliques acidentais

### RF-002: Transcrição via API Groq

**Prioridade:** Crítica  
**Descrição:** O áudio capturado DEVE ser enviado ao Groq (Whisper distil-large-v3-en) para transcrição.  
**Critério de Aceitação:**

- Taxa de sucesso > 95%
- Timeout de 30s
- Fallback para mensagem de erro amigável em caso de falha de rede

### RF-003: Polimento Textual via Gemini

**Prioridade:** Alta  
**Descrição:** O texto bruto DEVE ser enviado ao Gemini para correção gramatical e formatação.  
**Critério de Aceitação:**

- Remove vícios de fala ("né", "tipo assim")
- Adiciona pontuação correta
- Mantém significado original (não inventa informações)
- Retorna texto em formato de prosa (não listas)

### RF-004: Persistência de Histórico

**Prioridade:** Alta  
**Descrição:** Toda transcrição DEVE ser salva em banco SQLite local antes de qualquer operação de clipboard.  
**Critério de Aceitação:**

- Salvamento bloqueante (Write-Ahead Logging)
- Se SQLite falhar, criar arquivo emergencial no Desktop
- Retenção de 5 dias (limpeza automática)

### RF-005: Colagem Inteligente

**Prioridade:** Média  
**Descrição:** Se o usuário mantiver foco na mesma janela, o sistema DEVE colar automaticamente via Ctrl+V simulado.  
**Critério de Aceitação:**

- Detectar mudança de foco com Win32 `GetForegroundWindow`
- Se foco alterado, apenas copiar para clipboard + notificar
- Latência de colagem < 100ms

### RF-006: Interface de Histórico

**Prioridade:** Média  
**Descrição:** O usuário DEVE poder visualizar, buscar e excluir transcrições antigas.  
**Critério de Aceitação:**

- Busca full-text em texto bruto e polido
- Exibição de 100 últimos registros com paginação
- Exclusão individual e "limpar tudo" com confirmação

### RF-007: Widget de Status (OSD)

**Prioridade:** Média  
**Descrição:** Feedback visual flutuante mostrando estado atual (Gravando/Processando/Concluído).  
**Critério de Aceitação:**

- Frameless, always-on-top
- Cores: Vermelho (Recording), Amarelo (Processing), Verde (Success)
- Auto-hide após 3s em sucesso

### RF-008: Inicialização Automática

**Prioridade:** Baixa  
**Descrição:** O usuário PODE configurar o app para iniciar com o Windows.  
**Critério de Aceitação:**

- Toggle no menu da bandeja
- Registra entrada em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- Funciona com pythonw.exe (modo silencioso)

### RF-009: Auto-Enter (Novo - Fase 5 Parcial)

**Prioridade:** Baixa  
**Descrição:** Após colar automaticamente, o sistema PODE pressionar Enter se configurado.  
**Critério de Aceitação:**

- Delay de 800ms após Ctrl+V
- Toggle no menu da bandeja
- Persistido em config.json

## 2. Requisitos Não-Funcionais

### RNF-001: Performance

- **Latência End-to-End:** < 5s (do soltar CapsLock até colagem)
  - Transcrição (Groq): ~1-2s
  - Polimento (Gemini): ~1-2s
  - Persistência (SQLite): ~50ms
  - Colagem: ~100ms
- **Consumo de RAM:** < 80MB em idle, < 150MB durante processamento
- **Uso de CPU:** < 5% em idle

### RNF-002: Confiabilidade

- **Uptime:** > 99% (aplicação deve se recuperar de crashes de APIs)
- **Taxa de Persistência:** 100% (Write-Ahead Logging garante salvamento)
- **Recovery:** Se app crashar durante gravação, áudio temporário deve ser preservado

### RNF-003: Segurança

- **API Keys:** Armazenadas em `config.json` local (não versionado no Git)
- **Dados:** Histórico em SQLite local, sem envio para servidores terceiros
- **Privacidade:** Áudio temporário deletado após transcrição

### RNF-004: Usabilidade

- **Onboarding:** Usuário deve conseguir gravar primeira transcrição em < 2 minutos
- **Feedback:** Toda ação deve ter feedback visual (widget ou notificação)
- **Acessibilidade:** Atalho único (CapsLock) acessível sem mouse

### RNF-005: Manutenibilidade

- **Cobertura de Testes:** > 70% em lógica crítica (FSM, Persistência, APIs)
- **Documentação:** README + Docstrings em português
- **Logging:** Todos eventos importantes logados em `debug_log.txt`

---

## 3. Arquitetura do Sistema

### 3.1 Visão de Alto Nível

```
┌──────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                 │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Tray Icon  │  │ Status Widget │  │ History Window  │  │
│  │ (Menu)     │  │ (OSD)         │  │ (SQLite UI)     │  │
│  └────────────┘  └──────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────┘
                           │ (Qt Signals)
┌──────────────────────────────────────────────────────────┐
│                   CAMADA DE APLICAÇÃO                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │           VoiceFlowApp (voiceflow.py)            │   │
│  │  - Inicialização & Orquestração                 │   │
│  │  - Callbacks de UI                               │   │
│  │  - Gerenciamento de Configuração                │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                           │ (Method Calls)
┌──────────────────────────────────────────────────────────┐
│                    CAMADA DE DOMÍNIO                      │
│  ┌─────────────────┐  ┌───────────────────────────┐     │
│  │ MaquinaEstados  │  │   GerenciadorHistorico    │     │
│  │ (FSM Core)      │  │   (SQLite CRUD)           │     │
│  └─────────────────┘  └───────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
                           │ (Dependencies)
┌──────────────────────────────────────────────────────────┐
│                  CAMADA DE INFRAESTRUTURA                 │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐  │
│  │ ClienteAPI   │ │ KeyboardHook│ │ DetectorFoco     │  │
│  │ (Groq/Gemini)│ │ (Win32 Hook)│ │ (Win32 Focus)    │  │
│  └──────────────┘ └─────────────┘ └──────────────────┘  │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────────┐  │
│  │CapturadorAudio│ │   Logger    │ │ ClipboardManager │  │
│  │ (PyAudio)    │ │ (File Log)  │ │ (Win32 Clipboard)│  │
│  └──────────────┘ └─────────────┘ └──────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Componentes Detalhados

#### 3.2.1 Camada de Apresentação (UI)

**`ui/icone_bandeja.py`** — System Tray Icon

- **Responsabilidade:** Menu de contexto na bandeja do Windows
- **Dependências:** PySide6 (QSystemTrayIcon, QMenu)
- **Callbacks:**
  - Ver Histórico → Abre `JanelaHistorico`
  - Iniciar com Windows → Registra/Remove do Registry
  - Auto-Enter → Toggle e salva em config.json
  - Idioma de Saída → PT-BR/EN-US/ES-ES (Fase 5)
  - Sair → Encerra app gracefully

**`ui/status_widget.py`** — OSD Widget

- **Responsabilidade:** Feedback visual flutuante
- **Estados:**
  - `IDLE` → Oculto
  - `RECORDING` → Vermelho + Timer pulsante
  - `PROCESSING` → Amarelo + Spinner
  - `SUCCESS` → Verde + ✓ (auto-hide em 3s)
  - `ERROR` → Vermelho + ✗
- **Tecnologia:** Qt Frameless Window com opacity effects

**`ui/janela_historico.py`** — History Manager

- **Responsabilidade:** CRUD de transcrições históricas
- **Features:**
  - Busca full-text (case-insensitive)
  - Preview de 50 caracteres
  - Botão "Copiar" e "Excluir"
  - "Limpar Tudo" com dupla confirmação

#### 3.2.2 Camada de Aplicação

**`voiceflow.py`** — Orquestrador Principal

- **Responsabilidade:** Bootstrap da aplicação
- **Inicialização:**
  1. Carrega `config.json`
  2. Inicializa logger
  3. Cria componentes (FSM, Histórico, UI)
  4. Registra callbacks cross-component
  5. Inicia detector de teclado
  6. Entra em event loop Qt

**Callbacks Principais:**

```python
def _abrir_historico() -> None
def _toggle_autostart(ativar: bool) -> None
def _toggle_auto_enter(ativar: bool) -> None
def _on_mudanca_estado(estado: Estado) -> None  # Atualiza widget
def _on_nova_transcricao() -> None  # Refresh history window
```

#### 3.2.3 Camada de Domínio

**`core/maquina_estados.py`** — Finite State Machine

- **Responsabilidade:** Orquestração do fluxo de transcrição
- **Estados:**

  ```
  IDLE → RECORDING → TRANSCRIBING → POLISHING → COMPLETE → IDLE
                  ↘ ERROR ↗
  ```

**Transições:**

| De | Para | Trigger | Ação |
|----|------|---------|------|
| IDLE | RECORDING | `iniciar_gravacao()` | Inicia captura de áudio |
| RECORDING | TRANSCRIBING | `parar_gravacao()` | Salva WAV, envia para thread |
| TRANSCRIBING | POLISHING | Groq retorna texto | Envia para Gemini |
| POLISHING | COMPLETE | Gemini retorna texto | Salva no histórico (bloqueante) |
| COMPLETE | IDLE | `_finalizar()` | Copia para clipboard + cola (se foco preservado) |
| ANY | ERROR | Exception | Notifica erro, limpa recursos |

**Fluxo de Dados (Thread Safety):**

```python
# Thread Principal (Qt Event Loop)
iniciar_gravacao() → CapturadorAudio.iniciar()

# Thread Secundária (Worker Thread)
_processar_audio():
    1. ClienteAPI.transcrever(audio) → texto_bruto
    2. ClienteAPI.polir(texto_bruto) → texto_polido
    3. GerenciadorHistorico.salvar(bruto, polido) → [BLOQUEANTE]
    4. callback_clipboard(texto_polido) → [SINAL CROSS-THREAD]
    5. obter_janela_ativa() → verifica foco
    6. se foco == inicial: simular_ctrl_v()
    7. _finalizar() → limpa WAV temporário
```

**`core/historico.py`** — Persistência SQLite

- **Schema:**

  ```sql
  CREATE TABLE transcricoes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp TEXT NOT NULL,
      texto_bruto TEXT NOT NULL,
      texto_polido TEXT NOT NULL,
      duracao_segundos REAL NOT NULL
  );
  CREATE INDEX idx_timestamp ON transcricoes(timestamp DESC);
  ```

- **Localização:** `%APPDATA%/VoiceFlow/historico.db`
- **Operações:**
  - `salvar(bruto, polido, duracao) → int`
  - `listar(limite, offset) → List[RegistroTranscricao]`
  - `buscar(termo) → List[RegistroTranscricao]`
  - `excluir_por_id(id) → bool`
  - `limpar_antigos(dias=5) → int`

#### 3.2.4 Camada de Infraestrutura

**`core/cliente_api.py`** — API Abstraction

- **Groq (Transcrição):**
  - Endpoint: `https://api.groq.com/v1/audio/transcriptions`
  - Modelo: `distil-whisper-large-v3-en`
  - Formato: `multipart/form-data` (WAV file)
  - Retry: 3 tentativas com backoff exponencial
  
- **Gemini (Polimento):**
  - Endpoint: `https://generativelanguage.googleapis.com/v1beta/chat/completions`
  - Modelo: `gemini-1.5-flash`
  - Prompt: `PROMPT_POLIMENTO` (vide seção 4.3)

**`core/input_hook.py`** — Keyboard Hook (Win32)

- **Tecnologia:** `SetWindowsHookEx(WH_KEYBOARD_LL, ...)`
- **Lógica:**

  ```python
  if key == VK_CAPITAL:
      if event == WM_KEYDOWN:
          timestamp_inicio = time.time()
          return 1  # Bloqueia propagação (LED não acende)
      elif event == WM_KEYUP:
          duracao = time.time() - timestamp_inicio
          if duracao < 0.5:  # Tap
              UnhookWindowsHookEx() # Temporário
              SendInput(VK_CAPITAL Down + Up) # Simula toggle real
              SetWindowsHookEx() # Reinstala
          else:  # Hold
              callback_parar_gravacao()
          return 1
  ```

**`core/captura_audio.py`** — Audio Recording

- **Biblioteca:** PyAudio (PortAudio wrapper)
- **Configuração:**
  - Sample Rate: 16kHz
  - Channels: Mono
  - Format: INT16
  - Chunk Size: 1024 frames
- **Output:** WAV file em `%TEMP%/voiceflow_rec_<timestamp>.wav`

**`core/detector_foco.py`** — Focus Detection

- **Win32 APIs:**
  - `GetForegroundWindow() → HWND`
  - `SendInput(INPUT[], ...) → Simula Ctrl+V`
  - `SendInput(VK_RETURN, ...) → Simula Enter` (Auto-Enter)

**`core/autostart.py`** — Startup Management

- **Registry Key:** `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- **Valor:** `"C:\Path\to\pythonw.exe" "C:\Path\to\voiceflow.py"`
- **Operações:**
  - `verificar_autostart() → bool`
  - `definir_autostart(ativar: bool) → bool`

### 3.3 Stack Tecnológico

| Camada | Tecnologia | Versão | Justificativa |
|--------|-----------|--------|---------------|
| **UI Framework** | PySide6 (Qt for Python) | 6.6+ | Nativo, cross-thread signals, tray icon |
| **Audio Capture** | PyAudio | 0.2.14 | Wrapper Python para PortAudio, estável |
| **Win32 Hooks** | ctypes | Built-in | Acesso direto a APIs Windows sem deps |
| **Database** | SQLite3 | Built-in | Zero config, ACID, 100% reliable |
| **HTTP Client** | requests | 2.31+ | Simplicity para API calls |
| **Config** | JSON | Built-in | Legível, editável manualmente |
| **Logging** | logging | Built-in | Rotation, levels, thread-safe |
| **APIs** | Groq (Whisper) + Google Gemini | N/A | Melhor custo/benefício (Groq) + Qualidade (Gemini) |

**Dependências Externas:**

```
PySide6>=6.6.0
pyaudio>=0.2.14
requests>=2.31.0
```

---

## 4. Histórico de Desenvolvimento

### Fase 1: MVP (Concluída)

**Objetivo:** Proof of Concept funcional  
**Duração:** 3-5 dias  
**Entregas:**

- ✅ Detecção de CapsLock via polling (`GetAsyncKeyState`)
- ✅ Captura de áudio via PyAudio
- ✅ Transcrição via Groq API
- ✅ Polimento básico via Gemini

### Fase 2: Produtividade (Concluída)

**Objetivo:** Features de usabilidade  
**Duração:** 2-3 dias  
**Entregas:**

- ✅ Histórico SQLite persistente
- ✅ Colagem Inteligente (detecção de foco)
- ✅ Janela de histórico com busca
- ✅ System Tray Icon

### Fase 3: Polimento UX (Concluída)

**Objetivo:** Interface profissional  
**Duração:** 2 dias  
**Entregas:**

- ✅ Widget de Status (OSD) flutuante
- ✅ Notificações não-intrusivas
- ✅ Documentação técnica Tier 1

### Fase 4: Confiabilidade (Concluída)

**Objetivo:** Production-ready  
**Duração:** 5-7 dias  
**Entregas:**

- ✅ Write-Ahead Logging (persistência antes de clipboard)
- ✅ Keyboard Hook (CapsLock transparente)
- ✅ Anti-Alucinação (filtros de silêncio)
- ✅ Fail-safe (arquivo emergencial no Desktop se SQLite falhar)
- ✅ Inicialização Automática (Registry)
- ✅ Auto-Enter (pressiona Enter após colar)
- ✅ Identidade Visual (ícone customizado + atalho Desktop)
- ✅ Histórico gerenciável (excluir individual/tudo, retenção 5 dias)
- ✅ Documentação de Bugs (`Historico_Problemas_Solucoes.md`)

### Fase 5: Personalização (Em Andamento - 20% Concluída)

**Objetivo:** Interface de configurações  
**Status Atual:**

- ✅ Auto-Enter implementado
- ✅ Ícone customizado e atalho Desktop
- ⏳ Gestão de APIs (não iniciado)
- ⏳ Toggle de Polimento (não iniciado)
- ⏳ Tradução Integrada (briefing criado, não implementado)

---

## 5. Roadmap Futuro

### 5.1 Fase 5 (Restante) — Configurações & Personalização

**ETA:** 2-3 semanas  
**Prioridade:** Alta

#### Épico 1: Central de Preferências

**Tasks:**

- [ ] Criar janela de configurações (QDialog tabbed)
  - [ ] Aba "Geral": Threshold de hold, idioma de saída
  - [ ] Aba "Modelos": Escolha de API (Groq/OpenAI/Local) + modelo
  - [ ] Aba "Avançado": Logs, limpeza de histórico, reset config
- [ ] Adicionar item "Configurações" no menu (habilitado)
- [ ] Validação de campos (API keys vazias, threshold inválido)

#### Épico 2: Tradução Integrada

**Tasks:**

- [ ] Modificar `cliente_api.py`:
  - [ ] Método `polir(texto, idioma_alvo: Optional[str])`
  - [ ] Prompts bilíngues (PT→EN, PT→ES)
- [ ] Submenu "Idioma de Saída" na bandeja (Radio buttons)
- [ ] Testes de qualidade (coloquial vs técnico)

#### Épico 3: Toggle de Polimento

**Tasks:**

- [ ] Checkbox "Ativar Polimento" no menu
- [ ] Se desabilitado: pular Gemini, usar texto bruto do Groq
- [ ] Economia de tokens (~50% quando desabilitado)

### 5.2 Fase 6 (Futuro) — Supressão de Áudio

**ETA:** 1-2 semanas  
**Prioridade:** Média

**Objetivo:** Auto-mute de outras aplicações durante gravação

**Implementação:**

- Usar `pycaw` (Python Core Audio Windows)
- `snapshot_audio_state()` no `RECORDING`
- `mute_all_except(voiceflow_pid)`
- `restore_audio_state()` no `COMPLETE`/`ERROR`
- Handler `atexit` para garantir unmute em crash

### 5.3 Fase 7 (Futuro) — Gestão Avançada de Modelos

**ETA:** 2-3 semanas  
**Prioridade:** Baixa

**Features:**

- Suporte a múltiplos providers (OpenAI Whisper, Azure Speech, Local Whisper.cpp)
- Fallback automático (se Groq falhar, tentar OpenAI)
- Monitoramento de custos (tracking de tokens consumidos)
- Cache local de transcrições (evitar reprocessamento)

---

## 6. Fluxo de Dados End-to-End

### 6.1 Happy Path (Transcrição Bem-Sucedida)

```
[1] Usuário segura CapsLock (>500ms)
        ↓ [KeyboardHook detecta]
[2] FSM: IDLE → RECORDING
        ↓ [CapturadorAudio.iniciar()]
[3] Widget muda para VERMELHO (gravando...)
        ↓ [Usuário fala]
[4] Áudio capturado em buffer (PyAudio)
        ↓ [Usuário solta CapsLock]
[5] KeyboardHook detecta UP
        ↓ [FSM.parar_gravacao()]
[6] FSM: RECORDING → TRANSCRIBING
        ↓ [Salva WAV temporário]
[7] Widget muda para AMARELO (processando...)
        ↓ [Thread Secundária inicia]
[8] Upload WAV para Groq API
        ↓ [POST /v1/audio/transcriptions]
[9] Groq retorna: "olá meu nome é paulo"
        ↓ [FSM: TRANSCRIBING → POLISHING]
[10] Envia para Gemini API
        ↓ [POST /v1beta/chat/completions]
        ↓ [PROMPT_POLIMENTO aplicado]
[11] Gemini retorna: "Olá, meu nome é Paulo."
        ↓ [FSM: POLISHING → COMPLETE]
[12] **SALVAR NO HISTÓRICO (BLOQUEANTE)**
        ↓ [SQLite INSERT → ID retornado]
[13] Widget muda para VERDE (sucesso!)
        ↓ [Copia para clipboard]
[14] Verifica foco da janela
        ↓ [GetForegroundWindow() == janela_inicial?]
[15] SIM → Simula Ctrl+V
        ↓ [SendInput(VK_CONTROL + VK_V)]
[16] Se Auto-Enter ativado:
        ↓ [Sleep(800ms)]
        ↓ [SendInput(VK_RETURN)]
[17] Notifica: "Transcrição colada com sucesso!"
        ↓ [Widget auto-hide em 3s]
[18] Deleta WAV temporário
        ↓ [FSM: COMPLETE → IDLE]
```

### 6.2 Error Paths (Tratamento de Falhas)

**Cenário 1: Groq API Falha**

```
[Transcrição] → Timeout 30s
        ↓ [Retry 3x com backoff]
        ↓ [Todas falham]
→ FSM: ERROR
→ Widget: VERMELHO + "Erro na transcrição"
→ Notificação: "Verifique conexão de rede"
→ WAV preservado (não deletado)
```

**Cenário 2: SQLite Falha (Disco Cheio)**

```
[Polimento OK] → historico.salvar()
        ↓ [sqlite3.OperationalError: disk full]
        ↓ [Catch Exception]
→ Criar arquivo emergencial:
  `Desktop/VoiceFlow_EMERGENCIA_20260109_143000.txt`
→ Notificação: "Erro no banco! Texto salvo em: [caminho]"
→ Continua fluxo (clipboard + cola)
```

**Cenário 3: Mudança de Foco Durante Processamento**

```
[Processando...] → Usuário muda para Chrome
        ↓ [GetForegroundWindow() != janela_inicial]
→ Pula simulação de Ctrl+V
→ Notificação: "Transcrição pronta no clipboard (foco alterado)"
→ Usuário cola manualmente com Ctrl+V
```

---

## 7. Configuração (config.json)

### Estrutura Atual

```json
{
  "transcription": {
    "provider": "groq",
    "api_key": "gsk_...",
    "model": "distil-whisper-large-v3-en"
  },
  "polishing": {
    "provider": "gemini",
    "api_key": "AIza...",
    "model": "gemini-1.5-flash"
  },
  "hotkey": {
    "detector": "hook",  // "hook" ou "polling"
    "threshold_ms": 500
  },
  "auto_enter": false,  // Novo (Fase 5)
  "idioma_saida": "pt-br"  // Planejado (Fase 5 - Tradução)
}
```

### Validação de Configuração

**Regras:**

- `api_key` não pode ser vazia
- `model` deve estar em lista permitida
- `threshold_ms` deve estar entre 100-2000
- `detector` deve ser "hook" ou "polling"

**Fallbacks:**

- Se `config.json` não existir: criar com template
- Se campo inválido: usar valor padrão + logar warning

---

## 8. Logging e Debugging

### Estrutura de Logs

**Arquivo:** `debug_log.txt` (rotação automática a cada 10MB)  
**Formato:**

```
[2026-01-09 14:30:15] [INFO] [maquina_estados] Transição: IDLE → RECORDING
[2026-01-09 14:30:18] [INFO] [maquina_estados] Transição: RECORDING → TRANSCRIBING
[2026-01-09 14:30:20] [INFO] [cliente_api] Transcrição concluída: 127 caracteres
[2026-01-09 14:30:22] [INFO] [historico] Transcrição salva no histórico: ID 42
[2026-01-09 14:30:22] [INFO] [detector_foco] Foco preservado - Colando automaticamente
```

### Níveis de Log

| Nível | Uso | Exemplo |
|-------|-----|---------|
| **DEBUG** | Detalhes técnicos | `"SendInput retornou: 4 eventos enviados"` |
| **INFO** | Marcos de sucesso | `"Transcrição salva no histórico: ID 42"` |
| **WARNING** | Degradação de performance | `"Clipboard demorou 150ms (esperado <100ms)"` |
| **ERROR** | Falhas recuperáveis | `"Groq API timeout, tentando novamente (2/3)"` |
| **CRITICAL** | Falhas irrecuperáveis | `"Impossível salvar transcrição (SQLite e arquivo falharam)"` |

---

## 9. Testes e Validação

### 9.1 Testes Funcionais

| ID | Cenário | Input | Output Esperado | Status |
|----|---------|-------|-----------------|--------|
| T-001 | Gravação básica | Segurar CapsLock 2s, falar "teste" | Widget vermelho → verde, texto "teste" colado | ✅ Pass |
| T-002 | Tap CapsLock | Pressionar e soltar rápido (<500ms) | LED alterna, sem gravação | ✅ Pass |
| T-003 | Hold CapsLock | Segurar 3s | LED não muda, gravação ocorre | ✅ Pass |
| T-004 | Falha de rede | Desconectar internet, gravar | Erro exibido, WAV preservado | ✅ Pass |
| T-005 | Mudança de foco | Gravar, mudar janela, soltar | Texto no clipboard, não colado | ✅ Pass |
| T-006 | Histórico | Gravar 5 transcrições, abrir histórico | 5 itens listados | ✅ Pass |
| T-007 | Busca | Buscar "teste" no histórico | Filtra apenas registros com "teste" | ✅ Pass |
| T-008 | Auto-Enter | Ativar toggle, gravar em chat | Texto colado + Enter pressionado | ✅ Pass |

### 9.2 Testes de Performance

| Métrica | Alvo | Resultado Atual |
|---------|------|-----------------|
| Latência End-to-End | < 5s | 3.2s (média) |
| Consumo RAM (idle) | < 80MB | 52MB |
| Consumo RAM (processando) | < 150MB | 98MB |
| CPU (idle) | < 5% | 2.1% |
| Taxa de Sucesso (API) | > 95% | 98.3% |

### 9.3 Testes de Stress

**Teste de Resistência:**

- **Cenário:** 50 transcrições consecutivas em 5 minutos
- **Resultado:** ✅ Sem memory leaks, todas salvas no histórico
- **Observação:** Gemini rate limit após 40 chamadas (1 RPM limit), resolvido com retry

---

## 10. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação | Status |
|-------|--------------|---------|-----------|--------|
| **Keyboard Hook trava Windows** | Baixa | Crítico | Timeout de 1ms no callback + watchdog | ✅ Implementado |
| **APIs fora do ar** | Média | Alto | Retry com backoff + fallback para texto bruto | ✅ Implementado |
| **SQLite corrompido** | Baixa | Médio | Failsafe para arquivo emergencial no Desktop | ✅ Implementado |
| **Rate Limiting (Gemini)** | Alta | Médio | Retry exponencial + mensagem de erro clara | ✅ Implementado |
| **Alucinações de IA em silêncio** | Média | Médio | Filtro de frases conhecidas + tag `[SILENCIO]` | ✅ Implementado |
| **Custo de APIs** | Baixa | Baixo | Monitoramento manual (futuro: dashboard) | ⏳ Planejado |

---

## 11. Estratégia de Deploy

### 11.1 Modo Atual (Source)

**Usuário final executa:**

```bash
.\venv\Scripts\pythonw.exe voiceflow.py
```

**Ou usa o launcher:**

```bash
iniciar_voiceflow.bat
```

**Vantagens:**

- Fácil debugging
- Modificações instantâneas

**Desvantagens:**

- Requer Python + venv
- Usuário vê estrutura de código

### 11.2 Modo Futuro (Standalone EXE - Opcional)

**Ferramenta:** PyInstaller  
**Comando:**

```bash
pyinstaller --onefile --windowed --icon=resources/icon.ico voiceflow.py
```

**Output:** `dist/VoiceFlow.exe` (~50MB)

**Vantagens:**

- Distribuição simples (1 arquivo)
- Não requer Python instalado

**Desvantagens:**

- AV pode bloquear (falso positivo)
- Tamanho maior

**Decisão Atual:** Usuário preferiu modo Source. EXE fica como opção.

---

## 12. Métricas de Sucesso

### KPIs do Produto

| Métrica | Baseline | Alvo v1.0 | Atual |
|---------|----------|-----------|-------|
| **Tempo de Transcrição** | N/A | < 5s | 3.2s |
| **%Economia de Prompt** | 3-5 min/texto | | ~80% |
| **Taxa de Adoção** | 0 | 1 usuário piloto | 1 |
| **Uptime** | N/A | > 99% | ~99.8% |

### Feedback Qualitativo

**Casos Reais de Uso:**

1. ✅ Documentação de reuniões (30 transcrições/semana)
2. ✅ E-mails rápidos (15-20 transcrições/semana)
3. ✅ Notas de estudo (10-15 transcrições/semana)

---

## 13. Conclusão

O VoiceFlow Transcriber encontra-se em **estado de produção estável (v1.0)**, tendo completado 4 fases de desenvolvimento. O sistema é confiável, performático e resolve o problema central de forma elegante.

### Estado Atual

- ✅ **Funcional:** Todas features core implementadas
- ✅ **Confiável:** Write-Ahead Logging + Fail-safes
- ✅ **Usável:** Interface minimalista e intuitiva
- ✅ **Documentado:** README + Docstrings + Este PDR

### Próximos Passos Imediatos

1. **Completar Fase 5 (Tradução):** Briefing pronto, dev estimado em 4-6h
2. **Criar Central de Configurações:** Interface gráfica para ajustes
3. **Monitoramento de Custos:** Dashboard de consumo de API

---

**Documento Versionado:** v1.0 (09/01/2026)  
**Próxima Revisão:** Após conclusão da Fase 5
