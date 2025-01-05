import optuna
import logging
from datetime import datetime, timedelta
import os

from ..offline_backtest import run_backtest
from ..strategies.rsi_strategy import RSIStrategy

def optimize_rsi_strategy(
    symbols=['BTCUSDT'],
    start_date=None,
    end_date=None,
    n_trials=50,
    study_name='rsi_optimization',
    data_path='\\\\znas\\Main\\spot'
):
    """
    Optimize RSI strategy parameters using Optuna
    
    Args:
        symbols: List of trading pairs to optimize for
        start_date: Start date for backtesting
        end_date: End date for backtesting
        n_trials: Number of optimization trials
        study_name: Name of the optimization study
        data_path: Path to historical data
    """
    def objective(trial):
        # Define the parameter space
        params = {
            'rsi_period': trial.suggest_int('rsi_period', 10, 30),
            'rsi_buy': trial.suggest_int('rsi_buy', 20, 40),
            'rsi_sell': trial.suggest_int('rsi_sell', 60, 80),
            'stop_loss_pct': trial.suggest_float('stop_loss_pct', 0.02, 0.10),
            'btc_size': trial.suggest_float('btc_size', 0.0001, 0.001),
            'eth_size': trial.suggest_float('eth_size', 0.01, 0.1)
        }
        
        try:
            # Run backtest with the trial parameters
            results = run_backtest(
                strategy=RSIStrategy,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                timeframe='15m',
                initial_cash=200000,
                commission=0.0015,
                plot=False,
                use_local_data=True,
                data_path=data_path,
                **params
            )
            
            # Get the first strategy instance (we only use one)
            strategy = results[0]
            
            # Calculate metrics for optimization
            portfolio_value = strategy.broker.getvalue()
            roi = (portfolio_value - 200000) / 200000
            sharpe = strategy.analyzers.sharpe.get_analysis()['sharperatio']
            drawdown = strategy.analyzers.drawdown.get_analysis()['max']['drawdown']
            
            # Log trial results
            logging.info(f"Trial {trial.number}:")
            logging.info(f"Parameters: {params}")
            logging.info(f"ROI: {roi:.2%}")
            logging.info(f"Sharpe Ratio: {sharpe:.2f}")
            logging.info(f"Max Drawdown: {drawdown:.2%}")
            
            # Return a composite score (you can adjust the weights)
            score = roi * 0.4 + sharpe * 0.4 - (drawdown/100) * 0.2
            return score
            
        except Exception as e:
            logging.error(f"Error in trial {trial.number}: {str(e)}")
            return float('-inf')  # Return worst possible score on error
    
    # Create study directory
    os.makedirs('optimize/studies', exist_ok=True)
    
    # Set up the study
    study = optuna.create_study(
        study_name=study_name,
        direction="maximize",
        storage=f"sqlite:///optimize/studies/{study_name}.db",
        load_if_exists=True
    )
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'optimize/studies/{study_name}.log'),
            logging.StreamHandler()
        ]
    )
    
    # Run optimization
    logging.info(f"Starting optimization study: {study_name}")
    logging.info(f"Symbols: {symbols}")
    logging.info(f"Date range: {start_date} to {end_date}")
    
    study.optimize(objective, n_trials=n_trials)
    
    # Log best results
    logging.info("\n=== Optimization Results ===")
    logging.info(f"Best trial: #{study.best_trial.number}")
    logging.info(f"Best score: {study.best_trial.value:.4f}")
    logging.info("Best parameters:")
    for param, value in study.best_trial.params.items():
        logging.info(f"    {param}: {value}")
    
    return study

if __name__ == '__main__':
    # Example usage
    study = optimize_rsi_strategy(
        symbols=['BTCUSDT', 'ETHUSDT'],
        start_date='2024-01-01',
        end_date='2024-02-01',
        n_trials=50,
        study_name=f'rsi_opt_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    )
