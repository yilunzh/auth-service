/**
 * Auth Service — Client-side form validation, password strength, and UX enhancements.
 */

document.addEventListener('DOMContentLoaded', () => {
    // =========================================
    // Password show/hide toggle
    // =========================================
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('input');
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            btn.textContent = isPassword ? 'Hide' : 'Show';
        });
    });

    // =========================================
    // Password strength checker
    // =========================================
    const passwordInput = document.querySelector('input[name="password"]');
    const strengthBar = document.getElementById('strength-bar');
    const strengthLabel = document.getElementById('strength-label');

    if (passwordInput && strengthBar) {
        passwordInput.addEventListener('input', () => {
            const val = passwordInput.value;
            let score = 0;

            if (val.length >= 8) score++;
            if (val.length >= 12) score++;
            if (/[a-z]/.test(val) && /[A-Z]/.test(val)) score++;
            if (/\d/.test(val)) score++;
            if (/[^a-zA-Z0-9]/.test(val)) score++;

            strengthBar.className = 'strength-bar';

            if (val.length === 0) {
                strengthBar.className = 'strength-bar';
                if (strengthLabel) strengthLabel.textContent = '';
            } else if (score <= 2) {
                strengthBar.classList.add('weak');
                if (strengthLabel) strengthLabel.textContent = 'Weak';
            } else if (score <= 3) {
                strengthBar.classList.add('fair');
                if (strengthLabel) strengthLabel.textContent = 'Fair';
            } else {
                strengthBar.classList.add('strong');
                if (strengthLabel) strengthLabel.textContent = 'Strong';
            }
        });
    }

    // =========================================
    // Form validation
    // =========================================
    const form = document.getElementById('auth-form');

    if (form) {
        // Blur validation on required fields
        form.querySelectorAll('input[required]').forEach(input => {
            input.addEventListener('blur', () => {
                validateField(input);
            });

            // Clear error on input
            input.addEventListener('input', () => {
                clearFieldError(input);
            });
        });

        // Confirm password match validation
        const confirmPw = form.querySelector('input[name="confirm_password"]');
        if (confirmPw) {
            confirmPw.addEventListener('blur', () => {
                const pw = form.querySelector('input[name="password"]');
                if (pw && confirmPw.value && pw.value !== confirmPw.value) {
                    showFieldError(confirmPw, 'Passwords do not match');
                } else {
                    clearFieldError(confirmPw);
                }
            });
        }

        // Submit handler: loading state + prevent double submit
        form.addEventListener('submit', (e) => {
            // Run all validations
            let hasError = false;
            form.querySelectorAll('input[required]').forEach(input => {
                if (!validateField(input)) {
                    hasError = true;
                }
            });

            // Check confirm password match
            if (confirmPw) {
                const pw = form.querySelector('input[name="password"]');
                if (pw && pw.value !== confirmPw.value) {
                    e.preventDefault();
                    showFieldError(confirmPw, 'Passwords do not match');
                    return;
                }
            }

            if (hasError) {
                e.preventDefault();
                return;
            }

            // Show loading state
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.classList.add('loading');
                btn.disabled = true;
            }
            form.querySelectorAll('input').forEach(i => {
                i.readOnly = true;
            });
        });
    }
});

/**
 * Validate a single form field.
 * Returns true if valid, false if invalid.
 */
function validateField(input) {
    const value = input.value.trim();
    const name = input.name;

    // Required check
    if (input.hasAttribute('required') && value === '') {
        const label = input.closest('.form-group')?.querySelector('label');
        const fieldName = label ? label.textContent : name;
        showFieldError(input, fieldName + ' is required');
        return false;
    }

    // Email format check
    if (input.type === 'email' && value !== '') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showFieldError(input, 'Please enter a valid email address');
            return false;
        }
    }

    // Minimum length check
    const minLength = input.getAttribute('minlength');
    if (minLength && value.length > 0 && value.length < parseInt(minLength, 10)) {
        showFieldError(input, 'Must be at least ' + minLength + ' characters');
        return false;
    }

    clearFieldError(input);
    return true;
}

/**
 * Show an error message below a field.
 */
function showFieldError(input, message) {
    input.classList.add('input-error');

    // Find or create the error span
    const group = input.closest('.form-group');
    if (!group) return;

    let errorSpan = group.querySelector('.field-error');
    if (!errorSpan) {
        errorSpan = document.createElement('span');
        errorSpan.className = 'field-error';
        group.appendChild(errorSpan);
    }

    errorSpan.textContent = message;
}

/**
 * Remove the error message from a field.
 */
function clearFieldError(input) {
    input.classList.remove('input-error');

    const group = input.closest('.form-group');
    if (!group) return;

    const errorSpan = group.querySelector('.field-error');
    if (errorSpan) {
        errorSpan.textContent = '';
    }
}
