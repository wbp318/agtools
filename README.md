# AgTools Climate Adaptation

AgTools Climate Adaptation is a user-friendly application designed to help farmers in the Southern United States (particularly Louisiana, Arkansas, and Mississippi) adapt their agricultural practices to changing climate conditions. By leveraging machine learning techniques, this tool provides personalized recommendations for crop adaptations based on local climate data and farm characteristics.

## Features

- Interactive GUI for easy data input and visualization
- Machine learning model for predicting suitable climate adaptation strategies
- Support for both manual data entry and CSV file upload
- Customizable for different crops and soil types
- Built with Python, utilizing scikit-learn for machine learning and PyQt5 for the graphical interface

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/YourUsername/agtools-climate-adaptation.git
   cd agtools-climate-adaptation
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # On Windows
   source venv/bin/activate     # On macOS and Linux
   ```

3. Install the required packages:
   ```
   pip install pandas numpy scikit-learn PyQt5
   ```

## Usage

1. Generate sample data (optional):
   ```
   python generate_sample_csv.py
   ```

2. Run the main application:
   ```
   python climate_adaptation_gui.py
   ```

3. Use the GUI to:
   - Load your own CSV data or the generated sample data
   - Input specific farm conditions
   - Receive climate adaptation recommendations

## Data Format

If you're using your own CSV file, ensure it has the following columns:
- temperature (°F)
- rainfall (inches)
- soil_type (clay, loam, or sandy)
- current_crop
- recommended_adaptation

## Contributing

Contributions to improve AgTools Climate Adaptation are welcome. Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the agricultural communities of Louisiana, Arkansas, and Mississippi for inspiring this project.
- Special thanks to the open-source community for the tools and libraries that made this project possible.