/**
 * EduGenie Document & RAG Manager
 * Handles file dropzone, text extraction, RAG grounded Q&A,
 * and one-click conversion to Quiz, Notes, and Flashcards.
 */

let selectedDocumentId = null;

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('doc-dropzone');
  const fileInput = document.getElementById('doc-file-input');
  const docList = document.getElementById('uploaded-docs-list');
  const ragForm = document.getElementById('rag-ask-form');
  const ragInput = document.getElementById('rag-question-input');

  loadDocuments();

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        handleUpload(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        handleUpload(e.target.files[0]);
      }
    });
  }

  async function handleUpload(file) {
    const uploadStatus = document.getElementById('upload-status-text');
    if (uploadStatus) {
      uploadStatus.textContent = `Processing and chunking "${file.name}"...`;
      uploadStatus.style.display = 'block';
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await apiRequest('/api/documents/upload', 'POST', formData, true);
      showToast(`Document "${file.name}" indexed for RAG search!`, 'success');
      loadDocuments();
      if (res.data && res.data.document_id) {
        selectDocument(res.data.document_id, file.name);
      }
    } catch (err) {
      showToast('Document upload failed. Ensure valid PDF, DOCX, or TXT file.', 'error');
    } finally {
      if (uploadStatus) uploadStatus.style.display = 'none';
      if (fileInput) fileInput.value = '';
    }
  }

  async function loadDocuments() {
    if (!docList) return;
    try {
      const res = await apiRequest('/api/documents', 'GET');
      renderDocumentList(res.data);
    } catch (err) {
      console.warn('Could not load documents:', err);
    }
  }

  function renderDocumentList(docs) {
    if (!docList) return;
    docList.innerHTML = '';

    if (!docs || docs.length === 0) {
      docList.innerHTML = '<p class="text-muted p-3">No documents uploaded yet. Upload a PDF or TXT to test RAG.</p>';
      return;
    }

    docs.forEach(d => {
      const item = document.createElement('div');
      item.className = `card mb-2 ${selectedDocumentId === d.id ? 'border-primary' : ''}`;
      item.style.cursor = 'pointer';
      item.innerHTML = `
        <div class="card-header" style="margin-bottom: 0.5rem;">
          <strong class="d-flex align-items-center gap-2">
            <i data-lucide="file-text" class="text-primary"></i> ${d.filename}
          </strong>
          <span class="status-badge">${d.file_type} (${d.chunk_count} chunks)</span>
        </div>
        <div class="d-flex justify-content-between align-items-center">
          <small class="text-muted">Indexed for semantic search</small>
          <div class="d-flex gap-2">
            <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); triggerDocAction(${d.id}, 'summarize')">Summary</button>
            <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); triggerDocAction(${d.id}, 'quiz')">Quiz</button>
            <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); triggerDocAction(${d.id}, 'notes')">Notes</button>
          </div>
        </div>
      `;
      item.onclick = () => selectDocument(d.id, d.filename);
      docList.appendChild(item);
    });

    if (window.lucide) lucide.createIcons();
  }

  window.selectDocument = (id, filename) => {
    selectedDocumentId = id;
    const selectedBadge = document.getElementById('selected-doc-badge');
    if (selectedBadge) {
      selectedBadge.innerHTML = `<i data-lucide="check"></i> Active Document: <strong>${filename}</strong>`;
      if (window.lucide) lucide.createIcons();
    }
    const qSection = document.getElementById('rag-qa-section');
    if (qSection) qSection.style.display = 'block';
  };

  // Grounded RAG Query Submission
  if (ragForm) {
    ragForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!selectedDocumentId) {
        showToast('Please select an uploaded document first.', 'info');
        return;
      }
      const question = ragInput.value.trim();
      if (!question) return;

      const resultsBox = document.getElementById('rag-results-display');
      resultsBox.innerHTML = '<div class="typing-indicator"><span class="text-muted">Searching vector chunks and querying Gemini...</span><div class="typing-dot"></div><div class="typing-dot"></div></div>';

      try {
        const res = await apiRequest('/api/documents/qa', 'POST', {
          document_id: selectedDocumentId,
          question
        });

        const ans = res.data;
        let sourcesHtml = '';
        if (ans.referenced_chunks && ans.referenced_chunks.length > 0) {
          sourcesHtml = `
            <div class="rag-sources mt-3">
              <strong>Retrieved Document Passages:</strong>
              ${ans.referenced_chunks.map((c, i) => `
                <div class="card mt-2 p-2 bg-surface-elevated">
                  <small class="text-muted">Source Chunk #${i+1}:</small>
                  <p class="font-mono" style="font-size: 0.82rem; margin-top: 0.25rem;">${c}</p>
                </div>
              `).join('')}
            </div>
          `;
        }

        resultsBox.innerHTML = `
          <div class="card p-3">
            <h4 class="mb-2 text-primary">EduGenie Grounded Answer</h4>
            <p>${ans.answer}</p>
            ${sourcesHtml}
          </div>
        `;
      } catch (err) {
        resultsBox.innerHTML = '<p class="text-rose">Could not retrieve answer from document.</p>';
      }
    });
  }

  // Trigger Doc Transformation Actions
  window.triggerDocAction = async (docId, action) => {
    showToast(`Generating ${action} from document...`, 'info');
    try {
      const res = await apiRequest(`/api/documents/${docId}/action?action=${action}`, 'POST');
      showToast(`${action.toUpperCase()} created successfully!`, 'success');

      // If quiz was generated, redirect to quiz or render modal
      if (action === 'quiz' && res.data && res.data.quiz_id) {
        window.location.href = `/quiz`;
      } else if (action === 'notes') {
        window.location.href = `/notes`;
      } else if (action === 'flashcards') {
        window.location.href = `/flashcards`;
      } else {
        alert(JSON.stringify(res.data, null, 2));
      }
    } catch (err) {
      showToast(`Action ${action} failed.`, 'error');
    }
  };
});
