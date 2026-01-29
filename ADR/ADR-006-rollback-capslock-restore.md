# ADR-006: Rollback da Restauração de Estado do CapsLock

## Status

Revertido / Adiado

## Contexto

Na Fase 3, tentamos implementar a restauração automática do estado do LED do CapsLock (Ligado/Desligado) após a gravação para que o teclado voltasse ao estado anterior ao uso da hotkey.

## Decisão

Realizar um **rollback total** da implementação após detectar que ela introduziu instabilidade no loop crítico de detecção (`detector_tecla.py`) e causou erros de sintaxe decorrentes de edições complexas em blocos aninhados de hold/timeout.

## Racional

A estabilidade do pipeline de transcrição e a colagem inteligente são prioridades absolutas. Uma funcionalidade estética (LED) não deve comprometer a funcionalidade core (Texto). A decisão foi reverter para o estado estável v0.3.0 e mover a feature para o backlog da Fase 4 para uma reimplementação mais isolada.

## Consequências

- **Estabilidade Restaurada:** A aplicação voltou a funcionar de forma confiável.
- **Dívida Técnica:** A funcionalidade de "memória" do CapsLock continua pendente.
- **Aprendizado:** Mudanças em componentes de baixo nível (hardware polling) devem ser tratadas com cautela extrema e verificações de regressão rigorosas.

## Alternativas Rejeitadas

- **Tentar consertar em hotfix:** Descartado para evitar prolongar o estado de indisponibilidade da ferramenta durante a sessão de desenvolvimento.
