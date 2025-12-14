// Image Lightbox Functionality
class ImageLightbox {
  constructor() {
    this.images = [];
    this.currentIndex = 0;
    this.overlay = null;
    this.lightboxImage = null;
    this.counter = null;
    this.prevBtn = null;
    this.nextBtn = null;
    this.init();
  }

  init() {
    // Get all gallery images (supports both listing and marketplace images)
    const galleryImages = document.querySelectorAll('.gallery-image, .item-gallery-image');

    console.log('Image Lightbox: Found', galleryImages.length, 'images');

    if (galleryImages.length === 0) {
      console.log('Image Lightbox: No images found, skipping initialization');
      return; // No images to display
    }

    // Store image URLs
    this.images = Array.from(galleryImages).map(img => img.src);
    console.log('Image Lightbox: Image URLs:', this.images);

    // Create lightbox modal
    this.createLightbox();
    console.log('Image Lightbox: Modal created');

    // Add click handlers to gallery images
    galleryImages.forEach((img, index) => {
      img.addEventListener('click', () => {
        console.log('Image Lightbox: Image clicked, index:', index);
        this.openLightbox(index);
      });
      console.log('Image Lightbox: Added click handler to image', index);
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    console.log('Image Lightbox: Keyboard navigation enabled');
  }

  createLightbox() {
    // Create overlay
    this.overlay = document.createElement('div');
    this.overlay.className = 'lightbox-overlay';

    // Create container
    const container = document.createElement('div');
    container.className = 'lightbox-container';

    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'lightbox-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.setAttribute('aria-label', 'Close lightbox');
    closeBtn.addEventListener('click', () => this.closeLightbox());

    // Create image element
    this.lightboxImage = document.createElement('img');
    this.lightboxImage.className = 'lightbox-image';
    this.lightboxImage.alt = 'Enlarged view';

    // Create previous button
    this.prevBtn = document.createElement('button');
    this.prevBtn.className = 'lightbox-nav lightbox-prev';
    this.prevBtn.innerHTML = '&#10094;';
    this.prevBtn.setAttribute('aria-label', 'Previous image');
    this.prevBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.showPrevious();
    });

    // Create next button
    this.nextBtn = document.createElement('button');
    this.nextBtn.className = 'lightbox-nav lightbox-next';
    this.nextBtn.innerHTML = '&#10095;';
    this.nextBtn.setAttribute('aria-label', 'Next image');
    this.nextBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.showNext();
    });

    // Create counter
    this.counter = document.createElement('div');
    this.counter.className = 'lightbox-counter';

    // Assemble lightbox
    container.appendChild(this.lightboxImage);
    this.overlay.appendChild(closeBtn);
    this.overlay.appendChild(this.prevBtn);
    this.overlay.appendChild(this.nextBtn);
    this.overlay.appendChild(container);
    this.overlay.appendChild(this.counter);

    // Click overlay to close (but not the image itself)
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        this.closeLightbox();
      }
    });

    // Prevent container clicks from closing
    container.addEventListener('click', (e) => {
      e.stopPropagation();
    });

    // Add to document
    document.body.appendChild(this.overlay);
  }

  openLightbox(index) {
    this.currentIndex = index;
    this.updateImage();
    this.overlay.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
  }

  closeLightbox() {
    this.overlay.classList.remove('active');
    document.body.style.overflow = ''; // Restore scrolling
  }

  showNext() {
    if (this.currentIndex < this.images.length - 1) {
      this.currentIndex++;
      this.updateImage();
    }
  }

  showPrevious() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.updateImage();
    }
  }

  updateImage() {
    this.lightboxImage.src = this.images[this.currentIndex];
    this.counter.textContent = `${this.currentIndex + 1} / ${this.images.length}`;

    // Update button states
    this.prevBtn.disabled = this.currentIndex === 0;
    this.nextBtn.disabled = this.currentIndex === this.images.length - 1;

    // Hide navigation buttons if only one image
    if (this.images.length === 1) {
      this.prevBtn.style.display = 'none';
      this.nextBtn.style.display = 'none';
    } else {
      this.prevBtn.style.display = 'block';
      this.nextBtn.style.display = 'block';
    }
  }

  handleKeyboard(e) {
    if (!this.overlay.classList.contains('active')) {
      return;
    }

    switch(e.key) {
      case 'Escape':
        this.closeLightbox();
        break;
      case 'ArrowLeft':
        this.showPrevious();
        break;
      case 'ArrowRight':
        this.showNext();
        break;
    }
  }
}

// Initialize lightbox when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('Image Lightbox: Initializing...');
  const lightbox = new ImageLightbox();
  console.log('Image Lightbox: Initialized with', lightbox.images.length, 'images');
});
