# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo. O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.3.0] - 2026-01-03

### Adicionado

- **Colagem Inteligente (Context-Aware):** Novo módulo `core/detector_foco.py` que rastreia a janela ativa via Win32 API.
- **Simulação de Ctrl+V:** O sistema agora automatiza a colagem de texto se o foco da janela permanecer o mesmo após a gravação.
- **Proteção de Foco:** Se o usuário mudar de janela enquanto dita, o sistema evita colagem acidental e mantém o texto apenas no clipboard.

### Alterado

- **Prompt de Polimento (Gemini):** Refinado para ser mais assertivo na proibição de listas e exigência de texto dissertativo corrido.
- **Notificações:** Mensagens de sucesso agora distinguem entre "Colado com sucesso" e "Copiado para o Clipboard (Foco alterado)".

### Corrigido

- **Rollback de CapsLock Restore:** Removida funcionalidade experimental de restauração de LED do CapsLock que estava introduzindo instabilidade no loop principal.
- **Ícone de Bandeja:** Implementado fallback para `SP_ComputerIcon` caso o arquivo `.ico` não seja encontrado.

## [0.2.0] - 2026-01-03

### Adicionado

- **Histórico SQLite:** Implementação de persistência local em `%APPDATA%/VoiceFlow/historico.db`.
- **Janela de Histórico (UI):** Interface Qt completa para visualização, busca textual e recuperação de transcrições antigas.
- **Salvamento Antecipado:** As transcrições agora são salvas no banco de dados **antes** de qualquer tentativa de interação com o clipboard, garantindo segurança de dados.

### Alterado

- **Máquina de Estados:** Integrada com o gerenciador de histórico para fluxo transacional.

## [0.1.0] - 2026-01-02

### Adicionado

- **Pipeline Core:** Implementação do fluxo completo CapsLock Hold -> Gravação -> Groq -> Gemini -> Clipboard.
- **Detector CapsLock:** Sistema de polling via Win32 API para detecção de hardware sem interferência do estado toggle do SO.
- **Integração Groq:** Transcrição rápida usando o modelo `whisper-large-v3-turbo`.
- **Polimento Gemini:** Refinamento gramatical via `gemini-1.5-flash`.
- **System Tray:** Ícone de bandeja para controle da aplicação.

### Corrigido

- **Clipboard Win32:** Substituição de `pyperclip` por implementação direta via `ctypes` para garantir que o Windows aceite a escrita do texto de forma robusta.
- **Retry Logic:** Resolvido bug de re-leitura de arquivo WAV durante tentativas falhas de API.

---
*Este changelog é gerado e mantido pela equipe de documentação VoiceFlow.*
