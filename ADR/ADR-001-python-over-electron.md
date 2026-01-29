# ADR-001: Escolha de Stack (Python + Qt vs Electron)

## Status

Aceito

## Contexto

Precisávamos definir a stack tecnológica para uma aplicação desktop Windows que requer:

1. Longo tempo de execução em background (standby).
2. Acesso a APIs de baixo nível (Win32) para teclado e foco.
3. Integração rápida com SDKs de Inteligência Artificial.

## Decisão

Escolhemos **Python 3.10** com **PySide6 (Qt)**.

## Consequências

- **Consumo de RAM:** Baixíssimo (~25MB em standby) comparado aos 200MB+ de uma aplicação Electron típica.
- **Acesso Nativo:** Integração trivial com `user32.dll` via `ctypes`.
- **Distribuição:** Requer empacotamento (PyInstaller/Nuitka), que é mais complexo que o ecossistema Web.
- **UI:** Menos flexibilidade visual que CSS/HTML, mas suficiente para uma ferramenta "invisível".

## Alternativas Rejeitadas

- **Electron:** Descartado pelo overhead de memória e dificuldade de acesso ao kernel do Windows sem módulos em C++.
- **C# / .NET:** Excelente alternativa nativa, mas descartada pela menor agilidade da equipe na prototipagem com modelos de IA e processamento de áudio comparado a Python.
