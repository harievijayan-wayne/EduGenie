/**
 * EduGenie Progress & Study Session Logger
 */

document.addEventListener('DOMContentLoaded', () => {
  const sessionForm = document.getElementById('log-session-form');
  loadProgressPage();

  if (sessionForm) {
    sessionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const topic = document.getElementById('session-topic').value.trim();
      const duration_minutes = parseInt(document.getElementById('session-duration').value) || 25;
      const session_type = document.getElementById('session-type').value || 'practice';

      try {
        const res = await apiRequest('/api/progress/session', 'POST', {
          topic,
          duration_minutes,
          session_type
        });

        showToast(res.message, 'success');
        document.getElementById('session-topic').value = '';
        loadProgressPage();
      } catch (err) {
        showToast('Could not log session.', 'error');
      }
    });
  }
});

async function loadProgressPage() {
  try {
    const res = await apiRequest('/api/progress', 'GET');
    const data = res.data;

    // Set stats
    const setT = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setT('prog-total-hours', `${Math.round(data.stats.total_study_minutes / 60 * 10) / 10} hrs`);
    setT('prog-quizzes-count', data.stats.quizzes_completed);
    setT('prog-flashcards-count', data.stats.flashcards_reviewed);
    setT('prog-questions-count', data.stats.questions_asked);
    setT('prog-xp-val', `${data.user.xp} XP`);
    setT('prog-streak-val', `${data.user.streak} Days`);

    // Render session logs
    const sessionList = document.getElementById('recent-sessions-list');
    if (sessionList && data.recent_sessions) {
      sessionList.innerHTML = '';
      if (data.recent_sessions.length === 0) {
        sessionList.innerHTML = '<p class="text-muted p-2">No recorded study sessions yet. Log one above!</p>';
      } else {
        data.recent_sessions.forEach(s => {
          const row = document.createElement('div');
          row.className = 'card mb-2 p-3 bg-surface-elevated d-flex justify-content-between align-items-center';
          row.innerHTML = `
            <div>
              <strong>${s.topic}</strong>
              <small class="text-muted d-block">${s.date} • ${s.type.toUpperCase()}</small>
            </div>
            <span class="status-badge">+${s.duration} mins</span>
          `;
          sessionList.appendChild(row);
        });
      }
    }

    // Render Badges
    const badgeRack = document.getElementById('all-badges-rack');
    if (badgeRack && data.badges) {
      badgeRack.innerHTML = '';
      data.badges.forEach(b => {
        const item = document.createElement('div');
        item.className = 'badge-item';
        item.innerHTML = `
          <div class="badge-icon"><i data-lucide="${b.icon || 'award'}"></i></div>
          <div class="badge-info">
            <h4>${b.name}</h4>
            <p>${b.description}</p>
          </div>
        `;
        badgeRack.appendChild(item);
      });
      if (window.lucide) lucide.createIcons();
    }
  } catch (err) {
    console.warn('Error loading progress:', err);
  }
}
