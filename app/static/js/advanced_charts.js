/**
 * JavaScript cho các biểu đồ nâng cao mới
 */

let correlationHeatmapChart = null;
let scatterChart = null;
let boxPlotChart = null;
let waterfallChart = null;
let seasonalityChart = null;

/**
 * Khởi tạo Correlation Heatmap
 * Sử dụng bar chart để hiển thị correlation matrix
 */
function initializeCorrelationHeatmap(correlationData) {
    const ctx = document.getElementById('correlationHeatmapChart');
    if (!ctx || !correlationData || correlationData.error) return;
    
    const matrix = correlationData.correlation_matrix || {};
    const columns = correlationData.columns || [];
    
    if (columns.length === 0) return;
    
    // Prepare data: flatten matrix thành array of bars
    const data = [];
    const labels = [];
    
    for (let i = 0; i < columns.length; i++) {
        for (let j = 0; j < columns.length; j++) {
            const value = matrix[columns[i]]?.[columns[j]] || 0;
            labels.push(`${columns[i]} vs ${columns[j]}`);
            data.push(value);
        }
    }
    
    // Color based on correlation value
    const backgroundColors = data.map(value => {
        if (value >= 0.7) return 'rgba(34, 197, 94, 0.8)';  // Strong positive
        if (value >= 0.3) return 'rgba(59, 130, 246, 0.6)';  // Moderate positive
        if (value >= -0.3) return 'rgba(234, 179, 8, 0.4)';  // Weak
        if (value >= -0.7) return 'rgba(239, 68, 68, 0.6)';  // Moderate negative
        return 'rgba(239, 68, 68, 0.8)';  // Strong negative
    });
    
    correlationHeatmapChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: columns,  // Show only column names
            datasets: columns.map((col, idx) => ({
                label: col,
                data: columns.map(c => matrix[col]?.[c] || 0),
                backgroundColor: columns.map(c => {
                    const val = matrix[col]?.[c] || 0;
                    if (val >= 0.7) return 'rgba(34, 197, 94, 0.8)';
                    if (val >= 0.3) return 'rgba(59, 130, 246, 0.6)';
                    if (val >= -0.3) return 'rgba(234, 179, 8, 0.4)';
                    if (val >= -0.7) return 'rgba(239, 68, 68, 0.6)';
                    return 'rgba(239, 68, 68, 0.8)';
                })
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(3)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    min: -1,
                    max: 1,
                    ticks: {
                        stepSize: 0.2
                    },
                    title: {
                        display: true,
                        text: 'Correlation Coefficient'
                    }
                }
            }
        }
    });
}

/**
 * Khởi tạo Scatter Plot: Temperature vs Late Delivery
 */
function initializeScatterChart(scatterData) {
    const ctx = document.getElementById('scatterChart');
    if (!ctx || !scatterData || scatterData.length === 0) return;
    
    scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Nhiệt độ vs Giao trễ',
                data: scatterData,
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: 'rgb(59, 130, 246)',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Nhiệt độ: ${context.parsed.x}°C, Giao trễ: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Nhiệt độ (°C)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Giao trễ (0=Không, 1=Có)'
                    },
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

/**
 * Khởi tạo Box Plot: Sales Distribution by Category
 * Sử dụng bar chart với error bars để mô phỏng box plot
 */
function initializeBoxPlot(boxPlotData) {
    const ctx = document.getElementById('boxPlotChart');
    if (!ctx || !boxPlotData || boxPlotData.length === 0) return;
    
    const labels = boxPlotData.map(item => item.category);
    
    // Calculate statistics for each category
    const datasets = [{
        label: 'Mean Sales',
        data: boxPlotData.map(item => {
            const values = item.values;
            if (values.length === 0) return 0;
            return values.reduce((a, b) => a + b, 0) / values.length;
        }),
        backgroundColor: 'rgba(168, 85, 247, 0.6)',
        borderColor: 'rgb(168, 85, 247)',
        borderWidth: 1
    }];
    
    boxPlotChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const category = boxPlotData[context.dataIndex];
                            const values = category.values;
                            if (values.length === 0) return 'No data';
                            
                            const sorted = [...values].sort((a, b) => a - b);
                            const q1 = sorted[Math.floor(sorted.length * 0.25)];
                            const median = sorted[Math.floor(sorted.length * 0.5)];
                            const q3 = sorted[Math.floor(sorted.length * 0.75)];
                            const min = sorted[0];
                            const max = sorted[sorted.length - 1];
                            
                            return [
                                `Mean: $${context.parsed.y.toFixed(2)}`,
                                `Min: $${min.toFixed(2)}`,
                                `Q1: $${q1.toFixed(2)}`,
                                `Median: $${median.toFixed(2)}`,
                                `Q3: $${q3.toFixed(2)}`,
                                `Max: $${max.toFixed(2)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Doanh thu ($)'
                    }
                }
            }
        }
    });
}

/**
 * Khởi tạo Waterfall Chart: Profit Breakdown
 */
function initializeWaterfallChart(waterfallData) {
    const ctx = document.getElementById('waterfallChart');
    if (!ctx || !waterfallData || waterfallData.length === 0) return;
    
    const labels = waterfallData.map(item => item.label);
    const values = waterfallData.map(item => item.value);
    
    // Calculate cumulative for waterfall effect
    const cumulative = [];
    let runningTotal = 0;
    for (let i = 0; i < values.length; i++) {
        cumulative.push(runningTotal);
        runningTotal += values[i];
    }
    
    waterfallChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Lợi nhuận',
                data: values,
                backgroundColor: values.map(val => 
                    val >= 0 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)'
                ),
                borderColor: values.map(val => 
                    val >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'
                ),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 1000
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const idx = context.dataIndex;
                            const val = values[idx];
                            const cum = cumulative[idx];
                            return [
                                `Lợi nhuận: $${val.toLocaleString('en-US', {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                })}`,
                                `Cumulative: $${(cum + val).toLocaleString('en-US', {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                })}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Lợi nhuận ($)'
                    }
                }
            }
        }
    });
}

/**
 * Khởi tạo Seasonality Chart
 */
function initializeSeasonalityChart(seasonalityData) {
    const ctx = document.getElementById('seasonalityChart');
    if (!ctx || !seasonalityData || !seasonalityData.monthly_sales) return;
    
    const monthlySales = seasonalityData.monthly_sales || {};
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const labels = Object.keys(monthlySales).map(m => monthNames[parseInt(m) - 1] || `Month ${m}`);
    const data = Object.values(monthlySales);
    
    seasonalityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Doanh thu theo tháng',
                data: data,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Doanh thu: $${context.parsed.y.toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            })}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Doanh thu ($)'
                    }
                }
            }
        }
    });
}

/**
 * Load và khởi tạo tất cả advanced charts
 */
async function loadAdvancedCharts() {
    try {
        // Load correlation matrix
        const corrResponse = await fetch('/dashboard/api/correlation-matrix');
        if (corrResponse.ok) {
            const corrData = await corrResponse.json();
            if (!corrData.error) {
                initializeCorrelationHeatmap(corrData);
            }
        }
        
        // Load advanced metrics for seasonality
        const metricsResponse = await fetch('/dashboard/api/advanced-metrics');
        if (metricsResponse.ok) {
            const metricsData = await metricsResponse.json();
            if (metricsData.seasonality) {
                initializeSeasonalityChart(metricsData.seasonality);
            }
        }
        
        // Load scatter plot data
        const scatterResponse = await fetch('/dashboard/api/scatter-data');
        if (scatterResponse.ok) {
            const scatterData = await scatterResponse.json();
            if (scatterData.data && scatterData.data.length > 0) {
                initializeScatterChart(scatterData.data);
            }
        }
        
        // Load box plot data
        const boxplotResponse = await fetch('/dashboard/api/boxplot-data');
        if (boxplotResponse.ok) {
            const boxplotData = await boxplotResponse.json();
            if (boxplotData.data && boxplotData.data.length > 0) {
                initializeBoxPlot(boxplotData.data);
            }
        }
        
        // Load waterfall data
        const waterfallResponse = await fetch('/dashboard/api/waterfall-data');
        if (waterfallResponse.ok) {
            const waterfallData = await waterfallResponse.json();
            if (waterfallData.data && waterfallData.data.length > 0) {
                initializeWaterfallChart(waterfallData.data);
            }
        }
    } catch (error) {
        console.error('Error loading advanced charts:', error);
    }
}

