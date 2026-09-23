# Smart Fitness Session Analyzer — Option A

This program analyzes fitness sensor data and classifies a workout session based on the readings.

## Files

* `fitness_session_analyzer.py` — contains the classes and analysis logic.
* `run_generated_scenarios.py` — runs and tests all scenarios.
* `data_generator.py` — provided by the instructor.

## How to Run

Make sure all three files are in the same folder, then run:

`python3 run_generated_scenarios.py`

## How It Works

The program checks sensor data such as heart rate, skin response, temperature, and activity level. Invalid readings are rejected and the reason is saved.

Valid readings are compared with the participant's normal measurements. The program then classifies the session as:

* Resting
* Moderate activity
* High activity
* Recovering
* Insufficient data

The program tests all five scenarios provided by the data generator. The poor-quality scenario gives **insufficient data** because its readings are invalid.
