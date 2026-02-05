from dataclasses import dataclass
import datetime as dt
from typing import Optional, Sequence, Tuple, Mapping, Any

from apsimNGpy.manager.soilmanager import DownloadsurgoSoiltables, OrganiseSoilProfile
from apsimNGpy.core_utils.soil_lay_calculator import auto_gen_thickness_layers
from apsimNGpy.core.model_tools import find_all_in_scope, CastHelper
from apsimNGpy.core.model_tools import find_child_of_class
from apsimNGpy.settings import logger

lp = load_pythonnet()  # ensure CLR
import numpy as np
import Models
from System import Array, Double  # pythonnet: fast marshaling to double[]


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _to_net_double_array(values) -> Array[Double]:
    """Fast-ish conversion of a 1D numeric sequence to .NET double[]."""
    a = np.asarray(values, dtype=np.float64)
    # pythonnet marshaling from list -> double[] is reliable and reasonably fast
    return Array[Double](a.tolist())


def fill_in_meta_info(*,
                      record_number=0,
                      asc_order=None,
                      asc_sub_order=None,
                      soil_type=None,
                      local_name=None,
                      site=None,
                      nearest_town=None,
                      region=None,
                      state=None,
                      country=None,
                      natural_vegetation=None,
                      apsoil_number=None,
                      latitude=0.0,
                      longitude=0.0,
                      location_accuracy=None,
                      year_of_sampling=None,
                      data_source=None,
                      comments=None):
    return {
        "RecordNumber": record_number,
        "ASCOrder": asc_order,
        "ASCSubOrder": asc_sub_order,
        "SoilType": soil_type,
        "LocalName": local_name,
        "Site": site,
        "NearestTown": nearest_town,
        "Region": region,
        "State": state,
        "Country": country,
        "NaturalVegetation": natural_vegetation,
        "ApsoilNumber": apsoil_number,
        "Latitude": latitude,
        "Longitude": longitude,
        "LocationAccuracy": location_accuracy,
        "YearOfSampling": year_of_sampling,
        "DataSource": data_source,
        "Comments": comments
    }


class Soils(Models.Soils.Soil):
    pass


@dataclass(order=True, slots=True, repr=False)
class SoilManager:
    simulation_model: Models.Core.Simulation
    lonlat: Optional[Tuple[float, float]] = None
    soil_tables: Optional[Sequence[Any]] = None
    soil_series: str = None
    thickness_sequence: Optional[Sequence[Any]] = 'auto'
    thickness_value: int = None  # mm
    max_depth: Optional[int] = 2400  # mm
    n_layers: int = 10
    thinnest_layer: int = 100  # mm
    thickness_growth_rate: float = 1.5  # unitless
    soil_profile: Optional[Mapping] = None  # cached once

    # ------------------------ Profile prep ------------------------
    def __post_init__(self):
        if self.thickness_sequence == 'auto':
            self.thickness_sequence = auto_gen_thickness_layers(max_depth=self.max_depth,
                                                                n_layers=self.n_layers,
                                                                thin_thickness=self.thinnest_layer,
                                                                growth_type='linear',
                                                                thick_growth_rate=self.thickness_growth_rate)

    def _ensure_soil_profile(self) -> None:
        """
        Prepare `self.soil_profile` ONCE. No-ops if already set.
        This avoids re-downloading SSURGO and re-organizing on every edit.
        """
        if self.soil_profile is not None:
            return

        # Prefer lonlat (your original logic)
        if self.lonlat is not None:
            self.soil_profile = self.get_soil_profile_from_lonlat(
                self.lonlat,
                thickness=self.thickness_value,
                thinnest_layer=self.thinnest_layer,
                n_layers=self.n_layers,
                max_depth=self.max_depth,
                soil_series=self.soil_series,
                thickness_sequence=self.thickness_sequence,
            )

        # Fallback to provided tables (dict-like expected)
        if isinstance(self.soil_tables, dict):
            self.soil_profile = self.soil_tables
            self.thickness_sequence = self.soil_tables.get('Thickness', self.thickness_sequence)
            return

    @staticmethod
    def get_soil_profile_from_lonlat(
            lonlat,
            *,
            thickness_sequence=None,
            soil_series=None,
            thickness=None,
            max_depth=2400,
            n_layers=10,
            thinnest_layer=100,
            thick_growth_rate=1.3
    ):
        assert any([thickness_sequence, thickness]), \
            "both thickness_sequence and thickness must not be None"
        if all([thickness_sequence, thickness]):
            logger.warning(
                'Both "thickness_sequence" and "thickness" are provided; only "thickness_sequence" will be used.'
            )

        date_str = dt.date.today().strftime("%Y-%m-%d")
        sdf = DownloadsurgoSoiltables(lonlat=lonlat, select_componentname=soil_series, summarytable=True)
        if soil_series in sdf.componentname.unique():
            sdf = sdf[sdf['componentname'] == soil_series]
        if soil_series is None:
            max_compo_value = sdf.prcent.max()
            sdf = sdf[sdf['prcent'] == max_compo_value]
            # update
            soil_series = sdf['componentname'].iloc[0]
            mu_name = sdf['muname'].iloc[0]
        else:
            raise KeyError(f'{soil_series} not any of the available ones: {', '.join(sdf.componentname.unique())}')

        soil_profile = OrganiseSoilProfile(sdf, thickness_values=thickness_sequence)

        meta_info = fill_in_meta_info(
            soil_type=mu_name,
            record_number=mu_name,
            latitude=lonlat[0],
            longitude=lonlat[1],
            local_name=soil_series,
            data_source=(
                f"downloaded by apsimNGpy: `DownloadsurgoSoiltables` \n accessed from SSURGO on: {date_str}"

            ),
            comments=f"number of layers: {n_layers}"
        )
        return soil_profile.cal_missingFromSurgo(metadata=meta_info)

    # ------------------------ Editors ------------------------

    def _edit_soil_section(self, section_key: str, model_type) -> None:
        """
        Generic editor: sets properties on a .NET soil section from a pandas DataFrame
        found in self.soil_profile[section_key]. Uses vectorized conversion and .NET arrays.
        """
        self._ensure_soil_profile()

        section = find_child_of_class(self.simulation_model, child_class=model_type)
        if section:
            cast_as = CastHelper.CastAs[model_type]  # cache the generic once
            tmp = cast_as(section)
            if tmp:
                section = tmp
        else:
            section = model_type()  # NOTE: if needed, attach to parent outside

        df = self.soil_profile[section_key]

        # Cache attribute membership to avoid repeated hasattr C-bound lookups
        # (dir() is surprisingly cheap vs many hasattr calls)
        attr_set = set(dir(section))

        for prop in df.columns:
            if prop not in attr_set:
                continue

            col = df[prop]
            if prop == 'Depth':
                # Depth often strings like "[0-100]"; keep as-is to avoid coercion overhead
                setattr(section, prop, col.values)
            else:
                # Vectorized -> .NET double[] in one shot
                setattr(section, prop, _to_net_double_array(col.to_numpy(copy=False)))

    def edit_solute_sections(self) -> None:
        self._ensure_soil_profile()
        all_solutes = find_all_in_scope(self.simulation_model, child_class=Models.Soils.Solute)
        if not all_solutes:
            return

        for sol in all_solutes:
            sol = CastHelper.CastAs[Models.Soils.Solute](sol)
            name = sol.Name
            df = self.soil_profile.get(name)
            if df is None:
                continue

            attr_set = set(dir(sol))
            for column in df.columns:
                if column not in attr_set:
                    continue
                col = df[column]
                if column == 'Depth':
                    setattr(sol, column, col.values)
                else:
                    setattr(sol, column, _to_net_double_array(col.to_numpy(copy=False)))

    def edit_soil_crop(self, crops_in: Sequence[str] = ()) -> None:
        """
        Edits the shared SoilCrop first, then adds explicit crop entries as requested.
        """
        self._ensure_soil_profile()

        physical = find_child_of_class(parent=self.simulation_model, child_class=Models.Soils.Physical)
        if not physical:
            return
        physical = CastHelper.CastAs[Models.Soils.Physical](physical) or physical

        crop_soil = find_child_of_class(physical, child_class=Models.Soils.SoilCrop)
        if not crop_soil:
            return
        crop_soil = CastHelper.CastAs[Models.Soils.SoilCrop](crop_soil) or crop_soil

        df = self.soil_profile.get('soil_crop')
        if df is None:
            return

        attr_set = set(dir(crop_soil))
        for prop in df.columns:
            if prop not in attr_set:
                continue
            col = df[prop]
            if prop == 'Depth':
                setattr(crop_soil, prop, col.values)
            else:
                setattr(crop_soil, prop, _to_net_double_array(col.to_numpy(copy=False)))

        # Add explicit crop entries, copying values in bulk
        for crop in crops_in or ():
            sc = Models.Soils.SoilCrop()
            sc.Name = crop
            attr_set2 = set(dir(sc))
            for prop in df.columns:
                if prop not in attr_set2:
                    continue
                col = df[prop]
                if prop == 'Depth':
                    setattr(sc, prop, col.values)
                else:
                    setattr(sc, prop, _to_net_double_array(col.to_numpy(copy=False)))
            physical.Children.Add(sc)

    # Thin wrappers
    def edit_soil_physical(self) -> None:
        self._edit_soil_section('physical', Models.Soils.Physical)

    def edit_soil_organic(self) -> None:
        self._edit_soil_section('organic', Models.Soils.Organic)

    def edit_soil_chemical(self) -> None:
        self._edit_soil_section('chemical', Models.Soils.Chemical)

    def edit_soil_water_balance(self) -> None:
        self._edit_soil_section('soil_water', Models.WaterModel.WaterBalance)

    def edit_soil_initial_water(self) -> None:
        self._edit_soil_section('water', Models.Soils.Water)

    # Stubs kept for future parity
    def edit_som(self) -> None:
        pass

    def edit_sim3(self) -> None:
        pass

    def edit_meta_data(self) -> None:
        pass

    def edit_soil_layer_structure(self) -> None:
        pass

    def edit_soil_crops(self) -> None:
        pass

    def edit_sim3_solute(self) -> None:
        pass





if __name__ == "__main__":
    from apsimNGpy.core.apsim import ApsimModel

    model = ApsimModel('Maize', out_path='out__maize.apsimx')
    # soil = SoilManager(simulation_model=model.simulations[0], lonlat=(-93.97702, 42.8780025), soil_tables=[])
    # # sp = soil.get_soil_profile_from_lonlat(lonlat=(-92.297702, 41.321), thickness=100)
    # soil.edit_soil_physical()
    # soil.edit_soil_chemical()
    # soil.edit_soil_organic()
    # soil.edit_soil_initial_water()
    # soil.edit_solute_sections()
    # soil.edit_soil_water_balance()
    # soil.edit_soil_crop(crops_in=['Soybean'])
    # model.save()
