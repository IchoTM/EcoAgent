from uagents import Agent, Context, Model
from typing import Optional
from datetime import datetime

class EcoAlert(Model):
    consumption: float
    timestamp: str
    alert_type: str
    message: str

# Create the EcoMonitor agent
eco_monitor = Agent(
    name="eco_monitor",
    seed="your-secure-seed"  # Replace with a secure seed
)

@eco_monitor.on_interval(period=3600.0)  # Check every hour
async def monitor_consumption(ctx: Context):
    # Get latest consumption data from your database
    from database import ConsumptionData, get_session
    session = get_session()
    latest_data = session.query(ConsumptionData).order_by(ConsumptionData.timestamp.desc()).first()
    
    if latest_data:
        # Analyze the consumption data
        if latest_data.electricity > 100:  # Threshold value
            alert = EcoAlert(
                consumption=latest_data.electricity,
                timestamp=str(datetime.now()),
                alert_type="high_consumption",
                message="High electricity consumption detected!"
            )
            # Send alert to the dashboard
            ctx.storage.set("latest_alert", alert.dict())

@eco_monitor.on_message(model=EcoAlert)
async def handle_alert(ctx: Context, sender: str, msg: EcoAlert):
    # Process incoming alerts
    ctx.logger.info(f"Received alert from {sender}: {msg.message}")

if __name__ == "__main__":
    eco_monitor.run()
