# ADR-002: CapsLock como Hotkey de Ativação

## Status

Aceito

## Contexto

O usuário precisa de uma forma de ativar a gravação sem tirar as mãos da "home row" do teclado e sem depender de atalhos de múltiplas teclas (Ctrl+Alt+V).

## Decisão

Utilizar a tecla **CapsLock** como um botão "Push-to-Talk" (segurar para gravar).

## Consequências

- **Ergonomia:** É a tecla mais acessível para um usuário de produtividade.
- **Hardware:** CapsLock é uma *toggle key* no Windows, o que cria complexidade na detecção de eventos de subida/descida (release/press).
- **UX:** O usuário perde a funcionalidade original de "Gritar" (Caps ON) se não implementar uma restauração de estado (adiada para Fase 4).

## Alternativas Rejeitadas

- **F12:** Muito longe do centro do teclado.
- **Scroll Lock:** Ausente em muitos teclados modernos/compactos.
- **Shift+Espaço:** Conflito comum com editores de código e IDEs.
