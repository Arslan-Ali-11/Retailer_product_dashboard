"""
Streamlit Client Portal - Stock Monitoring Dashboard
A real-time dashboard for monitoring stock levels from Google Sheets
"""

import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh  # type: ignore

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Client Portal - Stock Monitor",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def load_data_from_gsheet():
    """
    Load ALL stock data from Google Sheets using CSV export URL.
    Renames critical columns for logic, but keeps all other retailer data.
    """
    try:
        # Get spreadsheet URL from secrets
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Extract sheet ID from URL
        if "/d/" in spreadsheet_url:
            sheet_id = spreadsheet_url.split("/d/")[1].split("/")[0]
        else:
            st.error("Invalid Google Sheet URL format")
            return pd.DataFrame()
        
        # Construct CSV export URL (gid=0 usually implies the first tab)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        
        # Read data from CSV export
        df = pd.read_csv(csv_url)

        # ---------------------------------------------------------
        # 1. CLEANING: Remove empty rows
        # ---------------------------------------------------------
        # We drop rows where the first or second column is missing (NaN)
        # This handles the empty rows often found at the bottom of sheets
        df = df.dropna(subset=[df.columns[0], df.columns[1]]) 

        # ---------------------------------------------------------
        # 2. SMART MAPPING: Identify Key Columns for Logic
        # ---------------------------------------------------------
        # We need to find which columns are "Stock" and "Restock Level" 
        # so the alerts work, but we won't delete the other columns.
        
        column_map = {
            'Available Stock': ['stock', 'qty', 'quantity', 'inventory', 'available', 'on hand', 'available stock(sync with shopify)'],
            'Restock Level': ['restock level', 'threshold', 'min stock', 'reorder point', 'minimum'],
            # We map these to ensure standard naming for the UI, but keep others as is
            'Product Name': ['product name', 'name', 'title', 'item name'],
            'SKU': ['sku', 'id', 'item no', 'item number', 'barcode']
        }

        # Normalize df columns for easier matching (lowercase + strip spaces)
        current_cols = {c.lower().strip(): c for c in df.columns}
        
        rename_dict = {}

        # Find the critical columns
        for internal_name, aliases in column_map.items():
            for alias in aliases:
                if alias in current_cols:
                    # Map the actual sheet header to our internal name
                    rename_dict[current_cols[alias]] = internal_name
                    break
        
        # Apply the renaming (Only renames matches, keeps other columns like 'Supplier' intact)
        df = df.rename(columns=rename_dict)

        # ---------------------------------------------------------
        # 3. TYPE CONVERSION & CALCULATIONS
        # ---------------------------------------------------------
        
        # Ensure Critical Columns exist (Fail-safe)
        if 'Available Stock' not in df.columns:
            st.error("⚠️ Could not detect a 'Stock' column. Please check headers.")
            return pd.DataFrame()
            
        if 'Restock Level' not in df.columns:
            df['Restock Level'] = 10 # Default if missing

        # Force numbers
        df['Available Stock'] = pd.to_numeric(df['Available Stock'], errors='coerce').fillna(0).astype(int)
        df['Restock Level'] = pd.to_numeric(df['Restock Level'], errors='coerce').fillna(0).astype(int)
        
        # Add Status column based on logic
        df['Status'] = df.apply(lambda row: 'Critical' if row['Available Stock'] <= 10 
                               else 'Low Stock' if row['Available Stock'] < row['Restock Level']
                               else 'In Stock', axis=1)
        
        # CRITICAL CHANGE: We return the WHOLE dataframe now, not just selected columns
        return df

    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {e}")
        return pd.DataFrame()

# ============================================================================
# HELPER FUNCTIONS (ADDITIONAL)
# ============================================================================
def get_critical_items(df, threshold=10):
    """
    Return list of records that are at or below the given threshold.
    """
    if df is None or df.empty:
        return []
    if 'Available Stock' not in df.columns:
        return []
    try:
        mask = pd.to_numeric(df['Available Stock'], errors='coerce').fillna(0) <= int(threshold)
    except Exception:
        # Fallback if conversion fails
        mask = df['Available Stock'] <= threshold
    return df[mask].to_dict('records')

def highlight_low_stock(row):
    """
    Styler function for df.style.apply(axis=1).
    Highlights the entire row if Available Stock < Restock Level.
    """
    try:
        available = pd.to_numeric(row.get('Available Stock', 0), errors='coerce')
        restock = pd.to_numeric(row.get('Restock Level', 0), errors='coerce')
        low = available < restock
    except Exception:
        low = False

    styles = []
    for _ in row.index:
        styles.append('background-color: #ffcccc' if low else '')
    return styles

def calculate_metrics(df):
    """
    Return (total_products, low_stock_count, total_stock_units)
    """
    total_products = len(df)
    if 'Available Stock' in df.columns:
        stock_vals = pd.to_numeric(df['Available Stock'], errors='coerce').fillna(0)
        stock_value = int(stock_vals.sum())
    else:
        stock_value = 0

    if 'Available Stock' in df.columns and 'Restock Level' in df.columns:
        low_mask = pd.to_numeric(df['Available Stock'], errors='coerce').fillna(0) < pd.to_numeric(df['Restock Level'], errors='coerce').fillna(0)
        low_stock_count = int(low_mask.sum())
    else:
        low_stock_count = 0

    return total_products, low_stock_count, stock_value

def trigger_restock_webhook(webhook_url, items):
    """
    Trigger a POST to the configured webhook with the items payload.
    Returns (success: bool, message: str).
    """
    if not webhook_url:
        return False, "Webhook URL not configured"

    payload = {"items": items}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if 200 <= resp.status_code < 300:
            return True, "Restock webhook triggered successfully"

        # Try to extract helpful information from the response
        hint = None
        try:
            parsed = resp.json()
            # Many automation platforms (e.g. n8n) return a JSON with 'hint' or 'message'
            hint = parsed.get('hint') or parsed.get('message')
        except Exception:
            hint = None

        hint_text = hint if hint else resp.text

        # n8n-specific guidance for 404 webhooks in test/edit mode
        if resp.status_code == 404:
            guidance = (
                "Ensure the workflow with this webhook is 'Activated' in n8n, "
                "or click 'Execute workflow' in the editor to register the temporary webhook before calling it."
            )
            return False, f"Webhook error {resp.status_code}: {hint_text} — {guidance}"

        return False, f"Webhook error {resp.status_code}: {hint_text}"
    except Exception as e:
        return False, f"Error triggering webhook: {e}"

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # ========================================================================
    # SIDEBAR
    # ========================================================================
    with st.sidebar:
        st.title("📦 Retailer Portal")
        st.markdown("---")
        
        # Manual refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        # Auto-refresh checkbox
        auto_refresh_enabled = st.checkbox("⏰ Auto-refresh (30s)", value=False)
        
        st.markdown("---")
        st.caption("💡 Data updates in real-time from Google Sheets")
    
    # ========================================================================
    # AUTO-REFRESH LOGIC
    # ========================================================================
    if auto_refresh_enabled:
        # Auto-refresh every 30 seconds (30000 milliseconds)
        st_autorefresh(interval=30000, key="datarefresh")
    
    # ========================================================================
    # DATA LOADING
    # ========================================================================
    # Load data from Google Sheets via CSV export
    with st.spinner("Loading stock data from Google Sheets..."):
        df = load_data_from_gsheet()
    
    if df.empty:
        st.warning("⚠️ No data available. Please check your Google Sheets connection.")
        return
    
    # ========================================================================
    # CRITICAL ALERTS
    # ========================================================================
    critical_items = get_critical_items(df, threshold=10)
    
    if critical_items:
        st.error("🚨 **CRITICAL ALERT: Low Stock Items (≤10 units)**")
        
        # Add modal popup button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{len(critical_items)} item(s) at critical stock levels**")
        
        with col2:
            if st.button("📋 View All", key="view_critical_items", use_container_width=True):
                st.session_state.show_critical_modal = True
        
        # Modal popup for critical items
        if st.session_state.get("show_critical_modal", False):
            with st.container():
                st.markdown("---")
                st.subheader("🚨 Critical Stock Items")
                
                # Create dataframe from critical items
                critical_df = pd.DataFrame(critical_items)
                
                # Display in table format
                st.dataframe(
                    critical_df[['Product Name', 'SKU', 'Available Stock', 'Restock Level', 'Status']],
                    use_container_width=True,
                    hide_index=True
                )
                
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("❌ Close", key="close_critical_modal", use_container_width=True):
                        st.session_state.show_critical_modal = False
                        st.rerun()
                
                st.markdown("---")
    
    # ========================================================================
    # METRICS DASHBOARD
    # ========================================================================
    st.title("📊 Stock Monitoring Dashboard")
    
    # Calculate metrics
    total_products, low_stock_count, stock_value = calculate_metrics(df)
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🏷️ Total Products",
            value=total_products,
            delta=None
        )
    
    with col2:
        st.metric(
            label="⚠️ Low Stock Items",
            value=low_stock_count,
            delta=f"-{low_stock_count}" if low_stock_count > 0 else "All Good",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="📦 Total Stock Units",
            value=f"{stock_value:,}",
            delta=None
        )
    
    st.markdown("---")
    
    # ========================================================================
    # DETAILED DATA VIEW
    # ========================================================================
    st.subheader("📋 Detailed Inventory View")
    
    # Configure column display with progress bar for Available Stock
    column_config = {
        "Product Name": st.column_config.TextColumn("Product Name", width="medium"),
        "SKU": st.column_config.TextColumn("SKU", width="small"),
        "Available Stock": st.column_config.ProgressColumn(
            "Available Stock",
            help="Current stock level (synced with Shopify)",
            min_value=0,
            max_value=300,
            format="%d units"
        ),
        "Restock Level": st.column_config.NumberColumn(
            "Restock Level",
            help="Minimum stock threshold",
            format="%d units"
        ),
        "Status": st.column_config.TextColumn("Status", width="small")
    }
    
    # Apply highlighting to rows with low stock
    styled_df = df.style.apply(highlight_low_stock, axis=1)
    
    # Display the data with custom column configuration
    st.dataframe(
        styled_df,
        column_config=column_config,
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    st.markdown("---")
    
    # ========================================================================
    # LOW STOCK ITEMS (Below Restock Level)
    # ========================================================================
    low_stock_df = df[df['Available Stock'] < df['Restock Level']].copy()
    low_stock_items = low_stock_df.where(pd.notna(low_stock_df), None).to_dict('records')
    
    if low_stock_items:
        st.warning("⚠️ **LOW STOCK ITEMS** (Below Restock Level)")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{len(low_stock_items)} item(s) below restock level**")
        
        with col2:
            if st.button("📋 View All", key="view_low_stock_items", use_container_width=True):
                st.session_state.show_low_stock_modal = True
        
        # Modal popup for low stock items
        if st.session_state.get("show_low_stock_modal", False):
            with st.container():
                st.markdown("---")
                st.subheader("⚠️ Low Stock Items")
                
                # Create dataframe from low stock items
                low_stock_display_df = pd.DataFrame(low_stock_items)
                
                # Display in table format
                st.dataframe(
                    low_stock_display_df[['Product Name', 'SKU', 'Available Stock', 'Restock Level', 'Status']],
                    use_container_width=True,
                    hide_index=True
                )
                
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("❌ Close", key="close_low_stock_modal", use_container_width=True):
                        st.session_state.show_low_stock_modal = False
                        st.rerun()
                
                st.markdown("---")

# ============================================================================
# RUN APPLICATION
# ============================================================================
if __name__ == "__main__":
    main()
