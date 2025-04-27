// static/js/sidebar.js
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const overlay = document.getElementById('sidebarOverlay');
    
    // Toggle sidebar function
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        document.body.classList.toggle('sidebar-open');
        
        // Show/hide overlay
        if (sidebar.classList.contains('active')) {
            overlay.style.display = 'block';
        } else {
            overlay.style.display = 'none';
        }
    }
    
    // Event listeners for toggle and close buttons
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    if (sidebarClose) {
        sidebarClose.addEventListener('click', toggleSidebar);
    }
    
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar when clicking on a link
    const sidebarLinks = sidebar.querySelectorAll('.nav-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (sidebar.classList.contains('active')) {
                toggleSidebar();
            }
        });
    });
    
    // Handle escape key to close sidebar
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) {
            toggleSidebar();
        }
    });
    
    // Fix for mobile browsers: prevent touchmove on body when sidebar is open
    document.body.addEventListener('touchmove', function(e) {
        if (document.body.classList.contains('sidebar-open')) {
            e.preventDefault();
        }
    }, { passive: false });
});