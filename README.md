# VoiceFlow Transcriber v1.0
>
> **Transforme pensamentos em texto fluído instantaneamente, sem tirar as mãos do teclado.**

![Status](https://img.shields.io/badge/Status-Produção-green)
![Versão](https://img.shields.io/badge/Versão-1.0.0-blue)
![Plataforma](https://img.shields.io/badge/Plataforma-Windows-lightgrey)

O **VoiceFlow Transcriber** é uma ferramenta de produtividade focada em fluidez e acessibilidade. Desenhado para profissionais que pensam mais rápido do que digitam, o VoiceFlow remove a fricção da escrita ao oferecer uma ponte invisível entre a voz e o texto polido.

## ✨ Funcionalidades (v1.0)

### 🎙️ Core

- **Transcrição Instantânea via CapsLock:** Segure a tecla CapsLock para falar (Tap to Toggle / Hold to Record).
- **Polimento Inteligente (Gemini):** Transforma fala bruta em texto dissertativo profissional, removendo gaguejos e vícios de linguagem.
- **Anti-Alucinação:** Filtros avançados no Groq e Gemini impedem a invenção de textos ("Obrigado por assistir", legendas falsas) em ambientes silenciosos.

### 🖥️ Interface & UX

- **Widget de Status (OSD):** Feedback visual minimalista e flutuante. Vermelho (Gravando), Amarelo (Processando), Verde (Pronto).
- **Colagem Inteligente:** Detecta se você manteve a janela em foco e cola o texto automaticamente.
- **System Tray:** Ícone na bandeja para controle discreto e notificações não-intrusivas.

### 💾 Gerenciamento de Dados

- **Histórico Persistente:** Banco de dados SQLite local.
- **Janela de Histórico:** Pesquise, copie ou exclua transcrições antigas.
- **Retenção Automática:** Limpeza automática de registros com mais de 5 dias (configurável).

### ⚙️ Sistema

- **Inicialização Automática:** Opção "Iniciar com Windows" integrada ao menu da bandeja.
- **Baixo Consumo:** Otimizado para rodar em background (<20MB RAM).

## 🛠️ Instalação

### Pré-requisitos

- Python 3.10+
- Chaves de API: **Groq** e **Google Gemini**.

### Configuração

1. **Clone e Instale:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure as chaves:**
   Crie `config.json` na raiz:

   ```json
   {
       "transcription": {
           "provider": "groq",
           "api_key": "seu_key_groq",
           "model": "distil-whisper-large-v3-en"
       },
       "polishing": {
           "provider": "gemini",
           "api_key": "seu_key_gemini",
           "model": "gemini-1.5-flash"
       }
   }
   ```

3. **Execute:**

   ```bash
   python voiceflow.py
   ```

## ⌨️ Como Usar

1. **Gravar:** Segure **CapsLock** (>500ms). O Widget ficará vermelho.
2. **Falar:** Dite suas ideias. O sistema filtra pausas e ruídos.
3. **Soltar:** Ao soltar a tecla, o Widget fica amarelo (Processando).
4. **Receber:** Em segundos, o texto polido é colado no seu cursor. O Widget fica verde.

---
*VoiceFlow Team — 2026*
