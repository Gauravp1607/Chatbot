document.addEventListener('DOMContentLoaded', () => {
    if (navigator.userAgent.includes('LivestockAI-Android-App') || window.innerWidth <= 768) {
        document.body.classList.add('is-android-app');
    }

    const navbar = document.getElementById('siteNavbar');
    const backToTop = document.getElementById('backToTop');
    const revealItems = document.querySelectorAll('.reveal');

    const updateNavbar = () => {
        if (!navbar) return;
        navbar.classList.toggle('scrolled', window.scrollY > 24);
    };

    const updateBackToTop = () => {
        if (!backToTop) return;
        backToTop.classList.toggle('show', window.scrollY > 400);
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    revealItems.forEach((item) => observer.observe(item));

    updateNavbar();
    updateBackToTop();
    window.addEventListener('scroll', () => {
        updateNavbar();
        updateBackToTop();
    });

    if (backToTop) {
        backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    }

    /* -------------------------------------------------------------------
       Bulletproof Mobile Navbar Toggler for Android WebView & Browsers
    ---------------------------------------------------------------------- */
    const togglers = document.querySelectorAll('.mobile-toggler-btn, [data-bs-toggle="collapse"]');
    togglers.forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = btn.getAttribute('data-bs-target');
            if (targetId) {
                const targetEl = document.querySelector(targetId);
                if (targetEl) {
                    const isShown = targetEl.classList.contains('show');
                    if (isShown) {
                        targetEl.classList.remove('show');
                    } else {
                        targetEl.classList.add('show');
                    }
                    btn.setAttribute('aria-expanded', !isShown);
                }
            }
        });
    });

    // Auto-close menu drawer when clicking any link inside it
    const navLinks = document.querySelectorAll('#navbarNav .nav-link, #navbarNav .btn, #navbarNav .dropdown-item');
    navLinks.forEach((link) => {
        link.addEventListener('click', () => {
            const targetEl = document.getElementById('navbarNav');
            if (targetEl && targetEl.classList.contains('show')) {
                targetEl.classList.remove('show');
            }
        });
    });
});
