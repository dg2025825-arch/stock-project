import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="테슬라 정밀 분석",
    page_icon="🇺🇸",
    layout="wide"
)

st.title("⚡ 테슬라 (Tesla Inc., TSLA) 초고변동성 및 모멘텀 정밀 분석")
st.markdown("""
당곡고등학교 학생 여러분 반갑습니다! 본 대시보드는 글로벌 서학개미들의 가장 뜨거운 관심을 받는 **테슬라(TSLA)**의 데이터를 심층 분석합니다.
테슬라 특유의 **극단적인 변동성**, **볼린저 밴드를 활용한 가격 채널**, 그리고 **나스닥 지수와의 상대 성과**를 탐구하며 통계학과 행동재무학의 이론을 현실 데이터에 적용해 보세요.
""")

# 2. 사이드바 기간 설정
st.sidebar.header("📅 분석 기간 및 변수 설정")
today = datetime.today()
one_year_ago = today - timedelta(days=365)
start_date = st.sidebar.date_input("분석 시작일", one_year_ago)
end_date = st.sidebar.date_input("분석 종료일", today)

if start_date >= end_date:
    st.sidebar.error("오류: 시작일은 종료일보다 이전이어야 합니다.")

# 3. 데이터 로드 함수 (yfinance 버그 완벽 대처 방식)
@st.cache_data(ttl=1800)
def load_tesla_complex_data(start, end):
    try:
        # 안전하게 종목별로 개별 다운로드하여 딕셔너리로 취합
        tesla = yf.download("TSLA", start=start, end=end, multi_level_index=False)
        nasdaq = yf.download("^IXIC", start=start, end=end, multi_level_index=False)
        return tesla, nasdaq
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 데이터 로딩 실행
df_tsla, df_ndx = load_tesla_complex_data(start_date, end_date)

if not df_tsla.empty and not df_ndx.empty:
    # 4. 실시간 주요 지표 카드
    current_price = df_tsla['Close'].iloc[-1]
    prev_price = df_tsla['Close'].iloc[-2] if len(df_tsla) > 1 else current_price
    price_diff = current_price - prev_price
    price_pct = (price_diff / prev_price) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="테슬라 현재가", value=f"$ {current_price:.2f}", delta=f"${price_diff:.2f} ({price_pct:.2f}%)")
    with col2:
        max_price = df_tsla['High'].max()
        st.metric(label="기간 내 최고가 (장중)", value=f"$ {max_price:.2f}")
    with col3:
        min_price = df_tsla['Low'].min()
        st.metric(label="기간 내 최저가 (장중)", value=f"$ {min_price:.2f}")

    # 탭 구성 (다양한 학술적 비교 요소 탑재)
    tab1, tab2, tab3 = st.tabs([
        "📈 주가 채널 분석 (볼린저 밴드)", 
        "🌀 변동성 통계 & 극단적 하루 (Extreme Days)", 
        "⚖️ 나스닥 대비 성과 및 최대 낙폭 (MDD)"
    ])

    # ----------------------------------------------------
    # Tab 1: 주가 채널 분석 (볼린저 밴드)
    # ----------------------------------------------------
    with tab1:
        st.subheader("📊 볼린저 밴드 (Bollinger Bands) 분석")
        st.markdown("""
        **볼린저 밴드**는 이동평균선(중심선)을 기준으로 주가의 변동성(표준편차)을 더하고 뺀 가격 채널입니다.
        - **상단 밴드**: 중간선 + (2 * 20일 표준편차) $\\rightarrow$ 통계적으로 주가가 매우 상승하여 **과열된 상태**로 해석
        - **하단 밴드**: 중간선 - (2 * 20일 표준편차) $\\rightarrow$ 통계적으로 주가가 매우 하락하여 **과매도된 상태**로 해석
        - 통계학적 원리에 따라 주가는 **약 95.4%의 확률로 이 밴드 안에서 움직입니다.** 밴드를 찢고 돌파할 때의 가격 모멘텀을 관찰해 보세요.
        """)
        
        # 볼린저 밴드 계산
        df_tsla['MA20'] = df_tsla['Close'].rolling(window=20).mean()
        df_tsla['Std20'] = df_tsla['Close'].rolling(window=20).std()
        df_tsla['Upper'] = df_tsla['MA20'] + (2 * df_tsla['Std20'])
        df_tsla['Lower'] = df_tsla['MA20'] - (2 * df_tsla['Std20'])
        
        fig_bb = go.Figure()
        # 하단 밴드와 상단 밴드 사이 영역을 채우기 위해 밴드 먼저 그림
        fig_bb.add_trace(go.Scatter(x=df_tsla.index, y=df_tsla['Upper'], name="상단 밴드 (과열선)", line=dict(color="rgba(239, 68, 68, 0.3)", width=1)))
        fig_bb.add_trace(go.Scatter(x=df_tsla.index, y=df_tsla['Lower'], name="하단 밴드 (침체선)", line=dict(color="rgba(59, 130, 246, 0.3)", width=1), fill='tonexty', fillcolor='rgba(241, 245, 249, 0.4)'))
        
        # 중심선과 종가 추가
        fig_bb.add_trace(go.Scatter(x=df_tsla.index, y=df_tsla['Close'], name="테슬라 종가", line=dict(color="#CC0000", width=2)))
        fig_bb.add_trace(go.Scatter(x=df_tsla.index, y=df_tsla['MA20'], name="20일 중심선", line=dict(color="#475569", width=1.2, dash="dash")))
        
        fig_bb.update_layout(template="plotly_white", hovermode="x unified", yaxis_title="주가 ($)")
        st.plotly_chart(fig_bb, use_container_width=True)

    # ----------------------------------------------------
    # Tab 2: 변동성 통계 & 극단적 하루 (Extreme Days)
    # ----------------------------------------------------
    with tab2:
        st.subheader("🌀 변동성 군집성(Clustering)과 수익률 통계")
        st.markdown("""
        금융시장의 중요한 특징 중 하나인 **변동성 군집 현상**은 변동성이 큰 시기(뉴스나 실적 발표 전후)에는 큰 변동성이 뭉쳐서 나타나고, 
        평온한 시기에는 변동성이 계속 작게 유지되는 현상입니다. 테슬라의 연율화 변동성을 통해 이를 분석합니다.
        """)
        
        df_tsla['Daily_Return'] = df_tsla['Close'].pct_change() * 100
        # 20일 기준 움직임으로 구한 연율화 변동성: 일일수익률 표준편차 * sqrt(252영업일)
        df_tsla['Rolling_Vol'] = df_tsla['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
        
        fig_rolling_vol = px.line(
            df_tsla, x=df_tsla.index, y="Rolling_Vol",
            labels={"Rolling_Vol": "연율화 변동성 (%)", "index": "날짜"},
            title="테슬라의 20일 이동 연율화 변동성 추이 (위험도 시계열 흐름)",
            template="plotly_white",
            color_discrete_sequence=["#CC0000"]
        )
        st.plotly_chart(fig_rolling_vol, use_container_width=True)
        
        st.markdown("---")
        st.subheader("💥 선택 기간 내 최고/최악의 순간 Top 5")
        st.markdown("테슬라는 CEO 일론 머스크의 트윗, 자율주행(FSD) 발표, 분기 인도량 수치 등에 따라 하루에 10% 이상 급등락하는 경우가 잦습니다.")
        
        df_clean = df_tsla.dropna()
        best_days = df_clean.nlargest(5, 'Daily_Return')[['Close', 'Daily_Return']]
        worst_days = df_clean.nsmallest(5, 'Daily_Return')[['Close', 'Daily_Return']]
        
        col_day1, col_day2 = st.columns(2)
        with col_day1:
            st.success("🟢 **일일 주가 급등 Top 5**")
            st.dataframe(best_days.style.format({"Close": "${:.2f}", "Daily_Return": "+{:.2f}%"}))
        with col_day2:
            st.error("🔴 **일일 주가 급락 Top 5**")
            st.dataframe(worst_days.style.format({"Close": "${:.2f}", "Daily_Return": "{:.2f}%"}))

    # ----------------------------------------------------
    # Tab 3: 나스닥 대비 성과 및 최대 낙폭 (MDD)
    # ----------------------------------------------------
    with tab3:
        st.subheader("⚖️ 나스닥(NASDAQ) 지수 대비 상대 성과 및 위험 분석")
        st.markdown("""
        테슬라는 기술주 중심의 **나스닥 100 지수**의 핵심 구성 종목입니다. 
        나스닥 전체 시장 평균과 비교했을 때 테슬라가 거둔 **초과 수익률(Alpha)**과, 하락장일 때 얼마나 깊은 고통을 주는지 **최대 낙폭(MDD)**을 비교합니다.
        """)
        
        # 1. 누적 수익률 비교
        cum_tsla = (df_tsla['Close'] / df_tsla['Close'].iloc[0] - 1) * 100
        cum_ndx = (df_ndx['Close'] / df_ndx['Close'].iloc[0] - 1) * 100
        
        df_cum_compare = pd.DataFrame({
            '테슬라 (TSLA)': cum_tsla,
            '나스닥 지수 (NASDAQ)': cum_ndx
        }).ffill().bfill()
        
        fig_cum = px.line(
            df_cum_compare,
            labels={"value": "누적 수익률 (%)", "index": "날짜", "variable": "자산"},
            title="동일 시작일 기준 누적 수익률 (%) 비교",
            template="plotly_white",
            color_discrete_map={'테슬라 (TSLA)': '#CC0000', '나스닥 지수 (NASDAQ)': '#1F77B4'}
        )
        fig_cum.update_layout(hovermode="x unified")
        st.plotly_chart(fig_cum, use_container_width=True)
        
        # 2. 최대 낙폭 (MDD) 비교
        roll_max_tsla = df_tsla['Close'].cummax()
        mdd_tsla = (df_tsla['Close'] - roll_max_tsla) / roll_max_tsla * 100
        
        roll_max_ndx = df_ndx['Close'].cummax()
        mdd_ndx = (df_ndx['Close'] - roll_max_ndx) / roll_max_ndx * 100
        
        df_mdd_compare = pd.DataFrame({
            '테슬라 MDD': mdd_tsla,
            '나스닥 MDD': mdd_ndx
        }).ffill().bfill()
        
        st.subheader("📉 고점 대비 낙폭(Drawdown) 및 MDD 비교")
        st.markdown("""
        테슬라의 최대 낙폭선(빨간색)이 나스닥 지수의 낙폭선(파란색)보다 훨씬 깊게 내려앉는 경향을 볼 수 있습니다. 
        이는 테슬라 투자자가 높은 기대 수익률을 얻기 위해 **얼마나 거대한 심리적 하락 고통(MDD)**을 견뎌야 하는지 통계적으로 증명합니다.
        """)
        
        fig_mdd = px.area(
            df_mdd_compare,
            labels={"value": "고점 대비 낙폭 (%)", "index": "날짜", "variable": "구분"},
            title="테슬라 vs 나스닥 고점 대비 하락 흐름 시계열",
            template="plotly_white",
            color_discrete_map={'테슬라 MDD': 'rgba(204, 0, 0, 0.5)', '나스닥 MDD': 'rgba(31, 119, 180, 0.5)'}
        )
        st.plotly_chart(fig_mdd, use_container_width=True)

else:
    st.error("데이터 로드에 실패했습니다. Ticker나 네트워크 상태를 점검해 주세요.")
