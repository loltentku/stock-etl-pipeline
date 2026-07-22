import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine

st.set_page_config(page_title="Stock ETL Dashboard", layout="wide")

# connection string ไปยัง Postgres (รันจากเครื่อง Windows เลยใช้ localhost)
DB_CONNECTION = "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow"


@st.cache_data(ttl=300)  
def load_data():
    """ดึงข้อมูลจากตาราง mart_stock_indicators ที่ dbt คำนวณ SMA/RSI ไว้แล้ว"""
    engine = create_engine(DB_CONNECTION)
    query = "SELECT * FROM mart_stock_indicators ORDER BY ticker, date"
    return pd.read_sql(query, engine)


df = load_data()

st.title("📈 Stock ETL Pipeline Dashboard")
st.caption("Data pipeline: yfinance → Airflow → Postgres → dbt → Streamlit")

# ============================================================
# SIDEBAR: dropdown เลือกหุ้น
# ============================================================
st.sidebar.header("ตัวเลือก")
tickers = sorted(df["ticker"].unique())
selected_ticker = st.sidebar.selectbox("เลือกหุ้น", tickers)

ticker_df = df[df["ticker"] == selected_ticker].sort_values("date")

# ============================================================
# METRIC CARDS (แถวบนสุด 4 ช่อง)
# ============================================================
latest = ticker_df.iloc[-1]
prev = ticker_df.iloc[-2] if len(ticker_df) > 1 else latest

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Close Price",
    f"${latest['close_price']:.2f}",
    f"{latest['close_price'] - prev['close_price']:.2f}",
    help="ราคาปิดล่าสุดของหุ้น ตัวเลขเล็กใต้ราคาคือส่วนต่างจากวันก่อนหน้า (สีเขียว = ขึ้น, สีแดง = ลง)"
)

col2.metric(
    "SMA (5-day)",
    f"${latest['sma_5']:.2f}" if pd.notna(latest['sma_5']) else "N/A",
    help="ราคาเฉลี่ยย้อนหลัง 5 วัน (Simple Moving Average) ใช้ดูเทรนด์ระยะสั้นของหุ้น"
)

col3.metric(
    "RSI (14-day)",
    f"{latest['rsi_14']:.1f}" if pd.notna(latest['rsi_14']) else "N/A",
    help="ตัวเลข 0-100 บอกว่าหุ้นถูกซื้อ/ขายมากเกินไปหรือยัง คำนวณจากข้อมูล 14 วันย้อนหลัง"
)

col4.metric(
    "Volume",
    f"{int(latest['volume']):,}",
    help="จำนวนหุ้นที่ถูกซื้อขายในวันล่าสุด บอกว่าคนสนใจหุ้นนี้มากแค่ไหนในวันนั้น"
)

st.divider()

# ============================================================
# กราฟที่ 1: Price & SMA
# ============================================================
st.subheader(f"{selected_ticker} — ราคาหุ้น เทียบกับ ค่าเฉลี่ย SMA")

with st.expander("ℹ️ กราฟนี้บอกอะไร"):
    st.markdown("""
    - เส้น **Close Price** คือราคาปิดจริงรายวัน จะขึ้นๆ ลงๆ ตามตลาด
    - เส้น **SMA 5** คือราคาเฉลี่ยย้อนหลัง 5 วัน จะ smooth กว่า ไม่กระตุกเท่าราคาจริง
    - **วิธีอ่าน:** ถ้าราคาจริงอยู่ **เหนือ** เส้น SMA → เทรนด์ขาขึ้น ถ้าอยู่ **ใต้** เส้น SMA → เทรนด์ขาลง
    """)

fig_price = go.Figure()
fig_price.add_trace(go.Scatter(x=ticker_df["date"], y=ticker_df["close_price"], name="Close Price"))
fig_price.add_trace(go.Scatter(x=ticker_df["date"], y=ticker_df["sma_5"], name="SMA 5"))
fig_price.update_layout(height=400, xaxis_title="Date", yaxis_title="Price ($)")
st.plotly_chart(fig_price, use_container_width=True)

st.divider()

# ============================================================
# กราฟที่ 2: RSI
# ============================================================
st.subheader(f"{selected_ticker} — RSI (14-day)")

with st.expander("ℹ️ กราฟนี้บอกอะไร"):
    st.markdown("""
    - เส้นหลักคือค่า **RSI** ที่วิ่งอยู่ระหว่าง 0-100
    - เส้นประ **สีแดงที่ 70** = โซน **Overbought** (ซื้อกันเยอะเกินไป มีโอกาสราคาจะย่อ/ลง)
    - เส้นประ **สีเขียวที่ 30** = โซน **Oversold** (ขายกันเยอะเกินไป มีโอกาสราคาจะเด้งขึ้น)
    - **วิธีอ่าน:** ถ้าเส้น RSI แตะหรือเกิน 70 นักเทรดมักระวังเรื่องราคาปรับฐาน ถ้าแตะ 30 มักมองว่าเป็นจุดที่ราคาอาจกลับตัวขึ้น
    """)

fig_rsi = go.Figure()
fig_rsi.add_trace(go.Scatter(x=ticker_df["date"], y=ticker_df["rsi_14"], name="RSI"))
fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
fig_rsi.update_layout(height=300, xaxis_title="Date", yaxis_title="RSI")
st.plotly_chart(fig_rsi, use_container_width=True)

st.divider()

# ============================================================
# ตาราง Raw Data (ล่างสุด)
# ============================================================
st.subheader("ข้อมูลดิบทั้งหมด (ทุกหุ้น)")
st.caption("ตารางนี้โชว์ทุกหุ้นทุกวันที่มีในระบบ ไม่ผูกกับตัวเลือกใน sidebar ไว้เผื่ออยากเช็คตัวเลขละเอียดหรือ export ไปใช้ต่อ")
st.dataframe(df.sort_values(["ticker", "date"], ascending=[True, False]), use_container_width=True)