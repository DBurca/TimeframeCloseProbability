# Stock Consecutive Move Probability Analyzer

A Python tool for analyzing the probability of consecutive up/down moves in stock prices based on historical data patterns. This analyzer helps traders and investors identify potential momentum opportunities by calculating the statistical likelihood of price movements continuing or reversing.

## 🚀 Features

### Single Stock Analysis
- **Deep Statistical Analysis**: Analyze any stock ticker with comprehensive consecutive streak statistics
- **Multiple Timeframes**: Support for 1-minute to 1-month intervals (1m, 2m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo)
- **Flexible Historical Data**: Load anywhere from days to years of historical data
- **Current Streak Detection**: Automatically identifies current consecutive up/down periods
- **Probability Calculations**: 
  - Next period probability (upside vs downside)
  - Period-after-next conditional probabilities
  - Historical streak distribution analysis

### S&P 500 Scanner
- **Mass Market Screening**: Scan all S&P 500 stocks simultaneously
- **Customizable Filters**: Set minimum probability thresholds for upside/downside moves
- **Smart Results Sorting**: Automatically sorts results by market capitalization
- **Progress Tracking**: Real-time progress updates with tqdm progress bars
- **Comprehensive Results**: View probability distributions, top opportunities, and detailed statistics

### Advanced Analytics
- **Streak Rarity Analysis**: Understand how rare current consecutive moves are historically
- **Pattern Recognition**: Identify momentum patterns and reversal probabilities
- **Risk Assessment**: Evaluate the statistical likelihood of trend continuation vs reversal
- **Market Cap Intelligence**: Prioritize larger, more liquid stocks in scanner results

## 📋 Requirements

```
yfinance>=0.2.0
pandas>=1.3.0
tqdm>=4.62.0
```

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock-probability-analyzer.git
cd stock-probability-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the analyzer:
```bash
python main.py
```

## 🎯 Usage

### Single Stock Analysis

Choose option 1 and analyze any stock with customizable parameters:

```
Choose what you'd like to do:
1. Analyze a single stock
2. Scan S&P 500 stocks for opportunities

Enter your choice: 1
Enter desired timeframe: 1d
Enter number of days: 1000
Enter a stock ticker symbol: AAPL
```

**Example Output:**
```
============================================================
ANALYZING AAPL - 1D TIMEFRAME
============================================================
Successfully loaded 1000 data points
Data range: 2021-08-07 to 2024-08-07

Historical Streak Analysis:
Total up streaks found: 152
Total down streaks found: 153
Longest up streak: 12 periods
Average up streak: 2.8 periods

Current Status:
Current streak: 3 consecutive up period(s)
Last close: $185.42

============================================================
NEXT CLOSE PROBABILITIES
============================================================
Probability of extending up streak to 4 periods: 45.2%
Probability of breaking up streak: 54.8%

SUMMARY - Next Period Close:
Upside probability: 45.2%
Downside probability: 54.8%
```

### S&P 500 Scanner

Choose option 2 to scan for opportunities across the entire S&P 500:

```
Choose what you'd like to do:
2. Scan S&P 500 stocks for opportunities

Scanner Options:
1. Scan for upside probability
2. Scan for downside probability  
3. Scan for both

Select scan type: 1
Enter minimum probability threshold: 75
```

**Example Scanner Output:**
```
SCAN RESULTS
================================================================================
Ticker   Price      Upside%  Downside%   Streak       Direction  Market Cap     
--------------------------------------------------------------------------------
AAPL     $185.42    78.3%    21.7%       3 periods    UP         $2.9T          
MSFT     $415.26    82.1%    17.9%       2 periods    UP         $3.1T          
NVDA     $118.57    76.4%    23.6%       5 periods    UP         $2.9T          

TOP 10 UPSIDE OPPORTUNITIES:
 1. MSFT - 82.1% upside probability
 2. AAPL - 78.3% upside probability
 3. NVDA - 76.4% upside probability
```

## 📊 Understanding the Analysis

### Consecutive Streaks
The analyzer identifies consecutive periods where:
- **Up Period**: Closing price > Previous closing price
- **Down Period**: Closing price ≤ Previous closing price

### Probability Calculations
- **Streak Extension**: Historical frequency of streaks continuing beyond current length
- **Streak Breaking**: Probability of current streak ending
- **Conditional Probabilities**: Future scenarios based on next period's direction

### Key Metrics
- **Current Streak**: Number of consecutive up/down periods
- **Historical Distribution**: Frequency analysis of all past streaks
- **Rarity Assessment**: How unusual the current streak length is
- **Market Cap Weighting**: Prioritizes larger, more liquid stocks

## ⚠️ Important Considerations

### Data Limitations
- **Intraday Data**: yfinance limits high-frequency data (1m data limited to 7 days)
- **Weekend Gaps**: Analysis uses actual trading periods, not calendar days
- **Historical Bias**: Past performance does not guarantee future results

### Statistical Assumptions
- Assumes independence of consecutive moves (which may not hold in reality)
- Does not account for fundamental analysis, news events, or market conditions
- Probabilities are based purely on historical price patterns

### Risk Disclaimer
This tool is for educational and research purposes only. It should not be used as the sole basis for investment decisions. Always:
- Conduct thorough fundamental analysis
- Consider current market conditions and news
- Implement proper risk management
- Consult with financial advisors when appropriate

## 🏗️ Project Structure

```
stock-probability-analyzer/
├── main.py          # Main application entry point
├── scanner.py       # S&P 500 scanning functionality
├── utils.py         # Shared utility functions
├── requirements.txt # Python dependencies
└── README.md       # This file
```

## Future Enhancements

- **Additional Markets**: Support for international exchanges and cryptocurrencies
- **Advanced Filters**: Sector-based filtering, volume analysis, volatility metrics  
- **Export Capabilities**: CSV/Excel export for scan results
- **Backtesting Framework**: Historical validation of probability predictions
- **API Integration**: Real-time alerts and automated scanning
- **Technical Indicators**: Integration with RSI, MACD, and other indicators

## License

This project is open source

## Acknowledgments

- **yfinance**: For providing free access to Yahoo Finance market data
- **pandas**: For powerful data manipulation capabilities
- **tqdm**: For elegant progress bar implementation

---

**Disclaimer**: This repository was developed with the assistance of Claude.ai