/**
 * EduGenie Dashboard & Analytics Engine
 * Manages Chart.js visualizations, live metrics, weak topic diagnosis,
 * and adaptive learning recommendations.
 */

let activityChartInstance = null;
let accuracyChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();
});

async function loadDashboardData() {
  try {
    const res = await apiRequest('/api/dashboard/metrics', 'GET');
    const data = res.data;

    // Populate Top KPI Cards
    setElemText('stat-study-time', `${Math.round(data.total_study_minutes / 60 * 10) / 10} hrs`);
    setElemText('stat-quiz-accuracy', `${data.quiz_accuracy}%`);
    setElemText('stat-questions-count', data.questions_asked);
    setElemText('stat-streak-count', `${data.streak} Days`);

    // Topbar Chips
    setElemText('topbar-xp', `${data.xp} XP`);
    setElemText('topbar-streak', `${data.streak} 🔥`);

    // Weak & Strong Areas
    renderTagList('dash-weak-areas', data.weak_areas, 'badge-rose');
    renderTagList('dash-strong-areas', data.strong_areas, 'badge-emerald');

    // Adaptive Learning Recommendations
    renderRecommendations(data.recommended_topics);

    // Badges Showcase
    renderBadges(data.recent_badges);

    // Render Charts
    initActivityChart(data.weekly_activity);
    initAccuracyChart(data.quiz_accuracy);
  } catch (err) {
    console.error('Failed to load dashboard metrics:', err);
  }
}

function setElemText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function renderTagList(containerId, items, badgeClass) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';

  if (!items || items.length === 0) {
    container.innerHTML = '<span class="text-muted">None recorded yet</span>';
    return;
  }

  items.forEach(item => {
    const span = document.createElement('span');
    span.className = `stat-chip ${badgeClass}`;
    span.textContent = item;
    container.appendChild(span);
  });
}

function renderRecommendations(topics) {
  const container = document.getElementById('dash-recommendations-list');
  if (!container) return;
  container.innerHTML = '';

  if (!topics || topics.length === 0) {
    container.innerHTML = '<p class="text-muted">No recommendations generated yet. Take a diagnostic quiz to trigger adaptive suggestions!</p>';
    return;
  }

  topics.forEach(t => {
    const card = document.createElement('div');
    card.className = 'card mb-2 p-3 bg-surface-elevated';
    card.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <span class="status-badge demo mb-1">AI Adaptive Target</span>
          <h4 style="font-size: 0.95rem; margin-top: 0.25rem;">${t}</h4>
        </div>
        <a href="/chat" class="btn btn-secondary btn-sm">Study Topic</a>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderBadges(badges) {
  const container = document.getElementById('dash-badges-container');
  if (!container) return;
  container.innerHTML = '';

  badges.forEach(b => {
    const div = document.createElement('div');
    div.className = 'badge-item';
    div.innerHTML = `
      <div class="badge-icon"><i data-lucide="${b.icon || 'award'}"></i></div>
      <div class="badge-info">
        <h4>${b.name}</h4>
        <p>${b.description}</p>
      </div>
    `;
    container.appendChild(div);
  });

  if (window.lucide) lucide.createIcons();
}

function initActivityChart(weeklyActivity) {
  const ctx = document.getElementById('weeklyActivityChart');
  if (!ctx || !window.Chart) return;

  const labels = weeklyActivity.map(w => w.day);
  const minutes = weeklyActivity.map(w => w.minutes);

  if (activityChartInstance) activityChartInstance.destroy();

  activityChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Study Minutes',
        data: minutes,
        backgroundColor: 'rgba(99, 102, 241, 0.75)',
        borderColor: '#6366f1',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function initAccuracyChart(accuracy) {
  const ctx = document.getElementById('quizAccuracyChart');
  if (!ctx || !window.Chart) return;

  if (accuracyChartInstance) accuracyChartInstance.destroy();

  accuracyChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Accurate', 'Review Needed'],
      datasets: [{
        data: [accuracy, Math.max(0, 100 - accuracy)],
        backgroundColor: ['#10b981', '#21262d'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '75%',
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}
