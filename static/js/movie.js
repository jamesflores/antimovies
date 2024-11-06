 let isAntiMode = false;
    
 document.addEventListener('DOMContentLoaded', function() {
     const findButton = document.querySelector('#find-recommendations');
     if (findButton) {
         findButton.disabled = true;
         findButton.addEventListener('click', function() {
             // Scroll to the top of the page
             window.scrollTo({ top: 0, behavior: 'smooth' });

             // Change button text and disable it
             this.disabled = true;
             this.textContent = "Analyzing your preferences...";
         });
     }

     // Set initial viewport size
     updateViewportSize();

     // Update viewport size on resize with debounce
     let resizeTimeout;
     window.addEventListener('resize', function() {
         clearTimeout(resizeTimeout);
         resizeTimeout = setTimeout(updateViewportSize, 250);
     });

     // Initialize intersection observer for infinite scroll
     const options = {
         root: null,
         rootMargin: '100px',
         threshold: 0.1
     };

     const observer = new IntersectionObserver((entries) => {
         entries.forEach(entry => {
             if (entry.isIntersecting) {
                 const loadMoreBtn = document.getElementById('load-more-trigger');
                 if (loadMoreBtn && !loadMoreBtn.disabled) {
                     loadMoreBtn.click();
                 }
             }
         });
     }, options);

     // Observe the sentinel element
     const sentinel = document.getElementById('scroll-sentinel');
     if (sentinel) {
         observer.observe(sentinel);
     }

     // Footer actions
     const footerActions = document.querySelector('.footer-actions');
     let lastScrollTop = 0;

     // Add scroll effect to footer
     window.addEventListener('scroll', () => {
         const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

         if (footerActions) {
             if (scrollTop > lastScrollTop) {
                 footerActions.classList.add('scrolled');
             } else {
                 footerActions.classList.remove('scrolled');
             }
         }

         lastScrollTop = scrollTop;
     });

     // HTMX event listeners for loading overlay and button updates
     document.addEventListener('htmx:beforeRequest', function(evt) {
         const target = evt.detail.target;

         // Add loading overlay if the target is the poster container
         if (target && target.id === 'poster-container') {
             // Create a full-screen loading overlay to keep it in view
             const loadingOverlay = document.createElement('div');
             loadingOverlay.className = 'loading-overlay fixed-top w-100 h-100 d-flex justify-content-center align-items-center';
             loadingOverlay.style.zIndex = "1050";  // Ensure it's above other elements
             loadingOverlay.innerHTML = `
                 <div class="spinner-border text-primary" role="status">
                     <span class="visually-hidden">Loading...</span>
                 </div>
             `;

             // Append overlay to the body
             document.body.appendChild(loadingOverlay);
         }
     });

     // HTMX event listener for after request
     document.addEventListener('htmx:afterRequest', function(evt) {
         const target = evt.detail.target;
     
         if (target && target.id === 'poster-container') {
             // Remove loading overlay
             const loadingOverlay = document.querySelector('.loading-overlay');
             if (loadingOverlay) {
                 loadingOverlay.remove();
             }
     
             // Handle different request types
             if (evt.detail.requestConfig.path === '/refresh-posters') {
                 // For new session/refresh
                 const findButton = document.querySelector('#find-recommendations');
                 if (findButton) {
                     findButton.disabled = true;
                     findButton.textContent = "Find My Anti-Movies!";  // Reset text
                 }
                 updateSelectionCount();
             } 
             else if (evt.detail.requestConfig.path === '/get-recommendations') {
                 isAntiMode = true;
                 
                 // Show restart button and update the lead text
                 document.querySelector('#restart-app').classList.remove('d-none');
                 document.querySelector('#selection-status').classList.add('d-none');
                 const findButton = document.querySelector('#find-recommendations');
                 if (findButton) {
                     findButton.textContent = "Find My Anti-Movies!";  // Reset text before hiding
                     findButton.classList.add('d-none');
                 }
                 document.querySelector('.lead').textContent = "Scrolling through movies you'd hate...";
     
                 // Apply anti-match theme
                 document.querySelector('.content-wrapper').classList.add('anti-match-theme');
                 document.querySelector('.footer-actions').classList.add('anti-match');
             }
             else {
                 // For other requests (like load more), just reset the button text
                 const findButton = document.querySelector('#find-recommendations');
                 if (findButton) {
                     findButton.textContent = "Find My Anti-Movies!";
                 }
             }
         }
     });

     // Modify the load-more endpoint based on mode
     document.querySelector('#load-more-trigger').addEventListener('htmx:configRequest', function(evt) {
         if (isAntiMode) {
             evt.detail.path = '/load-more-anti-recommendations';
         }
     });
 });  // End of DOMContentLoaded

// Viewport size detection for HTMX headers
function updateViewportSize() {
    document.body.setAttribute('hx-headers', JSON.stringify({
        'Viewport-Height': window.innerHeight,
        'Viewport-Width': window.innerWidth
    }));
}

 // Update selection count in the footer
 function updateSelectionCount() {
     const selectedCount = document.querySelectorAll('.poster-card.selected').length;
     const badges = document.querySelectorAll('#selection-status .badge');
     badges.forEach(badge => {
         badge.textContent = `${selectedCount} movies selected`;
     });
     // Update find recommendations button state
     updateFindButton();
 }

 // Enable/Disable the 'Find My Anti-Movies' button based on selection
 function updateFindButton() {
     const selectedCount = document.querySelectorAll('.poster-card.selected').length;
     const findButton = document.querySelector('#find-recommendations');
     if (findButton) {
         findButton.disabled = selectedCount === 0;
     }
 }

 // Toggle selection on poster card click
 function toggleSelection(card) {
     card.classList.toggle('selected');
     const input = card.querySelector('input');
     input.disabled = !input.disabled;

     const overlay = card.querySelector('.selection-overlay');
     if (overlay) {
         overlay.classList.toggle('d-none');
     }

     updateSelectionCount();
 }

 // Restart app and reset selections
 function restartApp() {
     // Immediately scroll to top
     window.scrollTo({ top: 0, behavior: 'smooth' });
 
     // Reset all state
     isAntiMode = false;
     sessionStorage.clear();
 
     // Immediately disable the button
     const findButton = document.querySelector('#find-recommendations');
     if (findButton) {
         findButton.disabled = true;
     }
 
     fetch('/reset-session', {
         method: 'POST',
         headers: {
             'Content-Type': 'application/json'
         }
     })
     .then(response => response.json())
     .then(() => {
         // Reset UI elements
         document.querySelector('#restart-app').classList.add('d-none');
         document.querySelector('#selection-status').classList.remove('d-none');
         document.querySelector('#find-recommendations').classList.remove('d-none');
         document.querySelector('.lead').textContent = "Select movies you love to find ones you'd hate!";
 
         // Remove dark theme
         document.querySelector('.content-wrapper').classList.remove('anti-match-theme');
         document.querySelector('.footer-actions').classList.remove('anti-match');
 
         // Clear selections
         document.querySelectorAll('.poster-card.selected').forEach(card => {
             card.classList.remove('selected');
         });
 
         // Force button to disabled state
         const findButton = document.querySelector('#find-recommendations');
         if (findButton) {
             findButton.disabled = true;
         }
 
         // Reset selection count
         updateSelectionCount();
 
         // Reload initial movies
         htmx.ajax('GET', '/refresh-posters', {
             target: '#poster-container',
             swap: 'innerHTML',
             complete: function() {
                 // Only update the button state after content loads
                 const findButton = document.querySelector('#find-recommendations');
                 if (findButton) {
                     findButton.disabled = true;
                 }
                 updateSelectionCount();
             }
         });
     })
     .catch(error => {
         console.error('Error resetting session:', error);
     });
 }