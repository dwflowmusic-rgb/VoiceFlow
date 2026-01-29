# VoiceFlow Roadmap

Este documento descreve a visão de longo prazo e as funcionalidades planejadas para o VoiceFlow Transcriber.

## Visão Geral

O VoiceFlow visa ser a ferramenta de entrada de texto mais rápida do mundo no PC, removendo todas as fricções entre o pensamento e a palavra escrita, com foco total em usuários de alta performance e neurodiversos.

---

## 📈 Fases de Desenvolvimento

### 🟢 Fase Corrente (Q1 2026): Estabilização e UX Primária

- [x] **v0.3.0:** Colagem Inteligente e Histórico SQLite.
- [ ] **v0.4.0:** Interface de Configurações Completa (GUI).
- [ ] **v0.4.1:** Ajuste de sensibilidade do "Hold Threshold" via UI.
- [ ] **v0.4.2:** Restauração segura do estado do CapsLock (LED).
- [ ] **v0.4.5:** Empacotamento oficial como Executável (.exe).

### 🟡 Curto Prazo (Q2 2026): Personalização e Feedback

- [ ] **Personas de Polimento:** Opções para mudar o tom do texto (Formal, Casual, E-mail, TDAH-Friendly, Code-Comment).
- [ ] **Overlay Discreto:** Feedback visual flutuante (não intrusivo) durante a gravação para indicar níveis de áudio.
- [ ] **Atalhos Customizáveis:** Permitir trocar CapsLock por outras teclas (Scroll Lock, F-Keys).
- [ ] **Estatísticas de Produtividade:** Contador de palavras transcritas e estimativa de tempo economizado.

### 🔴 Médio Prazo (H2 2026): Integrações e Power Features

- [ ] **Integração com Notion/Obsidian:** Envio direto de blocos de texto para páginas específicas via API.
- [ ] **Comandos de Voz de Gestão:** "VoiceFlow, deletar última transcrição" ou "VoiceFlow, modo advogado".
- [ ] **Transcrição Multilíngue:** Detecção automática de idioma e suporte a tradução simultânea.
- [ ] **Exportação em Lote:** Exportar histórico para Markdown, JSON ou TXT.

### 🚀 Longo Prazo (2027+): O Futuro "Local-First"

- [ ] **Whisper Local (Whisper.cpp):** Transcrição offline completa para privacidade absoluta e custo zero.
- [ ] **LLM Local (Phi/Gemma):** Polimento básico offline.
- [ ] **Sincronização Cloud (Opcional):** Sincronizar histórico entre computadores de trabalho e pessoal.

---

## ❌ Fora de Escopo (Anti-Goals)

Para manter o foco na simplicidade e invisibilidade, as seguintes features **não** estão no roadmap:

- **Mobile App:** O VoiceFlow é uma ferramenta nativa de desktop projetada para workflows de digitação pesada.
- **Gravação Passiva:** Jamais gravaremos áudio de forma contínua por motivos de ética e privacidade.
- **Edição de Texto Completa:** O VoiceFlow entrega o texto no seu editor favorito, ele não tenta ser um editor.

---
*Roadmap sujeito a alterações baseadas no feedback dos usuários.*
