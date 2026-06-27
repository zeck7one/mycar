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

| Categoria       | Uso                            |
| --------------- | ------------------------------ |
| ⛽ Combustível | Abastecimentos                 |
| 🔧 Manutenção | Revisões, troca de óleo, etc |
| ⚙️ Peça      | Peças compradas ou trocadas   |
| 📋 Outros       | IPVA, seguro, lavagem, etc     |




MELHORIAS:

**00:10**

Aqui estão ideias pra melhorar MEU projeto:

---

### 🎨 **Interface & UX**

* **Dashboard com gráficos** — mostrar gastos por mês/tipo com Chart.js
* **Tema escuro/claro** — toggle de tema salvo no banco
* **Responsivo mobile** — melhorar layout em celular
* **Ícones** — adicionar ícones com Font Awesome
* **Notificações** — toast notifications mais elegantes

---

### 📊 **Funcionalidades**

* **Relatórios PDF** — gerar PDF com gastos do período
* **Exportar CSV/Excel** — baixar dados em planilha
* **Manutenções agendadas** — alertar quando é hora de trocar óleo, pneus, etc
* **Múltiplos carros** — cada usuário pode ter vários carros
* **Fotos dos recibos** — upload de comprovantes
* **Categorias personalizadas** — criar tipos customizados

---

### 🔒 **Segurança**

* **2FA (autenticação dupla)** — verificação por email/SMS
* **Recuperação de senha** — reset por email
* **Backup automático** — salvar dados na nuvem
* **Rate limiting** — evitar brute force
* **Criptografia de dados sensíveis** — criptografar valores

---

### ⚡ **Performance & Deploy**

* **PostgreSQL** — trocar SQLite para melhor escalabilidade
* **Cache** — cachear totais/estatísticas
* **Paginação** — se tiver muitos registros
* **Índices no banco** — speedup nas buscas
* **Subir na nuvem** — Railway, Render, Vercel, etc

---

### 🤖 **Automação**

* **Lembrete por email** — avisar sobre manutenções
* **API** — permitir que app mobile acesse dados
* **Integração com APIs** — preço do combustível, FIPE do carro
* **Importação automática** — ler SMS/email de despesas

---

### 📱 **App Mobile**

* **Progressive Web App (PWA)** — funciona offline
* **Flutter/React Native** — app nativo

---

### 🎯 **O que eu recomendo começar:**

**Curto prazo (fácil):**

1. Gráficos com Chart.js
2. Tema escuro
3. Exportar CSV
4. Recuperação de senha

**Médio prazo (médio):**
5. Múltiplos carros
6. Upload de fotos
7. Relatórios PDF
8. 2FA

**Longo prazo (complexo):**
9. PostgreSQL
10. API REST
11. App mobile
