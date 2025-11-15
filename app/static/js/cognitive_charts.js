/**
 * JavaScript cho Cognitive Dashboard Charts
 */

let strategiesComparisonChart = null;

/**
 * Update comparison chart
 */
function updateComparisonChart(strategies, comparison) {
    const ctx = document.getElementById('strategies-comparison-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (strategiesComparisonChart) {
        strategiesComparisonChart.destroy();
    }
    
    const labels = strategies.map(s => s.name);
    const profitData = strategies.map(s => s.estimated_profit);
    const costData = strategies.map(s => s.estimated_cost);
    const revenueData = strategies.map(s => s.estimated_revenue);
    const confidenceData = strategies.map(s => s.confidence * 100);
    
    strategiesComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Lợi nhuận ước tính ($)',
                    data: profitData,
                    backgroundColor: 'rgba(34, 197, 94, 0.6)',
                    borderColor: 'rgb(34, 197, 94)',
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Chi phí ước tính ($)',
                    data: costData,
                    backgroundColor: 'rgba(239, 68, 68, 0.6)',
                    borderColor: 'rgb(239, 68, 68)',
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Doanh thu ước tính ($)',
                    data: revenueData,
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Độ tin cậy (%)',
                    data: confidenceData,
                    type: 'line',
                    backgroundColor: 'rgba(168, 85, 247, 0.2)',
                    borderColor: 'rgb(168, 85, 247)',
                    borderWidth: 2,
                    yAxisID: 'y1',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: 'So Sánh Chiến Lược',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Giá trị ($)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Độ tin cậy (%)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

