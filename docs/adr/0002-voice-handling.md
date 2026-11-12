# ADR 0002: Voice Order Handling & Multimodal Architecture

## Status
Accepted

## Context
Retailers in Indian wholesale ecosystems frequently place orders by sending WhatsApp voice notes. These voice notes are rarely spoken in standard formal English or Hindi; they feature heavy colloquial mixing (Hinglish, Tanglish), background warehouse noise, regional grocery terms, and informal abbreviations (e.g., *"ek carton parle-g aur paanch kilo madhur cheeni bhej do"*).

Traditional architectures use a two-stage pipeline: Whisper STT $\to$ LLM parsing. However, this causes compounding errors: if Whisper mistranscribes a regional brand or unit, the downstream LLM cannot recover.

## Decision
1. **Direct Multimodal Audio Processing:**
   - Ingest audio files (OGG, MP3, WAV, AAC) directly into Google Gemini (`gemini-2.0-flash` / `gemini-1.5-flash`).
   - Gemini's native multimodal audio model ingests raw acoustic features directly, understanding spoken Hinglish, regional accents, and inflection without an intermediate textual error cascade.
2. **Batching & Background Extraction:**
   - Voice audio is uploaded to storage, referenced in `messages`, and parsed via an asynchronous background job.
   - The worker passes the audio buffer with the versioned system prompt and structured JSON schema, extracting phrases, units, and quantities.
3. **Safety Fallback:**
   - If audio quality is degraded or confidence is low, the worker flags the message as `needs_manual_entry` and extracts partial items to RED status lines.

## Consequences
- Eliminates the operational overhead and latency of maintaining a separate Whisper server.
- Significantly higher extraction accuracy on mixed Indian regional languages and trade slang.
