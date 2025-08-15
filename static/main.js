const $ = (sel) => document.querySelector(sel);

const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

let charts = {};

function resetCharts() {
  Object.values(charts).forEach((c) => c.destroy());
  charts = {};
}

function drawYearChart(canvasId, year, monthly, p1, p2) {
  const ctx = document.getElementById(canvasId);
  const p1Data = months.map((_, i) => monthly[year][i+1]?.[p1] ?? 0);
  const p2Data = months.map((_, i) => monthly[year][i+1]?.[p2] ?? 0);

  charts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: p1,
          data: p1Data,
          borderColor: '#111',
          backgroundColor: 'rgba(0,0,0,0.08)',
          tension: 0.3
        },
        {
          label: p2,
          data: p2Data,
          borderColor: '#7a7a7a',
          backgroundColor: 'rgba(0,0,0,0.04)',
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: {
          grid: { color: '#e6e6e6' },
          ticks: { color: '#6b6b6b' }
        },
        y: {
          grid: { color: '#e6e6e6' },
          ticks: { color: '#6b6b6b' },
          beginAtZero: true
        }
      },
      plugins: {
        legend: { labels: { color: '#111' } },
        tooltip: {
          enabled: true,
          backgroundColor: '#ffffff',
          titleColor: '#111',
          bodyColor: '#111',
          borderColor: '#e6e6e6',
          borderWidth: 1,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y ?? 0}`
          }
        }
      }
    }
  });
}

async function analyze(formData) {
  const res = await fetch('/analyze', { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(err.error || 'Request failed');
  }
  return res.json();
}

function renderStats(data) {
  const { person1, person2 } = data;
  $('#p1-name').textContent = person1.name;
  $('#p2-name').textContent = person2.name;
  $('#p1-messages').textContent = person1.messages;
  $('#p2-messages').textContent = person2.messages;
  $('#p1-characters').textContent = person1.characters;
  $('#p2-characters').textContent = person2.characters;
  $('#p1-avg').textContent = person1.average_length;
  $('#p2-avg').textContent = person2.average_length;
  $('#p1-sorry').textContent = person1.sorry_count;
  $('#p2-sorry').textContent = person2.sorry_count;
  $('#p1-media').textContent = person1.media_count;
  $('#p2-media').textContent = person2.media_count;
  $('#p1-links').textContent = person1.link_count;
  $('#p2-links').textContent = person2.link_count;
  $('#p1-emojis').textContent = person1.emoji_count;
  $('#p2-emojis').textContent = person2.emoji_count;
  $('#p1-active').textContent = person1.active_days_percentage;
  $('#p2-active').textContent = person2.active_days_percentage;
  $('#p1-growth').textContent = person1.monthly_growth;
  $('#p2-growth').textContent = person2.monthly_growth;
  $('#stats').hidden = false;
}

function hasYearData(year, monthly, p1, p2) {
  const monthsArr = Object.values(monthly[year] || {});
  return monthsArr.some((m) => (m?.[p1] || 0) > 0 || (m?.[p2] || 0) > 0);
}

function renderCharts(data) {
  const { person1, person2, monthly } = data;
  resetCharts();
  const years = [2022, 2023, 2024, 2025];

  let anyVisible = false;
  years.forEach((y) => {
    const card = document.getElementById(`card-${y}`);
    if (hasYearData(y, monthly, person1.name, person2.name)) {
      card.hidden = false;
      drawYearChart(`chart-${y}`, y, monthly, person1.name, person2.name);
      anyVisible = true;
    } else {
      card.hidden = true;
    }
  });

  $('#charts').hidden = !anyVisible;
}

document.addEventListener('DOMContentLoaded', () => {
  const form = $('#upload-form');
  const fileInput = $('#file-input');
  const selectBtn = $('#select-file');
  const fileName = $('#file-name');
  const analyzeBtn = $('#analyze-btn');
  const errorEl = $('#error');
  const uploadPage = $('#upload-page');
  const dashPage = $('#dashboard-page');
  const backBtn = $('#back-btn');

  selectBtn.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) {
      fileName.textContent = fileInput.files[0].name;
      analyzeBtn.disabled = false;
    } else {
      fileName.textContent = '';
      analyzeBtn.disabled = true;
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.hidden = true;
    $('#stats').hidden = true;
    $('#charts').hidden = true;

    if (!fileInput.files || !fileInput.files[0]) {
      errorEl.textContent = 'Please select a .txt file.';
      errorEl.hidden = false;
      return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing…';

    try {
      const fd = new FormData();
      fd.append('file', fileInput.files[0]);
      const data = await analyze(fd);
      renderStats(data);
      renderCharts(data);
      uploadPage.classList.remove('active');
      uploadPage.hidden = true;
      dashPage.hidden = false;
      dashPage.classList.add('active');
    } catch (err) {
      errorEl.textContent = err.message || 'Something went wrong';
      errorEl.hidden = false;
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = 'Analyze';
    }
  });

  backBtn.addEventListener('click', () => {
    // Reset UI
    fileInput.value = '';
    fileName.textContent = '';
    analyzeBtn.disabled = true;
    $('#stats').hidden = true;
    $('#charts').hidden = true;
    Object.values(charts).forEach((c) => c.destroy());
    charts = {};
    // Toggle pages
    dashPage.classList.remove('active');
    dashPage.hidden = true;
    uploadPage.hidden = false;
    uploadPage.classList.add('active');
  });
});


