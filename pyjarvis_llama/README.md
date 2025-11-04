# PyJarvis LLM Integration

Módulo CLI ativo para integração com Ollama LLM e PyJarvis, incluindo reconhecimento de voz.

## Funcionalidades

- CLI interativo que aguarda entrada do usuário
- Integração com servidor Ollama (configurável)
- **Reconhecimento de voz** com microfone (`/m`)
- **Multi-idioma** para STT (`/lang`)
- **Múltiplas personalidades** de IA (`/persona`)
- Envio automático de respostas da LLM para PyJarvis (TTS)
- Suporte a histórico de conversação
- Comandos especiais para controle

## Requisitos

- Ollama instalado e rodando
- Modelo LLM disponível no Ollama (padrão: llama3.2)
- PyJarvis service rodando

## Instalação

1. Instale o Ollama: <https://ollama.ai/>
2. Baixe um modelo:

   ```bash
   ollama pull llama3.2
   ```

3. Inicie o servidor Ollama:

   ```bash
   ollama serve
   ```

## Uso

### Executar o CLI

```bash
python -m pyjarvis_llama
```

### Configuração

A configuração está em `pyjarvis_shared/config.py`:

```python
ollama_base_url: str = "http://localhost:11434"  # URL do servidor Ollama
ollama_model: str = "llama3.2"  # Modelo a usar
```

### Comandos

**Entrada de Texto:**

- Digite sua mensagem e pressione Enter
- A resposta da LLM será enviada automaticamente para PyJarvis

**Comandos Especiais:**

- `/exit` ou `/quit` - Sair do programa
- `/clear` - Limpar histórico de conversação
- `/m` - Gravar áudio do microfone (pressione Enter para parar)
- `/lang [code]` - Definir idioma de reconhecimento de voz
  - Exemplo: `/lang pt` (Português), `/lang en` (Inglês)
  - Sem argumento: mostra idioma atual e ajuda
- `/persona <name>` - Mudar personalidade da IA
  - Disponíveis: `jarvis`, `friendly`, `professional`, `portuguese`
  - Sem argumento: mostra persona atual e opções

### Idioma de Reconhecimento de Voz

Use `/lang` para configurar o idioma do reconhecimento de voz:

```bash
# Ver idioma atual
/lang

# Mudar para Português
/lang pt
# ou
/lang portuguese

# Mudar para Inglês
/lang en
# ou
/lang english
```

Idiomas suportados: en, pt, es, fr, de, it, ja, ko, zh, ru, ar, hi, tr, pl, nl, sv, fi, no

## Fluxo

### Entrada de Texto

1. Usuário digita mensagem no CLI
2. Mensagem é enviada para Ollama
3. Ollama gera resposta usando o modelo configurado
4. Resposta é enviada automaticamente para PyJarvis
5. Service processa e gera áudio
6. UI reproduz o áudio com animações

### Entrada de Voz (`/m`)

1. Usuário executa `/m` e pressiona Enter
2. Sistema inicia gravação do microfone
3. Áudio é salvo em `./audio/rec_YYYYMMDD-HHmmss.wav`
4. RealtimeSTT transcreve áudio para texto
5. Texto transcrito é enviado para Ollama
6. Ollama gera resposta
7. Resposta é enviada para PyJarvis (mesmo fluxo acima)
8. Arquivo de áudio é deletado após transcrição

## Estrutura

```text
pyjarvis_llama/
├── __init__.py          # Exports principais
├── __main__.py          # Entry point
├── cli.py               # CLI interativo (comandos /m, /lang, /persona)
├── llama_client.py      # Cliente Ollama (aiohttp)
├── audio_recorder.py    # Gravação e STT (RealtimeSTT wrapper)
├── personas.py          # Estratégias de personalidade (Strategy Pattern)
└── README.md            # Esta documentação
```

## Configuração

A configuração está em `pyjarvis_shared/config.py`:

```python
# Ollama Configuration
ollama_base_url: str = "http://localhost:11434"
ollama_model: str = "llama3.2"
ollama_persona: str = "jarvis"

# Speech-to-Text Configuration
stt_model: str = "base"  # Whisper model: base, small, medium, large
stt_language: str = "en"  # Default recognition language
```

## Troubleshooting

### Erro: "Failed to connect to Ollama server"

- Verifique se o Ollama está rodando: `ollama serve`
- Verifique a URL em `ollama_base_url` na configuração
- Teste manualmente: `curl http://localhost:11434/api/tags`

### Erro: "Model 'llama3.2' not found"

- Baixe o modelo: `ollama pull llama3.2`
- Ou altere o modelo na configuração para um modelo disponível

### Erro: "Failed to send to PyJarvis"

- Verifique se `pyjarvis_service` está rodando
- Verifique se `pyjarvis_ui` está conectada ao serviço

### Erro: "RealtimeSTT not available"

- Instale: `pip install RealtimeSTT`
- Primeira execução baixará modelos Whisper (pode demorar)

### Erro: "No speech detected"

- Verifique permissões do microfone
- Fale claramente e aguarde 1-2 segundos após falar
- Verifique se o idioma está correto: `/lang`
- Teste o microfone em outros aplicativos

### Áudio não sendo transcrito

- Verifique se o microfone está funcionando
- Aguarde um momento após pressionar Enter antes de falar
- Use `/lang` para definir o idioma correto
- Verifique logs para mensagens de erro

### Delay na inicialização da gravação

- Normal na primeira vez (download de modelos)
- Stream de áudio paralelo já captura mesmo durante inicialização
- Mensagem "Listening..." aparece quando gravação realmente inicia
