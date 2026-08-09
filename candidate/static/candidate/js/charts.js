/**
 * Chart.js — Radar, Pie, and Bar charts for Dashboard & Report pages.
 * Expects global variables set in the template: skillCategories, marketData, careerPaths
 */
document.addEventListener('DOMContentLoaded', () => {

    // ── Chart.js defaults ──
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
    Chart.defaults.font.family = "'Inter', sans-serif";

    // ── 1. Skill Radar Chart ──
    const radarEl = document.getElementById('skillRadarChart');
    if (radarEl && window.skillCategories) {
        const cats = window.skillCategories;
        const labels = Object.keys(cats);
        const values = Object.values(cats);
        const maxVal = Math.max(...values, 1);

        new Chart(radarEl, {
            type: 'radar',
            data: {
                labels,
                datasets: [{
                    label: 'Your Skills',
                    data: values,
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                    borderColor: '#6366f1',
                    borderWidth: 2,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: maxVal + 1,
                        ticks: { stepSize: 1, display: false },
                        grid: { color: 'rgba(255,255,255,0.06)' },
                        angleLines: { color: 'rgba(255,255,255,0.06)' },
                        pointLabels: { font: { size: 11, weight: '500' } },
                    },
                },
                plugins: { legend: { display: false } },
            },
        });
    }

    // ── 2. Skill Distribution Pie ──
    const pieEl = document.getElementById('skillPieChart');
    if (pieEl && window.skillCategories) {
        const cats = window.skillCategories;
        const labels = Object.keys(cats).filter(k => cats[k] > 0);
        const values = labels.map(k => cats[k]);
        const colours = ['#6366f1', '#8b5cf6', '#10b981', '#3b82f6', '#f59e0b', '#ef4444'];

        new Chart(pieEl, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: colours.slice(0, labels.length),
                    borderWidth: 0,
                    hoverOffset: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, font: { size: 11 } },
                    },
                },
            },
        });
    }

    // ── 3. Hiring Trend Bar Chart ──
    const barEl = document.getElementById('hiringTrendChart');
    if (barEl && window.marketData && window.marketData.hiring_trend) {
        const md = window.marketData;

        new Chart(barEl, {
            type: 'bar',
            data: {
                labels: md.months || [],
                datasets: [{
                    label: 'Job Postings Index',
                    data: md.hiring_trend,
                    backgroundColor: createGradient(barEl, '#6366f1', '#8b5cf6'),
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 32,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' } },
                    x: { grid: { display: false } },
                },
                plugins: {
                    legend: { display: false },
                },
            },
        });
    }

    // ── 4. Top Skills Demand (Horizontal Bar) ──
    const demandEl = document.getElementById('skillDemandChart');
    if (demandEl && window.marketData && window.marketData.top_skills) {
        const skills = window.marketData.top_skills;
        const values = skills.map((_, i) => 100 - i * 15);

        new Chart(demandEl, {
            type: 'bar',
            data: {
                labels: skills,
                datasets: [{
                    label: 'Demand Index',
                    data: values,
                    backgroundColor: ['#6366f1', '#8b5cf6', '#10b981', '#3b82f6', '#f59e0b'],
                    borderRadius: 6,
                    borderSkipped: false,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.04)' } },
                    y: { grid: { display: false } },
                },
                plugins: { legend: { display: false } },
            },
        });
    }

    // ── Animate score bars ──
    document.querySelectorAll('.score-bar-fill[data-width]').forEach(bar => {
        setTimeout(() => {
            bar.style.width = bar.dataset.width + '%';
        }, 400);
    });
});

function createGradient(canvas, c1, c2) {
    const ctx = canvas.getContext('2d');
    const grad = ctx.createLinearGradient(0, 0, 0, 300);
    grad.addColorStop(0, c1);
    grad.addColorStop(1, c2);
    return grad;
}
