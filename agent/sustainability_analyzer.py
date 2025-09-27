import pandas as pd
import numpy as np
from typing import Dict, Any

class SustainabilityAnalyzer:
    def __init__(self):
        # Constants for calculations
        self.ELECTRICITY_CO2_PER_KWH = 0.92  # lbs CO2 per kWh
        self.GAS_CO2_PER_THERM = 11.7  # lbs CO2 per therm
        self.CAR_CO2_PER_MILE = 0.404  # lbs CO2 per mile
        self.PUBLIC_TRANSPORT_CO2_PER_MILE = 0.14  # lbs CO2 per mile
        
        # National averages (monthly)
        self.AVG_ELECTRICITY = 877  # kWh per household
        self.AVG_GAS = 63  # therms per household
        self.AVG_WATER = 7000  # gallons per household
        self.AVG_CAR_MILES = 1000  # miles
        self.AVG_PUBLIC_TRANSPORT = 150  # miles
        
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sustainability data and return metrics"""
        # Calculate percentiles and comparisons
        electricity_percentile = self._calculate_percentile(
            data.get('electricity', 0), self.AVG_ELECTRICITY, 200
        )
        water_percentile = self._calculate_percentile(
            data.get('water', 0), self.AVG_WATER, 2000
        )
        transport_percentile = self._calculate_percentile(
            data.get('car_miles', 0), self.AVG_CAR_MILES, 300
        )
        
        results = {
            'carbon_footprint': self._calculate_carbon_footprint(data),
            'energy_score': self._calculate_energy_score(data),
            'comparative_metrics': {
                'electricity': {
                    'value': data.get('electricity', 0),
                    'vs_average': (data.get('electricity', 0) - self.AVG_ELECTRICITY) / self.AVG_ELECTRICITY * 100,
                    'percentile': electricity_percentile
                },
                'water': {
                    'value': data.get('water', 0),
                    'vs_average': (data.get('water', 0) - self.AVG_WATER) / self.AVG_WATER * 100,
                    'percentile': water_percentile
                },
                'transportation': {
                    'car_miles': {
                        'value': data.get('car_miles', 0),
                        'vs_average': (data.get('car_miles', 0) - self.AVG_CAR_MILES) / self.AVG_CAR_MILES * 100,
                        'percentile': transport_percentile
                    },
                    'public_transport': {
                        'value': data.get('public_transport', 0),
                        'vs_average': (data.get('public_transport', 0) - self.AVG_PUBLIC_TRANSPORT) / self.AVG_PUBLIC_TRANSPORT * 100
                    }
                }
            },
            'recommendations': self._generate_recommendations(data)
        }
        return results
    
    def _calculate_percentile(self, value: float, average: float, std_dev: float) -> float:
        """Calculate the percentile of a value relative to a normal distribution"""
        from scipy.stats import norm
        z_score = (value - average) / std_dev
        return norm.cdf(z_score) * 100
    
    def _calculate_carbon_footprint(self, data: Dict[str, Any]) -> float:
        """Calculate total carbon footprint in tons CO2"""
        total_co2 = 0
        
        # Energy usage
        if 'electricity' in data:
            total_co2 += data['electricity'] * self.ELECTRICITY_CO2_PER_KWH
        if 'gas' in data:
            total_co2 += data['gas'] * self.GAS_CO2_PER_THERM
            
        # Transportation
        if 'car_miles' in data:
            total_co2 += data['car_miles'] * self.CAR_CO2_PER_MILE
        if 'public_transport' in data:
            total_co2 += data['public_transport'] * self.PUBLIC_TRANSPORT_CO2_PER_MILE
            
        # Diet impact (rough estimates)
        diet_multipliers = {
            'Meat Daily': 1.0,
            'Meat Weekly': 0.8,
            'Vegetarian': 0.6,
            'Vegan': 0.4
        }
        if 'diet' in data:
            total_co2 *= diet_multipliers.get(data['diet'], 1.0)
            
        # Convert from lbs to tons
        return total_co2 / 2000
    
    def _calculate_energy_score(self, data: Dict[str, Any]) -> int:
        """Calculate energy efficiency score (0-100)"""
        score = 100
        
        # Compare to national averages
        if 'electricity' in data:
            elec_ratio = data['electricity'] / self.AVG_ELECTRICITY
            score -= max(0, min(30, int(30 * (elec_ratio - 1))))
        
        if 'gas' in data:
            gas_ratio = data['gas'] / self.AVG_GAS
            score -= max(0, min(20, int(20 * (gas_ratio - 1))))
        
        if 'water' in data:
            water_ratio = data['water'] / self.AVG_WATER
            score -= max(0, min(20, int(20 * (water_ratio - 1))))
        
        # Transportation impact
        if 'car_miles' in data and 'public_transport' in data:
            transport_ratio = data['public_transport'] / (data['car_miles'] + 0.1)
            if transport_ratio > 0.5:  # Rewards high public transport usage
                score += min(10, int(10 * transport_ratio))
        
        # Diet impact
        diet_scores = {
            'Vegan': 10,
            'Vegetarian': 7,
            'Meat Weekly': 3,
            'Meat Daily': 0
        }
        if 'diet' in data:
            score += diet_scores.get(data['diet'], 0)
        
        return max(0, min(100, score))
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> list:
        """Generate personalized sustainability recommendations"""
        recommendations = []
        
        # Energy recommendations based on comparative analysis
        if data.get('electricity', 0) > self.AVG_ELECTRICITY:
            potential_savings = (data['electricity'] - self.AVG_ELECTRICITY) * 0.12  # Assuming $0.12 per kWh
            recommendations.append({
                'category': 'energy',
                'title': 'Reduce Electricity Usage',
                'description': f'Your electricity usage is {((data["electricity"]/self.AVG_ELECTRICITY)-1)*100:.1f}% above average.',
                'actions': [
                    'Switch to LED bulbs (saves up to 75% on lighting)',
                    'Use smart power strips for electronics',
                    'Upgrade to Energy Star appliances',
                    'Install a programmable thermostat'
                ],
                'potential_impact': f'Save approximately ${potential_savings:.2f} monthly and reduce CO2 emissions by {(data["electricity"] - self.AVG_ELECTRICITY) * self.ELECTRICITY_CO2_PER_KWH / 2000:.1f} tons'
            })
            
        # Water conservation recommendations
        if data.get('water', 0) > self.AVG_WATER:
            recommendations.append({
                'category': 'water',
                'title': 'Reduce Water Consumption',
                'description': f'Your water usage is {((data["water"]/self.AVG_WATER)-1)*100:.1f}% above average.',
                'actions': [
                    'Install low-flow showerheads and faucet aerators',
                    'Fix leaky faucets and pipes',
                    'Collect rainwater for gardening',
                    'Run full loads of laundry and dishes'
                ],
                'potential_impact': f'Potential savings of {(data["water"] - self.AVG_WATER) * 0.01:.2f} gallons monthly'  # Assuming $0.01 per gallon
            })
            
        # Transportation recommendations
        if data.get('car_miles', 0) > self.AVG_CAR_MILES:
            recommendations.append({
                'category': 'transportation',
                'title': 'Optimize Transportation',
                'description': f'Your car usage is {((data["car_miles"]/self.AVG_CAR_MILES)-1)*100:.1f}% above average.',
                'actions': [
                    'Consider carpooling options',
                    'Use public transportation when possible',
                    'Combine errands into single trips',
                    'Consider an electric or hybrid vehicle'
                ],
                'potential_impact': f'Reduce CO2 emissions by {(data["car_miles"] - self.AVG_CAR_MILES) * self.CAR_CO2_PER_MILE / 2000:.1f} tons monthly'
            })
            
        # Diet-based recommendations
        if data.get('diet') == 'Meat Daily':
            recommendations.append({
                'category': 'lifestyle',
                'title': 'Consider Plant-Based Meals',
                'description': 'Regular meat consumption has a significant environmental impact.',
                'actions': [
                    'Start with Meatless Mondays',
                    'Explore plant-based protein alternatives',
                    'Reduce red meat consumption',
                    'Choose local and seasonal produce'
                ],
                'potential_impact': 'Reduce your dietary carbon footprint by up to 30%'
            })
            
        return recommendations
