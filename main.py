import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정 및 디자인 테마
st.set_page_config(
    page_title="글로벌 주식 융합 분석 플랫폼",
    page_icon="📈",
    layout="wide"
)

# 모던한 화이트/네이비 톤 스타일 지정
st.markdown("""
    <style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #475569;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #F8FAFC;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 글로벌 주식 다각도 비교 분석 플랫폼</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">당곡고등학교 학생들의 경제·통계학 탐구를 위한 한국·미국 주요 자산 다각도 분석 및 시뮬레이션 시스템입니다.</div>', unsafe_allow_html=True)

# 2. 고정 주식 데이터베이스 (각각 대표 10개 종목)
KR_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
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

# 벤치마크 지수 자동 로드용
BENCHMARKS = {
    "S&P 500 지수": "^GSPC",
    "코스피 지수": "^KS11"
}

# 역방향 매핑 사전 (티커 -> 한글이름)
TICKER_TO_NAME = {
    **{v: k for k, v in KR_STOCKS.items()}, 
    **{v: k for k, v in US_STOCKS.items()},
    **{v: k for k, v in BENCHMARKS.items()}
}

# 3. 사이드바 - 설정 영역
st.sidebar.header("⚙️ 분석 설정 및 자산 선택")

# 분석 기간 설정
today = datetime.today()
one_year_ago = today - timedelta(days=365)
start_date = st.sidebar.date_input("📅 분석 시작일", one_year_ago)
end_date = st.sidebar.date_input("📅 분석 종료일", today)

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

# 직접 티커 입력
custom_input = st.sidebar.text_input("➕ 추가할 티커 직접 입력 (쉼표 구분)", placeholder="예: TSMC의 TSM, 카카오의 035720.KS")

# 샤프지수용 무위험 수익률
rf_rate = st.sidebar.number_input("💵 무위험 수익률 설정 (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)

# 모든 티커 취합 (선택 종목 + 벤치마크 지수들 포함)
tickers_kr = [KR_STOCKS[name] for name in selected_kr]
tickers_us = [US_STOCKS[name] for name in selected_us]

tickers_custom = []
if custom_input:
    tickers_custom = [t.strip().upper() for t in custom_input.split(",") if t.strip()]

all_selected_tickers = tickers_kr + tickers_us + tickers_custom
all_tickers_with_benchmarks = list(set(all_selected_tickers + list(BENCHMARKS.values())))

# 4. 데이터 로드 및 정제 함수 (예외 처리 강화)
@st.cache_data(ttl=3600)
def fetch_stock_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame(), pd.DataFrame()
    try:
        data = yf.download(tickers, start=start, end=end)
        if data.empty:
            return pd.DataFrame(), pd.DataFrame()
            
        df_close = pd.DataFrame()
        df_volume = pd.DataFrame()
        
        # 다운로드된 데이터 구조(단일/멀티 인덱스)에 맞게 안전하게 종가와 거래량 분리 추출
        for ticker in tickers:
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    if ticker in data.columns.get_level_values(1):
                        df_close[ticker] = data['Close'][ticker]
                        df_volume[ticker] = data['Volume'][ticker]
                    elif ticker in data.columns.get_level_values(0):
                        df_close[ticker] = data[ticker]['Close']
                        df_volume[ticker] = data[ticker]['Volume']
                else:
                    if len(tickers) == 1:
                        df_close[ticker] = data['Close']
                        df_volume[ticker] = data['Volume']
                    else:
                        if ticker in data.columns:
                            df_close[ticker] = data[ticker]
            except Exception:
                continue
                
        return df_close, df_volume
    except Exception as e:
        st.error(f"데이터 로드 에러: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 데이터 로딩 실행
if all_selected_tickers:
    with st.spinner("⏳ 실시간 시장 데이터를 다운로드 중입니다..."):
        df_prices, df_volumes = fetch_stock_data(all_tickers_with_benchmarks, start_date, end_date)
        
    if not df_prices.empty:
        # 시장 휴장일 보정 (ffill 후 bfill)
        df_prices = df_prices.ffill().bfill()
        df_volumes = df_volumes.ffill().bfill()
        
        # 5. 핵심 통계 및 비교 요소들 계산
        df_returns = df_prices.pct_change().dropna()
        df_cum_returns = (df_prices / df_prices.iloc[0] - 1) * 100
        
        # 이름 변환 (한글명 매핑)
        df_cum_renamed = df_cum_returns.rename(columns=TICKER_TO_NAME)
        df_prices_renamed = df_prices.rename(columns=TICKER_TO_NAME)
        df_returns_renamed = df_returns.rename(columns=TICKER_TO_NAME)
        
        # 선택된 한국 및 미국 주식 이름 목록 (한글명 기준 필터링 - 버그 완벽 수정!)
        kr_selected_names = [name for name in selected_kr if name in df_cum_renamed.columns]
        us_selected_names = [name for name in selected_us if name in df_cum_renamed.columns]
        custom_selected_names = [TICKER_TO_NAME.get(ticker, ticker) for ticker in tickers_custom if TICKER_TO_NAME.get(ticker, ticker) in df_cum_renamed.columns]
        
        all_active_names = kr_selected_names + us_selected_names + custom_selected_names
        
        # 통계 연산 수행
        stats_summary = []
        for name in all_active_names:
            ticker = KR_STOCKS.get(name) or US_STOCKS.get(name) or name
            if name in df_prices_renamed.columns:
                series = df_prices_renamed[name]
                cum_ret = df_cum_renamed[name].iloc[-1]
                
                # 변동성 (Volatility)
                daily_std = df_returns_renamed[name].std() if name in df_returns_renamed.columns else 0
                annual_vol = daily_std * np.sqrt(252) * 100
                
                # 최대 낙폭 (MDD)
                roll_max = series.cummax()
                drawdown = (series - roll_max) / roll_max * 100
                mdd = drawdown.min()
                
                # 연환산 수익률 (CAGR)
                days = (series.index[-1] - series.index[0]).days
                annual_ret = (((series.iloc[-1] / series.iloc[0])) ** (365 / days) - 1) * 100 if days > 0 else 0
                
                # 샤프 지수
                sharpe = (annual_ret - rf_rate) / annual_vol if annual_vol > 0 else 0
                
                stats_summary.append({
                    "종목명": name,
                    "누적 수익률 (%)": round(cum_ret, 2),
                    "연간 환산 수익률 (%)": round(annual_ret, 2),
                    "연간 변동성 (%)": round(annual_vol, 2),
                    "샤프 지수": round(sharpe, 2),
                    "최대 낙폭 (MDD) (%)": round(mdd, 2)
                })
        
        df_stats = pd.DataFrame(stats_summary).set_index("종목명") if stats_summary else pd.DataFrame()

        # 6. 모던한 탭 기반 레이아웃 구성
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🇰🇷 한국 주식 분석", 
            "🇺🇸 미국 주식 분석", 
            "⚖️ 한-미 국가간 비교", 
            "📉 최대 낙폭(MDD) 위험 비교",
            "💼 글로벌 자산배분 시뮬레이터",
            "📊 변동성 & 상관관계",
            "🔍 개별 종목 탐색 (RSI 추가)"
        ])

        # ----------------------------------------------------
        # Tab 1: 한국 주식 분석
        # ----------------------------------------------------
        with tab1:
            st.subheader("🇰🇷 선택된 한국 주식 수익률 추이")
            if kr_selected_names:
                fig_kr = px.line(
                    df_cum_renamed[kr_selected_names],
                    labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "종목명"},
                    title="한국 주식 누적 수익률 (%)",
                    template="plotly_white"
                )
                fig_kr.update_layout(hovermode="x unified")
                st.plotly_chart(fig_kr, use_container_width=True)
                
                st.write("#### 📊 한국 선택 주식 핵심 지표")
                if not df_stats.empty:
                    st.dataframe(df_stats.loc[df_stats.index.isin(kr_selected_names)])
            else:
                st.info("왼쪽 사이드바에서 한국 주식을 선택해 주세요.")

        # ----------------------------------------------------
        # Tab 2: 미국 주식 분석
        # ----------------------------------------------------
        with tab2:
            st.subheader("🇺🇸 선택된 미국 주식 수익률 추이")
            if us_selected_names:
                fig_us = px.line(
                    df_cum_renamed[us_selected_names],
                    labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "종목명"},
                    title="미국 주식 누적 수익률 (%)",
                    template="plotly_white"
                )
                fig_us.update_layout(hovermode="x unified")
                st.plotly_chart(fig_us, use_container_width=True)
                
                st.write("#### 📊 미국 선택 주식 핵심 지표")
                if not df_stats.empty:
                    st.dataframe(df_stats.loc[df_stats.index.isin(us_selected_names)])
            else:
                st.info("왼쪽 사이드바에서 미국 주식을 선택해 주세요.")

        # ----------------------------------------------------
        # Tab 3: 한-미 국가간 비교
        # ----------------------------------------------------
        with tab3:
            st.subheader("⚖️ 국가 대표 주식 및 지수 성과 비교")
            st.markdown("한국과 미국에서 선택한 모든 주식의 누적 수익률을 동등한 기준선(0%)에서 한눈에 비교합니다.")
            
            fig_all = px.line(
                df_cum_renamed[all_active_names],
                labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "종목명"},
                title="한-미 전체 선택 종목 누적 수익률 통합 그래프",
                template="plotly_white"
            )
            fig_all.update_layout(hovermode="x unified")
            st.plotly_chart(fig_all, use_container_width=True)
            
            if not df_stats.empty:
                st.write("#### 🏆 전체 선택 주식 성과 평가")
                try:
                    st.dataframe(df_stats.style.background_gradient(cmap="Blues", subset=["누적 수익률 (%)", "샤프 지수"]))
                except Exception:
                    st.dataframe(df_stats)

        # ----------------------------------------------------
        # Tab 4: 최대 낙폭 (MDD) 위험 비교
        # ----------------------------------------------------
        with tab4:
            st.subheader("📉 최대 낙폭 (MDD: Max Drawdown) 비교")
            st.markdown("""
            **최대 낙폭(MDD)**은 특정 기간 동안 자산의 고점 대비 하락한 비율을 뜻하며, 투자자가 겪게 되는 **'심리적 고통의 최대치'**를 측정하는 아주 훌륭한 위험 통계 지표입니다.
            그래프가 아래로 깊게 내려갈수록 해당 자산이 과거에 크게 하락했음을 의미합니다.
            """)
            
            # MDD 시계열 데이터 계산
            df_mdd_series = (df_prices_renamed[all_active_names] / df_prices_renamed[all_active_names].cummax() - 1) * 100
            
            fig_mdd = px.line(
                df_mdd_series,
                labels={"value": "고점 대비 낙폭 (%)", "Date": "날짜", "variable": "종목명"},
                title="일별 낙폭(Drawdown) 추이 비교",
                template="plotly_white"
            )
            fig_mdd.update_layout(hovermode="x unified")
            st.plotly_chart(fig_mdd, use_container_width=True)

        # ----------------------------------------------------
        # Tab 5: 글로벌 자산배분 시뮬레이터 (융합 분석)
        # ----------------------------------------------------
        with tab5:
            st.subheader("💼 나만의 글로벌 가상 포트폴리오 백테스터")
            st.markdown("""
            한국과 미국 주식을 섞어서 나만의 포트폴리오를 만들면 성과가 어떻게 될까요? 
            아래 종목들의 투자 비중을 합해서 **100%**로 맞춰 입력해 보세요. 벤치마크 지수(S&P 500, 코스피)와 성능을 직접 비교할 수 있습니다.
            """)
            
            if len(all_active_names) > 0:
                # 비중 조절 컨테이너
                weights = {}
                total_w = 0.0
                st.write("##### 🎛️ 각 종목의 비중을 설정해 주세요 (합계 100%)")
                
                cols = st.columns(len(all_active_names))
                equal_w = round(100.0 / len(all_active_names), 1)
                
                for i, name in enumerate(all_active_names):
                    with cols[i]:
                        w = st.number_input(f"{name} (%)", min_value=0.0, max_value=100.0, value=equal_w, key=f"port_{name}")
                        weights[name] = w / 100.0
                        total_w += w
                
                st.markdown(f"**현재 설정한 총 비중 합계:** `{total_w:.1f}%`")
                
                if abs(total_w - 100.0) > 0.1:
                    st.warning("⚠️ 투자 비중의 합계가 100%가 되도록 조정해 주세요!")
                else:
                    # 포트폴리오 수익률 시계열 계산
                    portfolio_growth = pd.Series(0.0, index=df_cum_renamed.index)
                    for name in all_active_names:
                        portfolio_growth += weights[name] * (1 + df_cum_renamed[name] / 100.0)
                    
                    df_simulation = pd.DataFrame()
                    df_simulation["내 글로벌 포트폴리오"] = (portfolio_growth - 1) * 100
                    
                    # 벤치마크 추가
                    if "S&P 500 지수" in df_cum_renamed.columns:
                        df_simulation["S&P 500 Benchmark"] = df_cum_renamed["S&P 500 지수"]
                    if "코스피 지수" in df_cum_renamed.columns:
                        df_simulation["KOSPI Benchmark"] = df_cum_renamed["코스피 지수"]
                        
                    fig_sim = px.line(
                        df_simulation,
                        labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "포트폴리오"},
                        title="내 포트폴리오 vs 대표 시장 지수 성과 비교",
                        template="plotly_white"
                    )
                    fig_sim.update_layout(hovermode="x unified")
                    st.plotly_chart(fig_sim, use_container_width=True)
            else:
                st.info("비교 분석을 위해 왼쪽 사이드바에서 주식을 1개 이상 선택해 주세요.")

        # ----------------------------------------------------
        # Tab 6: 변동성 & 상관관계
        # ----------------------------------------------------
        with tab6:
            st.subheader("📊 변동성 분포 및 상관관계 분석")
            
            sub_tab_corr, sub_tab_dist = st.tabs(["🔥 상관관계 Heatmap", "📈 일일 수익률 분포 (Risk-Profile)"])
            
            with sub_tab_corr:
                st.markdown("자산 간의 동조화 현상(같은 방향으로 움직이는 정도)을 통계적으로 보여줍니다.")
                if len(all_active_names) > 1:
                    df_corr = df_returns_renamed[all_active_names].corr()
                    fig_heat = px.imshow(
                        df_corr,
                        text_auto=".2f",
                        color_continuous_scale="RdBu_r",
                        zmin=-1.0, zmax=1.0,
                        title="종목 간 일일 수익률 상관계수 지도"
                    )
                    st.plotly_chart(fig_heat, use_container_width=True)
                else:
                    st.info("상관관계 분석을 위해서는 2개 이상의 종목을 선택해 주세요.")
                    
            with sub_tab_dist:
                st.markdown("자산의 일일 수익률 분포를 뜻하며, 분포의 폭(가로)이 넓을수록 가격 변동성과 투자 위험이 큰 자산임을 직관적으로 보여줍니다.")
                if all_active_names:
                    fig_hist = px.histogram(
                        df_returns_renamed[all_active_names],
                        barmode="overlay",
                        title="자산별 일일 수익률 빈도 분포 (히스토그램)",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

        # ----------------------------------------------------
        # Tab 7: 개별 종목 탐색 (RSI 추가)
        # ----------------------------------------------------
        with tab7:
            st.subheader("🔍 개별 종목 기술적 지표 정밀 탐색")
            st.markdown("자산의 실제 주가와 함께 과매수/과매도를 평가하는 대표적인 모멘텀 보조지표인 **RSI(Relative Strength Index)**를 시각화합니다.")
            
            target_stock = st.selectbox("분석할 자산을 선택하세요", options=all_active_names)
            
            if target_stock:
                price_series = df_prices_renamed[target_stock]
                
                # 이동평균선 계산
                sma_20 = price_series.rolling(window=20).mean()
                sma_60 = price_series.rolling(window=60).mean()
                
                # RSI 14 계산 공식 함수
                def calc_rsi(series, period=14):
                    delta = series.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rs = gain / (loss + 1e-9)
                    return 100 - (100 / (1 + rs))
                
                rsi_series = calc_rsi(price_series)
                
                # 주가 및 이평선 그래프
                fig_price_detail = go.Figure()
                fig_price_detail.add_trace(go.Scatter(x=price_series.index, y=price_series, name="종가", line=dict(color="#0F172A", width=2)))
                fig_price_detail.add_trace(go.Scatter(x=sma_20.index, y=sma_20, name="20일 이평선", line=dict(color="#3B82F6", width=1.2, dash="dash")))
                fig_price_detail.add_trace(go.Scatter(x=sma_60.index, y=sma_60, name="60일 이평선", line=dict(color="#EF4444", width=1.2, dash="dot")))
                fig_price_detail.update_layout(title=f"{target_stock} 가격 및 이동평균선", template="plotly_white")
                st.plotly_chart(fig_price_detail, use_container_width=True)
                
                # RSI 그래프
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=rsi_series.index, y=rsi_series, name="RSI (14)", line=dict(color="#8B5CF6", width=1.5)))
                # 기준선 표시 (30: 과매도 바닥 영역, 70: 과매수 천장 영역)
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="#EF4444", annotation_text="과매수 기준선 (70)")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="#3B82F6", annotation_text="과매도 기준선 (30)")
                fig_rsi.update_layout(title=f"{target_stock} RSI (14) 보조지표", yaxis=dict(range=[0, 100]), template="plotly_white")
                st.plotly_chart(fig_rsi, use_container_width=True)

    else:
        st.error("데이터를 정상적으로 가져오지 못했습니다. 날짜 범위를 조절하거나 선택 항목을 확인해 주세요.")
else:
    st.info("💡 왼쪽 사이드바에서 비교할 한국 및 미국 주식을 선택하시면 분석 플랫폼이 가동됩니다!")
