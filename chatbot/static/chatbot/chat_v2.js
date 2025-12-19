(function(){
  const chatPanel = document.getElementById('chat-panel');
  const toggleBtn = document.getElementById('chat-toggle');
  const closeBtn = document.getElementById('chat-close');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messages = document.getElementById('chat-messages');
  const typing = document.getElementById('chat-typing');

  if(!toggleBtn) return;

  toggleBtn.addEventListener('click', ()=>{
    if(!chatPanel) return;
    chatPanel.classList.toggle('hidden');
    chatPanel.setAttribute('aria-hidden', chatPanel.classList.contains('hidden'));
  });
  closeBtn?.addEventListener('click', ()=>chatPanel.classList.add('hidden'));

  function addMessage(text, role){
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerText = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    saveChat();
  }

  function showTyping(show=true){
    if(!typing) return;
    typing.classList.toggle('hidden', !show);
    typing.setAttribute('aria-hidden', !show);
  }

  function saveChat(){
    try{ localStorage.setItem('chat_history', messages.innerHTML); }catch(e){}
  }
  function loadChat(){
    try{ const saved = localStorage.getItem('chat_history'); if(saved) messages.innerHTML = saved; }catch(e){}
  }

  async function postMessageToServer(text){
    // use CSRF token cookie if present
    const re = /(^|; )csrftoken=([^;]+)/;
    const m = document.cookie.match(re);
    const token = m ? decodeURIComponent(m[2]) : '';

    try{
      const res = await fetch('/chatbot/api/', {
        method: 'POST',
        headers: { 'X-CSRFToken': token },
        body: new URLSearchParams({ message: text })
      });
      return await res.json();
    }catch(e){ return { reply: null, error: true }; }
  }

  form?.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const text = input.value.trim();
    if(!text) return;
    addMessage(text, 'user');
    input.value = '';
    showTyping(true);

    const r = await postMessageToServer(text);
    showTyping(false);
    if(r && !r.error){ addMessage(r.reply || 'No reply', 'bot'); }
    else{ addMessage('⚠️ Network error. Please try again.', 'bot'); }
  });

  loadChat();
})();

