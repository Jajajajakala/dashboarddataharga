import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ta.momentum 
from plotly.subplots import make_subplots
from datetime import timedelta

# Inisialisasi koneksi ke MetaTrader 5
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    mt5.shutdown()
else:
    print("Connected to MT5!")


# Ambil data harga
# symbol = "XAUUSD"
# rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 10)

option = st.sidebar.selectbox(
    "ticks",
    ("XAUUSD", "GBPUSD", "EURUSD", "USDJPY", "MSFT", "NVDA", "IBM", "TSLA"),
)

options2 = ["H1", "H4", "D1"]
selection = st.sidebar.pills("Timeframe", options2, selection_mode="single")

if selection == "H1":
    bb = mt5.TIMEFRAME_H1
elif selection == "H4":
    bb = mt5.TIMEFRAME_H4
else:
    bb = mt5.TIMEFRAME_D1


current_date = datetime.now()
print(current_date)
rates = mt5.copy_rates_from(option, bb, current_date, 50000)

if rates is not None:
    import pandas as pd
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    print(df)
else:
    print("Gagal ambil data")
# Jika Anda mengimpor: from datetime import datetime
# min_date = datetime(2023, 10, 26).date() # Ini akan mengambil bagian tanggal dari objek datetime
# max_date = datetime(2024, 12, 26).date()

df['time'] = pd.to_datetime(df['time'])
min_datee = df['time'].min()
max_datee = df['time'].max()

min_date = st.sidebar.date_input("tanggal awal", value = min_datee, min_value = min_datee, max_value = max_datee)
max_date = st.sidebar.date_input("tanggal akhir", value = max_datee, min_value = min_datee, max_value = max_datee)

options3 = [ "None", "Last 7 days", "Last 30 days", "Last 1 year"]
selection2 = st.sidebar.radio("Insight options", options3)

if selection2 == "Last 7 days":
    start_date = datetime.now() - timedelta(8)
elif selection2 == "Last 30 days":
    start_date = datetime.now() - timedelta(31)
elif selection2 == "Last 1 year":
    start_date = datetime.now() - timedelta(365)
else:
    start_date = min_date


# df = df[(df['Tanggal']>=pd.to_datetime(min_date)) & (df['Tanggal']<=pd.to_datetime(max_date))]
max_date_with_time = pd.to_datetime(max_date) + timedelta(days=1) - timedelta(seconds=1)



# Filter df agar sampai akhir hari max_date
df = df[(df['time'] >= pd.to_datetime(start_date)) & (df['time'] <= max_date_with_time)]

st.title("Dashboard Data Harga")

st.dataframe(df)


print(df)
harga_close_terakhir = df['close'].iloc[-1]
close_awal = df['close'].iloc[0]
harga_perbedaan_close = harga_close_terakhir-close_awal
close_tertinggi = df['close'].max()
close_terendah = df['close'].min()


col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Close", f"${harga_close_terakhir:.2f}")
col2.metric("Price Diff", f"${harga_perbedaan_close:.2f}", f"{harga_perbedaan_close/close_awal*100:.2f}%")
col3.metric("close tertinggi", f"${close_tertinggi}")
col4.metric("Lowest Close", f"${close_terendah}")

df['moving10'] = df['close'].rolling(10).mean()
df['moving21'] = df['close'].rolling(21).mean()

df['cross'] = df['moving10'] - df['moving21']
df['prev_cross'] = df['cross'].shift(1)

golden_crosses = df[(df['cross'] > 0) & (df['prev_cross'] < 0)]
death_crosses = df[(df['cross'] < 0) & (df['prev_cross'] > 0)]

fig = go.Figure(data=[go.Candlestick(x=df['time'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'], 
                increasing_line_color = 'forestgreen', 
                decreasing_line_color = 'tomato'),
                go.Scatter(x=df['time'], y=df['moving10'], line=dict(color='orange', width=0.5)),
                go.Scatter(x=df['time'], y=df['moving21'], line=dict(color='brown', width=0.5))]
                )

fig.add_trace(go.Scatter(
    x=golden_crosses['time'],
    y=golden_crosses['close'],
    mode='markers',
    marker=dict(color='green', size=8, symbol='triangle-up'),
    name='Golden Cross'
))

fig.add_trace(go.Scatter(
    x=death_crosses['time'],
    y=death_crosses['close'],
    mode='markers',
    marker=dict(color='red', size=8, symbol='triangle-down'),
    name='Death Cross'
))

                     

fig.update_layout(xaxis_rangeslider_visible=True, height = 700)

st.plotly_chart(fig)

# RSI
df["RSI"] = ta.momentum.rsi(df["close"], window=14, fillna=False)

# Construct a 2 x 1 Plotly figure
fig2 = make_subplots(rows=2, cols=1, vertical_spacing=0.01, shared_xaxes=True)
# fig2 = go.Figure()

# Plot RSI
fig2.add_trace(go.Scatter(x=df['time'], y=df['RSI'], name='RSI'),
              row=1, col=1)

fig2.add_hline(y=30, line_dash='dash', line_color='limegreen', line_width=1)
fig2.add_hline(y=70, line_dash='dash', line_color='red', line_width=1)
fig2.update_yaxes(title_text='RSI Score')
fig2.update_layout(height = 600)

st.plotly_chart(fig2)

# ========= Insight MA & Crossover ============
ma10_terakhir = df['moving10'].iloc[-1]
ma21_terakhir = df['moving21'].iloc[-1]
harga_terakhir = df['close'].iloc[-1]

# Insight posisi harga terhadap MA10
if harga_terakhir > ma10_terakhir:
    insight_ma = f"📈 Harga saat ini (${harga_terakhir:.2f}) berada **di atas MA10 (${ma10_terakhir:.2f})**, menandakan potensi **tren naik jangka pendek**.\n\n"
else:
    insight_ma = f"📉 Harga saat ini (${harga_terakhir:.2f}) berada **di bawah MA10 (${ma10_terakhir:.2f})**, menandakan potensi **pelemahan harga jangka pendek**.\n\n"

# Insight perbandingan MA10 dan MA21
if ma10_terakhir > ma21_terakhir:
    insight_crossover = f"🟢 MA10 (${ma10_terakhir:.2f}) > MA21 (${ma21_terakhir:.2f}): **tren naik jangka menengah**.\n\n"
elif ma10_terakhir < ma21_terakhir:
    insight_crossover = f"🔴 MA10 (${ma10_terakhir:.2f}) < MA21 (${ma21_terakhir:.2f}): **tren turun jangka menengah**.\n\n"
else:
    insight_crossover = f"➖ MA10 dan MA21 saat ini hampir sama, belum ada tren dominan.\n\n"

# Deteksi Golden/Death Cross terbaru (dari 2 data terakhir)
ma10_sebelum = df['moving10'].iloc[-2]
ma21_sebelum = df['moving21'].iloc[-2]

if ma10_sebelum < ma21_sebelum and ma10_terakhir > ma21_terakhir:
    crossover_event = "🟢 **Golden Cross terdeteksi** (MA10 memotong ke atas MA21), sinyal **bullish** potensial.\n\n"
elif ma10_sebelum > ma21_sebelum and ma10_terakhir < ma21_terakhir:
    crossover_event = "🔴 **Death Cross terdeteksi** (MA10 memotong ke bawah MA21), sinyal **bearish** potensial.\n\n"
else:
    crossover_event = ""

# ========= Insight RSI ============
rsi_terakhir = df['RSI'].iloc[-1]

if rsi_terakhir > 70:
    insight_rsi = f"⚠️ RSI saat ini adalah **{rsi_terakhir:.2f}**, berada di atas 70. Potensi **overbought**, kemungkinan koreksi harga.\n\n"
elif rsi_terakhir < 30:
    insight_rsi = f"🟢 RSI saat ini adalah **{rsi_terakhir:.2f}**, di bawah 30. Potensi **oversold**, kemungkinan rebound harga.\n\n"
else:
    insight_rsi = f"🔍 RSI saat ini adalah **{rsi_terakhir:.2f}**, dalam zona netral.\n\n"

# Gabungkan semua insight
st.subheader("📊 Insight Otomatis")
st.markdown(insight_ma + insight_crossover + crossover_event + insight_rsi)

# Tambahkan informasi apakah crossover pernah muncul dalam rentang waktu
if golden_crosses.empty and death_crosses.empty:
    st.info("📌 Tidak ada Golden Cross maupun Death Cross yang terdeteksi **selama rentang waktu yang dipilih**.")
else:
    st.success(f"📌 Terdeteksi {len(golden_crosses)} Golden Cross dan {len(death_crosses)} Death Cross **dalam rentang waktu ini**.")
