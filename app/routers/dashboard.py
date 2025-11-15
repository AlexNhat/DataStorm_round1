"""
Router cho dashboard.
Cung cấp các endpoint để hiển thị dashboard và API lấy dữ liệu.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
import os
import sys

# Thêm thư mục app vào path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.services.data_loader import load_supply_chain_data, load_weather_data
from app.services.analytics import (
    calculate_supply_chain_kpis,
    get_top_products,
    get_top_countries,
    get_time_series_data,
    calculate_weather_stats,
    analyze_weather_delivery_correlation,
    get_sample_orders,
    engineer_features,
    calculate_advanced_metrics,
    analyze_seasonality
)
from app.services.cache_manager import clear_cache, invalidate_cache_pattern
import pandas as pd

router = APIRouter()

# Cấu hình templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
templates = Jinja2Templates(directory=templates_dir)

# Cache dữ liệu (có thể cải thiện bằng Redis hoặc cache khác)
_data_cache = None


def get_cached_data():
    """Lấy dữ liệu từ cache hoặc load mới."""
    global _data_cache
    
    if _data_cache is None:
        try:
            supply_df = load_supply_chain_data()
            weather_df = load_weather_data()
            _data_cache = {
                'supply': supply_df,
                'weather': weather_df
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi load dữ liệu: {str(e)}")
    
    return _data_cache


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Trang dashboard chính.
    Hiển thị KPI, biểu đồ và bảng dữ liệu.
    """
    try:
        data_cache = get_cached_data()
        supply_df = data_cache['supply']
        weather_df = data_cache['weather']
        
        # Tính toán KPI
        kpis = calculate_supply_chain_kpis(supply_df)
        
        # Top products và countries
        top_products = get_top_products(supply_df, top_n=10, by='Sales')
        top_countries = get_top_countries(supply_df, top_n=10, by='Sales')
        
        # Time series data
        time_series = get_time_series_data(supply_df, freq='M')
        
        # Delivery status distribution
        delivery_status_dist = kpis.get('delivery_status_distribution', {})
        
        # Weather stats
        weather_stats = calculate_weather_stats(weather_df)
        
        # Weather correlation (nếu có thể)
        weather_correlation = analyze_weather_delivery_correlation(supply_df, weather_df)
        
        # Advanced metrics và seasonality
        advanced_metrics = calculate_advanced_metrics(supply_df)
        seasonality = analyze_seasonality(supply_df)
        
        # Sample orders
        sample_orders = get_sample_orders(supply_df, n=50)
        
        # Lấy danh sách countries và categories cho filter
        countries = sorted(supply_df['Order Country'].dropna().unique().tolist()) if 'Order Country' in supply_df.columns else []
        categories = sorted(supply_df['Category Name'].dropna().unique().tolist()) if 'Category Name' in supply_df.columns else []
        delivery_statuses = sorted(supply_df['Delivery Status'].dropna().unique().tolist()) if 'Delivery Status' in supply_df.columns else []
        
        # Date range
        if 'order date (DateOrders)' in supply_df.columns:
            supply_df['order date (DateOrders)'] = pd.to_datetime(supply_df['order date (DateOrders)'], errors='coerce')
            min_date = supply_df['order date (DateOrders)'].min()
            max_date = supply_df['order date (DateOrders)'].max()
            date_range = {
                'min': min_date.strftime('%Y-%m-%d') if pd.notna(min_date) else None,
                'max': max_date.strftime('%Y-%m-%d') if pd.notna(max_date) else None
            }
        else:
            date_range = {'min': None, 'max': None}
        
        context = {
            "request": request,
            "kpis": kpis,
            "top_products": top_products,
            "top_countries": top_countries,
            "time_series": time_series,
            "delivery_status_dist": delivery_status_dist,
            "weather_stats": weather_stats,
            "weather_correlation": weather_correlation,
            "advanced_metrics": advanced_metrics,
            "seasonality": seasonality,
            "sample_orders": sample_orders,
            "countries": countries,
            "categories": categories,
            "delivery_statuses": delivery_statuses,
            "date_range": date_range
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi render dashboard: {str(e)}")


@router.get("/api/data")
async def get_dashboard_data():
    """
    API endpoint trả về dữ liệu JSON cho frontend.
    """
    try:
        data_cache = get_cached_data()
        supply_df = data_cache['supply']
        weather_df = data_cache['weather']
        
        # Tính toán tất cả metrics
        kpis = calculate_supply_chain_kpis(supply_df)
        top_products = get_top_products(supply_df, top_n=10, by='Sales')
        top_countries = get_top_countries(supply_df, top_n=10, by='Sales')
        time_series = get_time_series_data(supply_df, freq='M')
        delivery_status_dist = kpis.get('delivery_status_distribution', {})
        weather_stats = calculate_weather_stats(weather_df)
        weather_correlation = analyze_weather_delivery_correlation(supply_df, weather_df)
        
        return {
            "kpis": kpis,
            "top_products": top_products,
            "top_countries": top_countries,
            "time_series": time_series,
            "delivery_status_dist": delivery_status_dist,
            "weather_stats": weather_stats,
            "weather_correlation": weather_correlation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy dữ liệu: {str(e)}")


@router.get("/api/filter")
async def get_filtered_data(
    country: str = None,
    category: str = None,
    delivery_status: str = None,
    start_date: str = None,
    end_date: str = None
):
    """
    API endpoint để lấy dữ liệu đã lọc.
    Tối ưu: sử dụng boolean indexing thay vì copy DataFrame.
    """
    try:
        import pandas as pd
        
        data_cache = get_cached_data()
        supply_df = data_cache['supply']
        
        # Tạo mask để filter (không copy DataFrame)
        mask = pd.Series([True] * len(supply_df), index=supply_df.index)
        
        # Áp dụng filters với boolean indexing
        if country and 'Order Country' in supply_df.columns:
            mask = mask & (supply_df['Order Country'] == country)
        
        if category and 'Category Name' in supply_df.columns:
            mask = mask & (supply_df['Category Name'] == category)
        
        if delivery_status and 'Delivery Status' in supply_df.columns:
            mask = mask & (supply_df['Delivery Status'] == delivery_status)
        
        if start_date or end_date:
            if 'order date (DateOrders)' in supply_df.columns:
                date_col = pd.to_datetime(supply_df['order date (DateOrders)'], errors='coerce')
                if start_date:
                    mask = mask & (date_col >= pd.to_datetime(start_date))
                if end_date:
                    mask = mask & (date_col <= pd.to_datetime(end_date))
        
        # Apply mask (chỉ tạo view, không copy)
        filtered_df = supply_df[mask]
        
        # Tính lại KPI với dữ liệu đã lọc
        kpis = calculate_supply_chain_kpis(filtered_df)
        top_products = get_top_products(filtered_df, top_n=10, by='Sales')
        top_countries = get_top_countries(filtered_df, top_n=10, by='Sales')
        time_series = get_time_series_data(filtered_df, freq='M')
        delivery_status_dist = kpis.get('delivery_status_distribution', {})
        
        return {
            "kpis": kpis,
            "top_products": top_products,
            "top_countries": top_countries,
            "time_series": time_series,
            "delivery_status_dist": delivery_status_dist,
            "filtered_rows": len(filtered_df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lọc dữ liệu: {str(e)}")


@router.get("/api/advanced-metrics")
async def get_advanced_metrics():
    """
    API endpoint trả về advanced metrics và seasonality analysis.
    """
    try:
        data_cache = get_cached_data()
        supply_df = data_cache['supply']
        
        advanced_metrics = calculate_advanced_metrics(supply_df)
        seasonality = analyze_seasonality(supply_df)
        
        return {
            "advanced_metrics": advanced_metrics,
            "seasonality": seasonality
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tính advanced metrics: {str(e)}")


@router.get("/api/correlation-matrix")
async def get_correlation_matrix():
    """
    API endpoint trả về correlation matrix giữa các biến.
    """
    try:
        data_cache = get_cached_data()
        supply_df = data_cache['supply']
        weather_df = data_cache['weather']
        
        # Merge data
        merged = analyze_weather_delivery_correlation(supply_df, weather_df)
        if 'error' in merged:
            return {"error": merged['error']}
        
        # Select numeric columns for correlation
        numeric_cols = ['Sales', 'Benefit per order', 'Late_delivery_risk',
                       'Days for shipping (real)', 'Days for shipment (scheduled)']
        
        # Try to get merged data
        supply_date_col = 'order date (DateOrders)'
        supply_customer_col = 'Order Customer Id'
        weather_date_col = 'order_date'
        weather_customer_col = 'customer_id'
        
        if (supply_date_col in supply_df.columns and 
            supply_customer_col in supply_df.columns and
            weather_date_col in weather_df.columns and
            weather_customer_col in weather_df.columns):
            
            supply_df[supply_date_col] = pd.to_datetime(supply_df[supply_date_col], errors='coerce')
            weather_df[weather_date_col] = pd.to_datetime(weather_df[weather_date_col], errors='coerce')
            
            supply_df['order_date_only'] = supply_df[supply_date_col].dt.date
            weather_df['order_date_only'] = weather_df[weather_date_col].dt.date
            
            merged_df = supply_df.merge(
                weather_df,
                left_on=[supply_customer_col, 'order_date_only'],
                right_on=[weather_customer_col, 'order_date_only'],
                how='inner'
            )
            
            if len(merged_df) > 0:
                # Calculate correlation matrix
                corr_cols = numeric_cols + ['temperature_2m_mean', 'precipitation_sum', 
                                           'wind_speed_10m_mean', 'relative_humidity_2m_mean']
                available_cols = [col for col in corr_cols if col in merged_df.columns]
                
                if len(available_cols) > 1:
                    corr_matrix = merged_df[available_cols].corr()
                    return {
                        "correlation_matrix": corr_matrix.to_dict(),
                        "columns": available_cols
                    }
        
        return {"error": "Không đủ dữ liệu để tính correlation matrix"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tính correlation matrix: {str(e)}")


@router.get("/api/scatter-data")
async def get_scatter_data():
    """
    API endpoint trả về dữ liệu cho scatter plot (Temperature vs Late Delivery).
    """
    try:
        data_cache = get_cached_data()
        supply_df = data_cache['supply']
        weather_df = data_cache['weather']
        
        # Merge data
        supply_date_col = 'order date (DateOrders)'
        supply_customer_col = 'Order Customer Id'
        weather_date_col = 'order_date'
        weather_customer_col = 'customer_id'
        
        if (supply_date_col in supply_df.columns and 
            supply_customer_col in supply_df.columns and
            weather_date_col in weather_df.columns and
            weather_customer_col in weather_df.columns):
            
            supply_df[supply_date_col] = pd.to_datetime(supply_df[supply_date_col], errors='coerce')
            weather_df[weather_date_col] = pd.to_datetime(weather_df[weather_date_col], errors='coerce')
            
            supply_df['order_date_only'] = supply_df[supply_date_col].dt.date
            weather_df['order_date_only'] = weather_df[weather_date_col].dt.date
            
            merged_df = supply_df.merge(
                weather_df,
                left_on=[supply_customer_col, 'order_date_only'],
                right_on=[weather_customer_col, 'order_date_only'],
                how='inner'
            )
            
            if len(merged_df) > 0 and 'temperature_2m_mean' in merged_df.columns and 'Late_delivery_risk' in merged_df.columns:
                scatter_data = merged_df[['temperature_2m_mean', 'Late_delivery_risk']].dropna()
                scatter_list = [
                    {'x': float(row['temperature_2m_mean']), 'y': float(row['Late_delivery_risk'])}
                    for _, row in scatter_data.iterrows()
                ]
                return {"data": scatter_list[:1000]}  # Limit to 1000 points for performance
        
        return {"data": [], "error": "Không đủ dữ liệu"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy scatter data: {str(e)}")


@router.get("/api/boxplot-data")
async def get_boxplot_data():
    """
    API endpoint trả về dữ liệu cho box plot (Sales distribution by category).
    """
    try:
        data_cache = get_cached_data()
        supply_df = data_cache['supply']
        
        if 'Category Name' in supply_df.columns and 'Sales' in supply_df.columns:
            # Group by category and get sales values
            categories = supply_df['Category Name'].dropna().unique()[:10]  # Top 10
            boxplot_data = []
            
            for category in categories:
                category_sales = supply_df[supply_df['Category Name'] == category]['Sales'].dropna().tolist()
                if len(category_sales) > 0:
                    boxplot_data.append({
                        'category': str(category),
                        'values': [float(x) for x in category_sales[:100]]  # Limit per category
                    })
            
            return {"data": boxplot_data}
        
        return {"data": [], "error": "Không đủ dữ liệu"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy boxplot data: {str(e)}")


@router.get("/api/waterfall-data")
async def get_waterfall_data():
    """
    API endpoint trả về dữ liệu cho waterfall chart (Profit breakdown).
    """
    try:
        data_cache = get_cached_data()
        supply_df = data_cache['supply']
        
        if 'Category Name' in supply_df.columns and 'Benefit per order' in supply_df.columns:
            # Group by category and sum benefit
            category_benefit = supply_df.groupby('Category Name')['Benefit per order'].sum().sort_values(ascending=False).head(10)
            
            waterfall_data = []
            cumulative = 0
            
            for category, benefit in category_benefit.items():
                waterfall_data.append({
                    'label': str(category),
                    'value': float(benefit),
                    'cumulative': float(cumulative)
                })
                cumulative += benefit
            
            return {"data": waterfall_data}
        
        return {"data": [], "error": "Không đủ dữ liệu"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy waterfall data: {str(e)}")


@router.post("/api/cache/clear")
async def clear_data_cache():
    """
    API endpoint để clear cache (admin function).
    """
    try:
        clear_cache()
        # Invalidate data cache
        global _data_cache
        _data_cache = None
        return {"status": "success", "message": "Cache đã được xóa"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa cache: {str(e)}")

