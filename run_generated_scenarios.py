from data_generator import available_scenarios, generate_fitness_data
from fitness_session_analyzer import FitnessSession, Participant, ReferenceMeasurements, report


# Create a participant with their baseline measurements.
def build_participant(profile):
    reference = ReferenceMeasurements(
        profile["baseline_heart_rate"],
        profile["baseline_skin_response"],
        profile["baseline_temperature"],
    )
    return Participant(profile["participant_id"], reference)


# Generate and analyze one fitness scenario.
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


# Run all available scenarios.
def main():
    for scenario in available_scenarios():
        run_scenario(scenario)


if __name__ == "__main__":
    main()
