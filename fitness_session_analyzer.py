from statistics import mean

FIELDS = ("timestamp", "heart_rate", "skin_response", "temperature", "activity_level", "signal_quality")


# Check if the sensor data is valid.
def validate(data):
    missing = []
    for field in FIELDS:
        if field not in data:
            missing.append(field)
    if missing:
        return "missing: " + ", ".join(missing)

    for field in FIELDS:
        if not isinstance(data[field], (int, float)):
            return "all values must be numbers"

    if data["timestamp"] < 0:
        return "negative timestamp"
    if not (30 <= data["heart_rate"] <= 230):
        return "invalid heart rate"
    if not (0 <= data["skin_response"] <= 20):
        return "invalid skin response"
    if not (15 <= data["temperature"] <= 45):
        return "invalid temperature"
    if not (0 <= data["activity_level"] <= 1):
        return "invalid activity level"
    if not (0.70 <= data["signal_quality"] <= 1):
        return "poor signal quality"

    return None


# Calculate the average, minimum, and maximum for each measurement.
def summary(readings):
    result = {}

    for field in FIELDS[1:]:
        values = [getattr(reading, field) for reading in readings]

        result[field] = {
            "avg": round(mean(values), 2),
            "min": min(values),
            "max": max(values),
        }

    return result


# Compare session averages with the participant's baseline.
def compare(data, reference):
    result = {}
    for field, baseline in reference.values().items():
        result[field] = round(data[field]["avg"] - baseline, 2)
    return result

# Check if heart rate and activity decrease at the end of the session.
def recovery(readings):
    if len(readings) < 4:
        return False

    section_size = max(1, len(readings) // 3)
    before = readings[-2 * section_size:-section_size]
    end = readings[-section_size:]

    heart_rate_drop = mean(reading.heart_rate for reading in before) - mean(
        reading.heart_rate for reading in end
    )
    activity_drop = mean(reading.activity_level for reading in before) - mean(
        reading.activity_level for reading in end
    )
    return heart_rate_drop >= 8 and activity_drop >= 0.15

    
# Classify the fitness session based on the analyzed data.
def classify(data, diff, is_recovering):
    if is_recovering:
        return "recovering", "heart rate and activity fell near the end"
    if data["activity_level"]["avg"] < 0.20 and diff["heart_rate"] < 15:
        return "resting", "low activity and heart rate close to baseline"
    if data["activity_level"]["avg"] >= 0.65 or diff["heart_rate"] >= 55:
        return "high activity", "high activity or large heart-rate rise"
    return "moderate activity", "activity is above the resting range"


# Store the participant's baseline measurements.
class ReferenceMeasurements:
    def __init__(self, heart_rate, skin_response, temperature):
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature

    @property
    def heart_rate(self):
        return self._heart_rate

    @heart_rate.setter
    def heart_rate(self, value):
        if not 30 <= value <= 150:
            raise ValueError("baseline heart rate must be between 30 and 150")
        self._heart_rate = value

    def values(self):
        return {
            "heart_rate": self.heart_rate,
            "skin_response": self.skin_response,
            "temperature": self.temperature,
        }


# Store the participant and their reference measurements.
class Participant:
    def __init__(self, participant_id, reference):
        self.participant_id = participant_id
        self.reference = reference


# Represents a valid sensor reading.
class Observation:
    def __init__(self, data):
        self.__dict__.update(data)

    @classmethod
    def from_dict(cls, data):
        reason = validate(data)
        if reason:
            return RejectedObservation(reason)
        return cls(data)

    def usable(self):
        return True


# Represents an observation that failed validation.
class RejectedObservation(Observation):
    def __init__(self, reason):
        self.reason = reason

    def usable(self):
        return False


# Store a participant and their fitness observations.
class FitnessSession:
    MIN_READINGS = 3

    def __init__(self, participant, name):
        self.participant = participant
        self.name = name
        self.observations = []

    def add(self, data):
        self.observations.append(Observation.from_dict(data))

    def analyse(self):
        usable = []
        rejected = []

        for observation in self.observations:
            if observation.usable():
                usable.append(observation)
            else:
                rejected.append(observation.reason)

        usable.sort(key=lambda observation: observation.timestamp)

        result = {
            "session": self.name,
            "usable": len(usable),
            "rejected": rejected,
        }

        if len(usable) < self.MIN_READINGS:
            result["classification"] = "insufficient data"
            result["reason"] = "fewer than 3 usable readings"
            result["summary"] = {}
            result["reference_difference"] = {}
            return result

        data = summary(usable)
        difference = compare(data, self.participant.reference)
        is_recovering = recovery(usable)
        label, reason = classify(data, difference, is_recovering)

        result["classification"] = label
        result["reason"] = reason
        result["summary"] = data
        result["reference_difference"] = difference

        return result


# Print the analysis results.
def report(result):
    print(f"\n{result['session']}: {result['classification']}")
    print(f"Usable observations: {result['usable']}")
    print(f"Reason: {result['reason']}")

    if result["summary"]:
        heart_rate = result["summary"]["heart_rate"]
        print(
            f"Heart rate - average: {heart_rate['avg']}, "
            f"min: {heart_rate['min']}, max: {heart_rate['max']}"
        )

    if result["rejected"]:
        print("Rejected: " + "; ".join(result["rejected"]))
