## Voice MCP

A **Model Context Protocol (MCP)** server for voice-related operations, offering a secure and extensible interface for text-to-speech synthesis, playback, and audio processing.

---

### Key Features

- **Text-to-Speech Synthesis**: Generate natural-sounding speech from text using Kokoro TTS.
- **Instant Playback**: Play audio in-memory without intermediate file output.
- **Audio Manipulation**: Support for custom sample rates and voice parameters.
- **Multilingual Support**: Synthesize speech in multiple languages and accents.
- **MCP Integration**: Seamless interaction via the Model Context Protocol framework.

---

## Technology Stack

**Kokoro TTS** (HuggingFace hexgrad/Kokoro-82M) powers the speech synthesis, offering:

- High fidelity voice output with only 82M parameters.
- Broad multilingual capability (Chinese, Japanese, English, and more).
- Low computational overhead ideal for real-time applications.

---

## Prerequisites

1. **System Dependencies**  
   - **Linux**: `sudo apt-get install espeak-ng`  
   - **Windows/macOS**: Install `espeak-ng` via your package manager or installer.

2. **Python Environment**  
   ```bash
   git clone <repository-url>
   cd voice_mcp
   python -m venv env
   source env/bin/activate      # Windows: env\Scripts\activate
   pip install --upgrade pip
   ```

3. **Python Packages**  
   ```bash
   pip install mcp[cli] uv dotenv  kokoro>=0.9.2 soundfile sounddevice
   pip install misaki[zh,ja] # for japanese and chinese
   ```

---

## Configuration

### 1. Command-Line Arguments

```bash
python voice_server.py --lang us --voice af_nicole --sample-rate 24000
```

### 2. Environment Variables

```bash
export VOICE_LANG=us
export VOICE_NAME=af_nicole
export VOICE_SAMPLE_RATE=24000
```

### 3. MCP Configuration File (`mcp.json`)

```json
{
  "mcpServers": {
    "voice_mcp": {
      "command": "python",
      "args": ["voice_server.py", "--lang", "us", "--voice", "af_nicole"],
      "env": {
        "VOICE_SAMPLE_RATE": "24000"
      },
      "env": {
        // "VOICE_LANG": "us",
        // "VOICE_NAME": "af_nicole",
        // "VOICE_SAMPLE_RATE": "24000"
      }
    }
  }
}
```

---

## Supported Voices

| Language   | Voice Name       | Identifier      |
|------------|------------------|-----------------|
| English (US) | Michael         | `am_michael`    |
| English (US) | Adam            | `am_adam`       |
| English (UK) | George          | `bm_george`     |
| English (UK) | Emma            | `bf_emma`       |
| Spanish      | Sky             | `af_sky`        |
| French       | Nicole          | `af_nicole`     |
| Hindi        | Sarah           | `af_sarah`      |
| Italian      | Emma            | `bf_emma`       |
| Japanese     | Bella           | `af_bella`      |
| Portuguese   | Isabella        | `bf_isabella`   |
| Chinese      | Adam            | `am_adam`       |

---


## Available Tools

| Tool | Description |
|------|-------------|
| `play_audio` | Converts input text to speech and plays it instantly in-memory, without saving to a file. |

## Usage Examples

```text
"The quick brown fox jumps over the lazy dog."
```

```text
"Play a festive poem about Santa’s journey through snowy nights and cheerful hearts."
```

```text
"Welcome to the Acme Learning Portal. In today’s module, we’ll cover information security best practices."
```

---

## Troubleshooting

1. **Missing Dependencies**: Ensure `espeak-ng` is installed and accessible.
2. **Model Load Failures**: Verify the Kokoro TTS model is downloaded and compatible.
3. **Audio Device Errors**: Check system audio settings and permissions.

---

## Attribution

Voice synthesis powered by [Kokoro TTS (82M)](https://huggingface.co/hexgrad/Kokoro-82M). Refer to the model’s license for terms.

---

## Contributing

Contributions are welcome via GitHub:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request with descriptive commit messages.

---

## Running with MCP Inspector

Launch in development mode for debugging:

```bash
mcp dev voice_server.py:main
```

- **Transport Type**: STUDIO  
- **Command**: `uvicorn`  
- **Args**: `run server.py --voice af_nicole --lang fr --sample-rate 24000`
