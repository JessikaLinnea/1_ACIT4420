Smart Fitness Session Analyzer — Option A
How to run

Make sure all three Python files are in the same folder, then run:

python3 run_generated_scenarios.py

The program will run all the scenarios from data_generator.py and print the results.

How it works

The program analyzes fitness data such as heart rate, skin response, temperature, and activity level.

It uses classes for the participant, their normal reference measurements, observations, and the fitness session. Each observation is checked before being used. If a reading is missing data or has an invalid value, it is rejected and the reason is saved.

The valid readings are then analyzed and compared with the participant's normal values. The session is classified as resting, moderate activity, high activity, recovering, or insufficient data.

Five scenarios are tested: resting, moderate activity, high activity, recovery, and poor quality. The poor-quality scenario gives insufficient data because the readings are invalid.
