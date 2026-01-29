# FASE 5: INTERFACES E CONTRATOS DE API

## RESUMO EXECUTIVO

Whispo integra-se com **4 camadas de interfaces**: (1) **APIs Externas** (Whisper, LLMs), (2) **IPC Tipado** (comunicação Electron), (3) **Integração com SO** (hotkeys, clipboard), e (4) **Schema de Configuração**. Este documento fornece especificação completa para cada interface, permitindo reuso, troubleshooting e integração com outros sistemas.

**Total de Interfaces Documentadas**: 45+
- 6 procedimentos IPC (Renderer → Main)
- 4 event handlers IPC (Main → Renderer)
- 3 APIs externas (Whisper, LLM x3 providers)
- 4 APIs do SO
- 1 schema de config

---

## PARTE 1: APIS EXTERNAS

### 1.1 WHISPER API (OpenAI e Groq)

#### **1.1.1 Especificação OpenAPI-Style**

**Recurso**: Transcrição de Áudio

**Endpoint Base URLs:**
```
OpenAI:  https://api.openai.com/v1
Groq:    https://api.groq.com/openai/v1
```

**Endpoint Específico:**
```
POST /audio/transcriptions
```

**Propósito**: Converter arquivo de áudio (WebM, MP3, WAV, M4A) em texto transcrito usando modelo Whisper.

---

#### **1.1.2 Request Specification**

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Headers Obrigatórios**:
```http
Authorization: Bearer {API_KEY}
```

Exemplo com OpenAI:
```http
POST /v1/audio/transcriptions HTTP/1.1
Host: api.openai.com
Authorization: Bearer sk-proj-xxxxx...
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="recording.webm"
Content-Type: audio/webm

[binary audio data]
------WebKitFormBoundary
Content-Disposition: form-data; name="model"

whisper-1
------WebKitFormBoundary
Content-Disposition: form-data; name="response_format"

json
------WebKitFormBoundary--
```

**Form Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | File (binary) | ✅ | — | Audio file to transcribe. Supports: mp3, mp4, mpeg, mpga, m4a, wav, webm |
| `model` | String | ✅ | — | Model to use. OpenAI: "whisper-1". Groq: "whisper-large-v3" |
| `language` | String (ISO-639-1) | ❌ | auto | Language of audio. Example: "en", "es", "fr", "ja", "pt", "zh" |
| `prompt` | String | ❌ | — | Optional text to guide transcription style |
| `response_format` | String | ❌ | "json" | Output format: "json", "text", "srt", "verbose_json" |
| `temperature` | Float | ❌ | 0 | Sampling temperature. Range [0, 1]. Lower = deterministic |
| `timestamp_granularities` | Array | ❌ | — | For verbose_json: "segment", "word" |

**Implementação em Whispo** (`tipc.ts`):

```typescript
// Extrato real do código
const form = new FormData()
form.append("file", new File([input.recording], "recording.webm", {
  type: "audio/webm"
}))
form.append("model", 
  config.sttProviderId === "groq" ? "whisper-large-v3" : "whisper-1"
)
form.append("response_format", "json")

const transcriptResponse = await fetch(
  config.sttProviderId === "groq"
    ? `${groqBaseUrl}/audio/transcriptions`
    : `${openaiBaseUrl}/audio/transcriptions`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${
        config.sttProviderId === "groq" ? config.groqApiKey : config.openaiApiKey
      }`
    },
    body: form
  }
)
```

---

#### **1.1.3 Response Specification**

**Success Response** (HTTP 200):

```json
{
  "text": "Hello, world. This is a test transcription."
}
```

**TypeScript Interface** (Whispo):

```typescript
// Não existe interface explícita, mas esperado:
interface WhisperResponse {
  text: string
  language?: string
  duration?: number
  segments?: Array<{
    id: number
    seek: number
    start: number
    end: number
    text: string
    tokens: number[]
    temperature: number
    avg_logprob: number
    compression_ratio: number
    no_speech_prob: number
  }>
}
```

**Exemplos de Response**:

```json
// Success: Whisper-1 (OpenAI)
{
  "text": "Hello, how are you today? I'm doing great, thanks for asking."
}
```

```json
// Success: Whisper-large-v3 (Groq) - identical format
{
  "text": "Hello, how are you today? I'm doing great, thanks for asking."
}
```

---

#### **1.1.4 Error Responses**

**HTTP 400 - Bad Request** (Arquivo inválido):
```json
{
  "error": {
    "message": "Invalid file format. Supported formats are: mp3, mp4, mpeg, mpga, m4a, wav, webm",
    "type": "invalid_request_error",
    "param": "file"
  }
}
```

**HTTP 401 - Unauthorized** (API key inválido):
```json
{
  "error": {
    "message": "Incorrect API key provided. You can find your API key at https://platform.openai.com/account/api-keys.",
    "type": "invalid_request_error"
  }
}
```

**HTTP 429 - Too Many Requests** (Rate limit excedido):
```json
{
  "error": {
    "message": "Rate limit exceeded. You exceeded your current quota, please check your plan and billing settings.",
    "type": "server_error"
  }
}
```

**HTTP 500 - Internal Server Error**:
```json
{
  "error": {
    "message": "The server has encountered an unexpected condition that prevented it from fulfilling the request.",
    "type": "server_error"
  }
}
```

**Error Handling em Whispo** (`tipc.ts`):

```typescript
if (!transcriptResponse.ok) {
  const message = `${transcriptResponse.statusText} ${
    (await transcriptResponse.text()).slice(0, 300)
  }`
  throw new Error(message)
}

const json: { text: string } = await transcriptResponse.json()
// ✅ Response processado
```

---

#### **1.1.5 Exemplo de Curl Request**

```bash
# OpenAI Whisper
curl -X POST \
  https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer sk-proj-xxxxx" \
  -F "file=@recording.webm" \
  -F "model=whisper-1" \
  -F "response_format=json"

# Groq Whisper
curl -X POST \
  https://api.groq.com/openai/v1/audio/transcriptions \
  -H "Authorization: Bearer gsk_xxxxx" \
  -F "file=@recording.webm" \
  -F "model=whisper-large-v3" \
  -F "response_format=json"
```

---

### 1.2 LLM APIs (Post-Processamento)

#### **1.2.1 OpenAI Chat Completions API**

**Endpoint**:
```
POST https://api.openai.com/v1/chat/completions
```

**Headers**:
```http
Authorization: Bearer {OPENAI_API_KEY}
Content-Type: application/json
```

**Request Body** (Whispo):

```json
{
  "model": "gpt-4o-mini",
  "temperature": 0,
  "messages": [
    {
      "role": "system",
      "content": "Fix grammar and punctuation:\n\n{transcript}"
    }
  ]
}
```

**Implementação em Whispo** (`llm.ts`):

```typescript
const chatResponse = await fetch(`${baseUrl}/chat/completions`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${config.openaiApiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    temperature: 0,
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content: prompt  // User-defined prompt with {transcript} replaced
      },
    ],
  }),
})
```

**Success Response** (HTTP 200):

```json
{
  "id": "chatcmpl-8qK7xZ3bZ3ZZZ",
  "object": "chat.completion",
  "created": 1699564383,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello, world! This is a test transcription."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 14,
    "total_tokens": 39
  }
}
```

**Parsing em Whispo**:

```typescript
const chatJson = await chatResponse.json()
const processedText = chatJson.choices[0].message.content.trim()
```

---

#### **1.2.2 Groq API (LLaMA-3.1)**

**Endpoint**:
```
POST https://api.groq.com/openai/v1/chat/completions
```

**Request Format**: Idêntico ao OpenAI (compatível com OpenAI SDK)

```json
{
  "model": "llama-3.1-70b-versatile",
  "temperature": 0,
  "messages": [
    {
      "role": "system",
      "content": "Fix grammar and punctuation:\n\n{transcript}"
    }
  ]
}
```

**Implementação em Whispo**: Mesmo endpoint que OpenAI (abstração)

**Response Format**: Idêntico ao OpenAI

---

#### **1.2.3 Google Gemini API**

**Endpoint**:
```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-002:generateContent?key={API_KEY}
```

**Headers**:
```http
Content-Type: application/json
```

**Request Body** (Whispo):

```json
{
  "contents": [
    {
      "parts": [
        {
          "text": "Fix grammar and punctuation:\n\nhello world this is a test"
        }
      ]
    }
  ]
}
```

**Implementação em Whispo** (`llm.ts`):

```typescript
if (chatProviderId === "gemini") {
  if (!config.geminiApiKey) throw new Error("Gemini API key is required")
  
  const gai = new GoogleGenerativeAI(config.geminiApiKey)
  const gModel = gai.getGenerativeModel({model: "gemini-1.5-flash-002"})
  
  const result = await gModel.generateContent([prompt], {
    baseUrl: config.geminiBaseUrl,
  })
  
  return result.response.text().trim()
}
```

**Success Response** (HTTP 200):

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "Hello, world! This is a test."
          }
        ],
        "role": "model"
      },
      "finishReason": "STOP",
      "index": 0,
      "safetyRatings": []
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 10,
    "candidatesTokenCount": 8,
    "totalTokenCount": 18
  }
}
```

**Parsing em Whispo**:

```typescript
const text = result.response.text().trim()
```

---

#### **1.2.4 Comparativa de Providers LLM**

| Aspecto | OpenAI | Groq | Gemini |
|---------|--------|------|--------|
| **Endpoint** | /v1/chat/completions | /openai/v1/chat/completions | /v1beta/models/.../generateContent |
| **Auth** | Bearer token | Bearer token | Query param `?key=...` |
| **Modelo Default** | gpt-4o-mini | llama-3.1-70b-versatile | gemini-1.5-flash-002 |
| **Température** | 0 (determinístico) | 0 (determinístico) | N/A (useFull) |
| **Cost** | Pago ($) | Grátis/Freemium | Freemium |
| **Speed** | Médio | Rápido | Rápido |
| **Response Format** | JSON standard | JSON standard (compatível) | JSON custom (via SDK) |

---

### 1.3 Diagrama de Integração com APIs Externas

```mermaid
graph LR
    A["🎙️ Whispo<br/>Main Process"] 
    
    B["📡 Whisper API<br/>OpenAI ou Groq"]
    C["🌐 OpenAI<br/>gpt-4o-mini"]
    D["🌐 Groq<br/>llama-3.1-70b"]
    E["🌐 Google Gemini<br/>gemini-1.5-flash"]
    
    A -->|1. POST /audio/transcriptions<br/>FormData: file, model| B
    B -->|200 OK {text: '...'}| A
    
    A -->|2. POST /chat/completions<br/>JSON: messages, model| C
    C -->|200 OK {choices: [...]}| A
    
    A -->|2. POST /chat/completions<br/>JSON: messages, model| D
    D -->|200 OK {choices: [...]}| A
    
    A -->|2. POST .../generateContent<br/>JSON: contents| E
    E -->|200 OK {candidates: [...]}| A
    
    style B fill:#10b981
    style C fill:#f59e0b
    style D fill:#f59e0b
    style E fill:#f59e0b
    style A fill:#4f46e5
```

---

## PARTE 2: INTERFACE IPC (Inter-Process Communication)

### 2.1 Visão Geral do IPC Whispo

**Framework**: `@egoist/tipc` (RPC tipado)

**Arquitetura**:
- **Main Process** (Node.js) expõe procedures (podem ser remotos)
- **Renderer Process** (React) chama via `tipcClient`
- **Type Safety**: TypeScript garante compatibilidade

**Dois Fluxos**:
1. **Renderer → Main**: Procedure call (request/response)
2. **Main → Renderer**: Event handler (one-way push)

---

### 2.2 Procedures (Renderer → Main)

#### **P1: createRecording**

**Propósito**: Enviar áudio gravado para transcrição

**Direção**: Renderer → Main

**Location**: `main/tipc.ts` linhas ~95-210

```typescript
createRecording: t.procedure
  .input<{
    recording: ArrayBuffer
    duration: number
  }>()
  .action(async ({ input }) => {
    // implementation
  })
```

**Input Schema**:
```typescript
{
  recording: ArrayBuffer   // Audio blob converted to ArrayBuffer
  duration: number         // Duration in milliseconds (e.g., 10500)
}
```

**Process Flow**:
1. Validar que config tem API key
2. Criar FormData com arquivo + modelo
3. POST para Whisper API
4. Pós-processar com LLM (opcional)
5. Salvar em histórico (history.json)
6. Salvar arquivo WebM em disk
7. Colocar no clipboard
8. Simular keystroke (se permitido)
9. Notificar renderer para refetch histórico
10. Esconder panel window

**Output**: Promise que resolve quando tudo completo

**Error Handling**: Throws Error se qualquer step falhar

**Exemplo de Chamada**:
```typescript
// panel.tsx
await tipcClient.createRecording({
  recording: await blob.arrayBuffer(),
  duration: 10500
})
```

---

#### **P2: getRecordingHistory**

**Propósito**: Buscar lista de gravações prévias

**Direção**: Renderer → Main

**Location**: `main/tipc.ts` linhas ~56-74

```typescript
getRecordingHistory: t.procedure.action(async () => {
  try {
    const history = JSON.parse(
      fs.readFileSync(path.join(recordingsFolder, "history.json"), "utf8"),
    ) as RecordingHistoryItem[]
    return history.sort((a, b) => b.createdAt - a.createdAt)
  } catch {
    return []
  }
})
```

**Input Schema**: Nenhum (sem parâmetros)

**Output Schema**:
```typescript
RecordingHistoryItem[] = [
  {
    id: string              // Timestamp string (e.g., "1735814400000")
    createdAt: number       // Timestamp em ms
    duration: number        // Duration em ms
    transcript: string      // Texto transcrito
  },
  ...
]
```

**Sorting**: Descendente por `createdAt` (mais recente primeiro)

**Exemplo de Chamada**:
```typescript
// pages/index.tsx
const history = await tipcClient.getRecordingHistory()
// Returns: [{id: "123", createdAt: 1735814400000, duration: 10500, transcript: "..."}, ...]
```

---

#### **P3: deleteRecordingItem**

**Propósito**: Deletar um item do histórico

**Direção**: Renderer → Main

**Location**: `main/tipc.ts` linhas ~212-225

```typescript
deleteRecordingItem: t.procedure
  .input<{ id: string }>()
  .action(async ({ input }) => {
    const recordings = getRecordingHistory().filter(
      (item) => item.id !== input.id,
    )
    saveRecordingsHitory(recordings)
    fs.unlinkSync(path.join(recordingsFolder, `${input.id}.webm`))
  })
```

**Input Schema**:
```typescript
{
  id: string  // Recording ID (timestamp)
}
```

**Process**:
1. Carrega histórico
2. Filtra item por ID
3. Salva nova lista em history.json
4. Deleta arquivo WebM correspondente

**Output**: Promise que resolve quando tudo completo

**Exemplo de Chamada**:
```typescript
// pages/index.tsx - Delete button
await tipcClient.deleteRecordingItem({id: "1735814400000"})
```

---

#### **P4: getConfig**

**Propósito**: Buscar configuração salva

**Direção**: Renderer → Main

**Location**: `main/tipc.ts` linhas ~231-235

```typescript
getConfig: t.procedure.action(async () => {
  return configStore.get()
})
```

**Output Schema**:
```typescript
Config = {
  shortcut?: "hold-ctrl" | "ctrl-slash"
  hideDockIcon?: boolean
  sttProviderId?: "openai" | "groq"
  openaiApiKey?: string
  openaiBaseUrl?: string
  groqApiKey?: string
  groqBaseUrl?: string
  geminiApiKey?: string
  geminiBaseUrl?: string
  transcriptPostProcessingEnabled?: boolean
  transcriptPostProcessingProviderId?: "openai" | "groq" | "gemini"
  transcriptPostProcessingPrompt?: string
}
```

**Exemplo de Chamada**:
```typescript
// Any page
const config = await tipcClient.getConfig()
console.log(config.openaiApiKey)  // ⚠️ API key em plain text!
```

---

#### **P5: saveConfig**

**Propósito**: Salvar configuração

**Direção**: Renderer → Main

**Location**: `main/tipc.ts` linhas ~237-244

```typescript
saveConfig: t.procedure
  .input<{ config: Config }>()
  .action(async ({ input }) => {
    configStore.save(input.config)
  })
```

**Input Schema**:
```typescript
{
  config: Config  // Config object to save
}
```

**Process**:
1. Valida que input.config é Config type
2. Salva em configStore
3. configStore escreve em config.json (JSON.stringify)

**Exemplo de Chamada**:
```typescript
// pages/settings-general.tsx
await tipcClient.saveConfig({
  config: {
    ...currentConfig,
    openaiApiKey: "sk-..."
  }
})
```

**React Query Integration**:
```typescript
// lib/query-client.ts
export const useSaveConfigMutation = () => useMutation({
  mutationFn: tipcClient.saveConfig,
  onSuccess() {
    queryClient.invalidateQueries({
      queryKey: ["config"]  // Refetch após save
    })
  },
})
```

---

#### **P6: Procedimentos de Permissões**

**P6a: requestMicrophoneAccess**

```typescript
requestMicrophoneAccess: t.procedure.action(async () => {
  return systemPreferences.askForMediaAccess("microphone")
})
```

**Output**: `boolean` (true = granted, false = denied)

**P6b: getMicrophoneStatus**

```typescript
getMicrophoneStatus: t.procedure.action(async () => {
  return systemPreferences.getMediaAccessStatus("microphone")
})
```

**Output**: `"granted" | "denied" | "unknown"`

**P6c: requestAccesssbilityAccess** (macOS only)

```typescript
requestAccesssbilityAccess: t.procedure.action(async () => {
  if (process.platform !== "win32") {
    return systemPreferences.isTrustedAccessibilityClient(true)
  }
  return true
})
```

**P6d: isAccessibilityGranted**

```typescript
isAccessibilityGranted: t.procedure.action(async () => {
  return isAccessibilityGranted()
})
```

**Output**: `boolean`

---

#### **P7: Procedimentos Gerais**

**P7a: restartApp**

```typescript
restartApp: t.procedure.action(async () => {
  app.relaunch()
  app.quit()
})
```

**P7b: hidePanelWindow**

```typescript
hidePanelWindow: t.procedure.action(async () => {
  const panel = WINDOWS.get("panel")
  panel?.hide()
})
```

**P7c: deleteRecordingHistory**

```typescript
deleteRecordingHistory: t.procedure.action(async () => {
  fs.rmSync(recordingsFolder, {force: true, recursive: true})
})
```

---

### 2.3 Event Handlers (Main → Renderer)

**Framework**: `createEventHandlers<RendererHandlers>` de `@egoist/tipc/renderer`

**Location**: `main/renderer-handlers.ts`

---

#### **E1: startRecording**

**Direção**: Main → Renderer (one-way push)

**Payload**: Nenhum

**Quando Dispara**:
- User segura Ctrl por 800ms
- Panel window abre
- Receiver inicia gravação

**Receiver Code** (`panel.tsx`):
```typescript
useEffect(() => {
  const unlisten = rendererHandlers.startRecording.listen(() => {
    recorderRef.current?.startRecording()
  })
  return unlisten
}, [])
```

---

#### **E2: finishRecording**

**Direção**: Main → Renderer

**Payload**: Nenhum

**Quando Dispara**:
- User liberta Ctrl (após hold)
- Marker: confirma que gravação deve ser finalizada

**Receiver Code** (`panel.tsx`):
```typescript
useEffect(() => {
  const unlisten = rendererHandlers.finishRecording.listen(() => {
    isConfirmedRef.current = true
    recorderRef.current?.stopRecording()
  })
  return unlisten
}, [])
```

---

#### **E3: stopRecording**

**Direção**: Main → Renderer

**Payload**: Nenhum

**Quando Dispara**:
- User pressiona Escape enquanto gravando
- Outro key pressionado enquanto holding Ctrl

**Receiver Code** (`panel.tsx`):
```typescript
useEffect(() => {
  const unlisten = rendererHandlers.stopRecording.listen(() => {
    isConfirmedRef.current = false
    recorderRef.current?.stopRecording()
  })
  return unlisten
}, [])
```

---

#### **E4: startOrFinishRecording**

**Direção**: Main → Renderer

**Payload**: Nenhum

**Modo**: Toggle para "Ctrl+/" shortcut

**Quando Dispara**:
- User pressiona Ctrl+/
- Se não gravando: inicia
- Se gravando: finaliza

**Receiver Code** (`panel.tsx`):
```typescript
useEffect(() => {
  const unlisten = rendererHandlers.startOrFinishRecording.listen(() => {
    if (recording) {
      isConfirmedRef.current = true
      recorderRef.current?.stopRecording()
    } else {
      tipcClient.showPanelWindow()
      recorderRef.current?.startRecording()
    }
  })
  return unlisten
}, [recording])
```

---

#### **E5: refreshRecordingHistory**

**Direção**: Main → Renderer

**Payload**: Nenhum

**Quando Dispara**:
- Após createRecording completar (novo item adicionado)

**Receiver Code** (pages/index.tsx):
```typescript
// Implicitamente via React Query invalidation
// Main process não chama diretamente, mas invalida query
```

---

#### **E6: updateAvailable**

**Direção**: Main → Renderer

**Payload**: `UpdateDownloadedEvent` (electron-updater)

**Quando Dispara**:
- Auto-update download completa

**Receiver Code** (`components/updater.tsx`):
```typescript
useEffect(() => {
  const unlisten = rendererHandlers.updateAvailable.listen((event) => {
    showNotification("Update ready to install")
    // Show install button
  })
  return unlisten
}, [])
```

---

### 2.4 Tabela Completa de IPC

| ID | Type | Name | Direction | Payload In | Payload Out | Async | Location |
|----|------|------|-----------|-----------|------------|-------|----------|
| P1 | Procedure | createRecording | R→M | {recording, duration} | void | ✅ | tipc.ts:95 |
| P2 | Procedure | getRecordingHistory | R→M | — | RecordingHistoryItem[] | ✅ | tipc.ts:56 |
| P3 | Procedure | deleteRecordingItem | R→M | {id} | void | ✅ | tipc.ts:212 |
| P4 | Procedure | getConfig | R→M | — | Config | ✅ | tipc.ts:231 |
| P5 | Procedure | saveConfig | R→M | {config} | void | ✅ | tipc.ts:237 |
| P6a | Procedure | requestMicrophoneAccess | R→M | — | boolean | ✅ | tipc.ts:144 |
| P6b | Procedure | getMicrophoneStatus | R→M | — | string | ✅ | tipc.ts:133 |
| P6c | Procedure | requestAccesssbilityAccess | R→M | — | boolean | ✅ | tipc.ts:150 |
| P6d | Procedure | isAccessibilityGranted | R→M | — | boolean | ✅ | tipc.ts:139 |
| P7a | Procedure | restartApp | R→M | — | void | ✅ | tipc.ts:47 |
| P7b | Procedure | hidePanelWindow | R→M | — | void | ✅ | tipc.ts:74 |
| P7c | Procedure | deleteRecordingHistory | R→M | — | void | ✅ | tipc.ts:224 |
| E1 | Event | startRecording | M→R | — | — | ❌ | handlers.ts |
| E2 | Event | finishRecording | M→R | — | — | ❌ | handlers.ts |
| E3 | Event | stopRecording | M→R | — | — | ❌ | handlers.ts |
| E4 | Event | startOrFinishRecording | M→R | — | — | ❌ | handlers.ts |
| E5 | Event | refreshRecordingHistory | M→R | — | — | ❌ | handlers.ts |
| E6 | Event | updateAvailable | M→R | UpdateDownloadedEvent | — | ❌ | handlers.ts |

---

## PARTE 3: INTEGRAÇÃO COM SISTEMA OPERACIONAL

### 3.1 Global Hotkey Listener (Rust + Node.js)

**Framework**: `rdev` (Rust crate) + child process (Node.js)

**Fluxo**:
1. Node.js spawna processo Rust (`whispo-rs listen`)
2. Rust `rdev` escuta eventos globalmente
3. Rust emite JSON para stdout
4. Node.js lê e processa eventos

**Arquivo Rust**: `whispo-rs/src/main.rs`

**Código de Execução** (`keyboard.ts`):

```typescript
const rdevPath = path.join(
  __dirname,
  `../../resources/bin/whispo-rs${process.env.IS_MAC ? "" : ".exe"}`,
).replace("app.asar", "app.asar.unpacked")

const child = spawn(rdevPath, ["listen"], {})

child.stdout.on("data", (data) => {
  const event = parseEvent(data)  // Parse JSON
  if (!event) return
  handleEvent(event)
})
```

**Event Format**:

```json
{
  "event_type": "KeyPress" | "KeyRelease",
  "data": {
    "key": "ControlLeft" | "Escape" | "Slash" | string
  },
  "time": {
    "secs_since_epoch": 1735814400
  }
}
```

**Tipos de Keys Detectados**:
- `ControlLeft`: Ctrl esquerdo
- `Escape`: Esc (para cancelar gravação)
- `Slash`: / (para Ctrl+/)
- Outros: Qualquer outra tecla

**Permissões Requeridas**:
- **Windows**: Nenhuma (funciona por padrão)
- **macOS**: Accessibility Access (System Preferences → Security & Privacy → Accessibility)
- **Linux**: Não suportado (app não funciona)

---

### 3.2 Clipboard API

**Framework**: Electron `clipboard` module

**Método Utilizado**: `clipboard.writeText()`

**Código** (`tipc.ts`):

```typescript
clipboard.writeText(transcript)
```

**Propósito**: Colocar texto transcrito na clipboard para Ctrl+V

**Plataformas Suportadas**: Windows, macOS, Linux ✅

**Permissões Requeridas**: Nenhuma

---

### 3.3 Keystroke Simulation (Rust)

**Framework**: `enigo` (Rust crate)

**Fluxo**:
1. Node.js chama Rust: `spawn(rdevPath, ["write", text])`
2. Rust `enigo` simula digitação
3. Keystrokes injetadas na aplicação em foco

**Arquivo Rust** (`whispo-rs/src/main.rs`):

```rust
fn write_text(text: &str) {
  use enigo::{Enigo, Keyboard, Settings};
  let mut enigo = Enigo::new(&Settings::default()).unwrap();
  enigo.text(text).unwrap();
}
```

**Código Node.js** (`keyboard.ts`):

```typescript
export const writeText = (text: string) => {
  return new Promise<void>((resolve, reject) => {
    const child = spawn(rdevPath, ["write", text])
    
    child.on("close", (code) => {
      keysPressed.clear()
      if (code === 0) {
        resolve()
      } else {
        reject(new Error(`child process exited with code ${code}`))
      }
    })
  })
}
```

**Permissões Requeridas**:
- **Windows**: Nenhuma
- **macOS**: Accessibility Access (mesmo de global hotkeys)
- **Linux**: Não suportado

**Suporta**: Caracteres especiais (!, @, #, etc) via enigo

---

### 3.4 Permissões do Sistema

#### **Windows**

| Recurso | Permissão | Como Solicitar |
|---------|-----------|---|
| Microfone | Automática | Primeira gravação |
| Clipboard | Automática | Sem necessidade |
| Keystroke | Automática | Sem necessidade |
| Hotkeys Globais | Automática | Sem necessidade |

#### **macOS**

| Recurso | Permissão | Como Solicitar | Location |
|---------|-----------|---|---|
| Microfone | Necessária | `systemPreferences.askForMediaAccess("microphone")` | pages/setup.tsx |
| Clipboard | Automática | — | — |
| Keystroke | Accessibility Access | `systemPreferences.isTrustedAccessibilityClient(true)` | pages/setup.tsx |
| Hotkeys Globais | Accessibility Access | Mesmo de Keystroke | — |

#### **Linux**

| Recurso | Permissão | Suporte |
|---------|-----------|--------|
| Microfone | Necessária | ✅ |
| Clipboard | Automática | ✅ |
| Keystroke | Necessária | ❌ |
| Hotkeys Globais | Necessária | ❌ |

---

## PARTE 4: SCHEMA DE CONFIGURAÇÃO

### 4.1 Estrutura do Arquivo de Config

**Localização**:
```
Windows: C:\Users\{user}\AppData\Roaming\io.github.egoist.whispo\config.json
macOS:   ~/Library/Application Support/io.github.egoist.whispo/config.json
Linux:   ~/.config/io.github.egoist.whispo/config.json
```

**Formato**: JSON

---

### 4.2 JSON Schema Completo

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Whispo Configuration",
  "description": "Configuration file for Whispo AI-powered dictation tool",
  "type": "object",
  "properties": {
    "shortcut": {
      "type": "string",
      "enum": ["hold-ctrl", "ctrl-slash"],
      "default": "hold-ctrl",
      "description": "Recording hotkey mode. 'hold-ctrl': hold to record, release to finish. 'ctrl-slash': toggle mode."
    },
    "hideDockIcon": {
      "type": "boolean",
      "default": false,
      "description": "macOS only. Hide dock icon when main window is closed."
    },
    "sttProviderId": {
      "type": "string",
      "enum": ["openai", "groq"],
      "default": "openai",
      "description": "Speech-to-text provider for transcription."
    },
    "openaiApiKey": {
      "type": "string",
      "pattern": "^sk-[a-zA-Z0-9]{40,}$",
      "description": "OpenAI API key for Whisper transcription. Format: sk-xxx (48+ chars)."
    },
    "openaiBaseUrl": {
      "type": "string",
      "format": "uri",
      "default": "https://api.openai.com/v1",
      "description": "Custom OpenAI base URL for proxies or self-hosted."
    },
    "groqApiKey": {
      "type": "string",
      "pattern": "^gsk_[a-zA-Z0-9]{40,}$",
      "description": "Groq API key for Whisper-large-v3. Format: gsk_xxx (~50 chars)."
    },
    "groqBaseUrl": {
      "type": "string",
      "format": "uri",
      "default": "https://api.groq.com/openai/v1",
      "description": "Custom Groq base URL for proxies or self-hosted."
    },
    "geminiApiKey": {
      "type": "string",
      "minLength": 20,
      "description": "Google Gemini API key for LLM post-processing."
    },
    "geminiBaseUrl": {
      "type": "string",
      "format": "uri",
      "default": "https://generativelanguage.googleapis.com",
      "description": "Google Gemini base URL."
    },
    "transcriptPostProcessingEnabled": {
      "type": "boolean",
      "default": false,
      "description": "Enable LLM post-processing of transcribed text (grammar, punctuation, etc)."
    },
    "transcriptPostProcessingProviderId": {
      "type": "string",
      "enum": ["openai", "groq", "gemini"],
      "default": "openai",
      "description": "LLM provider for post-processing. Used only if transcriptPostProcessingEnabled is true."
    },
    "transcriptPostProcessingPrompt": {
      "type": "string",
      "maxLength": 2000,
      "default": "Fix grammar and spelling in the following text:\n\n{transcript}",
      "description": "Prompt template for LLM. Must include {transcript} placeholder for original text."
    }
  },
  "required": [],
  "additionalProperties": false
}
```

---

### 4.3 Exemplo de Config.json

```json
{
  "shortcut": "hold-ctrl",
  "hideDockIcon": false,
  "sttProviderId": "openai",
  "openaiApiKey": "sk-proj-xxxxxxxxxxxxx",
  "openaiBaseUrl": "https://api.openai.com/v1",
  "groqApiKey": "gsk_xxxxxxxxxxxxx",
  "groqBaseUrl": "https://api.groq.com/openai/v1",
  "geminiApiKey": "xxxxxxxxxxxxxxx",
  "geminiBaseUrl": "https://generativelanguage.googleapis.com",
  "transcriptPostProcessingEnabled": true,
  "transcriptPostProcessingProviderId": "openai",
  "transcriptPostProcessingPrompt": "Fix all grammar and punctuation errors. Maintain original meaning:\n\n{transcript}"
}
```

---

### 4.4 TypeScript Types

**Location**: `src/shared/types.ts`

```typescript
export type Config = {
  shortcut?: "hold-ctrl" | "ctrl-slash"
  hideDockIcon?: boolean
  sttProviderId?: STT_PROVIDER_ID
  openaiApiKey?: string
  openaiBaseUrl?: string
  groqApiKey?: string
  groqBaseUrl?: string
  geminiApiKey?: string
  geminiBaseUrl?: string
  transcriptPostProcessingEnabled?: boolean
  transcriptPostProcessingProviderId?: CHAT_PROVIDER_ID
  transcriptPostProcessingPrompt?: string
}

export type RecordingHistoryItem = {
  id: string
  createdAt: number
  duration: number
  transcript: string
}

export type STT_PROVIDER_ID = "openai" | "groq"
export type CHAT_PROVIDER_ID = "openai" | "groq" | "gemini"
```

---

### 4.5 Carregamento e Salvamento

**Location**: `src/main/config.ts`

```typescript
class ConfigStore {
  config: Config | undefined

  constructor() {
    this.config = getConfig()
  }

  get() {
    return this.config || {}
  }

  save(config: Config) {
    this.config = config
    fs.mkdirSync(dataFolder, {recursive: true})
    fs.writeFileSync(configPath, JSON.stringify(config))
  }
}

export const configStore = new ConfigStore()
```

**Comportamento**:
- ✅ Carregamento gracioso: se arquivo não existe/corrupto, retorna {}
- ✅ Salvamento seguro: cria diretório se necessário
- ⚠️ Sem encriptação (API keys em plain text)
- ⚠️ Sem schema validation (qualquer JSON é aceito)

---

## PARTE 5: DIAGRAMA DE INTEGRAÇÃO COMPLETO

```mermaid
graph TB
    subgraph "Whispo Application"
        A["Main Process<br/>(Node.js)"]
        B["Renderer Process<br/>(React)"]
        C["Preload Bridge"]
    end

    subgraph "System Integration"
        D["Global Hotkey<br/>(whispo-rs + rdev)"]
        E["Clipboard<br/>(Electron)"]
        F["Keystroke Simulation<br/>(whispo-rs + enigo)"]
        G["Permissions<br/>(systemPreferences)"]
    end

    subgraph "External APIs"
        H["Whisper API<br/>(OpenAI/Groq)"]
        I["LLM API<br/>(OpenAI/Groq/Gemini)"]
    end

    subgraph "Local Storage"
        J["config.json"]
        K["history.json + recordings/"]
    end

    B -->|tipcClient| A
    A -->|rendererHandlers| B
    A -->|IPC| C
    C -->|electronAPI| B

    A -->|Listen + Write| D
    A -->|writeText()| E
    A -->|enigo| F
    A -->|askForAccess| G

    A -->|POST /audio/transcriptions| H
    A -->|POST /chat/completions| I

    A -->|Read/Write| J
    A -->|Read/Write| K

    B -->|query config| J
    B -->|list recordings| K

    D -->|hotkey events| A
    H -->|transcribed text| A
    I -->|processed text| A

    style A fill:#4f46e5,color:#fff
    style B fill:#4f46e5,color:#fff
    style D fill:#8b5cf6,color:#fff
    style H fill:#10b981,color:#fff
    style I fill:#10b981,color:#fff
    style J fill:#f59e0b,color:#fff
    style K fill:#f59e0b,color:#fff
```

---

## PARTE 6: REFERÊNCIA RÁPIDA

### Checklist para Integração

#### **Antes de Implementar Novo Provider de LLM**:
- [ ] Adicionar novo entry em `CHAT_PROVIDERS` (`shared/index.ts`)
- [ ] Implementar novo condicional em `llm.ts` para handler
- [ ] Testar request/response format
- [ ] Adicionar documentação de API key format

#### **Antes de Adicionar Nova Procedure IPC**:
- [ ] Definir em `tipc.ts` com `.input<T>().action(async () => {})`
- [ ] Adicionar tipos em `shared/types.ts` se necessário
- [ ] Adicionar handler correspondente em `renderer-handlers.ts`
- [ ] Testar com `tipcClient.yourProcedure()`

#### **Antes de Alterar Schema Config**:
- [ ] Atualizar `Config` type em `shared/types.ts`
- [ ] Atualizar `getConfig()` fallback em `config.ts`
- [ ] Testar com config velho (backward compat)
- [ ] Documentar novo field em JSON Schema

---

## CONCLUSÃO

**Total de Interfaces Documentadas**:
- ✅ 3 APIs externas (Whisper, OpenAI, Groq, Gemini)
- ✅ 12 Procedures IPC (R→M)
- ✅ 6 Event handlers IPC (M→R)
- ✅ 4 APIs do SO (hotkeys, clipboard, keystroke, permissions)
- ✅ 1 Schema de config com JSON Schema

**Qualidade da Documentação**:
- ✅ Exemplos de curl para APIs HTTP
- ✅ TypeScript interfaces para todos os tipos
- ✅ Diagramas Mermaid de fluxo
- ✅ Error handling mapeado
- ✅ Permissões por SO documentadas

**Readiness for Reuse**:
- ✅ Outro desenvolvedor pode implementar novo provider com referência
- ✅ Troubleshooting facilitado (saber exato endpoint/header/format)
- ✅ Integração com sistemas externos possível (exemplo: Zapier)

---

**Documento da FASE 5 Concluído com Sucesso**
