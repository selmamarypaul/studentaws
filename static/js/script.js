/**
 * StudentHub - Student Registration Portal JavaScript
 * Pure Vanilla JavaScript for UI interactions, photo preview, and AJAX submission.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('registrationForm');
  const photoInput = document.getElementById('photoInput');
  const dropzone = document.getElementById('uploadDropzone');
  const uploadPrompt = document.getElementById('uploadPrompt');
  const previewContainer = document.getElementById('previewContainer');
  const previewThumbnail = document.getElementById('previewThumbnail');
  const previewFilename = document.getElementById('previewFilename');
  const previewFilesize = document.getElementById('previewFilesize');
  const btnReplace = document.getElementById('btnReplace');
  const submitBtn = document.getElementById('submitBtn');
  const btnText = document.getElementById('btnText');
  const alertBanner = document.getElementById('alertBanner');
  const alertMessage = document.getElementById('alertMessage');

  const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png'];
  const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

  // Helper: Format Bytes to KB/MB
  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  // Helper: Display Alert Banner
  function showAlert(message, type = 'error') {
    alertBanner.className = `alert-banner alert-${type}`;
    const icon = type === 'success' ? '✓' : '⚠️';
    alertBanner.querySelector('.alert-icon').textContent = icon;
    alertMessage.textContent = message;
    alertBanner.classList.remove('hidden');
    alertBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Helper: Hide Alert Banner
  function hideAlert() {
    alertBanner.classList.add('hidden');
  }

  // Photo Input Handling
  function handleFileSelect(file) {
    if (!file) return;

    const fileExt = file.name.split('.').pop().toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(fileExt)) {
      showAlert('Invalid file format. Please upload a JPG, JPEG, or PNG image.');
      photoInput.value = '';
      resetPhotoPreview();
      return;
    }

    hideAlert();

    // Read and display thumbnail preview
    const reader = new FileReader();
    reader.onload = (e) => {
      previewThumbnail.src = e.target.result;
      previewFilename.textContent = file.name;
      previewFilesize.textContent = formatBytes(file.size);

      uploadPrompt.style.display = 'none';
      previewContainer.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  }

  function resetPhotoPreview() {
    uploadPrompt.style.display = 'flex';
    previewContainer.classList.add('hidden');
    previewThumbnail.src = '';
    previewFilename.textContent = '';
    previewFilesize.textContent = '';
  }

  photoInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  });

  // Drag and Drop Events
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files && files.length > 0) {
      photoInput.files = files;
      handleFileSelect(files[0]);
    }
  });

  btnReplace.addEventListener('click', (e) => {
    e.preventDefault();
    photoInput.click();
  });

  // Form Validation & Submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert();

    const name = document.getElementById('nameInput').value.trim();
    const email = document.getElementById('emailInput').value.trim();
    const course = document.getElementById('courseSelect').value;
    const photo = photoInput.files[0];

    // Client-side Validation
    if (!name) {
      showAlert('Please enter the student\'s full name.');
      return;
    }

    if (!email || !EMAIL_REGEX.test(email)) {
      showAlert('Please enter a valid email address (e.g. student@college.edu).');
      return;
    }

    if (!course) {
      showAlert('Please select a course of study.');
      return;
    }

    if (!photo) {
      showAlert('Please select a student photo to upload.');
      return;
    }

    // Set Loading State
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    btnText.textContent = 'Registering Student...';

    const formData = new FormData(form);

    try {
      const response = await fetch('/register', {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        body: formData
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showAlert(result.message || 'Registration Successful!', 'success');
        form.reset();
        resetPhotoPreview();
      } else {
        showAlert(result.message || 'Registration failed. Please try again.');
      }
    } catch (error) {
      console.error('Submission Error:', error);
      showAlert('Network or connection error. Please verify your connection.');
    } finally {
      submitBtn.disabled = false;
      submitBtn.classList.remove('loading');
      btnText.textContent = 'Register Student';
    }
  });
});
