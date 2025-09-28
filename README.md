# EcoAgent - Environmental Sustainability Tracker

EcoAgent is a comprehensive web application designed to help users track and visualize their environmental impact through monitoring utilities consumption, transportation usage, and other sustainability metrics.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-green.svg)
![Flask](https://img.shields.io/badge/flask-latest-green.svg)

## Features

- 📊 **Comprehensive Dashboard**: View your environmental impact metrics at a glance
- 📈 **Data Analytics**: Interactive charts and graphs showing consumption trends
- 🚗 **Transportation Tracking**: Monitor both personal vehicle and public transit usage
- ⚡ **Utility Monitoring**: Track electricity, gas, and water consumption
- 🔐 **Secure Authentication**: Powered by Auth0 for robust user management
- 📱 **Responsive Design**: Fully functional on both desktop and mobile devices

## Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite
- **Authentication**: Auth0
- **Visualization**: Plotly.js
- **Deployment**: Render

## Getting Started

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- A modern web browser

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/IchoTM/MHacks25.git
   cd MHacks25
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   Create a `.env` file in the root directory and add:
   ```
   AUTH0_CLIENT_ID=your_client_id
   AUTH0_CLIENT_SECRET=your_client_secret
   AUTH0_DOMAIN=your_domain
   ```

5. Initialize the database
   ```bash
   python database.py
   ```

6. Run the application
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:8501`

## Features in Detail

### Dashboard
- Overview of current consumption metrics
- Comparison with previous periods
- Environmental impact summaries

### Data Entry
- Easy-to-use forms for entering consumption data
- Support for multiple utility types
- Transportation usage tracking

### Analytics
- Interactive graphs showing consumption trends
- Monthly, quarterly, and yearly comparisons
- Environmental impact calculations

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built during MHacks 25
- Thanks to all contributors and participants
- Special thanks to the MHacks organizing team

## Contact

- Project Link: [https://github.com/IchoTM/MHacks25](https://github.com/IchoTM/MHacks25)
