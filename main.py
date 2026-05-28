import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인 테마
st.set_page_config(
    page_title="글로벌 주식 다각도 비교 분석기",
    page_icon="📈",
    layout="wide"
)

# 커스텀 CSS로 좀 더 모던한 UI 구현
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 글로벌 주식 다각도 비교 분석 플랫폼</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">당곡고등학교 학생들을 위한 한국·미국 주요 주식 데이터 수집 및 고급 포트폴리오 통계 분석기입니다.</div>', unsafe_allow_html=True)

# 2. 데이터베이스 구성 (각각 10개 종목)
KR_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "POSCO홀딩스": "005490.KS",
    "NAVER": "035420.KS"
}

US_STOCKS = {
    "애플 (Apple)": "AAPL",
    "마이크로소프트 (Microsoft)": "MSFT",
    "엔비디아 (NVIDIA)": "NVDA",
    "알파벳 (Google)": "GOOGL",
    "아마존 (Amazon)": "AMZN",
    "메타 (Meta)": "META",
    "테슬라 (Tesla)": "TSLA",
    "버크셔 해서웨이 (Berkshire)": "BRK-B",
    "일라이 릴리 (Eli Lilly)": "LLY",
    "JP모건 체이스 (JPMorgan)": "JPM"
}

# 역방향 매핑 사전 (티커 -> 이름)
TICKER_TO_NAME = {**{v: k for k, v in KR_STOCKS.items()}, **{v: k for k, v in US_STOCKS.items()}}

# 3. 사이드바 구성 (설정 및 데이터 입력)
st.sidebar.header("⚙️ 분석 설정 및 자산 선택")

# 기간 설정
today = datetime.today()
one_year_ago = today - timedelta(days=365)
start_date = st.sidebar.date_input("시작일", one_year_ago)
end_date = st.sidebar.date_input("종료일", today)

if start_date >= end_date:
    st.sidebar.error("오류: 시작일은 종료일보다 이전이어야 합니다.")

# 한국 주식 다중 선택
selected_kr = st.sidebar.multiselect(
    "🇰🇷 한국 주요 주식 선택 (최대 10개)",
    options=list(KR_STOCKS.keys()),
    default=["삼성전자", "SK하이닉스", "현대차"]
)

# 미국 주식 다중 선택
selected_us = st.sidebar.multiselect(
    "🇺🇸 미국 주요 주식 선택 (최대 10개)",
    options=list(US_STOCKS.keys()),
    default=["애플 (Apple)", "엔비디아 (NVIDIA)", "테슬라 (Tesla)"]
)

# 추가 사용자 정의 티커
custom_input = st.sidebar.text_input("➕ 추가할 티커 직접 입력 (쉼표 구분)", placeholder="예: TSMC의 TSM, 카카오의 035720.KS")

# 분석용 무위험 수익률 (샤프 지수 계산용)
rf_rate = st.sidebar.number_input("💵 무위험 수익률 설정 (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)

# 선택된 모든 티커 취합
tickers_kr = [KR_STOCKS[name] for name in selected_kr]
tickers_us = [US_STOCKS[name] for name in selected_us]

tickers_custom = []
if custom_input:
    tickers_custom = [t.strip().upper() for t in custom_input.split(",") if t.strip()]

all_selected_tickers = tickers_kr + tickers_us + tickers_custom

# 4. 데이터 로드 함수
@st.cache_data(ttl=3600)
def fetch_stock_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame(), pd.DataFrame()
    try:
        # 야후 파이낸스 일괄 다운로드
        data = yf.download(tickers, start=start, end=end)
        
        # 다운로드된 데이터에서 'Close'(종가) 및 'Volume'(거래량) 추출
        if len(tickers) == 1:
            df_close = pd.DataFrame({tickers[0]: data['Close']})
            df_volume = pd.DataFrame({tickers[0]: data['Volume']})
        else:
            df_close = data['Close']
            df_volume = data['Volume']
            
        return df_close, df_volume
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 데이터 로딩 실행
if all_selected_tickers:
    with st.spinner("⏳ 실시간 시장 데이터를 불러오고 분석 통계치를 계산 중입니다..."):
        df_prices, df_volumes = fetch_stock_data(all_selected_tickers, start_date, end_date)
        
    if not df_prices.empty:
        # 결측값 정제 (시장 휴장일 차이 보정)
        df_prices = df_prices.ffill().bfill()
        df_volumes = df_volumes.ffill().bfill()
        
        # 5. 핵심 재무 통계 지표 계산
        df_returns = df_prices.pct_change().dropna()
        df_cum_returns = (df_prices / df_prices.iloc[0] - 1) * 100
        
        stats_summary = []
        for ticker in df_prices.columns:
            cum_ret = df_cum_returns[ticker].iloc[-1]
            daily_std = df_returns[ticker].std() if ticker in df_returns.columns else 0
            annual_vol = daily_std * np.sqrt(252) * 100
            
            # MDD (최대 낙폭)
            roll_max = df_prices[ticker].cummax()
            drawdowns = (df_prices[ticker] - roll_max) / roll_max * 100
            mdd = drawdowns.min()
            
            # CAGR (연환산 수익률)
            days_held = (df_prices.index[-1] - df_prices.index[0]).days
            if days_held > 0:
                annual_ret = (((df_prices[ticker].iloc[-1] / df_prices[ticker].iloc[0])) ** (365 / days_held) - 1) * 100
            else:
                annual_ret = 0
            
            # 샤프 지수
            excess_return = annual_ret - rf_rate
            sharpe_ratio = excess_return / annual_vol if annual_vol > 0 else 0
            
            display_name = TICKER_TO_NAME.get(ticker, ticker)
            stats_summary.append({
                "종목명": display_name,
                "티커": ticker,
                "누적 수익률 (%)": round(cum_ret, 2),
                "연간 환산 수익률 (%)": round(annual_ret, 2),
                "연간 변동성 (위험) (%)": round(annual_vol, 2),
                "샤프 지수 (위험대비 성과)": round(sharpe_ratio, 2),
                "최대 낙폭 (MDD) (%)": round(mdd, 2)
            })
            
        df_stats = pd.DataFrame(stats_summary).set_index("종목명")
        
        # 컬럼 이름 변경 (가독성 향상)
        df_cum_renamed = df_cum_returns.rename(columns=TICKER_TO_NAME)
        df_prices_renamed = df_prices.rename(columns=TICKER_TO_NAME)

        # 6. 메인 화면 구성 - 탭 레이아웃
        tab_kr, tab_us, tab_compare, tab_heatmap, tab_single = st.tabs([
            "🇰🇷 한국 주식 분석", 
            "🇺🇸 미국 주식 분석", 
            "🔄 한-미 통합 비교", 
            "📊 상관관계 분석 (Heatmap)", 
            "🔍 개별 종목 깊이 보기"
        ])

        # ----------------------------------------------------
        # Tab 1: 한국 주식 분석
        # ----------------------------------------------------
        with tab_kr:
            st.subheader("🇰🇷 선택된 한국 주식 누적 수익률")
            kr_selected_cols = [TICKER_TO_NAME.get(KR_STOCKS[name]) for name in selected_kr if KR_STOCKS[name] in df_cum_renamed.columns]
            
            if kr_selected_cols:
                fig_kr = px.line(
                    df_cum_renamed[kr_selected_cols],
                    labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "종목명"},
                    title="한국 주식 누적 수익률 비교 추이",
                    template="plotly_white"
                )
                fig_kr.update_layout(hovermode="x unified")
                st.plotly_chart(fig_kr, use_container_width=True)
                
                st.write("### 📉 한국 주식 핵심 성과 지표")
                st.dataframe(df_stats.loc[df_stats.index.isin(selected_kr)])
            else:
                st.info("왼쪽 사이드바에서 한국 주식을 선택해 주세요.")

        # ----------------------------------------------------
        # Tab 2: 미국 주식 분석
        # ----------------------------------------------------
        with tab_us:
            st.subheader("🇺🇸 선택된 미국 주식 누적 수익률")
            us_selected_cols = [TICKER_TO_NAME.get(US_STOCKS[name]) for name in selected_us if US_STOCKS[name] in df_cum_renamed.columns]
            
            if us_selected_cols:
                fig_us = px.line(
                    df_cum_renamed[us_selected_cols],
                    labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "종목명"},
                    title="미국 주식 누적 수익률 비교 추이",
                    template="plotly_white"
                )
                fig_us.update_layout(hovermode="x unified")
                st.plotly_chart(fig_us, use_container_width=True)
                
                st.write("### 📉 미국 주식 핵심 성과 지표")
                st.dataframe(df_stats.loc[df_stats.index.isin(selected_us)])
            else:
                st.info("왼쪽 사이드바에서 미국 주식을 선택해 주세요.")

        # ----------------------------------------------------
        # Tab 3: 한-미 통합 비교 (오류가 발생했던 곳)
        # ----------------------------------------------------
        with tab_compare:
            st.subheader("🔄 한-미 주식 통합 비교 시각화")
            st.markdown("한국과 미국 주식의 누적 수익률을 한 차트에 그려 국가 간 자산 성과를 직관적으로 비교합니다.")
            
            fig_all = px.line(
                df_cum_renamed,
                labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "종목명"},
                title="전체 선택 종목 누적 수익률 일괄 비교",
                template="plotly_white"
            )
            fig_all.update_layout(hovermode="x unified")
            st.plotly_chart(fig_all, use_container_width=True)
            
            # 종합 성과 대시보드
            st.write("### 🏆 전체 자산 종합 성과 분석표")
            st.markdown("- **연간 변동성**: 주가 움직임의 위험도를 뜻하며, 높을수록 가격 변동이 심합니다.")
            st.markdown("- **샤프 지수**: 1 단위의 위험을 감수할 때 얻는 초과 수익입니다. **높을수록 우수한 자산**입니다.")
            st.markdown("- **최대 낙폭(MDD)**: 최고점 대비 최대 하락폭으로, 투자 시 겪을 수 있는 최악의 고통 지수입니다.")
            
            # 스타일 에러 방지를 위해 try-except 적용
            try:
                # matplotlib이 성공적으로 임포트되었을 때 그라데이션 스타일 적용
                styled_df = df_stats.style.background_gradient(
                    cmap="Blues", 
                    subset=["누적 수익률 (%)", "샤프 지수 (위험대비 성과)"]
                )
                st.dataframe(styled_df)
            except Exception as style_error:
                # 스타일 적용 중 오류가 나면 일반 데이터프레임으로 안전하게 출력
                st.warning("테이블 스타일(색상) 적용 중 오류가 발생하여 기본 형식으로 표시합니다. (requirements.txt에 matplotlib이 정상 설치되었는지 확인해 주세요)")
                st.dataframe(df_stats)

        # ----------------------------------------------------
        # Tab 4: 상관관계 분석 (Heatmap)
        # ----------------------------------------------------
        with tab_heatmap:
            st.subheader("📊 자산 간 수익률 상관관계 분석 (Correlation)")
            st.markdown("""
            서로 다른 주식들이 얼마나 비슷하게 움직이는지 통계적으로 비교하는 피어슨 상관계수(Pearson Correlation Coefficient) 지도입니다.
            - **1.0에 가까울수록**: 양의 상관관계 (두 주식이 똑같이 상승/하락)
            - **0.0에 가까울수록**: 무상관 (서로 전혀 영향 없이 따로 움직임 -> **포트폴리오 분산 투자 효과 극대화**)
            - **-1.0에 가까울수록**: 음의 상관관계 (청개구리처럼 반대로 움직임)
            """)
            
            if len(df_returns.columns) > 1:
                df_corr = df_returns.corr()
                df_corr_renamed = df_corr.rename(index=TICKER_TO_NAME, columns=TICKER_TO_NAME)
                
                fig_heat = px.imshow(
                    df_corr_renamed,
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    zmin=-1.0,
                    zmax=1.0,
                    title="종목 간 일일 수익률 상관계수 행렬"
                )
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.warning("상관관계를 분석하려면 최소 2개 이상의 종목을 선택해 주세요.")

        # ----------------------------------------------------
        # Tab 5: 개별 종목 깊이 보기 (이동평균선 & 거래량)
        # ----------------------------------------------------
        with tab_single:
            st.subheader("🔍 개별 종목 기술적 지표 & 거래량 상세 분석")
            
            all_names_list = list(df_prices_renamed.columns)
            selected_single_name = st.selectbox("분석할 종목을 하나 선택하세요", options=all_names_list)
            
            single_price = df_prices_renamed[selected_single_name]
            sma_20 = single_price.rolling(window=20).mean()
            sma_60 = single_price.rolling(window=60).mean()
            
            fig_single = go.Figure()
            fig_single.add_trace(go.Scatter(x=single_price.index, y=single_price, name="종가", line=dict(color="#1F77B4", width=2)))
            fig_single.add_trace(go.Scatter(x=sma_20.index, y=sma_20, name="20일 이동평균선", line=dict(color="#FF7F0E", width=1.5, dash="dash")))
            fig_single.add_trace(go.Scatter(x=sma_60.index, y=sma_60, name="60일 이동평균선", line=dict(color="#2CA02C", width=1.5, dash="dot")))
            
            fig_single.update_layout(
                title=f"{selected_single_name} 주가 및 이동평균선 추이",
                xaxis_title="날짜",
                yaxis_title="주가 (로컬 통화)",
                template="plotly_white",
                hovermode="x unified"
            )
            st.plotly_chart(fig_single, use_container_width=True)
            
            st.write("#### 일별 거래량 (Volume) 분석")
            inv_ticker_map = {v: k for k, v in TICKER_TO_NAME.items()}
            actual_ticker = inv_ticker_map.get(selected_single_name, selected_single_name)
            
            if actual_ticker in df_volumes.columns:
                single_volume = df_volumes[actual_ticker]
                fig_vol = px.bar(
                    x=single_volume.index,
                    y=single_volume,
                    labels={"x": "날짜", "y": "거래량 (주)"},
                    title=f"{selected_single_name} 일별 거래량 추이",
                    color_discrete_sequence=["#9467BD"],
                    template="plotly_white"
                )
                st.plotly_chart(fig_vol, use_container_width=True)

    else:
        st.error("데이터를 불러오지 못했습니다. 선택한 종목의 티커 혹은 날짜 범위를 다시 확인해 주세요.")
else:
    st.info("왼쪽 사이드바에서 비교하고 싶은 한국 및 미국 주식을 선택하세요!")
