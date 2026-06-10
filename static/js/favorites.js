document.addEventListener('DOMContentLoaded', () => {
    const favoriteBtn = document.getElementById('favorite-btn');
    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', async () => {
            const slug = favoriteBtn.getAttribute('data-slug');
            const csrfTokenElement = document.querySelector('#csrf-wrapper input[name="csrfmiddlewaretoken"]');
            
            if (!csrfTokenElement) {
                console.error("CSRF token missing");
                return;
            }
            const csrfToken = csrfTokenElement.value;

            try {
                const response = await fetch(`/artigo/${slug}/favoritar/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const starIcon = document.getElementById('star-icon');
                    if (data.favorited) {
                        starIcon.setAttribute('fill', 'currentColor');
                    } else {
                        starIcon.setAttribute('fill', 'none');
                    }
                } else {
                    console.error("Erro ao alternar o favorito.");
                }
            } catch (err) {
                console.error("Erro na comunicação: ", err);
            }
        });
    }
});
