// Czekamy, aż cały dokument HTML zostanie w pełni załadowany i przetworzony.
// Używamy TYLKO JEDNEGO nasłuchiwacza na cały plik.
document.addEventListener('DOMContentLoaded', function () {

    function handleNavbarScroll() {
        const navbar = document.querySelector(".custom-navbar");
        const logo = document.querySelector(".navbar-logo");

        if (!navbar || !logo) return;

        window.addEventListener("scroll", function () {
            if (window.scrollY > 50) {
                navbar.style.backgroundColor = "rgba(15, 15, 15, 0.65)";
                navbar.style.backdropFilter = "blur(8px)";
                navbar.style.padding = "5px 5px";
                logo.style.width = "90px";
            } else {
                navbar.style.backgroundColor = "transparent";
                navbar.style.backdropFilter = "none";
                navbar.style.padding = "7px 7px";
                logo.style.width = "140px";
            }
        });
    }
    function handleScrollToTopButton() {
        const scrollToTopBtn = document.getElementById("scrollToTopBtn");

        if (!scrollToTopBtn) {
            return;
        }

        window.addEventListener("scroll", function () {
            if (window.scrollY > 300) {
                scrollToTopBtn.style.opacity = "1";
                scrollToTopBtn.style.visibility = "visible";
            } else {
                scrollToTopBtn.style.opacity = "0";
                scrollToTopBtn.style.visibility = "hidden";
            }
        });

        scrollToTopBtn.addEventListener("click", function () {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }
    function handleScrollDownButton() {
        const scrollDownButtons = document.querySelectorAll('.scroll-down-btn');
        scrollDownButtons.forEach(button => {
            button.addEventListener('click', function (e) {
                e.preventDefault();
                const headerElement = this.closest('header');
                if (headerElement) {
                    const mainContent = headerElement.nextElementSibling;
                    if (mainContent) {
                        mainContent.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            });
        });
    }

    function handleToastNotifications() {
        const toastContainer = document.querySelector('.toast-container');
        if (toastContainer) {
            const toastElList = toastContainer.querySelectorAll('.toast');
            
            [...toastElList].forEach((toastEl, index) => {
                // Używamy pełnej inicjalizacji Bootstrapa, która obsługuje autohide i delay
                const toast = new bootstrap.Toast(toastEl, {
                    autohide: true,
                    delay: 8000 // 8000 ms = 8 sekund (tyle co animacja paska w CSS)
                });
    
                const progressBar = toastEl.querySelector('.toast-progress-bar-inner');
    
                // Dodajemy logikę do pauzowania animacji paska, gdy myszka jest nad toastem
                if (progressBar) {
                    toastEl.addEventListener('mouseenter', () => {
                        progressBar.style.animationPlayState = 'paused';
                    });
                    toastEl.addEventListener('mouseleave', () => {
                        progressBar.style.animationPlayState = 'running';
                    });
                }
    
                // Pokazujemy każdy toast z niewielkim opóźnieniem
                setTimeout(() => {
                    toast.show();
                }, index * 700);
            });
        }
    }
    
    handleNavbarScroll();
    handleScrollToTopButton();
    handleScrollDownButton();
    handleToastNotifications();


});