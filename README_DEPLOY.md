# Deploy na Railway com Supabase

## 1. Antes de subir pro GitHub

- Confirme que o arquivo `.env` **não** está sendo commitado (o `.gitignore` já cuida disso, mas dá uma olhada com `git status`).
- Se você já tinha um `carro.db` (SQLite) commitado antes, pode deletar — não é mais usado.

## 2. Na Railway

1. Crie um novo projeto → "Deploy from GitHub repo" → selecione este repositório.
2. A Railway vai detectar o `Procfile` automaticamente e usar o Gunicorn.
3. Vá em **Variables** e adicione:
   - `SECRET_KEY` → gere com `python -c "import secrets; print(secrets.token_hex(32))"`
   - `DATABASE_URL` → a connection string do Supabase (veja abaixo)
   - `FLASK_ENV` → `production`
4. A Railway já define `PORT` automaticamente — não precisa adicionar essa.

## 3. Pegando a DATABASE_URL no Supabase

No painel do Supabase:
`Project Settings` → `Database` → `Connection string` → aba **URI**

Vai parecer com isso:
```
postgresql://postgres:[SUA-SENHA]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
```

⚠️ Troque `[SUA-SENHA]` pela senha real do banco (a que você definiu ao criar o projeto Supabase, ou redefina em Database → Settings).

**Dica:** o Supabase também oferece a opção "Connection pooling" (porta 6543 em vez de 5432) — recomendado para apps com várias conexões simultâneas, como é o caso aqui com Gunicorn rodando 4 workers. Se notar erros de "too many connections", troque para a URI do pooler.

## 4. Primeira execução

Na primeira vez que o app rodar, a função `init_db()` cria as tabelas automaticamente no Postgres do Supabase (`usuarios` e `registros`). Você pode confirmar isso no painel do Supabase em `Table Editor`.

## 5. Testando localmente antes do deploy (opcional, mas recomendado)

```bash
cp .env.example .env
# edite o .env com sua SECRET_KEY e DATABASE_URL real
pip install -r requirements.txt
python app.py
```

Acesso `http://localhost:5000`.
