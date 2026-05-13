from apsimNGpy.starter.starter import CLR

sw_data = {
    "$type": "Models.WaterModel.WaterBalance, Models",
    "SummerDate": "1-Nov",
    "SummerU": 5.0,
    "SummerCona": 5.0,
    "WinterDate": "1-Apr",
    "WinterU": 5.0,
    "WinterCona": 5.0,
    "DiffusConst": 40.0,
    "DiffusSlope": 16.0,
    "Salb": 0.12,
    "CN2Bare": 73.0,
    "CNRed": 20.0,
    "CNCov": 0.8,
    "DischargeWidth": "NaN",
    "CatchmentArea": "NaN",
    "PSIDul": -100.0,
    "Thickness": [
        150.0,
        150.0,
        300.0,
        300.0,
        300.0,
        300.0,
        300.0
    ],
    "SWCON": [
        0.3,
        0.3,
        0.3,
        0.3,
        0.3,
        0.3,
        0.3
    ],
    "KLAT": None,
    "Name": "SoilWater",
    "ResourceName": "WaterBalance",
    "Children": [],
    "Enabled": True,
    "ReadOnly": False
}

swim_data = {
    "$type": "Models.Soils.Swim3, Models",
    "Salb": 0.13,
    "CN2Bare": 50.0,
    "CNRed": 20.0,
    "CNCov": 0.8,
    "KDul": 1.0,
    "PSIDul": -100.0,
    "VC": True,
    "DTMin": 0.0,
    "DTMax": 60.0,
    "MaxWaterIncrement": 5.0,
    "SpaceWeightingFactor": 0.0,
    "SoluteSpaceWeightingFactor": 1.0,
    "Dis": 0.0,
    "Disp": 1.0,
    "A": 2.0,
    "DTHC": 0.1,
    "DTHP": 2.0,
    "vcon1": 7.28E-09,
    "vcon2": 7.26E-07,
    "eo_time": "06:00",
    "eo_durn": 720.0,
    "default_rain_time": "00:00",
    "default_rain_duration": 720.0,
    "Diagnostics": True,
    "Name": "Swim3",
    "ResourceName": True,
    "Children": [],
    "Enabled": True,
    "ReadOnly": True
}

set_swim_lower_bc = {
    "$type": "Models.Manager, Models",
    "CodeArray": [
        "using Models.Climate;",
        "using APSIM.Shared.Utilities;",
        "using Models.Soils.Nutrients;",
        "using Models.Soils;",
        "using Models.PMF;",
        "using Models.Core;",
        "using System.Xml.Serialization;",
        "using System;",
        "using System.Linq;",
        "using Models.AgPasture;",
        "using Models.Interfaces;",
        "",
        "namespace Models",
        "{",
        "    [Serializable] ",
        "    [System.Xml.Serialization.XmlInclude(typeof(Model))]",
        "    public class Script : Model",
        "    {",
        "        [Link] Clock clock;",
        "        [Link] ISummary summary;",
        "        [Link] private Swim3 swim;",
        "        //[Link] private PastureSpecies ryegrass;",
        "        //[Link] private SimpleGrazing grazing;",
        "        ",
        "        public enum LowerBCTypeOptions {gradient,seepage,potential};",
        "",
        "        [Separator(\"Sets the lower boundary condition type (and value if set to 'potential' for SWIM3. The change is applied at the beginning of the first day of the simulation.\")]",
        "        [Description(\"[Get a dropdown] What lower boundary condition is wanted?\")] public LowerBCTypeOptions LowerBCType { get; set; }",
        "        [Description(\"If 'potential', then what potential? (mm) \")] public double LowerBCValue { get; set; }",
        "",
        "        public double SoilWaterStart  { get; set; }",
        "        public double SoilWaterEnd  { get; set; }",
        "",
        "        [EventSubscribe(\"DoDailyInitialisation\")]",
        "        private void DoDailyInitialisation(object sender, EventArgs e)",
        "        {",
        "        }",
        "",
        "        [EventSubscribe(\"DoReportCalculations\")]",
        "        private void DoReportCalculations(object sender, EventArgs e)",
        "        {",
        "        }",
        "",
        "        [EventSubscribe(\"DoManagement\")]",
        "        private void DoDailyCalculations(object sender, EventArgs e)",
        "        {",
        "            if (clock.Today == clock.StartDate)",
        "            {",
        "                summary.WriteMessage(this, \"Script is setting lower boundary condition to \" + LowerBCType, MessageType.Diagnostic);",
        "                if (LowerBCType == LowerBCTypeOptions.gradient)",
        "                    swim.SetLowerBCForGradient(bbcGradient: 0.0);   // in cm/cm (ibbc=0) Note that this is the default setting",
        "                else if (LowerBCType == LowerBCTypeOptions.potential)",
        "                    swim.SetLowerBCForGivenPotential(bbcPotential: LowerBCValue /10.0 );    //  convert to cm (ibbc=1), DUL is -100 cm so values more positive will often result in inflow to the bottom of the soil profile. Input in mm so divide here.",
        "                else if (LowerBCType == LowerBCTypeOptions.seepage)",
        "                    swim.SetLowerBCForSeepage(bbcPotentialSeepage: 0.0);  // in cm (ibbc=3). This is for zero-tension lysimeters",
        "                else",
        "                    throw new Exception(\"Wrong lower boundary condition type\");",
        "            }",
        "        }",
        "    }",
        "}"
    ],
    "Parameters": [
        {
            "Key": "LowerBCType",
            "Value": "gradient"
        },
        {
            "Key": "LowerBCValue",
            "Value": "-500"
        }
    ],
    "Name": "SWIMSetLowerBC",
    "ResourceName": None,
    "Children": [],
    "Enabled": True,
    "ReadOnly": False
}

layer_struct = {
    "$type": "Models.Soils.LayerStructure, Models",
    "Thickness": [
        10.0,
        20.0,
        30.0,
        40.0,
        50.0,
        50.0,
        50.0,
        50.0,
        100.0,
        100.0,
        50.0,
        50.0,
        50.0,
        50.0
    ],
    "Name": "LayerStructure",
    "ResourceName": None,
    "Children": [],
    "Enabled": True,
    "ReadOnly": False
}

ci_layer_properties = {"InitialValues", "Exco", "FIP", "Thickness"}
ci = {
    "$type": "Models.Soils.Solute, Models",
    "Thickness": [
        60.0,
        110.0,
        140.0,
        240.0,
        150.0
    ],
    "InitialValues": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
    ],
    "InitialValuesUnits": 0,

    "WaterTableConcentration": 0.0,
    "D0": 0.05,
    "Exco": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
    ],
    "FIP": [
        1.0,
        1.0,
        1.0,
        1.0,
        1.0
    ],
    "DepthConstant": 0.0,
    "MaxDepthSoluteAccessible": 0.0,
    "RunoffEffectivenessAtMovingSolute": 0.0,
    "MaxEffectiveRunoff": 0.0,
    "ConcInSolution": None,
    "Name": "Cl",
    "ResourceName": None,
    "Children": [],
    "Enabled": True,
    "ReadOnly": True
}

no3 = {
    "$type": "Models.Soils.Solute, Models",
    "Thickness": [
        60.0,
        110.0,
        140.0,
        240.0,
        150.0
    ],
    "InitialValues": [
        6.503,
        2.101,
        2.101,
        1.701,
        1.701
    ],
    "InitialValuesUnits": 0,
    "WaterTableConcentration": 0.0,
    "D0": 0.05,
    "Exco": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
    ],
    "FIP": [
        1.0,
        1.0,
        1.0,
        1.0,
        1.0
    ],
    "DepthConstant": 0.0,
    "MaxDepthSoluteAccessible": 0.0,
    "RunoffEffectivenessAtMovingSolute": 0.0,
    "MaxEffectiveRunoff": 0.0,
    "ConcInSolution": None,
    "Name": "NO3",
    "ResourceName": None,
    "Children": [],
    "Enabled": True,
    "ReadOnly": False
}

nh4 = {
    "$type": "Models.Soils.Solute, Models",
    "Thickness": [
        60.0,
        110.0,
        140.0,
        240.0,
        150.0
    ],
    "InitialValues": [
        0.599,
        0.1,
        0.1,
        0.1,
        0.1
    ],
    "InitialValuesUnits": 0,
    "WaterTableConcentration": 0.0,
    "D0": 0.05,
    "Exco": [
        1.0,
        1.0,
        1.0,
        1.0,
        1.0
    ],
    "FIP": [
        1.0,
        1.0,
        1.0,
        1.0,
        1.0
    ],
    "DepthConstant": 0.0,
    "MaxDepthSoluteAccessible": 0.0,
    "RunoffEffectivenessAtMovingSolute": 0.0,
    "MaxEffectiveRunoff": 0.0,
    "ConcInSolution": None,
    "Name": "NH4",
    "ResourceName": None,
    "Children": [],
    "Enabled": True,
    "ReadOnly": False
}

urea = {
    "$type": "Models.Soils.Solute, Models",
    "Thickness": [
        60.0,
        110.0,
        140.0,
        240.0,
        150.0
    ],
    "InitialValues": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
    ],
    "InitialValuesUnits": 1,
    "WaterTableConcentration": 0.0,
    "D0": 0.05,
    "Exco": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0
    ],
    "FIP": [
        1.0,
        1.0,
        1.0,
        1.0,
        1.0
    ],
    "DepthConstant": 0.0,
    "MaxDepthSoluteAccessible": 0.0,
    "RunoffEffectivenessAtMovingSolute": 0.0,
    "MaxEffectiveRunoff": 0.0,
    "ConcInSolution": None,
    "Name": "Urea",
    "ResourceName": None,
    "Children": [],
    "Enabled": True,
    "ReadOnly": True
}


def geometric_layers(*,
                     max_depth,
                     top_thickness=20,
                     growth=1.3,
                     max_thickness=100,

                     ):
    layers = []

    total = 0
    dz = top_thickness

    while total < max_depth:
        dz = min(dz, max_thickness)

        if total + dz > max_depth:
            dz = max_depth - total

        layers.append(round(dz, 1))

        total += dz
        dz *= growth

    return layers
