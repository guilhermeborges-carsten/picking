// Melhorias para experiência mobile
document.addEventListener('DOMContentLoaded', function() {
    
    // Ajustar altura do viewport para mobile
    function setViewportHeight() {
        let vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    
    setViewportHeight();
    window.addEventListener('resize', setViewportHeight);
    window.addEventListener('orientationchange', setViewportHeight);
    
    // Melhorar navegação mobile
    const navbarCollapse = document.querySelector('.navbar-collapse');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    // Fechar menu mobile ao clicar em um link
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 992) { // Bootstrap lg breakpoint
                const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                bsCollapse.hide();
            }
        });
    });
    
    // Melhorar experiência de formulários em mobile
    const formInputs = document.querySelectorAll('input, select, textarea');
    
    formInputs.forEach(input => {
        // Adicionar classe para melhorar visualização em mobile
        if (window.innerWidth <= 768) {
            input.classList.add('mobile-input');
        }
        
        // Melhorar foco em mobile
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
            
            // Scroll suave para o campo focado em mobile
            if (window.innerWidth <= 768) {
                setTimeout(() => {
                    this.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                }, 300);
            }
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
    
    // Melhorar botões em mobile
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        if (window.innerWidth <= 768) {
            button.classList.add('mobile-btn');
        }
        
        // Adicionar feedback visual para touch
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.98)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Melhorar tabelas em mobile
    const tables = document.querySelectorAll('.table');
    
    tables.forEach(table => {
        if (window.innerWidth <= 768) {
            table.classList.add('mobile-table');
            
            // Adicionar scroll horizontal para tabelas grandes
            if (table.scrollWidth > table.clientWidth) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        }
    });
    
    // Melhorar cards em mobile
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        if (window.innerWidth <= 768) {
            card.classList.add('mobile-card');
        }
    });
    
    // Detectar orientação do dispositivo
    function handleOrientation() {
        if (window.orientation === 90 || window.orientation === -90) {
            document.body.classList.add('landscape');
        } else {
            document.body.classList.remove('landscape');
        }
    }
    
    window.addEventListener('orientationchange', handleOrientation);
    handleOrientation();
    
    // Melhorar performance em mobile
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // Recarregar funcionalidades após redimensionamento
            setViewportHeight();
            handleOrientation();
        }, 250);
    });
    
    // Adicionar suporte para gestos touch (swipe)
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                // Swipe para esquerda
                console.log('Swipe para esquerda');
            } else {
                // Swipe para direita
                console.log('Swipe para direita');
            }
        }
    }
    
    // Melhorar acessibilidade em mobile
    const focusableElements = document.querySelectorAll(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    // Adicionar indicador visual para elementos focáveis
    focusableElements.forEach(element => {
        if (window.innerWidth <= 768) {
            element.setAttribute('data-mobile-focusable', 'true');
        }
    });
    
    // Melhorar feedback visual para interações touch
    document.addEventListener('touchstart', function() {
        document.body.classList.add('touch-active');
    });
    
    document.addEventListener('touchend', function() {
        setTimeout(() => {
            document.body.classList.remove('touch-active');
        }, 100);
    });
    
    // Adicionar classe para dispositivos touch
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        document.body.classList.add('touch-device');
    }
    
    // Melhorar navegação por teclado em mobile
    document.addEventListener('keydown', function(e) {
        if (window.innerWidth <= 768) {
            // Permitir navegação por teclado em mobile
            if (e.key === 'Tab') {
                e.preventDefault();
                const focusable = Array.from(focusableElements).filter(el => 
                    !el.hasAttribute('disabled') && el.offsetParent !== null
                );
                const currentIndex = focusable.indexOf(document.activeElement);
                let nextIndex = 0;
                
                if (e.shiftKey) {
                    nextIndex = currentIndex > 0 ? currentIndex - 1 : focusable.length - 1;
                } else {
                    nextIndex = currentIndex < focusable.length - 1 ? currentIndex + 1 : 0;
                }
                
                focusable[nextIndex].focus();
            }
        }
    });
    
    console.log('Mobile enhancements carregados com sucesso! 📱');
});
