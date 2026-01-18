// Page Navigation System
const pages = document.querySelectorAll('.page');
const navLinks = document.querySelectorAll('.nav-links a');
const logo = document.querySelector('.logo');

let currentPage = 'home';
let isTransitioning = false;

// Check if mobile
let isMobile = window.innerWidth <= 768;

// Initialize mobile layout
function initMobileLayout() {
    if (isMobile) {
        // Make all pages visible and stacked
        pages.forEach(page => {
            page.classList.add('active');
            page.style.position = 'relative';
            page.style.opacity = '1';
            page.style.visibility = 'visible';
        });
        
        // Disable body overflow hidden
        document.body.style.overflowY = 'auto';
        document.body.style.height = 'auto';
        
        // Make page container scrollable
        const pageContainer = document.querySelector('.page-container');
        if (pageContainer) {
            pageContainer.style.height = 'auto';
            pageContainer.style.overflow = 'visible';
            pageContainer.style.position = 'relative';
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileLayout);
} else {
    initMobileLayout();
}

// Also handle window resize
window.addEventListener('resize', () => {
    const wasMobile = isMobile;
    isMobile = window.innerWidth <= 768;
    if (wasMobile !== isMobile) {
        if (isMobile) {
            initMobileLayout();
        } else {
            // Reset to desktop layout
            pages.forEach((page, index) => {
                if (index === 0) {
                    page.classList.add('active');
                } else {
                    page.classList.remove('active');
                }
                page.style.position = '';
                page.style.opacity = '';
                page.style.visibility = '';
            });
            document.body.style.overflowY = '';
            document.body.style.height = '';
            const pageContainer = document.querySelector('.page-container');
            if (pageContainer) {
                pageContainer.style.height = '';
                pageContainer.style.overflow = '';
                pageContainer.style.position = '';
            }
        }
    }
});

// Page order for scroll navigation
const pageOrder = ['home', 'pricing', 'features', 'support', 'faq'];
let scrollTimeout = null;
let isScrolling = false;

// Navigate to a page
function navigateToPage(pageId) {
    // On mobile, scroll to page instead of transitioning
    if (isMobile) {
        const targetPage = document.getElementById(pageId);
        if (targetPage) {
            const navbar = document.querySelector('.navbar');
            const navbarHeight = navbar ? navbar.offsetHeight : 0;
            const targetPosition = targetPage.offsetTop - navbarHeight;
            
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
            currentPage = pageId;
        }
        return;
    }
    
    if (isTransitioning || pageId === currentPage) return;
    
    isTransitioning = true;
    
    const currentPageEl = document.getElementById(currentPage);
    const nextPageEl = document.getElementById(pageId);
    
    // Start transition
    currentPageEl.classList.add('transitioning-out');
    
    setTimeout(() => {
        currentPageEl.classList.remove('active', 'transitioning-out');
        nextPageEl.classList.add('transitioning-in');
        
        // Reset scroll position of content pages
        const contentPage = nextPageEl.querySelector('.content-page');
        if (contentPage) {
            contentPage.scrollTop = 0;
        }
        
        setTimeout(() => {
            nextPageEl.classList.add('active');
            nextPageEl.classList.remove('transitioning-in');
            currentPage = pageId;
            isTransitioning = false;
        }, 50);
    }, 300);
}

// Navigation click handlers
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        const pageId = link.getAttribute('data-page');
        // Only prevent default and navigate if it's an internal page link
        if (pageId) {
            e.preventDefault();
            navigateToPage(pageId);
        }
        // If no data-page attribute, let the link work normally (e.g., external links)
    });
});

// Logo click - go home
logo.addEventListener('click', () => {
    navigateToPage('home');
});

// Scroll-based page navigation
function getCurrentPageIndex() {
    return pageOrder.indexOf(currentPage);
}

function navigateToNextPage() {
    const currentIndex = getCurrentPageIndex();
    if (currentIndex < pageOrder.length - 1) {
        navigateToPage(pageOrder[currentIndex + 1]);
    }
}

function navigateToPreviousPage() {
    const currentIndex = getCurrentPageIndex();
    if (currentIndex > 0) {
        navigateToPage(pageOrder[currentIndex - 1]);
    }
}

// Handle scroll events
function handleScroll(e) {
    // Disable scroll navigation on mobile
    if (isMobile) return;
    
    if (isTransitioning || isScrolling) return;
    
    // Check if we're on a content page with scrollable content
    const currentPageEl = document.getElementById(currentPage);
    const contentPage = currentPageEl.querySelector('.content-page');
    
    if (contentPage) {
        // For content pages, only navigate if at top (scrolling up) or bottom (scrolling down)
        const isAtTop = contentPage.scrollTop <= 0;
        const isAtBottom = contentPage.scrollTop + contentPage.clientHeight >= contentPage.scrollHeight - 10;
        
        if (e.deltaY > 0 && isAtBottom) {
            // Scrolling down and at bottom - go to next page
            e.preventDefault();
            isScrolling = true;
            navigateToNextPage();
            setTimeout(() => { isScrolling = false; }, 1000);
        } else if (e.deltaY < 0 && isAtTop) {
            // Scrolling up and at top - go to previous page
            e.preventDefault();
            isScrolling = true;
            navigateToPreviousPage();
            setTimeout(() => { isScrolling = false; }, 1000);
        }
        // Otherwise, allow normal scrolling within the content page
    } else {
        // For home page (no scrollable content), navigate directly
        e.preventDefault();
        
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        
        scrollTimeout = setTimeout(() => {
            if (e.deltaY > 0) {
                // Scrolling down
                navigateToNextPage();
            } else if (e.deltaY < 0) {
                // Scrolling up
                navigateToPreviousPage();
            }
        }, 50);
    }
}

// Add wheel event listener
window.addEventListener('wheel', handleScroll, { passive: false });

// Also handle touch events for mobile (only on desktop for page navigation)
let touchStartY = 0;
let touchEndY = 0;

if (!isMobile) {
    window.addEventListener('touchstart', (e) => {
        touchStartY = e.touches[0].clientY;
    }, { passive: true });

    window.addEventListener('touchend', (e) => {
        if (isTransitioning || isScrolling) return;
    
    touchEndY = e.changedTouches[0].clientY;
    const swipeDistance = touchStartY - touchEndY;
    const minSwipeDistance = 50;
    
    const currentPageEl = document.getElementById(currentPage);
    const contentPage = currentPageEl.querySelector('.content-page');
    
    if (contentPage) {
        const isAtTop = contentPage.scrollTop <= 0;
        const isAtBottom = contentPage.scrollTop + contentPage.clientHeight >= contentPage.scrollHeight - 10;
        
        if (swipeDistance < -minSwipeDistance && isAtBottom) {
            // Swipe down - go to next page
            isScrolling = true;
            navigateToNextPage();
            setTimeout(() => { isScrolling = false; }, 1000);
        } else if (swipeDistance > minSwipeDistance && isAtTop) {
            // Swipe up - go to previous page
            isScrolling = true;
            navigateToPreviousPage();
            setTimeout(() => { isScrolling = false; }, 1000);
        }
    } else {
        if (swipeDistance < -minSwipeDistance) {
            // Swipe down - go to next page
            navigateToNextPage();
        } else if (swipeDistance > minSwipeDistance) {
            // Swipe up - go to previous page
            navigateToPreviousPage();
        }
    }
}, { passive: true });
}

// Smooth fade-in on load
window.addEventListener('load', () => {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.6s ease';
    
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});

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

// Animate elements on scroll (for content pages)
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '0';
            entry.target.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                entry.target.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }, index * 100);
        }
    });
}, observerOptions);

// Observe pricing cards
setTimeout(() => {
    const pricingCards = document.querySelectorAll('.pricing-card');
    pricingCards.forEach(card => observer.observe(card));
    
    const featureItems = document.querySelectorAll('.feature-item');
    featureItems.forEach(item => observer.observe(item));
    
    const supportCards = document.querySelectorAll('.support-card');
    supportCards.forEach(card => observer.observe(card));
    
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => observer.observe(item));
}, 100);

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

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    // Escape key to go home
    if (e.key === 'Escape') {
        navigateToPage('home');
    }
    
    // Number keys for quick navigation
    if (e.key === '1') navigateToPage('home');
    if (e.key === '2') navigateToPage('pricing');
    if (e.key === '3') navigateToPage('features');
    if (e.key === '4') navigateToPage('support');
    if (e.key === '5') navigateToPage('faq');
});


console.log('%caxora.', 'color: #FF6B4A; font-size: 24px; font-weight: 600;');
console.log('%cYour funds, full control, anytime.', 'color: #A855F7; font-size: 14px;');
console.log('%cKeyboard shortcuts: 1=Home, 2=Pricing, 3=Features, 4=Support, 5=FAQ, ESC=Home', 'color: #6e6e73; font-size: 12px;');