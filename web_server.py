from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# Import shared data management
import data_sync
import bot_settings

app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)

# Use shared data structures (direct references to module data)
# Note: We reference data_sync module directly to ensure synchronization

# Use dynamic settings
def get_current_settings():
    """Get current settings from bot_settings"""
    team1, team2 = bot_settings.get_team_names()
    return {
        'exchange_rates': bot_settings.get_exchange_rates(),
        'coefficients': bot_settings.get_coefficients(),
        'team_emojis': bot_settings.get_team_emojis(),
        'teams': {
            'team1': team1,
            'team2': team2
        }
    }

def convert_to_uah(amount, currency):
    """Convert amount to UAH using current exchange rates"""
    rates = bot_settings.get_exchange_rates()
    currency_code = currency.split(' ')[-1] if ' ' in currency else currency
    return amount * rates.get(currency_code, 1.0)

@app.route('/')
def index():
    """Serve the main web app"""
    return send_from_directory('static', 'index.html')

@app.route('/api/balance', methods=['POST'])
def get_balance():
    """Get user balance"""
    request_data = request.get_json()
    user_id = str(request_data.get('user_id'))
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    # Reload data to get latest balance
    data_sync.reload_data()
    balance = data_sync.user_balances.get(user_id, 0.0)
    
    print(f"BALANCE DEBUG: user_id={user_id}, returning balance={balance}")
    
    return jsonify({'balance': balance})

@app.route('/api/place_bet', methods=['POST'])
def place_bet():
    """Place a bet via web app"""
    try:
        request_data = request.get_json()
        print(f"Received bet request: {request_data}")
        
        user_id = request_data.get('user_id')
        team = request_data.get('team')
        currency = request_data.get('currency')
        amount = request_data.get('amount')
        coef = request_data.get('coef')
        
        # Validation
        if not all([user_id, team, currency, amount, coef]):
            print(f"Missing fields: user_id={user_id}, team={team}, currency={currency}, amount={amount}, coef={coef}")
            return jsonify({'success': False, 'error': 'Все поля обязательны'}), 400
        
        # Clear any previous result for this user (for new match)
        if data_sync.get_user_result(user_id):
            data_sync.set_user_result(user_id, None)
            print(f"Cleared previous result for user {user_id}")
        
        # Reload data to get latest balances and states
        data_sync.reload_data()
        
        # Check if user already made a bet
        if user_id in data_sync.user_bets:
            print(f"User {user_id} already has a bet")
            return jsonify({'success': False, 'error': 'Вы уже сделали ставку на этот матч'}), 400
        
        # Validate team
        current_coefficients = bot_settings.get_coefficients()
        if team not in current_coefficients:
            print(f"Invalid team: {team}")
            return jsonify({'success': False, 'error': 'Неверная команда'}), 400
        
        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError as e:
            print(f"Invalid amount: {amount}, error: {e}")
            return jsonify({'success': False, 'error': 'Неверная сумма ставки'}), 400
        
        # Convert currency format for compatibility with bot code
        currency_map = {
            'USD': '💵 USD',
            'EUR': '💶 EUR', 
            'UAH': '💸 UAH',
            'BTC': '₿ BTC',
            'ETH': '⟠ ETH'
        }
        
        formatted_currency = currency_map.get(currency, currency)
        print(f"Placing bet: user_id={user_id}, team={team}, currency={formatted_currency}, amount={amount}, coef={coef}")
        
        # Place the bet
        bet_uah = convert_to_uah(amount, formatted_currency)
        
        # Ensure user_id is string for consistency
        user_id = str(user_id)
        
        if user_id not in data_sync.user_balances:
            data_sync.user_balances[user_id] = 0.0
        
        # Debug current balance state
        current_balance = data_sync.user_balances.get(user_id, 0.0)
        print(f"PLACE BET DEBUG: user_id={user_id}, current_balance={current_balance}, bet_uah={bet_uah}")
        print(f"PLACE BET DEBUG: user_balances dict: {data_sync.user_balances}")
        
        # Check if user has enough balance
        if current_balance < bet_uah:
            raise ValueError(f"Недостаточно средств! Баланс: {current_balance:.2f} UAH, требуется: {bet_uah:.2f} UAH")
        
        # Deduct bet amount from balance (not add!)
        data_sync.user_balances[user_id] -= bet_uah
        
        # Ensure balance doesn't go negative
        if data_sync.user_balances[user_id] < 0:
            data_sync.user_balances[user_id] = 0.0
        
        # Record bet
        data_sync.user_state[user_id] = {
            "team": team,
            "currency": formatted_currency,
            "coef": coef,
            "bet": amount,
            "bet_uah": bet_uah
        }
        data_sync.user_bets.add(user_id)
        
        # Save data to file for cross-process sync
        data_sync.save_data()
        
        print(f"Bet placed successfully, new balance: {data_sync.user_balances[user_id]}")
        
        return jsonify({
            'success': True,
            'new_balance': data_sync.user_balances[user_id],
            'message': 'Ставка принята!'
        })
    except ValueError as e:
        print(f"ValueError in place_bet: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"Unexpected error in place_bet: {e}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/settings', methods=['GET'])
def get_current_game_settings():
    """Get current game settings (teams, coefficients, etc.)"""
    settings = get_current_settings()
    teams = settings['teams']
    coefficients = settings['coefficients']
    exchange_rates = settings['exchange_rates']
    team_emojis = settings['team_emojis']
    
    team1 = teams['team1']
    team2 = teams['team2']
    
    # Get coefficients by team key and name
    team1_coef = coefficients.get('team1') or coefficients.get(team1, 1.5)
    team2_coef = coefficients.get('team2') or coefficients.get(team2, 2.0)
    
    return jsonify({
        'teams': {
            'team1': team1,
            'team2': team2
        },
        'coefficients': {
            team1: team1_coef,
            team2: team2_coef
        },
        'team_emojis': {
            team1: team_emojis.get(team1, '🧑‍💼'),
            team2: team_emojis.get(team2, '🦅'),
            'team1': team_emojis.get(team1, '🧑‍💼'),
            'team2': team_emojis.get(team2, '🦅')
        },
        'exchange_rates': exchange_rates
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get betting statistics"""
    data_sync.reload_data()
    total_bets = len(data_sync.user_bets)
    total_users = len(data_sync.user_state)
    
    team_stats = {'Sovkamax': 0, 'Faze': 0}
    for state in data_sync.user_state.values():
        if 'team' in state:
            team_stats[state['team']] = team_stats.get(state['team'], 0) + 1
    
    return jsonify({
        'total_bets': total_bets,
        'total_users': total_users,
        'team_stats': team_stats,
        'coefficients': COEFFICIENTS,
        'exchange_rates': EXCHANGE_RATES
    })

@app.route('/api/announce_winner', methods=['POST'])
def announce_winner():
    """Admin function to announce match winner"""
    try:
        request_data = request.get_json()
        winning_team = request_data.get('winning_team')
        
        if winning_team not in COEFFICIENTS:
            return jsonify({'success': False, 'error': 'Invalid team'}), 400
        
        # Set match result in shared data
        data_sync.set_match_result(winning_team)
        
        results = []
        
        data_sync.reload_data()  # Get latest data
        for user_id, state in data_sync.user_state.items():
            if 'team' in state and 'bet_uah' in state:
                user_team = state['team']
                bet_amount = state['bet_uah']
                coef = state['coef']
                
                if user_team == winning_team:
                    # User won - add full payout to balance (bet was deducted when placed)
                    winnings = bet_amount * coef
                    data_sync.user_balances[user_id] += winnings
                    
                    print(f"WINNER DEBUG: user_id={user_id}, bet_amount={bet_amount}, coef={coef}, winnings={winnings}, new_balance={data_sync.user_balances[user_id]}")
                    
                    # Store user result
                    data_sync.set_user_result(user_id, {
                        'result': 'win',
                        'winnings': winnings,
                        'balance': data_sync.user_balances[user_id],
                        'winning_team': winning_team,
                        'user_team': user_team
                    })
                    
                    results.append({
                        'user_id': user_id,
                        'result': 'win',
                        'winnings': winnings,
                        'new_balance': data_sync.user_balances[user_id]
                    })
                else:
                    # User lost - money already deducted when bet was placed, no change needed
                    print(f"LOSER DEBUG: user_id={user_id}, bet_amount={bet_amount}, current_balance={data_sync.user_balances[user_id]}")
                    
                    # Store user result
                    data_sync.set_user_result(user_id, {
                        'result': 'lose',
                        'lost': bet_amount,
                        'balance': data_sync.user_balances[user_id],
                        'winning_team': winning_team,
                        'user_team': user_team
                    })
                    
                    results.append({
                        'user_id': user_id,
                        'result': 'lose',
                        'lost': bet_amount,
                        'new_balance': data_sync.user_balances[user_id]
                    })
        
        # Save all changes to file
        data_sync.save_data()
        
        return jsonify({
            'success': True,
            'winning_team': winning_team,
            'results': results
        })
    except Exception as e:
        print(f"Error in announce_winner: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/check_result', methods=['POST'])
def check_result():
    """Check result for specific user"""
    try:
        request_data = request.get_json()
        user_id = request_data.get('user_id')
        
        # Check if user has a stored result from previous match
        user_result = data_sync.get_user_result(user_id)
        if user_result:
            print(f"Found stored result for user {user_id}: {user_result}")
            return jsonify(user_result)
        
        # Reload data to get latest state
        data_sync.reload_data()
        
        # Check if user has an active bet
        if user_id not in data_sync.user_state:
            return jsonify({'result': 'no_bet'})
        
        # Check if match result has been announced for current bet
        winner = data_sync.get_match_result()
        if winner is None:
            return jsonify({
                'result': 'pending',
                'balance': data_sync.user_balances.get(user_id, 0.0)
            })
        
        # Match has been decided, calculate result based on user's bet
        user_state_data = data_sync.user_state[user_id]
        user_team = user_state_data['team']
        bet_amount = user_state_data.get('bet_uah', 0)
        coef = user_state_data.get('coef', 1.0)
        
        if user_team == winner:
            # User won - add full payout to balance (bet was already deducted when placed)
            total_payout = bet_amount * coef
            data_sync.user_balances[user_id] += total_payout
            
            result_data = {
                'result': 'win',
                'balance': data_sync.user_balances[user_id],
                'winnings': total_payout,
                'winning_team': winner,
                'user_team': user_team
            }
        else:
            # User lost - money already deducted when bet was placed, no change needed
            result_data = {
                'result': 'lose',
                'balance': data_sync.user_balances[user_id],
                'lost': bet_amount,
                'winning_team': winner,
                'user_team': user_team
            }
        
        # Save updated balance to file
        data_sync.save_data()
        
        # Store the result for future checks
        data_sync.set_user_result(user_id, result_data)
        print(f"Calculated and stored result for user {user_id}: {result_data}")
        
        return jsonify(result_data)
    except Exception as e:
        print(f"Error in check_result: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deposit', methods=['POST'])
def deposit_balance():
    """Add balance to user account"""
    try:
        request_data = request.get_json()
        user_id = str(request_data.get('user_id'))
        amount = float(request_data.get('amount', 0))
        
        print(f"DEPOSIT DEBUG: user_id={user_id}, amount={amount}")
        
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Сумма должна быть больше 0'}), 400
            
        if amount > 10000:
            return jsonify({'success': False, 'error': 'Максимальная сумма пополнения: 10,000 UAH'}), 400
            
        # Reload data first
        data_sync.reload_data()
        
        # Get current balance BEFORE any operations
        current_balance = data_sync.user_balances.get(user_id, 0.0)
        print(f"DEPOSIT DEBUG: current_balance before operations = {current_balance}")
        
        # Add deposit amount to existing balance (correct logic)
        new_balance = current_balance + amount
        data_sync.user_balances[user_id] = new_balance
        
        print(f"DEPOSIT DEBUG: added {amount} to {current_balance}, new balance = {new_balance}")
        
        # Check balance limit after adding deposit
        if new_balance > 500000:
            return jsonify({'success': False, 'error': f'Превышен лимит баланса (500,000 UAH). Текущий баланс: {current_balance:.2f}, максимальное пополнение: {500000 - current_balance:.2f}'}), 400
        
        # Clear any old match data for fresh start
        data_sync.reset_user_after_match(user_id)
        
        # Save the new balance
        data_sync.save_data()
        
        print(f"DEPOSIT DEBUG: Balance set for user {user_id}: {new_balance} UAH")
        
        return jsonify({
            'success': True,
            'new_balance': new_balance,
            'deposited': amount,
            'message': f'Баланс пополнен на {amount} UAH'
        })
    except ValueError:
        return jsonify({'success': False, 'error': 'Неверная сумма'}), 400
    except Exception as e:
        print(f"DEPOSIT ERROR: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for anti-sleep system"""
    try:
        data_sync.reload_data()
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            'status': 'healthy',
            'timestamp': current_time,
            'users': len(data_sync.user_balances),
            'active_bets': len(data_sync.user_bets),
            'match_result': data_sync.match_result,
            'uptime': 'active'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/ping', methods=['GET'])
def uptime_robot_ping():
    """Simple ping endpoint for UptimeRobot monitoring"""
    return "OK", 200

@app.route('/status', methods=['GET'])
def bot_status():
    """Bot status endpoint for external monitoring"""
    try:
        data_sync.reload_data()
        return f"CS2 Betting Bot is running. Users: {len(data_sync.user_balances)}, Active bets: {len(data_sync.user_bets)}", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)