// Browse Marketplace JavaScript

document.addEventListener('DOMContentLoaded', function() {
  const filterForm = document.getElementById('filterForm');
  const keywordInput = document.getElementById('keyword');
  const categorySelect = document.getElementById('category');
  const priceMinInput = document.getElementById('price_min');
  const priceMaxInput = document.getElementById('price_max');

  // Auto-submit form when category changes
  if (categorySelect) {
    categorySelect.addEventListener('change', function() {
      filterForm.submit();
    });
  }

  // Validate price inputs
  if (priceMinInput && priceMaxInput) {
    priceMinInput.addEventListener('change', validatePriceRange);
    priceMaxInput.addEventListener('change', validatePriceRange);
  }

  // Focus on keyword input for better UX
  if (keywordInput) {
    keywordInput.focus();
  }
});

function validatePriceRange() {
  const priceMin = parseFloat(document.getElementById('price_min').value);
  const priceMax = parseFloat(document.getElementById('price_max').value);

  if (!isNaN(priceMin) && !isNaN(priceMax) && priceMin > priceMax) {
    alert('Minimum price cannot be greater than maximum price.');
    document.getElementById('price_max').value = '';
  }
}
