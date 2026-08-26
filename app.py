from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
import os
import sys
import logging
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Carrega variáveis do arquivo .env (não versionado no git)
load_dotenv()

app = Flask(__name__)

# ─── SECRET KEY ──────────────────────────────────────────────────
# Em produção, a SECRET_KEY DEVE vir de variável de ambiente, nunca
# hardcoded no código. Se não existir no .env, o app nem inicia —
# é melhor falhar alto e claro do que rodar inseguro silenciosamente.
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY não definida! Crie um arquivo .env com:\n'
        'SECRET_KEY=<valor aleatório longo>\n'
        'Gere um valor com: python -c "import secrets; print(secrets.token_hex(32))"'
    )
app.secret_key = SECRET_KEY

# ─── CONFIGURAÇÃO DE COOKIES DE SESSÃO ──────────────────────────
# HttpOnly: JavaScript não consegue ler o cookie (protege contra XSS roubando sessão)
# SameSite=Lax: o navegador não envia o cookie em requisições cross-site (protege contra CSRF básico)
# Secure: só ativa em produção (HTTPS) — em dev/HTTP local quebraria o login
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'

# ─── BANCO DE DADOS (Supabase) ──────────────────────────────────
# SUPABASE_URL: Project Settings > Data API > Project URL
# SUPABASE_KEY: Project Settings > API Keys > service_role (secret)
#
# IMPORTANTE: use a service_role key, NÃO a anon/public key.
# A service_role key tem acesso total ao banco (ignora Row Level
# Security) — é a chave certa pra um backend confiável como este
# Flask, que já faz sua própria verificação de login e permissões
# antes de tocar no banco. A anon key é pra uso direto no navegador
# do cliente, o que não é o caso aqui.
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        'SUPABASE_URL e/ou SUPABASE_KEY não definidas! Configure no .env\n'
        '(local) ou nas Variables do projeto na Railway.\n'
        'SUPABASE_URL: Project Settings > Data API > Project URL\n'
        'SUPABASE_KEY: Project Settings > API Keys > service_role (secret)'
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── LOGGING ─────────────────────────────────────────────────────
# Na Railway o filesystem é efêmero (reinicia/perde dados a cada deploy
# ou restart), então logar em arquivo não garante persistência. A Railway
# captura automaticamente tudo que vai pro stdout/stderr e mostra na aba
# "Logs" do projeto — por isso logamos direto pra lá, sem RotatingFileHandler.
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
app.logger.setLevel(logging.INFO)

# ─── RATE LIMITING ───────────────────────────────────────────────
# Protege contra brute force: limita quantas tentativas de login/registro
# um mesmo IP pode fazer em um período de tempo.
# Observação: storage_uri="memory://" guarda os contadores na memória do
# próprio processo. Como a Railway pode reiniciar o container (deploy,
# restart, crash), os contadores zeram nesses momentos — não é um bug,
# é uma limitação aceitável pra esse tamanho de projeto. Se no futuro
# quiser persistir entre restarts, dá pra apontar pro Redis.
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


# ─── NOTA SOBRE init_db() ────────────────────────────────────────
# O SDK supabase-py não cria tabelas (ele só consulta/insere/atualiza
# dados em tabelas que já existem). A criação das tabelas 'usuarios'
# e 'registros' deve ser feita UMA VEZ, direto no painel do Supabase:
# SQL Editor > cole o conteúdo de supabase_schema.sql > Run.
# Por isso não existe mais uma função init_db() chamada no final
# deste arquivo.


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('usuario_id'):
            flash('Você precisa estar logado!', 'erro')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def senha_e_forte(senha):
    """
    Validação básica de força de senha, além do mínimo de 6 caracteres.
    Exige pelo menos 1 letra e 1 número, e bloqueia senhas óbvias comuns.
    Retorna (True, '') se ok, ou (False, 'motivo') se não.
    """
    SENHAS_COMUNS = {'123456', '1234567', '12345678', '123456789', 'senha123',
                      'password', 'qwerty123', '11111111', '00000000', 'abc12345'}

    if senha.lower() in SENHAS_COMUNS:
        return False, 'Essa senha é muito comum, escolha outra.'

    tem_letra = any(c.isalpha() for c in senha)
    tem_numero = any(c.isdigit() for c in senha)

    if not (tem_letra and tem_numero):
        return False, 'A senha deve ter pelo menos uma letra e um número.'

    return True, ''


# KM máximo aceito. 2 milhões de km está bem acima de qualquer carro
# real (mesmo carros muito antigos raramente passam de 1 milhão), mas
# fica dentro do limite seguro do tipo INTEGER do Postgres (~2,1 bilhões),
# evitando o erro "value out of range" caso alguém digite um número
# absurdo por engano (ex: dedo encostando em teclas extras).
KM_MAXIMO = 2_000_000


def km_valido(km_str):
    """
    Valida o campo KM antes de mandar pro banco.
    Retorna (km_int_ou_None, mensagem_erro). Se mensagem_erro for '',
    a validação passou e km_int_ou_None é o valor pronto pra salvar
    (ou None, se o campo estava vazio — KM é opcional).
    """
    if not km_str:
        return None, ''

    try:
        km_int = int(km_str)
    except ValueError:
        return None, 'KM deve ser um número inteiro válido.'

    if km_int < 0:
        return None, 'KM não pode ser negativo.'

    if km_int > KM_MAXIMO:
        return None, f'KM muito alto (máximo {KM_MAXIMO:,} km). Verifique o valor digitado.'.replace(',', '.')

    return km_int, ''


# ─── AUTENTICAÇÃO ───────────────────────────────────────────────
@app.route('/mudar-tema/<tema>')
@login_required
def mudar_tema(tema):
    if tema not in ['claro', 'escuro']:
        tema = 'claro'

    usuario_id = session['usuario_id']
    supabase.table('usuarios').update({'tema': tema}).eq('id', usuario_id).execute()

    session['tema'] = tema
    return redirect(request.referrer or url_for('index'))


@app.route('/registro', methods=['GET', 'POST'])
@limiter.limit("10 per hour")  # limita criação de contas pelo mesmo IP
def registro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirma_senha = request.form.get('confirma_senha', '')

        # Validações
        if not nome or not email or not senha:
            flash('Todos os campos são obrigatórios!', 'erro')
            return redirect(url_for('registro'))

        if len(senha) < 6:
            flash('A senha deve ter no mínimo 6 caracteres!', 'erro')
            return redirect(url_for('registro'))

        senha_ok, motivo = senha_e_forte(senha)
        if not senha_ok:
            flash(motivo, 'erro')
            return redirect(url_for('registro'))

        if senha != confirma_senha:
            flash('As senhas não conferem!', 'erro')
            return redirect(url_for('registro'))

        if '@' not in email:
            flash('Email inválido!', 'erro')
            return redirect(url_for('registro'))

        # Verifica se o email já existe (o SDK não tem "IntegrityError"
        # automático como o sqlite3/psycopg2 — checamos manualmente antes)
        existe = supabase.table('usuarios').select('id').eq('email', email).execute()
        if existe.data:
            flash('Este email já está registrado!', 'erro')
            return redirect(url_for('registro'))

        senha_hash = generate_password_hash(senha)
        supabase.table('usuarios').insert({
            'nome': nome,
            'email': email,
            'senha': senha_hash
        }).execute()

        app.logger.info(f'Nova conta criada: {email}')
        flash('Conta criada com sucesso! Faça login.', 'sucesso')
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # protege contra brute force de senha
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Email e senha são obrigatórios!', 'erro')
            return redirect(url_for('login'))

        resultado = supabase.table('usuarios').select('*').eq('email', email).execute()
        usuario = resultado.data[0] if resultado.data else None

        if usuario and check_password_hash(usuario['senha'], senha):
            session['usuario_id'] = usuario['id']
            session['nome'] = usuario['nome']
            session['email'] = usuario['email']
            app.logger.info(f'Login bem-sucedido: {email}')
            flash(f'Bem-vindo, {usuario["nome"]}!', 'sucesso')
            return redirect(url_for('index'))
        else:
            app.logger.warning(f'Tentativa de login falhou para: {email}')
            flash('Email ou senha incorretos!', 'erro')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Deslogado com sucesso!', 'sucesso')
    return redirect(url_for('login'))


# ─── PÁGINAS PRINCIPAIS ─────────────────────────────────────────

@app.route('/')
@login_required
def index():
    usuario_id = session['usuario_id']

    tipo_filtro = request.args.get('tipo', '')
    ordem = request.args.get('ordem', 'data_desc')

    query = supabase.table('registros').select('*').eq('usuario_id', usuario_id)

    if tipo_filtro:
        query = query.eq('tipo', tipo_filtro)

    if ordem == 'data_asc':
        query = query.order('data', desc=False)
    elif ordem == 'valor_desc':
        query = query.order('valor', desc=True)
    elif ordem == 'valor_asc':
        query = query.order('valor', desc=False)
    else:
        query = query.order('data', desc=True)

    registros = query.execute().data

    # totais por tipo
    # O SDK não tem "GROUP BY" embutido de forma simples, então
    # buscamos todos os registros do usuário e somamos em Python.
    todos = supabase.table('registros').select('tipo, valor').eq('usuario_id', usuario_id).execute().data
    totais = {}
    for row in todos:
        totais[row['tipo']] = totais.get(row['tipo'], 0) + row['valor']

    total_geral = sum(totais.values()) if totais else 0

    # último KM
    ultimo = supabase.table('registros') \
        .select('km') \
        .eq('usuario_id', usuario_id) \
        .not_.is_('km', 'null') \
        .order('data', desc=True) \
        .limit(1) \
        .execute().data
    ultimo_km = ultimo[0]['km'] if ultimo else None

    # Nome do carro
    usuario = supabase.table('usuarios').select('nome_carro').eq('id', usuario_id).execute().data
    nome_carro = usuario[0]['nome_carro'] if usuario else ''

    return render_template('index.html',
        registros=registros,
        totais=totais,
        total_geral=total_geral,
        tipo_filtro=tipo_filtro,
        ordem=ordem,
        ultimo_km=ultimo_km,
        nome_usuario=session['nome'],
        nome_carro=nome_carro,
        logado=True  # <-- ADICIONADO: o template index.html usa {% if logado %}
                      # para decidir se mostra os botões de Adicionar/Editar/Configurar.
                      # Como essa rota só é acessada se o usuário já passou pelo
                      # @login_required, aqui SEMPRE é True.
    )


@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    usuario_id = session['usuario_id']

    if request.method == 'POST':
        tipo = request.form.get('tipo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        valor = request.form.get('valor', '0').replace(',', '.')
        data = request.form.get('data', '')
        km = request.form.get('km') or None
        observacao = request.form.get('observacao', '').strip() or None

        if not tipo or not descricao or not valor or not data:
            flash('Preencha todos os campos obrigatórios!', 'erro')
            return redirect(url_for('adicionar'))

        try:
            valor = float(valor)
        except ValueError:
            flash('Valor inválido!', 'erro')
            return redirect(url_for('adicionar'))

        km_int, erro_km = km_valido(km)
        if erro_km:
            flash(erro_km, 'erro')
            return redirect(url_for('adicionar'))

        supabase.table('registros').insert({
            'usuario_id': usuario_id,
            'tipo': tipo,
            'descricao': descricao,
            'valor': valor,
            'data': data,
            'km': km_int,
            'observacao': observacao
        }).execute()

        flash('Registro adicionado com sucesso!', 'sucesso')
        return redirect(url_for('index'))

    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('form.html', registro=None, hoje=hoje)


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    usuario_id = session['usuario_id']

    # Verifica se o registro pertence ao usuário
    resultado = supabase.table('registros').select('*').eq('id', id).eq('usuario_id', usuario_id).execute()
    registro = resultado.data[0] if resultado.data else None

    if not registro:
        flash('Registro não encontrado!', 'erro')
        return redirect(url_for('index'))

    if request.method == 'POST':
        tipo = request.form.get('tipo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        valor = request.form.get('valor', '0').replace(',', '.')
        data = request.form.get('data', '')
        km = request.form.get('km') or None
        observacao = request.form.get('observacao', '').strip() or None

        try:
            valor = float(valor)
        except ValueError:
            flash('Valor inválido!', 'erro')
            return redirect(url_for('editar', id=id))

        km_int, erro_km = km_valido(km)
        if erro_km:
            flash(erro_km, 'erro')
            return redirect(url_for('editar', id=id))

        supabase.table('registros').update({
            'tipo': tipo,
            'descricao': descricao,
            'valor': valor,
            'data': data,
            'km': km_int,
            'observacao': observacao
        }).eq('id', id).eq('usuario_id', usuario_id).execute()

        flash('Registro atualizado!', 'sucesso')
        return redirect(url_for('index'))

    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('form.html', registro=registro, hoje=hoje)


@app.route('/excluir/<int:id>')
@login_required
def excluir(id):
    usuario_id = session['usuario_id']

    # Verifica se o registro pertence ao usuário
    resultado = supabase.table('registros').select('id').eq('id', id).eq('usuario_id', usuario_id).execute()
    if not resultado.data:
        flash('Registro não encontrado!', 'erro')
        return redirect(url_for('index'))

    supabase.table('registros').delete().eq('id', id).execute()

    flash('Registro excluído.', 'sucesso')
    return redirect(url_for('index'))


@app.route('/configurar', methods=['GET', 'POST'])
@login_required
def configurar():
    usuario_id = session['usuario_id']

    if request.method == 'POST':
        nome_carro = request.form.get('nome_carro', '').strip()

        supabase.table('usuarios').update({'nome_carro': nome_carro}).eq('id', usuario_id).execute()

        flash('Nome do carro atualizado!', 'sucesso')
        return redirect(url_for('index'))

    # GET: busca o nome atual pra preencher o campo no formulário
    resultado = supabase.table('usuarios').select('nome_carro').eq('id', usuario_id).execute()
    nome_atual = resultado.data[0]['nome_carro'] if resultado.data else ''

    return render_template('configurar.html', nome_atual=nome_atual)


@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    usuario_id = session['usuario_id']
    resultado = supabase.table('usuarios').select('*').eq('id', usuario_id).execute()
    usuario = resultado.data[0] if resultado.data else None

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        nome_carro = request.form.get('nome_carro', '').strip()

        if not nome:
            flash('Nome é obrigatório!', 'erro')
        else:
            supabase.table('usuarios').update({
                'nome': nome,
                'nome_carro': nome_carro
            }).eq('id', usuario_id).execute()
            session['nome'] = nome
            flash('Perfil atualizado!', 'sucesso')
            return redirect(url_for('perfil'))

    return render_template('perfil.html', usuario=usuario)


# ─── INICIAR ────────────────────────────────────────────────────
# Em DESENVOLVIMENTO (sua máquina), rode normalmente:
#     python app.py
#
# Em PRODUÇÃO (Railway), o Procfile já configura o Gunicorn pra
# rodar o app — NÃO é o app.run() abaixo que é usado lá. O comando
# usado em produção é:
#     gunicorn -w 4 -b 0.0.0.0:$PORT app:app
#
if __name__ == '__main__':
    # PORT vem da variável de ambiente em produção (Railway define isso
    # automaticamente). Localmente, cai no 5000 por padrão.
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    print("\n🚗  Sistema do Carro rodando em modo desenvolvimento!")
    print(f"👉  Acesse: http://localhost:{port}\n")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)