document.addEventListener('DOMContentLoaded', () => {
    const signUpButton = document.getElementById('signUp');
    const signInButton = document.getElementById('signIn');
    const container = document.getElementById('container');
    const registerForm = document.getElementById('registerForm');
    const loginForm = document.getElementById('loginForm');

    // Panel Toggling
    signUpButton.addEventListener('click', () => {
        container.classList.add("right-panel-active");
    });

    signInButton.addEventListener('click', () => {
        container.classList.remove("right-panel-active");
    });

    // Password Visibility Toggling
    const setupPasswordToggle = (toggleId, inputId) => {
        const toggle = document.getElementById(toggleId);
        const input = document.getElementById(inputId);
        toggle.addEventListener('click', () => {
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            toggle.classList.toggle('fa-eye');
            toggle.classList.toggle('fa-eye-slash');
        });
    };

    setupPasswordToggle('toggleRegPassword', 'regPassword');
    setupPasswordToggle('toggleRegConfirmPassword', 'regConfirmPassword');
    setupPasswordToggle('toggleLoginPassword', 'loginPassword');

    // Helper functions for validation
    const showError = (input, message) => {
        const inputGroup = input.parentElement;
        const errorMsg = inputGroup.querySelector('.error-msg');
        errorMsg.innerText = message;
        input.style.borderColor = 'var(--error)';
        input.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
    };

    const clearError = (input) => {
        const inputGroup = input.parentElement;
        const errorMsg = inputGroup.querySelector('.error-msg');
        errorMsg.innerText = '';
        input.style.borderColor = 'transparent';
        input.style.backgroundColor = '#2d3748';
    };

    const isValidEmail = (email) => {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    };

    // Registration Validation and API Call
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        let isValid = true;

        const fullName = document.getElementById('regFullName');
        const email = document.getElementById('regEmail');
        const password = document.getElementById('regPassword');
        const confirmPassword = document.getElementById('regConfirmPassword');

        // Validation logic
        if (!fullName.value.trim()) {
            showError(fullName, 'Full Name is required');
            isValid = false;
        } else clearError(fullName);

        if (!email.value.trim()) {
            showError(email, 'Email is required');
            isValid = false;
        } else if (!isValidEmail(email.value)) {
            showError(email, 'Invalid email format');
            isValid = false;
        } else clearError(email);

        if (password.value.length < 6) {
            showError(password, 'Min 6 characters required');
            isValid = false;
        } else clearError(password);

        if (confirmPassword.value !== password.value) {
            showError(confirmPassword, 'Passwords do not match');
            isValid = false;
        } else clearError(confirmPassword);

        if (isValid) {
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: fullName.value,
                        email: email.value,
                        password: password.value
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    alert(result.message);
                    container.classList.remove("right-panel-active");
                    registerForm.reset();
                } else {
                    showError(email, result.error || result.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred during registration. Please try again.');
            }
        }
    });

    // Login Validation and API Call
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        let isValid = true;

        const email = document.getElementById('loginEmail');
        const password = document.getElementById('loginPassword');

        if (!email.value.trim()) {
            showError(email, 'Email is required');
            isValid = false;
        } else if (!isValidEmail(email.value)) {
            showError(email, 'Invalid email format');
            isValid = false;
        } else clearError(email);

        if (!password.value.trim()) {
            showError(password, 'Password is required');
            isValid = false;
        } else clearError(password);

        if (isValid) {
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: email.value,
                        password: password.value
                    })
                });

                let result;
                try {
                    result = await response.json();
                } catch (e) {
                    showError(email, 'Server error occurred');
                    return;
                }

                if (response.ok) {
                    localStorage.setItem('userEmail', result.user.email);
                    localStorage.setItem('userName', result.user.username);
                    window.location.href = '/upload';
                } else {
                    showError(password, result.error || result.message);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred during login. Please try again.');
            }
        }
    });
});
