async function csrfToken(){
  const re = /(^|; )csrftoken=([^;]+)/;
  const m = document.cookie.match(re);
  return m ? decodeURIComponent(m[2]) : '';
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

  async function sendMsg(){
    const text = input.value.trim();
    if(!text) return;
    appendMessage(text, 'user');
    input.value = '';
    const token = await csrfToken();
    const form = new URLSearchParams();
    form.append('message', text);
    try{
      const r = await fetch('/chatbot/api/', { method:'POST', headers:{ 'X-CSRFToken': token }, body: form });
      const j = await r.json();
      appendMessage(j.reply || 'No reply', 'bot');
    }catch(e){
      appendMessage('Network error', 'bot');
    }
  }

  send.addEventListener('click', sendMsg);
  input.addEventListener('keydown', function(e){ if(e.key === 'Enter') sendMsg(); });
});

