from ocean_backend.data.observations import Observation


class ObservationStore:
    """In-memory store for in-situ observations."""

    def __init__(self, observations: list[Observation] | None = None):
        self.observations = observations or []

    def get_by_id(self, observation_id: str) -> Observation | None:
        """Return an observation by its ID."""

        for observation in self.observations:
            if observation.platform_id == observation_id:
                return observation

        return None

    def get_by_profile(
        self,
        profile_id: str,
        variable: str,
        depth: float,
    ) -> tuple[Observation, float] | None:
        """
        Return the observation closest to the requested depth
        and the absolute depth separation.
        """

        candidates = [
            observation
            for observation in self.observations
            if observation.platform_id == profile_id
            and observation.variable == variable
        ]

        if not candidates:
            return None

        observation = min(
            candidates,
            key=lambda item: abs(item.depth - depth),
        )

        depth_difference = abs(observation.depth - depth)

        return observation, depth_difference

    def add(self, observation: Observation) -> None:
        """Add one observation."""

        self.observations.append(observation)

    def add_many(self, observations: list[Observation]) -> None:
        """Add multiple observations."""

        self.observations.extend(observations)

    def count(self) -> int:
        """Return the number of observations."""

        return len(self.observations)