from statistics import mean

FIELDS = ("timestamp", "heart_rate", "skin_response", "temperature", "activity_level", "signal_quality")


# Return a reason a reading is unusable, or None if it's fine.
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


# Average/min/max for each measured field.
def summary(readings):
    result = {}
    for field in FIELDS[1:]:
        values = [getattr(r, field) for r in readings]
        result[field] = {"avg": round(mean(values), 2), "min": min(values), "max": max(values)}
    return result


# Difference between session averages and the participant's baseline.
def compare(data, reference):
    result = {}
    for field, baseline in reference.values().items():
        result[field] = round(data[field]["avg"] - baseline, 2)
    return result


# True if heart rate and activity both drop near the session's end.
def recovery(readings):
    if len(readings) < 4:
        return False
    n = max(1, len(readings) // 3)
    before = readings[-2 * n:-n]
    end = readings[-n:]
    heart_rate_drop = mean(r.heart_rate for r in before) - mean(r.heart_rate for r in end)
    activity_drop = mean(r.activity_level for r in before) - mean(r.activity_level for r in end)
    return heart_rate_drop >= 8 and activity_drop >= .15


# Label a session from its averages, baseline diff, and recovery flag.
def classify(data, diff, is_recovering):
    if is_recovering:
        return "recovering", "heart rate and activity fell near the end"
    if data["activity_level"]["avg"] < .20 and diff["heart_rate"] < 15:
        return "resting", "low activity and heart rate close to baseline"
    if data["activity_level"]["avg"] >= .65 or diff["heart_rate"] >= 55:
        return "high activity", "high activity or large heart-rate rise"
    return "moderate activity", "activity is above the resting range"


# A participant's personal baseline; heart_rate is validated via a property.
class ReferenceMeasurements:
    def __init__(self, heart_rate, skin_response, temperature):
        self.heart_rate = heart_rate
        self.skin_response, self.temperature = skin_response, temperature

    @property
    def heart_rate(self):
        return self._heart_rate

    @heart_rate.setter
    def heart_rate(self, value):
        if not 30 <= value <= 150:
            raise ValueError("baseline heart rate must be 30–150")
        self._heart_rate = value

    def values(self):
        return {"heart_rate": self._heart_rate, "skin_response": self.skin_response, "temperature": self.temperature}


# Composition: a participant owns their reference measurements.
class Participant:
    def __init__(self, name, reference):
        self.name, self.reference = name, reference


# A usable reading. from_dict() routes invalid data to RejectedObservation.
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


# Inheritance: overrides usable() for readings that failed validation.
class RejectedObservation(Observation):
    def __init__(self, reason):
        self.reason = reason

    def usable(self):
        return False


# Composition: groups a participant with their observations.
class FitnessSession:
    MIN_READINGS = 3

    def __init__(self, participant, name):
        self.participant, self.name, self.observations = participant, name, []

    def add(self, data):
        self.observations.append(Observation.from_dict(data))

    def analyse(self):
        good = []
        bad = []
        for r in self.observations:
            if r.usable():
                good.append(r)
            else:
                bad.append(r.reason)
        good.sort(key=lambda r: r.timestamp)

        result = {"session": self.name, "usable": len(good), "rejected": bad}

        if len(good) < self.MIN_READINGS:
            result["classification"] = "insufficient data"
            result["reason"] = "fewer than 3 usable readings"
            result["summary"] = {}
            return result

        data = summary(good)
        diff = compare(data, self.participant.reference)
        label, reason = classify(data, diff, recovery(good))

        result["classification"] = label
        result["reason"] = reason
        result["summary"] = data
        result["reference_difference"] = diff
        return result


# Print the structured result as a readable report.
def report(result):
    print(f"\n{result['session']}: {result['classification']}")
    print(f"Usable observations: {result['usable']} | Reason: {result['reason']}")
    if result["summary"]:
        hr = result["summary"]["heart_rate"]
        print(f"Heart rate — average: {hr['avg']}, min: {hr['min']}, max: {hr['max']}")
    if result["rejected"]:
        print("Rejected: " + "; ".join(result["rejected"]))


# Build one simulated reading, with sensible defaults for the rest.
def reading(time, heart_rate, activity, quality=.95):
    return {"timestamp": time, "heart_rate": heart_rate, "skin_response": 2.5,
            "temperature": 32.9, "activity_level": activity, "signal_quality": quality}


# Run the five demo scenarios and print each report.
def run_demo():
    participant = Participant("Alex", ReferenceMeasurements(65, 2, 32.5))
    scenarios = {
        "Resting": [reading(1, 64, .05), reading(2, 67, .08), reading(3, 66, .06)],
        "Moderate": [reading(1, 82, .35), reading(2, 88, .45), reading(3, 90, .48)],
        "High": [reading(1, 125, .72), reading(2, 138, .82), reading(3, 145, .79)],
        "Recovery": [reading(1, 100, .55), reading(2, 130, .82), reading(3, 136, .85),
                     reading(4, 108, .50), reading(5, 90, .24), reading(6, 78, .12)],
        "Invalid": [reading(1, 80, .4, .3), reading(2, 300, .5), {"timestamp": 3, "heart_rate": 83}],
        "Mixed": [reading(1, 80, .30), reading(2, 85, .35), reading(3, 90, .40), reading(4, 250, .40)],
    }
    for name, readings in scenarios.items():
        session = FitnessSession(participant, name)
        for item in readings:
            session.add(item)
        report(session.analyse())


if __name__ == "__main__":
    run_demo()