/**
 * Authentication Management (Login, Register, Logout)
 */

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const logoutBtn = document.getElementById('logout-btn');

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('login-email').value.trim();
      const password = document.getElementById('login-password').value;

      try {
        const res = await apiRequest('/api/auth/login', 'POST', { email, password });
        if (res.success) {
          showToast('Login successful! Redirecting to dashboard...', 'success');
          localStorage.setItem('edugenie-user', JSON.stringify(res.data.user));
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 800);
        }
      } catch (err) {
        // Handled in apiRequest
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('register-name').value.trim();
      const email = document.getElementById('register-email').value.trim();
      const password = document.getElementById('register-password').value;

      try {
        const res = await apiRequest('/api/auth/register', 'POST', { name, email, password });
        if (res.success) {
          showToast('Welcome to EduGenie! Setting up your workspace...', 'success');
          localStorage.setItem('edugenie-user', JSON.stringify(res.data.user));
          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 800);
        }
      } catch (err) {
        // Handled
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      try {
        await apiRequest('/api/auth/logout', 'POST');
        localStorage.removeItem('edugenie-user');
        showToast('Logged out successfully.', 'info');
        setTimeout(() => {
          window.location.href = '/login';
        }, 500);
      } catch (err) {
        window.location.href = '/login';
      }
    });
  }
});
