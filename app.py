from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'carro_secreto_2024'

DB = "carro.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()


    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome_carro TEXT DEFAULT '',
            tema TEXT DEFAULT 'claro',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    

    conn.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            km INTEGER,
            observacao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')

    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('usuario_id'):
            flash('Você precisa estar logado!', 'erro')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── AUTENTICAÇÃO ───────────────────────────────────────────────
@app.route('/mudar-tema/<tema>')
@login_required
def mudar_tema(tema):
    if tema not in ['claro', 'escuro']:
        tema = 'claro'
    
    usuario_id = session['usuario_id']
    conn = get_db()
    conn.execute('UPDATE usuarios SET tema=? WHERE id=?', (tema, usuario_id))
    conn.commit()
    conn.close()
    
    session['tema'] = tema
    return redirect(request.referrer or url_for('index'))


@app.route('/registro', methods=['GET', 'POST'])
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

        if senha != confirma_senha:
            flash('As senhas não conferem!', 'erro')
            return redirect(url_for('registro'))

        if '@' not in email:
            flash('Email inválido!', 'erro')
            return redirect(url_for('registro'))

        conn = get_db()
        try:
            senha_hash = generate_password_hash(senha)
            conn.execute(
                'INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
                (nome, email, senha_hash)
            )
            conn.commit()
            conn.close()
            flash('Conta criada com sucesso! Faça login.', 'sucesso')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Este email já está registrado!', 'erro')
            return redirect(url_for('registro'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Email e senha são obrigatórios!', 'erro')
            return redirect(url_for('login'))

        conn = get_db()
        usuario = conn.execute('SELECT * FROM usuarios WHERE email=?', (email,)).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario['senha'], senha):
            session['usuario_id'] = usuario['id']
            session['nome'] = usuario['nome']
            session['email'] = usuario['email']
            flash(f'Bem-vindo, {usuario["nome"]}!', 'sucesso')
            return redirect(url_for('index'))
        else:
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
    conn = get_db()

    tipo_filtro = request.args.get('tipo', '')
    ordem = request.args.get('ordem', 'data_desc')

    query = 'SELECT * FROM registros WHERE usuario_id=?'
    params = [usuario_id]

    if tipo_filtro:
        query += ' AND tipo=?'
        params.append(tipo_filtro)

    if ordem == 'data_asc':
        query += ' ORDER BY data ASC'
    elif ordem == 'valor_desc':
        query += ' ORDER BY valor DESC'
    elif ordem == 'valor_asc':
        query += ' ORDER BY valor ASC'
    else:
        query += ' ORDER BY data DESC'

    registros = conn.execute(query, params).fetchall()

    # totais por tipo
    totais = {}
    for row in conn.execute('''
        SELECT tipo, SUM(valor) as total FROM registros 
        WHERE usuario_id=? GROUP BY tipo
    ''', (usuario_id,)).fetchall():
        totais[row['tipo']] = row['total']

    total_geral = sum(totais.values()) if totais else 0

    # último KM
    ultimo_km = conn.execute('''
        SELECT km FROM registros WHERE usuario_id=? AND km IS NOT NULL 
        ORDER BY data DESC LIMIT 1
    ''', (usuario_id,)).fetchone()
    ultimo_km = ultimo_km['km'] if ultimo_km else None

    # Nome do carro
    usuario = conn.execute('SELECT nome_carro FROM usuarios WHERE id=?', (usuario_id,)).fetchone()
    nome_carro = usuario['nome_carro'] if usuario else ''

    conn.close()

    return render_template('index.html',
        registros=registros,
        totais=totais,
        total_geral=total_geral,
        tipo_filtro=tipo_filtro,
        ordem=ordem,
        ultimo_km=ultimo_km,
        nome_usuario=session['nome'],
        nome_carro=nome_carro
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

        conn = get_db()
        conn.execute('''
            INSERT INTO registros (usuario_id, tipo, descricao, valor, data, km, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (usuario_id, tipo, descricao, valor, data, km, observacao))
        conn.commit()
        conn.close()

        flash('Registro adicionado com sucesso!', 'sucesso')
        return redirect(url_for('index'))

    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('form.html', registro=None, hoje=hoje)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    usuario_id = session['usuario_id']
    conn = get_db()

    # Verifica se o registro pertence ao usuário
    registro = conn.execute(
        'SELECT * FROM registros WHERE id=? AND usuario_id=?',
        (id, usuario_id)
    ).fetchone()

    if not registro:
        flash('Registro não encontrado!', 'erro')
        conn.close()
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
            conn.close()
            return redirect(url_for('editar', id=id))

        conn.execute('''
            UPDATE registros SET tipo=?, descricao=?, valor=?, data=?, km=?, observacao=?
            WHERE id=? AND usuario_id=?
        ''', (tipo, descricao, valor, data, km, observacao, id, usuario_id))
        conn.commit()
        conn.close()

        flash('Registro atualizado!', 'sucesso')
        return redirect(url_for('index'))

    conn.close()
    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('form.html', registro=registro, hoje=hoje)

@app.route('/excluir/<int:id>')
@login_required
def excluir(id):
    usuario_id = session['usuario_id']
    conn = get_db()

    # Verifica se o registro pertence ao usuário
    registro = conn.execute(
        'SELECT * FROM registros WHERE id=? AND usuario_id=?',
        (id, usuario_id)
    ).fetchone()

    if not registro:
        flash('Registro não encontrado!', 'erro')
        conn.close()
        return redirect(url_for('index'))

    conn.execute('DELETE FROM registros WHERE id=?', (id,))
    conn.commit()
    conn.close()

    flash('Registro excluído.', 'sucesso')
    return redirect(url_for('index'))

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    usuario_id = session['usuario_id']
    conn = get_db()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id=?', (usuario_id,)).fetchone()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        nome_carro = request.form.get('nome_carro', '').strip()

        if not nome:
            flash('Nome é obrigatório!', 'erro')
        else:
            conn.execute(
                'UPDATE usuarios SET nome=?, nome_carro=? WHERE id=?',
                (nome, nome_carro, usuario_id)
            )
            conn.commit()
            session['nome'] = nome
            flash('Perfil atualizado!', 'sucesso')
            return redirect(url_for('perfil'))

    conn.close()
    return render_template('perfil.html', usuario=usuario)

# ─── INICIAR ────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("\n🚗  Sistema do Carro rodando!")
    print("👉  Acesse: http://localhost:5000\n")
    app.run(debug=False, host='0.0.0.0', port=5000)