"""
Portfolio Dashboard Module
Provides portfolio visualization and performance tracking functionality.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
from ibkr_api import Portfolio, Position, IBKRAPIClient


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    total_value: float
    cash: float
    invested_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    return_percentage: float
    positions_count: int
    largest_position: Optional[Position] = None
    largest_gain: Optional[Position] = None
    largest_loss: Optional[Position] = None


class PortfolioDashboard:
    """
    Portfolio dashboard for visualization and analysis of trading performance.
    
    Provides methods to:
    - Display portfolio summary
    - Visualize portfolio allocation
    - Track performance metrics
    - Generate reports
    """
    
    def __init__(self, ibkr_client: IBKRAPIClient):
        """
        Initialize portfolio dashboard.
        
        Args:
            ibkr_client: IBKR API client instance
        """
        self.ibkr_client = ibkr_client
        self.portfolio_history = []
        
    async def get_portfolio_summary(self) -> PortfolioMetrics:
        """
        Get comprehensive portfolio summary.
        
        Returns:
            PortfolioMetrics object with key metrics
        """
        portfolio = await self.ibkr_client.get_portfolio()
        
        if not portfolio.positions:
            return PortfolioMetrics(
                total_value=portfolio.cash,
                cash=portfolio.cash,
                invested_value=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                total_pnl=0.0,
                return_percentage=0.0,
                positions_count=0
            )
        
        # Calculate metrics
        invested_value = sum(abs(pos.market_value) for pos in portfolio.positions)
        total_pnl = portfolio.unrealized_pnl + portfolio.realized_pnl
        
        # Calculate return percentage
        if invested_value > 0:
            return_percentage = (total_pnl / invested_value) * 100
        else:
            return_percentage = 0.0
        
        # Find largest position, gain, and loss
        largest_position = max(portfolio.positions, key=lambda p: abs(p.market_value)) if portfolio.positions else None
        largest_gain = max(portfolio.positions, key=lambda p: p.unrealized_pnl) if portfolio.positions else None
        largest_loss = min(portfolio.positions, key=lambda p: p.unrealized_pnl) if portfolio.positions else None
        
        return PortfolioMetrics(
            total_value=portfolio.total_value,
            cash=portfolio.cash,
            invested_value=invested_value,
            unrealized_pnl=portfolio.unrealized_pnl,
            realized_pnl=portfolio.realized_pnl,
            total_pnl=total_pnl,
            return_percentage=return_percentage,
            positions_count=len(portfolio.positions),
            largest_position=largest_position,
            largest_gain=largest_gain,
            largest_loss=largest_loss
        )
    
    async def display_portfolio_summary(self):
        """Display a comprehensive portfolio summary."""
        metrics = await self.get_portfolio_summary()
        
        print("=" * 60)
        print("PORTFOLIO SUMMARY")
        print("=" * 60)
        
        print(f"Total Portfolio Value: ${metrics.total_value:,.2f}")
        print(f"Cash Available: ${metrics.cash:,.2f}")
        print(f"Invested Value: ${metrics.invested_value:,.2f}")
        print(f"Number of Positions: {metrics.positions_count}")
        
        print("\nPERFORMANCE METRICS")
        print("-" * 30)
        print(f"Unrealized P&L: ${metrics.unrealized_pnl:,.2f}")
        print(f"Realized P&L: ${metrics.realized_pnl:,.2f}")
        print(f"Total P&L: ${metrics.total_pnl:,.2f}")
        print(f"Return Percentage: {metrics.return_percentage:.2f}%")
        
        if metrics.largest_position:
            print(f"\nLargest Position: {metrics.largest_position.symbol} "
                  f"(${abs(metrics.largest_position.market_value):,.2f})")
        
        if metrics.largest_gain:
            print(f"Best Performer: {metrics.largest_gain.symbol} "
                  f"(+${metrics.largest_gain.unrealized_pnl:,.2f})")
        
        if metrics.largest_loss:
            print(f"Worst Performer: {metrics.largest_loss.symbol} "
                  f"(${metrics.largest_loss.unrealized_pnl:,.2f})")
        
        print("=" * 60)
    
    async def display_positions_table(self):
        """Display detailed positions table."""
        portfolio = await self.ibkr_client.get_portfolio()
        
        if not portfolio.positions:
            print("No positions currently held.")
            return
        
        # Create DataFrame for better formatting
        positions_data = []
        for pos in portfolio.positions:
            positions_data.append({
                'Symbol': pos.symbol,
                'Quantity': pos.quantity,
                'Avg Cost': f"${pos.avg_cost:.2f}",
                'Market Price': f"${pos.market_price:.2f}",
                'Market Value': f"${pos.market_value:,.2f}",
                'Unrealized P&L': f"${pos.unrealized_pnl:,.2f}",
                'Return %': f"{(pos.unrealized_pnl / abs(pos.market_value - pos.unrealized_pnl) * 100):.2f}%"
            })
        
        df = pd.DataFrame(positions_data)
        print("\nPOSITIONS DETAIL")
        print("-" * 80)
        print(df.to_string(index=False))
        print("-" * 80)
    
    async def plot_portfolio_allocation(self, save_path: Optional[str] = None):
        """
        Plot portfolio allocation pie chart.
        
        Args:
            save_path: Optional path to save the plot
        """
        portfolio = await self.ibkr_client.get_portfolio()
        
        if not portfolio.positions:
            print("No positions to plot.")
            return
        
        # Prepare data for pie chart
        symbols = []
        values = []
        
        for pos in portfolio.positions:
            symbols.append(pos.symbol)
            values.append(abs(pos.market_value))
        
        # Add cash as a separate slice if significant
        if portfolio.cash > portfolio.total_value * 0.05:  # Show cash if > 5% of total
            symbols.append('Cash')
            values.append(portfolio.cash)
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(symbols)))
        
        wedges, texts, autotexts = ax.pie(values, labels=symbols, autopct='%1.1f%%',
                                         colors=colors, startangle=90)
        
        ax.set_title('Portfolio Allocation', fontsize=16, fontweight='bold')
        
        # Add value labels
        for i, (wedge, value) in enumerate(zip(wedges, values)):
            angle = (wedge.theta2 + wedge.theta1) / 2
            x = wedge.r * 0.7 * np.cos(np.radians(angle))
            y = wedge.r * 0.7 * np.sin(np.radians(angle))
            ax.text(x, y, f'${value:,.0f}', ha='center', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Portfolio allocation chart saved to {save_path}")
        
        plt.show()
    
    async def plot_performance_chart(self, days: int = 30, save_path: Optional[str] = None):
        """
        Plot portfolio performance over time.
        
        Args:
            days: Number of days to show
            save_path: Optional path to save the plot
        """
        # This is a simplified implementation
        # In a real system, you'd store historical portfolio values
        
        if len(self.portfolio_history) < 2:
            print("Insufficient historical data for performance chart.")
            print("Historical data will be collected over time.")
            return
        
        # Create performance DataFrame
        df = pd.DataFrame(self.portfolio_history)
        df['date'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('date').sort_index()
        
        # Filter to requested days
        end_date = df.index.max()
        start_date = end_date - timedelta(days=days)
        df = df[df.index >= start_date]
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Portfolio value over time
        ax1.plot(df.index, df['total_value'], linewidth=2, color='blue', label='Total Value')
        ax1.fill_between(df.index, df['total_value'], alpha=0.3, color='blue')
        ax1.set_title('Portfolio Value Over Time', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Value ($)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # P&L over time
        ax2.plot(df.index, df['unrealized_pnl'], linewidth=2, color='green', label='Unrealized P&L')
        ax2.plot(df.index, df['realized_pnl'], linewidth=2, color='red', label='Realized P&L')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_title('Profit & Loss Over Time', fontsize=14, fontweight='bold')
        ax2.set_ylabel('P&L ($)')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Performance chart saved to {save_path}")
        
        plt.show()
    
    async def record_portfolio_snapshot(self):
        """Record current portfolio state for historical tracking."""
        portfolio = await self.ibkr_client.get_portfolio()
        
        snapshot = {
            'timestamp': datetime.now(),
            'total_value': portfolio.total_value,
            'cash': portfolio.cash,
            'unrealized_pnl': portfolio.unrealized_pnl,
            'realized_pnl': portfolio.realized_pnl,
            'positions_count': len(portfolio.positions)
        }
        
        self.portfolio_history.append(snapshot)
        
        # Keep only last 1000 snapshots to manage memory
        if len(self.portfolio_history) > 1000:
            self.portfolio_history = self.portfolio_history[-1000:]
    
    async def generate_risk_report(self) -> Dict[str, float]:
        """
        Generate risk metrics report.
        
        Returns:
            Dictionary with risk metrics
        """
        portfolio = await self.ibkr_client.get_portfolio()
        
        if not portfolio.positions:
            return {
                'concentration_risk': 0.0,
                'largest_position_pct': 0.0,
                'positions_at_loss': 0,
                'total_unrealized_loss': 0.0,
                'risk_score': 0.0
            }
        
        # Calculate concentration risk (largest position as % of portfolio)
        largest_position_value = max(abs(pos.market_value) for pos in portfolio.positions)
        concentration_risk = (largest_position_value / portfolio.total_value) * 100
        
        # Count positions at loss
        positions_at_loss = sum(1 for pos in portfolio.positions if pos.unrealized_pnl < 0)
        
        # Total unrealized loss
        total_unrealized_loss = sum(pos.unrealized_pnl for pos in portfolio.positions if pos.unrealized_pnl < 0)
        
        # Simple risk score (0-100, higher = more risky)
        risk_score = 0
        risk_score += min(concentration_risk, 50)  # Up to 50 points for concentration
        risk_score += min(positions_at_loss / len(portfolio.positions) * 30, 30)  # Up to 30 points for losing positions
        if portfolio.total_value > 0:
            risk_score += min(abs(total_unrealized_loss) / portfolio.total_value * 20, 20)  # Up to 20 points for loss magnitude
        
        return {
            'concentration_risk': concentration_risk,
            'largest_position_pct': (largest_position_value / portfolio.total_value) * 100,
            'positions_at_loss': positions_at_loss,
            'total_unrealized_loss': total_unrealized_loss,
            'risk_score': risk_score
        }
    
    async def display_risk_report(self):
        """Display risk analysis report."""
        risk_metrics = await self.generate_risk_report()
        
        print("\nRISK ANALYSIS REPORT")
        print("-" * 40)
        print(f"Concentration Risk: {risk_metrics['concentration_risk']:.1f}%")
        print(f"Largest Position: {risk_metrics['largest_position_pct']:.1f}% of portfolio")
        print(f"Positions at Loss: {risk_metrics['positions_at_loss']}")
        print(f"Total Unrealized Loss: ${risk_metrics['total_unrealized_loss']:,.2f}")
        print(f"Risk Score: {risk_metrics['risk_score']:.1f}/100")
        
        # Risk level interpretation
        if risk_metrics['risk_score'] < 25:
            risk_level = "LOW"
        elif risk_metrics['risk_score'] < 50:
            risk_level = "MODERATE"
        elif risk_metrics['risk_score'] < 75:
            risk_level = "HIGH"
        else:
            risk_level = "VERY HIGH"
        
        print(f"Risk Level: {risk_level}")
        print("-" * 40)
    
    async def export_portfolio_data(self, filename: str = None):
        """
        Export portfolio data to CSV.
        
        Args:
            filename: Optional filename (default: portfolio_YYYYMMDD.csv)
        """
        portfolio = await self.ibkr_client.get_portfolio()
        
        if filename is None:
            filename = f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Prepare data for export
        data = []
        for pos in portfolio.positions:
            data.append({
                'Symbol': pos.symbol,
                'Quantity': pos.quantity,
                'Average_Cost': pos.avg_cost,
                'Market_Price': pos.market_price,
                'Market_Value': pos.market_value,
                'Unrealized_PnL': pos.unrealized_pnl,
                'Realized_PnL': pos.realized_pnl,
                'Export_Date': datetime.now().strftime('%Y-%m-%d'),
                'Export_Time': datetime.now().strftime('%H:%M:%S')
            })
        
        # Add summary row
        data.append({
            'Symbol': 'TOTAL',
            'Quantity': '',
            'Average_Cost': '',
            'Market_Price': '',
            'Market_Value': portfolio.total_value,
            'Unrealized_PnL': portfolio.unrealized_pnl,
            'Realized_PnL': portfolio.realized_pnl,
            'Export_Date': datetime.now().strftime('%Y-%m-%d'),
            'Export_Time': datetime.now().strftime('%H:%M:%S')
        })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Portfolio data exported to {filename}")
    
    async def run_dashboard(self):
        """Run interactive dashboard."""
        print("Portfolio Dashboard")
        print("=" * 50)
        
        while True:
            print("\nAvailable options:")
            print("1. Portfolio Summary")
            print("2. Positions Detail")
            print("3. Portfolio Allocation Chart")
            print("4. Performance Chart")
            print("5. Risk Report")
            print("6. Export Data")
            print("7. Record Snapshot")
            print("8. Exit")
            
            choice = input("\nEnter your choice (1-8): ").strip()
            
            try:
                if choice == '1':
                    await self.display_portfolio_summary()
                elif choice == '2':
                    await self.display_positions_table()
                elif choice == '3':
                    await self.plot_portfolio_allocation()
                elif choice == '4':
                    await self.plot_performance_chart()
                elif choice == '5':
                    await self.display_risk_report()
                elif choice == '6':
                    await self.export_portfolio_data()
                elif choice == '7':
                    await self.record_portfolio_snapshot()
                    print("Portfolio snapshot recorded.")
                elif choice == '8':
                    print("Exiting dashboard...")
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")
            
            input("\nPress Enter to continue...")