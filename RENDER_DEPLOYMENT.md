# 🚀 Deploy no Render - Sistema Picking

## 📋 Configurações Necessárias

### 1. **Variáveis de Ambiente no Render:**
```
FLASK_APP=app.py
FLASK_ENV=production
PORT=5000
HOST=0.0.0.0
SECRET_KEY=sua_chave_secreta_aqui
```

### 2. **Build Command:**
```bash
pip install -r requirements.txt
```

### 3. **Start Command:**
```bash
python app.py
```

### 4. **Python Version:**
- **Versão:** 3.9.16 ou superior

## 🔧 Arquivos de Configuração

### ✅ **Arquivos já configurados:**
- `render.yaml` - Configuração do Render
- `wsgi.py` - Ponto de entrada WSGI
- `Procfile` - Configuração do processo
- `requirements.txt` - Dependências Python

### 📁 **Estrutura de arquivos estáticos:**
```
static/
├── css/
│   └── style.css
├── js/
│   └── script.js
└── images/
    └── fundo.jpg
```

## 🚨 **Problemas Comuns e Soluções:**

### **❌ Imagem de fundo não carrega:**
- ✅ **Solução:** Caminho atualizado para `/static/images/fundo.jpg`
- ✅ **Configuração:** `staticPublishPath: ./static` no `render.yaml`

### **❌ Arquivos estáticos não servem:**
- ✅ **Solução:** `app.config['STATIC_FOLDER'] = 'static'` no `app.py`
- ✅ **Configuração:** `staticRoutes: ['/static']` no `render.yaml`

### **❌ Aplicação não inicia:**
- ✅ **Solução:** Porta configurada via variável de ambiente
- ✅ **Configuração:** `host='0.0.0.0'` para aceitar conexões externas

## 📝 **Passos para Deploy:**

1. **Faça push** do código para o GitHub
2. **Conecte** o repositório ao Render
3. **Configure** as variáveis de ambiente
4. **Deploy automático** será executado
5. **Verifique** se a imagem de fundo carrega

## 🔍 **Verificação Pós-Deploy:**

- ✅ Aplicação acessível via URL do Render
- ✅ Imagem de fundo visível na tela de login
- ✅ CSS e JavaScript funcionando
- ✅ Banco de dados funcionando
- ✅ Sistema de logs funcionando

## 📞 **Suporte:**

Se ainda houver problemas com a imagem de fundo:
1. Verifique se o arquivo `fundo.jpg` está na pasta `static/images/`
2. Confirme se as variáveis de ambiente estão configuradas
3. Verifique os logs do Render para erros específicos
