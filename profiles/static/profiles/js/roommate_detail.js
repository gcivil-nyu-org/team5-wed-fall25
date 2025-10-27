// Roommate Detail JavaScript

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Favorite button functionality - updated selector for new template
    const favoriteBtn = document.querySelector('.favorite-btn-detail');

    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            const userId = this.dataset.userId;

            try {
                const response = await fetch(`/roommates/${userId}/favorite/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json',
                    },
                });

                const data = await response.json();

                if (response.ok) {
                    this.textContent = data.favorited ? '❤️ Favorited' : '🤍 Add to Favorites';
                    if (data.favorited) {
                        this.classList.add('favorited');
                    } else {
                        this.classList.remove('favorited');
                    }
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
});

// Helper function to get CSRF token
function getCsrfToken() {
    // Try to get from cookie first
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

    if (cookieValue) return cookieValue;

    // Fallback to hidden input
    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenInput ? tokenInput.value : '';
}
