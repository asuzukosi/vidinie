// Page Navigation System
const pages = document.querySelectorAll('.page');
const navLinks = document.querySelectorAll('.nav-links a');
const logo = document.querySelector('.logo');

let currentPage = 'home';
let isTransitioning = false;

// Page order for scroll navigation
const pageOrder = ['home', 'pricing', 'features', 'support', 'faq'];
let scrollTimeout = null;
let isScrolling = false;

// Detect Safari mobile (which may have inverted scroll behavior)
const isSafariMobile = /iPhone|iPad|iPod/.test(navigator.userAgent) && !window.MSStream;

// Navigate to a page
function navigateToPage(pageId) {
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
            
            // Set up scroll listeners for the new page
            setupContentPageScrollListeners();
        }, 50);
    }, 300);
}

// Navigation click handlers
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const pageId = link.getAttribute('data-page');
        navigateToPage(pageId);
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

// Helper to check if we can navigate in a direction
function canNavigateNext() {
    return getCurrentPageIndex() < pageOrder.length - 1;
}

function canNavigatePrevious() {
    return getCurrentPageIndex() > 0;
}

// Handle scroll events
function handleScroll(e) {
    if (isTransitioning || isScrolling) return;
    
    // Check if we're on a content page with scrollable content
    const currentPageEl = document.getElementById(currentPage);
    const contentPage = currentPageEl.querySelector('.content-page');
    
    let deltaY = e.deltaY;
    
    // On Safari mobile, sometimes deltaY is inverted. We'll use the actual value
    // but add extra validation for the home page to prevent wrong navigation
    
    if (contentPage) {
        // For content pages, only navigate if at top (scrolling up) or bottom (scrolling down)
        const scrollTop = contentPage.scrollTop;
        const scrollHeight = contentPage.scrollHeight;
        const clientHeight = contentPage.clientHeight;
        const isAtTop = scrollTop <= 5; // Small threshold for better detection
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 5;
        
        // Use deltaY to detect scroll direction
        const scrollDown = deltaY > 0;
        const scrollUp = deltaY < 0;
        
        if (scrollDown && isAtBottom) {
            // Scrolling down and at bottom - go to next page
            e.preventDefault();
            isScrolling = true;
            navigateToNextPage();
            setTimeout(() => { isScrolling = false; }, 1000);
        } else if (scrollUp && isAtTop) {
            // Scrolling up and at top - go to previous page
            e.preventDefault();
            isScrolling = true;
            navigateToPreviousPage();
            setTimeout(() => { isScrolling = false; }, 1000);
        }
        // Otherwise, allow normal scrolling within the content page
    } else {
        // For home page (no scrollable content), navigate directly
        // But be extra careful - only navigate if we're actually at the home page
        // and the direction makes sense
        const currentIndex = getCurrentPageIndex();
        
        e.preventDefault();
        
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        
        scrollTimeout = setTimeout(() => {
            // Only navigate if we're on home and scrolling down, or not on home and scrolling in valid direction
            if (deltaY > 0) {
                // Positive deltaY should mean scroll down = next page
                // But if we're on home (index 0) and this triggers, it should go to pricing
                if (currentIndex === 0) {
                    // On home page, positive deltaY = scroll down = go to next (pricing)
                    navigateToNextPage();
                } else if (canNavigateNext()) {
                    navigateToNextPage();
                }
            } else if (deltaY < 0) {
                // Negative deltaY should mean scroll up = previous page
                // But if we're on home, there's no previous page, so do nothing
                if (canNavigatePrevious()) {
                    navigateToPreviousPage();
                }
                // If on home (index 0), don't navigate - there's nowhere to go
            }
        }, 50);
    }
}

// Add wheel event listener (only for non-touch devices to avoid conflicts)
// On mobile, touch events handle navigation
const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
if (!isTouchDevice) {
    window.addEventListener('wheel', handleScroll, { passive: false });
}

// Handle scroll events on content pages for better mobile support
function handleContentPageScroll(e) {
    if (isTransitioning || isScrolling) return;
    
    const contentPage = e.target;
    const scrollTop = contentPage.scrollTop;
    const scrollHeight = contentPage.scrollHeight;
    const clientHeight = contentPage.clientHeight;
    const isAtTop = scrollTop <= 5;
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 5;
    
    // Store scroll direction for potential page navigation
    if (!contentPage.lastScrollTop) {
        contentPage.lastScrollTop = scrollTop;
    }
    
    const scrollingDown = scrollTop > contentPage.lastScrollTop;
    const scrollingUp = scrollTop < contentPage.lastScrollTop;
    
    contentPage.lastScrollTop = scrollTop;
    
    // If user tries to scroll past boundaries, allow page navigation
    // This will be handled by the touch/wheel events, but we track state here
    contentPage._isAtTop = isAtTop;
    contentPage._isAtBottom = isAtBottom;
    contentPage._scrollingDown = scrollingDown;
    contentPage._scrollingUp = scrollingUp;
}

// Set up scroll listeners on content pages after page navigation
let currentScrollListener = null;

function setupContentPageScrollListeners() {
    // Remove previous listener if it exists
    if (currentScrollListener) {
        const prevPageEl = document.querySelector('.content-page');
        if (prevPageEl) {
            prevPageEl.removeEventListener('scroll', currentScrollListener);
        }
    }
    
    const currentPageEl = document.getElementById(currentPage);
    const contentPage = currentPageEl?.querySelector('.content-page');
    
    if (contentPage) {
        // Reset scroll tracking
        contentPage.lastScrollTop = contentPage.scrollTop;
        currentScrollListener = handleContentPageScroll;
        contentPage.addEventListener('scroll', handleContentPageScroll, { passive: true });
    } else {
        currentScrollListener = null;
    }
}

// Initialize scroll listeners
setupContentPageScrollListeners();

// Also handle touch events for mobile
let touchStartY = 0;
let touchEndY = 0;
let touchStartTime = 0;
let lastTouchY = 0;
let touchMoved = false;

window.addEventListener('touchstart', (e) => {
    touchStartY = e.touches[0].clientY;
    lastTouchY = touchStartY;
    touchStartTime = Date.now();
    touchMoved = false;
}, { passive: true });

window.addEventListener('touchmove', (e) => {
    // Track if user is actually scrolling within content
    const currentPageEl = document.getElementById(currentPage);
    const contentPage = currentPageEl.querySelector('.content-page');
    
    if (contentPage) {
        const currentY = e.touches[0].clientY;
        const deltaY = lastTouchY - currentY;
        lastTouchY = currentY;
        
        // Check scroll boundaries
        const scrollTop = contentPage.scrollTop;
        const scrollHeight = contentPage.scrollHeight;
        const clientHeight = contentPage.clientHeight;
        const isAtTop = scrollTop <= 5;
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 5;
        
        // If there's significant vertical movement, mark as moved
        if (Math.abs(deltaY) > 5) {
            touchMoved = true;
            
            // If at boundary and trying to scroll past it, allow the gesture
            // This helps with Safari mobile's momentum scrolling
            if ((isAtTop && deltaY < 0) || (isAtBottom && deltaY > 0)) {
                // User is trying to scroll past boundary - this is a navigation gesture
                // Don't prevent default here, let touchend handle it
            }
        }
    } else {
        // On home page, any movement is a navigation gesture
        const currentY = e.touches[0].clientY;
        const deltaY = lastTouchY - currentY;
        if (Math.abs(deltaY) > 5) {
            touchMoved = true;
        }
        lastTouchY = currentY;
    }
}, { passive: true });

window.addEventListener('touchend', (e) => {
    if (isTransitioning || isScrolling) return;
    
    touchEndY = e.changedTouches[0].clientY;
    const swipeDistance = touchStartY - touchEndY;
    const swipeTime = Date.now() - touchStartTime;
    const minSwipeDistance = 50;
    const maxSwipeTime = 600; // Max time for a swipe gesture
    
    const currentPageEl = document.getElementById(currentPage);
    const contentPage = currentPageEl.querySelector('.content-page');
    
    if (contentPage) {
        // Re-check scroll position at touchend (might have changed during touch)
        const scrollTop = contentPage.scrollTop;
        const scrollHeight = contentPage.scrollHeight;
        const clientHeight = contentPage.clientHeight;
        const isAtTop = scrollTop <= 10; // Slightly larger threshold for better detection
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
        
        // Only navigate if at boundaries and it's a clear swipe gesture
        // Swipe down (finger moves down screen) = negative swipeDistance = should scroll down = go to next page
        // Swipe up (finger moves up screen) = positive swipeDistance = should scroll up = go to previous page
        if (swipeDistance < -minSwipeDistance && isAtBottom && swipeTime < maxSwipeTime) {
            // Swipe down and at bottom - go to next page
            e.preventDefault();
            e.stopPropagation();
            isScrolling = true;
            navigateToNextPage();
            setTimeout(() => { isScrolling = false; }, 1000);
        } else if (swipeDistance > minSwipeDistance && isAtTop && swipeTime < maxSwipeTime) {
            // Swipe up and at top - go to previous page
            e.preventDefault();
            e.stopPropagation();
            isScrolling = true;
            navigateToPreviousPage();
            setTimeout(() => { isScrolling = false; }, 1000);
        }
    } else {
        // For home page, allow swipes to navigate (quick swipes only)
        if (swipeTime < maxSwipeTime && Math.abs(swipeDistance) > minSwipeDistance) {
            if (swipeDistance < -minSwipeDistance) {
                // Swipe down (finger moves down) - go to next page (pricing)
                e.preventDefault();
                e.stopPropagation();
                navigateToNextPage();
            } else if (swipeDistance > minSwipeDistance) {
                // Swipe up (finger moves up) - go to previous page
                // But on home page, there's no previous, so do nothing
                // This prevents the bug where scrolling up on home goes to pricing
                if (canNavigatePrevious()) {
                    e.preventDefault();
                    e.stopPropagation();
                    navigateToPreviousPage();
                }
            }
        }
    }
    
    // Reset touch tracking
    touchMoved = false;
    touchStartY = 0;
    touchEndY = 0;
    lastTouchY = 0;
}, { passive: false });

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