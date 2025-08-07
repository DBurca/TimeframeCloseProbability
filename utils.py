import yfinance as yf
import pandas as pd
from collections import defaultdict, Counter
import time, tqdm

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