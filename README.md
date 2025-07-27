# Food recommendation agent

This project implements an Agentic AI-powered restaurant ordering assistant that provides user with personalized recommendations which align with users' nutritional needs and preferences.

Key Features:
- Health Data Integration: Collects and analyzes user health metrics (age, gender, BMI, blood pressure, dietary restrictions, etc.) to provide personalized meal recommendations
- User Preference Customization: Allows users to set dietary goals, cuisine preferences, and budget ranges for tailored recommendations
- Interactive Interface: Features a modern chat interface with styled message bubbles for natural conversation, plus a dedicated health & preferences tab for easy profile management
- Health & Preference-Aware Recommendations: Provides intelligent dish suggestions based on nutritional needs and user preferences, with clear price breakdowns including tax and tips
- Visual Previews: Generates AI-powered images of recommended dishes to help users visualize their potential meals
- Health Guidance: Offers personalized health advice to support informed menu choices as well as assisting user to make additional orders


Notes
- The project uses AutoGen for agent build
- The agent uses Selenium for web automation
- Health data is stored in CSV format
- The UI is built using Streamlit

## Setup

1. Clone the repository
2. Setup miniconda with python 3.12
   ```bash
   conda create --name what_to_eat python=3.12
   conda activate restaurant_ordering_helper
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   export OPENAI_API_KEY=xxx
   ```
5. Install Chrome Browser and ChromeDriver
   - Ensure that the Chrome browser is installed on your system.
   - Install ChromeDriver, which is required for Selenium-based implementations. 
     - Make sure the version of ChromeDriver is compatible with your installed version of Chrome.
     - To check your Chrome version, you can refer to [this guide](https://www.google.com/search?q=how+to+find+chrome+version).
     - Download the appropriate version of ChromeDriver from [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/).
     - After downloading, replace the existing ChromeDriver in your project directory with the new one.
   - If applicable, ensure you have the appropriate API keys for any cloud services you plan to use.
   - After placing the ChromeDriver in the correct directory, run the following command in your terminal to make it executable:
     ```bash
     chmod +x chromedriver
     ```

6. Install Tesseract OCR (required for menu processing):
   - On macOS: `brew install tesseract`
   - On Ubuntu: `sudo apt-get install tesseract-ocr`
   - On Windows: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

7. Run the application:
   ```bash
   pip install .
   streamlit run src/ui/app.py
   ```

### Debug note
1. If you run into path error when initializing streamlit, try the following:
   a. Navigate the WHAT2EAT_AI_AGENT folder
   b. run "export PYTHONPATH=$(pwd):$PYTHONPATH"

## Project Structure
```
src/
├── agent/
│   ├── agent.py              # Main agent implementation
│   └── tools/                # Tool implementations
│       ├── __init__.py       # Tool exports
│       ├── browser.py        # Browser automation tool
│       ├── find_menu_on_doordash.py  # DoorDash menu search tool
│       ├── locate_restaurant.py      # Restaurant location search tool
│       ├── normalize_menu.py         # Menu normalization tool
│       ├── restaurant_menu.py        # Menu processing tool
│       └── restaurant_recommendations.py  # Recommendations tool
├── utils/                    # Utility functions and helpers
│   ├── constants.py          # Project constants and configurations
│   ├── data_utils.py         # Data processing utilities
│   └── __init__.py
├── data/                     # Data storage and processing
│   ├── health_data.csv      # Sample health data
│   └── __init__.py
└── ui/                       # User interface implementation
    ├── app.py               # Main Streamlit application
    ├── components/          # UI components
    │   ├── display_info.py  # Information display components
    │   ├── existing_user.py # Existing user interface
    │   ├── health_tab.py    # Health data interface
    │   ├── initialize.py    # Initialization components
    │   ├── new_user.py      # New user interface
    │   └── __init__.py
    └── __init__.py
```

## Usage

1. Launch the application using the command above (`streamlit run src/ui/app.py`)
2. Enter your unique ID when prompted, or create a new user profile
3. Setup your user preferences
4. View and update your health & preferences in the "Health & Preferences" tab
5. Use the chat interface to:
   - Search for restaurants by name and location, e.g. I want to eat at Chipotle near 90210.
   - Receive personalized food recommendations
   - Receive customized health advice 
   - Generate dish pictures for preview

## License

This project is licensed under the MIT License with the [Commons Clause](https://commonsclause.com/) restriction.

- You may use, modify, and distribute this project **for non-commercial purposes** only.
- **Commercial use, resale, or offering as a hosted service is prohibited without prior written permission.**
- See the [LICENSE](./LICENSE) file for full terms.

For licensing inquiries, please contact: hhuang2@tepper.cmu.edu






