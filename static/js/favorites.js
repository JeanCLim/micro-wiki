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
                        // Adiciona item específico à barra lateral.
                        const container = document.getElementById('sidebar-favorites-container');
                        const list = document.getElementById('sidebar-favorites-list');
                        if (container && list) {
                            container.style.display = 'block';
                            // Valida a existência prévia do item no DOM.
                            if (!list.querySelector(`li[data-slug="${data.slug}"]`)) {
                                const li = document.createElement('li');
                                li.setAttribute('data-slug', data.slug);
                                li.innerHTML = `<a href="${data.url}"><span class="icon"><svg class="sidebar-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg></span> ${data.title}</a>`;
                                list.appendChild(li);
                            }
                        }
                    } else {
                        starIcon.setAttribute('fill', 'none');
                        // Remove o item selecionado da barra lateral.
                        const container = document.getElementById('sidebar-favorites-container');
                        const list = document.getElementById('sidebar-favorites-list');
                        if (container && list) {
                            const li = list.querySelector(`li[data-slug="${data.slug}"]`);
                            if (li) {
                                li.remove();
                            }
                            if (list.children.length === 0) {
                                container.style.display = 'none';
                            }
                        }
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
