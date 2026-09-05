"""Model-observation comparison mathematics."""


def difference(model_value: float, observed_value: float) -> float:
    """Return model minus observation.

    This is deliberately named difference, not model error. The latter would require
    additional uncertainty/sampling assumptions that are outside this primitive.
    """
    return float(model_value - observed_value)


def bias(model_values, observed_values) -> float:
    return float((model_values - observed_values).mean())


def mae(model_values, observed_values) -> float:
    return float(abs(model_values - observed_values).mean())


def rmse(model_values, observed_values) -> float:
    residual = model_values - observed_values
    return float((residual**2).mean() ** 0.5)
