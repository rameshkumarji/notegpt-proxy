from flask import Flask, request, jsonify, Response
import requests
import json
import uuid

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # No escapar caracteres Unicode

# Configurar CORS para todas las rutas
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET')
    return response

@app.route('/api/chat', methods=['GET'])
def chat():
    # Solo GET - Obtener parámetros de la URL
    modelo = request.args.get('modelo', 'gpt-4.1-mini')
    mensaje = request.args.get('mensaje') or request.args.get('prompt') or request.args.get('texto')
    
    # Validar que haya un mensaje
    if not mensaje:
        data = {
            'error': 'Falta el parámetro "mensaje", "prompt" o "texto"',
            'success': False
        }
        return Response(
            json.dumps(data, ensure_ascii=False, indent=2),
            mimetype='application/json; charset=utf-8',
            status=400
        )
    
    # Configurar la petición a NoteGPT
    url = "https://notegpt.io/api/v2/chat/stream"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Referer": "https://notegpt.io/ai-chat",
        "Origin": "https://notegpt.io",
        "Cookie": "anonymous_user_id=05522698-d985-48a3-b8de-179c66683b3b"
    }
    
    payload = {
        "message": mensaje,
        "model": modelo,
        "tone": "default",
        "length": "moderate",
        "conversation_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        
        if response.status_code != 200:
            data = {
                'error': f'Error {response.status_code}',
                'success': False
            }
            return Response(
                json.dumps(data, ensure_ascii=False, indent=2),
                mimetype='application/json; charset=utf-8',
                status=response.status_code
            )
        
        # Leer bytes y decodificar correctamente como UTF-8
        responseText = response.content.decode('utf-8')
        
        if not responseText or not responseText.strip():
            data = {
                'error': 'Empty response from NoteGPT',
                'success': False
            }
            return Response(
                json.dumps(data, ensure_ascii=False, indent=2),
                mimetype='application/json; charset=utf-8',
                status=500
            )
        
        # Acumular toda la respuesta
        respuesta_completa = ""
        razonamiento = ""
        
        # Dividir por líneas y procesar
        for line in responseText.split('\n'):
            if line.startswith('data:'):
                try:
                    jsonStr = line.replace('data:', '').strip()
                    if not jsonStr:
                        continue
                    
                    data = json.loads(jsonStr)
                    
                    # Acumular texto
                    if data.get('text'):
                        respuesta_completa += data['text']
                    
                    if data.get('reasoning'):
                        razonamiento += data['reasoning']
                        
                except:
                    continue
        
        if not respuesta_completa.strip():
            data = {
                'error': 'No text content extracted from NoteGPT',
                'success': False
            }
            return Response(
                json.dumps(data, ensure_ascii=False, indent=2),
                mimetype='application/json; charset=utf-8',
                status=500
            )
        
        # Devolver respuesta completa
        resultado = {
            'success': True,
            'respuesta': respuesta_completa.strip(),
            'modelo': modelo,
            'pregunta': mensaje
        }
        
        if razonamiento.strip():
            resultado['razonamiento'] = razonamiento.strip()
        
        # Crear respuesta con encoding correcto
        return Response(
            json.dumps(resultado, ensure_ascii=False, indent=2),
            mimetype='application/json; charset=utf-8',
            status=200
        )
                    
    except Exception as e:
        data = {
            'error': str(e),
            'success': False
        }
        return Response(
            json.dumps(data, ensure_ascii=False, indent=2),
            mimetype='application/json; charset=utf-8',
            status=500
        )

@app.route('/api/modelos', methods=['GET'])
def modelos():
    """Endpoint para listar modelos disponibles"""
    available_models = [
        "TA/deepseek-ai/DeepSeek-V3",
        "TA/deepseek-ai/DeepSeek-R1",
        "gpt-4.1-mini",
        "gemini-3-flash-preview"
    ]
    data = {
        'modelos': available_models,
        'default': 'gpt-4.1-mini'
    }
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8'
    )

@app.route('/', methods=['GET'])
@app.route('/api', methods=['GET'])
def home():
    """Endpoint de información"""
    data = {
        'servicio': 'NoteGPT API Proxy',
        'version': '2.0',
        'tipo_respuesta': 'JSON completo (no streaming)',
        'endpoints': {
            '/api/chat': {
                'metodo': 'GET',
                'parametros': {
                    'modelo': 'Modelo a usar (opcional, default: gpt-4.1-mini)',
                    'mensaje': 'Texto del mensaje (requerido)'
                },
                'nota': 'El idioma se detecta automáticamente basándose en el mensaje',
                'ejemplo': '/api/chat?mensaje=Hello',
                'respuesta': {
                    'success': True,
                    'respuesta': 'Texto de la respuesta completa',
                    'modelo': 'gpt-4.1-mini',
                    'pregunta': 'Tu pregunta original'
                }
            },
            '/api/modelos': {
                'metodo': 'GET',
                'descripcion': 'Lista los modelos disponibles'
            }
        }
    }
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8'
    )

# Para Vercel
if __name__ == '__main__':
    app.run(debug=True)