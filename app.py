# -*- coding: utf-8 -*-
"""
=========================================================
CONTROLE DE REBAIXAS - WEB
=========================================================

Sistema web profissional para gerenciamento de rebaixas

INSTALAR:
pip install flask pandas openpyxl

EXECUTAR:
python app.py
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'sua-chave-secreta-aqui'

# Configuração do banco de dados PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    # Fallback para SQLite se não houver DATABASE_URL (desenvolvimento local)
    import sqlite3
    from pathlib import Path
    DB_PATH = Path(__file__).parent / "controle_rebaixas.db"
    USE_POSTGRES = False
else:
    USE_POSTGRES = True


class Database:
    """Gerencia o banco de dados para rebaixas (PostgreSQL ou SQLite)."""
    
    def __init__(self):
        if not USE_POSTGRES:
            self.db_path = DB_PATH
        self.inicializar()
    
    def get_connection(self):
        """Retorna a conexão com o banco de dados."""
        if USE_POSTGRES:
            return psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            return sqlite3.connect(self.db_path)
    
    def inicializar(self):
        """Cria as tabelas do banco de dados se não existirem."""
        conn = self.get_connection()
        try:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rebaixas (
                        id SERIAL PRIMARY KEY,
                        nome TEXT NOT NULL,
                        responsavel TEXT,
                        status TEXT DEFAULT 'programada',
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        quantidade_itens INTEGER DEFAULT 0,
                        itens TEXT DEFAULT '[]'
                    )
                """)
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rebaixas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        responsavel TEXT,
                        status TEXT DEFAULT 'programada',
                        data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
                        data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP,
                        quantidade_itens INTEGER DEFAULT 0,
                        itens TEXT DEFAULT '[]'
                    )
                """)
            conn.commit()
        finally:
            conn.close()
    
    def adicionar_rebaixa(self, nome, responsavel, status, itens_json):
        """Adiciona uma nova rebaixa ao banco de dados."""
        import json
        conn = self.get_connection()
        try:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    INSERT INTO rebaixas (nome, responsavel, status, itens, quantidade_itens)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (nome, responsavel, status, itens_json, len(json.loads(itens_json))))
                result = cursor.fetchone()
                conn.commit()
                return result['id']
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO rebaixas (nome, responsavel, status, itens, quantidade_itens)
                    VALUES (?, ?, ?, ?, ?)
                """, (nome, responsavel, status, itens_json, len(json.loads(itens_json))))
                conn.commit()
                return cursor.lastrowid
        finally:
            conn.close()
    
    def listar_rebaixas(self):
        """Lista todas as rebaixas."""
        import json
        conn = self.get_connection()
        try:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT id, nome, responsavel, status, data_criacao, data_atualizacao, quantidade_itens, itens
                    FROM rebaixas
                    ORDER BY data_criacao DESC
                """)
                rebaixas = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    row_dict['itens'] = json.loads(row_dict['itens']) if row_dict['itens'] else []
                    rebaixas.append(row_dict)
                return rebaixas
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, nome, responsavel, status, data_criacao, data_atualizacao, quantidade_itens, itens
                    FROM rebaixas
                    ORDER BY data_criacao DESC
                """)
                rebaixas = []
                for row in cursor.fetchall():
                    rebaixas.append({
                        'id': row[0],
                        'nome': row[1],
                        'responsavel': row[2],
                        'status': row[3],
                        'data_criacao': row[4],
                        'data_atualizacao': row[5],
                        'quantidade_itens': row[6],
                        'itens': json.loads(row[7]) if row[7] else []
                    })
                return rebaixas
        finally:
            conn.close()
    
    def obter_rebaixa(self, rebaixa_id):
        """Obtém detalhes de uma rebaixa específica."""
        import json
        conn = self.get_connection()
        try:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT id, nome, responsavel, status, data_criacao, data_atualizacao, quantidade_itens, itens
                    FROM rebaixas WHERE id = %s
                """, (rebaixa_id,))
                row = cursor.fetchone()
                if row:
                    row_dict = dict(row)
                    row_dict['itens'] = json.loads(row_dict['itens']) if row_dict['itens'] else []
                    return row_dict
                return None
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, nome, responsavel, status, data_criacao, data_atualizacao, quantidade_itens, itens
                    FROM rebaixas WHERE id = ?
                """, (rebaixa_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'nome': row[1],
                        'responsavel': row[2],
                        'status': row[3],
                        'data_criacao': row[4],
                        'data_atualizacao': row[5],
                        'quantidade_itens': row[6],
                        'itens': json.loads(row[7]) if row[7] else []
                    }
                return None
        finally:
            conn.close()
    
    def atualizar_rebaixa(self, rebaixa_id, status, data_atualizacao):
        """Atualiza o status de uma rebaixa."""
        conn = self.get_connection()
        try:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    UPDATE rebaixas SET status = %s, data_atualizacao = %s WHERE id = %s
                """, (status, data_atualizacao, rebaixa_id))
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE rebaixas SET status = ?, data_atualizacao = ? WHERE id = ?
                """, (status, data_atualizacao, rebaixa_id))
            conn.commit()
        finally:
            conn.close()
    
    def deletar_rebaixa(self, rebaixa_id):
        """Deleta uma rebaixa."""
        conn = self.get_connection()
        try:
            if USE_POSTGRES:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("DELETE FROM rebaixas WHERE id = %s", (rebaixa_id,))
            else:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM rebaixas WHERE id = ?", (rebaixa_id,))
            conn.commit()
        finally:
            conn.close()


# Inicializar o banco de dados com tratamento de erro
try:
    db = Database()
    print("Banco de dados inicializado com sucesso")
except Exception as e:
    print(f"Erro ao inicializar banco de dados: {e}")
    db = None


@app.route('/')
def index():
    """Página principal."""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        return f"Erro ao renderizar template: {str(e)}", 500


@app.route('/api/rebaixas', methods=['GET'])
def listar_rebaixas_api():
    """API para listar rebaixas."""
    if db is None:
        return jsonify({'erro': 'Banco de dados não disponível'}), 500
    try:
        import json
        rebaixas = db.listar_rebaixas()
        return jsonify(rebaixas)
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar rebaixas: {str(e)}'}), 500


@app.route('/api/rebaixas', methods=['POST'])
def criar_rebaixa_api():
    """API para criar uma nova rebaixa."""
    if db is None:
        return jsonify({'erro': 'Banco de dados não disponível'}), 500
    try:
        import json
        data = request.json
        
        rebaixa_id = db.adicionar_rebaixa(
            nome=data['nome'],
            responsavel=data.get('responsavel', 'Não informado'),
            status=data.get('status', 'programada'),
            itens_json=json.dumps(data.get('itens', []))
        )
        
        return jsonify({'id': rebaixa_id, 'mensagem': 'Rebaixa criada com sucesso'})
    except Exception as e:
        return jsonify({'erro': f'Erro ao criar rebaixa: {str(e)}'}), 500


@app.route('/api/rebaixas/<int:rebaixa_id>', methods=['GET'])
def obter_rebaixa_api(rebaixa_id):
    """API para obter detalhes de uma rebaixa."""
    if db is None:
        return jsonify({'erro': 'Banco de dados não disponível'}), 500
    try:
        rebaixa = db.obter_rebaixa(rebaixa_id)
        
        if not rebaixa:
            return jsonify({'erro': 'Rebaixa não encontrada'}), 404
        
        return jsonify(rebaixa)
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter rebaixa: {str(e)}'}), 500


@app.route('/api/rebaixas/<int:rebaixa_id>', methods=['PUT'])
def atualizar_rebaixa_api(rebaixa_id):
    """API para atualizar uma rebaixa."""
    if db is None:
        return jsonify({'erro': 'Banco de dados não disponível'}), 500
    try:
        data = request.json
        
        db.atualizar_rebaixa(
            rebaixa_id=rebaixa_id,
            status=data.get('status'),
            data_atualizacao=data.get('data_atualizacao')
        )
        
        return jsonify({'mensagem': 'Rebaixa atualizada com sucesso'})
    except Exception as e:
        return jsonify({'erro': f'Erro ao atualizar rebaixa: {str(e)}'}), 500


@app.route('/api/rebaixas/<int:rebaixa_id>', methods=['DELETE'])
def deletar_rebaixa_api(rebaixa_id):
    """API para deletar uma rebaixa."""
    if db is None:
        return jsonify({'erro': 'Banco de dados não disponível'}), 500
    try:
        db.deletar_rebaixa(rebaixa_id)
        return jsonify({'mensagem': 'Rebaixa deletada com sucesso'})
    except Exception as e:
        return jsonify({'erro': f'Erro ao deletar rebaixa: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
