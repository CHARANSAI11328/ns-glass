/* ==========================================================================
   NS-GLASS — Interactive Glass Refraction & Tilt Engine
   Provides interactive lighting, specular highlights, and tilt responsiveness
   ========================================================================== */

(function() {
  function initGlassTilt() {
    const cards = document.querySelectorAll('.glass-panel, .glass-card, .sc, .mc, .owner-card, .vcard, .safe-card');
    
    cards.forEach(card => {
      card.addEventListener('mousemove', e => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = ((y - centerY) / centerY) * -4;
        const rotateY = ((x - centerX) / centerX) * 4;
        
        card.style.transition = 'none';
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px)`;
      });
      
      card.addEventListener('mouseleave', () => {
        card.style.transition = 'transform 0.5s ease';
        card.style.transform = '';
      });
    });
  }

  function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn') || document.querySelector('.mob-btn');
    const mobileMenu = document.getElementById('mobileMenu') || document.querySelector('.mob-overlay');
    
    if (mobileMenuBtn && mobileMenu) {
      mobileMenuBtn.addEventListener('click', () => {
        mobileMenuBtn.classList.toggle('active');
        mobileMenu.classList.toggle('active');
        mobileMenu.classList.toggle('open');
        document.body.style.overflow = mobileMenu.classList.contains('active') || mobileMenu.classList.contains('open') ? 'hidden' : '';
      });
      
      mobileMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
          mobileMenuBtn.classList.remove('active');
          mobileMenu.classList.remove('active');
          mobileMenu.classList.remove('open');
          document.body.style.overflow = '';
        });
      });
    }
  }

  function init() {
    initGlassTilt();
    initMobileMenu();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
