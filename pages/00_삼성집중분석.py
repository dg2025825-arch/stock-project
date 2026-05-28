def run_samsung_analysis(start_date, end_date):
    st.title("🇰🇷 삼성전자 (005930.KS) 집중 분석")
    st.markdown("""
    **삼성전자**는 글로벌 메모리 반도체 1위 기업이자 코스피 시장의 대장주입니다. 
    이 분석 메뉴에서는 **중장기 반도체 업황 사이클(120일선)**과 **거래량-주가 상관관계**를 통해 시장 참여자들의 심리를 분석합니다.
    """)
    
    df = get_single_stock_data("005930.KS", start_date, end_date)
    if df.empty:
        st.error("데이터를 가져올 수 없습니다.")
        return
        
    # 1. 기술적 분석: 20일선 vs 120일선 (사이클 분석)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA120'] = df['Close'].rolling(window=120).mean()
    
    st.subheader("🔍 중장기 반도체 업황 사이클 (종가 vs 120일선)")
    st.markdown("- **120일 이동평균선(약 6개월)**은 기업의 장기 펀더멘탈과 글로벌 IT 수요 사이클을 나타내는 중요한 지지/저항선입니다.")
    
    fig_cycle = go.Figure()
    fig_cycle.add_trace(go.Scatter(x=df.index, y=df['Close'], name="삼성전자 종가", line=dict(color="#1F4E79", width=2)))
    fig_cycle.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="20일 단기선", line=dict(color="#FFC000", width=1.2, dash="dash")))
    fig_cycle.add_trace(go.Scatter(x=df.index, y=df['MA120'], name="120일 경기선", line=dict(color="#ED7D31", width=1.5)))
    fig_cycle.update_layout(template="plotly_white", hovermode="x unified", yaxis_title="주가 (원)")
    st.plotly_chart(fig_cycle, use_container_width=True)
    
    # 2. 거래량 분석 (수급 대리 지표)
    st.subheader("📈 거래량 변화 및 주가 동조화 분석")
    st.markdown("주가 상승일의 대량 거래량은 매수세의 유입을, 주가 하락일의 대량 거래량은 매도 압력을 시각적으로 보여줍니다.")
    
    df['Daily_Return'] = df['Close'].pct_change()
    df['Color'] = np.where(df['Daily_Return'] > 0, '상승일 (매수 우위)', '하락일 (매도 우위)')
    
    fig_vol = px.scatter(
        df.dropna(),
        x="Volume",
        y="Daily_Return",
        color="Color",
        color_discrete_map={'상승일 (매수 우위)': '#2CA02C', '하락일 (매도 우위)': '#D62728'},
        labels={"Volume": "거래량", "Daily_Return": "일일 수익률"},
        title="삼성전자 일일 수익률과 거래량의 상관성",
        template="plotly_white"
    )
    st.plotly_chart(fig_vol, use_container_width=True)
