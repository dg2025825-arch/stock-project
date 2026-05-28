import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="애플 정밀 분석",
    page_icon="🇺🇸",
    layout="wide"
)

st.title("🍏 애플 (Apple Inc., AAPL) 추세 및 모멘텀 정밀 분석")
st.markdown("""
당곡고등학교 학생 여러분 반갑습니다! 본 대시보드는 전 세계 우량주를 대표하는 **애플(AAPL)**의 데이터를 정밀 분석합니다.
애플의 강력한 **장단기 지수이동평균(EMA)** 흐름, 수학적 원리가 결합된 **MACD 지표**, 그리고 신제품 출시 주기와 관련된 **월별 계절성(Seasonality)**을 탐구해 보세요.
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
def load_apple_complex_data(start, end):
    try:
        # 안전하게 종목별로 개별 다운로드하여 딕셔너리로 취합
        apple = yf.download("AAPL", start=start, end=end, multi_level_index=False)
        spy = yf.download("SPY", start=start, end=end, multi_level_index=False)  # S&P 500 ETF
        return apple, spy
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 데이터 로딩 실행
df_aapl, df_spy = load_apple_complex_data(start_date, end_date)

if not df_aapl.empty and not df_spy.empty:
    # 4. 실시간 주요 지표 카드
    current_price = df_aapl['Close'].iloc[-1]
    prev_price = df_aapl['Close'].iloc[-2] if len(df_aapl) > 1 else current_price
    price_diff = current_price - prev_price
    price_pct = (price_diff / prev_price) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="애플 현재가", value=f"$ {current_price:.2f}", delta=f"${price_diff:.2f} ({price_pct:.2f}%)")
    with col2:
        max_price = df_aapl['High'].max()
        st.metric(label="기간 내 최고가 (장중)", value=f"$ {max_price:.2f}")
    with col3:
        min_price = df_aapl['Low'].min()
        st.metric(label="기간 내 최저가 (장중)", value=f"$ {min_price:.2f}")

    # 탭 구성 (수학적, 경제학적 깊이를 더한 탭)
    tab1, tab2, tab3 = st.tabs([
        "📈 장단기 EMA 추세 (골든/데드크로스)", 
        "📊 MACD 보조지표 (수학적 수렴과 확산)", 
        "📅 월별 계절성 및 시장 대비 방어력"
    ])

    # ----------------------------------------------------
    # Tab 1: 장단기 EMA 추세 (골든/데드크로스)
    # ----------------------------------------------------
    with tab1:
        st.subheader("📊 지수이동평균선(EMA) 돌파 분석")
        st.markdown("""
        **지수이동평균선(EMA)**은 단순이동평균(SMA)보다 **최근 주가에 가중치를 더 많이 부여**하여 계산하는 방식입니다. 따라서 주가의 추세 변화를 훨씬 더 민감하고 빠르게 포착합니다.
        - **골든크로스**: 50일 단기 EMA(녹색선)가 200일 장기 EMA(빨간선)를 골든크로스(상향돌파)할 때 $\\rightarrow$ 강력한 매수 신호 및 장기 상승 추세 진입
        - **데드크로스**: 50일 단기 EMA가 200일 장기 EMA를 데드크로스(하향이탈)할 때 $\\rightarrow$ 매도 신호 및 추세 하락 진입
        """)
        
        # EMA 계산
        df_aapl['EMA50'] = df_aapl['Close'].ewm(span=50, adjust=False).mean()
        df_aapl['EMA200'] = df_aapl['Close'].ewm(span=200, adjust=False).mean()
        
        fig_ema = go.Figure()
        fig_ema.add_trace(go.Scatter(x=df_aapl.index, y=df_aapl['Close'], name="Apple 종가", line=dict(color="#1C1C1E", width=2)))
        fig_ema.add_trace(go.Scatter(x=df_aapl.index, y=df_aapl['EMA50'], name="50일 지수평균선 (단기)", line=dict(color="#10B981", width=1.5)))
        fig_ema.add_trace(go.Scatter(x=df_aapl.index, y=df_aapl['EMA200'], name="200일 지수평균선 (장기)", line=dict(color="#EF4444", width=1.5)))
        
        fig_ema.update_layout(template="plotly_white", hovermode="x unified", yaxis_title="주가 ($)")
        st.plotly_chart(fig_ema, use_container_width=True)

    # ----------------------------------------------------
    # Tab 2: MACD 보조지표 (수학적 수렴과 확산)
    # ----------------------------------------------------
    with tab2:
        st.subheader("📐 MACD (Moving Average Convergence Divergence) 수리 분석")
        st.markdown("""
        **MACD**는 제럴드 어펠(Gerald Appel)이 개발한 지표로, 단기 지수이동평균과 장기 지수이동평균의 **차이(거리)**를 이용해 추세의 강도를 계산하는 매우 수학적인 도구입니다.
        - **MACD 선**: $EMA(Close, 12) - EMA(Close, 26)$ $\\rightarrow$ 두 이동평균선의 거리
        - **시그널 선**: MACD 선의 9일 지수이동평균선
        - **오실레이터(히스토그램)**: $MACD\\,선 - 시그널\\,선$ $\\rightarrow$ 두 선의 간격이 벌어지는지(확산), 좁아지는지(수렴) 시각화한 막대그래프
        """)
        
        # MACD 수식 구현
        ema12 = df_aapl['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df_aapl['Close'].ewm(span=26, adjust=False).mean()
        df_aapl['MACD'] = ema12 - ema26
        df_aapl['Signal'] = df_aapl['MACD'].ewm(span=9, adjust=False).mean()
        df_aapl['Hist'] = df_aapl['MACD'] - df_aapl['Signal']
        
        # MACD 그래프 그리기
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df_aapl.index, y=df_aapl['MACD'], name="MACD 선", line=dict(color="#2563EB", width=1.5)))
        fig_macd.add_trace(go.Scatter(x=df_aapl.index, y=df_aapl['Signal'], name="시그널 선", line=dict(color="#F59E0B", width=1.5, dash="dash")))
        
        # 히스토그램 추가 (양수는 초록색, 음수는 빨간색)
        hist_colors = np.where(df_aapl['Hist'] >= 0, '#10B981', '#EF4444')
        fig_macd.add_trace(go.Bar(x=df_aapl.index, y=df_aapl['Hist'], name="오실레이터", marker_color=hist_colors))
        
        fig_macd.update_layout(template="plotly_white", hovermode="x unified", title="애플 MACD 지표 시각화")
        st.plotly_chart(fig_macd, use_container_width=True)

    # ----------------------------------------------------
    # Tab 3: 월별 계절성 및 시장 대비 방어력
    # ----------------------------------------------------
    with tab3:
        st.subheader("📅 애플의 월별 수익률 계절성 (Seasonality) 패턴")
        st.markdown("""
        소비재 성격이 강한 테크 기업인 애플은 매년 가을(주로 9월) 신형 아이폰을 발표합니다. 
        이러한 기업 비즈니스 모델의 이벤트 주기가 **실제 주식 시장의 월별 평균 수익률**에 통계적인 영향을 미치는지 직접 탐구해 보세요.
        """)
        
        df_aapl['Daily_Return'] = df_aapl['Close'].pct_change() * 100
        df_aapl['Month'] = df_aapl.index.strftime('%m - %b')
        monthly_avg = df_aapl.groupby('Month')['Daily_Return'].mean() * 100
        
        fig_season = px.bar(
            x=monthly_avg.index,
            y=monthly_avg.values,
            labels={"x": "월 (Month)", "y": "평균 수익률 (%)"},
            title="조회 기간 내 애플의 월별 평균 수익률 (%)",
            color=monthly_avg.values,
            color_continuous_scale="RdYlGn",  # 초록(상승) ~ 빨강(하락)
            template="plotly_white"
        )
        st.plotly_chart(fig_season, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🛡️ 시장 평균(S&P 500) 대비 애플의 변동성 비교 (방어력 검증)")
        st.markdown("""
        애플은 하락장에서도 강력한 현금 흐름과 자사주 매입으로 인해 S&P 500 시장 지수 대비 굳건한 방어력을 보여준다는 평가를 받습니다. 
        두 자산의 **고점 대비 하락폭(Drawdown)**을 겹쳐 보며 애플이 '안전자산' 역할을 하는지 확인해 보세요.
        """)
        
        roll_max_aapl = df_aapl['Close'].cummax()
        dd_aapl = (df_aapl['Close'] - roll_max_aapl) / roll_max_aapl * 100
        
        roll_max_spy = df_spy['Close'].cummax()
        dd_spy = (df_spy['Close'] - roll_max_spy) / roll_max_spy * 100
        
        df_dd_compare = pd.DataFrame({
            '애플 (AAPL)': dd_aapl,
            'S&P 500 (SPY)': dd_spy
        }).ffill().bfill()
        
        fig_dd_spy = px.line(
            df_dd_compare,
            labels={"value": "고점 대비 낙폭 (%)", "index": "날짜", "variable": "자산"},
            title="애플 vs S&P 500 시장 지수 낙폭 비교",
            template="plotly_white",
            color_discrete_map={'애플 (AAPL)': '#1C1C1E', 'S&P 500 (SPY)': '#3B82F6'}
        )
        st.plotly_chart(fig_dd_spy, use_container_width=True)

else:
    st.error("데이터 로드에 실패했습니다. Ticker나 네트워크 상태를 점검해 주세요.")
