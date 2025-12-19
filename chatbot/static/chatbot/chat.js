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

document.addEventListener('DOMContentLoaded', function(){
  const input = document.getElementById('chatbot-input-field');
  const send = document.getElementById('chatbot-send');

  // ensure we have a persisted session id for the chat widget
  let sessionId = localStorage.getItem('chat_session_id');
  if(!sessionId){
    sessionId = uuidv4();
    localStorage.setItem('chat_session_id', sessionId);
  }

  async function sendMsg(){
    const text = input.value.trim();
    if(!text) return;
    appendMessage(text, 'user');
    input.value = '';
    const token = await csrfToken();

    const form = new URLSearchParams();
    form.append('message', text);
    form.append('session_id', sessionId);
    try{
      const r = await fetch('/chatbot/api/', { method:'POST', headers:{ 'X-CSRFToken': token }, body: form });
      const j = await r.json();
      appendMessage(j.reply || 'No reply', 'bot');

      // server may return a canonical session id (optional); persist if provided
      if(j.session_id){
        sessionId = j.session_id;
        localStorage.setItem('chat_session_id', sessionId);
      }
    }catch(e){
      appendMessage('Network error', 'bot');
    }
  }

  send.addEventListener('click', sendMsg);
  input.addEventListener('keydown', function(e){ if(e.key === 'Enter') sendMsg(); });
});
