"""Run the Smart Fitness Session Analyzer against the instructor-supplied
data generator, covering every scenario it can produce."""

from data_generator import available_scenarios, generate_fitness_data
from fitness_session_analyzer import FitnessSession, Participant, ReferenceMeasurements, report


# Turn a generator profile dict into our Participant + ReferenceMeasurements objects.
def build_participant(profile):
    reference = ReferenceMeasurements(
        profile["baseline_heart_rate"],
        profile["baseline_skin_response"],
        profile["baseline_temperature"],
    )
    return Participant(profile["participant_id"], reference)


# Generate one scenario's data, run it through the analyzer, and print the report.
def run_scenario(scenario, seed=42, number_of_windows=12):
    profile, observations = generate_fitness_data(
        participant_id="P001",
        scenario=scenario,
        seed=seed,
        number_of_windows=number_of_windows,
    )
    session = FitnessSession(build_participant(profile), scenario)
    for observation in observations:
        session.add(observation)
    report(session.analyse())


def main():
    for scenario in available_scenarios():
        run_scenario(scenario)


if __name__ == "__main__":
    main()