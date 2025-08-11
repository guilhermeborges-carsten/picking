#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar a senha hash do administrador
Execute este script para obter o hash da senha 'admin123'
"""

from werkzeug.security import generate_password_hash

def gerar_senha_admin():
    """Gera o hash da senha padrão do administrador"""
    senha = "admin123"
    hash_senha = generate_password_hash(senha)
    
    print("=" * 60)
    print("GERADOR DE SENHA ADMINISTRADOR")
    print("=" * 60)
    print(f"Senha: {senha}")
    print(f"Hash gerado: {hash_senha}")
    print("=" * 60)
    print("\nINSTRUÇÕES:")
    print("1. Copie o hash acima")
    print("2. Abra o arquivo database_setup.sql")
    print("3. Substitua 'YOUR_HASH_HERE' pelo hash gerado")
    print("4. Execute o script SQL no seu banco de dados")
    print("5. Faça login com username: 'admin' e senha: 'admin123'")
    print("6. ALTERE A SENHA IMEDIATAMENTE após o primeiro login!")
    print("=" * 60)
    
    return hash_senha

if __name__ == "__main__":
    gerar_senha_admin()
