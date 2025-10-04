# -*- coding: utf-8 -*-
# @Software: PyCharm
import json
from dataclasses import dataclass, field, asdict, astuple
from collections import OrderedDict


def IOderedDict(obj):
    return OrderedDict({key: value for key, value in vars(obj).items()})


@dataclass(order=True)
class Models:
    module = True

    @dataclass(order=True)
    class Core:
        def module(self):
            return True

        @dataclass(order=True)
        class Simulations:
            Schema: str = 'Models.Core.Simulations, Models'
            ExplorerWidth: int = 259
            Version: str = 174
            ApsimVersion: str = '0.0.0.0'
            Name: str = 'Simulations'
            ResourceName: str = None
            Children: list = field(default_factory=list)
            Enabled: bool = True
            ReadOnly: bool = False

            @property
            def module(self) -> bool:
                return False

            def add(self, obj):
                return self.Children.append(IOderedDict(obj))

            def build(self):
                return json.dumps(obj=self.__dict__,
                                  default=lambda x: x.__dict__, sort_keys=False, indent=2, ensure_ascii=False).replace(
                    'Schema',
                    '$type')

            def save(self, path):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.build())

        @dataclass(order=True)
        class Simulation:
            '''
            A simulation model
            '''
            Schema: str = 'Models.Core.Simulation, Models'
            # IsRunning: bool = False
            Descriptors: str = None
            Name: str = 'Simulation'
            ResourceName: str = None
            Children: list = field(default_factory=list)
            Enabled: bool = True
            ReadOnly: bool = False

            @property
            def module(self) -> bool:
                return False

            def add(self, obj):
                return self.Children.append(IOderedDict(obj))

        @dataclass(order=True)
        class Zone:
            Schema: str = 'Models.Core.Zone, Models'
            Area: float = 1.0
            Slope: float = 0.0
            AspectAngle: float = 0.0
            Altitude: float = 0.0
            Name: str = "Field"
            ResourceName: str = None
            Children: list = field(default_factory=list)
            Enabled: bool = True
            ReadOnly: bool = False

            @property
            def module(self) -> bool:
                return False

            def add(self, obj):
                return self.Children.append(IOderedDict(obj))

        @dataclass(order=True)
        class Replacements:
            Schema: str = 'Models.Core.Folder, Models'
            ShowInDocs: bool = False
            GraphsPerPage: int = 6
            Name: str = "Replacements"
            Children: list = field(default_factory=list)
            # IncludeInDocumentation:bool=True
            Enabled: bool = True
            ReadOnly: bool = False

            @property
            def module(self) -> bool:
                return False

            def add(self, obj):
                return self.Children.append(IOderedDict(obj))

    class PMF:
        module = True

        @dataclass(order=True)
        class Plant:
            Schema: str = 'Models.PMF.Plant, Models'
            Name: str = None
            ResourceName: str = None
            Children: list = field(default_factory=list)
            Enabled: bool = True
            ReadOnly: bool = False

            @property
            def module(self) -> bool:
                return False

            def add(self, obj):
                return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Experiment:
        Schema: str = 'Models.Factorial.Experiment, Models'
        Name: str = "Experiment"
        Children: list = field(default_factory=list)
        # IncludeInDocumentation:bool=True
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Factors:
        Schema: str = 'Models.Factorial.Factors, Models'
        Name: str = "Factors"
        Children: list = field(default_factory=list)
        # IncludeInDocumentation:bool=True
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Permutation:
        '''
        This class permutates all child models by each other.
        '''
        Schema: str = 'Models.Factorial.Permutation, Models'
        Name: str = "Permutation"
        Children: list = field(default_factory=list)
        # IncludeInDocumentation:bool=True
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Memo:
        Schema: str = 'Models.Memo, Models'
        Text: str = ""
        Name: str = 'Memo'
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class DataStore:
        Schema: str = 'Models.Storage.DataStore, Models'
        useFirebird: bool = False
        CustomFileName: str = None
        Name: str = "DataStore"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Weather:
        Schema: str = 'Models.Climate.Weather, Models'
        ConstantsFile: str = None
        FileName: str = ''
        ExcelWorkSheetName: str = None
        Name: str = "Weather"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Clock:
        Schema: str = 'Models.Clock, Models'
        Start: str = None
        End: str = None
        Name: str = "Clock"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Summary:
        Schema: str = 'Models.Summary, Models'
        Verbosity: int = 100
        Name: bool = "Summary"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Cultivar:
        Schema: str = 'Models.PMF.Cultivar, Models'
        Command: list = field(default_factory=list)
        Name: str = "Cultivar"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        # IncludeInDocumentation:bool=True
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class SoilArbitrator:
        Schema: str = 'Models.Soils.Arbitrator.SoilArbitrator, Models'
        Name: str = "Soil Arbitrator"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Soil:
        Schema: str = 'Models.Soils.Soil, Models'

        RecordNumber: int = 0
        ASCOrder: float = None
        ASCSubOrder: float = None
        SoilType: str = ''
        LocalName: str = ''
        Site: str = None
        NearestTown: str = None
        Region: str = None
        State: str = None
        Country: str = None
        NaturalVegetation: str = None
        ApsoilNumber: float = None
        Latitude: float = 0.0
        Longitude: float = 0.0
        LocationAccuracy: float = None
        YearOfSampling: float = None
        DataSource: str = None
        Comments: str = None
        Name: str = "Soil"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class SurfaceOrganicMatter:
        Schema: str = 'Models.Surface.SurfaceOrganicMatter, Models'
        SurfOM: list = field(default_factory=list)
        Canopies: list = field(default_factory=list)
        InitialResidueName: str = "maize"
        InitialResidueType: str = "maize"
        InitialResidueMass: float = 0.0
        InitialStandingFraction: float = 0.0
        InitialCPR: float = 0.0
        InitialCNR: float = 0.0
        Name: str = "SurfaceOrganicMatter"
        ResourceName: str = "SurfaceOrganicMatter"
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def __post_init__(self):
            self.InitialResidueName: str = self.InitialResidueType

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class MicroClimate:
        Schema: str = 'Models.MicroClimate, Models'
        a_interception: float = 0.0
        b_interception: float = 1.0
        c_interception: float = 0.0
        d_interception: float = 0.0
        # soil_albedo:float =  0.23
        SoilHeatFluxFraction: float = 0.4
        MinimumHeightDiffForNewLayer: float = 0.0
        NightInterceptionFraction: float = 0.5
        ReferenceHeight: float = 2.0
        Name: str = "MicroClimate"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Irrigation:
        '''
        This model controls irrigation events.
        '''
        Schema: str = 'Models.Irrigation, Models'
        Name: str = "Irrigation"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True)
    class Fertiliser:
        '''
        This model is responsible for applying fertiliser.
        '''
        Schema: str = 'Models.Fertiliser, Models'
        Name: str = "Fertiliser"
        ResourceName: str = "Fertiliser"
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class Operations:
        Schema: str = 'Models.Operations, Models'
        Name: str = "Operations"
        Operation: list = field(default_factory=list)
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def __post_init__(self):
            for i in range(len(self.Operation)):
                Operation = self.Operation[i]

                if Operation['Action'] == 'Fertiliser':
                    self.Operation[i] = {"Schema": "Models.Operation, Models",
                                         "Date": Operation['Date'],
                                         "Action": f"[Fertiliser].Apply({Operation['Amount']}, Fertiliser.Types.{Operation['FertiliserType']},0);",
                                         "Enabled": True
                                         }
                elif Operation['Action'] == 'Irrigation':
                    self.Operation[i] = {"Schema": "Models.Operation, Models",
                                         "Date": Operation['Date'],
                                         "Action": f"[Irrigation].Apply({Operation['Amount']};",
                                         "Enabled": True
                                         }

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class Report:
        Schema: str = 'Models.Report, Models'
        VariableNames: list = field(default_factory=list)
        EventNames: list = field(default_factory=list)
        GroupByVariableName: str = None
        Name: str = "Report"
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class Manager:
        Schema: str = 'Models.Manager, Models'
        Code: str = None
        Parameters: list = field(default_factory=list)
        Name: str = "PotatoPlantAndHarvest"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    IDepth = ["0-4.5",
              "4.5-9.1",
              "9.1-16.6",
              "16.6-28.9",
              "28.9-49.3",
              "49.3-82.9"]  # "82.9-138.3"
    IThickness = [45,
                  46,
                  75,
                  123,
                  204,
                  336]  # 554

    @dataclass(order=True, repr=True)
    class Physical:
        Schema: str = 'Models.Soils.Physical, Models'
        # Depth:list = field(default_factory=lambda: IDepth)
        Thickness: list = field(default_factory=lambda: IThickness)
        ParticleSizeClay: float = None
        ParticleSizeSand: float = None
        ParticleSizeSilt: float = None
        Rocks: str = None
        Texture: str = None
        BD: list = field(default_factory=list)
        AirDry: list = field(default_factory=list)
        LL15: list = field(default_factory=list)
        DUL: list = field(default_factory=list)
        SAT: list = field(default_factory=list)
        KS: float = None
        BDMetadata: str = None
        AirDryMetadata: str = None
        LL15Metadata: str = None
        DULMetadata: str = None
        SATMetadata: str = None
        KSMetadata: str = None
        RocksMetadata: str = None
        TextureMetadata: str = None
        ParticleSizeSandMetadata: str = None
        ParticleSizeSiltMetadata: str = None
        ParticleSizeClayMetadata: str = None
        Name: str = "Physical"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class SoilCrop:
        Schema: str = 'Models.Soils.SoilCrop, Models'
        LL: list = field(default_factory=list)
        KL: list = field(default_factory=list)
        XF: list = field(default_factory=list)

        LLMetadata: str = None
        KLMetadata: str = None
        XFMetadata: str = None
        Name: str = "PotatoSoil"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class SoilWater:
        Schema: str = 'Models.WaterModel.WaterBalance, Models'
        SummerDate: str = "28-Apr"
        SummerU: float = 9.0
        SummerCona: float = 4.4
        WinterDate: str = "1-Nov"
        WinterU: float = 9.0
        WinterCona: float = 4.4
        DiffusConst: float = 88.0
        DiffusSlope: float = 35.4
        Salb: float = 0.18
        CN2Bare: float = 0.0
        CNRed: float = 20
        CNCov: float = 0.8
        DischargeWidth: str = "NaN"
        CatchmentArea: str = "NaN"
        PSIDul: float = -100.0
        Thickness: list = field(default_factory=lambda: IThickness)
        SWCON: list = field(default_factory=list)
        KLAT: str = None
        Name: str = "SoilWater"
        ResourceName: str = "WaterBalance"
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class Organic:
        Schema: str = 'Models.Soils.Organic, Models'
        # Depth: list = field(default_factory=lambda: IDepth)
        FOMCNRatio: float = 30.0
        Thickness: list = field(default_factory=lambda: IThickness)
        Carbon: list = field(default_factory=list)
        CarbonUnits: int = 0
        SoilCNRatio: list = field(default_factory=list)
        FBiom: str = None
        FInert: str = None
        FOM: str = None
        CarbonMetadata: str = None
        FOMMetadata: str = None
        Name: str = "Organic"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class Chemical:
        Schema: str = 'Models.Soils.Chemical, Models'
        # Depth: list = field(default_factory=lambda: IDepth)
        Thickness: list = field(default_factory=lambda: IThickness)

        PH: list = field(default_factory=list)
        PHUnits: int = 0
        # NO3N: str = None
        # NH4N: str = None
        # CL: str = None
        EC: str = None
        ESP: str = None
        CEC: list = field(default_factory=list)
        # LabileP:str = None
        # UnavailableP: str = None
        ECMetadata: str = None
        CLMetadata: str = None
        ESPMetadata: str = None
        PHMetadata: str = None
        Name: str = "Chemical"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class InitialWater:
        Schema: str = 'Models.Soils.Water, Models'
        Thickness: list = field(default_factory=lambda: IThickness)
        InitialValues: list = field(default_factory=list)
        InitialPAWmm: float = None
        RelativeTo: str = "LL15"
        FilledFromTop: bool = True
        Name: str = "Water"
        ResourceName: str = None

        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class Sample:
        Schema: str = 'Models.Soils.Sample, Models'
        # Depth: list = field(default_factory=lambda: IDepth)
        Thickness: list = field(default_factory=lambda: IThickness)
        NO3N: str = None
        NH4N: str = None
        SW: str = None
        OC: str = None
        EC: str = None
        CL: str = None
        ESP: str = None
        PH: str = None
        SWUnits: int = 0
        OCUnits: int = 0
        PHUnits: int = 0
        Name: str = "Sample"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        # IncludeInDocumentation: bool = True
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class CERESSoilTemperature:
        Schema: str = 'Models.Soils.CERESSoilTemperature, Models'
        Name: str = "Temperature"
        ResourceName: str = None
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class Nutrient:
        Schema: str = 'Models.Soils.Nutrients.Nutrient, Models'
        Name: str = "Nutrient"
        ResourceName: str = "Nutrient"
        Children: list = field(default_factory=list)
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))

    @dataclass(order=True, repr=True)
    class Solute:
        Schema: str = 'Models.Soils.Solute, Models'
        Thickness: list = field(default_factory=lambda: IThickness)
        InitialValues: list = field(default_factory=list)
        InitialValuesUnits: int = 0
        WaterTableConcentration: float = 0.0
        D0: float = 0.0
        Exco: float = None
        FIP: float = None
        DepthConstant: float = 0.0
        MaxDepthSoluteAccessible: float = 0.0
        RunoffEffectivenessAtMovingSolute: float = 0.0
        MaxEffectiveRunoff: float = 0.0
        Name: str = "NO3"
        ResourceName: str = None
        Enabled: bool = True
        ReadOnly: bool = False

        @property
        def module(self) -> bool:
            return False

        def add(self, obj):
            return self.Children.append(IOderedDict(obj))


if __name__ == '__main__':
    Simulations = Models.Core.Simulations()
    sim = Models.Core.Simulation()

    zone = Models.Core.Zone()
    zone.add(Models.PMF.Plant(Name='Maize'))
    sim.add(zone)
    Simulations.add(sim)
    Simulations.build()
    Simulations.save('ma.apsimx')
