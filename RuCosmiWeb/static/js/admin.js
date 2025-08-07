document.addEventListener('DOMContentLoaded', function() {
    // Toast notifications
    function showToast(message, type = 'success') {
        const toastContainer = document.querySelector('.toast-container') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                ${type === 'success' ? '✓' : type === 'error' ? '✕' : '⚠'}
            </div>
            <div class="toast-message">${message}</div>
            <div class="toast-close">&times;</div>
        `;

        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });

        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }

    // Convert flash messages to toasts
    document.querySelectorAll('.alert').forEach(alert => {
        const type = alert.classList.contains('alert-success') ? 'success' :
                    alert.classList.contains('alert-error') ? 'error' : 'warning';
        showToast(alert.textContent.trim(), type);
        alert.remove();
    });

    // Confirm before delete
    document.querySelectorAll('.btn-danger').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Вы уверены, что хотите удалить эту услугу?')) {
                e.preventDefault();
            }
        });
    });

    // Add hover effects to cards
    document.querySelectorAll('.service-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px)';
            card.style.boxShadow = '0 15px 30px rgba(108, 92, 231, 0.15)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            card.style.boxShadow = 'var(--shadow)';
        });
    });
});

// Add toast container if not exists
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}