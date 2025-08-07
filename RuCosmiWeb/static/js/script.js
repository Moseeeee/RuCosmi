document.addEventListener('DOMContentLoaded', function() {
    const mainHeader = document.getElementById('main-header');

    // Анимация шапки при скролле
    window.addEventListener('scroll', function() {
        const scrollPosition = window.scrollY;
        const heroHeight = document.querySelector('.hero-section').offsetHeight;

        if (scrollPosition > heroHeight * 0.3) {
            const progress = Math.min((scrollPosition - heroHeight * 0.3) / (heroHeight * 0.4), 1);

            mainHeader.style.opacity = progress;
            mainHeader.style.transform = `translateY(${progress * 10}px)`;

            if (progress > 0.9) {
                mainHeader.classList.add('visible');
            } else {
                mainHeader.classList.remove('visible');
            }
        } else {
            mainHeader.style.opacity = '0';
            mainHeader.style.transform = 'translateY(-10px)';
            mainHeader.classList.remove('visible');
        }
    });

    // Анимации карточек услуг
    document.querySelectorAll('.service-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) rotateZ(-1deg)';
            this.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.15)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) rotateZ(0)';
            this.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.1)';
        });
    });
});