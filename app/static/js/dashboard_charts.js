/**
 * JavaScript để khởi tạo và cập nhật các biểu đồ Chart.js
 */

let timeSeriesChart = null;
let deliveryStatusChart = null;
let topCountriesChart = null;
let topCategoriesChart = null;

/**
 * Khởi tạo tất cả các biểu đồ
 */
function initializeCharts(data) {
    initializeTimeSeriesChart(data.timeSeries);
    initializeDeliveryStatusChart(data.deliveryStatusDist);
    initializeTopCountriesChart(data.topCountries);
    initializeTopCategoriesChart(data.topProducts);
}

/**
 * Khởi tạo biểu đồ xu hướng theo thời gian
 */
function initializeTimeSeriesChart(timeSeriesData) {
    const ctx = document.getElementById('timeSeriesChart');
    if (!ctx) return;
    
    const salesData = timeSeriesData.sales || {};
    const ordersData = timeSeriesData.orders_count || {};
    const lateRateData = timeSeriesData.late_delivery_rate || {};
    
    const labels = Object.keys(salesData).length > 0 ? Object.keys(salesData) : 
                   Object.keys(ordersData).length > 0 ? Object.keys(ordersData) : 
                   Object.keys(lateRateData);
    
    labels.sort();
    
    timeSeriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Doanh thu ($)',
                    data: labels.map(label => salesData[label] || 0),
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'Số đơn hàng',
                    data: labels.map(label => ordersData[label] || 0),
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4
                },
                {
                    label: 'Tỉ lệ giao trễ (%)',
                    data: labels.map(label => lateRateData[label] || 0),
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    yAxisID: 'y2',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Doanh thu ($)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Số đơn hàng'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                },
                y2: {
                    type: 'linear',
                    display: false,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Tỉ lệ giao trễ (%)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    enabled: true
                }
            }
        }
    });
}

/**
 * Khởi tạo biểu đồ phân bố trạng thái giao hàng
 */
function initializeDeliveryStatusChart(deliveryStatusData) {
    const ctx = document.getElementById('deliveryStatusChart');
    if (!ctx) return;
    
    const labels = Object.keys(deliveryStatusData);
    const data = Object.values(deliveryStatusData);
    
    const colors = [
        'rgb(239, 68, 68)',   // Red for Late
        'rgb(34, 197, 94)',   // Green for Advance
        'rgb(59, 130, 246)',  // Blue for On Time
        'rgb(234, 179, 8)',   // Yellow for others
        'rgb(168, 85, 247)'   // Purple for others
    ];
    
    deliveryStatusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: 'Số lượng',
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 800,
                animateRotate: true,
                animateScale: true
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(2);
                            return `${label}: ${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Khởi tạo biểu đồ top quốc gia
 */
function initializeTopCountriesChart(topCountriesData) {
    const ctx = document.getElementById('topCountriesChart');
    if (!ctx) return;
    
    const labels = topCountriesData.map(item => item.country);
    const sales = topCountriesData.map(item => item.sales);
    
    topCountriesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Doanh thu ($)',
                data: sales,
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: 'rgb(59, 130, 246)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Doanh thu: $' + context.parsed.x.toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            });
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString('en-US');
                        }
                    }
                }
            }
        }
    });
}

/**
 * Khởi tạo biểu đồ top danh mục
 */
function initializeTopCategoriesChart(topProductsData) {
    const ctx = document.getElementById('topCategoriesChart');
    if (!ctx) return;
    
    const labels = topProductsData.map(item => item.category);
    const sales = topProductsData.map(item => item.sales);
    
    topCategoriesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Doanh thu ($)',
                data: sales,
                backgroundColor: 'rgba(168, 85, 247, 0.8)',
                borderColor: 'rgb(168, 85, 247)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Doanh thu: $' + context.parsed.x.toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            });
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString('en-US');
                        }
                    }
                }
            }
        }
    });
}

/**
 * Cập nhật tất cả các biểu đồ với dữ liệu mới
 */
function updateCharts(data) {
    if (data.timeSeries && timeSeriesChart) {
        updateTimeSeriesChart(data.timeSeries);
    }
    if (data.delivery_status_dist && deliveryStatusChart) {
        updateDeliveryStatusChart(data.delivery_status_dist);
    }
    if (data.top_countries && topCountriesChart) {
        updateTopCountriesChart(data.top_countries);
    }
    if (data.top_products && topCategoriesChart) {
        updateTopCategoriesChart(data.top_products);
    }
}

/**
 * Cập nhật biểu đồ time series
 */
function updateTimeSeriesChart(timeSeriesData) {
    const salesData = timeSeriesData.sales || {};
    const ordersData = timeSeriesData.orders_count || {};
    const lateRateData = timeSeriesData.late_delivery_rate || {};
    
    const labels = Object.keys(salesData).length > 0 ? Object.keys(salesData) : 
                   Object.keys(ordersData).length > 0 ? Object.keys(ordersData) : 
                   Object.keys(lateRateData);
    labels.sort();
    
    timeSeriesChart.data.labels = labels;
    timeSeriesChart.data.datasets[0].data = labels.map(label => salesData[label] || 0);
    timeSeriesChart.data.datasets[1].data = labels.map(label => ordersData[label] || 0);
    timeSeriesChart.data.datasets[2].data = labels.map(label => lateRateData[label] || 0);
    timeSeriesChart.update('active');  // Smooth animation
}

/**
 * Cập nhật biểu đồ delivery status
 */
function updateDeliveryStatusChart(deliveryStatusData) {
    const labels = Object.keys(deliveryStatusData);
    const data = Object.values(deliveryStatusData);
    
    deliveryStatusChart.data.labels = labels;
    deliveryStatusChart.data.datasets[0].data = data;
    deliveryStatusChart.update('active');  // Smooth animation
}

/**
 * Cập nhật biểu đồ top countries
 */
function updateTopCountriesChart(topCountriesData) {
    const labels = topCountriesData.map(item => item.country);
    const sales = topCountriesData.map(item => item.sales);
    
    topCountriesChart.data.labels = labels;
    topCountriesChart.data.datasets[0].data = sales;
    topCountriesChart.update('active');  // Smooth animation
}

/**
 * Cập nhật biểu đồ top categories
 */
function updateTopCategoriesChart(topProductsData) {
    const labels = topProductsData.map(item => item.category);
    const sales = topProductsData.map(item => item.sales);
    
    topCategoriesChart.data.labels = labels;
    topCategoriesChart.data.datasets[0].data = sales;
    topCategoriesChart.update('active');  // Smooth animation
}

