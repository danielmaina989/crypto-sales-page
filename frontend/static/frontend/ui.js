// Small UI helpers for interactive components
(function(window){
  function toggleLoading(btn, isLoading){
    if(!btn) return;
    if(isLoading){
      btn.classList.add('loading');
      btn.disabled = true;
    } else {
      btn.classList.remove('loading');
      btn.disabled = false;
    }
  }

  // A simple delegation: any button with data-loading="true" will get the loading class toggled
  function delegatedLoadingHandler(e){
    var btn = e.target.closest('[data-loading]');
    if(!btn) return;
    // if attribute is present and value is "auto", we toggle on click and expect callers to remove when ready
    if(btn.getAttribute('data-loading') === 'auto'){
      toggleLoading(btn, true);
    }
  }

  document.addEventListener('click', delegatedLoadingHandler, true);

  // Expose globally
  window.UI = window.UI || {};
  window.UI.toggleLoading = toggleLoading;

})(window);

