// Roommate Search JavaScript

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Filter Toggle Functionality
    const filterToggle = document.getElementById('filterToggle');
    const filterSection = document.getElementById('filterSection');
    const filterForm = document.getElementById('filterForm');
    const filterCount = document.getElementById('filterCount');

    if (filterToggle && filterSection) {
        // Check if there are active filters on page load
        const hasActiveFilters = checkActiveFilters();
        if (hasActiveFilters) {
            filterSection.classList.add('active');
            filterToggle.classList.add('active');
        }

        // Toggle filter section
        filterToggle.addEventListener('click', function() {
            filterSection.classList.toggle('active');
            filterToggle.classList.toggle('active');

            // Update button text
            const filterText = filterToggle.querySelector('.filter-text');
            if (filterSection.classList.contains('active')) {
                filterText.textContent = 'Hide Filters';
            } else {
                filterText.textContent = 'Filters';
            }
        });
    }

    // Count and display active filters
    function checkActiveFilters() {
        if (!filterForm) return false;

        let count = 0;
        const checkboxes = filterForm.querySelectorAll('input[type="checkbox"]:checked');
        const textInputs = filterForm.querySelectorAll('input[type="text"], input[type="number"]');

        count += checkboxes.length;

        textInputs.forEach(input => {
            if (input.value && input.value.trim() !== '') {
                count++;
            }
        });

        if (filterCount) {
            if (count > 0) {
                filterCount.textContent = count;
                filterCount.style.display = 'inline-block';
            } else {
                filterCount.textContent = '';
                filterCount.style.display = 'none';
            }
        }

        return count > 0;
    }

    // Update filter count when form changes
    if (filterForm) {
        filterForm.addEventListener('change', checkActiveFilters);
        filterForm.addEventListener('input', checkActiveFilters);

        // Initial count check
        checkActiveFilters();
    }

    // Favorite button functionality
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
});
