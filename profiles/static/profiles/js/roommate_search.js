// roommate search JavaScript

document.querySelectorAll('.favorite-btn').forEach(btn => {
    btn.addEventListener('click', async function(e) {
        e.preventDefault();
        const userId = this.dataset.userId;

        try {
            const response = await fetch(`/roommates/${userId}/favorite/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (response.ok) {
                if (data.favorited) {
                    this.textContent = '♥ Added to Favorites';
                    this.style.fontSize = '0.875rem';
                    this.classList.add('favorited');
                } else {
                    this.textContent = '❤️';
                    this.style.fontSize = '1rem';
                    this.classList.remove('favorited');
                }
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
});
