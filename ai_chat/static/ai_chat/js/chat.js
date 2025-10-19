// ai_chat/static/ai_chat/js/chat.js

const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const loginButton = document.getElementById('login-button');
const logoutButton = document.getElementById('logout-button');
const loginScreen = document.getElementById('login-screen');
const chatScreen = document.getElementById('chat-screen');

// Function to check initial login status (requires Django session or cookie check)
function checkLoginStatus() {
    // A simplified check. In production, check for a user cookie/session.
    const loggedIn = sessionStorage.getItem('isLoggedIn') === 'true';
    if (loggedIn) {
        showChatScreen();
    } else {
        showLoginScreen();
    }
}

function showChatScreen() {
    loginScreen.style.display = 'none';
    chatScreen.style.display = 'block';
    // Optionally fetch historical messages from a Django endpoint if needed
}

function showLoginScreen() {
    loginScreen.style.display = 'block';
    chatScreen.style.display = 'none';
}

function appendMessage(role, content) {
    const messageDiv = document.createElement('div');
    const headerClass = role === 'user' ? 'user-header' : 'bot-header';
    const messageClass = role === 'user' ? 'user-message' : 'bot-message';
    const headerText = role === 'user' ? 'You' : 'AyurVeda Assistant';
    
    messageDiv.className = `chat-message ${messageClass}`;
    messageDiv.innerHTML = `
        <div class="message-header ${headerClass}">${headerText}</div>
        <div class="message-content">${content}</div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll
}

function showTypingIndicator() {
    // Injects the custom HTML from custom.css
    const indicatorHTML = `
        <div id="typing-indicator" class="typing-indicator">
            <span class="typing-text">🕉️ AyurVeda Assistant is thinking...</span>
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>`;
    chatMessages.insertAdjacentHTML('beforeend', indicatorHTML);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

async function handleSendMessage() {
    const question = userInput.value.trim();
    if (!question) return;

    appendMessage('user', question);
    userInput.value = '';
    showTypingIndicator();
    sendButton.disabled = true;

    try {
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Important: Add CSRF token for production Django forms
                'X-CSRFToken': getCookie('csrftoken') 
            },
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        removeTypingIndicator();
        appendMessage('assistant', data.answer);
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator();
        appendMessage('assistant', "🙏 I apologize, but I encountered an error. Please check the server logs.");
    } finally {
        sendButton.disabled = false;
    }
}

// --- Login/Logout Handlers ---

async function handleLogin() {
    const email = document.getElementById('login-email').value;
    const name = document.getElementById('login-name').value;
    if (!email || !name) {
        alert("Please enter both email and name.");
        return;
    }

    try {
        const response = await fetch('/api/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ email: email, name: name })
        });
        
        if (response.ok) {
            sessionStorage.setItem('isLoggedIn', 'true');
            alert(`Welcome, ${name}!`);
            showChatScreen();
        } else {
            alert("Login failed.");
        }
    } catch (error) {
        console.error('Login error:', error);
        alert("An error occurred during login.");
    }
}

async function handleLogout() {
    try {
        await fetch('/api/logout/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        sessionStorage.setItem('isLoggedIn', 'false');
        alert("You have been logged out.");
        showLoginScreen();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Helper function to get CSRF token (required for Django POST requests)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Event Listeners
sendButton.addEventListener('click', handleSendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
});
loginButton.addEventListener('click', handleLogin);
logoutButton.addEventListener('click', handleLogout);

// Initialize application state
document.addEventListener('DOMContentLoaded', checkLoginStatus);