# 🗺️ Roadmap - SpeakEasy

Este documento descreve o plano estratégico de evolução do projeto, incluindo novas funcionalidades, melhorias técnicas e dívidas técnicas conhecidas.

## 🔴 Crítico / Bloqueante

*Items que impedem o uso pleno ou oferecem risco.*

- [ ] **Resolving Build Infra (winCodeSign):** O processo de build automático no Windows (`electron-builder`) falha frequentemente ao baixar ferramentas de assinatura (`winCodeSign`) em redes restritas.
  - *Ação:* Investigar configuração de mirror ou incluir tools no repositório (vendoring) se a licença permitir.
- [ ] **Code Signing Certificate:** O executável gerado não é assinado digitalmente, o que dispara o alerta "SmartScreen" do Windows Defender.
  - *Ação:* Adquirir certificado EV ou Standard Code Signing para distribuição profissional.
- [ ] **Onda 3.1 - Unificação de Persistência:** Eliminar duplicidade entre `history.json` (Electron) e `transcripts.db` (Python Core)
  - *Ação:* Electron deve consumir dados via `GET /history` do Python Core - single source of truth

## 🟡 Importante / Alto Impacto

*Features que agregam valor significativo.*

- [ ] **Onda 4.1 - Fallback Híbrido:** Groq Cloud com fallback para Whisper local quando circuit breaker ativa
  - *Complexidade:* Alta (requer lazy loading do modelo Whisper + circuit breaker inteligente)
  - *Benefício:* Garantir 100% uptime mesmo em falhas de rede prolongadas

- [ ] **Modo Offline (Ollama/LocalLLM):** Permitir o uso de modelos locais (Llama 3, Mistral) rodando na máquina do usuário para privacidade total sem depender de APIs externas.
  - *Complexidade:* Alta (requer integrar servidor de inferência local ou conectar a Olama.ai).
- [ ] **Suporte Cross-Platform:** O código Rust (`whispo-rs`) já usa crates compatíveis (`rdev`), mas o build script e os atalhos precisam de testes no Linux e macOS.
  - *Status:* Parcialmente implementado, mas não validado.

## 🟢 Desejável / Futuro

*Melhorias de qualidade de vida e otimizações.*

- [x] **Editor de Prompt Visual:** Interface gráfica para editar o System Prompt - ✅ **Completado v2.0.0**
  - Dialog modal com textarea, templates predefinidos, placeholder visual
- [ ] **RAG Semântico:** Busca por similaridade no histórico de transcrições
  - Usuário encontra "o que disse sobre X" sem lembrar palavras exatas
  - Requer embeddings (~50MB modelo) e índice vetorial
- [ ] **Histórico de Transcrições com Pesquisa:** Banco de dados local (SQLite) para salvar e buscar ditados antigos.
- [ ] **Personalização de Atalhos:** Permitir que o usuário escolha outra tecla além do `CapsLock` (ex: Botão lateral do mouse).
- [ ] **Export PDF com Speaker Badges:** Diarização + formatação visual para uso jurídico/comercial

## 📝 Dívida Técnica

- **Testes Automatizados:** O projeto carece de testes unitários para o frontend (React) e integração para o Rust.
- **Tipagem Estrita:** Alguns pontos do código usam `any` implícito ou asserções de tipo que poderiam ser mais seguras.
- **Onda 3.2 - Suite Testes:** Fixtures WAV, mocks Groq, CI/CD GitHub Actions para regressão

---

*Última atualização: Versão 2.0.0 - 31/12/2025*
