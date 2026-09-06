from ocean_backend.data.observations import Observation


class ObservationStore:

    def __init__(self, observations: list[Observation] | None = None):
        self.observations = observations or []

    def get_by_id(self, observation_id: str) -> Observation | None:
        for observation in self.observations:
            if observation.platform_id == observation_id:
                return observation

        return None