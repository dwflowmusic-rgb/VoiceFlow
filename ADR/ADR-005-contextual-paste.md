# ADR-005: Colagem Contextual Inteligente

## Status

Aceito

## Contexto

Durante ditações longas, o usuário pode mudar de janela (ex: para consultar uma referência). Caso o sistema cole o texto automaticamente ao soltar a tecla, ele pode "poluir" a janela errada, causando frustração e risco de perda de contexto.

## Decisão

Implementar uma verificação de foco via `GetForegroundWindow`.

- Capturar o `HWND` inicial no momento do press do CapsLock.
- No momento do release, comparar com o `HWND` atual.
- **Se igual:** Executar colagem automática (SendInput Ctrl+V).
- **Se diferente:** Apenas copiar para o clipboard e notificar o usuário.

## Consequências

- **UX Protegida:** O usuário tem controle total sobre onde o texto será inserido.
- **Transparência:** Notificações contextuais informam exatamente o que aconteceu ("Colado" vs "Pronto no Clipboard").
- **Dependência:** Adiciona necessidade de monitoramento nativo de janelas do Windows.

## Alternativas Rejeitadas

- **Sempre Colar:** Prejudicial à experiência do usuário em fluxos multitarefa.
- **Nunca Colar (Sempre Clipboard):** Exige um passo manual extra (Ctrl+V) desnecessário para o caso de uso mais comum (90% das vezes o usuário continua na mesma janela).
