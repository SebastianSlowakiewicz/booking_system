document.addEventListener('DOMContentLoaded', function () {
    /**
     * Funkcja obsługująca zmianę wyglądu nawigacji podczas przewijania strony.
     */
    function handleNavbarScroll() {
        const navbar = document.querySelector(".custom-navbar");
        const logo = document.querySelector(".navbar-logo");

        // Sprawdzamy, czy elementy istnieją na stronie
        if (!navbar || !logo) {
            return;
        }

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

    /**
     * Funkcja obsługująca przycisk "przewiń do góry".
     */
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

    /**
     * Funkcja obsługująca slider z ofertami.
     */
    function handleOfferSlider() {
        const offerSlider = document.getElementById('offerSlider');
        const prevArrow = document.getElementById('prevArrow');
        const nextArrow = document.getElementById('nextArrow');

        if (!offerSlider || !prevArrow || !nextArrow) {
            return;
        }

        let scrollAmount = 320; // Domyślna wartość

        const calculateScrollAmount = () => {
            const firstItem = offerSlider.querySelector('.offer-item');
            if (firstItem) {
                const itemWidth = firstItem.offsetWidth;
                const itemMarginRight = parseInt(window.getComputedStyle(firstItem).marginRight);
                scrollAmount = itemWidth + itemMarginRight;
            }
        };
        
        // UWAGA: Funkcja checkScrollArrows nie została zdefiniowana w Twoim kodzie.
        // Dodałem pustą definicję, aby uniknąć błędów. Musisz tu wstawić swoją logikę.
        function checkScrollArrows() {
            // TODO: Wstaw tutaj swoją logikę do pokazywania/ukrywania strzałek
            // na podstawie pozycji przewinięcia slidera.
            const maxScrollLeft = offerSlider.scrollWidth - offerSlider.clientWidth;
            prevArrow.style.display = offerSlider.scrollLeft > 0 ? 'block' : 'none';
            nextArrow.style.display = offerSlider.scrollLeft < maxScrollLeft - 1 ? 'block' : 'none';
        }


        calculateScrollAmount();
        window.addEventListener('resize', calculateScrollAmount);
        
        prevArrow.addEventListener('click', function() {
            offerSlider.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });

        nextArrow.addEventListener('click', function() {
            offerSlider.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });

        offerSlider.addEventListener('scroll', checkScrollArrows);
        checkScrollArrows(); // Sprawdź stan początkowy
    }

    /**
     * Funkcja obsługująca wyskakujące powiadomienia (toasty) z ofertami specjalnymi.
     */
    function handleSpecialOfferToasts() {
        const specialOfferToasts = document.querySelectorAll('.toast-rich-offer');
        
        if (specialOfferToasts.length === 0) {
            return;
        }

        specialOfferToasts.forEach((toastEl, index) => {
            const toast = new bootstrap.Toast(toastEl, {
                autohide: true,
                delay: 8000
            });

            const progressBar = toastEl.querySelector('.toast-progress-bar-inner');

            toastEl.addEventListener('mouseover', () => {
                if (progressBar) progressBar.style.animationPlayState = 'paused';
            });

            toastEl.addEventListener('mouseout', () => {
                if (progressBar) progressBar.style.animationPlayState = 'running';
            });
            
            toastEl.addEventListener('hidden.bs.toast', () => {
                if (progressBar) progressBar.style.animation = 'none';
            });

            setTimeout(() => {
                if (progressBar) progressBar.style.animation = 'shrink 8s linear forwards';
                toast.show();
            }, 1000 * (index + 1));
        });
    }

    // Wywołanie wszystkich funkcji inicjujących
    handleNavbarScroll();
    handleScrollToTopButton();
    handleOfferSlider();
    handleSpecialOfferToasts();
});

document.addEventListener('DOMContentLoaded', function() {
    const track = document.getElementById('custom-scrollbar-track');
    const thumb = document.getElementById('custom-scrollbar-thumb');

    // Jeśli elementy paska nie istnieją na stronie, zakończ działanie skryptu
    if (!track || !thumb) {
        return;
    }

    function updateScrollbar() {
        const viewportHeight = window.innerHeight;
        const pageHeight = document.documentElement.scrollHeight;
        const scrollTop = window.pageYOffset;

        // Jeśli strona nie jest przewijalna, ukryj nasz pasek
        if (pageHeight <= viewportHeight) {
            track.style.display = 'none';
            return;
        }
        track.style.display = 'block';

        // --- DYNAMICZNE OBLICZANIE WYSOKOŚCI SUWAKA ---
        // Wysokość suwaka jest proporcjonalna do tego, jak duża część strony jest widoczna.
        const thumbHeight = (viewportHeight / pageHeight) * track.clientHeight;
        // Ustawiamy minimalną wysokość suwaka, aby nie był zbyt mały
        thumb.style.height = `${Math.max(20, thumbHeight)}px`;

        // --- OBLICZANIE POZYCJI SUWAKA ---
        const scrollablePageArea = pageHeight - viewportHeight;
        const scrollPercentage = scrollTop / scrollablePageArea;
        
        const scrollableTrackArea = track.clientHeight - thumb.clientHeight;
        const thumbTopPosition = scrollPercentage * scrollableTrackArea;
        
        thumb.style.top = `${thumbTopPosition}px`;
    }

    // --- LOGIKA PRZECIĄGANIA SUWAKA ---
    let isDragging = false;
    let startY;
    let startScrollTop;

    thumb.addEventListener('mousedown', (e) => {
        e.preventDefault();
        isDragging = true;
        startY = e.clientY;
        startScrollTop = window.pageYOffset;
        thumb.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        e.preventDefault();

        const deltaY = e.clientY - startY;
        const trackHeight = track.clientHeight;
        const thumbHeight = thumb.clientHeight;
        
        // Oblicz, jak ruch myszki przekłada się na przewinięcie strony
        const pageHeight = document.documentElement.scrollHeight;
        const viewportHeight = window.innerHeight;
        const maxPageScroll = pageHeight - viewportHeight;
        const maxThumbScroll = trackHeight - thumbHeight;
        
        const scrollDelta = (deltaY / maxThumbScroll) * maxPageScroll;
        
        window.scrollTo(0, startScrollTop + scrollDelta);
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            thumb.style.cursor = 'grab';
            document.body.style.userSelect = '';
        }
    });
    
    // Nasłuchuj na zdarzenia i uruchom funkcję na starcie
    window.addEventListener('scroll', updateScrollbar);
    window.addEventListener('resize', updateScrollbar);
    updateScrollbar(); // Wywołanie początkowe
});

document.addEventListener('DOMContentLoaded', function() {
    // 1. Logika dla przycisku przewijającego w dół z karuzeli
    const scrollDownButtons = document.querySelectorAll('.scroll-down-btn');
    
    scrollDownButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Znajdujemy element <header>, w którym jest karuzela
            const headerElement = this.closest('header');
            
            if (headerElement) {
                // Celem jest następny element po <header>, czyli <main>
                const mainContent = headerElement.nextElementSibling;
                
                if (mainContent) {
                    mainContent.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // 2. Możesz tutaj zostawić lub dodać inne swoje skrypty, np. dla przycisku "do góry"
    const scrollToTopBtn = document.getElementById("scrollToTopBtn");
    
    if (scrollToTopBtn) {
        window.onscroll = function() {
            if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
                scrollToTopBtn.style.display = "block";
            } else {
                scrollToTopBtn.style.display = "none";
            }
        };

        scrollToTopBtn.addEventListener("click", function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});