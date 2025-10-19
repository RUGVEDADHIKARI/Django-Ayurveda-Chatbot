# ai_chat/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render

from .service import get_agent_service
import hashlib
import json

# Dummy Authentication: Django Sessions should handle this in a real app.
# For quick testing, we use a simple session key.
SESSION_KEY = 'user_session_id'

def chat_interface_view(request):
    # You'll pass any initial context here.
    return render(request, 'ai_chat/chat_interface.html', {})

def create_session_id(username: str) -> str:
    """Create unique session ID (same logic as in app.py)"""
    return hashlib.md5(username.encode()).hexdigest()

@method_decorator(csrf_exempt, name='dispatch') # For testing outside of a form
class ChatAPIView(APIView):
    """API endpoint to interact with the AyurVeda Agent."""

    def post(self, request):
        # 1. Get User Input and Session ID
        data = request.data
        user_input = data.get('question')
        
        # In a real Django app, use request.user.email or a proper session key
        # For simplicity, we'll use a hardcoded or simple user identifier.
        user_identifier = request.session.get('user_email', 'anonymous_user@example.com')
        
        if 'user_email' in request.session:
            session_id = create_session_id(request.session['user_email'])
        else:
            # Simple session for anonymous testing
            session_id = create_session_id("django_anon_user")
            
        if not user_input:
            return Response(
                {"error": "The 'question' field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Get the Agent Executor with the correct memory
        agent_executor = get_agent_service().get_agent_executor(session_id)
        
        # 3. Invoke the Agent
        try:
            # The agent executor handles the memory internally (read/write to Redis)
            response = agent_executor.invoke({
                "input": user_input
            })
            
            # 4. Return the AI's response
            return Response({
                "question": user_input,
                "answer": response["output"]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = f"I apologize, but an internal server error occurred while processing your request: {str(e)}"
            return Response(
                {"error": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# --- Simple Login/Session Management (Placeholder for OAuth/Allauth) ---

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    """
    Placeholder for Google OAuth login.
    For this transition, we'll use a simple session-based login.
    """
    def post(self, request):
        # In a real app, this would exchange the Google token for user info.
        # For local testing, we simulate a successful login.
        
        # Get simulated user info from POST data
        email = request.data.get('email', 'testuser@ayurveda.com')
        name = request.data.get('name', 'Test User')
        
        # Set session variables
        request.session['logged_in'] = True
        request.session['user_email'] = email
        request.session['user_name'] = name
        
        return Response({
            "success": True, 
            "message": f"Welcome, {name}!",
            "email": email,
            "name": name
        })

@method_decorator(csrf_exempt, name='dispatch')
class LogoutAPIView(APIView):
    def post(self, request):
        # Clear session variables
        request.session.flush()
        return Response({"success": True, "message": "Logged out successfully."})

class IndexAPIView(APIView):
    def get(self, request):
        return Response({"message": "Ayurveda Chatbot API. POST your question to /chat/ with {'question': '...'}"})
