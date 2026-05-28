import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. 페이지 설정 및 제목
st.set_page_config(
    page_title="한-미 주식 비교 분석기",
    page_icon="📊",
    layout="wide"
)

st.title("📊 한-미 주요 주식 수익률 및 차트 비교 분석기")
st.markdown("""
당곡고등학교 학생 여러분 반갑습니다! 이 웹앱은 한국과 미국의 주요 기업 및 시장 지수의 데이터를 실시간으로 가져와 **수익률을 비교**해 줍니다.
서로 다른 주가의 스케일을 맞추기 위해 **시작일 기준 누적 수익률(%)**로 변환하여 시각화합니다.
""")

# 2. 사이드바 - 설정 영역
st.sidebar.header("⚙️ 설정 및 입력")

# 기본 제공 티커 사전 (이름: 티커 기호)
# 한국 주식은 끝에 .KS(코스피) 또는 .KQ(코스닥)를 붙여야 합니다.
ticker_dict = {
    "삼성전자 (한국)": "005930.KS",
    "SK하이닉스 (한국)": "000660.KS",
    "NAVER (한국)": "035420.KS",
    "현대차 (한국)": "005380.KS",
    "코스피 지수 (한국)": "^KS11",
    "애플 (미국)": "AAPL",
    "마이크로소프트 (미국)": "MSFT",
    "테슬라 (미국)": "TSLA",
    "엔비디아 (미국)": "NVDA",
    "S&P 500 (미국)": "^GSPC"
}

# 분석 기간 선택
today = datetime.today()
one_year_ago = today - timedelta(days=365)

start_date = st.sidebar.date_input("시작일 선택", one_year_ago)
end_date = st.sidebar.date_input("종료일 선택", today)

if start_date >= end_date:
    st.sidebar.error("오류: 시작일은 종료일보다 빨라야 합니다.")

# 비교 대상 주식 다중 선택
selected_names = st.sidebar.multiselect(
    "비교할 기본 주식을 선택하세요",
    options=list(ticker_dict.keys()),
    default=["삼성전자 (한국)", "애플 (미국)", "S&P 500 (미국)"]
)

# 직접 티커 입력 기능 (학생들의 자율 탐구 지원)
custom_tickers = st.sidebar.text_input(
    "직접 티커 입력 (쉼표로 구분)",
    placeholder="예: GOOG, 035720.KS (카카오)"
)

# 최종 조회 대상 티커 리스트 생성
tickers_to_fetch = [ticker_dict[name] for name in selected_names]
if custom_tickers:
    custom_list = [t.strip().upper() for t in custom_tickers.split(",") if t.strip()]
    tickers_to_fetch.extend(custom_list)

# 3. 데이터 로드 및 연산
@st.cache_data(ttl=3600)  # 1시간 동안 캐싱하여 속도 향상
def load_data(tickers, start, end):
    df_all = pd.DataFrame()
    for ticker in tickers:
        try:
            # 주식의 종가(Close) 데이터 가져오기
            data = yf.download(ticker, start=start, end=end)
            if not data.empty:
                # pandas 버전에 따라 MultiIndex가 생길 수 있으므로 'Close' 열만 안전하게 추출
                if isinstance(data.columns, pd.MultiIndex):
                    close_series = data['Close'][ticker]
                else:
                    close_series = data['Close']
                
                df_all[ticker] = close_series
        except Exception as e:
            st.warning(f"티커 '{ticker}' 데이터를 불러오는 도중 오류가 발생했습니다.")
    return df_all

# 데이터 가져오기 실행
if tickers_to_fetch:
    with st.spinner("야후 파이낸스에서 데이터를 가져오는 중입니다..."):
        df_prices = load_data(tickers_to_fetch, start_date, end_date)
    
    if not df_prices.empty:
        # 결측치 처리 (휴장일 등이 다를 수 있으므로 앞의 데이터로 채움)
        df_prices = df_prices.ffill().bfill()
        
        # 누적 수익률 계산 공식: ((현재가 / 시작일 기준가) - 1) * 100
        df_returns = (df_prices / df_prices.iloc[0] - 1) * 100
        
        # 한글 이름 매핑 (시각화 시 범례를 알아보기 쉽게 변경)
        reverse_ticker_dict = {v: k for k, v in ticker_dict.items()}
        rename_cols = {col: reverse_ticker_dict.get(col, col) for col in df_returns.columns}
        df_returns_renamed = df_returns.rename(columns=rename_cols)
        df_prices_renamed = df_prices.rename(columns=rename_cols)

        # 4. 화면 레이아웃 구성
        # 메인 메트릭 표시 (마지막 날 누적 수익률)
        st.subheader("📈 선택 기간 최종 누적 수익률")
        cols = st.columns(len(df_returns_renamed.columns))
        for i, col_name in enumerate(df_returns_renamed.columns):
            final_return = df_returns_renamed[col_name].iloc[-1]
            cols[i % len(cols)].metric(
                label=col_name,
                value=f"{final_return:.2f}%",
                delta=f"{final_return:.2f}%"
            )

        # 수익률 비교 차트 (Plotly 사용)
        st.subheader("📊 일별 누적 수익률 추이 비교")
        fig_returns = px.line(
            df_returns_renamed,
            x=df_returns_renamed.index,
            y=df_returns_renamed.columns,
            labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "자산명"},
            title="기준일(0%) 대비 수익률 변화"
        )
        fig_returns.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_returns, use_container_width=True)

        # 실제 주가(종가) 추이 차트
        st.subheader("💵 실제 주가(종가) 추이")
        st.write("*주의: 한국 주식은 원화(KRW), 미국 주식은 달러(USD) 기준이므로 단순 수치 크기 비교는 의미가 없습니다.*")
        fig_prices = px.line(
            df_prices_renamed,
            x=df_prices_renamed.index,
            y=df_prices_renamed.columns,
            labels={"value": "주가 (원화 또는 달러)", "Date": "날짜", "variable": "자산명"},
            title="개별 자산의 단순 주가 흐름"
        )
        st.plotly_chart(fig_prices, use_container_width=True)

        # 데이터 테이블 보여주기
        with st.expander("원본 데이터 보기"):
            st.write("### 최근 10영업일의 누적 수익률 데이터 (%)")
            st.dataframe(df_returns_renamed.tail(10))
            
    else:
        st.error("불러온 데이터가 없습니다. 선택한 기간이나 티커가 올바른지 확인해 주세요.")
else:
    st.info("비교할 주식을 왼쪽 사이드바에서 최소 하나 이상 선택하거나 입력해 주세요.")
