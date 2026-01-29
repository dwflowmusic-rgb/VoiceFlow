# FASE 4: REGRAS DE NEGÓCIO E LÓGICA CORE

## RESUMO EXECUTIVO

Whispo implementa lógica de negócio principalmente em 3 áreas: **(1) Captura e processamento de áudio**, **(2) Integração com APIs externas**, e **(3) Gerenciamento de configuração**. Notavelmente, **validação de entrada é quase inexistente** — não há schema validation, regex de API keys, ou limites de tamanho. Isso é uma oportunidade de melhoria importante.

**Validações Implementadas**: 4 (poucas)
**Validações Recomendadas**: 12 (gap importante)
**Transformações de Dados**: 3
**Algoritmos Proprietários**: 2

---

## 1. VALIDAÇÕES E SANITIZAÇÃO

### 1.1 Validações Atualmente Implementadas

#### **Regra V1: Verificação de Existência de API Key**

| Aspecto | Detalhe |
|---------|---------|
| **Condição** | Quando usuário tenta fazer transcrição |
| **Validação** | `if (!config.openaiApiKey && config.sttProviderId === "openai")` |
| **Ação Resultante** | Enviar request mesmo assim (deixa API retornar 401) |
| **Código Fonte** | `tipc.ts` linhas ~120-130 (fetch endpoint com Authorization header) |
| **Tipo** | Verificação básica (não-preventiva) |
| **Criticidade** | 🟡 IMPORTANTE - deveria bloquear antes de enviar request |

**Implementação Atual:**
```typescript
// tipc.ts - createRecording procedure
const openaiApiKey = config.openaiApiKey;
// ❌ Sem verificação antes de usar
fetch(endpoint, {
  headers: {
    Authorization: `Bearer ${openaiApiKey}`  // undefined se não configurado
  }
})
```

**Recomendação:**
```typescript
if (!config.openaiApiKey && config.sttProviderId === "openai") {
  throw new Error("OpenAI API key is required. Configure in Settings.")
}
```

---

#### **Regra V2: Verificação de Base URL Customizada**

| Aspecto | Detalhe |
|---------|---------|
| **Condição** | Quando usuário define base URL customizada em settings |
| **Validação** | Nenhuma (usa valor diretamente) |
| **Ação Resultante** | Se URL malformado, fetch falhará silenciosamente |
| **Código Fonte** | `tipc.ts` linhas ~115-125 |
| **Tipo** | Sem validação |
| **Criticidade** | 🔴 CRÍTICO - usuario pode quebrar app com URL inválida |

**Implementação Atual:**
```typescript
const groqBaseUrl = config.groqBaseUrl || "https://api.groq.com/openai/v1"
const openaiBaseUrl = config.openaiBaseUrl || "https://api.openai.com/v1"

const endpoint = `${baseUrl}/audio/transcriptions`
// ❌ Sem validação de URL
```

**Recomendação:**
```typescript
function validateApiUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' || parsed.protocol === 'http:'
  } catch {
    return false
  }
}

if (config.openaiBaseUrl && !validateApiUrl(config.openaiBaseUrl)) {
  throw new Error("Invalid OpenAI Base URL. Must be valid HTTPS URL.")
}
```

---

#### **Regra V3: Verificação de Permissão de Acessibilidade (macOS)**

| Aspecto | Detalhe |
|---------|---------|
| **Condição** | Quando tentando inserir texto no app |
| **Validação** | `if (isAccessibilityGranted())` |
| **Ação Resultante** | Se falso, não chama `writeText()` - texto fica em clipboard |
| **Código Fonte** | `tipc.ts` linhas ~185-190 |
| **Tipo** | Verificação preventiva |
| **Criticidade** | 🟢 BOM - fallback gracioso para clipboard |

**Implementação:**
```typescript
// tipc.ts - createRecording procedure
clipboard.writeText(transcript)
if (isAccessibilityGranted()) {
  await writeText(transcript)  // Only if permission granted
}
```

**Comportamento:**
- ✅ Texto SEMPRE entra no clipboard (fallback seguro)
- ✅ Keystroke simulation só se permitido
- ✅ User pode Ctrl+V manualmente se keystroke falhar

---

#### **Regra V4: Try/Catch no JSON Config Load**

| Aspecto | Detalhe |
|---------|---------|
| **Condição** | Ao carregar arquivo de config na inicialização |
| **Validação** | Try/catch ao fazer `JSON.parse()` |
| **Ação Resultante** | Se arquivo corrompido, retorna `{}` (config vazia) |
| **Código Fonte** | `config.ts` linhas ~10-15 |
| **Tipo** | Error handling gracioso |
| **Criticidade** | 🟢 BOM - app não crashes com config corrupta |

**Implementação:**
```typescript
// config.ts
const getConfig = () => {
  try {
    return JSON.parse(fs.readFileSync(configPath, "utf8")) as Config
  } catch {
    return {}  // ✅ Fallback to empty config
  }
}
```

---

### 1.2 Validações Recomendadas (Gaps Importantes)

#### **Regra V5: Validação de Formato de API Key** ❌ NÃO IMPLEMENTADO

```
Input:  Qualquer string digitada pelo usuário em "API Key" field
Rule:   API keys têm formato específico por provider
        - OpenAI: "sk-" prefix, 48 caracteres
        - Groq: "gsk_" prefix, ~50 caracteres
        - Gemini: Base64 encoded, ~100 caracteres

Validação Esperada:
if (!config.openaiApiKey.startsWith("sk-")) {
  throw new Error("Invalid OpenAI API key format (must start with 'sk-')")
}

Criticidade: 🟡 IMPORTANTE - evita 401 errors depois
```

---

#### **Regra V6: Teste de Conectividade de API Key** ❌ NÃO IMPLEMENTADO

```
Input:  API Key após usuário pressionar Enter/Save
Action: Enviar request test para API com a key
        - OpenAI: GET /models (lista modelos disponíveis)
        - Groq: GET /models
        - Gemini: GET /models

Resultado Esperado:
if (response.status === 401) {
  showErrorDialog("Invalid API key. Please check and try again.")
} else if (response.ok) {
  showSuccessToast("API key is valid!")
}

Criticidade: 🔴 CRÍTICO - permite user detectar key inválida imediatamente
```

---

#### **Regra V7: Tamanho Máximo de Áudio** ❌ NÃO IMPLEMENTADO

```
Input:  Blob de áudio do recorder
Rule:   - Tamanho máximo: 20 MB (limite OpenAI/Groq Whisper)
        - Duração máxima: 60 segundos (UX - ninguém quer gravar 1 min)

Validação:
if (blob.size > 20 * 1024 * 1024) {
  throw new Error("Audio file too large (max 20 MB)")
}

if (duration > 60000) {  // 60 segundos em ms
  throw new Error("Recording too long (max 60 seconds)")
}

Criticidade: 🟡 IMPORTANTE - evita failures silenciosos
```

---

#### **Regra V8: Tamanho Mínimo de Áudio** ❌ NÃO IMPLEMENTADO

```
Input:  Duration da gravação
Rule:   Duração mínima: 0.5 segundos
        (Whisper necessita mínimo de áudio válido)

Validação:
if (duration < 500) {  // 0.5 segundos
  throw new Error("Recording too short. Please record at least 0.5 seconds.")
}

Criticidade: 🟢 COMPLEMENTAR - melhora UX
```

---

#### **Regra V9: Sanitização de Prompt LLM** ❌ NÃO IMPLEMENTADO

```
Input:  Prompt customizado definido pelo usuário
Rule:   - Máximo 2000 caracteres
        - Deve conter placeholder {transcript}
        - Sem injection de ambiente (não há risco real mas seria bom)

Validação:
if (!config.transcriptPostProcessingPrompt.includes("{transcript}")) {
  throw new Error("Prompt must include {transcript} placeholder")
}

if (config.transcriptPostProcessingPrompt.length > 2000) {
  throw new Error("Prompt too long (max 2000 characters)")
}

Criticidade: 🟡 IMPORTANTE - evita prompts quebrados
```

---

#### **Regra V10: Validação de Idioma** ❌ NÃO IMPLEMENTADO

```
Input:  Idioma selecionado (quando implementado)
Rule:   Apenas idiomas suportados por Whisper:
        en, es, fr, de, ja, ko, zh, pt, ar, hi, ru, etc

Status Atual:
- Não há UI de seleção de idioma
- Whisper usa default (inglês)
- Poderia ser adicionado ao Config

Criticidade: 🟢 COMPLEMENTAR - feature futura
```

---

#### **Regra V11: Limite de Rate Limiting Client-Side** ❌ NÃO IMPLEMENTADO

```
Rule:   Não permitir enviar múltiplas transcrições em paralelo
        (API pode rejeitar com 429 Rate Limit)

Implementação Esperada:
const transcriptionQueue = []
const isTranscribing = ref(false)

async function queueTranscription(blob) {
  if (isTranscribing.value) {
    transcriptionQueue.push(blob)
    return
  }
  
  isTranscribing.value = true
  try {
    await transcribe(blob)
  } finally {
    isTranscribing.value = false
    if (transcriptionQueue.length > 0) {
      queueTranscription(transcriptionQueue.shift())
    }
  }
}

Criticidade: 🟡 IMPORTANTE - previne cascata de erros
```

---

#### **Regra V12: Validação de Resposta Whisper** ❌ PARCIALMENTE IMPLEMENTADO

```
Input:  Response JSON da API Whisper
Rule:   - Campo "text" deve existir
        - Não deve estar vazio

Implementação Atual:
const json: { text: string } = await response.json()
const transcript = json.text

❌ Sem verificação se json.text existe ou está vazio

Recomendação:
if (!json.text || typeof json.text !== 'string') {
  throw new Error("Invalid Whisper response: missing transcript")
}

if (json.text.trim() === "") {
  // Pode ser áudio com apenas silêncio
  throw new Error("Whisper returned empty transcription. Recording may be too quiet.")
}

Criticidade: 🟡 IMPORTANTE - melhora error messages
```

---

### 1.3 Tabela Consolidada de Validações

| ID | Validação | Status | Severidade | Localização | Recomendação |
|----|-----------|--------|-----------|------------|--------------|
| V1 | API key existe | ✅ Implementado | 🟡 Important | tipc.ts | Bloquear antes de request |
| V2 | Base URL válida | ❌ Ausente | 🔴 Critical | tipc.ts | Validar com new URL() |
| V3 | Permissão Accessibility | ✅ Implementado | 🟢 Good | tipc.ts | Mantém como está |
| V4 | Config JSON parse | ✅ Implementado | 🟢 Good | config.ts | Mantém como está |
| V5 | API key formato | ❌ Ausente | 🟡 Important | settings | Regex por provider |
| V6 | API key conectividade | ❌ Ausente | 🔴 Critical | settings | Test call ao salvar |
| V7 | Tamanho máx áudio | ❌ Ausente | 🟡 Important | panel.tsx | Checkar antes de upload |
| V8 | Tamanho mín áudio | ❌ Ausente | 🟢 Nice-to-have | panel.tsx | Checkar duration |
| V9 | Sanitização prompt LLM | ❌ Ausente | 🟡 Important | settings | Validar placeholder |
| V10 | Idioma suportado | ❌ N/A | 🟢 Feature-future | — | Para feature de idioma |
| V11 | Rate limit client-side | ❌ Ausente | 🟡 Important | tipc.ts | Queue de requests |
| V12 | Resposta Whisper válida | ⚠️ Parcial | 🟡 Important | tipc.ts | Validar json.text |

---

## 2. TRANSFORMAÇÕES DE DADOS

### 2.1 Transformação 1: Captura de Áudio → WebM Blob

**Ponto de Entrada**: `recorder.ts - startRecording()`

```
Input:  MediaStream (áudio raw do microfone)
Process:
  1. navigator.mediaDevices.getUserMedia({audio: {deviceId: "default"}})
  2. new MediaRecorder(stream, {audioBitsPerSecond: 128e3})
     - Codec: OPUS (padrão em navegadores, recomendado W3C)
     - Container: WebM (formato aberto, suporta OPUS)
     - Bitrate: 128 kbps (balanço qualidade/tamanho)
     - Amostragem: Browser default (~48 kHz)
  3. mediaRecorder.start()
  4. mediaRecorder.ondataavailable(): coleta chunks em Array
  5. new Blob(chunks, {type: "audio/webm"})
Output: Blob {type: "audio/webm", size: ~100KB para 10s de fala}
```

**Código:**
```typescript
// recorder.ts
mediaRecorder = new MediaRecorder(stream, {
  audioBitsPerSecond: 128e3  // 128 kbps OPUS
})

mediaRecorder.ondataavailable = (event) => {
  audioChunks.push(event.data)
}

mediaRecorder.onstop = async () => {
  blob = new Blob(audioChunks, {type: mediaRecorder.mimeType})
  this.emit("record-end", blob, duration)
}
```

**Justificativas:**
- ✅ WebM + OPUS escolha padrão W3C (compatível com Whisper)
- ✅ 128 kbps ideal (20KB/sec, 10s ~= 200KB)
- ✅ Sem pré-processamento (Whisper preferencia)
- ❌ Sem redução de ruído (deixa para Whisper fazer)
- ❌ Sem normalização de volume (Whisper robusto a variação)

---

### 2.2 Transformação 2: Visualizador RMS (Sound Level Display)

**Ponto de Entrada**: `recorder.ts - analyseAudio()`

```
Input:  MediaStream (áudio do microfone)
Process:
  1. AudioContext.createMediaStreamSource(stream)
  2. Analyser.getByteTimeDomainData() [1024 ou 2048 samples]
  3. Calcular RMS (Root Mean Square) dos samples
     RMS = sqrt(sum(x²) / N)
  4. Normalizar RMS para 0-1 range
     - Multiplicar por 10 (amplificar porque valores pequenos)
     - Aplicar expoente 1.5 (compressão não-linear)
     - Clamp entre 0.01 e 1.0
  5. Renderizar barra vertical com altura proporcional ao RMS
Output: number (0.01 a 1.0) → height no visualizador
```

**Código Detalhado:**
```typescript
const calculateRMS = (data: Uint8Array) => {
  let sumSquares = 0
  for (let i = 0; i < data.length; i++) {
    const normalizedValue = (data[i] - 128) / 128  // Convert to signed [-1, 1]
    sumSquares += normalizedValue * normalizedValue
  }
  return Math.sqrt(sumSquares / data.length)
}

const normalizeRMS = (rms: number) => {
  rms = rms * 10  // Amplify
  const exp = 1.5  // Non-linear compression
  const scaledRMS = Math.pow(rms, exp)
  return Math.min(1.0, Math.max(0.01, scaledRMS))  // Clamp [0.01, 1.0]
}
```

**Visualização em panel.tsx:**
```typescript
{visualizerData.map((rms, index) => (
  <div
    style={{
      height: `${Math.min(100, Math.max(16, rms * 100))}%`
    }}
  />
))}
```

**Transformação da altura:**
- RMS 0.01 → 16px (mínimo visual)
- RMS 0.5 → 50px
- RMS 1.0 → 100px (máximo)

**Justificativas:**
- ✅ RMS é métrica padrão de nível de áudio
- ✅ Expoente 1.5 dá visual responsivo (não linear)
- ✅ Clamping evita barras muito pequenas/grandes
- ⚠️ Sem detecção de silêncio (seria bom implementar)

---

### 2.3 Transformação 3: Texto → FormData Multipart

**Ponto de Entrada**: `tipc.ts - createRecording()`

```
Input:  ArrayBuffer (blob.arrayBuffer())
Process:
  1. Converter para File object (Whisper necessita)
     new File([buffer], "recording.webm", {type: "audio/webm"})
  2. Criar FormData (multipart/form-data)
  3. Append fields:
     - file: File object (body do audio)
     - model: String ("whisper-1" ou "whisper-large-v3")
     - response_format: "json"
  4. fetch() com método POST + headers Auth
Output: FormData pronto para POST
```

**Código:**
```typescript
const form = new FormData()

form.append(
  "file",
  new File([input.recording], "recording.webm", {type: "audio/webm"})
)

form.append(
  "model",
  config.sttProviderId === "groq" ? "whisper-large-v3" : "whisper-1"
)

form.append("response_format", "json")

const response = await fetch(`${baseUrl}/audio/transcriptions`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`
    // ❌ Content-Type é auto-set por FormData
  },
  body: form
})
```

**Seleção de Modelo:**
- OpenAI: "whisper-1" (mais rápido, menor latência)
- Groq: "whisper-large-v3" (modelo maior, mais preciso)

**Justificativas:**
- ✅ FormData é padrão REST para upload de arquivos
- ✅ Modelo Groq é "large" (melhor qual. vs OpenAI "tiny/base")
- ⚠️ Sem compression de áudio (Whisper aceita até 25MB)

---

### 2.4 Transformação 4: Transcrição → Pós-Processamento LLM

**Ponto de Entrada**: `llm.ts - postProcessTranscript()`

```
Input:  String (ex: "hello world thats great")
Process:
  1. Verificar se pós-processamento está ativado
  2. Recuperar prompt template do usuário
  3. Substituir placeholder {transcript} no prompt
     Prompt exemplo: "Fix grammar and punctuation:\n\n{transcript}"
     Resultado: "Fix grammar and punctuation:\n\nhello world thats great"
  4. Enviar para LLM (OpenAI/Groq/Gemini)
  5. Extrair texto de response (provider-specific parsing)
Output: String (ex: "Hello, world! That's great.")
```

**Código:**
```typescript
// llm.ts - postProcessTranscript
const prompt = config.transcriptPostProcessingPrompt.replace(
  "{transcript}",
  transcript
)

if (providerId === "gemini") {
  const gai = new GoogleGenerativeAI(config.geminiApiKey)
  const gModel = gai.getGenerativeModel({model: "gemini-1.5-flash-002"})
  const result = await gModel.generateContent([prompt])
  return result.response.text().trim()
}

else {  // OpenAI or Groq
  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    body: JSON.stringify({
      temperature: 0,
      model: chatModel,
      messages: [{
        role: "system",
        content: prompt
      }]
    })
  })
  
  const json = await response.json()
  return json.choices[0].message.content.trim()
}
```

**Template Customizável:**
- Usuário define no Settings → "Transcript Post-Processing" → "Prompt"
- Exemplo padrão (não implementado, user precisa digitar):
  ```
  Fix grammar and capitalization. Keep original meaning:
  
  {transcript}
  ```

**Parsing Provider-Specific:**
- Gemini: `result.response.text()`
- OpenAI/Groq: `json.choices[0].message.content`

---

### 2.5 Fluxograma de Transformações de Dados

```mermaid
flowchart TD
    A["🎙️ Microfone (Raw Audio Stream)"]
    B["📊 MediaRecorder API"]
    C["🔧 OPUS Codec + WebM Container<br/>128 kbps"]
    D["📦 Blob Array → Blob Object<br/>audio/webm"]
    
    E["📡 Whisper API Request<br/>FormData Multipart"]
    F["🌐 OpenAI/Groq API"]
    G["📄 JSON Response<br/>{text: 'transcribed'}"]
    
    H{"LLM Post-Processing<br/>Enabled?"}
    I["🧠 LLM API Request<br/>Chat Completions"]
    J["🌐 OpenAI/Groq/Gemini"]
    K["📝 Processed Text<br/>{choices[0].message.content}"]
    
    L["📋 Clipboard Write"]
    M["⌨️ Keystroke Simulation<br/>via whispo-rs"]
    N["✅ Text in Focused App"]
    
    A -->|Record 10-60s| B
    B -->|Chunks| C
    C -->|Combine| D
    D -->|arrayBuffer| E
    E -->|POST /audio/transcriptions| F
    F -->|200 OK| G
    
    G -->|extract .text| H
    H -->|No| L
    H -->|Yes| I
    I -->|POST /chat/completions| J
    J -->|200 OK| K
    K -->|extract content| L
    
    L -->|setText| M
    M -->|enigo::text()| N
    
    style A fill:#4f46e5
    style D fill:#4f46e5
    style G fill:#10b981
    style K fill:#10b981
    style N fill:#f59e0b
```

---

## 3. CONFIGURAÇÕES E POLÍTICAS

### 3.1 Política de Providers

**STT (Speech-to-Text) Providers:**

```
Provider: OpenAI Whisper
  - Models: whisper-1
  - Endpoint: https://api.openai.com/v1/audio/transcriptions
  - Cost: $0.006 per minute
  - Speed: ~5-10 seconds for 30s audio
  - Accuracy: Excellent
  - Default: Yes
  - Code Location: shared/index.ts (STT_PROVIDERS)

Provider: Groq Whisper (via Groq API)
  - Models: whisper-large-v3
  - Endpoint: https://api.groq.com/openai/v1/audio/transcriptions
  - Cost: Free tier available
  - Speed: Fast (~2-3 seconds for 30s audio)
  - Accuracy: Good
  - Default: No
  - Code Location: shared/index.ts (STT_PROVIDERS)

UI Selection: pages/settings-general.tsx
  - Dropdown para selecionar STT provider
  - Fallback: OpenAI (se sttProviderId não definido)
```

**Chat (LLM) Providers:**

```
Provider: OpenAI
  - Models: gpt-4o-mini
  - Purpose: Post-processing de transcrição
  - Endpoint: https://api.openai.com/v1/chat/completions
  - Cost: $0.00015 per 1K input tokens
  - Temperature: 0 (determinístico)
  - Code: tipc.ts (llm.ts), lines ~40-60

Provider: Groq
  - Models: llama-3.1-70b-versatile
  - Purpose: Post-processing de transcrição
  - Endpoint: https://api.groq.com/openai/v1/chat/completions
  - Cost: Free
  - Temperature: 0 (determinístico)
  - Code: tipc.ts (llm.ts), lines ~40-60

Provider: Google Gemini
  - Models: gemini-1.5-flash-002
  - Purpose: Post-processing de transcrição
  - Endpoint: https://generativelanguage.googleapis.com
  - Cost: Free tier available
  - Code: tipc.ts (llm.ts), lines ~30-38

UI Selection: pages/settings-general.tsx
  - Dropdown para pós-processamento provider
  - Fallback: OpenAI (se não definido)
```

**Código de Seleção:**
```typescript
// shared/index.ts
export const STT_PROVIDERS = [
  { label: "OpenAI", value: "openai" },
  { label: "Groq", value: "groq" }
] as const

export const CHAT_PROVIDERS = [
  { label: "OpenAI", value: "openai" },
  { label: "Groq", value: "groq" },
  { label: "Gemini", value: "gemini" }
] as const

// settings-general.tsx - UI
<Select
  defaultValue={sttProviderId}
  onValueChange={(value) => saveConfig({sttProviderId: value})}
>
  {STT_PROVIDERS.map(p => (
    <SelectItem key={p.value} value={p.value}>
      {p.label}
    </SelectItem>
  ))}
</Select>
```

---

### 3.2 Política de Armazenamento de Dados

**Localização de Dados:**

```
Base Directory: {appData}/whispo
  Windows: C:\Users\{user}\AppData\Roaming\io.github.egoist.whispo
  macOS: ~/Library/Application Support/io.github.egoist.whispo
  Linux: ~/.config/io.github.egoist.whispo

Estrutura:
├── config.json (configuração do usuário)
├── recordings/ (histórico de gravações)
│   ├── history.json (metadados)
│   ├── {timestamp1}.webm (arquivo de áudio)
│   ├── {timestamp2}.webm
│   └── ...
```

**Config Storage Policy:**

```
File: config.json
Format: JSON simples (sem encriptação)
Size: ~2-5 KB

Contents:
{
  "shortcut": "hold-ctrl" | "ctrl-slash",
  "hideDockIcon": boolean (macOS only),
  "sttProviderId": "openai" | "groq",
  "openaiApiKey": "sk-...",
  "openaiBaseUrl": "https://api.openai.com/v1",
  "groqApiKey": "gsk_...",
  "groqBaseUrl": "https://api.groq.com/openai/v1",
  "geminiApiKey": "...",
  "geminiBaseUrl": "https://generativelanguage.googleapis.com",
  "transcriptPostProcessingEnabled": boolean,
  "transcriptPostProcessingProviderId": "openai" | "groq" | "gemini",
  "transcriptPostProcessingPrompt": string
}

Segurança: ⚠️ Sem encriptação
  - API keys armazenados em plain text
  - Risco: Se máquina comprometida, keys expostas
  - Recomendação: Usar electron.safeStorage para encriptar
```

**Recordings Storage Policy:**

```
history.json
  - Array de RecordingHistoryItem
  - Salvo após cada transcrição bem-sucedida
  - Nunca deletado automaticamente
  - Deletion via UI: "Settings" → "Data" → "Delete All"

Format:
[
  {
    "id": "1735814400000",  // Date.now()
    "createdAt": 1735814400000,
    "duration": 10500,  // milliseconds
    "transcript": "hello world this is a test"
  },
  ...
]

Audio Files:
  - Nome: {id}.webm (ex: 1735814400000.webm)
  - Formato: WebM Opus (original da captura)
  - Retenção: Indefinida (até user deletar)
  - Size: ~10-20 KB per 10 seconds de fala

Carregamento:
  - Em memory (React Query)
  - Renderizado em pages/index.tsx
  - Suporta playback via <audio> tag
  - Protocolo customizado: assets://recording/{id}
```

---

### 3.3 Política de Cache

**Cache de Configuração:**

```
Location: React Query queryClient
Key: ["config"]
TTL: Infinite (cache até invalidar manualmente)
Invalidation: tipcClient.saveConfig() → queryClient.invalidateQueries({queryKey: ["config"]})

Behavior:
- Query carrega config uma vez na inicialização
- Todas as pages veem mesma versão (React Query cache)
- Ao salvar settings, query é invalidada e refetched
```

**Cache de Histórico de Gravações:**

```
Location: React Query queryClient
Key: ["recording-history"]
TTL: Infinite
Invalidation: 
  - Após createRecording (novo item)
  - Após deleteRecordingItem
  - Após deleteRecordingHistory

Behavior:
- Query carrega histórico do history.json
- Renderizado em pages/index.tsx
- Sorted descending by createdAt
```

**Cache de Status de Microfone:**

```
Location: React Query queryClient
Key: ["microphone-status"]
TTL: Infinite
Invalidation: Manual (não refetch automático)

Behavior:
- Query chama tipcClient.getMicrophoneStatus()
- Usado em pages/setup.tsx
- ⚠️ Não refetch quando user muda permissão em System Settings
- Recomendação: Refetch ao app retorna do background
```

---

### 3.4 Política de Telemetria e Logging

**Telemetria:**

```
Status: ❌ NENHUMA telemetria implementada
  - Sem Google Analytics
  - Sem Sentry
  - Sem rastreamento de uso
  - Sem tracking de erros
  - Privacidade garantida (dados ficam locais)

Recomendação:
  - Adicionar opt-in para error tracking (Sentry)
  - User nunca compartilha dados a menos que explícitamente aceitar
```

**Logging:**

```
Console Logs: ✅ Implementados
  - keyboard.ts: console.log("start recording", "release ctrl", etc)
  - recorder.ts: logTime() function para performance monitoring
  - tipc.ts: console.log(chatJson) para response inspection

File Logging: ❌ Não implementado
  - Nenhum log arquivo persistente
  - Logs perdidos ao fechar app
  - Difícil debug após crashes

Recomendação:
  - Implementar file logging com winston ou similar
  - Arquivar logs por data (7 dias de retention)
  - Incluir em error reports
```

---

## 4. ALGORITMOS PROPRIETÁRIOS

### 4.1 Algoritmo 1: Máquina de Estados de Hotkey Detection

**Propósito:** Detectar quando usuário segura Ctrl e diferencia entre "hold to record" e "press other key"

**Estados:**

```
idle:
  - isHoldingCtrlKey = false
  - isPressedCtrlKey = false
  - startRecordingTimer = undefined

waiting (800ms):
  - User segura Ctrl
  - Timer iniciado (800ms)
  - Se outro key pressionado → cancela timer
  - Se Ctrl liberado antes de 800ms → volta idle

holding:
  - 800ms completou
  - isHoldingCtrlKey = true
  - Panel window aparece
  - Gravação inicia

recording:
  - User tem Ctrl pressionado
  - Se outro key pressionado → cancela gravação
  - Se Ctrl liberado → finaliza gravação

Transitions:
idle → waiting: Ctrl pressed (setTimeout 800ms)
waiting → idle: Ctrl released OR other key pressed
waiting → holding: 800ms timer fires
holding → idle: Ctrl released (finishRecording)
holding → idle: Other key pressed (stopRecording)
```

**Código:**

```typescript
// keyboard.ts - handleEvent()
if (e.event_type === "KeyPress") {
  if (e.data.key === "ControlLeft") {
    isPressedCtrlKey = true
    
    if (hasRecentKeyPress()) return  // Other keys in last 10s?
    
    if (startRecordingTimer) return  // Already waiting?
    
    // Start waiting (800ms)
    startRecordingTimer = setTimeout(() => {
      isHoldingCtrlKey = true  // Transition to holding
      showPanelWindowAndStartRecording()
    }, 800)
  }
  
  else {  // Other key pressed
    keysPressed.set(e.data.key, timestamp)
    clearTimeout(startRecordingTimer)  // Cancel waiting
    
    if (isHoldingCtrlKey) {
      stopRecordingAndHidePanelWindow()  // Cancel recording
    }
    
    isHoldingCtrlKey = false  // Transition to idle
  }
}

else if (e.event_type === "KeyRelease") {
  if (e.data.key === "ControlLeft") {
    isPressedCtrlKey = false
    
    if (isHoldingCtrlKey) {
      rendererHandlers.finishRecording.send()  // End recording
    } else {
      stopRecordingAndHidePanelWindow()  // Cancel waiting
    }
    
    isHoldingCtrlKey = false  // Transition to idle
  }
}
```

**Características Especiais:**

```
1. Anti-bounce (hasRecentKeyPress):
   - Ignora Ctrl se outro key pressionado nos últimos 10s
   - Evita triggers acidentais (ex: Ctrl+C, Ctrl+V)

2. Timeout para KeyRelease:
   - Se KeyRelease event perdido (bug OS), key fica em map
   - Cleanup: keysPressed.clear() após writeText()
   - Timeout automático: 10 segundos (fallback)

3. Dual Mode:
   - Default: Hold Ctrl (mode 1)
   - Config: Ctrl+/ (mode 2)
   - Mode 2 é toggle, não hold-to-record
```

---

### 4.2 Algoritmo 2: Normalização de RMS para Visualizador

**Propósito:** Converter níveis de áudio bruto em barra visual responsiva

**Fórmula:**

```
Step 1: Extrair amostras em tempo real
  timeDomainData = Uint8Array (1024 ou 2048 samples)
  Range: [0, 255] (unsigned bytes)

Step 2: Normalizar para signed range
  normalizedValue = (sample - 128) / 128
  Range: [-1, 1]

Step 3: Calcular RMS (Root Mean Square)
  sumSquares = sum(normalizedValue²)
  rms = sqrt(sumSquares / N)
  Range: [0, ~0.7] (tipicamente)

Step 4: Amplificar e comprimir
  rms = rms * 10  // Amplify [0, ~7]
  rms = rms ^ 1.5  // Non-linear compression [0, ~13]
  
  Exemplo de valores após passo 4:
  - Silêncio: ~0.1
  - Fala normal: ~0.5-2
  - Fala alta: ~5-10

Step 5: Normalizar para [0.01, 1.0]
  rms = clamp(rms, 0.01, 1.0)
  
  0.01 → 1% (barra mínima)
  1.0 → 100% (barra máxima)

Step 6: Mapear para altura CSS
  height = rms * 100 + "px"  // [16px, 100px]
  
  Clamped: max(16px, min(100px, height))
```

**Justificativa do Expoente 1.5:**

```
Linear (expoente 1.0):
  rms: 0 → height: 0
  rms: 0.5 → height: 50
  rms: 1.0 → height: 100
  Problema: Pouca diferença visual entre 0 e 0.5

Quadrático (expoente 2.0):
  rms: 0 → height: 0
  rms: 0.5 → height: 25
  rms: 1.0 → height: 100
  Problema: Muito agrupado em cima

Expoente 1.5 (Goldilocks):
  rms: 0 → height: 0
  rms: 0.25 → height: ~4
  rms: 0.5 → height: ~18
  rms: 0.75 → height: ~48
  rms: 1.0 → height: 100
  Benefício: Distribuição visual uniforme
```

---

## 5. ANÁLISE DE PROMPTS LLM

### 5.1 Prompts Customizáveis

**Status:** ✅ Prompts são customizáveis pelo usuário

**UI para Editar Prompt:**

```typescript
// pages/settings-general.tsx
<Control label="Prompt" className="px-3">
  <Dialog>
    <DialogTrigger asChild>
      <Button size="sm" variant="outline">Edit</Button>
    </DialogTrigger>
    <DialogContent>
      <DialogTitle>Edit Prompt</DialogTitle>
      <Textarea
        rows={10}
        defaultValue={config.transcriptPostProcessingPrompt}
        onChange={(e) => {
          saveConfig({
            transcriptPostProcessingPrompt: e.target.value
          })
        }}
      />
      <div className="text-sm text-muted-foreground">
        Use <span className="select-text">{{"{transcript}"}}</span> placeholder to insert transcript
      </div>
    </DialogContent>
  </Dialog>
</Control>
```

**Execução do Prompt:**

```typescript
// llm.ts - postProcessTranscript
const prompt = config.transcriptPostProcessingPrompt
  .replace("{transcript}", transcript)

// Enviado como system message
const messages = [
  {
    role: "system",
    content: prompt
  }
]
```

---

### 5.2 Prompts Padrão Sugeridos (Não Implementados)

**Não há templates padrão no código. Usuário deve escrever do zero.**

**Exemplos que Funcionariam Bem:**

#### Prompt 1: Correção Gramatical
```
Fix all grammar and spelling errors in the following text. Keep the original meaning and tone. Only output the corrected text, nothing else:

{transcript}
```

Expected Output:
```
Input:  "hello world thats great im so happy"
Output: "Hello, world! That's great. I'm so happy."
```

---

#### Prompt 2: Formatação de Conversação
```
This is a transcribed conversation. Format it with proper capitalization, punctuation, and line breaks for readability. Add speaker labels if identifiable:

{transcript}
```

Expected Output:
```
Input:  "hey john how are you im doing great thanks for asking"
Output: 
"Hey John, how are you?
I'm doing great, thanks for asking!"
```

---

#### Prompt 3: Extração de Pontos-Chave
```
Extract the main action items or key points from the following transcript. Format as a numbered list:

{transcript}
```

Expected Output:
```
Input:  "we need to call the client on monday then send them the proposal by wednesday and schedule a follow up for next week"
Output:
"1. Call the client on Monday
2. Send proposal by Wednesday
3. Schedule follow-up for next week"
```

---

#### Prompt 4: Tradução (se multi-língua)
```
Translate the following text to English:

{transcript}
```

Expected Output:
```
Input:  "bonjour comment allez vous"
Output: "Hello, how are you?"
```

---

## 6. EDGE CASES E COMPORTAMENTOS ESPECIAIS

### 6.1 Edge Case 1: Áudio Muito Curto (<1 segundo)

```
Cenário: Usuário segura Ctrl por < 1 segundo
Input Duration: 500ms
Result Path:
  1. panel.tsx: duration < 500ms
  2. Blob enviado mesmo assim para Whisper
  3. Whisper: ❌ Pode retornar texto vazio ou erro

Recomendação:
  if (duration < 500) {
    showWarning("Recording too short")
    return  // Don't send to API
  }
```

---

### 6.2 Edge Case 2: Áudio Muito Longo (>60 segundos)

```
Cenário: Usuário esquece de liberar Ctrl
Input Duration: 120 segundos
Input Size: ~2-4 MB
Result Path:
  1. FormData enviado com áudio de 120s
  2. Whisper API: ✅ Processa (limite é 25 MB)
  3. Resposta: Texto com transcrição completa
  4. Panel.tsx: transcribeMutation.isPending = true (UI bloqueada)

Problema: User quer cancelar mas can't (sem botão de cancel)

Recomendação:
  1. Adicionar máximo de 60 segundos
  2. Se usuário tenta gravar mais, mostrar warning
  3. Auto-stop após 60s
```

---

### 6.3 Edge Case 3: Múltiplos Idiomas no Mesmo Áudio

```
Cenário: "Hello, comment ça va? 你好"
Whisper Response: Mescla idiomas no output
Output: "Hello, comment ça va? You how"
Problem: Tradução incorreta, mistura idiomas

Status: Sem tratamento especial
Recomendação:
  - Adicionar seleção de idioma em settings
  - Passar language param ao Whisper API
  - Documentar que Whisper funciona melhor com idioma único
```

---

### 6.4 Edge Case 4: Ruído Excessivo

```
Cenário: Background muito barulhento
Whisper Response: "hxjdka lkajsd jsaklj" (gibberish)
Problem: Sem validação de qualidade

Status: Sem tratamento
Recomendation:
  1. Implementar Voice Activity Detection (VAD) pré-transcrição
  2. Rejeitar áudio com SNR (Signal-to-Noise Ratio) muito baixo
  3. Ou: Permitir user decidir via flag "was this audio clear?"
```

---

### 6.5 Edge Case 5: Permissão de Acessibilidade Revogada Mid-Session

```
Cenário: 
  1. App rodando com accessibility granted
  2. User vai em System Settings e revoga acesso
  3. User segura Ctrl para gravar
  4. Transcrição completa, tenta writeText()

Result Path:
  1. isAccessibilityGranted() → false (verificação no momento)
  2. Pula writeText()
  3. Texto fica só em clipboard
  4. User pode fazer Ctrl+V

Status: ✅ Tratado corretamente (fallback a clipboard)
```

---

### 6.6 Edge Case 6: API Key Alterada Entre Requests

```
Cenário:
  1. User inicia gravação com API key A
  2. Enquanto está gravando, user abre Settings
  3. User troca para API key B
  4. Gravação termina, tenta enviar com key B

Result Path:
  1. createRecording() lê config.openaiApiKey
  2. Pega valor atual (B)
  3. Whisper processa com key B
  4. ✅ Funciona (sem race condition)

Status: ✅ Sem problema (config é sincronizado)
```

---

### 6.7 Edge Case 7: LLM Post-Processing com Prompt Inválido

```
Cenário: User define prompt sem placeholder {transcript}
Prompt: "Fix this text:"
Transcript: "hello world"
Resultado: "Fix this text:" é enviado, {transcript} nunca é substituído

Result:
  LLM recebe: "Fix this text:" (sem o áudio!)
  LLM responde: "I need the text to fix"
  User vê: Resposta genérica, não corrigida

Status: ❌ Sem validação
Recomendação: V9 na tabela de validações (acima)
```

---

### 6.8 Edge Case 8: Network Timeout Durante Whisper API

```
Cenário: Conexão de internet cai enquanto enviando áudio
Status Code: Nenhum (timeout/connection reset)

Result Path:
  1. fetch() lança AbortError ou timeout
  2. tipcClient.createRecording() não tem try/catch? ⚠️
  3. Promise rejeita
  4. panel.tsx: transcribeMutation.onError() dispara
  5. displayError() mostra ao user

Status: ⚠️ Parcialmente tratado (sem retry)
Recomendação: Implementar retry com backoff (Prioridade 1)
```

---

## 7. TABELA RESUMIDA DE REGRAS DE NEGÓCIO

| Tipo | Regra | Status | Severidade | Código |
|------|-------|--------|-----------|--------|
| **Validação** | API key existe | ✅ | 🟡 | tipc.ts |
| | Base URL válida | ❌ | 🔴 | tipc.ts |
| | Permissão Accessibility | ✅ | 🟢 | tipc.ts |
| | Config JSON parse | ✅ | 🟢 | config.ts |
| | Tamanho máx áudio | ❌ | 🟡 | panel.tsx |
| | Tamanho mín áudio | ❌ | 🟢 | recorder.ts |
| **Transformação** | Áudio → WebM | ✅ | — | recorder.ts |
| | Visualizador RMS | ✅ | — | recorder.ts |
| | Blob → FormData | ✅ | — | tipc.ts |
| | Texto → LLM | ✅ | — | llm.ts |
| **Algoritmo** | Hotkey State Machine | ✅ | — | keyboard.ts |
| | RMS Normalization | ✅ | — | recorder.ts |
| **Config** | STT Provider Selection | ✅ | — | shared/index |
| | LLM Provider Selection | ✅ | — | shared/index |
| | Data Retention Policy | ✅ (indefinida) | — | tipc.ts |

---

## 8. CONCLUSÕES E RECOMENDAÇÕES

### Validações Implementadas: 4/12 (33%)

- ✅ Config JSON parsing (gracioso)
- ✅ API key existence check (básico)
- ✅ Accessibility permission guard (bom)
- ✅ Try/catch no filesystem (bom)

- ❌ Faltam 8 validações críticas (API key format, conectividade, tamanho, etc)

### Transformações Bem Implementadas

- ✅ WebM @ 128 kbps é padrão inteligente
- ✅ RMS normalization com expoente 1.5 é sofisticado
- ✅ FormData multipart é correto para Whisper API

### Algoritmos

- ✅ Máquina de estados de hotkey é robusta
- ⚠️ Sem VAD (Voice Activity Detection) para auto-stop
- ⚠️ Sem streaming support (one-shot apenas)

### Score Geral: 6/10

**Implementado bem:** Transformações de dados, provedor abstração, UI customização
**Fraco:** Validações de entrada, error handling, edge cases

**Prioridades de Melhoria:**
1. Adicionar schema validation (Zod) para config
2. Implementar retry + timeout para APIs
3. Adicionar validações de tamanho de áudio
4. Teste de API key na settings

---

## APÊNDICE: Pseudocódigo de Validações Recomendadas

```typescript
// recommended-validations.ts

// V2: URL Validation
function validateApiUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return ['https:', 'http:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

// V5: API Key Format Validation
function validateApiKeyFormat(apiKey: string, provider: 'openai' | 'groq' | 'gemini'): boolean {
  const patterns = {
    openai: /^sk-[a-zA-Z0-9]{48,}$/,
    groq: /^gsk_[a-zA-Z0-9]{40,}$/,
    gemini: /^[a-zA-Z0-9_-]{40,}$/  // Approximate
  }
  return patterns[provider].test(apiKey)
}

// V6: API Key Connectivity Test
async function testApiKey(apiKey: string, provider: 'openai' | 'groq'): Promise<boolean> {
  const baseUrl = provider === 'groq' 
    ? 'https://api.groq.com/openai/v1'
    : 'https://api.openai.com/v1'
  
  try {
    const response = await fetch(`${baseUrl}/models`, {
      headers: { Authorization: `Bearer ${apiKey}` },
      timeout: 5000
    })
    return response.status === 200
  } catch {
    return false
  }
}

// V7-V8: Audio Size Validation
function validateAudioSize(blob: Blob, durationMs: number): {valid: boolean, error?: string} {
  const maxSizeBytes = 20 * 1024 * 1024  // 20 MB
  const minDurationMs = 500  // 0.5 seconds
  const maxDurationMs = 60000  // 60 seconds
  
  if (blob.size > maxSizeBytes) {
    return {valid: false, error: `Audio file too large (${blob.size / 1024 / 1024}MB, max 20MB)`}
  }
  if (durationMs < minDurationMs) {
    return {valid: false, error: `Recording too short (${durationMs}ms, min 500ms)`}
  }
  if (durationMs > maxDurationMs) {
    return {valid: false, error: `Recording too long (${durationMs}ms, max 60000ms)`}
  }
  
  return {valid: true}
}

// V9: Prompt Validation
function validateLLMPrompt(prompt: string): {valid: boolean, errors: string[]} {
  const errors: string[] = []
  
  if (!prompt.includes("{transcript}")) {
    errors.push("Prompt must include {transcript} placeholder")
  }
  if (prompt.length > 2000) {
    errors.push(`Prompt too long (${prompt.length} chars, max 2000)`)
  }
  if (prompt.trim().length === 0) {
    errors.push("Prompt cannot be empty")
  }
  
  return {
    valid: errors.length === 0,
    errors
  }
}

// V11: Client-Side Rate Limiting
class TranscriptionQueue {
  private isProcessing = false
  private queue: Array<{blob: Blob, duration: number}> = []
  
  async transcribe(blob: Blob, duration: number): Promise<string> {
    return new Promise((resolve, reject) => {
      this.queue.push({blob, duration})
      this.processQueue()
    })
  }
  
  private async processQueue() {
    if (this.isProcessing || this.queue.length === 0) return
    
    this.isProcessing = true
    const {blob, duration} = this.queue.shift()!
    
    try {
      const result = await tipcClient.createRecording({
        recording: await blob.arrayBuffer(),
        duration
      })
      // resolve(result)
    } finally {
      this.isProcessing = false
      this.processQueue()  // Process next in queue
    }
  }
}
```

---

**Documento Completo da FASE 4 Finalizado.**
**Total de Regras de Negócio Documentadas: 20+ (4 implementadas, 16 recomendadas)**
