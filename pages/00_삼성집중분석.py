import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(
    page_title="삼성전자 집중 분석",
    page_icon="🇰🇷",
    layout="wide"
)

st.title("🇰🇷 삼성전자 (005930.KS) 정밀 분석 대시보드")
st.markdown("""
당곡고등학교 학생 여러분 반갑습니다! 이 페이지는 **삼성전자**의 기술적 지표와 수급을 단독으로 깊이 있게 탐구하는 독립 페이지입니다.
메모리 반도체 경기 사이클과 거래량을 통해 시장의 흐름을 분석해 보세요.
""")

# 2. 사이드바 기간 설정
st.sidebar.header("📅 조회 기간 설정")
today = datetime.today()
one_year_ago = today - timedelta(days=365)
start_date = st.sidebar.date_input("시작일", one_year_ago)
end_date = st.sidebar.date_input("종료일", today)

if start_date >= end_date:
    st.sidebar.error("시작일은 종료일보다 이전이어야 합니다.")

# 3. 데이터 로드 (최신 yfinance 버그 완벽 대처 기법 적용)
@st.cache_data(ttl=1800)
def load_samsung_data(start, end):
    try:
        # multi_level_index=False 옵션으로 데이터 구조 단일화 (버그 해결)
        df = yf.download("005930.KS", start=start, end=end, multi_level_index=False)
        if df.empty:
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

df = load_samsung_data(start_date, end_date)

if not df.empty:
    # 4. 데이터 연산 (이동평균선 및 보조지표)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA120'] = df['Close'].rolling(window=120).mean()
    
    # 일일 수익률 계산
    df['Daily_Return'] = df['Close'].pct_change() * 100
    
    # RSI(상대강도지수) 계산 공식
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # 주요 지표 시각화 (Metric)
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
    price_diff = current_price - prev_price
    price_pct = (price_diff / prev_price) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="현재 주가", value=f"{int(current_price):,} 원", delta=f"{int(price_diff):,}원 ({price_pct:.2f}%)")
    with col2:
        max_price = df['High'].max()
        st.metric(label="기간 내 최고가", value=f"{int(max_price):,} 원")
    with col3:
        min_price = df['Low'].min()
        st.metric(label="기간 내 최저가", value=f"{int(min_price):,} 원")

    # 5. 메인 레이아웃 (주가 & 이평선 경기선 비교)
    st.subheader("📈 중장기 업황 사이클 분석 (20일선 vs 120일선)")
    st.markdown("""
    - **20일선(노란 점선)**: 한 달간의 단기 수급선입니다.
    - **120일선(빨간 선)**: 약 6개월간의 경기선으로, 반도체 수요 공급의 장기 추세를 뜻합니다. 주가가 120일선 위에 있으면 상승세, 아래에 있으면 침체기로 해석합니다.
    """)
    
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df.index, y=df['Close'], name="삼성전자 종가", line=dict(color="#1F4E79", width=2)))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="20일 단기선", line=dict(color="#FFC000", width=1.2, dash="dash")))
    fig_price.add_trace(go.Scatter(x=df.index, y=df['MA120'], name="120일 장기 경기선", line=dict(color="#EF4444", width=1.5)))
    fig_price.update_layout(template="plotly_white", hovermode="x unified", yaxis_title="주가 (원)")
    st.plotly_chart(fig_price, use_container_width=True)

    # 6. 보조지표 RSI & 거래량 시각화
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("⏱️ 과매수/과매도 판별 (RSI 14)")
        st.markdown("RSI가 **70 이상이면 과열(과매수)**로 매도를 고려하고, **30 이하이면 침체(과매도)**로 매수를 고려하는 통계 보조지표입니다.")
        
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color="#8B5CF6", width=1.5)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#EF4444", annotation_text="과열 (70)")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#3B82F6", annotation_text="침체 (30)")
        fig_rsi.update_layout(yaxis=dict(range=[0, 100]), template="plotly_white")
        st.plotly_chart(fig_rsi, use_container_width=True)
        
    with col_right:
        st.subheader("📊 거래량 및 일일 변동 분포")
        st.markdown("주가가 상승한 날과 하락한 날 거래량이 어떻게 달라지는지 분석하여 세력과 대중의 거래 유입도를 파악합니다.")
        
        df['Day_Type'] = np.where(df['Daily_Return'] > 0, '상승일', '하락일')
        fig_vol = px.bar(
            df, x=df.index, y="Volume",
            color="Day_Type",
            color_discrete_map={'상승일': '#10B981', '하락일': '#EF4444'},
            labels={"Volume": "거래량", "index": "날짜"},
            title="일별 거래량 추이 (상승/하락 구분)",
            template="plotly_white"
        )
        st.plotly_chart(fig_vol, use_container_width=True)

else:
    st.error("삼성전자 데이터를 가져오지 못했습니다. 야후 파이낸스 서버 상태를 확인하거나 조회 날짜를 조절해 보세요.")
