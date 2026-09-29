/**
 * EduGenie MCQ Quiz Engine
 * Handles generation, timer countdown, user selection, submission,
 * scoring, weak area diagnosis, and quiz retries.
 */

let activeQuiz = null;
let currentQuestionIndex = 0;
let userAnswers = {};
let quizTimerInterval = null;
let secondsRemaining = 300; // 5 minutes default

document.addEventListener('DOMContentLoaded', () => {
  const generateForm = document.getElementById('quiz-generate-form');
  const quizActiveCard = document.getElementById('quiz-active-card');
  const quizSetupCard = document.getElementById('quiz-setup-card');
  const quizResultsCard = document.getElementById('quiz-results-card');

  if (generateForm) {
    generateForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const topic = document.getElementById('quiz-topic').value.trim();
      const numQuestions = parseInt(document.getElementById('quiz-num-questions').value) || 5;
      const difficulty = document.getElementById('quiz-difficulty').value || 'medium';

      if (!topic) return;

      const genBtn = document.getElementById('quiz-generate-btn');
      genBtn.disabled = true;
      genBtn.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> Generating Questions...';

      try {
        const res = await apiRequest('/api/quiz/generate', 'POST', {
          topic,
          num_questions: numQuestions,
          difficulty
        });

        activeQuiz = res.data;
        currentQuestionIndex = 0;
        userAnswers = {};
        secondsRemaining = activeQuiz.total_questions * 60; // 1 min per question

        quizSetupCard.style.display = 'none';
        quizResultsCard.style.display = 'none';
        quizActiveCard.style.display = 'block';

        startTimer();
        renderQuestion();
      } catch (err) {
        showToast('Failed to generate quiz. Please retry.', 'error');
      } finally {
        genBtn.disabled = false;
        genBtn.innerHTML = '<i data-lucide="zap"></i> Start Diagnostic Quiz';
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  // Timer Countdown
  function startTimer() {
    clearInterval(quizTimerInterval);
    const timerElem = document.getElementById('quiz-timer-display');

    quizTimerInterval = setInterval(() => {
      secondsRemaining--;
      const mins = Math.floor(secondsRemaining / 60);
      const secs = secondsRemaining % 60;
      if (timerElem) {
        timerElem.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      }

      if (secondsRemaining <= 0) {
        clearInterval(quizTimerInterval);
        showToast('Time is up! Auto-submitting answers...', 'info');
        submitQuiz();
      }
    }, 1000);
  }

  // Render Current Question
  function renderQuestion() {
    if (!activeQuiz || !activeQuiz.questions) return;

    const q = activeQuiz.questions[currentQuestionIndex];
    document.getElementById('current-q-num').textContent = currentQuestionIndex + 1;
    document.getElementById('total-q-num').textContent = activeQuiz.total_questions;
    document.getElementById('quiz-question-text').textContent = q.question;

    const optionsContainer = document.getElementById('quiz-options-container');
    optionsContainer.innerHTML = '';

    const selectedAnswer = userAnswers[currentQuestionIndex];

    q.options.forEach((opt) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `quiz-option-btn ${selectedAnswer === opt ? 'selected' : ''}`;
      btn.innerHTML = `
        <span class="option-indicator">${selectedAnswer === opt ? '●' : '○'}</span>
        <span class="option-text">${opt}</span>
      `;
      btn.onclick = () => selectOption(opt);
      optionsContainer.appendChild(btn);
    });

    // Update Next/Submit buttons
    const prevBtn = document.getElementById('quiz-prev-btn');
    const nextBtn = document.getElementById('quiz-next-btn');
    const submitBtn = document.getElementById('quiz-submit-btn');

    if (prevBtn) prevBtn.disabled = currentQuestionIndex === 0;

    const isLast = currentQuestionIndex === activeQuiz.total_questions - 1;
    if (nextBtn) nextBtn.style.display = isLast ? 'none' : 'inline-flex';
    if (submitBtn) submitBtn.style.display = isLast ? 'inline-flex' : 'none';
  }

  function selectOption(optionText) {
    userAnswers[currentQuestionIndex] = optionText;
    renderQuestion();
  }

  // Navigation handlers
  window.nextQuestion = () => {
    if (currentQuestionIndex < activeQuiz.total_questions - 1) {
      currentQuestionIndex++;
      renderQuestion();
    }
  };

  window.prevQuestion = () => {
    if (currentQuestionIndex > 0) {
      currentQuestionIndex--;
      renderQuestion();
    }
  };

  // Submit and Evaluate
  window.submitQuiz = async () => {
    clearInterval(quizTimerInterval);
    const submitBtn = document.getElementById('quiz-submit-btn');
    if (submitBtn) submitBtn.disabled = true;

    try {
      const res = await apiRequest('/api/quiz/submit', 'POST', {
        quiz_id: activeQuiz.quiz_id,
        user_answers: userAnswers
      });

      renderResults(res.data);
    } catch (err) {
      showToast('Could not evaluate quiz.', 'error');
    }
  };

  function renderResults(evalData) {
    quizActiveCard.style.display = 'none';
    quizResultsCard.style.display = 'block';

    document.getElementById('result-score').textContent = `${evalData.score} / ${evalData.total_questions}`;
    document.getElementById('result-percentage').textContent = `${evalData.percentage}%`;
    document.getElementById('result-xp').textContent = `+${evalData.xp_earned} XP`;

    // Render Weak Areas
    const weakList = document.getElementById('result-weak-topics');
    if (weakList) {
      weakList.innerHTML = '';
      if (evalData.weak_topics && evalData.weak_topics.length > 0) {
        evalData.weak_topics.forEach(t => {
          const li = document.createElement('li');
          li.className = 'weak-topic-pill';
          li.textContent = t;
          weakList.appendChild(li);
        });
      } else {
        weakList.innerHTML = '<span class="text-emerald">Outstanding! No weak areas detected in this quiz.</span>';
      }
    }

    // Render Detailed Answer Reviews
    const reviewContainer = document.getElementById('result-reviews-container');
    if (reviewContainer && evalData.reviews) {
      reviewContainer.innerHTML = '';
      evalData.reviews.forEach((r, idx) => {
        const item = document.createElement('div');
        item.className = `review-item card mb-3 ${r.is_correct ? 'border-emerald' : 'border-rose'}`;
        item.innerHTML = `
          <div class="card-header">
            <strong>Q${idx + 1}: ${r.question}</strong>
            <span class="status-badge ${r.is_correct ? '' : 'demo'}">${r.is_correct ? 'Correct' : 'Needs Review'}</span>
          </div>
          <p class="mb-1"><span class="text-muted">Your Answer:</span> <strong>${r.user_answer}</strong></p>
          <p class="mb-2"><span class="text-muted">Correct Answer:</span> <strong class="text-emerald">${r.correct_answer}</strong></p>
          <div class="explanation-box">
            <small><strong>Explanation:</strong> ${r.explanation}</small>
          </div>
        `;
        reviewContainer.appendChild(item);
      });
    }

    if (window.lucide) lucide.createIcons();
  }

  // Retry or new quiz
  window.resetQuiz = () => {
    quizResultsCard.style.display = 'none';
    quizActiveCard.style.display = 'none';
    quizSetupCard.style.display = 'block';
  };
});
