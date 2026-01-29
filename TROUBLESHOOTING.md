# Guia de Solução de Problemas (Troubleshooting)

Se o VoiceFlow não estiver se comportando como esperado, consulte este guia antes de abrir um ticket.

## 🔍 Problemas Comuns

### 1. O ícone da bandeja não aparece

- **Causa:** O Windows pode estar ocultando o ícone.
- **Solução:** Verifique a "setinha" da área de notificação do Windows. Se o problema persistir, verifique o console do terminal para erros de inicialização do PySide6.

### 2. Aperto CapsLock mas não grava

- **Causa:** Threshold de tempo ou conflito de driver.
- **Solução:** Você precisa segurar a tecla por pelo menos **500ms** (meio segundo). Se ainda não funcionar, tente executar o VoiceFlow como Administrador (o Windows às vezes bloqueia hooks de teclado em janelas de sistema).

### 3. O texto transcrito não cola (Ctrl+V falha)

- **Causa:** Perda de foco ou concorrência no clipboard.
- **Solução:** Verifique se você mudou de janela enquanto falava. O VoiceFlow agora protege o foco e não cola se a janela mudar. Confira se a notificação diz "Copiado para o Clipboard". Se sim, basta dar Ctrl+V manualmente.

### 4. Erros de API (Groq/Gemini)

- **Causa:** Chave inválida, falta de internet ou limite de cota.
- **Solução:** Verifique sua conexão e valide suas chaves no arquivo `.env` ou `config.json`. Veja o log `status.log` para mensagens de erro detalhadas das APIs.

### 5. Áudio distorcido ou "Nenhum som detectado"

- **Causa:** Microfone errado selecionado no Windows.
- **Solução:** Verifique se o microfone padrão do Windows está funcionando. O VoiceFlow utiliza o dispositivo de entrada padrão do sistema.

## 🛠️ Logs de Diagnóstico

O VoiceFlow gera logs automáticos para ajudar no diagnóstico:

- Verifique o terminal de execução.
- Procure por arquivos `.log` na raiz do projeto (se configurado).

## 🆘 Ainda precisa de ajuda?

Abra uma **Issue** no repositório com o log de erro anexado e descrevendo os passos para reproduzir o problema.
