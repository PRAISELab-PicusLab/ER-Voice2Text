"""
Modulo di autenticazione per il sistema medico
Gestisce login/logout senza CSRF per l'ambiente di sviluppo
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from datetime import datetime


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def login_view(request):
    """
    Endpoint di login per il sistema medico
    """
    if request.method == 'OPTIONS':
        # Gestione preflight CORS
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
        
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Metodo non permesso'
        }, status=405)
    
    try:
        # Debug logging
        print(f"Login request: {request.method}")
        print(f"Request body: {request.body}")
        print(f"Content-Type: {request.META.get('CONTENT_TYPE')}")
        
        # Parse JSON data
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        print(f"Username: {username}, Password: {'*' * len(password) if password else 'None'}")
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'error': 'Username e password richiesti'
            }, status=400)
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user and user.is_active:
            # Success response
            token = f"token-{user.id}-{datetime.now().timestamp()}"
            
            return JsonResponse({
                'success': True,
                'access': token,
                'refresh': f"refresh-{token}",
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'specialization': getattr(user, 'specialization', ''),
                    'department': getattr(user, 'department', ''),
                    'is_emergency_doctor': getattr(user, 'is_emergency_doctor', False),
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Credenziali non valide'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON non valido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Errore interno: {str(e)}'
        }, status=500)


@csrf_exempt
def logout_view(request):
    """
    Endpoint di logout
    """
    return JsonResponse({
        'success': True,
        'message': 'Logout effettuato con successo'
    })


@csrf_exempt
def health_check(request):
    """
    Endpoint di controllo stato server
    """
    return JsonResponse({
        'success': True,
        'message': 'Server Django funzionante',
        'timestamp': datetime.now().isoformat()
    })