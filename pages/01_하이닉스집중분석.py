import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="SK하이닉스 정밀 분석",
    page_icon="🇰🇷",
    layout="wide"
)

st.title("🚀 SK하이닉스 (000660.KS) 글로벌 AI 반도체 정밀 분석")
st.markdown("""
당곡고등학교 학생 여러분 반갑습니다! 본 대시보드는 글로벌 HBM(고대역폭 메모리) 시장의 선두 주자인 **SK하이닉스**의 데이터를 심층 분석합니다.
특히 **KOSPI 지수 대비 민감도(Beta)**와 글로벌 AI 핵심 파트너인 **엔비디아(NVIDIA)와의 동조화(Correlation) 현상**을 집중적으로 탐구해 보세요.
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
def load_hynix_complex_data(start, end):
    try:
        # 안전하게 종목별로 개별 다운로드하여 딕셔너리로 취합
        hynix = yf.download("000660.KS", start=start, end=end, multi_level_index=False)
        kospi = yf.download("^KS11", start=start, end=end, multi_level_index=False)
        nvidia = yf.download("NVDA", start=start, end=end, multi_level_index=False)
        
        return hynix, kospi, nvidia
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로딩 실행
df_hynix, df_kospi, df_nvda = load_hynix_complex_data(start_date, end_date)

if not df_hynix.empty and not df_kospi.empty and not df_nvda.empty:
    # 4. 실시간 주요 지표 카드
    current_price = df_hynix['Close'].iloc[-1]
    prev_price = df_hynix['Close'].iloc[-2] if len(df_hynix) > 1 else current_price
    price_diff = current_price - prev_price
    price_pct = (price_diff / prev_price) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="SK하이닉스 현재가", value=f"{int(current_price):,} 원", delta=f"{int(price_diff):,}원 ({price_pct:.2f}%)")
    with col2:
        max_price = df_hynix['High'].max()
        st.metric(label="기간 내 최고가", value=f"{int(max_price):,} 원")
    with col3:
        min_price = df_hynix['Low'].min()
        st.metric(label="기간 내 최저가", value=f"{int(min_price):,} 원")

    # 탭 구성 (다양한 학술적 비교 요소 탑재)
    tab1, tab2, tab3 = st.tabs([
        "📈 기술적 추세 및 거래량", 
        "⚖️ KOSPI 대비 민감도 (Beta 분석)", 
        "🔗 AI 공급망 동조화 (NVIDIA 상관성)"
    ])

    # ----------------------------------------------------
    # Tab 1: 기술적 추세 및 거래량
    # ----------------------------------------------------
    with tab1:
        st.subheader("📊 기술적 가격 추이 및 이동평균선")
        st.markdown("단기 수급선(20일선)과 중기 매물대선(60일선)을 통해 골든크로스와 데드크로스를 분석해 보세요.")
        
        # 이동평균선 계산
        df_hynix['MA20'] = df_hynix['Close'].rolling(window=20).mean()
        df_hynix['MA60'] = df_hynix['Close'].rolling(window=60).mean()
        
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=df_hynix.index, y=df_hynix['Close'], name="SK하이닉스 종가", line=dict(color="#FF7F0E", width=2)))
        fig_price.add_trace(go.Scatter(x=df_hynix.index, y=df_hynix['MA20'], name="20일 단기 이평선", line=dict(color="#1F77B4", width=1.2, dash="dash")))
        fig_price.add_trace(go.Scatter(x=df_hynix.index, y=df_hynix['MA60'], name="60일 중기 이평선", line=dict(color="#2CA02C", width=1.2, dash="dot")))
        fig_price.update_layout(template="plotly_white", hovermode="x unified", yaxis_title="주가 (원)")
        st.plotly_chart(fig_price, use_container_width=True)
        
        # 일별 거래량 차트
        st.subheader("📥 일별 거래량 추이")
        df_hynix['Daily_Return'] = df_hynix['Close'].pct_change() * 100
        df_hynix['Type'] = np.where(df_hynix['Daily_Return'] > 0, '상승일', '하락일')
        
        fig_vol = px.bar(
            df_hynix, x=df_hynix.index, y="Volume",
            color="Type",
            color_discrete_map={'상승일': '#10B981', '하락일': '#EF4444'},
            labels={"Volume": "거래량", "index": "날짜"},
            title="상승/하락 구분에 따른 거래량 유입 패턴",
            template="plotly_white"
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    # ----------------------------------------------------
    # Tab 2: KOSPI 대비 민감도 (Beta 분석)
    # ----------------------------------------------------
    with tab2:
        st.subheader("⚖️ 통계적 시장 위험 및 베타(Beta, β) 계수 분석")
        st.markdown("""
        **베타(Beta) 계수**는 시장 전체(KOSPI)가 1% 변할 때 개별 자산(SK하이닉스)이 얼마나 민감하게 움직이는지 나타내는 **체계적 위험 지표**입니다.
        - **Beta > 1**: 시장 평균보다 변동성이 큰 공격형 주식 (SK하이닉스가 대표적입니다.)
        - **Beta < 1**: 시장 평균보다 변동성이 작은 방어형 주식
        """)
        
        # 일일 수익률 계산 및 병합
        ret_hynix = df_hynix['Close'].pct_change().dropna()
        ret_kospi = df_kospi['Close'].pct_change().dropna()
        
        df_beta = pd.DataFrame({'Hynix': ret_hynix, 'KOSPI': ret_kospi}).dropna()
        
        # 공분산과 분산을 이용한 Beta 수식 구현
        covariance = df_beta['Hynix'].cov(df_beta['KOSPI'])
        kospi_variance = df_beta['KOSPI'].var()
        beta_value = covariance / kospi_variance
        
        # 연율화 변동성 계산
        hynix_vol = ret_hynix.std() * np.sqrt(252) * 100
        kospi_vol = ret_kospi.std() * np.sqrt(252) * 100

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.metric(label="SK하이닉스 통계적 Beta", value=f"{beta_value:.2f}", delta="시장(KOSPI) 대비 고위험" if beta_value > 1 else "시장 대비 저위험")
        with col_b2:
            st.metric(label="SK하이닉스 연율화 변동성", value=f"{hynix_vol:.2f}%")
        with col_b3:
            st.metric(label="KOSPI 지수 연율화 변동성", value=f"{kospi_vol:.2f}%")
            
        # 산점도 및 회귀선 그래프
        fig_scatter = px.scatter(
            df_beta, x="KOSPI", y="Hynix",
            trendline="ols",
            labels={"KOSPI": "코스피 지수 일일 수익률", "Hynix": "SK하이닉스 일일 수익률"},
            title="코스피 대비 SK하이닉스 일일 수익률 분포 및 선형 회귀선",
            template="plotly_white"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ----------------------------------------------------
    # Tab 3: AI 공급망 동조화 (NVIDIA 상관성)
    # ----------------------------------------------------
    with tab3:
        st.subheader("🔗 글로벌 AI 공급망 동조화 연구 (NVIDIA vs SK하이닉스)")
        st.markdown("""
        SK하이닉스는 고성능 인공지능 학습에 핵심 부품인 **HBM(고대역폭 메모리)**을 전 세계에서 최초로 개발하여 **NVIDIA(엔비디아)**에 독점적 지위로 납품하고 있습니다.
        두 기업의 주가 데이터가 글로벌 인공지능 거품 논란이나 칩 수요 변화에 어떻게 **커플링(Coupling, 동조화)**되는지 과학적으로 검증합니다.
        """)
        
        # 1. 스케일 맞추기 위한 누적 수익률 계산
        cum_hynix = (df_hynix['Close'] / df_hynix['Close'].iloc[0] - 1) * 100
        cum_nvda = (df_nvda['Close'] / df_nvda['Close'].iloc[0] - 1) * 100
        
        df_cum_compare = pd.DataFrame({
            'SK하이닉스 누적수익률 (%)': cum_hynix,
            'NVIDIA 누적수익률 (%)': cum_nvda
        }).ffill().bfill()
        
        fig_cum = px.line(
            df_cum_compare,
            labels={"value": "누적 수익률 (%)", "index": "날짜", "variable": "기업명"},
            title="동일 시작일 기준 누적 수익률 (%) 비교",
            template="plotly_white",
            color_discrete_map={'SK하이닉스 누적수익률 (%)': '#FF7F0E', 'NVIDIA 누적수익률 (%)': '#76B900'} # 엔비디아 시그니처 초록색 매핑
        )
        fig_cum.update_layout(hovermode="x unified")
        st.plotly_chart(fig_cum, use_container_width=True)
        
        # 2. 피어슨 상관계수(Pearson Correlation Coefficient) 분석
        ret_nvda = df_nvda['Close'].pct_change().dropna()
        df_corr_analysis = pd.DataFrame({
            'SK하이닉스 일일수익률': ret_hynix,
            'NVIDIA 일일수익률': ret_nvda
        }).dropna()
        
        correlation_coefficient = df_corr_analysis.corr().iloc[0, 1]
        
        st.write("#### 📐 통계적 상관계수 결과")
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1:
            st.metric(label="NVIDIA와의 수익률 상관계수 (R)", value=f"{correlation_coefficient:.3f}")
        with col_b2:
            if correlation_coefficient >= 0.7:
                st.success("🔥 **매우 강한 양의 상관관계**입니다. 두 기업은 하나의 경제적 생태계로 묶여 아주 밀접하게 움직이고 있습니다.")
            elif correlation_coefficient >= 0.4:
                st.info("⚡ **적절한 수준의 양의 상관관계**입니다. 글로벌 반도체 및 AI 업황의 훈풍이 두 주가에 공통으로 작용하고 있습니다.")
            else:
                st.warning("💤 **낮은 상관관계**입니다. 조회 기간 동안 개별 기업의 호재나 주가 변동성, 또는 거시경제적 외풍(환율 등)이 더 큰 영향을 미쳤습니다.")

else:
    st.error("데이터 로드에 실패했습니다. Ticker나 네트워크 상태를 점검해 주세요.")
