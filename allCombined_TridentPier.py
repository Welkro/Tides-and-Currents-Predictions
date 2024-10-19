import requests 
import time
import pandas as pd
import lightningchart as lc

# Set the license key
lc.set_license("LICENSE_KEY")

# API URLs for the parameters
urls = {
    'wind': 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20241008&end_date=20241012&station=8721604&product=wind&datum=MHHW&time_zone=gmt&units=metric&format=json',
    'air_pressure': 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20241008&end_date=20241012&station=8721604&product=air_pressure&datum=MHHW&time_zone=gmt&units=metric&format=json',
    'water_level': 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20241008&end_date=20241012&station=8721604&product=water_level&datum=MHHW&time_zone=gmt&units=metric&format=json',
    'tide_predictions': 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20241008&end_date=20241012&station=8721604&product=predictions&datum=MHHW&time_zone=gmt&units=metric&format=json',
    'water_temperature': 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20241008&end_date=20241012&station=8721604&product=water_temperature&datum=MHHW&time_zone=gmt&units=metric&format=json',
    'air_temperature': 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=20241008&end_date=20241012&station=8721604&product=air_temperature&datum=MHHW&time_zone=gmt&units=metric&format=json',
}

# Fetch data and store it
data_store = {}
timestamps = []
for param, url in urls.items():
    response = requests.get(url)
    data = response.json()
    
    # Check if the data is under 'data' or 'predictions'
    if 'data' in data:
        data_store[param] = data['data']
    elif 'predictions' in data:
        data_store[param] = data['predictions']
    else:
        print(f"Error: Unexpected structure for {param}. Response: {data}")
        continue

    # Collect all timestamps to find min and max
    for entry in data_store[param]:
        timestamps.append(pd.to_datetime(entry['t']))

# Find the min and max timestamps
min_time = min(timestamps)
max_time = max(timestamps)

# Convert min and max time to milliseconds for X-axis
min_time_ms = min_time.value / 10**6 
max_time_ms = max_time.value / 10**6

# Create the chart
chart = lc.ChartXY(theme=lc.Themes.Dark)

# Set title for the chart
chart.set_title("All Parameters at Trident Pier (Oct 8-12, 2024) - Simulated Real-time")

# Configure X-axis to use DateTime directly and set interval based on min and max time
x_axis = chart.get_default_x_axis()
x_axis.set_tick_strategy('DateTime')
x_axis.set_interval(min_time_ms, max_time_ms)  # Set X-axis interval
x_axis.set_title("Time (GMT)")

# Dispose of the default y-axis to customize with multiple stacked y-axes
chart.get_default_y_axis().dispose()

# Add y-axes with units in their titles
series_list = {}
y_axis_units = {
    'wind': 'Wind (m/s)',
    'air_pressure': 'Pressure (hPa)',
    'water_level': 'Water Lvl (m)',
    'tide_predictions': 'Tide Pred. (m)',
    'water_temperature': 'Water Temp (°C)',
    'air_temperature': 'Air Temp (°C)'
}

for i, (param, _) in enumerate(urls.items()): 
    axis_y = chart.add_y_axis(stack_index=i) # Add a new y-axis for each parameter
    axis_y.set_margins(15 if i > 0 else 0, 15 if i < len(urls) - 1 else 0)   
    axis_y.set_title(y_axis_units[param])  # Add units to the y-axis title
    axis_y.set_interval(0, 1)  # Set initial intervals, update them as data comes in

    # Create a new line series for each y-axis
    series = chart.add_line_series(y_axis=axis_y, data_pattern='ProgressiveX')
    series.set_name(y_axis_units[param])  # Set series name for easy identification
    series_list[param] = series

# Open the live chart
chart.open(live=True)

# Simulate real-time plotting using pre-fetched data
for i in range(len(data_store['wind'])):  # Iterate through the fetched data
    for param, series in series_list.items():
        # Extract the appropriate value for each parameter
        entry = data_store[param][i]
        timestamp = pd.to_datetime(entry['t'])  # Get the timestamp in datetime format
        x_value = timestamp.value / 10**6  # Convert pandas timestamp to milliseconds

        # Handle different parameters based on their field names
        if param == 'wind':
            value_str = entry['s']  # Wind speed uses 's'
        elif param in ['air_pressure', 'water_level', 'tide_predictions', 'water_temperature', 'air_temperature']:
            value_str = entry['v']  # Other parameters use 'v' for value

        # Ensure the value is not empty before converting to float
        if value_str and value_str != '':
            y_value = float(value_str)  # Convert to float only if value is valid

            # Add the new value to the corresponding series
            series.add(x_value, y_value)
        else:
            print(f"Missing or invalid data for {param} at time {timestamp}")

    time.sleep(0.03) # Add a slight delay to simulate real-time plotting