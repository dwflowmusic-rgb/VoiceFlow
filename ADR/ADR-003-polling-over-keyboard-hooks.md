# ADR-003: Polling Win32 sobre Hooks Globais

## Status

Aceito

## Contexto

Bibliotecas padrão de teclado em Python (`keyboard`, `pynput`) falharam em detectar de forma confiável o momento exato em que o CapsLock era solto, pois o Windows intercepta essa tecla para alternar o estado do sistema.

## Decisão

Implementar um **loop de polling** (verificação ativa) a cada 20ms utilizando a função `user32.GetAsyncKeyState(0x14)`.

## Consequências

- **Confiabilidade:** 100% de sucesso na detecção física da tecla, independente do estado lógico (LED ON/OFF).
- **Performance:** Consumo de CPU imperceptível (<0.1%) devido à eficiência da chamada Win32.
- **Threading:** Requer rodar em uma thread dedicada ou gerenciada pelo event loop do Qt para não bloquear a UI.

## Alternativas Rejeitadas

- **Hooks de Evento (SetWindowsHookEx):** Complexo demais para manter em Python e instável com teclas de toggle.
- **Bibliotecas High-Level:** Descartadas por inconsistência no reporte do estado UP do CapsLock.
