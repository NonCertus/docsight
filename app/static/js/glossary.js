/* glossary.js — Click-to-open popovers for DOCSIS term explanations */

(function () {
  'use strict';

  function closeAll() {
    document.querySelectorAll('.glossary-hint.open').forEach(function (el) {
      el.classList.remove('open');
    });
  }

  function positionPopover(hint) {
    var pop = hint.querySelector('.glossary-popover');
    if (!pop) return;
    pop.classList.remove('above');
    var r = hint.getBoundingClientRect();
    // Position below the icon, centered
    var top = r.bottom + 8;
    var left = r.left + r.width / 2;
    pop.style.left = left + 'px';
    pop.style.top = top + 'px';
    pop.style.transform = 'translateX(-50%)';
    // Flip above if near bottom
    var popRect = pop.getBoundingClientRect();
    if (popRect.bottom > window.innerHeight - 20) {
      pop.classList.add('above');
      pop.style.top = (r.top - 8) + 'px';
      pop.style.transform = 'translateX(-50%) translateY(-100%)';
    }
  }

  document.addEventListener('click', function (e) {
    var hint = e.target.closest('.glossary-hint');
    if (hint) {
      e.preventDefault();
      e.stopPropagation();
      var wasOpen = hint.classList.contains('open');
      closeAll();
      if (!wasOpen) {
        hint.classList.add('open');
        positionPopover(hint);
      }
      return;
    }
    closeAll();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAll();
  });
})();
