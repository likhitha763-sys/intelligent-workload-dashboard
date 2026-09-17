// Main JavaScript file for Academic Workload Dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Workload Dashboard JavaScript initialized.');

    // 1. Sidebar Toggle for Responsive Mobile/Tablet Layouts
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const wrapper = document.getElementById('wrapper');
    if (sidebarToggle && wrapper) {
        sidebarToggle.addEventListener('click', (e) => {
            e.preventDefault();
            wrapper.classList.toggle('toggled');
        });
    }

    // 2. Password Show/Hide Visibility Toggle
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            if (targetInput) {
                if (targetInput.type === 'password') {
                    targetInput.type = 'text';
                    btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
                } else {
                    targetInput.type = 'password';
                    btn.innerHTML = '<i class="bi bi-eye"></i>';
                }
            }
        });
    });

    // 3. Auto-dismiss Alert Messages
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // 4. Data-Confirm Handler for Destructive Actions
    document.querySelectorAll('form[data-confirm], a[data-confirm], button[data-confirm]').forEach(element => {
        element.addEventListener('submit', (e) => {
            const message = element.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // 5. Loading Indicator Spinner on Form Submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            if (form.hasAttribute('data-no-loader')) return;
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                setTimeout(() => {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...`;
                }, 0);
                // Fallback timeout to re-enable button if response is delayed
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 8000);
            }
        });
    });
});
