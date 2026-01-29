# VoiceFlow - Especificação Arquitetural (Tier 1)

Este documento descreve as decisões técnicas, a organização de módulos e os princípios de design que compõem o VoiceFlow Transcriber.

## 1. Filosofia de Design e Princípios

O VoiceFlow foi construído sobre três pilares fundamentais:

- **Invisibilidade:** A aplicação deve operar como uma extensão natural do sistema operacional, sem janelas persistentes ou interfaces densas.
- **Robustez de Dados:** Nenhum dado deve ser perdido. A persistência (banco de dados) precede a entrega (clipboard).
- **Latência Determinística:** O uso de modelos ultra-rápidos (Groq) garante que o feedback seja quase instantâneo, essencial para manter o fluxo de pensamento do usuário.

## 2. Decisões Tecnológicas do Core

### 2.1 Stack Técnica

- **Linguagem:** Python 3.10+ (agilidade e ecossistema de dados/IA).
- **UI Framework:** PySide6 (Qt para Python) para gestão de eventos cross-thread e system tray robusto.
- **Persistência:** SQLite (embutido, robusto, single-file).
- **Interação Desktop:** Win32 API via `ctypes` para detecção de foco e hooks de teclado precisos.

### 2.2 Por que não Electron?

Embora o Electron facilite o design visual, ele imporia um consumo de memória 10x superior (200MB+ vs 25MB do VoiceFlow) e dificultaria o acesso direto a APIs de baixo nível do Windows, como o rastreio de handles de janelas (`HWND`) e hooks globais de hardware.

## 3. Arquitetura de Componentes

### 3.1 Camada de Detecção de Input (`core.detector_tecla`)

- **Implementação:** Utiliza *polling* ativo via `user32.GetAsyncKeyState` em um loop de 20ms.
- **Racional:** Diferente de bibliotecas baseadas em eventos que falham com a tecla CapsLock (por ser uma chave de toggle), o polling direto no hardware garante detecção 100% confiável do estado "pressionado" físico.
- **Parâmetros:** Threshold de 500ms para diferenciar toques acidentais e timeout de segurança de 5 minutos.

### 3.2 Camada de Captura e Audio (`core.captura_audio`)

- **Pipeline:** Sounddevice captura buffers PCM 16kHz Mono.
- **Segurança:** O áudio é bufferizado em memória e salvo temporariamente em arquivo WAV apenas para envio à API, sendo limpo imediatamente após o sucesso.

### 3.3 Camada de Processamento de IA (`core.cliente_api`)

- **Pipeline Híbrido:**
    1. **Transcrição:** Groq (Whisper large-v3-turbo) para velocidade máxima.
    2. **Polimento:** Google Gemini Flash para refinamento dissertativo.
- **Resiliência:** Implementa *exponential backoff retry* para lidar com instabilidades de rede.

### 3.4 Inteligência de Entrega (`core.gerenciador_clipboard` e `core.detector_foco`)

- **Lógica de Foco:** Ao iniciar a gravação, o sistema captura o `HWND` da janela ativa. Ao finalizar, compara-se o foco atual.
- **Simulação de Teclado:** Se o foco for preservado, o sistema utiliza `SendInput` para disparar um `Ctrl+V` nativo, injetando o texto diretamente no contexto do usuário.

### 3.5 Camada de Persistência (`core.historico`)

- **Schema:** Tabela única `transcricoes` com IDs, timestamps e versões (bruta vs polida).
- **Transacional:** Inserção ACID garantida logo após o polimento, servindo como fonte da verdade caso a colagem automática falhe.

## 4. Máquina de Estados (Coordenação)

O sistema segue uma máquina de estados finitos (FSM) rigorosa:

1. **IDLE:** Aguardando pressionamento do CapsLock.
2. **RECORDING:** Capturando áudio e bloqueando novas ações.
3. **TRANSCRIBING:** Enviando áudio para o Groq.
4. **POLISHING:** Enviando texto para o Gemini.
5. **SAVING:** Persistindo no SQLite.
6. **DELIVERING:** Colando texto ou apenas notificando.
7. **FINISHING:** Limpeza de buffers e retorno ao IDLE.

## 5. Performance e Concorrência

- **Threading:** Todas as chamadas de rede e processamento de áudio ocorrem em threads separadas (via Python `threading` ou `QThread`).
- **Sinais:** A comunicação entre threads de processamento e a UI de bandeja é feita via **Qt Signals**, garantindo que operações de UI (como notificações) ocorram apenas na thread principal (Safe UI Thread).
- **Footprint:** Consumo típico de ~30MB de RAM e <1% de CPU em standby.

---
*Documento mantido pela equipe de arquitetura VoiceFlow.*
