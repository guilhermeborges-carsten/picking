from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session, flash
from datetime import datetime
import os
import sqlite3
import pandas as pd
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Configurações
DATABASE = 'cadastro_clientes.db'
CLIENTES = ["YPÊ", "LIDER", "SELMI", "BRITVIC", "MARS", "FUGINI", "BAUDUCCO", 
            "BARILLA", "MOCOCA", "J MACEDO", "CEPERA", "MDIAS", "RECKITT"]

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabela de clientes (nova tabela)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            codigo VARCHAR(20) UNIQUE,
            ativo BOOLEAN DEFAULT 1,
            data_cadastro DATE DEFAULT CURRENT_DATE
        )
        ''')
        
        # Tabela de usuários (mantida como estava)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            nome VARCHAR(100),
            cargo VARCHAR(50),
            admin BOOLEAN DEFAULT 0,
            ativo BOOLEAN DEFAULT 1
        )
        ''')
        
        # Tabela de cadastros (mantida como estava)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tb_pck_arm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE NOT NULL,
            cliente_id INTEGER,
            mod_carsten VARCHAR(20),
            mod_3 VARCHAR(20),
            total_volumes VARCHAR(20),
            vol_pessoas VARCHAR(20),
            usuario_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
        ''')
        
        # Tabela de colaboradores Carsten
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores_carsten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            cargo VARCHAR(100) NOT NULL,
            departamento VARCHAR(100) NOT NULL,
            data_contratacao DATE NOT NULL,
            ativo BOOLEAN DEFAULT 1,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de logs do sistema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sistema_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario_id INTEGER,
            usuario_nome VARCHAR(100),
            acao VARCHAR(100) NOT NULL,
            modulo VARCHAR(100) NOT NULL,
            detalhes TEXT,
            ip_address VARCHAR(45),
            user_agent TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        ''')
        
        # Inserir clientes padrão se não existirem
        clientes_padrao = ["YPÊ", "LIDER", "SELMI", "BRITVIC", "MARS", 
                          "FUGINI", "BAUDUCCO", "BARILLA", "MOCOCA", 
                          "J MACEDO", "CEPERA", "MDIAS", "RECKITT"]
        
        for cliente in clientes_padrao:
            cursor.execute('SELECT id FROM clientes WHERE nome = ?', (cliente,))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO clientes (nome) VALUES (?)', (cliente,))
        
        # Restante da inicialização...
        conn.commit()
        conn.close()

from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def validar_data(data_texto):
    try:
        datetime.strptime(data_texto, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def registrar_log(acao, modulo, detalhes="", usuario_id=None, usuario_nome=None):
    """Registra uma ação no sistema de logs"""
    try:
        conn = get_db_connection()
        
        # Obter informações do usuário se não fornecidas
        if usuario_id is None and 'user_id' in session:
            usuario_id = session['user_id']
            usuario_nome = session.get('username', 'Desconhecido')
        
        # Obter IP e User Agent
        ip_address = request.remote_addr if request else 'N/A'
        user_agent = request.headers.get('User-Agent', 'N/A') if request else 'N/A'
        
        conn.execute('''
            INSERT INTO sistema_logs 
            (usuario_id, usuario_nome, acao, modulo, detalhes, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (usuario_id, usuario_nome, acao, modulo, detalhes, ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        # Se falhar ao registrar log, não interromper a aplicação
        print(f"Erro ao registrar log: {str(e)}")

def obter_logs(filtros=None, pagina=1, por_pagina=50):
    """Obtém logs do sistema com filtros e paginação"""
    try:
        conn = get_db_connection()
        
        query = '''
            SELECT l.*, u.username as username
            FROM sistema_logs l
            LEFT JOIN usuarios u ON l.usuario_id = u.id
        '''
        
        params = []
        where_clauses = []
        
        if filtros:
            if filtros.get('usuario'):
                where_clauses.append("l.usuario_nome LIKE ?")
                params.append(f"%{filtros['usuario']}%")
            
            if filtros.get('acao'):
                where_clauses.append("l.acao LIKE ?")
                params.append(f"%{filtros['acao']}%")
            
            if filtros.get('modulo'):
                where_clauses.append("l.modulo LIKE ?")
                params.append(f"%{filtros['modulo']}%")
            
            if filtros.get('data_inicio'):
                where_clauses.append("DATE(l.timestamp) >= ?")
                params.append(filtros['data_inicio'])
            
            if filtros.get('data_fim'):
                where_clauses.append("DATE(l.timestamp) <= ?")
                params.append(filtros['data_fim'])
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY l.timestamp DESC"
        
        # Paginação
        offset = (pagina - 1) * por_pagina
        query += f" LIMIT {por_pagina} OFFSET {offset}"
        
        logs = conn.execute(query, params).fetchall()
        
        # Contar total de registros para paginação
        count_query = '''
            SELECT COUNT(*) as total
            FROM sistema_logs l
        '''
        
        if where_clauses:
            count_query += " WHERE " + " AND ".join(where_clauses)
        
        total = conn.execute(count_query, params).fetchone()['total']
        
        conn.close()
        
        return {
            'logs': logs,
            'total': total,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': (total + por_pagina - 1) // por_pagina
        }
        
    except Exception as e:
        print(f"Erro ao obter logs: {str(e)}")
        return {'logs': [], 'total': 0, 'pagina': 1, 'por_pagina': por_pagina, 'total_paginas': 0}

@app.route('/qualquer-rota')
def qualquer_rota():
    if 'user_id' not in session:
        return redirect(url_for('login.html'))
    
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    clientes = conn.execute('SELECT id, nome FROM clientes WHERE ativo = 1 ORDER BY nome').fetchall()
    colaboradores = conn.execute('SELECT id, nome FROM colaboradores_carsten WHERE ativo = 1 ORDER BY nome ASC').fetchall()
    conn.close()
    return render_template('cadastro.html', clientes=clientes, colaboradores=colaboradores)

    

@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['admin'] = user['admin']
            
            # Registrar log de login bem-sucedido
            registrar_log('LOGIN', 'AUTENTICACAO', f'Login realizado com sucesso - Usuário: {user["username"]}')
            
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            # Registrar tentativa de login falhada
            registrar_log('LOGIN_FALHADO', 'AUTENTICACAO', f'Tentativa de login falhada - Usuário: {username}', usuario_id=None, usuario_nome=username)
            flash('Usuário ou senha incorretos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Registrar log de logout
    if 'username' in session:
        registrar_log('LOGOUT', 'AUTENTICACAO', f'Logout realizado - Usuário: {session["username"]}')
    
    session.clear()
    flash('Você foi deslogado com sucesso', 'info')
    return redirect(url_for('login'))

@app.route('/salvar', methods=['POST'])
def salvar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 401
    
    try:
        # Obter dados do formulário
        data = request.form['data'].strip()
        mod_carsten = request.form.getlist('mod_carsten')  # Agora recebemos uma lista de colaboradores
        mdo_terceiro = request.form['mdo_terceiro'].strip()
        total_volumes = request.form['total_volumes'].strip()
        cliente_id = request.form['cliente_id'].strip()  # Agora recebemos o ID do cliente

        # Validação dos campos
        if not all([data, mod_carsten, mdo_terceiro, total_volumes, cliente_id]):
            return jsonify({'success': False, 'message': 'Todos os campos devem ser preenchidos.'})

        if not validar_data(data):
            return jsonify({'success': False, 'message': 'A data deve estar no formato DD/MM/AAAA.'})

        try:
            # Converter valores numéricos
            mdo_terceiro_float = float(mdo_terceiro)
            total_volumes_float = float(total_volumes)
            cliente_id_int = int(cliente_id)
        except ValueError:
            return jsonify({'success': False, 'message': 'Os campos MDO 3º e TOTAL VOLUMES devem conter valores numéricos válidos.'})

        # Filtrar colaboradores vazios e contar quantos foram selecionados
        colaboradores_selecionados = [col for col in mod_carsten if col.strip()]
        mod_carsten_count = len(colaboradores_selecionados)
        
        if (mod_carsten_count + mdo_terceiro_float) == 0:
            return jsonify({'success': False, 'message': 'MOD CARSTEN + MDO 3º não pode ser zero.'})

        # Calcular volume por pessoa
        vol_pessoa = round(total_volumes_float / (mod_carsten_count + mdo_terceiro_float), 2)

        # Salvar no banco de dados
        conn = get_db_connection()
        try:
            data_formatada = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
            
            # Para cada colaborador selecionado, verificar se já existe um registro para ele no dia
            # e inserir apenas se não existir
            colaboradores_inseridos = []
            for colaborador in colaboradores_selecionados:
                # Verificar se já existe um registro para este colaborador no dia
                existing = conn.execute('''
                    SELECT id FROM tb_pck_arm 
                    WHERE data = ? AND mod_carsten = ? AND cliente_id = ?
                ''', (data_formatada, colaborador, cliente_id_int)).fetchone()
                
                if not existing:
                    # Inserir novo registro apenas se não existir
                    conn.execute('''
                        INSERT INTO tb_pck_arm 
                        (data, cliente_id, mod_carsten, mod_3, total_volumes, vol_pessoas, usuario_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data_formatada,
                        cliente_id_int,
                        colaborador,
                        mdo_terceiro,
                        total_volumes,
                        str(vol_pessoa),
                        session['user_id']
                    ))
                    colaboradores_inseridos.append(colaborador)
            
            conn.commit()
            
            # Mensagem informando quantos colaboradores foram inseridos
            if colaboradores_inseridos:
                mensagem = f'Dados salvos com sucesso! {len(colaboradores_inseridos)} colaborador(es) inserido(s): {", ".join(colaboradores_inseridos)}'
                
                # Registrar log de cadastro bem-sucedido
                registrar_log('CADASTRO_CRIADO', 'CADASTROS', 
                            f'Novo cadastro criado - Cliente: {cliente_id_int}, Data: {data}, '
                            f'Colaboradores: {", ".join(colaboradores_inseridos)}, Volumes: {total_volumes}')
            else:
                mensagem = 'Todos os colaboradores já estavam cadastrados para este dia!'
                
                # Registrar log de tentativa de cadastro duplicado
                registrar_log('CADASTRO_DUPLICADO', 'CADASTROS', 
                            f'Tentativa de cadastro duplicado - Cliente: {cliente_id_int}, Data: {data}')
            
            return jsonify({
                'success': True,
                'message': mensagem,
                'vol_pessoa': vol_pessoa
            })
            
        except sqlite3.Error as e:
            return jsonify({'success': False, 'message': f'Erro ao salvar no banco de dados: {str(e)}'})
            
        finally:
            conn.close()

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao processar os dados: {str(e)}'})
    
# Adicione estas novas rotas:

@app.route('/historico_cadastros')
def historico_cadastros():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    
    # Buscar todos os registros agrupados por data, cliente e MDO 3º
    cadastros_raw = conn.execute('''
        SELECT c.id, date(c.data) as data, cl.nome as cliente, c.mod_carsten, c.mod_3, 
               c.total_volumes, c.vol_pessoas, c.usuario_id
        FROM tb_pck_arm c
        JOIN clientes cl ON c.cliente_id = cl.id
        ORDER BY c.data DESC, cl.nome
    ''').fetchall()
    
    # Agrupar registros por data, cliente e MDO 3º
    cadastros_agrupados = {}
    for registro in cadastros_raw:
        chave = (registro['data'], registro['cliente'], registro['mod_3'], registro['total_volumes'])
        
        if chave not in cadastros_agrupados:
            cadastros_agrupados[chave] = {
                'id': registro['id'],
                'data': registro['data'],
                'cliente': registro['cliente'],
                'mod_carsten': [registro['mod_carsten']],
                'mod_3': registro['mod_3'],
                'total_volumes': registro['total_volumes'],
                'vol_pessoas': registro['vol_pessoas'],
                'usuario_id': registro['usuario_id']
            }
        else:
            # Adicionar colaborador à lista se não estiver duplicado
            if registro['mod_carsten'] not in cadastros_agrupados[chave]['mod_carsten']:
                cadastros_agrupados[chave]['mod_carsten'].append(registro['mod_carsten'])
    
    # Converter para lista e ordenar
    cadastros = list(cadastros_agrupados.values())
    cadastros.sort(key=lambda x: (x['data'], x['cliente']), reverse=True)
    
    conn.close()
    
    return render_template('historico_cadastros.html', 
                         cadastros=cadastros,
                         titulos=["Data", "Cliente", "MOD CARSTEN", "MDO 3º", "TOTAL VOLUMES", "VOL/PESSOA"])



@app.route('/filtrar', methods=['POST'])
def filtrar():
    try:
        cliente = request.form.get('cliente_id', 'Todos')
        data = request.form.get('data', '').strip()

        df = pd.read_excel(get_db_connection)
        
        if cliente != 'Todos':
            df = df[df['cliente_id'] == cliente]
        if data:
            try:
                datetime.strptime(data, "%d/%m/%Y")
                df = df[df['Data'] == data]
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de data inválido. Use DD/MM/AAAA.'})

        registros = df.to_dict('records')
        return jsonify({'success': True, 'registros': registros})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    


@app.route('/editar_cadastro/<int:id>', methods=['GET', 'POST'])
def editar_cadastro(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            data = request.form['data'].strip()
            mod_carsten = request.form.getlist('mod_carsten')
            mdo_terceiro = request.form['mdo_terceiro'].strip()
            total_volumes = request.form['total_volumes'].strip()
            cliente_id = request.form['cliente_id'].strip()
            
            # Validação dos campos
            if not all([data, mod_carsten, mdo_terceiro, total_volumes, cliente_id]):
                flash('Todos os campos devem ser preenchidos.', 'danger')
                return redirect(url_for('editar_cadastro', id=id))
            
            if not validar_data(data):
                flash('A data deve estar no formato DD/MM/AAAA.', 'danger')
                return redirect(url_for('editar_cadastro', id=id))
            
            try:
                mdo_terceiro_float = float(mdo_terceiro)
                total_volumes_float = float(total_volumes)
                cliente_id_int = int(cliente_id)
            except ValueError:
                flash('Os campos MDO 3º e TOTAL VOLUMES devem conter valores numéricos válidos.', 'danger')
                return redirect(url_for('editar_cadastro', id=id))
            
            # Filtrar colaboradores vazios
            colaboradores_selecionados = [col for col in mod_carsten if col.strip()]
            mod_carsten_count = len(colaboradores_selecionados)
            
            if (mod_carsten_count + mdo_terceiro_float) == 0:
                flash('MOD CARSTEN + MDO 3º não pode ser zero.', 'danger')
                return redirect(url_for('editar_cadastro', id=id))
            
            # Calcular volume por pessoa
            vol_pessoa = round(total_volumes_float / (mod_carsten_count + mdo_terceiro_float), 2)
            data_formatada = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
            
            # Primeiro, excluir todos os registros antigos com a mesma data, cliente_id e mod_3
            conn.execute('''
                DELETE FROM tb_pck_arm 
                WHERE data = ? AND cliente_id = ? AND mod_3 = ?
            ''', (data_formatada, cliente_id_int, mdo_terceiro))
            
            # Inserir novos registros para cada colaborador
            for colaborador in colaboradores_selecionados:
                conn.execute('''
                    INSERT INTO tb_pck_arm 
                    (data, cliente_id, mod_carsten, mod_3, total_volumes, vol_pessoas, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_formatada,
                    cliente_id_int,
                    colaborador,
                    mdo_terceiro,
                    total_volumes,
                    str(vol_pessoa),
                    session['user_id']
                ))
            
            conn.commit()
            
            # Registrar log de edição
            registrar_log('CADASTRO_EDITADO', 'CADASTROS', 
                        f'Cadastro editado - ID: {id}, Cliente: {cliente_id_int}, Data: {data}, '
                        f'Colaboradores: {", ".join(colaboradores_selecionados)}, Volumes: {total_volumes}')
            
            flash('Cadastro atualizado com sucesso!', 'success')
            return redirect(url_for('historico_cadastros'))
            
        except Exception as e:
            flash(f'Erro ao atualizar cadastro: {str(e)}', 'danger')
        finally:
            conn.close()
    
    # Buscar dados do cadastro para edição
    cadastro = conn.execute('''
        SELECT c.id, c.data, c.cliente_id, c.mod_carsten, c.mod_3, c.total_volumes, c.vol_pessoas,
               cl.nome as cliente_nome
        FROM tb_pck_arm c
        JOIN clientes cl ON c.cliente_id = cl.id
        WHERE c.id = ?
    ''', (id,)).fetchone()
    
    if not cadastro:
        flash('Cadastro não encontrado!', 'danger')
        conn.close()
        return redirect(url_for('historico_cadastros'))
    
    # Buscar todos os colaboradores para o dropdown
    colaboradores = conn.execute('SELECT id, nome FROM colaboradores_carsten WHERE ativo = 1 ORDER BY nome ASC').fetchall()
    
    # Buscar todos os clientes para o dropdown
    clientes = conn.execute('SELECT id, nome FROM clientes WHERE ativo = 1 ORDER BY nome').fetchall()
    
    # Buscar todos os colaboradores do cadastro atual
    colaboradores_cadastro = conn.execute('''
        SELECT mod_carsten FROM tb_pck_arm 
        WHERE data = ? AND cliente_id = ? AND mod_3 = ?
    ''', (cadastro['data'], cadastro['cliente_id'], cadastro['mod_3'])).fetchall()
    
    colaboradores_selecionados = [col['mod_carsten'] for col in colaboradores_cadastro]
    
    conn.close()
    
    return render_template('editar_cadastro.html', 
                         cadastro=cadastro,
                         colaboradores=colaboradores,
                         clientes=clientes,
                         colaboradores_selecionados=colaboradores_selecionados)

@app.route('/excluir_cadastro')
def excluir_cadastro():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    id = request.args.get('id')
    conn = get_db_connection()
    
    # Buscar o registro para obter data, cliente_id e mod_3
    registro = conn.execute('''
        SELECT data, cliente_id, mod_3, total_volumes 
        FROM tb_pck_arm 
        WHERE id = ?
    ''', (id,)).fetchone()
    
    if registro:
        # Excluir todos os registros com a mesma data, cliente_id e mod_3
        conn.execute('''
            DELETE FROM tb_pck_arm 
            WHERE data = ? AND cliente_id = ? AND mod_3 = ? AND total_volumes = ?
        ''', (registro['data'], registro['cliente_id'], registro['mod_3'], registro['total_volumes']))
        
        conn.commit()
        
        # Registrar log de exclusão
        registrar_log('CADASTRO_EXCLUIDO', 'CADASTROS', 
                    f'Cadastro excluído - Data: {registro["data"]}, Cliente: {registro["cliente_id"]}, '
                    f'MDO 3º: {registro["mod_3"]}, Volumes: {registro["total_volumes"]}')
        
        flash('Todos os cadastros relacionados foram excluídos com sucesso!', 'success')
    else:
        flash('Cadastro não encontrado!', 'danger')
    
    conn.close()
    return redirect(url_for('historico_cadastros'))



@app.route('/excluir', methods=['POST'])
def excluir():
    try:
        idx = int(request.form['id'])
        
        df = pd.read_excel(get_db_connection)
        df.drop(index=idx, inplace=True)
        df.reset_index(drop=True, inplace=True)
        df.to_excel(get_db_connection, index=False)
        
        return jsonify({'success': True, 'message': 'Registro excluído com sucesso.'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/exportar', methods=['POST'])
def exportar():
    try:
        cliente = request.form.get('cliente_id', 'Todos')
        data = request.form.get('data', '').strip()

        df = pd.read_excel(get_db_connection)
        
        if cliente != 'Todos':
            df = df[df['cliente_id'] == cliente]
        if data:
            try:
                datetime.strptime(data, "%d/%m/%Y")
                df = df[df['Data'] == data]
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de data inválido. Use DD/MM/AAAA.'})

        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        df.to_excel(writer, index=False)
        writer.save()
        output.seek(0)

        nome_arquivo = f"export_{cliente}_{data.replace('/', '-')}.xlsx".replace("Todos", "geral").strip("_").replace("__", "_")
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nome_arquivo
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})       
    
@app.route('/admin/usuarios')
def gerenciar_usuarios():
    if 'user_id' not in session or not session.get('admin'):
        flash('Acesso negado. Somente administradores podem acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, username, nome, cargo, admin, ativo FROM usuarios').fetchall()
    conn.close()
    
    return render_template('admin_usuarios.html', usuarios=usuarios)     

@app.route('/admin/usuarios/criar', methods=['GET', 'POST'])
def criar_usuario():
    if 'user_id' not in session or not session.get('admin'):
        flash('Acesso negado. Somente administradores podem criar usuários.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nome = request.form['nome']
        cargo = request.form['cargo']
        admin = 1 if request.form.get('admin') else 0
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO usuarios (username, password, nome, cargo, admin)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                username,
                generate_password_hash(password),
                nome,
                cargo,
                admin
            ))
            conn.commit()
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('gerenciar_usuarios'))
        except sqlite3.IntegrityError:
            flash('Nome de usuário já existe. Escolha outro.', 'danger')
        finally:
            conn.close()
    
    return render_template('criar_usuario.html')

@app.route('/admin/usuarios/<int:id>/excluir', methods=['POST'])
def excluir_usuario(id):
    if 'user_id' not in session or not session.get('admin'):
        flash('Acesso negado. Somente administradores podem excluir usuários.', 'danger')
        return redirect(url_for('index'))

    if session['user_id'] == id:
        flash('Você não pode excluir a si mesmo.', 'warning')
        return redirect(url_for('gerenciar_usuarios'))

    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('gerenciar_usuarios'))



@app.route('/admin/usuarios/<int:id>/editar', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'user_id' not in session or not session.get('admin'):
        flash('Acesso negado. Somente administradores podem editar usuários.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        username = request.form['username']
        nome = request.form['nome']
        cargo = request.form['cargo']
        admin = 1 if request.form.get('admin') else 0
        
        try:
            conn.execute('''
                UPDATE usuarios 
                SET username = ?, nome = ?, cargo = ?, admin = ?
                WHERE id = ?
            ''', (username, nome, cargo, admin, id))
            conn.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('gerenciar_usuarios'))
        except sqlite3.IntegrityError:
            flash('Nome de usuário já existe. Escolha outro.', 'danger')
        finally:
            conn.close()
    
    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/admin/usuarios/<int:id>/alternar-status', methods=['POST'])
def alternar_status_usuario(id):
    if 'user_id' not in session or not session.get('admin'):
        flash('Acesso negado. Somente administradores podem alterar status de usuários.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    usuario = conn.execute('SELECT ativo FROM usuarios WHERE id = ?', (id,)).fetchone()
    novo_status = 0 if usuario['ativo'] else 1
    
    conn.execute('UPDATE usuarios SET ativo = ? WHERE id = ?', (novo_status, id))
    conn.commit()
    conn.close()
    
    flash(f'Status do usuário {"ativado" if novo_status else "desativado"} com sucesso!', 'success')
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/alterar-senha', methods=['GET', 'POST'])
def alterar_senha():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']
        confirmacao = request.form['confirmacao']
        
        conn = get_db_connection()
        usuario = conn.execute('SELECT password FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not check_password_hash(usuario['password'], senha_atual):
            flash('Senha atual incorreta.', 'danger')
        elif nova_senha != confirmacao:
            flash('Nova senha e confirmação não coincidem.', 'danger')
        else:
            conn.execute('UPDATE usuarios SET password = ? WHERE id = ?', 
                        (generate_password_hash(nova_senha), session['user_id']))
            conn.commit()
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('index'))
        
        conn.close()
    
    return render_template('alterar_senha.html')

@app.route('/clientes')
def listar_clientes():
    if 'user_id' not in session:
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    clientes = conn.execute('''
        SELECT id, nome, codigo, ativo 
        FROM clientes 
        ORDER BY nome
    ''').fetchall()
    conn.close()
    
    return render_template('clientes/listar.html', clientes=clientes)

@app.route('/clientes/novo', methods=['GET', 'POST'])
def novo_cliente():
    if 'user_id' not in session:
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        codigo = request.form.get('codigo', '').strip() or None
        
        if not nome:
            flash('O nome do cliente é obrigatório.', 'danger')
        else:
            conn = get_db_connection()
            try:
                conn.execute('''
                    INSERT INTO clientes (nome, codigo)
                    VALUES (?, ?)
                ''', (nome, codigo))
                conn.commit()
                flash('Cliente cadastrado com sucesso!', 'success')
                return redirect(url_for('listar_clientes'))
            except sqlite3.IntegrityError:
                flash('Código já existe. Utilize outro código ou deixe em branco.', 'danger')
            finally:
                conn.close()
    
    return render_template('clientes/novo.html')

@app.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    if 'user_id' not in session:
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        codigo = request.form.get('codigo', '').strip() or None
        ativo = 1 if request.form.get('ativo') else 0
        
        if not nome:
            flash('O nome do cliente é obrigatório.', 'danger')
        else:
            try:
                conn.execute('''
                    UPDATE clientes 
                    SET nome = ?, codigo = ?, ativo = ?
                    WHERE id = ?
                ''', (nome, codigo, ativo, id))
                conn.commit()
                flash('Cliente atualizado com sucesso!', 'success')
                return redirect(url_for('listar_clientes'))
            except sqlite3.IntegrityError:
                flash('Código já existe. Utilize outro código.', 'danger')
            finally:
                conn.close()
    
    return render_template('clientes/editar.html', cliente=cliente)

@app.route('/clientes/<int:id>/alternar-status', methods=['POST'])
def alternar_status_cliente(id):
    if 'user_id' not in session:
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cliente = conn.execute('SELECT ativo FROM clientes WHERE id = ?', (id,)).fetchone()
    novo_status = 0 if cliente['ativo'] else 1
    
    conn.execute('UPDATE clientes SET ativo = ? WHERE id = ?', (novo_status, id))
    conn.commit()
    conn.close()
    
    flash(f'Cliente {"ativado" if novo_status else "desativado"} com sucesso!', 'success')
    return redirect(url_for('listar_clientes'))




@app.route('/historico_escalas')
def historico_escalas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    colaboradores = conn.execute('''
        SELECT id, nome, cargo, departamento, data_contratacao, ativo
        FROM colaboradores_carsten
        ORDER BY nome
    ''').fetchall()
    conn.close()
    
    return render_template('colaboradores_carsten.html', colaboradores=colaboradores)

@app.route('/colaboradores/novo', methods=['GET', 'POST'])
def novo_colaborador():
    if 'user_id' not in session:
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        cargo = request.form['cargo'].strip()
        
        if not all([nome, cargo]):
            flash('Nome e cargo são obrigatórios.', 'danger')
        else:
            try:
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO colaboradores_carsten (nome, cargo, departamento, data_contratacao, ativo)
                    VALUES (?, ?, 'Não informado', CURRENT_DATE, 1)
                ''', (nome, cargo))
                conn.commit()
                conn.close()
                
                flash('Colaborador cadastrado com sucesso!', 'success')
                return redirect(url_for('historico_escalas'))
            except Exception as e:
                flash(f'Erro ao cadastrar colaborador: {str(e)}', 'danger')
    
    return render_template('colaboradores/novo.html')

@app.route('/colaboradores/<int:id>/editar', methods=['GET', 'POST'])
def editar_colaborador(id):
    if 'user_id' not in session:
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    colaborador = conn.execute('SELECT * FROM colaboradores_carsten WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        cargo = request.form['cargo'].strip()
        ativo = 1 if request.form.get('ativo') else 0
        
        if not all([nome, cargo]):
            flash('Nome e cargo são obrigatórios.', 'danger')
        else:
            try:
                conn.execute('''
                    UPDATE colaboradores_carsten 
                    SET nome = ?, cargo = ?, ativo = ?
                    WHERE id = ?
                ''', (nome, cargo, ativo, id))
                conn.commit()
                flash('Colaborador atualizado com sucesso!', 'success')
                return redirect(url_for('historico_escalas'))
            except Exception as e:
                flash(f'Erro ao atualizar colaborador: {str(e)}', 'danger')
            finally:
                conn.close()
    
    return render_template('colaboradores/editar.html', colaborador=colaborador)

@app.route('/colaboradores/<int:id>/excluir', methods=['POST'])
def excluir_colaborador(id):
    if 'user_id' not in session:
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM colaboradores_carsten WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Colaborador excluído com sucesso!', 'success')
    return redirect(url_for('historico_escalas'))

@app.route('/admin/logs')
def visualizar_logs():
    """Visualiza logs do sistema (apenas para administradores)"""
    if 'user_id' not in session or not session.get('admin'):
        flash('Acesso negado. Somente administradores podem visualizar logs.', 'danger')
        return redirect(url_for('index'))
    
    # Obter parâmetros de filtro
    pagina = request.args.get('pagina', 1, type=int)
    usuario = request.args.get('usuario', '')
    acao = request.args.get('acao', '')
    modulo = request.args.get('modulo', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    
    # Aplicar filtros
    filtros = {}
    if usuario:
        filtros['usuario'] = usuario
    if acao:
        filtros['acao'] = acao
    if modulo:
        filtros['modulo'] = modulo
    if data_inicio:
        filtros['data_inicio'] = data_inicio
    if data_fim:
        filtros['data_fim'] = data_fim
    
    # Obter logs com filtros e paginação
    resultado = obter_logs(filtros, pagina, 50)
    
    # Registrar visualização dos logs
    registrar_log('LOGS_VISUALIZADOS', 'ADMIN', f'Logs do sistema visualizados - Filtros aplicados: {filtros}')
    
    return render_template('admin_logs.html', 
                         logs=resultado['logs'],
                         paginacao=resultado,
                         filtros=filtros)

@app.route('/admin/logs/exportar')
def exportar_logs():
    """Exporta logs do sistema em formato CSV (apenas para administradores)"""
    if 'user_id' not in session or not session.get('admin'):
        flash('Acesso negado. Somente administradores podem exportar logs.', 'danger')
        return redirect(url_for('index'))
    
    # Obter todos os logs sem paginação
    resultado = obter_logs({}, 1, 10000)  # Limite alto para pegar todos
    
    # Criar arquivo CSV
    output = BytesIO()
    output.write('Data/Hora,Usuário,Ação,Módulo,Detalhes,IP,User Agent\n'.encode('utf-8'))
    
    for log in resultado['logs']:
        linha = f"{log['timestamp']},{log['usuario_nome']},{log['acao']},{log['modulo']},{log['detalhes']},{log['ip_address']},{log['user_agent']}\n"
        output.write(linha.encode('utf-8'))
    
    output.seek(0)
    
    # Registrar exportação
    registrar_log('LOGS_EXPORTADOS', 'ADMIN', f'Logs do sistema exportados - Total: {len(resultado["logs"])} registros')
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'logs_sistema_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

# ... (mantenha as outras rotas como /historico, /filtrar, /editar, /excluir, /exportar)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)