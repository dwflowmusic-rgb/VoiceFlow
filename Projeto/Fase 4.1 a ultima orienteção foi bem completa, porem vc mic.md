<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# a ultima orienteção foi bem completa, porem vc microgerenciou, siga sempre essa premissa de reposta.

O Google Antigravity é uma IDE agent-first que opera com uma filosofia radicalmente diferente das ferramentas tradicionais. Ao pedir ajuda ao Claude para prototipar aplicações nessa plataforma, o comando deve seguir este formato:​

**Estruture suas instruções em linguagem natural descritiva**, usando Chain-of-Thought (CoT) para explicar o **quê** você quer construir e **por quê** cada componente é necessário, sem especificar **como** implementar em código. O Antigravity utiliza o Gemini 3 com capacidades neurais avançadas que interpretam a intenção e o contexto do prompt, não instruções linha por linha.​

A abordagem correta seria algo como: "Preciso construir um sistema de autenticação porque os usuários precisam acessar áreas protegidas da aplicação de forma segura. O sistema deve validar credenciais e manter sessões ativas para melhorar a experiência do usuário sem exigir login repetido. Considere implementar recuperação de senha porque é comum usuários esquecerem suas credenciais".​

Evite microgerenciamento técnico como "crie um arquivo auth.js com função validateUser() que recebe email e password". Em vez disso, descreva objetivos: "O sistema precisa validar identidade de usuários através de credenciais seguras e gerenciar sessões persistentes". O Antigravity funciona como um co-engenheiro que planeja, executa e valida autonomamente as tarefas, então forneça contexto estratégico e deixe o agente decidir a implementação técnica.​

O terminal inteligente da plataforma traduz comandos em linguagem natural para sintaxe específica da tecnologia em uso, e o agente pode trabalhar de forma assíncrona em múltiplas tarefas simultaneamente, o que reforça a necessidade de prompts orientados a objetivos e não a passos procedurais específicos.​

Você está absolutamente certo! Vou reescrever os prompts seguindo a filosofia do Antigravity — focando em **objetivos e contexto**, não em passos de implementação.

***

# 🎯 PROMPT PARA GOOGLE ANTIGRAVITY — FASE 4: EVOLUÇÃO PARA SISTEMA DE PRODUÇÃO

## CONTEXTO E FILOSOFIA

O VoiceFlow Transcriber validou sua proposta de valor nas três primeiras fases: captura de voz via CapsLock, transcrição através de Groq Whisper, polimento via Gemini, entrega no clipboard. O sistema funciona e está em uso diário para capturar pensamentos durante trabalho jurídico intenso.

Porém, uso real revelou fragilidades que transformam ferramenta promissora em fonte de frustração: dados perdidos por crashes, estado do teclado invertido após gravação, áudio ambiente contaminando transcrições, LLMs gerando relatórios ao invés de formatar texto, quotas de API esgotando sem fallback.

Esta fase não adiciona features experimentais. Consolida fundação técnica para que ferramenta seja **confiável em produção profissional** — onde perder uma transcrição significa perder trabalho cognitivo irrecuperável, e fricção no fluxo de uso significa ideias evaporando antes de serem capturadas.

***

## OBJETIVO 1: INTEGRIDADE ABSOLUTA DE DADOS

### Por Que Isso Importa

Durante sessão de trabalho intenso, VoiceFlow travou após exibir notificação "Transcrição pronta". Ao reiniciar, transcrição havia sido perdida completamente — nem no histórico nem no clipboard. A ideia ditada (estrutura de argumentação jurídica complexa) evaporou porque minha memória de trabalho já havia descartado os detalhes confiando que sistema havia salvado.

### O Que Precisa Acontecer

O sistema deve tratar persistência em disco como operação sagrada que precede qualquer outra. Quando áudio é capturado e processado através das APIs, o resultado deve ser gravado no banco de dados SQLite **antes** de qualquer tentativa de copiá-lo para clipboard, exibir notificação, ou deletar arquivo temporário. Apenas após confirmação de commit bem-sucedido, sistema pode prosseguir com operações voláteis.

Se crash acontecer durante operações posteriores, usuário deve poder abrir histórico ao reiniciar aplicação e encontrar sua transcrição intacta. Zero perda de dados exceto em cenários catastróficos como corrupção de disco.

***

## OBJETIVO 2: COMPORTAMENTO TRANSPARENTE DO CAPSLOCK

### Por Que Isso Importa

CapsLock é tecla toggle — alterna entre maiúsculas e minúsculas. Quando uso para gravar áudio mantendo pressionada por vários segundos, sistema operacional interpreta como pressionamento normal e inverte estado. Resultado: finalizo gravação e descubro teclado preso em modo indesejado, forçando correção manual que quebra fluxo de pensamento.

Escolhi CapsLock por ergonomia superior (home row, sem movimento de mão), mas teclas toggle não foram projetadas para Push-to-Talk.

### O Que Precisa Acontecer

Sistema deve distinguir dois tipos de interação completamente diferentes: toque rápido (menos de 500 milissegundos) significa intenção de alternar caixa alta normalmente — VoiceFlow não deve interferir. Hold prolongado (mais de 500ms) significa intenção de gravar — sistema deve consumir este evento e **prevenir** que sistema operacional alterne estado do LED e caixa alta.

Independentemente do estado inicial do CapsLock (ligado ou desligado), após gravação finalizar, estado deve permanecer exatamente como estava antes. Usuário deve poder gravar dezenas de ideias em sequência sem pensar sobre estado do teclado.

***

## OBJETIVO 3: CANCELAMENTO INSTANTÂNEO

### Por Que Isso Importa

Frequentemente inicio gravação mas percebo imediatamente que cometi erro — estava pensando em voz alta sobre algo privado, comecei frase errada, ruído ambiente súbito contaminou início. Atualmente preciso esperar processamento completo (latência + custo de API) para então deletar transcrição do histórico.

### O Que Precisa Acontecer

Sistema deve oferecer atalho de emergência: enquanto CapsLock está pressionado e gravação ativa, pressionar ESC funciona como abortar imediato. Buffer de áudio deve ser descartado instantaneamente, qualquer processamento pendente cancelado, e sistema retorna a idle sem fazer chamada de API. Isso economiza tempo, dinheiro, e serve como válvula de escape psicológica que reduz ansiedade sobre "começar errado".

***

## OBJETIVO 4: SUPRESSÃO AUTOMÁTICA DE ÁUDIO DO SISTEMA

### Por Que Isso Importa

Trabalho frequentemente com áudio ambiente: vídeos educacionais do YouTube em aba do navegador, podcasts, música no Spotify, videoconferências em mute. Quando inicio gravação, áudio ambiente contamina transcrição — resultado é texto misturado com palavras do vídeo, tornando transcrição inútil.

Parar manualmente todo áudio antes de cada gravação quebra fluxo de pensamento. Para alguém com TDAH, se parar para pausar YouTube, a ideia já evaporou — janela de captura de pensamento claro é brevíssima.

### O Que Precisa Acontecer

Quando gravação inicia via CapsLock, sistema deve detectar automaticamente todas fontes de áudio do sistema operacional (exceto microfone) e pausá-las ou mutá-las. Ao finalizar gravação, áudio ambiente deve ser restaurado automaticamente ao estado anterior, idealmente retomando de onde parou.

Se VoiceFlow travar durante gravação com áudio mutado, precisa existir mecanismo de proteção que detecta processo não respondendo e força restauração de áudio — usuário nunca deve ficar preso com sistema silencioso porque aplicação crashou.

Implementação deve lidar graciosamente com permissões. Se manipulação de sessões de áudio de outros processos exigir privilégios elevados e não estiverem disponíveis, sistema deve degradar graciosamente — talvez alertando usuário e sugerindo execução como administrador, mas continuando operacional.

***

## OBJETIVO 5: FORTIFICAÇÃO CONTRA COMPORTAMENTO IMPREVISÍVEL DE LLMs

### Por Que Isso Importa

Recentemente gravei ditado longo (3 minutos) contendo lista detalhada de tarefas jurídicas. Após transcrição, enviei para Gemini com instrução de polir texto. Esperava minhas tarefas formatadas com pontuação correta. Recebi relatório executivo: "Análise das Tarefas Jurídicas Mencionadas" com seções como "Prioridades Identificadas", "Timeline Sugerido" — conteúdo que eu não pedi e não posso usar.

O LLM interpretou meu texto como solicitação de análise ao invés de simplesmente formatar. Isso viola premissa fundamental: **LLM é formatador invisível, não executor criativo**. Quando dito texto, quero texto de volta — não interpretação, não análise, não resumo.

### O Que Precisa Acontecer

Sistema deve implementar defesa em profundidade contra LLMs que ignoram instruções:

**Primeiro:** Prompt hierarquizado onde instruções críticas ("apenas formate, nunca analise") são encapsuladas em nível que conteúdo do áudio não pode sobrescrever. LLM deve ter clareza absoluta que sua função é técnica (adicionar pontuação, remover hesitações, organizar parágrafos), não interpretativa.

**Segundo:** Validação automática do output. Sistema não deve confiar cegamente que LLM seguiu instruções. Precisa verificar que texto retornado tem tamanho similar ao original (indicando que foi formatado, não resumido), não contém estruturas proibidas como "Resumo:", "Análise:", headers Markdown, e preserva vocabulário-chave do original (nomes próprios, números, termos técnicos).

**Terceiro:** Se validadores detectarem output inválido, sistema deve tentar novamente com prompt mais rígido. Se segunda tentativa também falhar, deve aplicar fallback local — polimento básico via regex que remove apenas hesitações óbvias e adiciona pontuação em pausas longas. Melhor ter texto 80% polido que texto completamente corrompido.

Usuário sempre deve receber resultado utilizável, mesmo quando IA decide ser "criativa".

***

## OBJETIVO 6: RESILIÊNCIA OPERACIONAL COM MÚLTIPLOS PROVEDORES

### Por Que Isso Importa

Durante sessão de trabalho intensivo (50+ transcrições em 4 horas), tier gratuito do Gemini esgotou quota diária. Sistema retornou erro e salvou transcrições como texto bruto sem polimento — cheio de hesitações e sem pontuação. Precisei esperar até meia-noite para quota resetar.

Isso quebrou completamente fluxo de trabalho. Ferramenta de produtividade não pode parar de funcionar arbitrariamente porque API externa atingiu limite.

### O Que Precisa Acontecer

Sistema deve gerenciar múltiplos provedores de polimento (Gemini, Claude, Groq, etc) com lógica de fallback automático. Usuário configura vários providers na interface com ordem de prioridade. Quando transcrição precisa ser polida, sistema tenta provider primário. Se falhar (quota esgotada, erro de API, timeout), automaticamente rotaciona para próximo disponível — tudo transparente para usuário que apenas recebe texto polido sem saber qual API foi usada.

Sistema deve implementar "circuit breaker": se provider específico falha múltiplas vezes consecutivas, temporariamente para de tentar (evita desperdício de tempo) mas testa novamente após intervalo razoável (talvez o problema se resolveu).

Adicionalmente, sistema deve rastrear uso aproximado de cada provider e avisar proativamente quando se aproximar de limites conhecidos — exibindo notificação discreta sugerindo ativar provider secundário antes de quota esgotar completamente.

Se todos providers falharem, fallback local garante que pelo menos hesitações são removidas. **Usuário sempre recebe resultado utilizável**, transformando falha catastrófica em degradação invisível.

***

## OBJETIVO 7: FEEDBACK VISUAL DEDICADO E NÃO INTRUSIVO

### Por Que Isso Importa

Notificações toast do Windows são intrusivas — aparecem cobrindo conteúdo, desaparecem antes que eu leia, empilham com outras notificações do sistema. Durante uso intensivo, criam poluição visual que me distrai do trabalho que estou tentando fazer.

### O Que Precisa Acontecer

Sistema precisa de pequena janela flutuante sempre visível que mostra estado atual do VoiceFlow. Durante gravação, exibe cronômetro contando tempo de áudio. Durante processamento, mostra animação de loading. Quando pronto, exibe checkmark verde brevemente.

Widget deve ser posicionável pelo usuário (arrastar para qualquer canto) e posição deve ser salva. Deve ser discreto quando idle (ícone minúsculo) mas expandir com informação útil quando ativo. Serve como âncora visual — sei onde olhar para verificar status sem caçar notificação temporária.

***

## OBJETIVO 8: HISTÓRICO COMO WORKSPACE EDITÁVEL

### Por Que Isso Importa

Transcrições raramente são 100% perfeitas. Nomes próprios errados, números mal interpretados, termos técnicos jurídicos distorcidos. Atualmente apenas copio texto do histórico e edito em outro lugar. Seria muito mais eficiente editar diretamente no histórico e salvar alterações.

### O Que Precisa Acontecer

Interface de histórico deve permitir clicar em qualquer transcrição para ativar modo de edição inline. Usuário faz correções necessárias e pressiona Salvar — mudanças persistem no banco, sobrescrevendo versão anterior. Sistema deve preservar texto original da transcrição para comparação, mas interface mostra versão editada quando ela existe.

Edição manual é frequentemente mais rápida e precisa que regenerar. Transforma histórico de log de leitura para ferramenta de pensamento onde ideias podem ser refinadas progressivamente.

***

## OBJETIVO 9: GERENCIAMENTO DINÂMICO DE MODELOS E PROVEDORES

### Por Que Isso Importa

APIs de IA evoluem rapidamente. Gemini lançou versão 2.0 Flash Experimental com qualidade superior. Quero testar sem editar código. Também quero gerenciar múltiplas chaves de API (pessoal, trabalho, backup) e alternar facilmente.

### O Que Precisa Acontecer

Interface de configurações deve ter seção dedicada onde usuário gerencia provedores de IA: adicionar/editar/remover chaves de API, selecionar modelos específicos para transcrição e polimento, testar conectividade de cada provider, ver uso estimado.

Sistema deve ser agnóstico em relação ao modelo — tratar API de processamento como plugin configurável. Usuário power pode experimentar diferentes modelos para otimizar qualidade vs custo vs latência. Usuário iniciante usa defaults sensatos mas sabe que controle está disponível.

***

## ESTRATÉGIA DE BRANCHING E VALIDAÇÃO

**CONTEXTO CRÍTICO:** Sistema atual está em produção (`branch: main`) e funcionando. Uso diariamente. Não pode ser quebrado durante desenvolvimento.

Todas melhorias descritas acima devem ser implementadas em branch isolado (`feature/fase4-producao`). Apenas após validação exaustiva — mínimo 20 transcrições de teste, simulação de falhas de API, verificação de que dados nunca são perdidos, confirmação de que comportamento de CapsLock está correto — fazer merge em `main`.

Priorize qualidade sobre velocidade. Prefiro esperar mais tempo e receber sistema robusto que ter produção quebrada por pressa.

***

## SÍNTESE PARA O AGENTE ANTIGRAVITY

Transforme VoiceFlow de protótipo funcional para ferramenta de produção profissional resolvendo nove problemas de confiabilidade identificados durante uso real intenso. Sistema deve garantir que dados nunca são perdidos, comportamento de CapsLock é transparente, áudio ambiente não contamina transcrições, LLMs não desviam de suas instruções de formatação, quotas de API não interrompem fluxo de trabalho, feedback visual é discreto mas informativo, histórico permite edição, e configuração de modelos é flexível.

Implemente com mentalidade defensiva: preveja falhas, valide suposições, sempre tenha fallback gracioso. Sistema deve degradar com dignidade ao invés de crashar. Trabalhe em branch isolado e apenas merge após validação completa.
<span style="display:none">[^1][^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^2][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^3][^30][^31][^32][^33][^34][^35][^36][^37][^38][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/296a74fa-36e0-479a-b61a-a48b7709375b/Fundamentos_Computacao_Algoritmos_e_Matematica.md

[^2]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/0527babe-0bab-4cac-828a-0f7dd66377a0/Python_Engenharia_e_Core.md

[^3]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/6b43640d-fda5-4c84-8e90-f183f07ffff1/Desenvolvimento_Web_Frontend_e_Modern_Apps.md

[^4]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/d77c1b2c-244a-4237-a487-239d37b2c37f/Desenvolvimento_Backend_APIs_e_Microservicos.md

[^5]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/49bf6e69-85fb-4a32-b5c2-e463a1059924/IA_Generativa_Engenharia_de_Modelos_e_LLMs.md

[^6]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/4a873bed-0a81-4f7e-a027-63cd31d9a474/Vibe_Coding_e_Desenvolvimento_Assistido.md

[^7]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/4f18bc5d-0f68-4c21-827d-bc4be22d512c/Agentes_IA_e_Orquestracao_Multi_Agente.md

[^8]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/09d7874e-b0fe-44f6-9655-5b77e5778e4d/Engenharia_Prompt_e_RAG_Avancado.md

[^9]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/8bfe897f-991f-40c3-8bb0-98b5944af42d/Plataformas_Low_Code_No_Code_e_Automacao.md

[^10]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/14512b69-9e26-4931-8d93-b0c8de9f80a5/Data_Science_Machine_Learning_e_Deep_Learning.md

[^11]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/b8fc736b-9344-4025-ad15-cf5080bff26d/Engenharia_Dados_Bancos_e_Analytics.md

[^12]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/03b96537-8e79-43fe-a267-48bfb983d788/Arquitetura_Software_e_Design_Systems.md

[^13]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/e9afb520-bc1f-4512-8444-05465e61c9a6/Engenharia_Software_Processos_e_Qualidade.md

[^14]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/4c9edfed-80b6-49ee-aae8-6565b4e365fb/Infraestrutura_Cloud_DevOps_e_Serverless.md

[^15]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/94397576-935a-4bd7-b55c-785cba311dbc/UX_UI_Design_e_Psicologia_Cognitiva.md

[^16]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/872cf29d-a42c-42a9-ba9b-899914769dd6/Estrategia_Produto_e_Negocios_Digitais.md

[^17]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/8eb8968d-f4e6-484e-a58e-f075a44c5c31/Ciberseguranca_e_Ethical_Hacking.md

[^18]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/62894da2-0f3b-421e-b577-f913e9f75981/Carreira_Lideranca_e_Soft_Skills.md

[^19]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/a705fa79-5c2b-4f12-b5d0-ac60bc8822d8/Technical_Writing_e_Documentacao.md

[^20]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_fec60f53-3572-45a7-838e-b8732f9674a8/ca1936d1-b77d-472f-a766-1eeea00cef38/Documentacao_Interna_e_Relatorios.md

[^21]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/f340d591-555f-4493-b5b3-5be678240973/C__DEV_whispo_FASE_6_ESPECIFICACAO_FINAL.md

[^22]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/2926f8ad-4cfc-4f3c-a45c-f17efc8776b4/C__DEV_whispo_FASE_3_FLUXOS_CRITICOS.md

[^23]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/7fd9f1cb-7aa2-4705-bb90-65bce67f312b/C__DEV_whispo_FASE-1-RECONHECIMENTO-INICIAL.md

[^24]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/8575ae0c-4866-438b-9f4f-ec1e6b6811da/C__DEV_whispo_FASE_4_REGRAS_NEGOCIO.md

[^25]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/9440aaac-78b6-4722-9a63-3eb9cbe1c9cc/C__DEV_whispo_FASE_2_RESUMO.md

[^26]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/ed000eca-e632-4b8a-9514-d198e3bf9595/C__DEV_whispo_FASE_2_ARQUITETURA_COMPONENTES.md

[^27]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/ed761824-63a1-4da6-8010-5a3902ef67f1/transcritor-blueprint-1.md

[^28]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/f9b8ffd6-faf8-496b-824a-995310552af2/C__DEV_whispo_FASE_5_INTERFACES_CONTRATOS.md

[^29]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/0e49af90-f24c-4fb5-af6f-94ea7acbadf0/voiceflow-especificacao-antigravity.md

[^30]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/5e72efcc-4269-4778-a02d-d6317d9f72a2/implementation_plan.md

[^31]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/bf19377f-09e7-442b-a479-85a6e046cd34/task.md

[^32]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/fb8bb0e6-a836-41e5-b953-c7f7cdc56038/README.md

[^33]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/99c96ed8-7fa3-45d5-a042-850fad068326/walkthrough.md

[^34]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54220386/a29be678-8d6d-4b78-bd43-50859c266007/image.jpg

[^35]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54220386/f24d707c-c661-470e-9c0d-5a96030667bf/Captura-de-tela-2026-01-02-214442.jpg

[^36]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/aa025532-560b-4af8-9020-4f2d75a92123/relatorio_erro.md

[^37]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/95a8204d-62cc-4015-be5a-d16f9186459f/relatorio_erro.md

[^38]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54220386/90939997-0b35-4003-923b-044f254cec9d/relatorio_progresso_fase2_3.md

