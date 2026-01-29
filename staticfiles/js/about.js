    document.addEventListener("DOMContentLoaded", function () {
        function applyToggleLogic() {
            const paragraphs = document.querySelectorAll('.content-section p');
            paragraphs.forEach(function (para) {
                const existingToggle = para.parentNode.querySelector('.view-toggle-btn');
                if (window.innerWidth <= 768 && para.scrollHeight > 120 && !existingToggle) {
                    para.classList.add('truncated');

                    const toggle = document.createElement('span');
                    toggle.classList.add('view-toggle-btn');
                    toggle.textContent = 'View More';
                    para.parentNode.appendChild(toggle);

                    toggle.addEventListener('click', function () {
                        para.classList.toggle('truncated');
                        toggle.textContent = para.classList.contains('truncated') ? 'View More' : 'View Less';
                    });
                }
            });
        }

        applyToggleLogic();

        window.addEventListener('resize', () => {
            document.querySelectorAll('.view-toggle-btn').forEach(el => el.remove());
            document.querySelectorAll('.content-section p').forEach(p => p.classList.remove('truncated'));
            applyToggleLogic();
        });
    });