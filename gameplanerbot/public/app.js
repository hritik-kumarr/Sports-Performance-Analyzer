document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  const userInput = document.getElementById('user-input');
  const sendButton = document.getElementById('send-btn');

  // Auto-resize textarea based on content
  userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
  });

  // Handle sending messages
  function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessageToChat('user', message);
    
    // Reset textarea height
    userInput.style.height = 'auto';
    
    // Clear input
    userInput.value = '';
    
    // Show loading indicator
    const loadingMessage = addLoadingMessage();
    
    // Add a unique timestamp to prevent caching
    const timestamp = new Date().getTime();
    
    // Send to backend with cache prevention
    fetch(`/api/chat?t=${timestamp}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
      body: JSON.stringify({ 
        message: message,
        timestamp: timestamp 
      })
    })
    .then(response => response.json())
    .then(data => {
      // Remove loading message
      loadingMessage.remove();
      
      // Force redraw before adding new content (helps with rendering issues)
      setTimeout(() => {
        // Add bot response
        addMessageToChat('bot', data.response, true);
      }, 50);
    })
    .catch(error => {
      console.error('Error:', error);
      // Remove loading message
      loadingMessage.remove();
      
      // Add error message
      addMessageToChat('bot', '<p>Sorry, there was an error processing your request. Please try again.</p>', true);
    });
  }

  // Add a loading message
  function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    
    const headerDiv = document.createElement('div');
    headerDiv.className = 'message-header';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    const icon = document.createElement('i');
    icon.className = 'fas fa-robot';
    avatarDiv.appendChild(icon);
    
    const infoDiv = document.createElement('div');
    infoDiv.className = 'message-info';
    
    const senderDiv = document.createElement('div');
    senderDiv.className = 'message-sender';
    senderDiv.textContent = 'TournamentGenius';
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = 'Just now';
    
    infoDiv.appendChild(senderDiv);
    infoDiv.appendChild(timeDiv);
    
    headerDiv.appendChild(avatarDiv);
    headerDiv.appendChild(infoDiv);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const loadingDots = document.createElement('div');
    loadingDots.className = 'loading-dots';
    loadingDots.innerHTML = '<span></span><span></span><span></span>';
    
    contentDiv.appendChild(loadingDots);
    messageDiv.appendChild(headerDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
    
    return messageDiv;
  }

  // Add a message to the chat display
  function addMessageToChat(sender, content, isHtml = false) {
    // Create unique ID for this message
    const messageId = `msg-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.id = messageId;
    
    // Create header
    const headerDiv = document.createElement('div');
    headerDiv.className = 'message-header';
    
    // Create avatar
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    const icon = document.createElement('i');
    icon.className = sender === 'bot' ? 'fas fa-robot' : 'fas fa-user';
    avatarDiv.appendChild(icon);
    
    // Create info
    const infoDiv = document.createElement('div');
    infoDiv.className = 'message-info';
    
    const senderDiv = document.createElement('div');
    senderDiv.className = 'message-sender';
    senderDiv.textContent = sender === 'bot' ? 'TournamentGenius' : 'You';
    
    // Add actual timestamp
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = `${hours}:${minutes}`;
    
    infoDiv.appendChild(senderDiv);
    infoDiv.appendChild(timeDiv);
    
    headerDiv.appendChild(avatarDiv);
    headerDiv.appendChild(infoDiv);
    
    // Create message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Handle HTML content or plain text
    if (isHtml) {
      contentDiv.innerHTML = content;
    } else {
      // Create paragraph for the text
      const paragraph = document.createElement('p');
      paragraph.textContent = content;
      contentDiv.appendChild(paragraph);
    }
    
    // Add elements to message
    messageDiv.appendChild(headerDiv);
    messageDiv.appendChild(contentDiv);
    
    // Add message to chat
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
    
    // Force browser reflow to ensure the message is rendered correctly
    void messageDiv.offsetHeight;
    
    return messageDiv;
  }

  // Function to scroll chat to bottom
  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Function to handle suggestion chips
  window.suggestQuery = function(element) {
    userInput.value = element.textContent;
    userInput.style.height = 'auto';
    userInput.style.height = (userInput.scrollHeight) + 'px';
    sendMessage();
  };

  // Handle sidebar menu item clicks
  document.querySelectorAll('.sidebar-menu li').forEach(item => {
    item.addEventListener('click', () => {
      const topic = item.textContent.trim();
      userInput.value = `Tell me about ${topic.toLowerCase()}`;
      userInput.style.height = 'auto';
      userInput.style.height = (userInput.scrollHeight) + 'px';
      sendMessage();
    });
  });

  // Event listeners
  sendButton.addEventListener('click', sendMessage);
  
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Focus input on load
  userInput.focus();

  // Add animation for the features
  const features = document.querySelectorAll('.feature');
  features.forEach((feature, index) => {
    feature.style.animationDelay = `${index * 0.1}s`;
    feature.classList.add('animate-in');
  });
}); 