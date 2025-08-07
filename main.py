import yfinance as yf
import pandas as pd
from collections import defaultdict, Counter
import time
import sys

def get_consecutive_streaks(closes):
    """
    Analyze consecutive up/down moves in closing prices.
    Returns dictionaries with streak lengths and their frequencies.
    """
    up_streaks = []
    down_streaks = []
    
    current_up_streak = 0
    current_down_streak = 0
    
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:  # Up day
            current_up_streak += 1
            if current_down_streak > 0:
                down_streaks.append(current_down_streak)
                current_down_streak = 0
        else:  # Down day (or equal)
            current_down_streak += 1
            if current_up_streak > 0:
                up_streaks.append(current_up_streak)
                current_up_streak = 0
    
    # Don't forget the last streak if it's still active
    if current_up_streak > 0:
        up_streaks.append(current_up_streak)
    if current_down_streak > 0:
        down_streaks.append(current_down_streak)
    
    return up_streaks, down_streaks

def get_current_streak(closes):
    """
    Determine the current consecutive streak and its direction.
    Returns (streak_length, direction) where direction is 'up' or 'down'
    """
    if len(closes) < 2:
        return 0, 'none'
    
    current_streak = 1
    if closes[-1] > closes[-2]:
        direction = 'up'
        for i in range(len(closes)-2, 0, -1):
            if closes[i] > closes[i-1]:
                current_streak += 1
            else:
                break
    else:
        direction = 'down'
        for i in range(len(closes)-2, 0, -1):
            if closes[i] <= closes[i-1]:
                current_streak += 1
            else:
                break
    
    return current_streak, direction

def calculate_streak_probabilities(streaks, current_length):
    """
    Calculate probability of extending a streak of given length.
    This properly accounts for the fact that longer streaks contain evidence
    of all intermediate lengths (e.g., a 10-day streak reached 8 and 9 days).
    """
    if not streaks:
        return 0.0
    
    # Count opportunities: how many times historically did we reach current_length?
    # A streak of length N provides evidence for reaching lengths 1, 2, 3, ..., N
    opportunities_at_current_length = sum(1 for streak in streaks if streak >= current_length)
    
    # Count extensions: how many times did we extend beyond current_length?
    # A streak of length N shows extension beyond lengths 1, 2, 3, ..., N-1
    extended_count = sum(1 for streak in streaks if streak > current_length)
    
    if opportunities_at_current_length == 0:
        return 0.0
    
    return (extended_count / opportunities_at_current_length) * 100

def calculate_break_probabilities(up_streaks, down_streaks, current_length, current_direction):
    """
    Calculate probabilities after breaking the current streak.
    """
    if current_direction == 'up':
        # If we break an up streak, we start a down streak
        relevant_streaks = down_streaks
    else:
        # If we break a down streak, we start an up streak
        relevant_streaks = up_streaks
    
    if not relevant_streaks:
        return 50.0, 50.0  # Default to 50/50 if no data
    
    # Probability of at least 1 day in the new direction
    continue_new_direction = sum(1 for streak in relevant_streaks if streak >= 1)
    total_breaks = len(relevant_streaks)
    
    if total_breaks == 0:
        return 50.0, 50.0
    
    continue_prob = (continue_new_direction / total_breaks) * 100
    reverse_prob = 100 - continue_prob
    
    return continue_prob, reverse_prob

def get_timeframe_selection():
    """
    Prompt user for timeframe selection and return appropriate yfinance interval.
    """
    timeframes = {
        '1': ('1m', '1 minute'),
        '2': ('2m', '2 minutes'),
        '5': ('5m', '5 minutes'),
        '15': ('15m', '15 minutes'),
        '30': ('30m', '30 minutes'),
        '60': ('1h', '1 hour'),
        '90': ('90m', '90 minutes'),
        '1h': ('1h', '1 hour'),
        '1d': ('1d', '1 day'),
        '5d': ('5d', '5 days'),
        '1wk': ('1wk', '1 week'),
        '1mo': ('1mo', '1 month')
    }
    
    print("\nAvailable timeframes:")
    print("1m, 2m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo")
    print("Examples: '1m' for 1-minute, '1h' for 1-hour, '1d' for daily, '1wk' for weekly")
    
    while True:
        timeframe = input("Enter desired timeframe: ").strip().lower()
        
        # Convert some common inputs
        if timeframe in ['1min', '1minute']:
            timeframe = '1m'
        elif timeframe in ['1hour', '1hr']:
            timeframe = '1h'
        elif timeframe in ['1day', 'daily', 'd']:
            timeframe = '1d'
        elif timeframe in ['1week', 'weekly', 'w']:
            timeframe = '1wk'
        elif timeframe in ['1month', 'monthly']:
            timeframe = '1mo'
        
        if timeframe in ['1m', '2m', '5m', '15m', '30m', '1h', '90m', '1d', '5d', '1wk', '1mo']:
            return timeframe
        else:
            print("Invalid timeframe. Please use: 1m, 2m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo")

def get_days_selection(timeframe):
    """
    Prompt user for number of days and validate based on timeframe limitations.
    """
    # Define limitations for different timeframes
    limitations = {
        '1m': {'max_days': 7, 'warning': 'yfinance limits 1-minute data to last 7 days'},
        '2m': {'max_days': 60, 'warning': 'yfinance limits 2-minute data to last 60 days'},
        '5m': {'max_days': 60, 'warning': 'yfinance limits 5-minute data to last 60 days'},
        '15m': {'max_days': 60, 'warning': 'yfinance limits 15-minute data to last 60 days'},
        '30m': {'max_days': 60, 'warning': 'yfinance limits 30-minute data to last 60 days'},
        '1h': {'max_days': 730, 'warning': 'yfinance limits hourly data to last 2 years'},
        '90m': {'max_days': 60, 'warning': 'yfinance limits 90-minute data to last 60 days'},
        '1d': {'max_days': None, 'warning': None},  # No practical limit for daily
        '5d': {'max_days': None, 'warning': None},
        '1wk': {'max_days': None, 'warning': None},
        '1mo': {'max_days': None, 'warning': None}
    }
    
    limit_info = limitations.get(timeframe, {'max_days': None, 'warning': None})
    
    print(f"\nSelected timeframe: {timeframe}")
    if limit_info['warning']:
        print(f"⚠️  WARNING: {limit_info['warning']}")
        if limit_info['max_days']:
            print(f"   Maximum recommended days: {limit_info['max_days']}")
    
    while True:
        try:
            days = int(input("Enter number of days of historical data to load: "))
            if days <= 0:
                print("Please enter a positive number of days.")
                continue
            
            # Check if requested days exceed limitations
            if limit_info['max_days'] and days > limit_info['max_days']:
                print(f"⚠️  WARNING: You requested {days} days, but {timeframe} data is limited to {limit_info['max_days']} days.")
                print("   The API may return less data than requested or fail.")
                
                continue_anyway = input("Continue anyway? (y/n): ").strip().lower()
                if continue_anyway not in ['y', 'yes']:
                    continue
            
            # Additional warnings for intraday data
            if timeframe in ['1m', '2m', '5m', '15m', '30m', '1h', '90m'] and days > 30:
                print(f"⚠️  NOTE: Requesting {days} days of {timeframe} data will require many data points.")
                print("   This may take longer to download and analyze.")
            
            return days
            
        except ValueError:
            print("Please enter a valid number.")

def get_sp500_tickers():
    """
    Get S&P 500 ticker symbols from Wikipedia.
    """
    try:
        # Read S&P 500 list from text file
        with open('stocks.txt', 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
        
        return tickers
    except Exception as e:
        print(f"Error loading S&P 500 list: {e}")
        # Fallback to a smaller list of major stocks
        return ['SPY', 'DJT', 'QQQ', 'AAPL','UNH', 'INTC', 'CMCSA', 'T', 'CVX', 'NVDA', 
                'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'META', 'AVGO', 'TSLA',
                'JPM', 'WMT', 'ORCL', 'LLY', 'V', 'MA', 'NFLX', 'XOM', 'COST', 'JNJ',
                'HD', 'ABBV', 'BAC', 'KO', 'MRK', 'CRM', 'ADBE', 'PEP', 'TMO',
                'TMUS', 'LIN', 'MCD', 'ACN', 'CSCO', 'GE', 'IBM', 'ABT', 'DHR', 'BX',
                'NOW', 'WFC', 'AXP', 'QCOM', 'PM', 'VZ', 'TXN', 'AMGN', 'INTU', 'CAT',
                'ISRG', 'NEE', 'DIS', 'PFE', 'MS', 'SPGI', 'AMAT', 'GS', 'RTX', 'SNOW', 'PANW'
                'PLTR']

def analyze_ticker_for_scanner(ticker, timeframe, days, min_data_points=50):
    """
    Lightweight version of analyze_ticker for scanner use.
    Returns probability data or None if analysis fails.
    """
    try:
        # Download data
        stock = yf.Ticker(ticker)
        
        # Calculate period string for yfinance
        if days <= 5:
            period_str = f"{days}d"
        elif days <= 365:
            period_str = f"{days}d"
        else:
            years = max(1, days // 365)
            period_str = f"{years}y"
        
        # Download with specified interval
        data = stock.history(period=period_str, interval=timeframe)
        
        if data.empty or len(data) < min_data_points:
            return None
        
        closes = data['Close'].values
        
        # Get consecutive streaks
        up_streaks, down_streaks = get_consecutive_streaks(closes)
        
        if not up_streaks or not down_streaks:
            return None
        
        # Get current streak
        current_length, current_direction = get_current_streak(closes)
        
        # Calculate probabilities for next close
        if current_direction == 'up':
            extend_prob = calculate_streak_probabilities(up_streaks, current_length)
            next_upside_prob = extend_prob
            next_downside_prob = 100 - extend_prob
        else:  # current_direction == 'down'
            extend_prob = calculate_streak_probabilities(down_streaks, current_length)
            next_upside_prob = 100 - extend_prob
            next_downside_prob = extend_prob
        
        # Get basic stock info
        info = stock.info
        market_cap = info.get('marketCap', 0) if info else 0
        current_price = closes[-1]
        
        return {
            'ticker': ticker,
            'upside_probability': next_upside_prob,
            'downside_probability': next_downside_prob,
            'current_streak': current_length,
            'streak_direction': current_direction,
            'current_price': current_price,
            'market_cap': market_cap,
            'data_points': len(closes)
        }
        
    except Exception as e:
        return None

def scanner_mode(timeframe, days):
    """
    Scanner mode to find stocks meeting probability criteria.
    """
    print(f"\n{'='*60}")
    print("STOCK PROBABILITY SCANNER")
    print(f"{'='*60}")
    print(f"Scanning S&P 500 stocks with {timeframe} timeframe and {days} days of data")
    
    # Get scan criteria
    print("\nScanner Options:")
    print("1. Scan for upside probability")
    print("2. Scan for downside probability")
    print("3. Scan for both (show all stocks)")
    
    while True:
        try:
            scan_type = input("Select scan type (1-3): ").strip()
            if scan_type in ['1', '2', '3']:
                break
            else:
                print("Please enter 1, 2, or 3")
        except:
            print("Please enter 1, 2, or 3")
    
    # Get minimum probability threshold
    while True:
        try:
            min_prob = float(input("Enter minimum probability threshold (e.g., 70 for 70%): "))
            if 0 <= min_prob <= 100:
                break
            else:
                print("Please enter a probability between 0 and 100")
        except ValueError:
            print("Please enter a valid number")
    
    # Get S&P 500 tickers
    print("Loading S&P 500 ticker list...")
    tickers = get_sp500_tickers()
    print(f"Found {len(tickers)} tickers to scan")
    
    # Initialize results storage
    results = []
    successful_scans = 0
    failed_scans = 0
    
    print(f"\nScanning stocks... (this may take a few minutes)")
    print("Progress: [", end="", flush=True)
    
    # Progress tracking
    total_tickers = len(tickers)
    progress_interval = max(1, total_tickers // 50)  # Show 50 progress marks max
    
    for i, ticker in enumerate(tickers):
        # Show progress
        if i % progress_interval == 0:
            print("█", end="", flush=True)
        
        # Analyze ticker
        result = analyze_ticker_for_scanner(ticker, timeframe, days)
        
        if result:
            successful_scans += 1
            
            # Check if it meets criteria
            meets_criteria = False
            
            if scan_type == '1':  # Upside only
                if result['upside_probability'] >= min_prob:
                    meets_criteria = True
            elif scan_type == '2':  # Downside only
                if result['downside_probability'] >= min_prob:
                    meets_criteria = True
            else:  # Both (scan_type == '3')
                if result['upside_probability'] >= min_prob or result['downside_probability'] >= min_prob:
                    meets_criteria = True
            
            if meets_criteria:
                results.append(result)
        else:
            failed_scans += 1
    
    print("]")  # Close progress bar
    
    # Display results
    print(f"\nScan Complete!")
    print(f"Successfully analyzed: {successful_scans} stocks")
    print(f"Failed to analyze: {failed_scans} stocks")
    print(f"Stocks meeting criteria: {len(results)}")
    
    if not results:
        print(f"\nNo stocks found with {min_prob}% or higher probability.")
        return
    
    # Sort by market cap (descending) if market cap data is available
    results_with_market_cap = [r for r in results if r['market_cap'] > 0]
    results_without_market_cap = [r for r in results if r['market_cap'] == 0]
    
    if results_with_market_cap:
        results_with_market_cap.sort(key=lambda x: x['market_cap'], reverse=True)
        final_results = results_with_market_cap + results_without_market_cap
    else:
        # Sort alphabetically if no market cap data
        final_results = sorted(results, key=lambda x: x['ticker'])
    
    # Display results
    print(f"\n{'='*100}")
    print("SCAN RESULTS")
    print(f"{'='*100}")
    print(f"{'Ticker':<8} {'Price':<10} {'Upside%':<9} {'Downside%':<11} {'Streak':<12} {'Direction':<10} {'Market Cap':<15}")
    print("-" * 100)
    
    # The following code block returns the analysis for the last stock in the list. Not necessary at this time, so commenting it out
    """
    for result in final_results:
        market_cap_str = f"${result['market_cap']/1e9:.1f}B" if result['market_cap'] > 0 else "N/A"
        streak_str = f"{result['current_streak']} periods"
        
        print(f"{result['ticker']:<8} "
              f"${result['current_price']:<9.2f} "
              f"{result['upside_probability']:<8.1f}% "
              f"{result['downside_probability']:<10.1f}% "
              f"{streak_str:<12} "
              f"{result['streak_direction'].upper():<10} "
              f"{market_cap_str:<15}")
    
    # Summary by probability ranges
    print(f"\n{'='*60}")
    print("PROBABILITY DISTRIBUTION")
    print(f"{'='*60}")
    
    if scan_type in ['1', '3']:  # Include upside analysis
        upside_ranges = {
            '90%+': len([r for r in results if r['upside_probability'] >= 90]),
            '80-89%': len([r for r in results if 80 <= r['upside_probability'] < 90]),
            '70-79%': len([r for r in results if 70 <= r['upside_probability'] < 80]),
            '60-69%': len([r for r in results if 60 <= r['upside_probability'] < 70]),
            '50-59%': len([r for r in results if 50 <= r['upside_probability'] < 60])
        }
        
        print("Upside Probability Distribution:")
        for range_name, count in upside_ranges.items():
            if count > 0:
                print(f"  {range_name}: {count} stocks")
    
    if scan_type in ['2', '3']:  # Include downside analysis
        downside_ranges = {
            '90%+': len([r for r in results if r['downside_probability'] >= 90]),
            '80-89%': len([r for r in results if 80 <= r['downside_probability'] < 90]),
            '70-79%': len([r for r in results if 70 <= r['downside_probability'] < 80]),
            '60-69%': len([r for r in results if 60 <= r['downside_probability'] < 70]),
            '50-59%': len([r for r in results if 50 <= r['downside_probability'] < 60])
        }
        
        print("Downside Probability Distribution:")
        for range_name, count in downside_ranges.items():
            if count > 0:
                print(f"  {range_name}: {count} stocks")
    
    # Show top 10 by highest probability
    print(f"\n{'='*60}")
    if scan_type == '1':
        top_stocks = sorted(results, key=lambda x: x['upside_probability'], reverse=True)[:50]
        print("TOP 50 UPSIDE OPPORTUNITIES:")
        for i, stock in enumerate(top_stocks, 1):
            print(f"{i:2d}. {stock['ticker']} - {stock['upside_probability']:.1f}% upside probability")
    elif scan_type == '2':
        top_stocks = sorted(results, key=lambda x: x['downside_probability'], reverse=True)[:50]
        print("TOP 50 DOWNSIDE OPPORTUNITIES:")
        for i, stock in enumerate(top_stocks, 1):
            print(f"{i:2d}. {stock['ticker']} - {stock['downside_probability']:.1f}% downside probability")
    else:  # Both
        print("TOP 50 HIGHEST PROBABILITY OPPORTUNITIES:")
        # Sort by highest probability (either upside or downside)
        for result in results:
            result['max_probability'] = max(result['upside_probability'], result['downside_probability'])
        
        top_stocks = sorted(results, key=lambda x: x['max_probability'], reverse=True)[:50]
        for i, stock in enumerate(top_stocks, 1):
            if stock['upside_probability'] > stock['downside_probability']:
                print(f"{i:2d}. {stock['ticker']} - {stock['upside_probability']:.1f}% upside probability")
            else:
                print(f"{i:2d}. {stock['ticker']} - {stock['downside_probability']:.1f}% downside probability")
    
    
   
    #### Main analysis function for a given ticker with specified timeframe and days.
    
    print(f"\n{'='*60}")
    print(f"ANALYZING {ticker.upper()} - {timeframe.upper()} TIMEFRAME")
    print(f"{'='*60}")
    
    try:
        # Download data
        stock = yf.Ticker(ticker)
        
        # Calculate period string for yfinance
        if days <= 5:
            period_str = f"{days}d"
        elif days <= 365:
            period_str = f"{days}d"
        else:
            # For longer periods, use years
            years = max(1, days // 365)
            period_str = f"{years}y"
        
        print(f"Downloading {days} days of {timeframe} data for {ticker.upper()}...")
        
        # Download with specified interval
        data = stock.history(period=period_str, interval=timeframe)
        
        if data.empty:
            print(f"Error: No data returned for {ticker} with {timeframe} timeframe")
            print("This might be due to:")
            print("- Invalid ticker symbol")
            print("- Timeframe limitations (try fewer days or different timeframe)")
            print("- Market hours (intraday data only available during trading hours)")
            return
        
        if len(data) < 10:
            print(f"Warning: Only {len(data)} data points loaded. Need at least 10 for meaningful analysis.")
            return
        
        closes = data['Close'].values
        print(f"Successfully loaded {len(closes)} data points")
        
        # Show data range
        start_date = data.index[0].strftime('%Y-%m-%d %H:%M') if timeframe != '1d' else data.index[0].strftime('%Y-%m-%d')
        end_date = data.index[-1].strftime('%Y-%m-%d %H:%M') if timeframe != '1d' else data.index[-1].strftime('%Y-%m-%d')
        print(f"Data range: {start_date} to {end_date}")
        
        # Get consecutive streaks
        up_streaks, down_streaks = get_consecutive_streaks(closes)
        
        print(f"\nHistorical Streak Analysis:")
        print(f"Total up streaks found: {len(up_streaks)}")
        print(f"Total down streaks found: {len(down_streaks)}")
        
        if up_streaks:
            print(f"Longest up streak: {max(up_streaks)} periods")
            print(f"Average up streak: {sum(up_streaks)/len(up_streaks):.1f} periods")
        
        if down_streaks:
            print(f"Longest down streak: {max(down_streaks)} periods")
            print(f"Average down streak: {sum(down_streaks)/len(down_streaks):.1f} periods")
        
        # Get current streak
        current_length, current_direction = get_current_streak(closes)
        
        print(f"\nCurrent Status:")
        print(f"Current streak: {current_length} consecutive {current_direction} period(s)")
        print(f"Last close: ${closes[-1]:.2f}")
        
        if len(closes) >= 2:
            print(f"Previous close: ${closes[-2]:.2f}")
            change = ((closes[-1] - closes[-2]) / closes[-2]) * 100
            print(f"Last period change: {change:+.2f}%")
        
        # Calculate probabilities for next close
        print(f"\n{'='*60}")
        print("NEXT CLOSE PROBABILITIES")
        print(f"{'='*60}")
        
        if current_direction == 'up':
            extend_prob = calculate_streak_probabilities(up_streaks, current_length)
            break_prob = 100 - extend_prob
            
            print(f"Probability of extending up streak to {current_length + 1} periods: {extend_prob:.1f}%")
            print(f"Probability of breaking up streak: {break_prob:.1f}%")
            
            next_upside_prob = extend_prob
            next_downside_prob = break_prob
            
        else:  # current_direction == 'down'
            extend_prob = calculate_streak_probabilities(down_streaks, current_length)
            break_prob = 100 - extend_prob
            
            print(f"Probability of extending down streak to {current_length + 1} periods: {extend_prob:.1f}%")
            print(f"Probability of breaking down streak: {break_prob:.1f}%")
            
            next_upside_prob = break_prob
            next_downside_prob = extend_prob
        
        print(f"\nSUMMARY - Next Period Close:")
        print(f"Upside probability: {next_upside_prob:.1f}%")
        print(f"Downside probability: {next_downside_prob:.1f}%")
        
        # Calculate probabilities for the close after next
        print(f"\n{'='*60}")
        print("PERIOD AFTER NEXT PROBABILITIES")
        print(f"{'='*60}")
        
        # Scenario 1: Next close is up (extending current streak)
        if current_direction == 'up':
            # We would have current_length + 1 consecutive up periods
            # Now calculate probability of extending to current_length + 2
            extended_length = current_length + 1
            scenario1_up = calculate_streak_probabilities(up_streaks, extended_length)
            scenario1_down = 100 - scenario1_up
        else:
            # We're breaking a down streak with an up period
            # Now calculate probability of extending this new up streak to 2 periods
            scenario1_up = calculate_streak_probabilities(up_streaks, 1)
            scenario1_down = 100 - scenario1_up
        
        # Scenario 2: Next close is down (extending current streak if down, or breaking if up)
        if current_direction == 'down':
            # We would have current_length + 1 consecutive down periods
            # Now calculate probability of extending to current_length + 2
            extended_length = current_length + 1
            scenario2_down = calculate_streak_probabilities(down_streaks, extended_length)
            scenario2_up = 100 - scenario2_down
        else:
            # We're breaking an up streak with a down period
            # Now calculate probability of extending this new down streak to 2 periods
            scenario2_down = calculate_streak_probabilities(down_streaks, 1)
            scenario2_up = 100 - scenario2_down
        
        print(f"If next close is ABOVE current:")
        print(f"  └─ Period after: {scenario1_up:.1f}% up, {scenario1_down:.1f}% down")
        
        print(f"If next close is BELOW current:")
        print(f"  └─ Period after: {scenario2_up:.1f}% up, {scenario2_down:.1f}% down")
        
        # Show some streak distribution for context
        print(f"\n{'='*60}")
        print("STREAK DISTRIBUTION (Historical)")
        print(f"{'='*60}")
        
        up_counter = Counter(up_streaks)
        down_counter = Counter(down_streaks)
        
        print("Up streaks:")
        for length in sorted(up_counter.keys())[:10]:  # Show first 10
            count = up_counter[length]
            percentage = (count / len(up_streaks)) * 100
            print(f"  {length} period(s): {count} times ({percentage:.1f}%)")
        
        print("\nDown streaks:")
        for length in sorted(down_counter.keys())[:10]:  # Show first 10
            count = down_counter[length]
            percentage = (count / len(down_streaks)) * 100
            print(f"  {length} period(s): {count} times ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"Error analyzing {ticker}: {str(e)}")
    """

def analyze_ticker(ticker, timeframe, days):
    """
    Main analysis function for a given ticker with specified timeframe and days.
    """
    print(f"\n{'='*60}")
    print(f"ANALYZING {ticker.upper()} - {timeframe.upper()} TIMEFRAME")
    print(f"{'='*60}")
    
    try:
        # Download data
        stock = yf.Ticker(ticker)
        
        # Calculate period string for yfinance
        if days <= 5:
            period_str = f"{days}d"
        elif days <= 365:
            period_str = f"{days}d"
        else:
            # For longer periods, use years
            years = max(1, days // 365)
            period_str = f"{years}y"
        
        print(f"Downloading {days} days of {timeframe} data for {ticker.upper()}...")
        
        # Download with specified interval
        data = stock.history(period=period_str, interval=timeframe)
        
        if data.empty:
            print(f"Error: No data returned for {ticker} with {timeframe} timeframe")
            print("This might be due to:")
            print("- Invalid ticker symbol")
            print("- Timeframe limitations (try fewer days or different timeframe)")
            print("- Market hours (intraday data only available during trading hours)")
            return
        
        if len(data) < 10:
            print(f"Warning: Only {len(data)} data points loaded. Need at least 10 for meaningful analysis.")
            return
        
        closes = data['Close'].values
        print(f"Successfully loaded {len(closes)} data points")
        
        # Show data range
        start_date = data.index[0].strftime('%Y-%m-%d %H:%M') if timeframe != '1d' else data.index[0].strftime('%Y-%m-%d')
        end_date = data.index[-1].strftime('%Y-%m-%d %H:%M') if timeframe != '1d' else data.index[-1].strftime('%Y-%m-%d')
        print(f"Data range: {start_date} to {end_date}")
        
        # Get consecutive streaks
        up_streaks, down_streaks = get_consecutive_streaks(closes)
        
        print(f"\nHistorical Streak Analysis:")
        print(f"Total up streaks found: {len(up_streaks)}")
        print(f"Total down streaks found: {len(down_streaks)}")
        
        if up_streaks:
            print(f"Longest up streak: {max(up_streaks)} periods")
            print(f"Average up streak: {sum(up_streaks)/len(up_streaks):.1f} periods")
        
        if down_streaks:
            print(f"Longest down streak: {max(down_streaks)} periods")
            print(f"Average down streak: {sum(down_streaks)/len(down_streaks):.1f} periods")
        
        # Get current streak
        current_length, current_direction = get_current_streak(closes)
        
        print(f"\nCurrent Status:")
        print(f"Current streak: {current_length} consecutive {current_direction} period(s)")
        print(f"Last close: ${closes[-1]:.2f}")
        
        if len(closes) >= 2:
            print(f"Previous close: ${closes[-2]:.2f}")
            change = ((closes[-1] - closes[-2]) / closes[-2]) * 100
            print(f"Last period change: {change:+.2f}%")
        
        # Calculate probabilities for next close
        print(f"\n{'='*60}")
        print("NEXT CLOSE PROBABILITIES")
        print(f"{'='*60}")
        
        if current_direction == 'up':
            extend_prob = calculate_streak_probabilities(up_streaks, current_length)
            break_prob = 100 - extend_prob
            
            print(f"Probability of extending up streak to {current_length + 1} periods: {extend_prob:.1f}%")
            print(f"Probability of breaking up streak: {break_prob:.1f}%")
            
            next_upside_prob = extend_prob
            next_downside_prob = break_prob
            
        else:  # current_direction == 'down'
            extend_prob = calculate_streak_probabilities(down_streaks, current_length)
            break_prob = 100 - extend_prob
            
            print(f"Probability of extending down streak to {current_length + 1} periods: {extend_prob:.1f}%")
            print(f"Probability of breaking down streak: {break_prob:.1f}%")
            
            next_upside_prob = break_prob
            next_downside_prob = extend_prob
        
        print(f"\nSUMMARY - Next Period Close:")
        print(f"Upside probability: {next_upside_prob:.1f}%")
        print(f"Downside probability: {next_downside_prob:.1f}%")
        
        # Calculate probabilities for the close after next
        print(f"\n{'='*60}")
        print("PERIOD AFTER NEXT PROBABILITIES")
        print(f"{'='*60}")
        
        # Scenario 1: Next close is up (extending current streak)
        if current_direction == 'up':
            # We would have current_length + 1 consecutive up periods
            # Now calculate probability of extending to current_length + 2
            extended_length = current_length + 1
            scenario1_up = calculate_streak_probabilities(up_streaks, extended_length)
            scenario1_down = 100 - scenario1_up
        else:
            # We're breaking a down streak with an up period
            # Now calculate probability of extending this new up streak to 2 periods
            scenario1_up = calculate_streak_probabilities(up_streaks, 1)
            scenario1_down = 100 - scenario1_up
        
        # Scenario 2: Next close is down (extending current streak if down, or breaking if up)
        if current_direction == 'down':
            # We would have current_length + 1 consecutive down periods
            # Now calculate probability of extending to current_length + 2
            extended_length = current_length + 1
            scenario2_down = calculate_streak_probabilities(down_streaks, extended_length)
            scenario2_up = 100 - scenario2_down
        else:
            # We're breaking an up streak with a down period
            # Now calculate probability of extending this new down streak to 2 periods
            scenario2_down = calculate_streak_probabilities(down_streaks, 1)
            scenario2_up = 100 - scenario2_down
        
        print(f"If next close is ABOVE current:")
        print(f"  └─ Period after: {scenario1_up:.1f}% up, {scenario1_down:.1f}% down")
        
        print(f"If next close is BELOW current:")
        print(f"  └─ Period after: {scenario2_up:.1f}% up, {scenario2_down:.1f}% down")
        
        # Show some streak distribution for context
        print(f"\n{'='*60}")
        print("STREAK DISTRIBUTION (Historical)")
        print(f"{'='*60}")
        
        up_counter = Counter(up_streaks)
        down_counter = Counter(down_streaks)
        
        print("Up streaks:")
        for length in sorted(up_counter.keys())[:10]:  # Show first 10
            count = up_counter[length]
            percentage = (count / len(up_streaks)) * 100
            print(f"  {length} period(s): {count} times ({percentage:.1f}%)")
        
        print("\nDown streaks:")
        for length in sorted(down_counter.keys())[:10]:  # Show first 10
            count = down_counter[length]
            percentage = (count / len(down_streaks)) * 100
            print(f"  {length} period(s): {count} times ({percentage:.1f}%)")
            
    except Exception as e:
        print(f"Error analyzing {ticker}: {str(e)}")

def main():
    """
    Main program loop.
    """
    print("Stock Consecutive Move Probability Analyzer")
    print("This program analyzes the probability of consecutive up/down moves")
    print("based on historical data with customizable timeframes and periods.\n")
    
    while True:
        # Get user inputs
        ticker = input("Enter a stock ticker symbol or type 'scanner': ").strip().upper()
        
        if not ticker:
            print("Please enter a valid ticker symbol.")
            continue
        
        # Get timeframe selection
        timeframe = get_timeframe_selection()
        
        # Get number of days
        days = get_days_selection(timeframe)
        
        if ticker == 'SCANNER':
            scanner_mode(timeframe, days)
        else:
            # Analyze the ticker
            analyze_ticker(ticker, timeframe, days)
            
        print(f"\n{'='*60}")
        continue_analysis = input("\nWould you like to analyze another ticker? (y/n): ").strip().lower()
        
        if continue_analysis not in ['y', 'yes']:
            print("Thank you for using the Stock Probability Analyzer!")
            break

if __name__ == "__main__":
    main()