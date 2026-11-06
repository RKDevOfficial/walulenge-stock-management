document.addEventListener('DOMContentLoaded', function () {

    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menuToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    function openSidebar() {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('open');
            sidebarOverlay.classList.add('show');
        } else {
            document.body.classList.toggle('sidebar-collapsed');
        }
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        sidebarOverlay.classList.remove('show');
    }

    menuToggle.addEventListener('click', openSidebar);

    sidebarClose.addEventListener('click', closeSidebar);

    sidebarOverlay.addEventListener('click', closeSidebar);

    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });

    function updateClock() {
        const now = new Date();

        const time = now.toLocaleTimeString('en-GB', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });

        const date = now.toLocaleDateString('en-GB', {
            weekday: 'short',
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });

        document.getElementById('liveTime').textContent = time;
        document.getElementById('liveDate').textContent = date;
    }

    updateClock();
    setInterval(updateClock, 1000);

});

