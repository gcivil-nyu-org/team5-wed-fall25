// Search Listings JavaScript

document.addEventListener('DOMContentLoaded', function() {
  const filterForm = document.getElementById('filterForm');
  const keywordInput = document.getElementById('keyword');
  const rentMinInput = document.getElementById('rent_min');
  const rentMaxInput = document.getElementById('rent_max');

  // Validate price inputs
  if (rentMinInput && rentMaxInput) {
    rentMinInput.addEventListener('change', validatePriceRange);
    rentMaxInput.addEventListener('change', validatePriceRange);
  }

  // Focus on keyword input for better UX
  if (keywordInput) {
    keywordInput.focus();
  }
});

function validatePriceRange() {
  const rentMin = parseFloat(document.getElementById('rent_min').value);
  const rentMax = parseFloat(document.getElementById('rent_max').value);

  if (!isNaN(rentMin) && !isNaN(rentMax) && rentMin > rentMax) {
    alert('Minimum rent cannot be greater than maximum rent.');
    document.getElementById('rent_max').value = '';
  }
}
