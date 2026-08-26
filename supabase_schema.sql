-- ─────────────────────────────────────────────────────────────
-- Execute este script UMA VEZ no Supabase:
-- Painel do Supabase → SQL Editor → New query → cole isto → Run
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    nome_carro TEXT DEFAULT '',
    tema TEXT DEFAULT 'claro',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registros (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    tipo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    data TEXT NOT NULL,
    km INTEGER,
    observacao TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────────────────────
-- IMPORTANTE: Row Level Security (RLS)
-- ─────────────────────────────────────────────────────────────
-- Por padrão, o Supabase ativa RLS em tabelas novas criadas pela
-- interface, mas tabelas criadas via SQL Editor ficam SEM RLS,
-- ou seja, totalmente abertas pra leitura/escrita via API pública.
--
-- Como este app usa a service_role key (acesso via backend, não
-- pelo navegador do usuário final), a service_role key ignora RLS
-- de qualquer forma — então tecnicamente não é obrigatório.
--
-- MAS, por segurança (caso a anon key seja exposta ou usada por
-- engano em algum lugar), é uma boa prática habilitar RLS e
-- bloquear acesso direto, já que toda a lógica de autorização
-- deste app vive no Flask, não no Supabase:

ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE registros ENABLE ROW LEVEL SECURITY;

-- Sem nenhuma policy criada, RLS ativado = ninguém acessa via
-- anon key. Apenas a service_role key (usada pelo seu Flask)
-- continua funcionando normalmente.
