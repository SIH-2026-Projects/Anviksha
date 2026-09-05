from dataclasses import dataclass
from pathlib import Path

import xarray as xr


@dataclass
class ModelField:
    variable: str
    data: xr.DataArray

    @property
    def latitude(self) -> xr.DataArray:
        return self.data["latitude"]

    @property
    def longitude(self) -> xr.DataArray:
        return self.data["longitude"]

    @property
    def depth(self) -> xr.DataArray | None:
        if "depth" in self.data.coords:
            return self.data["depth"]
        return None

    @property
    def time(self) -> xr.DataArray | None:
        if "time" in self.data.coords:
            return self.data["time"]
        return None

    @property
    def units(self) -> str | None:
        return self.data.attrs.get("units")

    @property
    def standard_name(self) -> str | None:
        return self.data.attrs.get("standard_name")

    @property
    def long_name(self) -> str | None:
        return self.data.attrs.get("long_name")


@dataclass
class ModelDataset:
    dataset: xr.Dataset

    @classmethod
    def open_netcdf(cls, path: str | Path) -> "ModelDataset":
        ds = xr.open_dataset(path)
        return cls(ds)

    def get_field(self, variable: str) -> ModelField:
        if variable not in self.dataset.data_vars:
            raise KeyError(f"Model variable not found: {variable}")

        return ModelField(
            variable=variable,
            data=self.dataset[variable],
        )

    def close(self) -> None:
        self.dataset.close()