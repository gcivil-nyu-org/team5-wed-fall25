// my favorites JavaScript

document.querySelectorAll('.remove-favorite-btn').forEach(btn => {
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

            if (response.ok) {
                // Reload page to update favorites list
                location.reload();
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
});
