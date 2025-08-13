#!/usr/bin/env python
# MAIN FILE

from collections import Counter

import yfinance as yf

from stock_probability_analyzer.scanner import scanner_mode
from stock_probability_analyzer.utils import (
    calculate_streak_probabilities,
    get_consecutive_streaks,
    get_current_streak,
)


def calculate_break_probabilities(
    up_streaks, down_streaks, current_length, current_direction
):
    """
    Calculate probabilities after breaking the current streak.
    """
    if current_direction == "up":
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
        "1": ("1m", "1 minute"),
        "2": ("2m", "2 minutes"),
        "5": ("5m", "5 minutes"),
        "15": ("15m", "15 minutes"),
        "30": ("30m", "30 minutes"),
        "60": ("1h", "1 hour"),
        "90": ("90m", "90 minutes"),
        "1h": ("1h", "1 hour"),
        "1d": ("1d", "1 day"),
        "5d": ("5d", "5 days"),
        "1wk": ("1wk", "1 week"),
        "1mo": ("1mo", "1 month"),
    }

    print("\nAvailable timeframes:")
    print("1m, 2m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo")
    print(
        "Examples: '1m' for 1-minute, '1h' for 1-hour, '1d' for daily, '1wk' for weekly"
    )

    while True:
        timeframe = input("Enter desired timeframe: ").strip().lower()

        # Convert some common inputs
        if timeframe in ["1min", "1minute"]:
            timeframe = "1m"
        elif timeframe in ["1hour", "1hr"]:
            timeframe = "1h"
        elif timeframe in ["1day", "daily", "d"]:
            timeframe = "1d"
        elif timeframe in ["1week", "weekly", "w"]:
            timeframe = "1wk"
        elif timeframe in ["1month", "monthly"]:
            timeframe = "1mo"

        if timeframe in [
            "1m",
            "2m",
            "5m",
            "15m",
            "30m",
            "1h",
            "90m",
            "1d",
            "5d",
            "1wk",
            "1mo",
        ]:
            return timeframe
        else:
            print(
                "Invalid timeframe. Please use: 1m, 2m, 5m, 15m, 30m, 1h, 1d, 5d, 1wk, 1mo"
            )


def get_days_selection(timeframe):
    """
    Prompt user for number of days and validate based on timeframe limitations.
    """
    # Define limitations for different timeframes
    limitations = {
        "1m": {
            "max_days": 7,
            "warning": "yfinance limits 1-minute data to last 7 days",
        },
        "2m": {
            "max_days": 60,
            "warning": "yfinance limits 2-minute data to last 60 days",
        },
        "5m": {
            "max_days": 60,
            "warning": "yfinance limits 5-minute data to last 60 days",
        },
        "15m": {
            "max_days": 60,
            "warning": "yfinance limits 15-minute data to last 60 days",
        },
        "30m": {
            "max_days": 60,
            "warning": "yfinance limits 30-minute data to last 60 days",
        },
        "1h": {
            "max_days": 730,
            "warning": "yfinance limits hourly data to last 2 years",
        },
        "90m": {
            "max_days": 60,
            "warning": "yfinance limits 90-minute data to last 60 days",
        },
        "1d": {"max_days": None, "warning": None},  # No practical limit for daily
        "5d": {"max_days": None, "warning": None},
        "1wk": {"max_days": None, "warning": None},
        "1mo": {"max_days": None, "warning": None},
    }

    limit_info = limitations.get(timeframe, {"max_days": None, "warning": None})

    print(f"\nSelected timeframe: {timeframe}")
    if limit_info["warning"]:
        print(f"⚠️  WARNING: {limit_info['warning']}")
        if limit_info["max_days"]:
            print(f"   Maximum recommended days: {limit_info['max_days']}")

    while True:
        try:
            days = int(input("Enter number of days of historical data to load: "))
            if days <= 0:
                print("Please enter a positive number of days.")
                continue

            # Check if requested days exceed limitations
            if limit_info["max_days"] and days > limit_info["max_days"]:
                print(
                    f"⚠️  WARNING: You requested {days} days, but {timeframe} data is limited to {limit_info['max_days']} days."
                )
                print("   The API may return less data than requested or fail.")

                continue_anyway = input("Continue anyway? (y/n): ").strip().lower()
                if continue_anyway not in ["y", "yes"]:
                    continue

            # Additional warnings for intraday data
            if timeframe in ["1m", "2m", "5m", "15m", "30m", "1h", "90m"] and days > 30:
                print(
                    f"⚠️  NOTE: Requesting {days} days of {timeframe} data will require many data points."
                )
                print("   This may take longer to download and analyze.")

            return days

        except ValueError:
            print("Please enter a valid number.")


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
            print(
                f"Warning: Only {len(data)} data points loaded. Need at least 10 for meaningful analysis."
            )
            return

        closes = data["Close"].values
        print(f"Successfully loaded {len(closes)} data points")

        # Show data range
        start_date = (
            data.index[0].strftime("%Y-%m-%d %H:%M")
            if timeframe != "1d"
            else data.index[0].strftime("%Y-%m-%d")
        )
        end_date = (
            data.index[-1].strftime("%Y-%m-%d %H:%M")
            if timeframe != "1d"
            else data.index[-1].strftime("%Y-%m-%d")
        )
        print(f"Data range: {start_date} to {end_date}")

        # Get consecutive streaks
        up_streaks, down_streaks = get_consecutive_streaks(closes)

        print("\nHistorical Streak Analysis:")
        print(f"Total up streaks found: {len(up_streaks)}")
        print(f"Total down streaks found: {len(down_streaks)}")

        if up_streaks:
            print(f"Longest up streak: {max(up_streaks)} periods")
            print(f"Average up streak: {sum(up_streaks)/len(up_streaks):.1f} periods")

        if down_streaks:
            print(f"Longest down streak: {max(down_streaks)} periods")
            print(
                f"Average down streak: {sum(down_streaks)/len(down_streaks):.1f} periods"
            )

        # Get current streak
        current_length, current_direction = get_current_streak(closes)

        print("\nCurrent Status:")
        print(
            f"Current streak: {current_length} consecutive {current_direction} period(s)"
        )
        print(f"Last close: ${closes[-1]:.2f}")

        if len(closes) >= 2:
            print(f"Previous close: ${closes[-2]:.2f}")
            change = ((closes[-1] - closes[-2]) / closes[-2]) * 100
            print(f"Last period change: {change:+.2f}%")

        # Calculate probabilities for next close
        print(f"\n{'='*60}")
        print("NEXT CLOSE PROBABILITIES")
        print(f"{'='*60}")

        if current_direction == "up":
            extend_prob = calculate_streak_probabilities(up_streaks, current_length)
            break_prob = 100 - extend_prob

            print(
                f"Probability of extending up streak to {current_length + 1} periods: {extend_prob:.1f}%"
            )
            print(f"Probability of breaking up streak: {break_prob:.1f}%")

            next_upside_prob = extend_prob
            next_downside_prob = break_prob

        else:  # current_direction == 'down'
            extend_prob = calculate_streak_probabilities(down_streaks, current_length)
            break_prob = 100 - extend_prob

            print(
                f"Probability of extending down streak to {current_length + 1} periods: {extend_prob:.1f}%"
            )
            print(f"Probability of breaking down streak: {break_prob:.1f}%")

            next_upside_prob = break_prob
            next_downside_prob = extend_prob

        print("\nSUMMARY - Next Period Close:")
        print(f"Upside probability: {next_upside_prob:.1f}%")
        print(f"Downside probability: {next_downside_prob:.1f}%")

        # Calculate probabilities for the close after next
        print(f"\n{'='*60}")
        print("PERIOD AFTER NEXT PROBABILITIES")
        print(f"{'='*60}")

        # Scenario 1: Next close is up (extending current streak)
        if current_direction == "up":
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
        if current_direction == "down":
            # We would have current_length + 1 consecutive down periods
            # Now calculate probability of extending to current_length + 2
            extended_length = current_length + 1
            scenario2_down = calculate_streak_probabilities(
                down_streaks, extended_length
            )
            scenario2_up = 100 - scenario2_down
        else:
            # We're breaking an up streak with a down period
            # Now calculate probability of extending this new down streak to 2 periods
            scenario2_down = calculate_streak_probabilities(down_streaks, 1)
            scenario2_up = 100 - scenario2_down

        print("If next close is ABOVE current:")
        print(f"  └─ Period after: {scenario1_up:.1f}% up, {scenario1_down:.1f}% down")

        print("If next close is BELOW current:")
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
        ticker = (
            input("Enter a stock ticker symbol or type 'scanner': ").strip().upper()
        )

        if not ticker:
            print("Please enter a valid ticker symbol.")
            continue

        # Get timeframe selection
        timeframe = get_timeframe_selection()

        # Get number of days
        days = get_days_selection(timeframe)

        if ticker == "SCANNER":
            scanner_mode(timeframe, days)
        else:
            # Analyze the ticker
            analyze_ticker(ticker, timeframe, days)

        print(f"\n{'='*60}")
        continue_analysis = (
            input("\nWould you like to analyze another ticker? (y/n): ").strip().lower()
        )

        if continue_analysis not in ["y", "yes"]:
            print("Thank you for using the Stock Probability Analyzer!")
            break


if __name__ == "__main__":
    main()
