async function csrfToken(){
  const re = /(^|; )csrftoken=([^;]+)/;
  const m = document.cookie.match(re);
  return m ? decodeURIComponent(m[2]) : '';
}

function uuidv4(){
  // simple RFC4122 version4 compliant generator
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function appendMessage(text, cls){
  const box = document.getElementById('chatbot-messages');
  const el = document.createElement('div');
  el.className = 'msg '+cls;
  el.textContent = text;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
}

function saveChatHistory(){
  const box = document.getElementById('chatbot-messages');
  localStorage.setItem('chat_history_html', box.innerHTML);
}

function loadChatHistory(){
  const html = localStorage.getItem('chat_history_html');
  if(html){
    const box = document.getElementById('chatbot-messages');
    box.innerHTML = html;
    box.scrollTop = box.scrollHeight;
  }
}

function setTyping(show){
  const el = document.getElementById('chatbot-typing');
  if(!el) return;
  if(show){ el.classList.remove('hidden'); el.setAttribute('aria-hidden','false'); }
  else { el.classList.add('hidden'); el.setAttribute('aria-hidden','true'); }
}

function setLoadingButton(isLoading){
  const btn = document.getElementById('chatbot-send');
  if(!btn) return;
  if(isLoading) btn.classList.add('loading'); else btn.classList.remove('loading');
}


document.addEventListener('DOMContentLoaded', function(){
  const input = document.getElementById('chatbot-input-field');
  const send = document.getElementById('chatbot-send');

  // ensure we have a persisted session id for the chat widget
  let sessionId = localStorage.getItem('chat_session_id');
  if(!sessionId){
    sessionId = uuidv4();
    localStorage.setItem('chat_session_id', sessionId);
  }

  loadChatHistory();

  async function sendMsg(){
    const text = input.value.trim();
    if(!text) return;
    appendMessage(text, 'user');
    saveChatHistory();
    input.value = '';
    const token = await csrfToken();

    // show typing indicator while waiting
    setTyping(true);
    setLoadingButton(true);
    try{
      const form = new URLSearchParams();
      form.append('message', text);
      form.append('session_id', sessionId);

      const r = await fetch('/chatbot/api/', { method:'POST', headers:{ 'X-CSRFToken': token }, body: form });
      const j = await r.json();

      setTyping(false);
      setLoadingButton(false);
      appendMessage(j.reply || 'No reply', 'bot');
      saveChatHistory();

      // server may return a canonical session id (optional); persist if provided
      if(j.session_id){
        sessionId = j.session_id;
        localStorage.setItem('chat_session_id', sessionId);
      }
    }catch(e){
      setTyping(false);
      setLoadingButton(false);
      appendMessage('Network error', 'bot');
      saveChatHistory();
    }
  }

  send.addEventListener('click', sendMsg);
  input.addEventListener('keydown', function(e){ if(e.key === 'Enter') sendMsg(); });
});
