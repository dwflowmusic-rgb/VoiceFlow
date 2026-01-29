# BLUEPRINT TÉCNICO: TRANSCRITOR COM POLIMENTO IA

**Projeto:** VoiceFlow Transcriber  
**Objetivo:** Aplicativo desktop Windows para transcrição instantânea via hotkey com polimento automático por IA  
**Versão do Blueprint:** 1.0  
**Data:** 02 de Janeiro de 2026

---

## 📋 VISÃO GERAL

### Propósito do Aplicativo

VoiceFlow é um transcritor de áudio desktop ultra-leve que remove completamente a fricção entre pensamento falado e texto escrito polido. O usuário pressiona e segura uma tecla de atalho global, fala naturalmente, solta a tecla, e segundos depois o texto transcrito e polido está no clipboard pronto para colar em qualquer aplicação. O diferencial crítico não é apenas transcrever, mas POLIR automaticamente removendo repetições, gagueiras, vícios de linguagem e adicionando pontuação e estrutura de parágrafos que refletem a intenção comunicativa do falante.

### Problema Resolvido

O Windows built-in speech-to-text e ferramentas similares produzem transcrições literais que exigem edição manual extensiva: falta pontuação adequada, parágrafos são inexistentes, repetições e tropeços na fala ficam registrados, e vícios de linguagem comuns em pessoas com TDAH (como "tipo", "né", "então") poluem o texto. Isso transforma ferramenta de produtividade em fonte de frustração, porque o usuário precisa gastar tempo corrigindo ao invés de usar o texto diretamente.

VoiceFlow resolve isso aplicando inteligência artificial no pós-processamento da transcrição bruta, transformando fala natural e imperfeita em texto escrito fluente que pode ser usado imediatamente sem necessidade de edição manual. O resultado deve parecer que foi escrito diretamente, não falado e transcrito.

### Público-Alvo e Contexto de Uso

Usuário primário é profissional com TDAH que precisa documentar pensamentos, rascunhar comunicações, criar conteúdo escrito ou tomar notas rápidas ao longo do dia de trabalho. O contexto de uso varia de redigir emails e mensagens, escrever trechos de documentos legais, capturar ideias para projetos em desenvolvimento, até documentar progressos e decisões sem interromper fluxo de trabalho para sessão formal de escrita.

O aplicativo deve ser completamente invisível quando não está sendo usado, e instantâneo quando acionado. Não pode existir fricção de abrir janela, clicar botões, ou navegar menus. A interação completa é: pressionar tecla → falar → soltar tecla → resultado no clipboard. Qualquer passo adicional representa falha de design.

---

## 🎯 REQUISITOS FUNCIONAIS ESSENCIAIS

### RF-01: Captura de Áudio via Hotkey Global
O aplicativo deve registrar hotkey configurável que funciona globalmente em qualquer aplicação do Windows, mesmo quando VoiceFlow não está em foco. Quando usuário pressiona e segura a tecla, sistema inicia gravação de áudio do microfone padrão do sistema. Quando usuário solta a tecla, gravação é finalizada e arquivo de áudio é processado imediatamente.

**Decisão Arquitetural:** Hotkey padrão sugerido é `Ctrl+Shift+Espaço` (mnemônico: Espaço = falar), mas deve ser configurável nas settings. Tecnicamente isso requer hook global do sistema operacional Windows para interceptar eventos de teclado independente de qual janela tem foco.

### RF-02: Transcrição via Groq Whisper API
Áudio capturado deve ser enviado para Groq Whisper Large v3 Turbo API que retorna transcrição em texto. O aplicativo tem acesso aos 8 horas diárias gratuitas de transcrição que Groq oferece, portanto não há preocupação com custos ou limites para uso pessoal intenso.

**Considerações Técnicas:** Groq Whisper aceita áudio em múltiplos formatos mas preferência é por Opus ou MP3 por melhor compressão sem perda significativa de qualidade para voz. Áudio deve ser enviado via POST multipart/form-data para endpoint da API. Resposta retorna JSON com campo "text" contendo transcrição bruta.

### RF-03: Polimento via Gemini Flash
Transcrição bruta do Whisper deve ser enviada para Gemini Flash 2.0 via Vertex AI com prompt especializado que instrui o modelo a polir o texto mantendo completamente a intenção e voz original do falante enquanto corrige problemas estruturais da fala transcrita.

**Prompt de Polimento (Especificação Detalhada):**

O prompt deve instruir o Gemini Flash com as seguintes diretrizes textuais precisas:

```
Você receberá transcrição literal de áudio falado em português do Brasil. Sua tarefa é polir este texto transformando fala em escrita fluente, aplicando as seguintes transformações:

PONTUAÇÃO E ESTRUTURA:
- Adicione pontuação adequada (vírgulas, pontos, interrogações, exclamações) onde a entonação e pausas naturais da fala indicarem
- Quebre texto em parágrafos quando houver mudança clara de assunto ou tópico
- Use dois-pontos e travessão quando apropriado para listas ou enumerações que aparecem na fala

LIMPEZA DE VÍCIOS DE LINGUAGEM:
- Remova completamente vícios de fala como "tipo", "né", "então" quando usados como preenchimento sem função semântica
- Elimine repetições de palavras ou frases que claramente foram tropeços na fala, não ênfase intencional
- Corrija falsos começos onde a pessoa inicia frase de um jeito e recomeça de outro

CORREÇÃO DE GAGUEIRAS E FRAGMENTOS:
- Reorganize frases que começaram fragmentadas e foram completadas depois
- Una pedaços de pensamento que foram separados por pausas mas formam ideia coesa
- Corrija concordância verbal e nominal quando houver erros claros de fala rápida

PRESERVAÇÃO ABSOLUTA:
- JAMAIS altere vocabulário, terminologia técnica ou nomes próprios mencionados
- JAMAIS formalize ou "academize" a linguagem - mantenha registro coloquial se foi coloquial, técnico se foi técnico
- JAMAIS adicione informações, explicações ou comentários que não estavam no áudio original
- JAMAIS mude primeira pessoa para terceira ou vice-versa
- Se houver gírias ou expressões regionais, mantenha integralmente

OBJETIVO FINAL: O texto polido deve ler como se tivesse sido escrito diretamente, não falado e transcrito. Mas a voz e personalidade do falante devem permanecer 100% intactas. Apenas remova imperfeições mecânicas da fala, não reescreva conteúdo.

Retorne APENAS o texto polido, sem comentários, avisos ou metadados.
```

**Justificativa:** Este prompt é extremamente específico porque LLMs tendem a "ajudar demais" e reescrever conteúdo ao invés de apenas polir. As instruções de preservação absoluta são críticas para garantir que o Operador não perca sua voz própria no processo.

### RF-04: Resultado no Clipboard
Texto polido retornado pelo Gemini Flash deve ser copiado automaticamente para clipboard do sistema Windows, permitindo que usuário cole imediatamente em qualquer aplicação com Ctrl+V. Não deve haver necessidade de interação adicional ou cliques.

**Feedback Visual Opcional:** Notificação toast discreta do Windows indicando "Transcrição pronta!" quando processo completa, mas isso é secundário - o importante é texto estar no clipboard.

### RF-05: Histórico de Transcrições
Todas transcrições polidas finais devem ser salvas em banco de dados local SQLite com timestamp, permitindo consulta posterior se usuário precisar recuperar texto transcrito anteriormente. Áudio original é descartado imediatamente após transcrição bem-sucedida para economizar espaço e preservar privacidade.

**Schema do Banco de Dados:**
```
Tabela: transcriptions
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- timestamp (DATETIME NOT NULL)
- transcribed_text (TEXT NOT NULL) - texto bruto do Whisper
- polished_text (TEXT NOT NULL) - texto final polido pelo Gemini
- duration_seconds (REAL) - duração do áudio original
- created_at (DATETIME DEFAULT CURRENT_TIMESTAMP)
```

**Interface de Histórico:** Janela secundária acessível via ícone na bandeja ou atalho que mostra lista de transcrições anteriores com busca por texto e filtro por data. Usuário pode clicar em transcrição antiga para copiar novamente para clipboard.

---

## 🏗️ ARQUITETURA TÉCNICA

### Stack Tecnológico Definido

**Framework Desktop:** Electron 28+  
**Justificativa:** Embora Tauri seja teoricamente mais performático, Electron oferece ecossistema maduro, bibliotecas abundantes para captura de áudio e hooks globais do Windows, e desenvolvimento substancialmente mais rápido. Para aplicativo de áudio que não precisa rodar constantemente em background consumindo recursos, overhead do Electron é negligenciável. Prioridade aqui é ter solução funcionando rapidamente.

**Frontend:** React 18+ com TypeScript  
**Justificativa:** React oferece componentização clara para interface de settings e histórico. TypeScript adiciona safety importante quando lidando com estados assíncronos complexos (gravando, transcrevendo, polindo).

**Backend/Main Process:** Node.js com TypeScript  
**Bibliotecas Críticas:**
- `electron-globalshortcut` ou `iohook` para hooks globais de teclado
- `node-microphone` ou `node-record-lpcm16` para captura de áudio do microfone
- `axios` para chamadas HTTP às APIs
- `better-sqlite3` para banco de dados local

**Build e Packaging:** electron-builder para gerar instalador Windows

### Arquitetura de Processos Electron

**Main Process (Node.js):**
- Gerenciamento de janela principal (tray icon)
- Registro de hotkey global
- Captura de áudio do sistema
- Comunicação com APIs externas (Groq, Gemini)
- Gerenciamento de banco de dados SQLite
- Manipulação de clipboard do sistema

**Renderer Process (React):**
- Janela de configurações (settings)
- Interface de histórico de transcrições
- Indicadores visuais de status (gravando, processando)

**IPC (Inter-Process Communication):**
Comunicação entre Main e Renderer via canais Electron IPC:
- `start-recording` / `stop-recording` / `recording-status`
- `transcription-complete` / `transcription-error`
- `get-history` / `search-history`
- `update-settings` / `get-settings`

### Fluxo de Dados End-to-End

```
[Usuário pressiona hotkey]
    ↓
[Main Process detecta via global hook]
    ↓
[Inicia gravação de áudio via microphone stream]
    ↓
[Áudio é bufferizado em memória]
    ↓
[Usuário solta hotkey]
    ↓
[Finaliza gravação e salva áudio temporário em disco]
    ↓
[Envia áudio para Groq Whisper API]
    ↓
[Recebe transcrição bruta em texto]
    ↓
[Envia texto para Gemini Flash via Vertex AI]
    ↓
[Recebe texto polido]
    ↓
[Salva ambos (bruto + polido) no SQLite]
    ↓
[Copia texto polido para clipboard]
    ↓
[Mostra notificação toast "Pronto!"]
    ↓
[Deleta arquivo de áudio temporário]
```

### Gerenciamento de Estado e Erros

**Estados da Aplicação:**
- `IDLE`: Aguardando hotkey
- `RECORDING`: Gravando áudio
- `TRANSCRIBING`: Enviando para Groq
- `POLISHING`: Processando com Gemini
- `COMPLETE`: Texto no clipboard
- `ERROR`: Falha em alguma etapa

**Tratamento de Erros Críticos:**
- Microfone não disponível → Notificar usuário, não crashar
- API Groq offline/erro → Tentar novamente 2x, depois mostrar erro
- API Gemini offline/erro → Se falhar, colocar transcrição bruta no clipboard mesmo assim (melhor algo que nada)
- Limite diário Groq atingido → Notificar usuário claramente
- Sem conexão internet → Detectar antes de tentar enviar

---

## 🗺️ ROADMAP DE IMPLEMENTAÇÃO

### FASE 1: CORE FUNCIONAL (PRIORIDADE MÁXIMA)
**Objetivo:** Sistema básico funcionando end-to-end sem interface complexa

**Bloco 1.1: Setup Inicial e Estrutura**
- [ ] Inicializar projeto Electron com TypeScript
- [ ] Configurar estrutura de pastas (main/, renderer/, shared/)
- [ ] Setup de build com electron-builder
- [ ] Configurar ESLint e Prettier para manter código consistente

**Bloco 1.2: Captura de Áudio**
- [ ] Implementar registro de hotkey global (testar com F12 inicialmente)
- [ ] Implementar captura de áudio do microfone durante pressão da tecla
- [ ] Testar gravação e salvamento de arquivo temporário
- [ ] Implementar indicador visual de que está gravando (LED vermelho no tray icon)

**Bloco 1.3: Integração com Groq Whisper**
- [ ] Configurar credenciais Groq API no .env
- [ ] Implementar envio de áudio para Groq Whisper
- [ ] Parsear resposta JSON e extrair texto transcrito
- [ ] Implementar retry logic para falhas de rede
- [ ] Testar com áudios de diferentes durações (5seg, 30seg, 2min)

**Bloco 1.4: Integração com Gemini Flash**
- [ ] Configurar credenciais Vertex AI no .env
- [ ] Implementar prompt de polimento conforme especificação acima
- [ ] Enviar transcrição bruta para Gemini
- [ ] Receber e processar texto polido
- [ ] Testar qualidade do polimento com transcrições reais do Operador

**Bloco 1.5: Clipboard e Feedback**
- [ ] Implementar cópia automática para clipboard do Windows
- [ ] Implementar notificação toast do Windows
- [ ] Testar que texto pode ser colado em diferentes apps (Word, Notepad, Chrome)

**🎯 CHECKPOINT FASE 1:** Neste ponto o aplicativo já funciona do jeito mais básico - você pressiona tecla, fala, solta, e texto polido aparece no clipboard. Isso já é usável e resolve o problema core.

---

### FASE 2: PERSISTÊNCIA E HISTÓRICO
**Objetivo:** Salvar transcrições e permitir consulta posterior

**Bloco 2.1: Banco de Dados SQLite**
- [ ] Implementar schema SQLite conforme especificado
- [ ] Criar funções de insert/select para transcrições
- [ ] Implementar migração automática de schema se necessário
- [ ] Testar que banco persiste entre reinícios do app

**Bloco 2.2: Interface de Histórico**
- [ ] Criar janela Renderer para histórico
- [ ] Implementar lista de transcrições com timestamp
- [ ] Implementar busca por texto nas transcrições
- [ ] Implementar filtro por data (hoje, última semana, último mês)
- [ ] Botão para copiar transcrição antiga para clipboard novamente
- [ ] Botão para deletar transcrições individuais

**🎯 CHECKPOINT FASE 2:** Agora você não perde mais nenhuma transcrição e pode buscar o que falou semana passada se precisar.

---

### FASE 3: CONFIGURAÇÕES E POLIMENTO UX
**Objetivo:** Tornar aplicativo configurável e agradável de usar

**Bloco 3.1: Settings Persistentes**
- [ ] Criar janela de Settings acessível via tray menu
- [ ] Implementar configuração de hotkey customizável
- [ ] Implementar seleção de dispositivo de microfone
- [ ] Implementar toggle de notificações toast on/off
- [ ] Salvar preferências em config.json local

**Bloco 3.2: Refinamentos de UX**
- [ ] Indicador visual mais sofisticado durante gravação (waveform?)
- [ ] Mostrar tempo de gravação em tempo real
- [ ] Permitir cancelar gravação (ESC durante gravação)
- [ ] Melhorar mensagens de erro com ações sugeridas
- [ ] Implementar shortcuts na interface de histórico (Ctrl+F para buscar)

**Bloco 3.3: Performance e Estabilidade**
- [ ] Implementar limpeza automática de áudio temporário em caso de crash
- [ ] Otimizar tamanho de bundle do Electron
- [ ] Implementar logging estruturado para debug
- [ ] Testar em máquinas Windows diferentes (Win 10, Win 11)

**🎯 CHECKPOINT FASE 3:** Aplicativo está polido, configurável, e robusto. Pronto para uso diário intenso.

---

### FASE 4: FEATURES AVANÇADAS (OPCIONAL)
**Objetivo:** Capacidades adicionais se tempo permitir

**Bloco 4.1: Melhorias de Transcrição**
- [ ] Detecção automática de idioma (PT-BR vs EN)
- [ ] Suporte a múltiplos idiomas no polimento
- [ ] Timestamps dentro da transcrição para trechos longos

**Bloco 4.2: Exportação e Integração**
- [ ] Exportar histórico completo para CSV/JSON
- [ ] Integração com Google Docs (enviar direto para novo doc)
- [ ] Webhook opcional para enviar transcrições para outro sistema

---

## ⚙️ ESPECIFICAÇÕES DE CONFIGURAÇÃO

### Variáveis de Ambiente Necessárias

```
GROQ_API_KEY=<chave_da_api_groq>
GOOGLE_CLOUD_PROJECT=<id_do_projeto_gcp>
GOOGLE_APPLICATION_CREDENTIALS=<caminho_para_service_account_json>
```

### Estrutura de Diretórios Recomendada

```
voiceflow-transcriber/
├── src/
│   ├── main/                  # Main process (Node.js)
│   │   ├── index.ts           # Entry point do Electron
│   │   ├── hotkey.ts          # Gerenciamento de hotkey global
│   │   ├── audio.ts           # Captura de áudio
│   │   ├── groq.ts            # Cliente Groq Whisper
│   │   ├── gemini.ts          # Cliente Gemini Flash
│   │   ├── database.ts        # SQLite wrapper
│   │   └── clipboard.ts       # Manipulação de clipboard
│   ├── renderer/              # Renderer process (React)
│   │   ├── App.tsx            # Componente raiz
│   │   ├── components/
│   │   │   ├── History.tsx    # Interface de histórico
│   │   │   └── Settings.tsx   # Interface de settings
│   │   └── index.tsx          # Entry point React
│   └── shared/                # Código compartilhado
│       ├── types.ts           # TypeScript types
│       └── constants.ts       # Constantes globais
├── assets/
│   └── icons/                 # Ícones do tray e app
├── package.json
├── tsconfig.json
└── electron-builder.yml       # Configuração de build
```

---

## 📊 CRITÉRIOS DE SUCESSO

### Métricas Funcionais
- ✅ Latência total (pressionar tecla até texto no clipboard): < 15 segundos para áudio de 1 minuto
- ✅ Taxa de sucesso de transcrição: > 95% (excluindo problemas de rede)
- ✅ Qualidade de polimento: Texto final requer zero edição manual em 80%+ dos casos
- ✅ Confiabilidade de hotkey: Funciona 100% das vezes em qualquer app Windows

### Métricas de UX
- ✅ Tempo para completar primeira transcrição após instalar: < 2 minutos (incluindo configuração inicial)
- ✅ Número de cliques/teclas necessárias por transcrição: 2 (pressionar hotkey + colar resultado)
- ✅ Aplicativo não aparece visualmente durante uso normal (só tray icon)

---

## 🔒 CONSIDERAÇÕES DE SEGURANÇA E PRIVACIDADE

### Dados Sensíveis
- **Áudio:** Descartado imediatamente após transcrição bem-sucedida. NUNCA enviado para servidores além das APIs necessárias (Groq, Google).
- **Transcrições:** Armazenadas APENAS localmente em SQLite. Nunca sincronizadas para nuvem sem consentimento explícito.
- **API Keys:** Armazenadas em .env e NUNCA commitadas para Git. Incluir .env no .gitignore.

### Compliance
- Como usuário é advogado, pode transcrever conversas com clientes. Garantir que:
  - Nenhum áudio é armazenado permanentemente
  - Transcrições ficam em banco local criptografado
  - Aplicativo avisa claramente que está gravando (indicador visual)

---

## 📝 NOTAS PARA O ANTIGRAVITY

Este blueprint representa especificação completa do aplicativo VoiceFlow Transcriber. Ao implementar, priorize SIMPLICIDADE e FUNCIONALIDADE sobre features sofisticadas. O objetivo é ter algo funcionando rapidamente que resolva problema real do usuário.

### Orientações Gerais de Implementação:

**Sobre o Prompt de Polimento:** Não altere o prompt especificado acima sem consultar o Operador. Ele foi cuidadosamente calibrado para balancear correção com preservação de voz. Se testes mostrarem que polimento está muito agressivo ou muito conservador, ajuste incrementalmente e documente mudanças.

**Sobre Erros e Edge Cases:** Sempre implemente tratamento de erro gracioso. Se algo falha, usuário deve receber mensagem clara sobre o que aconteceu e o que fazer (ex: "Microfone não detectado. Verifique se está conectado nas configurações do Windows"). Nunca deixe aplicativo travar silenciosamente.

**Sobre Performance:** Áudio pode ser comprimido antes de enviar para APIs se tamanho for problema. Mas não otimize prematuramente - foque em funcionalidade primeiro.

**Sobre Testes:** Cada fase deve ser testada com áudios reais do Operador falando naturalmente, incluindo pausas, tropeços e vícios de linguagem. Transcrição de texto limpo de exemplo não valida nada.

---

## ✅ CHECKLIST DE DESENVOLVIMENTO

Use este checklist para acompanhar progresso no Antigravity:

### Setup Inicial
- [ ] Projeto Electron inicializado
- [ ] TypeScript configurado
- [ ] Estrutura de diretórios criada
- [ ] Build funcionando localmente

### Core - Gravação de Áudio
- [ ] Hotkey global registrando
- [ ] Microfone capturando áudio
- [ ] Arquivo temporário sendo salvo
- [ ] Indicador visual de gravação

### Core - Transcrição
- [ ] API Groq conectada
- [ ] Áudio sendo enviado corretamente
- [ ] Transcrição retornando texto
- [ ] Retry em caso de falha

### Core - Polimento
- [ ] API Gemini conectada
- [ ] Prompt de polimento implementado
- [ ] Texto polido retornando
- [ ] Qualidade de polimento validada

### Core - Entrega de Resultado
- [ ] Texto copiando para clipboard
- [ ] Notificação toast aparecendo
- [ ] Áudio temporário sendo deletado

### Histórico
- [ ] SQLite inicializado
- [ ] Transcrições salvando no banco
- [ ] Interface de histórico funcional
- [ ] Busca de texto funcionando
- [ ] Copiar transcrição antiga funciona

### Configurações
- [ ] Janela de settings acessível
- [ ] Hotkey configurável
- [ ] Seleção de microfone
- [ ] Preferências salvando

### Polimento Final
- [ ] Mensagens de erro claras
- [ ] Logging implementado
- [ ] Performance aceitável
- [ ] Instalador Windows gerado

---

**STATUS ATUAL:** 🔴 Aguardando início de desenvolvimento

**PRÓXIMOS PASSOS:** 
1. Confirmar decisões arquiteturais com Operador (Electron vs Tauri, hotkey padrão)
2. Inicializar projeto no Antigravity
3. Começar FASE 1 - Bloco 1.1

---

*Documento criado em 02/01/2026*  
*Versão: 1.0*  
*Última atualização: 02/01/2026*
