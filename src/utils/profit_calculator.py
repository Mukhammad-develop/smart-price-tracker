from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProfitCalculator:
    """Calculate profit margins and fees for different e-commerce platforms"""
    
    def __init__(self):
        # Platform fee structures (as of 2024)
        self.platform_fees = {
            'amazon': {
                'referral_fee_rate': 0.15,  # 15% average referral fee
                'fba_fee_base': 2.50,       # Base FBA fee
                'fba_fee_per_pound': 0.50,  # Per pound after first pound
                'monthly_storage_fee': 0.75, # Per cubic foot per month
                'long_term_storage_fee': 6.90, # Per cubic foot (6+ months)
                'closing_fee': 1.80,        # Per item (media categories)
                'high_volume_listing_fee': 0.05, # If >100k listings
                'return_processing_fee': 3.00,
            },
            'ebay': {
                'final_value_fee_rate': 0.125, # 12.5% average
                'insertion_fee': 0.30,         # Per listing
                'optional_listing_upgrade': 0.50,
                'paypal_fee_rate': 0.029,      # 2.9% + $0.30
                'paypal_fee_fixed': 0.30,
                'promoted_listing_fee_rate': 0.02, # 2-12%
            },
            'walmart': {
                'referral_fee_rate': 0.15,     # 15% average
                'fulfillment_fee': 3.00,       # Average per item
                'return_fee': 2.00,            # Per returned item
                'advertising_fee_rate': 0.05,  # 5% of sales (optional)
            },
            'aliexpress': {
                'commission_rate': 0.05,       # 5-8% commission
                'payment_fee_rate': 0.03,      # 3% payment processing
                'promotion_fee_rate': 0.02,    # 2% promotion fee (optional)
            }
        }
    
    def calculate_amazon_fees(self, selling_price: float, cost_price: float, 
                             weight_lbs: float = 1.0, dimensions_cf: float = 0.1,
                             is_fba: bool = True, category: str = 'general') -> Dict[str, Any]:
        """Calculate Amazon-specific fees and profit"""
        
        fees = self.platform_fees['amazon']
        
        # Referral fee (varies by category)
        category_rates = {
            'electronics': 0.08,
            'books': 0.15,
            'clothing': 0.17,
            'home': 0.15,
            'toys': 0.15,
            'general': 0.15
        }
        
        referral_rate = category_rates.get(category.lower(), fees['referral_fee_rate'])
        referral_fee = selling_price * referral_rate
        
        total_fees = referral_fee
        fee_breakdown = {'referral_fee': referral_fee}
        
        if is_fba:
            # FBA fulfillment fee
            fba_fee = fees['fba_fee_base']
            if weight_lbs > 1:
                fba_fee += (weight_lbs - 1) * fees['fba_fee_per_pound']
            
            # Storage fees (estimated monthly)
            monthly_storage = dimensions_cf * fees['monthly_storage_fee']
            
            total_fees += fba_fee + monthly_storage
            fee_breakdown.update({
                'fba_fulfillment_fee': fba_fee,
                'monthly_storage_fee': monthly_storage
            })
        
        # Calculate profit metrics
        gross_profit = selling_price - cost_price
        net_profit = selling_price - cost_price - total_fees
        profit_margin = (net_profit / selling_price) * 100 if selling_price > 0 else 0
        roi = (net_profit / cost_price) * 100 if cost_price > 0 else 0
        
        return {
            'platform': 'amazon',
            'selling_price': selling_price,
            'cost_price': cost_price,
            'total_fees': total_fees,
            'fee_breakdown': fee_breakdown,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'profit_margin_percent': profit_margin,
            'roi_percent': roi,
            'break_even_price': cost_price + total_fees if total_fees > 0 else cost_price,
            'is_profitable': net_profit > 0
        }
    
    def calculate_ebay_fees(self, selling_price: float, cost_price: float,
                           is_promoted: bool = False, category: str = 'general') -> Dict[str, Any]:
        """Calculate eBay-specific fees and profit"""
        
        fees = self.platform_fees['ebay']
        
        # Final value fee
        final_value_fee = selling_price * fees['final_value_fee_rate']
        
        # PayPal fees
        paypal_fee = (selling_price * fees['paypal_fee_rate']) + fees['paypal_fee_fixed']
        
        total_fees = final_value_fee + paypal_fee + fees['insertion_fee']
        fee_breakdown = {
            'final_value_fee': final_value_fee,
            'paypal_fee': paypal_fee,
            'insertion_fee': fees['insertion_fee']
        }
        
        if is_promoted:
            promoted_fee = selling_price * fees['promoted_listing_fee_rate']
            total_fees += promoted_fee
            fee_breakdown['promoted_listing_fee'] = promoted_fee
        
        # Calculate profit metrics
        gross_profit = selling_price - cost_price
        net_profit = selling_price - cost_price - total_fees
        profit_margin = (net_profit / selling_price) * 100 if selling_price > 0 else 0
        roi = (net_profit / cost_price) * 100 if cost_price > 0 else 0
        
        return {
            'platform': 'ebay',
            'selling_price': selling_price,
            'cost_price': cost_price,
            'total_fees': total_fees,
            'fee_breakdown': fee_breakdown,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'profit_margin_percent': profit_margin,
            'roi_percent': roi,
            'break_even_price': cost_price + total_fees if total_fees > 0 else cost_price,
            'is_profitable': net_profit > 0
        }
    
    def calculate_walmart_fees(self, selling_price: float, cost_price: float,
                              use_wfs: bool = True) -> Dict[str, Any]:
        """Calculate Walmart-specific fees and profit"""
        
        fees = self.platform_fees['walmart']
        
        # Referral fee
        referral_fee = selling_price * fees['referral_fee_rate']
        
        total_fees = referral_fee
        fee_breakdown = {'referral_fee': referral_fee}
        
        if use_wfs:  # Walmart Fulfillment Services
            fulfillment_fee = fees['fulfillment_fee']
            total_fees += fulfillment_fee
            fee_breakdown['fulfillment_fee'] = fulfillment_fee
        
        # Calculate profit metrics
        gross_profit = selling_price - cost_price
        net_profit = selling_price - cost_price - total_fees
        profit_margin = (net_profit / selling_price) * 100 if selling_price > 0 else 0
        roi = (net_profit / cost_price) * 100 if cost_price > 0 else 0
        
        return {
            'platform': 'walmart',
            'selling_price': selling_price,
            'cost_price': cost_price,
            'total_fees': total_fees,
            'fee_breakdown': fee_breakdown,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'profit_margin_percent': profit_margin,
            'roi_percent': roi,
            'break_even_price': cost_price + total_fees if total_fees > 0 else cost_price,
            'is_profitable': net_profit > 0
        }
    
    def calculate_profit_for_platform(self, platform: str, selling_price: float, 
                                    cost_price: float, **kwargs) -> Dict[str, Any]:
        """Calculate profit for any supported platform"""
        
        platform = platform.lower()
        
        if platform == 'amazon':
            return self.calculate_amazon_fees(selling_price, cost_price, **kwargs)
        elif platform == 'ebay':
            return self.calculate_ebay_fees(selling_price, cost_price, **kwargs)
        elif platform == 'walmart':
            return self.calculate_walmart_fees(selling_price, cost_price, **kwargs)
        else:
            # Generic calculation for unsupported platforms
            return self.calculate_generic_fees(platform, selling_price, cost_price, **kwargs)
    
    def calculate_generic_fees(self, platform: str, selling_price: float, 
                              cost_price: float, fee_rate: float = 0.10) -> Dict[str, Any]:
        """Calculate generic profit with estimated fees"""
        
        total_fees = selling_price * fee_rate
        fee_breakdown = {'platform_fee': total_fees}
        
        gross_profit = selling_price - cost_price
        net_profit = selling_price - cost_price - total_fees
        profit_margin = (net_profit / selling_price) * 100 if selling_price > 0 else 0
        roi = (net_profit / cost_price) * 100 if cost_price > 0 else 0
        
        return {
            'platform': platform,
            'selling_price': selling_price,
            'cost_price': cost_price,
            'total_fees': total_fees,
            'fee_breakdown': fee_breakdown,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'profit_margin_percent': profit_margin,
            'roi_percent': roi,
            'break_even_price': cost_price + total_fees if total_fees > 0 else cost_price,
            'is_profitable': net_profit > 0,
            'note': f'Generic calculation with estimated {fee_rate*100}% fee'
        }
    
    def compare_platforms(self, cost_price: float, selling_prices: Dict[str, float],
                         **platform_kwargs) -> Dict[str, Any]:
        """Compare profit across multiple platforms"""
        
        comparisons = {}
        best_platform = None
        best_profit = float('-inf')
        
        for platform, selling_price in selling_prices.items():
            kwargs = platform_kwargs.get(platform, {})
            profit_data = self.calculate_profit_for_platform(platform, selling_price, cost_price, **kwargs)
            
            comparisons[platform] = profit_data
            
            if profit_data['net_profit'] > best_profit:
                best_profit = profit_data['net_profit']
                best_platform = platform
        
        # Calculate summary statistics
        total_revenue = sum(selling_prices.values())
        avg_profit_margin = sum(comp['profit_margin_percent'] for comp in comparisons.values()) / len(comparisons)
        profitable_platforms = [p for p, comp in comparisons.items() if comp['is_profitable']]
        
        return {
            'comparisons': comparisons,
            'best_platform': best_platform,
            'best_profit': best_profit,
            'total_potential_revenue': total_revenue,
            'average_profit_margin': avg_profit_margin,
            'profitable_platforms': profitable_platforms,
            'analysis_date': datetime.utcnow().isoformat()
        }
    
    def calculate_break_even_analysis(self, cost_price: float, platform: str,
                                    target_profit_margin: float = 20.0, **kwargs) -> Dict[str, Any]:
        """Calculate required selling price for target profit margin"""
        
        # Start with a reasonable selling price estimate
        estimated_selling_price = cost_price * 2  # 100% markup as starting point
        
        # Iterate to find the right selling price
        for _ in range(10):  # Max 10 iterations
            profit_data = self.calculate_profit_for_platform(
                platform, estimated_selling_price, cost_price, **kwargs
            )
            
            current_margin = profit_data['profit_margin_percent']
            
            if abs(current_margin - target_profit_margin) < 0.5:  # Within 0.5%
                break
            
            # Adjust selling price based on difference
            if current_margin < target_profit_margin:
                estimated_selling_price *= 1.1  # Increase by 10%
            else:
                estimated_selling_price *= 0.95  # Decrease by 5%
        
        final_profit_data = self.calculate_profit_for_platform(
            platform, estimated_selling_price, cost_price, **kwargs
        )
        
        return {
            'platform': platform,
            'cost_price': cost_price,
            'target_profit_margin': target_profit_margin,
            'required_selling_price': estimated_selling_price,
            'actual_profit_margin': final_profit_data['profit_margin_percent'],
            'expected_net_profit': final_profit_data['net_profit'],
            'total_fees': final_profit_data['total_fees'],
            'fee_breakdown': final_profit_data['fee_breakdown']
        }
    
    def get_platform_fee_info(self, platform: str) -> Dict[str, Any]:
        """Get fee structure information for a platform"""
        
        platform = platform.lower()
        if platform in self.platform_fees:
            return {
                'platform': platform,
                'fee_structure': self.platform_fees[platform],
                'last_updated': '2024-01-01',
                'note': 'Fees are estimates and may vary by category, volume, and other factors'
            }
        else:
            return {
                'platform': platform,
                'supported': False,
                'note': 'Platform not supported for detailed fee calculation'
            } 