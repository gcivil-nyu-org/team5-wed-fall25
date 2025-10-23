// Mobile menu toggle
function toggleMobileMenu() {
	const navLinks = document.getElementById('navLinks');
	navLinks.classList.toggle('active');
}

// Dropdown menu handler
let dropdownTimeout;
const navDropdown = document.querySelector('.nav-dropdown');
const dropdownMenu = document.querySelector('.dropdown-menu');

if (navDropdown && dropdownMenu) {
	navDropdown.addEventListener('mouseenter', function() {
		clearTimeout(dropdownTimeout);
		dropdownMenu.style.display = 'block';
		dropdownMenu.style.opacity = '1';
		dropdownMenu.style.pointerEvents = 'auto';
	});

	navDropdown.addEventListener('mouseleave', function() {
		dropdownTimeout = setTimeout(function() {
			dropdownMenu.style.opacity = '0';
			dropdownMenu.style.pointerEvents = 'none';
			setTimeout(function() {
				dropdownMenu.style.display = 'none';
			}, 200);
		}, 150);
	});
}
