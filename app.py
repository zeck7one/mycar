from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'carro_secreto_2024'

# ─── CONFIGURAÇÃO ───────────────────────────────────────────────
SENHA = "suasenha123"   # ← MUDE AQUI para sua senha
DB = "carro.db"
# ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            km INTEGER,
            observacao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logado'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── ROTAS ──────────────────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()

    # filtros
    tipo_filtro = request.args.get('tipo', '')
    ordem = request.args.get('ordem', 'data_desc')

    query = 'SELECT * FROM registros'
    params = []
    if tipo_filtro:
        query += ' WHERE tipo = ?'
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
    for row in conn.execute('SELECT tipo, SUM(valor) as total FROM registros GROUP BY tipo').fetchall():
        totais[row['tipo']] = row['total']

    total_geral = sum(totais.values()) if totais else 0

    # último registro de km
    ultimo_km = conn.execute('SELECT km FROM registros WHERE km IS NOT NULL ORDER BY data DESC LIMIT 1').fetchone()
    ultimo_km = ultimo_km['km'] if ultimo_km else None

    conn.close()
    return render_template('index.html',
        registros=registros,
        totais=totais,
        total_geral=total_geral,
        tipo_filtro=tipo_filtro,
        ordem=ordem,
        ultimo_km=ultimo_km,
        logado=session.get('logado', False)
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['senha'] == SENHA:
            session['logado'] = True
            return redirect(url_for('index'))
        flash('Senha incorreta!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('index'))

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    if request.method == 'POST':
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        valor = float(request.form['valor'].replace(',', '.'))
        data = request.form['data']
        km = request.form.get('km') or None
        observacao = request.form.get('observacao') or None

        conn = get_db()
        conn.execute('''
            INSERT INTO registros (tipo, descricao, valor, data, km, observacao)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tipo, descricao, valor, data, km, observacao))
        conn.commit()
        conn.close()
        flash('Registro adicionado com sucesso!')
        return redirect(url_for('index'))

    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('form.html', registro=None, hoje=hoje)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    conn = get_db()
    if request.method == 'POST':
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        valor = float(request.form['valor'].replace(',', '.'))
        data = request.form['data']
        km = request.form.get('km') or None
        observacao = request.form.get('observacao') or None

        conn.execute('''
            UPDATE registros SET tipo=?, descricao=?, valor=?, data=?, km=?, observacao=?
            WHERE id=?
        ''', (tipo, descricao, valor, data, km, observacao, id))
        conn.commit()
        conn.close()
        flash('Registro atualizado!')
        return redirect(url_for('index'))

    registro = conn.execute('SELECT * FROM registros WHERE id=?', (id,)).fetchone()
    conn.close()
    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('form.html', registro=registro, hoje=hoje)

@app.route('/excluir/<int:id>')
@login_required
def excluir(id):
    conn = get_db()
    conn.execute('DELETE FROM registros WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Registro excluído.')
    return redirect(url_for('index'))

# ─── INICIAR ────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("\n🚗  Sistema do Carro rodando!")
    print("👉  Acesse: http://localhost:5000\n")
    app.run(debug=False, host='0.0.0.0', port=5000)
