# Video Editor Pro

Uma interface moderna e profissional para edição de vídeos com recursos avançados de IA, incluindo remoção automática de silêncios, remoção de background e geração de legendas sincronizadas.

## 🚀 Recursos Principais

### Interface Profissional Similar ao CapCut
- **Design Moderno**: Interface responsiva com tema escuro profissional
- **Player de Vídeo Sofisticado**: Controles completos com timeline, volume, velocidade, fullscreen
- **Visualização Lado a Lado**: Compare vídeo original e processado simultaneamente
- **Drag & Drop**: Arraste vídeos diretamente para a interface
- **Animações Suaves**: Transições e efeitos visuais profissionais

### Ferramentas de IA Avançadas
- **Remoção de Silêncios**: Auto-editor com detecção automática e transições suaves
- **Remoção de Background**: BiRefNet IA + métodos alternativos com qualidade profissional
- **Geração de Legendas**: Whisper IA para transcrição automática e sincronizada
- **Exportação Múltipla**: MP4, MOV, AVI, MKV + legendas SRT

### Configuração Automática
- **setup.bat**: Instalação automática de todas as dependências
- **start.bat**: Execução completa com um clique
- **Configuração Zero**: Pronto para usar após setup

## 🛠️ Tecnologias Utilizadas

### Frontend
- **React 18** com TypeScript
- **Tailwind CSS** para design moderno
- **Lucide React** para ícones profissionais
- **Vite** para desenvolvimento rápido

### Backend & IA
- **FastAPI** para API REST de alta performance
- **PyTorch** com suporte CUDA para processamento de IA
- **BiRefNet** para remoção de background com qualidade profissional
- **Whisper** para geração de legendas precisas
- **Auto-editor** para remoção inteligente de silêncios
- **FFmpeg** para processamento de vídeo otimizado

## 📋 Pré-requisitos

O setup automático instalará tudo, mas você pode instalar manualmente:
- **Windows 10/11** (64-bit)
- **8GB RAM** (16GB recomendado)
- **GPU NVIDIA** (opcional, para aceleração CUDA)
- **5GB espaço livre** em disco

## 🚀 Instalação Ultra-Rápida

### 1. Clone ou baixe o projeto
```bash
git clone <repository-url>
cd video-editor-pro
```

### 2. Execute o setup automático (como Administrador)
```bash
setup.bat
```
*O script irá automaticamente:*
- ✅ Instalar Python 3.11 se necessário
- ✅ Instalar Node.js 20 se necessário  
- ✅ Baixar e configurar FFmpeg
- ✅ Instalar PyTorch com CUDA
- ✅ Configurar todos os modelos de IA
- ✅ Instalar todas as dependências
- ✅ Configurar métodos alternativos para máxima compatibilidade

### 3. Inicie a aplicação
```bash
start.bat
```

A aplicação abrirá automaticamente em `http://localhost:5173`

## 📖 Como Usar

### 1. Upload de Vídeo
- **Arraste e solte** um vídeo na interface
- Ou **clique para selecionar** um arquivo
- Formatos suportados: MP4, MOV, AVI, MKV

### 2. Ferramentas de Processamento

#### 🎬 Remover Silêncios
- Remove automaticamente pausas e silêncios
- Cria transições suaves entre trechos
- Configurável: limite de silêncio e margem de frames

#### 🎭 Remover Background  
- IA BiRefNet com qualidade profissional
- **Métodos alternativos** quando BiRefNet não disponível
- Detecção de bordas aprimorada
- Opções: transparente, cor sólida ou imagem
- Modo rápido ou alta qualidade

#### 📝 Gerar Legendas
- IA Whisper para transcrição precisa
- Sincronização automática
- Múltiplos idiomas suportados
- Exportação em formato SRT

### 3. Configurações Avançadas
- **Qualidade de Vídeo**: Controle CRF (18-28)
- **Resolução**: Original, 4K, 1080p, 720p, 480p
- **Codec**: H.264, H.265, VP9
- **Formato**: MP4, MOV, AVI, MKV

### 4. Exportação
- Download do vídeo processado
- Download das legendas SRT
- Múltiplos formatos disponíveis

## ⚙️ Configurações Detalhadas

### Remoção de Silêncios
```
Limite de Silêncio: -30dB (padrão)
Margem de Quadros: 6 frames (padrão)
Transições: Suaves e automáticas
```

### Remoção de Background
```
Modelo: BiRefNet (alta qualidade) / BiRefNet Lite (rápido) / Métodos alternativos
Qualidade: Baixa/Média/Alta
Aprimoramento: Suavização de bordas ativada
Background: Transparente/Cor/Imagem
Fallback: Métodos OpenCV para máxima compatibilidade
```

### Geração de Legendas
```
Modelo: Whisper base
Idiomas: pt-BR, en-US, es-ES, fr-FR, de-DE, it-IT, ja-JP, ko-KR
Formato: SRT com timestamps precisos
```

## 🎯 Presets Otimizados

### YouTube/Social Media
- Silêncio: -25dB | Margem: 6 frames
- Qualidade: CRF 20 | Resolução: 1080p
- Codec: H.264 | Formato: MP4

### Alta Qualidade Profissional
- Silêncio: -30dB | Margem: 12 frames  
- Qualidade: CRF 18 | Resolução: Original
- Codec: H.265 | Formato: MOV

### Processamento Rápido
- Silêncio: -20dB | Margem: 3 frames
- Qualidade: CRF 25 | Resolução: 720p
- Codec: H.264 | Formato: MP4

## 🔧 Estrutura do Projeto

```
video-editor-pro/
├── src/                    # Frontend React + TypeScript
│   ├── components/         # Componentes da interface
│   ├── types/             # Definições TypeScript
│   └── App.tsx            # Aplicação principal
├── backend/               # Backend Python + FastAPI
│   ├── main.py           # API principal
│   ├── background_remover.py  # BiRefNet IA + métodos alternativos
│   ├── silence_remover.py     # Auto-editor
│   ├── subtitle_generator.py # Whisper IA
│   └── huggingface_setup.py  # Configuração automática
├── setup.bat             # Instalação automática
├── start.bat             # Execução automática
└── README.md
```

## 🐛 Solução de Problemas

### Erro: "Virtual environment not found"
```bash
# Execute o setup novamente
setup.bat
```

### Erro: "Backend connection failed"
```bash
# Verifique se as portas estão livres
netstat -an | find "8000"
netstat -an | find "5173"
```

### Erro: "BiRefNet authentication failed"
```bash
# O sistema funcionará com métodos alternativos
# Para máxima qualidade, configure token Hugging Face:
# 1. Acesse: https://huggingface.co/settings/tokens
# 2. Crie um token gratuito
# 3. Execute: python backend/huggingface_setup.py
```

### Erro: "CUDA not available"
```bash
# Opcional - instale drivers NVIDIA mais recentes
# O sistema funcionará com CPU
```

### Erro: "FFmpeg not found"
```bash
# Execute setup.bat como Administrador
# Ou baixe FFmpeg manualmente de https://ffmpeg.org
```

## 📊 Requisitos de Sistema

### Mínimos
- **OS**: Windows 10 64-bit
- **CPU**: Intel i5 / AMD Ryzen 5
- **RAM**: 8GB
- **GPU**: Integrada (funcional)
- **Disco**: 5GB livres

### Recomendados
- **OS**: Windows 11 64-bit
- **CPU**: Intel i7 / AMD Ryzen 7
- **RAM**: 16GB+
- **GPU**: NVIDIA GTX 1060+ (CUDA)
- **Disco**: SSD com 10GB+ livres

## 🚀 Performance

### Tempos de Processamento (aproximados)
- **Remoção de Silêncios**: 1-2x duração do vídeo
- **Remoção de Background**: 3-5x duração do vídeo
- **Geração de Legendas**: 0.5-1x duração do vídeo

### Otimizações
- **CUDA**: Acelera processamento de IA em 3-5x
- **SSD**: Melhora velocidade de I/O significativamente
- **RAM**: Mais RAM = processamento de vídeos maiores
- **Métodos Alternativos**: Garantem funcionamento mesmo sem GPU

## 🎨 Interface CapCut-Style

### Características da Interface
- **Design Profissional**: Tema escuro com gradientes modernos
- **Glass Morphism**: Efeitos de vidro e transparência
- **Neumorphism**: Botões com efeitos 3D suaves
- **Animações Fluidas**: Transições e micro-interações
- **Responsivo**: Funciona em todas as resoluções

### Player de Vídeo Avançado
- **Controles Completos**: Play, pause, volume, timeline
- **Velocidade Variável**: 0.5x até 2x
- **Tela Cheia**: Suporte completo a fullscreen
- **Atalhos**: Espaço para play/pause, setas para navegação
- **Indicadores Visuais**: Loading, progresso, status

## 🔒 Compatibilidade e Segurança

### Funcionamento Garantido
- **Sem Token**: Sistema funciona completamente sem configuração
- **Métodos Alternativos**: OpenCV para remoção de background
- **Fallback Automático**: Troca automática entre métodos
- **Offline**: Funciona completamente offline após setup

### Configuração Opcional
- **Token Hugging Face**: Para máxima qualidade BiRefNet
- **CUDA**: Para aceleração de GPU
- **Configuração Automática**: Script interativo para setup

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Auto-editor** - Remoção inteligente de silêncios
- **BiRefNet** - IA para remoção de background profissional
- **Whisper** - IA para geração de legendas precisas
- **FFmpeg** - Processamento de vídeo otimizado
- **React + TypeScript** - Interface moderna e robusta
- **FastAPI** - Backend de alta performance

## 📞 Suporte

Para suporte e dúvidas:
- 🐛 Abra uma [Issue](../../issues)
- 📖 Consulte a [Documentação](../../wiki)
- 💬 Entre em contato via email

---

**Video Editor Pro** - Edição de vídeo profissional com IA 🎬✨

*Desenvolvido com ❤️ para criadores de conteúdo*

**FUNCIONA GARANTIDO** - Com ou sem token Hugging Face! 🚀