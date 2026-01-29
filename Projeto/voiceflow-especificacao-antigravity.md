# RELATÓRIO EXECUTIVO: VOICEFLOW TRANSCRIBER
## Especificação Completa para Desenvolvimento no Google Antigravity

**Projeto:** VoiceFlow Transcriber - Sistema Leve de Transcrição com IA  
**Plataforma:** Aplicação Desktop Windows em Python  
**Restrição Crítica:** Máximo 20MB de RAM em uso normal  
**Filosofia:** Simplicidade radical, não-intrusivo, invisível durante operação

---

## CONTEXTO E OBJETIVO FUNDAMENTAL

Estamos construindo ferramenta desktop Windows que elimina completamente a fricção entre pensamento falado e texto escrito polido. O usuário trabalha ao longo do dia e precisa capturar ideias, rascunhar comunicações, ou documentar pensamentos sem interromper fluxo de trabalho para sessão formal de escrita. A experiência ideal é absolutamente invisível: pressionar tecla, falar naturalmente, soltar tecla, e segundos depois ter texto bem estruturado pronto para colar em qualquer aplicação.

Esta ferramenta foi projetada especificamente para usuário com TDAH que enfrenta bloqueio executivo ao se deparar com interfaces complexas. Cada interação adicional representa ponto de fricção que pode levar ao abandono do sistema. Por isso, toda arquitetura prioriza simplicidade sobre features sofisticadas, leveza sobre funcionalidades elaboradas, e invisibilidade sobre presença visual.

A aplicação deve rodar continuamente em background consumindo recursos mínimos. O limite absoluto é vinte megabytes de memória RAM em estado idle. Este número não é aspiracional, é mandatório. Soluções anteriores baseadas em Electron foram testadas e rejeitadas por consumirem duzentos megabytes, o que é completamente inaceitável para ferramenta que permanece ativa o dia inteiro.

---

## DECISÕES ARQUITETURAIS FUNDAMENTAIS

O sistema será construído inteiramente em Python porque oferece ecossistema maduro de bibliotecas para todas funcionalidades necessárias enquanto mantém footprint de memória extremamente baixo. Python permite desenvolvimento rápido com código limpo e manutenível que o desenvolvedor conseguirá evoluir facilmente no futuro. A aplicação é para uso pessoal exclusivo em ambiente Windows, então não há necessidade de suporte multiplataforma ou considerações de distribuição ampla.

Para interface gráfica mínima necessária, o sistema utilizará PyQt5 ou similar que renderiza usando componentes nativos do Windows. A escolha específica de toolkit pode ser deixada para o agente avaliar qual oferece melhor balanço entre simplicidade de implementação e leveza de recursos. O importante é que interface não seja baseada em web (sem Electron, sem webview embutido) para evitar overhead de renderização HTML e JavaScript.

A aplicação não terá janela principal visível durante operação normal. A presença do sistema será indicada apenas por ícone discreto na bandeja do sistema (system tray). Toda interação acontece através de menu de contexto ao clicar com botão direito nesse ícone, ou automaticamente através do hotkey global. Esta abordagem garante que sistema seja completamente invisível quando não está sendo ativamente usado.

---

## FASEAMENTO DE DESENVOLVIMENTO COM VALIDAÇÃO

O desenvolvimento deve acontecer em três fases distintas, onde cada fase deve estar completamente funcional e validada antes de avançar para próxima. Esta abordagem evita acumular dívida técnica e garante que problemas sejam identificados e resolvidos cedo, quando são mais fáceis de corrigir.

### FASE 1: NÚCLEO FUNCIONAL VALIDADO

O objetivo desta primeira fase é implementar e validar o pipeline completo de captura de áudio até entrega de texto polido no clipboard. Quando esta fase estiver concluída, usuário deve conseguir pressionar tecla, falar, soltar tecla, e receber texto pronto para colar, mesmo que sem interface elaborada ou persistência de histórico.

O sistema precisa implementar máquina de estados clara que transita entre cinco estados bem definidos. O estado inicial é IDLE onde sistema aguarda silenciosamente. Quando usuário pressiona hotkey F12 e mantém pressionado, sistema transita para estado RECORDING onde captura stream de áudio do microfone padrão do Windows bufferizando em memória. Quando usuário solta hotkey, sistema transita para TRANSCRIBING onde envia arquivo WAV temporário para API do Groq Whisper e aguarda resposta. Ao receber transcrição, transita para POLISHING onde envia texto para Gemini Flash com prompt de polimento. Quando texto polido retorna, transita para COMPLETE onde copia resultado para clipboard e exibe notificação. Se qualquer etapa falhar, sistema deve transitar para estado ERROR e informar usuário do problema antes de retornar a IDLE.

A implementação de cada transição de estado deve incluir logging apropriado que permita debugging eficiente durante desenvolvimento. Quando sistema transita de IDLE para RECORDING, deve logar timestamp e confirmar que microfone foi acessado com sucesso. Durante RECORDING, deve logar periodicamente duração da gravação para permitir verificar que captura está acontecendo. Ao transitar para TRANSCRIBING, deve logar tamanho do arquivo WAV gerado e endpoint da API sendo chamado. Cada transição subsequente deve ser similarmente logada.

Para captura de áudio, sistema deve usar biblioteca Python que acessa diretamente API de áudio do Windows. A implementação precisa detectar microfone padrão configurado nas configurações do sistema e usar esse dispositivo automaticamente sem exigir seleção manual. O áudio deve ser capturado em formato compatível com especificações da API Groq - tipicamente WAV com taxa de amostragem de dezesseis mil hertz e codificação PCM de dezesseis bits. Durante captura, áudio deve ser mantido em buffer de memória eficiente que cresce dinamicamente conforme mais dados chegam.

Quando usuário solta hotkey, sistema deve imediatamente parar stream de áudio e converter buffer completo para arquivo WAV temporário salvo no diretório temp do Windows. O nome do arquivo deve incluir timestamp para evitar colisões se múltiplas gravações acontecerem rapidamente. Após salvar arquivo, sistema deve validar que arquivo foi criado com sucesso e tem tamanho maior que zero bytes antes de prosseguir para etapa de transcrição.

A integração com API do Groq deve ser implementada através de cliente HTTP que envia requisição POST multipart form-data contendo o arquivo WAV. A requisição precisa incluir header de autorização com API key que será fornecida através de arquivo de configuração JSON localizado no mesmo diretório do executável. O formato deste arquivo de configuração deve seguir estrutura que decidimos copiar do Whispo, contendo seções para transcription provider e polishing provider com seus respectivos modelos e credenciais.

Sistema deve implementar timeout de quinze segundos para chamada ao Groq. Se resposta não chegar nesse período, deve abortar requisição e tentar novamente até máximo de duas tentativas adicionais usando backoff exponencial - primeira retry após dois segundos, segunda retry após quatro segundos. Se todas tentativas falharem, sistema deve transitar para estado ERROR e exibir notificação clara informando que transcrição falhou, sugerindo verificar conexão de internet e tentar novamente.

Quando resposta bem-sucedida chega do Groq, sistema deve parsear JSON retornado e extrair campo text contendo transcrição. Esta transcrição bruta deve ser imediatamente logada para permitir debugging de qualidade. O texto então precisa ser enviado para API do Google Gemini Flash via Vertex AI acompanhado de prompt system detalhado.

O prompt de polimento deve instruir modelo de forma extremamente específica sobre o que fazer e o que evitar. Deve solicitar que modelo adicione pontuação apropriada incluindo vírgulas em pausas naturais, pontos finais ao fim de sentenças completas, interrogações em perguntas, e exclamações quando apropriado. Deve pedir organização em parágrafos quando houver mudança clara de assunto ou tópico. Deve instruir remoção de vícios de linguagem comuns como tipo, né, então quando usados apenas como preenchimento sem função semântica. Deve solicitar eliminação de repetições de palavras que claramente foram tropeços na fala. Deve pedir correção de falsos começos onde pessoa inicia frase de um jeito e recomeça de outro.

Crucialmente, o prompt deve enfatizar várias vezes usando linguagem clara que modelo NUNCA deve alterar vocabulário, NUNCA deve adicionar informações que não estavam no áudio, NUNCA deve formalizar linguagem se fala foi coloquial, NUNCA deve mudar primeira pessoa para terceira, e NUNCA deve reescrever conteúdo. O objetivo é apenas polir imperfeições mecânicas da fala transcrita mantendo completamente a voz e intenção do falante.

Similar à integração com Groq, chamada ao Gemini deve ter timeout de quinze segundos e lógica de retry com duas tentativas adicionais. Se polimento falhar completamente após todas tentativas, sistema deve implementar fallback gracioso usando transcrição bruta do Groq ao invés de deixar usuário sem nenhum texto. Texto não polido ainda é substancialmente melhor que nada.

Quando texto polido está pronto, sistema deve copiar para clipboard do Windows usando biblioteca apropriada que acessa API de clipboard do sistema operacional. Imediatamente após copiar, deve exibir notificação toast nativa do Windows dizendo simplesmente Transcrição pronta e disponível no clipboard. Esta notificação deve aparecer por três segundos e desaparecer automaticamente sem exigir interação do usuário.

Finalmente, arquivo WAV temporário que foi criado deve ser deletado para liberar espaço e proteger privacidade. Sistema deve logar se deletion foi bem-sucedida. Após completar todas essas etapas, sistema retorna para estado IDLE aguardando próxima ativação do hotkey.

**VALIDAÇÃO OBRIGATÓRIA DA FASE 1:**

Esta fase só pode ser considerada completa quando todas estas validações passarem com sucesso. Primeiro, deve existir teste que simula pressionar hotkey, aguardar três segundos, soltar hotkey, e verificar que arquivo WAV foi criado com tamanho apropriado. Segundo, deve existir teste que envia arquivo WAV de amostra para Groq e verifica que transcrição retorna corretamente. Terceiro, deve existir teste que envia texto de amostra para Gemini e verifica que polimento acontece conforme esperado. Quarto, deve existir teste end-to-end que executa fluxo completo do hotkey até clipboard e verifica que texto final está correto.

Todos logs gerados durante execução devem ser salvos em arquivo rotating que mantém últimas cem mil linhas para permitir debugging de problemas que apareçam durante uso real. Cada entrada de log deve incluir timestamp preciso, nível de severidade, nome do componente que gerou mensagem, e descrição clara do evento.

Somente quando todos esses testes passarem de forma confiável e sistema demonstrar consumo de memória abaixo de vinte megabytes durante todo pipeline, a Fase 1 pode ser considerada concluída e desenvolvimento pode avançar para Fase 2.

### FASE 2: PERSISTÊNCIA E HISTÓRICO

Com núcleo funcional validado, esta fase adiciona capacidade de salvar todas transcrições em banco de dados SQLite local para consulta posterior. O objetivo é que usuário consiga acessar transcrições antigas se precisar recuperar algo que falou dias ou semanas atrás.

Sistema deve criar banco de dados SQLite no diretório de dados da aplicação do usuário, tipicamente localizado em AppData Roaming sob nome da aplicação. O banco deve conter tabela transcriptions com estrutura que decidimos copiar do Whispo. Esta tabela deve ter campo id sendo chave primária tipo TEXT contendo UUID gerado para cada transcrição. Campo timestamp tipo INTEGER armazenando época Unix do momento quando transcrição foi iniciada. Campo raw_text tipo TEXT contendo transcrição bruta retornada pelo Groq. Campo polished_text tipo TEXT contendo versão final polida pelo Gemini. Campo duration_seconds tipo REAL armazenando duração da gravação em segundos com precisão de duas casas decimais. Campo created_at tipo INTEGER com valor padrão sendo timestamp de inserção no banco.

Sempre que transcrição completa com sucesso, sistema deve inserir novo registro nesta tabela contendo todos campos mencionados. A inserção deve acontecer de forma transacional para garantir que mesmo se aplicação crashar imediatamente após, registro já está persistido. Falha na inserção não deve impedir entrega do texto para clipboard, mas deve ser logada como warning para que desenvolvedor saiba que histórico pode estar incompleto.

Esta fase deve adicionar interface simples de histórico acessível através do menu de contexto do ícone na bandeja. Quando usuário seleciona opção Ver Histórico no menu, deve abrir janela mostrando lista de todas transcrições ordenadas por timestamp decrescente, ou seja, mais recente no topo. Cada item na lista deve mostrar timestamp formatado de forma legível, primeiras cinquenta caracteres do texto polido, e duração da gravação. Usuário deve conseguir clicar em qualquer item para ver texto completo em painel de detalhes.

A interface de histórico deve incluir campo de busca simples no topo que permite filtrar transcrições por texto. Quando usuário digita no campo de busca, lista deve atualizar em tempo real mostrando apenas transcrições onde texto polido ou texto bruto contém termo buscado, usando busca case-insensitive. Busca deve ser implementada através de query SQL com cláusula WHERE usando operador LIKE para permitir matching parcial.

Janela de histórico deve ter botão para copiar texto de transcrição selecionada novamente para clipboard, permitindo que usuário reutilize texto antigo sem precisar falar novamente. Deve também ter botão para deletar transcrição selecionada se usuário quiser remover algo do histórico, com dialog de confirmação antes de executar deletion permanente.

**VALIDAÇÃO OBRIGATÓRIA DA FASE 2:**

Teste deve criar dez transcrições via interface normal e verificar que todas aparecem corretamente no histórico ordenadas por timestamp. Teste deve usar funcionalidade de busca para encontrar transcrição específica por palavra-chave única e verificar que filtragem funciona. Teste deve deletar transcrição e verificar que desaparece do histórico e do banco de dados. Teste deve copiar texto de transcrição antiga para clipboard e verificar que conteúdo está correto.

Adicionalmente, deve existir teste que insere milhares de registros falsos no banco de dados e verifica que interface de histórico permanece responsiva durante scroll e busca. Deve também verificar que tamanho do arquivo SQLite cresce de forma razoável e não explode descontroladamente.

Somente quando histórico estiver funcionando de forma confiável e não introduzir regressões no core funcional da Fase 1, desenvolvimento pode avançar para Fase 3.

### FASE 3: CONFIGURAÇÕES E REFINAMENTOS DE UX

Esta fase final adiciona interface de configurações para permitir customização de comportamento, implementa melhorias de experiência do usuário como feedback visual durante gravação, e adiciona sistema de personas para polimento contextual.

Sistema deve adicionar janela de configurações acessível através de menu de contexto do ícone na bandeja. Esta janela deve exibir todas configurações atualmente disponíveis organizadas em seções lógicas. Seção de Transcrição deve mostrar provider atual (Groq), modelo sendo usado (whisper-large-v3), e campo para API key. Seção de Polimento deve mostrar se polimento está habilitado via toggle, provider (Gemini), e persona ativa selecionada via dropdown.

A configuração de hotkey deve ser editável através de campo especial que detecta quando usuário pressiona combinação de teclas desejada e registra essa combinação. Durante edição, sistema deve validar que combinação escolhida não conflita com hotkeys do sistema Windows e avisar usuário se houver potencial problema. Mudança de hotkey deve ter efeito imediato após salvar configurações sem exigir restart da aplicação.

Sistema deve implementar sistema de personas similar ao que analisamos no Whispo, onde usuário pode escolher entre diferentes estilos de polimento dependendo do contexto de uso. Persona Advogado mantém terminologia jurídica técnica e linguagem formal apropriada para ambiente profissional. Persona Desenvolvedor preserva termos técnicos de programação e usa sintaxe concisa. Persona Casual mantém tom coloquial sem formalização excessiva. Persona TDAH-Friendly organiza agressivamente em tópicos numerados e remove todas repetições. Cada persona tem variante específica do prompt de polimento otimizada para aquele contexto.

Configuração de persona ativa fica salva no arquivo config.json e é aplicada automaticamente em todas transcrições subsequentes. Usuário pode mudar persona a qualquer momento através da janela de configurações. O sistema deve também permitir desabilitar polimento completamente através de toggle, fazendo com que texto bruto da transcrição vá direto para clipboard sem passar pelo Gemini.

Para melhorar feedback durante gravação, sistema deve implementar pequena janela toast que aparece quando hotkey é pressionado mostrando ícone de microfone vermelho e contador de tempo em segundos indicando duração da gravação atual. Esta janela deve ser posicionada no canto superior direito da tela de forma não-intrusiva e atualizar contador a cada segundo. Quando gravação para, janela deve mostrar mensagem Processando por alguns segundos até texto estar pronto.

Opcionalmente, sistema pode implementar sons discretos de clique no início e fim da gravação para fornecer feedback auditivo que gravação iniciou e parou. Estes sons devem ser extremamente curtos, não mais que cem milissegundos, e com volume moderado para não serem intrusivos. A reprodução de sons deve ser configurável via toggle nas settings para usuários que preferem operação completamente silenciosa.

Sistema deve também implementar validação de descarte automático de gravações muito curtas. Se duração total da gravação for menor que meio segundo, isso provavelmente indica acionamento acidental do hotkey e pode ser descartado silenciosamente sem gastar chamadas de API. Esta lógica evita desperdiçar quota do Groq com toques inadvertidos no hotkey durante digitação normal.

**VALIDAÇÃO OBRIGATÓRIA DA FASE 3:**

Teste deve mudar hotkey nas configurações e verificar que novo hotkey funciona enquanto antigo para de funcionar. Teste deve alternar entre diferentes personas e verificar que polimento reflete estilo apropriado de cada persona. Teste deve desabilitar polimento e verificar que transcrição bruta vai direto para clipboard. Teste deve criar gravação de apenas duzentos milissegundos e verificar que é descartada automaticamente.

Interface de configurações deve ser testada extensivamente para garantir que todas mudanças são persistidas corretamente no config.json e que aplicação lê configurações ao iniciar sem falhar se arquivo estiver malformado ou ausente. Deve existir tratamento de erro que cria arquivo de configuração com valores padrão se arquivo não existir ou estiver corrompido.

Ao final da Fase 3, sistema deve estar completamente funcional com todas features essenciais e opcionais implementadas, testadas, e validadas.

---

## ESTRUTURA DE CONFIGURAÇÃO HERDADA DO WHISPO

O sistema deve utilizar arquivo config.json localizado no mesmo diretório do executável ou no diretório de dados da aplicação, seguindo estrutura hierárquica clara que separar configurações por domínio funcional. A estrutura completa deve conter chave hotkey no nível raiz especificando combinação de teclas, tipicamente valor único como F12 ou CapsLock. Deve conter objeto transcription com chaves provider indicando qual serviço usar (groq sendo único suportado inicialmente), model especificando qual modelo do provider (whisper-large-v3), e api_key contendo credencial de autenticação.

Deve conter objeto polishing com chave enabled sendo booleano indicando se polimento está ativo, provider especificando qual LLM usar (gemini), persona indicando estilo de polimento ativo (casual, advogado, desenvolvedor, tdah), e api_key contendo credenciais do Google Cloud. Opcionalmente pode conter objeto ui com configurações visuais como play_sounds booleano controlando feedback auditivo e show_recording_overlay booleano controlando se janela de gravação aparece.

Se arquivo não existir na primeira execução, sistema deve criar automaticamente com valores padrão sensatos que permitam funcionamento imediato após usuário adicionar apenas as API keys necessárias. Se arquivo existir mas estiver malformado, sistema deve logar erro detalhado e criar backup do arquivo corrompido antes de sobrescrever com configuração padrão.

---

## TRATAMENTO DE ERROS E ROBUSTEZ

Sistema deve ser extremamente robusto a condições de erro porque será usado continuamente ao longo do dia e falhas não podem interromper trabalho do usuário. Cada ponto de falha potencial deve ter tratamento específico que informa usuário claramente do problema sem crashar aplicação.

Se microfone não estiver disponível quando hotkey é pressionado, seja porque está sendo usado por outra aplicação ou porque não há dispositivo de áudio conectado, sistema deve exibir notificação toast dizendo Microfone não disponível e retornar imediatamente para estado IDLE. Não deve tentar gravar ou crashar.

Se conexão de internet estiver indisponível quando tentando chamar APIs, sistema deve detectar erro de rede e exibir notificação Sem conexão de internet - verifique rede e tente novamente. Deve retornar para IDLE sem deixar processo pendente consumindo recursos.

Se API keys estiverem inválidas ou quota de uso tiver sido excedida, sistema deve parsear mensagem de erro retornada pela API e exibir notificação contextual. Para Groq, se quota diária de oito horas foi excedida, deve avisar especificamente Limite diário do Groq atingido - tente novamente amanhã. Para Gemini, se API key estiver inválida, deve avisar Credenciais do Gemini inválidas - verifique configuração.

Se arquivo WAV gerado tiver problema (tamanho zero, formato corrompido, codec incompatível), sistema deve detectar durante validação pré-upload e abortar com mensagem Falha ao capturar áudio - tente novamente. Deve deletar arquivo corrompido e não tentar enviá-lo para API.

Todos erros devem ser logados com stack trace completo para permitir debugging, mas mensagens mostradas ao usuário devem ser simples e acionáveis sem jargão técnico. Usuário não precisa saber que houve ConnectionRefusedError na linha 247 do módulo api_client - precisa saber que não conseguiu conectar ao servidor e deve verificar internet.

---

## ESTRATÉGIA DE LOGGING E DEBUGGING

Sistema deve implementar logging estruturado usando biblioteca de logging do Python configurada para escrever em arquivo rotating que mantém máximo de cinco megabytes de logs antes de rotacionar para arquivo novo. Logs devem ficar em subdiretório logs dentro do diretório de dados da aplicação.

Cada entrada de log deve seguir formato consistente começando com timestamp ISO8601 com precisão de milissegundos, seguido de nível de severidade entre colchetes (DEBUG, INFO, WARNING, ERROR, CRITICAL), seguido de nome do módulo que gerou log, seguido da mensagem. Por exemplo: 2026-01-02T14:23:45.123 [INFO] audio_capture: Iniciando gravação com microfone padrão.

Durante desenvolvimento, nível de log deve ser DEBUG para capturar máximo de informação. Durante produção, pode ser INFO para reduzir verbosidade mas ainda manter visibilidade de operações importantes. Erros devem sempre ser logados em nível ERROR com stack trace completo.

Pontos críticos que devem ser logados incluem transições de estado da máquina, início e fim de chamadas de API com latência medida, criação e deletion de arquivos temporários, falhas de qualquer tipo com contexto completo, e mudanças de configuração. Logging bem implementado permite diagnosticar problemas reportados por usuário analisando arquivo de log sem precisar reproduzir bug.

---

## MÉTRICAS DE SUCESSO E VALIDAÇÃO FINAL

Ao final do desenvolvimento completo das três fases, sistema deve atender todos critérios de sucesso definidos. Consumo de memória RAM deve permanecer abaixo de vinte megabytes durante estado IDLE e não exceder cinquenta megabytes durante processamento ativo. Latência total desde soltar hotkey até texto aparecer no clipboard deve ser menor que quinze segundos para gravação de um minuto, assumindo conexão de internet razoável.

Taxa de sucesso de transcrição deve ser superior a noventa e cinco por cento excluindo falhas de rede que estão fora do controle da aplicação. Qualidade de polimento deve ser tal que oitenta por cento das transcrições não requeiram nenhuma edição manual para uso. Sistema deve funcionar de forma confiável por dias ou semanas consecutivos sem crashes ou memory leaks.

Interface deve ser responsiva com tempo de resposta abaixo de cem milissegundos para todas interações do usuário. Janelas devem abrir instantaneamente, busca no histórico deve retornar resultados em tempo real conforme usuário digita, e mudanças de configuração devem ter efeito imediato.

O aplicativo deve iniciar junto com Windows através de entrada no registro de startup e ficar disponível imediatamente após boot sem exigir ação do usuário. Ícone na bandeja deve estar sempre visível e acessível durante operação normal do sistema.

---

## PRÓXIMOS PASSOS APÓS CONCLUSÃO

Com sistema completamente funcional e validado, próximas evoluções podem incluir recursos adicionais que não são essenciais para MVP mas agregariam valor. Integração com VoiceFlow Transcriber poderia ser embeddable component que outros aplicativos consomem. Suporte a múltiplos idiomas além de português através de detecção automática. Sincronização opcional de histórico com cloud storage para backup. Exportação de histórico completo para formatos como CSV ou JSON.

Porém, todas essas evoluções futuras só devem ser consideradas após MVP estar em produção sendo usado diariamente e provando seu valor. Adicionar features antes de validar utilidade do core é armadilha comum que leva a software inchado que ninguém usa.

---

## RESUMO EXECUTIVO PARA ANTIGRAVITY

Este documento define aplicação desktop Windows em Python que captura áudio via hotkey global, transcreve usando Groq Whisper, poli usando Gemini Flash, e entrega texto no clipboard automaticamente. Sistema deve consumir no máximo vinte megabytes de RAM e ser completamente não-intrusivo durante operação.

Desenvolvimento acontece em três fases sequenciais com validação obrigatória entre fases. Fase 1 implementa núcleo funcional com máquina de estados, captura de áudio, integração com APIs, e entrega para clipboard. Fase 2 adiciona persistência em SQLite e interface de histórico com busca. Fase 3 adiciona configurações, sistema de personas, e refinamentos de UX.

Sistema herda conceitos específicos do projeto Whispo incluindo estrutura de config.json, máquina de estados com cinco estados bem definidos, timeout e retry logic com backoff exponencial, e formato de tabela SQLite para histórico. Implementação deve ser robusta com tratamento de erro comprehensivo e logging detalhado.

Sucesso será medido por consumo de memória abaixo de limite, latência total aceitável, alta taxa de sucesso de transcrição, e qualidade de polimento que elimina necessidade de edição manual na maioria dos casos.

Erratas e correções e adições.

AJUSTES FINAIS RECOMENDADOS (Opcionais)
1. Especificar Bibliotecas Python Sugeridas (Sem Obrigar)
O documento evita mencionar libs específicas, o que é bom para não microgerenciar. Mas seria útil sugerir (não obrigar) algumas opções que você já validou:

text
## BIBLIOTECAS PYTHON SUGERIDAS (Não Obrigatórias)

O agente tem autonomia para escolher stack específico, mas estas 
bibliotecas foram pré-validadas para os requisitos:

- **Hotkey Global**: `keyboard` ou `pynput` (ambas funcionam no Windows)
- **Captura de Áudio**: `pyaudio` ou `sounddevice` (PyAudio mais maduro)
- **Interface Gráfica**: `PyQt5` ou `PySide6` (PySide6 tem licença mais permissiva)
- **SQLite**: `sqlite3` (built-in Python, zero dependências)
- **HTTP Requests**: `requests` ou `httpx` (requests mais simples)
- **Clipboard**: `pyperclip` ou `win32clipboard` (pyperclip cross-platform)
- **Notificações**: `plyer` ou `win10toast` (win10toast nativo Windows)

Qualquer alternativa que atenda requisitos é aceitável.
Por quê? Antigravity pode gastar 20min experimentando libs ruins se não tiver ponto de partida. Sugerir sem obrigar acelera prototipagem.

2. Adicionar Seção "Não Fazer" Explícita
Documento já evita coisas ruins implicitamente, mas seria útil ter lista explícita:

text
## ⚠️ ANTI-PATTERNS A EVITAR

- ❌ **NÃO** usar Electron, webview, ou qualquer stack web-based
- ❌ **NÃO** adicionar features "nice-to-have" antes de validar MVP
- ❌ **NÃO** implementar multi-threading complexo (simplicidade > performance)
- ❌ **NÃO** criar abstrações genéricas para "suportar futuros providers"
- ❌ **NÃO** tentar otimizar código antes de medir consumo de memória
- ❌ **NÃO** salvar áudio permanentemente (privacidade + espaço)
- ❌ **NÃO** tentar fazer tudo em uma única fase gigante
Por quê? Agentes às vezes fazem "over-engineering" por default. Lista explícita de anti-patterns evita isso.

3. Especificar Estrutura de Diretórios Inicial
Documento menciona "config.json no mesmo diretório do executável", mas poderia ser mais específico:

text
## ESTRUTURA DE ARQUIVOS E DIRETÓRIOS

voiceflow/
├── voiceflow.py # Entry point da aplicação
├── config.json # Configurações (criado automaticamente)
├── core/
│ ├── state_machine.py # Máquina de estados
│ ├── audio_capture.py # Captura de áudio
│ ├── api_client.py # Integração Groq + Gemini
│ └── clipboard_manager.py # Gerenciamento de clipboard
├── ui/
│ ├── tray_icon.py # System tray icon
│ ├── history_window.py # Janela de histórico
│ └── settings_window.py # Janela de configurações
├── data/
│ ├── transcriptions.db # Banco SQLite
│ └── logs/ # Logs rotativos
└── resources/
├── icon.png # Ícone da aplicação
└── sounds/ # Sons de feedback (opcional)

text
undefined
Por quê? Estrutura clara desde o início evita refatorações massivas depois.

**Data de Criação:** 02 de Janeiro de 2026  
**Versão:** 1.0 - Especificação Completa para Prototipagem e Desenvolvimento  
**Status:** Pronto para Implementação no Google Antigravity
