# 🚗 Sistema de Controle do Carro

Controle todos os gastos e manutenções do seu carro em um sistema web local.

---

## ✅ Pré-requisitos

- Python 3.8 ou superior instalado
- Pip (geralmente já vem com o Python)

---

## 🚀 Como instalar e rodar

### 1. Instalar dependências
Abra o terminal/prompt dentro da pasta do projeto e rode:

```
pip install flask
```

### 2. Definir sua senha
Abra o arquivo `app.py` e mude a linha:

```python
SENHA = "suasenha123"   # ← MUDE AQUI
```

Troque `suasenha123` pela senha que você quiser.

### 3. Rodar o sistema
```
python app.py
```

### 4. Acessar
Abra o navegador e acesse:
```
http://localhost:5000
```

---

## 📱 Acessar de outro dispositivo na mesma rede Wi-Fi

1. Descubra o IP do seu PC:
   - Windows: abra o Prompt e digite `ipconfig` → anote o "Endereço IPv4"
   - Linux/Mac: `ip a` ou `ifconfig`

2. No celular ou outro PC da mesma rede, acesse:
   ```
   http://SEU_IP:5000
   ```
   Exemplo: `http://192.168.1.100:5000`

---

## 📁 Estrutura dos arquivos

```
carro_app/
├── app.py              ← Servidor principal (mude a senha aqui)
├── requirements.txt    ← Dependências
├── carro.db            ← Banco de dados (criado automaticamente)
└── templates/
    ├── index.html      ← Página principal
    ├── login.html      ← Tela de login
    └── form.html       ← Formulário de adicionar/editar
```

---

## 🔐 Sobre a segurança

- Sem login: qualquer pessoa **visualiza** os registros
- Com login: só você pode **adicionar, editar e excluir**
- O banco de dados fica salvo no arquivo `carro.db` localmente

---

## 🗂️ Categorias de registro

| Categoria | Uso |
|-----------|-----|
| ⛽ Combustível | Abastecimentos |
| 🔧 Manutenção | Revisões, troca de óleo, etc |
| ⚙️ Peça | Peças compradas ou trocadas |
| 📋 Outros | IPVA, seguro, lavagem, etc |
