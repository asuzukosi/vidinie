// Simple smooth scroll navigation
const navLinks = document.querySelectorAll('.nav-links a');
const logo = document.querySelector('.logo a');

// Navigation click handlers - smooth scroll to sections
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
            e.preventDefault();
            const targetId = href.substring(1);
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                const navbar = document.querySelector('.navbar');
                const navbarHeight = navbar ? navbar.offsetHeight : 0;
                const targetPosition = targetSection.offsetTop - navbarHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        }
    });
});

// Logo click - scroll to home
if (logo) {
    logo.addEventListener('click', (e) => {
        e.preventDefault();
        const homeSection = document.getElementById('home');
        if (homeSection) {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
    });
}

// Card hover effects (only on home page)
const cards = document.querySelectorAll('.card');
const cardVisual = document.querySelector('.card-visual');

if (cardVisual) {
    cardVisual.addEventListener('mousemove', (e) => {
        const rect = cardVisual.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        cards.forEach((card) => {
            if (card.classList.contains('card-left')) {
                card.style.transform = `
                    rotateY(${-15 + rotateY}deg) 
                    rotateX(${5 + rotateX}deg)
                    translateZ(20px)
                `;
            } else {
                card.style.transform = `
                    rotateY(${15 + rotateY}deg) 
                    rotateX(${5 + rotateX}deg)
                    translateZ(20px)
                `;
            }
        });
    });
    
    cardVisual.addEventListener('mouseleave', () => {
        cards.forEach(card => {
            if (card.classList.contains('card-left')) {
                card.style.transform = 'rotateY(-15deg) rotateX(5deg) translateZ(0)';
            } else {
                card.style.transform = 'rotateY(15deg) rotateX(5deg) translateZ(0)';
            }
        });
    });
}

// Button interactions
const allButtons = document.querySelectorAll('button, .app-store, .google-play');

allButtons.forEach(button => {
    button.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-2px)';
    });
    
    button.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
    
    button.addEventListener('mousedown', function() {
        this.style.transform = 'scale(0.98)';
    });
    
    button.addEventListener('mouseup', function() {
        this.style.transform = 'translateY(-2px)';
    });
});

// FAQ accordion functionality
const faqItems = document.querySelectorAll('.faq-item');

faqItems.forEach(item => {
    const answer = item.querySelector('.faq-answer');
    answer.style.maxHeight = '0';
    answer.style.overflow = 'hidden';
    answer.style.transition = 'max-height 0.3s ease';
    
    let isOpen = true; // Start open
    answer.style.maxHeight = answer.scrollHeight + 'px';
    
    item.addEventListener('click', () => {
        if (isOpen) {
            answer.style.maxHeight = '0';
            item.style.opacity = '0.6';
        } else {
            answer.style.maxHeight = answer.scrollHeight + 'px';
            item.style.opacity = '1';
        }
        isOpen = !isOpen;
    });
});

console.log('%cvidinie.', 'color: #FF6B4A; font-size: 24px; font-weight: 600;');
console.log('%cTransform articles into engaging videos.', 'color: #A855F7; font-size: 14px;');
