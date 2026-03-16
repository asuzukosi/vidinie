const navbar = document.querySelector('.navbar');
const navLinks = document.querySelectorAll('.nav-links a');
const logo = document.querySelector('.logo a');
const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-links');

const closeMobileNav = () => {
    if (!navToggle || !navMenu) {
        return;
    }

    navToggle.setAttribute('aria-expanded', 'false');
    navMenu.classList.remove('is-open');
};

const updateNavbarState = () => {
    if (!navbar) {
        return;
    }

    navbar.classList.toggle('is-scrolled', window.scrollY > 18);
};

updateNavbarState();
window.addEventListener('scroll', updateNavbarState);

if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
        const isOpen = navToggle.getAttribute('aria-expanded') === 'true';
        navToggle.setAttribute('aria-expanded', String(!isOpen));
        navMenu.classList.toggle('is-open', !isOpen);
    });
}

navLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
        const href = link.getAttribute('href');

        if (!href || !href.startsWith('#')) {
            closeMobileNav();
            return;
        }

        event.preventDefault();
        const targetSection = document.querySelector(href);

        if (!targetSection) {
            return;
        }

        const navbarHeight = navbar ? navbar.offsetHeight : 0;
        const targetPosition = targetSection.getBoundingClientRect().top + window.scrollY - navbarHeight - 12;

        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });

        closeMobileNav();
    });
});

if (logo) {
    logo.addEventListener('click', (event) => {
        const href = logo.getAttribute('href');
        if (href !== '#home') {
            return;
        }

        event.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        closeMobileNav();
    });
}

// code for reveal sections on scroll
const revealSections = document.querySelectorAll('.main-content > .section');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

if (revealSections.length) {
    revealSections.forEach((section, index) => {
        if (index === 0 || prefersReducedMotion.matches) {
            section.classList.add('is-visible');
        }
    });

    if (!prefersReducedMotion.matches && 'IntersectionObserver' in window) {
        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            });
        }, {
            threshold: 0.18,
            rootMargin: '0px 0px -10% 0px'
        });

        revealSections.forEach((section, index) => {
            if (index === 0) {
                return;
            }

            revealObserver.observe(section);
        });
    } else {
        revealSections.forEach((section) => {
            section.classList.add('is-visible');
        });
    }
}

// code for faq items
const faqItems = document.querySelectorAll('.faq-item');

faqItems.forEach((item, index) => {
    const trigger = item.querySelector('.faq-question');
    const answer = item.querySelector('.faq-answer');

    if (!trigger || !answer) {
        return;
    }

    const setOpenState = (isOpen) => {
        item.classList.toggle('is-open', isOpen);
        trigger.setAttribute('aria-expanded', String(isOpen));
        answer.style.maxHeight = isOpen ? `${answer.scrollHeight}px` : '0px';
    };

    trigger.setAttribute('aria-expanded', index === 0 ? 'true' : 'false');
    setOpenState(index === 0);

    trigger.addEventListener('click', () => {
        const isOpen = item.classList.contains('is-open');
        setOpenState(!isOpen);
    });
});

window.addEventListener('resize', () => {
    if (window.innerWidth > 820) {
        closeMobileNav();
    }

    faqItems.forEach((item) => {
        const answer = item.querySelector('.faq-answer');
        if (item.classList.contains('is-open') && answer) {
            answer.style.maxHeight = `${answer.scrollHeight}px`;
        }
    });
});

const consoleMessages = {
    en: 'turn articles and pdfs into polished videos.',
    es: 'convierte articulos y pdfs en videos pulidos.',
    fr: 'transformez articles et pdfs en videos soignees.',
    de: 'verwandeln sie artikel und pdfs in hochwertige videos.',
    it: 'trasforma articoli e pdf in video curati.',
    'pt-br': 'transforme artigos e pdfs em videos refinados.',
    ru: 'превращайте статьи и pdf в качественные видео.'
};

const pageLanguage = (document.documentElement.lang || 'en').toLowerCase();
const languageKey = consoleMessages[pageLanguage]
    ? pageLanguage
    : pageLanguage.startsWith('pt')
        ? 'pt-br'
        : pageLanguage.startsWith('ru')
            ? 'ru'
            : 'en';

console.log('%cvidinie.', 'color: #161613; font-size: 24px; font-weight: 700;');
console.log(`%c${consoleMessages[languageKey] || consoleMessages.en}`, 'color: #a95de3; font-size: 14px;');
