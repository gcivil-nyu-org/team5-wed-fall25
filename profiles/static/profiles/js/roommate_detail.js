// Roommate Detail JavaScript

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Favorite button functionality
    const favoriteBtn = document.querySelector('.favorite-btn');

    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', async function(e) {
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
                    this.textContent = data.favorited ? '❤️ Favorited' : '🤍 Add to Favorites';
                    if (data.favorited) {
                        this.classList.add('favorited');
                        this.classList.remove('not-favorited');
                    } else {
                        this.classList.add('not-favorited');
                        this.classList.remove('favorited');
                    }
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
});
