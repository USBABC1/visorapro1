"""
Script para configurar autenticação Hugging Face automaticamente
"""
import os
import sys
from pathlib import Path

def setup_huggingface_token():
    """Setup Hugging Face token automatically"""
    
    print("🤖 Configurando acesso aos modelos Hugging Face...")
    
    # Check if token already exists
    hf_home = Path.home() / ".huggingface"
    token_file = hf_home / "token"
    
    if token_file.exists():
        print("✓ Token Hugging Face já configurado")
        return True
    
    print("""
📝 Para usar os modelos BiRefNet com máxima qualidade, você pode:

1. OPÇÃO RECOMENDADA - Usar sem token (funciona para a maioria dos casos):
   - O sistema usará métodos alternativos de alta qualidade
   - Funciona imediatamente sem configuração
   
2. OPÇÃO AVANÇADA - Configurar token Hugging Face (qualidade máxima):
   - Acesse: https://huggingface.co/settings/tokens
   - Crie um token gratuito
   - Cole o token quando solicitado

⚠️  IMPORTANTE: O sistema funciona perfeitamente SEM token!
   Métodos alternativos garantem velocidade CapCut com ótima qualidade.
Escolha uma opção:
[1] Continuar sem token (recomendado)
[2] Configurar token Hugging Face
[3] Pular configuração
""")
    
    try:
        choice = input("Digite sua escolha (1-3): ").strip()
        
        if choice == "1":
            print("✓ Configurado para usar métodos alternativos de alta qualidade")
            return True
            
        elif choice == "2":
            token = input("Cole seu token Hugging Face aqui: ").strip()
            
            if token:
                # Create .huggingface directory
                hf_home.mkdir(exist_ok=True)
                
                # Save token
                with open(token_file, 'w') as f:
                    f.write(token)
                
                print("✓ Token Hugging Face configurado com sucesso!")
                return True
            else:
                print("⚠️ Token vazio, usando métodos alternativos")
                return True
                
        else:
            print("⚠️ Configuração pulada, usando métodos alternativos")
            return True
            
    except KeyboardInterrupt:
        print("\n⚠️ Configuração cancelada, usando métodos alternativos")
        return True
    except Exception as e:
        print(f"⚠️ Erro na configuração: {e}")
        print("Usando métodos alternativos")
        return True

def test_setup():
    """Test the setup"""
    try:
        from background_remover import test_models
        return test_models()
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Configurando Video Editor Pro...")
    
    success = setup_huggingface_token()
    
    if success:
        print("\n🧪 Testando configuração...")
        if test_setup():
            print("✅ Configuração concluída com sucesso!")
        else:
            print("⚠️ Configuração parcial - sistema funcionará com métodos alternativos")
    
    print("\n🎬 Sistema pronto para uso!")
    input("Pressione Enter para continuar...")