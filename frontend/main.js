import Chart from 'chart.js/auto';

const API_URL = 'https://quantengine-7i5s.onrender.com/api/monte-carlo';

// Elements
const meanGrowth = document.getElementById('mean-growth');
const stdGrowth = document.getElementById('std-growth');
const meanMargin = document.getElementById('mean-margin');
const stdMargin = document.getElementById('std-margin');
const terminalGrowth = document.getElementById('terminal-growth');
const simulations = document.getElementById('simulations');
const runBtn = document.getElementById('run-sim');
const loading = document.getElementById('loading');
const themeToggle = document.getElementById('theme-toggle');

const kpiBear = document.getElementById('kpi-bear');
const kpiBase = document.getElementById('kpi-base');
const kpiBull = document.getElementById('kpi-bull');

// Realtime value updates for sliders
const updateVal = (id, val, isPct = false) => {
  document.getElementById(`${id}-val`).innerText = isPct ? `${(val * 100).toFixed(1)}%` : Number(val).toLocaleString();
};

[
  [meanGrowth, true], [stdGrowth, true], 
  [meanMargin, true], [stdMargin, true], 
  [terminalGrowth, true], [simulations, false]
].forEach(([el, isPct]) => {
  el.addEventListener('input', (e) => updateVal(e.target.id, e.target.value, isPct));
});

// Chart.js Setup
const ctx = document.getElementById('monteCarloChart').getContext('2d');
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = 'Inter';

let mcChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Probability Density',
      data: [],
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: 0
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items) => `Share Price: ₹${Number(items[0].label).toFixed(0)}`,
          label: () => ''
        }
      }
    },
    scales: {
      x: { 
        grid: { color: getComputedStyle(document.body).getPropertyValue('--chart-grid') },
        ticks: { color: getComputedStyle(document.body).getPropertyValue('--text-secondary') }
      },
      y: { display: false, grid: { display: false } }
    }
  }
});

// Theme Toggle Logic
themeToggle.addEventListener('click', () => {
  document.body.classList.toggle('light-mode');
  const isLight = document.body.classList.contains('light-mode');
  themeToggle.innerText = isLight ? '🌙 Dark Mode' : '☀️ Light Mode';
  
  // Dynamically update Chart.js colors based on CSS variables
  mcChart.options.scales.x.grid.color = getComputedStyle(document.body).getPropertyValue('--chart-grid');
  mcChart.options.scales.x.ticks.color = getComputedStyle(document.body).getPropertyValue('--text-secondary');
  mcChart.data.datasets[0].backgroundColor = getComputedStyle(document.body).getPropertyValue('--chart-bg');
  mcChart.update();
});

// Fetch Data
const runSimulation = async () => {
  loading.classList.add('active');
  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mean_growth: parseFloat(meanGrowth.value),
        std_growth: parseFloat(stdGrowth.value),
        mean_margin: parseFloat(meanMargin.value),
        std_margin: parseFloat(stdMargin.value),
        terminal_growth: parseFloat(terminalGrowth.value),
        simulations: parseInt(simulations.value)
      })
    });
    const data = await res.json();
    
    // Update KPIs
    kpiBear.innerText = `₹ ${data.bear_case.toFixed(0)}`;
    kpiBase.innerText = `₹ ${data.base_case.toFixed(0)}`;
    kpiBull.innerText = `₹ ${data.bull_case.toFixed(0)}`;

    // Update Chart
    mcChart.data.labels = data.histogram.bins.map(b => b.toFixed(0));
    mcChart.data.datasets[0].data = data.histogram.counts;
    mcChart.update();
  } catch (error) {
    console.error("Simulation failed:", error);
  } finally {
    loading.classList.remove('active');
  }
};

runBtn.addEventListener('click', runSimulation);

// Run initial
runSimulation();
