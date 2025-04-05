from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import session, Flask, render_template, request, redirect, url_for
from markupsafe import Markup
import mysql.connector
from database import conectar
from datetime import datetime, timedelta

app = Flask(__name__)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT senha_hash, aprovado FROM usuarios_admin WHERE usuario = %s", (usuario,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            senha_hash, aprovado = resultado
            if not aprovado:
                return render_template('login.html', erro='Seu cadastro ainda não foi aprovado.')
            if check_password_hash(senha_hash, senha):
                session['logado'] = True
                return redirect(url_for('admin'))

        return render_template('login.html', erro='Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

app.secret_key = 'chave_super_secreta_123'

@app.route('/', methods=['GET', 'POST'])
def index():
    mensagem = None
    if request.method == 'POST':
        cpf = request.form['cpf']
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, praca FROM entregadores WHERE cpf = %s", (cpf,))
        entregador = cursor.fetchone()

        if not entregador:
            mensagem = 'CPF não encontrado.'
            return render_template('agendamento.html', mensagem=mensagem)

        nome, praca = entregador
        subpraca = None  # Subpraça não é obrigatória

        hoje = datetime.now()
        if hoje.hour < 19 or hoje.hour >= 21:
            mensagem = 'Agendamentos disponíveis apenas das 19h às 21h.'
            return render_template('agendamento.html', mensagem=mensagem)

        data_turno = (hoje.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).date()

        cursor.execute("""
            SELECT DISTINCT data_turno FROM vagas
            WHERE praca = %s AND data_turno = %s
        """, (praca, data_turno))
        datas_disponiveis = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT turno FROM vagas
            WHERE praca = %s AND data_turno = %s
        """, (praca, data_turno))
        turnos_disponiveis = [row[0] for row in cursor.fetchall()]

        conn.close()

        return render_template('agendamento.html', nome=nome, cpf=cpf, praca=praca, subpraca=subpraca,
                               datas=datas_disponiveis, turnos=turnos_disponiveis, mensagem=mensagem)

    return render_template('agendamento.html', mensagem=mensagem)

@app.route('/confirmar', methods=['POST'])
def confirmar_agendamento():
    cpf = request.form['cpf']
    data_turno = request.form['data']
    subpraca = request.form.get('subpraca')
    turnos_selecionados = request.form.getlist('turnos')

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT nome, praca FROM entregadores WHERE cpf = %s", (cpf,))
    entregador = cursor.fetchone()
    if not entregador:
        conn.close()
        return render_template('agendamento.html', mensagem='Entregador não encontrado.')

    nome, praca = entregador
    mensagens = []

    for turno in turnos_selecionados:
        # Verifica se já tem agendamento
        cursor.execute("""
            SELECT COUNT(*) FROM agendamentos
            WHERE cpf = %s AND data_turno = %s AND turno = %s
        """, (cpf, data_turno, turno))
        if cursor.fetchone()[0] > 0:
            mensagens.append(f"<p style='color:orange;'>⚠️ Turno {turno} já agendado.</p>")
            continue

        # Verifica se tem vaga
        cursor.execute("""
            SELECT vagas_total FROM vagas
            WHERE praca = %s AND data_turno = %s AND turno = %s
        """, (praca, data_turno, turno))
        vagas = cursor.fetchone()
        if not vagas or vagas[0] <= 0:
            mensagens.append(f"<p style='color:red;'>❌ Turno {turno} sem vagas disponíveis.</p>")
            continue

        # Realiza agendamento
        cursor.execute("""
            INSERT INTO agendamentos (nome, cpf, praca, subpraca, data_turno, turno)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nome, cpf, praca, subpraca, data_turno, turno))

        cursor.execute("""
            UPDATE vagas SET vagas_total = vagas_total - 1
            WHERE praca = %s AND data_turno = %s AND turno = %s
        """, (praca, data_turno, turno))

        mensagens.append(f"<p style='color:green;'>✅ Turno {turno} agendado com sucesso.</p>")

    conn.commit()
    conn.close()

    return render_template('agendamento.html', mensagem=Markup(''.join(mensagens)))

@app.route('/admin')
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))
    filtro_data = request.args.get('data')
    filtro_turno = request.args.get('turno')
    filtro_subpraca = request.args.get('subpraca')

    conn = conectar()
    cursor = conn.cursor()

    query = "SELECT id, nome, cpf, praca, subpraca, data_turno, turno FROM agendamentos WHERE 1=1"
    filtros = []

    if filtro_data:
        query += " AND data_turno = %s"
        filtros.append(filtro_data)
    if filtro_turno:
        query += " AND turno = %s"
        filtros.append(filtro_turno)
    if filtro_subpraca:
        query += " AND subpraca = %s"
        filtros.append(filtro_subpraca)

    query += " ORDER BY data_turno DESC, turno"

    cursor.execute(query, tuple(filtros))
    agendamentos = cursor.fetchall()

    cursor.execute("SELECT DISTINCT data_turno FROM agendamentos ORDER BY data_turno DESC")
    datas = [row[0].strftime('%Y-%m-%d') for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT turno FROM agendamentos")
    turnos = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT subpraca FROM agendamentos")
    subpracas = [row[0] for row in cursor.fetchall() if row[0] is not None]

    cpfs = [row[2] for row in agendamentos]
    cpfs_formatados = ', '.join([f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" for cpf in cpfs])

    conn.close()

    return render_template('admin.html', agendamentos=agendamentos, datas=datas, turnos=turnos,
                           subpracas=subpracas, filtro_data=filtro_data, filtro_turno=filtro_turno,
                           filtro_subpraca=filtro_subpraca, cpfs_formatados=cpfs_formatados)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    mensagem = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        nome_completo = request.form['nome_completo']
        setor = request.form.get('setor')
        cargo = request.form.get('cargo')
        senha_hash = generate_password_hash(senha)

        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO usuarios_admin (usuario, senha_hash, nome_completo, setor, cargo, aprovado)
                VALUES (%s, %s, %s, %s, %s, FALSE)
            """, (usuario, senha_hash, nome_completo, setor, cargo))
            conn.commit()
            mensagem = "Cadastro enviado! Aguarde aprovação do administrador."
        except mysql.connector.errors.IntegrityError:
            mensagem = "Usuário já existe. Escolha outro nome de usuário."
        finally:
            conn.close()

    return render_template('cadastrar.html', mensagem=mensagem)



@app.route('/admin/usuarios')
def admin_usuarios():
    if not session.get('logado'):
        return redirect(url_for('login'))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, usuario, senha_hash, nome_completo, setor, cargo FROM usuarios_admin WHERE aprovado = FALSE")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/admin/usuarios/aprovar', methods=['POST'])
def aprovar_usuario():
    if not session.get('logado'):
        return redirect(url_for('login'))

    user_id = request.form['id']
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios_admin SET aprovado = TRUE WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_usuarios'))


@app.route('/admin/usuarios/excluir', methods=['POST'])
def excluir_usuario():
    if not session.get('logado'):
        return redirect(url_for('login'))

    user_id = request.form['id']
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios_admin WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_usuarios'))




@app.route('/admin/turnos')
def painel_turnos():
    if not session.get('logado'):
        return redirect(url_for('login'))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM turnos ORDER BY data_turno, praca, subpraca, turno")
    turnos = cursor.fetchall()

    cursor.execute("SELECT DISTINCT praca FROM turnos ORDER BY praca")
    pracas = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT subpraca FROM turnos ORDER BY subpraca")
    subpracas = [row[0] for row in cursor.fetchall() if row[0]]

    conn.close()
    return render_template('turnos.html', turnos=turnos, pracas=pracas, subpracas=subpracas)


@app.route('/admin/turnos/atualizar', methods=['POST'])
def atualizar_turno():
    if not session.get('logado'):
        return redirect(url_for('login'))

    turno_id = request.form['id']
    vagas_total = request.form['vagas_total']

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE turnos SET vagas_total = %s WHERE id = %s", (vagas_total, turno_id))
    conn.commit()
    conn.close()
    return redirect(url_for('painel_turnos'))


@app.route('/admin/turnos/adicionar', methods=['POST'])
def adicionar_turno():
    if not session.get('logado'):
        return redirect(url_for('login'))

    data_turno = request.form['data_turno']
    praca = request.form['praca']
    subpraca = request.form['subpraca']
    turno = request.form['turno']
    vagas_total = request.form['vagas_total']

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO turnos (data_turno, praca, subpraca, turno, vagas_total)
        VALUES (%s, %s, %s, %s, %s)
    """, (data_turno, praca, subpraca, turno, vagas_total))
    conn.commit()
    conn.close()
    return redirect(url_for('painel_turnos'))




@app.route('/admin/turnos/duplicar', methods=['POST'])
def duplicar_turnos():
    if not session.get('logado'):
        return redirect(url_for('login'))

    praca = request.form['praca']
    subpraca = request.form.get('subpraca')
    modo = request.form['modo']

    conn = conectar()
    cursor = conn.cursor()

    if modo == '1_15':
        cursor.execute("""
            SELECT data_turno, praca, subpraca, turno, vagas_total
            FROM turnos
            WHERE DAY(data_turno) BETWEEN 1 AND 15
              AND praca = %s
              AND (%s = '' OR subpraca = %s)
        """, (praca, subpraca, subpraca))
        dias_add = 15
    elif modo == '16_30':
        cursor.execute("""
            SELECT data_turno, praca, subpraca, turno, vagas_total
            FROM turnos
            WHERE DAY(data_turno) BETWEEN 16 AND 31
              AND praca = %s
              AND (%s = '' OR subpraca = %s)
        """, (praca, subpraca, subpraca))
        dias_add = 16  # vai para o mês seguinte

    turnos_ref = cursor.fetchall()

    novos_turnos = []
    for row in turnos_ref:
        nova_data = row[0] + timedelta(days=dias_add)
        cursor.execute("""
            SELECT COUNT(*) FROM turnos
            WHERE data_turno = %s AND praca = %s AND subpraca = %s AND turno = %s
        """, (nova_data, row[1], row[2], row[3]))
        existe = cursor.fetchone()[0]
        if existe == 0:
            novos_turnos.append((nova_data, row[1], row[2], row[3], row[4]))

    if novos_turnos:
        cursor.executemany("""
            INSERT INTO turnos (data_turno, praca, subpraca, turno, vagas_total)
            VALUES (%s, %s, %s, %s, %s)
        """, novos_turnos)
        conn.commit()

    conn.close()
    return redirect(url_for('painel_turnos'))


if __name__ == '__main__':
    app.run(debug=True)







