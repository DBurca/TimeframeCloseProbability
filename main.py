import yfinance as yf
import pandas as pd
from collections import defaultdict, Counter

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
    """
    if not streaks:
        return 0.0
    
    # Count how many times we had streaks of current_length or longer
    extended_count = sum(1 for streak in streaks if streak > current_length)
    total_opportunities = sum(1 for streak in streaks if streak >= current_length)
    
    if total_opportunities == 0:
        return 0.0
    
    return (extended_count / total_opportunities) * 100

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

def analyze_ticker(ticker):
    """
    Main analysis function for a given ticker.
    """
    print(f"\n{'='*60}")
    print(f"ANALYZING {ticker.upper()}")
    print(f"{'='*60}")
    
    try:
        # Download data
        stock = yf.Ticker(ticker)
        data = stock.history(period="1000d")  # Last 1000 trading days
        
        if data.empty or len(data) < 10:
            print(f"Error: Insufficient data for {ticker}")
            return
        
        closes = data['Close'].values
        print(f"Loaded {len(closes)} trading days of data")
        
        # Get consecutive streaks
        up_streaks, down_streaks = get_consecutive_streaks(closes)
        
        print(f"\nHistorical Streak Analysis:")
        print(f"Total up streaks found: {len(up_streaks)}")
        print(f"Total down streaks found: {len(down_streaks)}")
        
        if up_streaks:
            print(f"Longest up streak: {max(up_streaks)} days")
            print(f"Average up streak: {sum(up_streaks)/len(up_streaks):.1f} days")
        
        if down_streaks:
            print(f"Longest down streak: {max(down_streaks)} days")
            print(f"Average down streak: {sum(down_streaks)/len(down_streaks):.1f} days")
        
        # Get current streak
        current_length, current_direction = get_current_streak(closes)
        
        print(f"\nCurrent Status:")
        print(f"Current streak: {current_length} consecutive {current_direction} day(s)")
        print(f"Last close: ${closes[-1]:.2f}")
        
        if len(closes) >= 2:
            print(f"Previous close: ${closes[-2]:.2f}")
            change = ((closes[-1] - closes[-2]) / closes[-2]) * 100
            print(f"Last day change: {change:+.2f}%")
        
        # Calculate probabilities for next close
        print(f"\n{'='*60}")
        print("NEXT CLOSE PROBABILITIES")
        print(f"{'='*60}")
        
        if current_direction == 'up':
            extend_prob = calculate_streak_probabilities(up_streaks, current_length)
            break_prob = 100 - extend_prob
            
            print(f"Probability of extending up streak to {current_length + 1} days: {extend_prob:.1f}%")
            print(f"Probability of breaking up streak: {break_prob:.1f}%")
            
            next_upside_prob = extend_prob
            next_downside_prob = break_prob
            
        else:  # current_direction == 'down'
            extend_prob = calculate_streak_probabilities(down_streaks, current_length)
            break_prob = 100 - extend_prob
            
            print(f"Probability of extending down streak to {current_length + 1} days: {extend_prob:.1f}%")
            print(f"Probability of breaking down streak: {break_prob:.1f}%")
            
            next_upside_prob = break_prob
            next_downside_prob = extend_prob
        
        print(f"\nSUMMARY - Next Daily Close:")
        print(f"Upside probability: {next_upside_prob:.1f}%")
        print(f"Downside probability: {next_downside_prob:.1f}%")
        
        # Calculate probabilities for the close after next
        print(f"\n{'='*60}")
        print("DAY AFTER NEXT PROBABILITIES")
        print(f"{'='*60}")
        
        # Scenario 1: Next close is up (extending current streak)
        if current_direction == 'up':
            # We would have current_length + 1 consecutive up days
            # Now calculate probability of extending to current_length + 2
            extended_length = current_length + 1
            scenario1_up = calculate_streak_probabilities(up_streaks, extended_length)
            scenario1_down = 100 - scenario1_up
        else:
            # We're breaking a down streak with an up day
            # Now calculate probability of extending this new up streak to 2 days
            scenario1_up = calculate_streak_probabilities(up_streaks, 1)
            scenario1_down = 100 - scenario1_up
        
        # Scenario 2: Next close is down (extending current streak if down, or breaking if up)
        if current_direction == 'down':
            # We would have current_length + 1 consecutive down days
            # Now calculate probability of extending to current_length + 2
            extended_length = current_length + 1
            scenario2_down = calculate_streak_probabilities(down_streaks, extended_length)
            scenario2_up = 100 - scenario2_down
        else:
            # We're breaking an up streak with a down day
            # Now calculate probability of extending this new down streak to 2 days
            scenario2_down = calculate_streak_probabilities(down_streaks, 1)
            scenario2_up = 100 - scenario2_down
        
        print(f"If next daily close is ABOVE current:")
        print(f"  └─ Day after: {scenario1_up:.1f}% up, {scenario1_down:.1f}% down")
        
        print(f"If next daily close is BELOW current:")
        print(f"  └─ Day after: {scenario2_up:.1f}% up, {scenario2_down:.1f}% down")
        
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
            print(f"  {length} day(s): {count} times ({percentage:.1f}%)")
        
        print("\nDown streaks:")
        for length in sorted(down_counter.keys())[:10]:  # Show first 10
            count = down_counter[length]
            percentage = (count / len(down_streaks)) * 100
            print(f"  {length} day(s): {count} times ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"Error analyzing {ticker}: {str(e)}")

def main():
    """
    Main program loop.
    """
    print("Stock Consecutive Move Probability Analyzer")
    print("This program analyzes the probability of consecutive up/down moves")
    print("based on historical data from the past 1000 trading days.\n")
    
    while True:
        ticker = input("Enter a stock ticker symbol (e.g., SPY, AAPL): ").strip().upper()
        
        if not ticker:
            print("Please enter a valid ticker symbol.")
            continue
        
        analyze_ticker(ticker)
        
        print(f"\n{'='*60}")
        continue_analysis = input("\nWould you like to analyze another ticker? (y/n): ").strip().lower()
        
        if continue_analysis not in ['y', 'yes']:
            print("Thank you for using the Stock Probability Analyzer!")
            break

if __name__ == "__main__":
    main()