"""Sample data for testing and development"""

SAMPLE_USER_DATA = {
    'user_id': '12345',
    'name': 'John Doe',
    'email': 'john@example.com',
    'preferences': {
        'weekly_report': True,
        'eco_tips': True,
        'reminders': True
    },
    'sustainability_data': {
        'electricity': 750,  # kWh per month
        'gas': 30,  # therms per month
        'car_miles': 500,  # miles per month
        'public_transport': 100,  # miles per month
        'diet': 'Meat Weekly'
    }
}

SAMPLE_RECOMMENDATIONS = [
    {
        'category': 'energy',
        'title': 'Switch to LED Bulbs',
        'description': 'Replace traditional bulbs with LED alternatives',
        'potential_impact': 'Reduce electricity usage by 75%'
    },
    {
        'category': 'transportation',
        'title': 'Increase Public Transit Usage',
        'description': 'Try using public transportation for your daily commute',
        'potential_impact': 'Reduce carbon emissions by 50%'
    },
    {
        'category': 'lifestyle',
        'title': 'Start Composting',
        'description': 'Begin composting food scraps and yard waste',
        'potential_impact': 'Reduce waste by 30%'
    }
]

SAMPLE_ECO_TIPS = [
    {
        'title': 'Unplug Idle Electronics',
        'description': 'Many devices draw power even when turned off',
        'impact': 'Save up to 10% on electricity'
    },
    {
        'title': 'Use Reusable Bags',
        'description': 'Bring your own bags for shopping',
        'impact': 'Reduce plastic waste by 50+ bags per year'
    },
    {
        'title': 'Install a Smart Thermostat',
        'description': 'Optimize your home temperature automatically',
        'impact': 'Save up to 15% on heating/cooling costs'
    }
]
