 I need you to refactor inline CSS and JavaScript in Django templates following Django best practices for static files organization.

  ## Context
  This is a Django project called CampusNest (see CLAUDE.md for full project details). I've been refactoring templates to move inline
  styles and scripts into separate static files.

  ## What's Already Been Done
  The following pages have been refactored:
  1. `templates/home.html` - CSS moved to `static/css/home.css`
  2. `accounts/templates/accounts/register.html` - CSS moved to `accounts/static/accounts/css/register.css`
  3. `listings/templates/listings/my_listings.html` - CSS moved to `listings/static/listings/css/my_listings.css`
  4. `profiles/templates/profiles/my_favorites.html` - CSS moved to `profiles/static/profiles/css/my_favorites.css` and JS to
  `profiles/static/profiles/js/my_favorites.js`

  ## Django Best Practices Being Followed
  1. **App-specific static files**: Each app's static files go in `<app>/static/<app>/css/` and `<app>/static/<app>/js/`
     - Example: `accounts/static/accounts/css/register.css`
     - Referenced in templates as: `{% static 'accounts/css/register.css' %}`

  2. **Project-wide static files**: Global files (like base.css, base.js) stay in `static/css/` and `static/js/`

  3. **Template structure**:
     - Add `{% load static %}` at the top
     - Use `{% block extra_css %}` for page-specific CSS
     - Use `{% block extra_js %}` for page-specific JavaScript
     - Remove ALL inline `style="..."` attributes
     - Remove `<style>` blocks
     - Remove inline `<script>` blocks
     - Replace with semantic CSS classes

  4. **CSRF tokens**: If JavaScript makes POST requests, ensure `{% csrf_token %}` is in the template

  ## Your Task
  Continue refactoring remaining templates that have inline styles or scripts. For each page:

  1. Create a todo list to track progress
  2. Check if the app's static directory structure exists (`<app>/static/<app>/css/` and `<app>/static/<app>/js/`)
  3. Create CSS file with extracted styles in the appropriate app directory
  4. Create JS file if there are inline scripts
  5. Update the HTML template to:
     - Add `{% load static %}`
     - Add CSS/JS references in appropriate blocks
     - Replace inline styles with semantic CSS classes
     - Remove `<style>` and `<script>` blocks
  6. Ensure proper namespacing (use app-specific class names to avoid conflicts)

  ## Example Refactoring Pattern

  **Before:**
  ```html
  {% extends 'base.html' %}
  <div style="max-width: 1200px; margin: 0 auto;">
      <h1 style="color: var(--text-primary);">Title</h1>
  </div>
  <style>
      .some-class:hover { transform: scale(1.1); }
  </style>

  After:
  {% extends 'base.html' %}
  {% load static %}

  {% block extra_css %}
  <link rel="stylesheet" href="{% static 'app/css/page_name.css' %}">
  {% endblock %}

  <div class="page-container">
      <h1 class="page-title">Title</h1>
  </div>

  And create app/static/app/css/page_name.css with all the styles.

  Important Notes

  - Maintain existing functionality - don't change behavior, just reorganize code
  - Use semantic, descriptive class names
  - Keep CSS organized with comments for different sections
  - Preserve all existing CSS variables (like var(--color-primary))
  - Test that static files are in the correct location

  Please start by finding templates with inline styles/scripts and refactor them one by one using this approach.
