# 📦 Retailer Product Dashboard - Inventory Stock Monitor

A real-time inventory stock monitoring dashboard built with **Streamlit** that syncs data from Google Sheets and provides instant alerts for low stock items.

---

## 🎯 Problems This Solves

### 1. **Manual Stock Tracking**
- ❌ Manually checking spreadsheets for stock levels is time-consuming and error-prone
- ✅ **Automated real-time monitoring** from Google Sheets

### 2. **Delayed Alert Response**
- ❌ Stock shortages go unnoticed until a customer complains
- ✅ **Instant critical alerts** for items at or below 10 units

### 3. **Data Visibility Issues**
- ❌ Stock data scattered across different systems and formats
- ✅ **Centralized dashboard** with color-coded status indicators

### 4. **Restock Management**
- ❌ Difficult to identify which items need restocking
- ✅ **Clear categorization** of critical, low stock, and in-stock items with clickable popups

### 5. **Multi-Location Tracking**
- ❌ No easy way to see all inventory across retail locations
- ✅ **Unified view** of all products and stock levels in one place

---

## 🚀 How It Works

### System Architecture

```
┌─────────────────┐
│  Google Sheets  │
│  (Source Data)  │
└────────┬────────┘
         │ CSV Export
         ▼
┌─────────────────┐
│  Streamlit App  │
│ (main.py)       │
├─────────────────┤
│ • Data Loading  │
│ • Cleaning      │
│ • Status Logic  │
│ • Alerts        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dashboard UI   │
│ • Real-time     │
│ • Interactive   │
│ • Visual        │
└─────────────────┘
```

### Data Flow

1. **Data Source**: Google Sheets contains all inventory data (Product Name, SKU, Available Stock, Restock Level)

2. **Auto-Detection**: The app automatically detects and maps column names flexibly
   - Stock columns: `Available Stock`, `Stock`, `Qty`, `Quantity`, `Inventory`...
   - Restock columns: `Restock Level`, `Threshold`, `Min Stock`, `Reorder Point`...

3. **Data Processing**:
   - Removes empty rows
   - Normalizes column names
   - Converts values to proper numeric types
   - Adds `Status` categorization

4. **Status Calculation**:
   ```
   IF Stock ≤ 10 → 🔴 CRITICAL
   ELSE IF Stock < Restock Level → 🟡 LOW STOCK
   ELSE → 🟢 IN STOCK
   ```

5. **Dashboard Display**:
   - Metrics: Total Products, Low Stock Count, Total Units
   - Alerts: Critical items highlighted in red
   - Table: Full inventory with color-coded rows
   - Popups: Click "View All" to see detailed lists

---

## 🎨 Key Features

### 📊 Dashboard Metrics
- **Total Products**: Count of all inventory items
- **Low Stock Items**: Number of items below restock level
- **Total Stock Units**: Sum of all available stock

### 🚨 Alert System
| Alert Type | Condition | Color | Action |
|-----------|-----------|-------|--------|
| **Critical** | Stock ≤ 10 units | 🔴 Red | Click "View All" for popup |
| **Low Stock** | Stock < Restock Level | 🟡 Yellow | Expandable popup with details |
| **In Stock** | Stock ≥ Restock Level | 🟢 Green | No action needed |

### 📋 Interactive Features
- **Clickable Popups**: View all critical/low stock items in a detailed table
- **Auto-Refresh**: Optional 30-second auto-refresh for real-time updates
- **Manual Refresh**: One-click data refresh button
- **Progress Bars**: Visual stock level indicators
- **Sortable Table**: Full inventory with color-coded highlighting



## 🎯 Usage Guide

### Sidebar Controls
- 🔄 **Refresh Data** - Manually pull latest data from Google Sheets
- ⏰ **Auto-refresh (30s)** - Toggle automatic updates every 30 seconds

### Main Dashboard

**Step 1: View Metrics**
- See at a glance: total products, low stock count, total units

**Step 2: Check Alerts**
- 🚨 **Critical Alert** appears if any items are at ≤10 units
- Click **"📋 View All"** to see popup with all critical items

**Step 3: View Low Stock**
- ⚠️ **Low Stock** section shows items below restock level
- Click **"📋 View All"** to see details

**Step 4: Detailed Inventory**
- Scroll through the table to see all products
- 🔴 Red highlighted rows = stock below restock level
- Progress bars show stock levels visually

---

## 📊 Use Cases

✅ **Retail Operations** - Monitor stock across multiple stores  
✅ **E-commerce** - Track inventory in real-time  
✅ **Warehouse Management** - Identify items needing restock  
✅ **Supply Chain** - Automate reorder triggers  
✅ **Management Reporting** - Dashboard for stakeholders  


## 📝 Column Name Mapping

The app automatically detects these column variations:

**Stock/Inventory:**
- `Available Stock`, `Stock`, `Qty`, `Quantity`, `Inventory`, `Available`, `On Hand`

**Restock Level:**
- `Restock Level`, `Threshold`, `Min Stock`, `Reorder Point`, `Minimum`

**Product Name:**
- `Product Name`, `Name`, `Title`, `Item Name`

**SKU:**
- `SKU`, `ID`, `Item No`, `Item Number`, `Barcode`
---

## 📄 License

This project is provided as-is for inventory management purposes.

---

**Repository:** https://github.com/Arslan-Ali-11/Retailer_product_dashboard  
**Live:** http://35.172.150.199:8501/
**Last Updated:** December 8, 2025  
**Version:** 1.0.0


