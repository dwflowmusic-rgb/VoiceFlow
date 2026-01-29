# VoiceFlow Next-Generation: Visão de Futuro

Este documento é um exercício especulativo de design, capturando como o VoiceFlow poderia evoluir ou ser reescrito se utilizássemos todos os aprendizados das Fases 1-3 sem as restrições do código legado atual.

## 1. Lições da Arquitetura Atual (v0.x)

- **O que deu muito certo:**
  - O modelo de *polling* para o CapsLock é indestrutível. É a única forma confiável de ignorar o comportamento de toggle do SO.
  - O banco de dados SQLite local é a melhor defesa contra bugs de UI/Clipboard.
  - O Gemini como "Polidor" dissertativo é superior a heurísticas de texto tradicionais.
- **O que poderia ser melhor:**
  - O modelo de threading misto (threading.Thread + Qt Signals) pode causar race conditions sutis em logs.
  - Dependência total de internet para transcrição (Groq/Gemini).

## 2. Tecnologias Emergentes e Mudanças de Rumo

### 2.1 Rust como Core Engine

Para a próxima geração (`VoiceFlow v2.0`), o motor de detecção de input (`user32.dll` e `GetAsyncKeyState`) e a captura de áudio poderiam ser escritos em **Rust** e expostos ao Python via **PyO3**.

- **Benefício:** Footprint de memória ainda menor (<10MB) e estabilidade de hardware garantida contra falhas do interpretador Python.

### 2.2 Transcrição "Local-First"

Com o avanço do **Whisper.cpp**, é possível mover a transcrição para o processador local.

- **Vantagem:** Latência zero de rede, custo operacional zero e privacidade total dos dados sensíveis do usuário.

### 2.3 Modelo Híbrido de LLM

- **Local (Offline):** Modelos como Phi-3 ou Gemma 2B rodando localmente para correções gramaticais básicas offline.
- **Cloud (Online):** Gemini 1.5 Pro/Flash apenas para polimentos de alta complexidade ou quando o computador estiver conectado à energia.

## 3. Arquitetura "Ideal" Hipotética

### Tier 1: O Motor (Native Layer)

Escrito em Rust, atuando como um serviço de sistema leve. Responsável por:

- Detecção de CapsLock (Polling 20ms).
- Injeção de Texto (Clipboard e SendInput).
- Captura de Áudio (CoreAudio/WASAPI).

### Tier 2: A Orquestra (Logic Layer)

Python mantido para a lógica de negócio devido à facilidade de integração com LLMs.

- FSM (Máquina de Estados).
- Context-Awareness (decisões de foco).
- Prompt Engineering.

### Tier 3: A Memória (Event Sourcing)

Em vez de salvar apenas o texto polido, o histórico v2.0 usaria **Event Sourcing**:

- Salvaria o áudio bruto (opcional), a transcrição crua e as versões de polimento.
- Isso permitiria ao usuário "re-polir" uma fala antiga com um novo prompt ou persona semanas depois.

## 4. Conclusão

O VoiceFlow v1.0 é um sucesso de engenharia pragmática. A visão v2.0 foca em **Privacidade Absoluta e Performance Nativa**, removendo a última fronteira: a dependência de APIs de terceiros e da conexão com a nuvem.

---
*Brainstorming realizado em 03/01/2026 pela equipe Antigravity.*
