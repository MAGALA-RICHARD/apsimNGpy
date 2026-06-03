weather_node = {
    "$type": "Models.Climate.Weather, Models",
    "ConstantsFile": None,
    "FileName": "%root%/Examples/WeatherFiles/AU_WaggaWagga.met",
    "ExcelWorkSheetName": "",
    "Name": "Weather",
    "ResourceName": None,
    "Children": [],
    "Enabled": True,
    "ReadOnly": False,
}

clock_node = {
    "$type": "Models.Clock, Models",
    "Start": "1992-01-01T00:00:00",
    "End": "1995-12-31T00:00:00",
    "Name": "Clock",
    "ResourceName": None,
    "Children": [],
    "Enabled": True,
    "ReadOnly": False,
}

summary_node = {
    "$type": "Models.Summary, Models",
    #"Verbosity": '100',
    "Name": "SummaryFile",
    "ResourceName": None,
    #"Children": [],
    "Enabled": True,
    "ReadOnly": False,
}

plant_node = {
    "$type": "Models.PMF.Plant, Models",
    "Name": "Canola",
    "ResourceName": "Canola",
    "Children": [],
    "Enabled": True,
    "ReadOnly": False,
}
replacements=  {
  "$type": "Models.Core.Folder, Models",
  "ShowInDocs": False,
  "GraphsPerPage": 6,
  "Name": "Replacements",
  "ResourceName": None,
  "Children": [

  ],
  "Enabled": True,
  "ReadOnly": False
}

manager_node = {
  "$type": "Models.Manager, Models",
  "CodeArray": [
    "using APSIM.Numerics;",
    "using Models.Climate;",
    "using System.Linq;",
    "using System;",
    "using Models.Core;",
    "using Models.PMF;",
    "using Models.Soils;",
    "using Models.Utilities;",
    "using APSIM.Shared.Utilities;",
    "using Models.Interfaces;",
    "",
    "namespace Models",
    "{",
    "    [Serializable]",
    "    public class Script : Model",
    "    {",
    "        [Link] private Clock Clock;",
    "        [Link] private Fertiliser Fertiliser;",
    "        [Link] private Summary Summary;",
    "        [Link] private Soil Soil;",
    "        private Accumulator accumulatedRain;",
    "        [Link]",
    "        private ISoilWater waterBalance;",
    "        ",
    "        [Description(\"Crop\")]",
    "        public IPlant Crop { get; set; }",
    "",
    "        [Description(\"Start of sowing window (d-mmm)\")]",
    "        public string StartDate { get; set; }",
    "",
    "        [Description(\"End of sowing window (d-mmm)\")]",
    "        public string EndDate { get; set; }",
    "",
    "        [Description(\"Minimum extractable soil water for sowing (mm)\")]",
    "        public double MinESW { get; set; }",
    "",
    "        [Description(\"Accumulated rainfall required for sowing (mm)\")]",
    "        public double MinRain { get; set; }",
    "",
    "        [Description(\"Duration of rainfall accumulation (d)\")]",
    "        public int RainDays { get; set; }",
    "",
    "        [Display(Type = DisplayType.CultivarName)]",
    "        [Description(\"Cultivar to be sown\")]",
    "        public string CultivarName { get; set; }",
    "",
    "        [Description(\"Sowing depth (mm)\")]",
    "        public double SowingDepth { get; set; }",
    "",
    "        [Description(\"Row spacing (mm)\")]",
    "        public double RowSpacing { get; set; }",
    "",
    "        [Description(\"Plant population (/m2)\")]",
    "        public double Population { get; set; }",
    "        ",
    "        ",
    "        [EventSubscribe(\"StartOfSimulation\")]",
    "        private void OnSimulationCommencing(object sender, EventArgs e)",
    "        {",
    "            accumulatedRain = new Accumulator(this, \"[Weather].Rain\", RainDays);",
    "        }",
    "",
    "        [EventSubscribe(\"DoManagement\")]",
    "        private void OnDoManagement(object sender, EventArgs e)",
    "        {",
    "            accumulatedRain.Update();",
    "            ",
    "            if (DateUtilities.WithinDates(StartDate, Clock.Today, EndDate) &&",
    "                !Crop.IsAlive &&",
    "                MathUtilities.Sum(waterBalance.ESW) > MinESW &&",
    "                accumulatedRain.Sum > MinRain)",
    "            {",
    "                Crop.Sow(population: Population, cultivar: CultivarName, depth: SowingDepth, rowSpacing: RowSpacing);    ",
    "            }",
    "        }",
    "    }",
    "}"
  ],
  "Parameters": [
    {
      "Key": "Crop",
      "Value": "[Maize]"
    },
    {
      "Key": "StartDate",
      "Value": "1-nov"
    },
    {
      "Key": "EndDate",
      "Value": "10-jan"
    },
    {
      "Key": "MinESW",
      "Value": "100"
    },
    {
      "Key": "MinRain",
      "Value": "25"
    },
    {
      "Key": "RainDays",
      "Value": "10"
    },
    {
      "Key": "CultivarName",
      "Value": "Dekalb_XL82"
    },
    {
      "Key": "SowingDepth",
      "Value": "30"
    },
    {
      "Key": "RowSpacing",
      "Value": "750"
    },
    {
      "Key": "Population",
      "Value": "6"
    }
  ],
  "Name": "Sow using a variable rule",

}
soil_arbitrator= {
  "$type": "Models.Soils.Arbitrator.SoilArbitrator, Models",
  "Name": "SoilArbitrator",
  "ResourceName": None,
  "Children": [],

}
simple_rotation = {
  "$type": "Models.Manager, Models",
  "CodeArray": [
    "using Models.Soils;",
    "using System.Collections.Generic;",
    "using APSIM.Shared.Utilities;",
    "using Models.PMF;",
    "using Models.Interfaces;",
    "using Models.Core;",
    "using System;",
    "",
    "namespace Models",
    "{",
    "    [Serializable]",
    "    public class Script : Model",
    "    {",
    "        [Link] IClock Clock;",
    "        [Link] ISummary Summary;",
    "        ",
    "        [Description(\"Rotation Sequence (comma separated crop names)\")]",
    "        public string[] Crops { get; set; }",
    "        ",
    "        // Repeating cycle of input crops. Don't loop on this, loop on Crops",
    "        private IEnumerable<string> cropsEnum()",
    "        {",
    "            var counter = 0;",
    "            while (true)",
    "            {",
    "                yield return Crops[counter];",
    "                ++counter;",
    "                if (counter >= Crops.Length)",
    "                    counter = 0;",
    "            }",
    "        }",
    "        ",
    "        private IEnumerator<string> cropCycle;",
    "        ",
    "        [Description(\"Next crop to sow in the simple rotation.\")]",
    "        public string NextCrop",
    "        { get => cropCycle.Current; }",
    "        ",
    "        [EventSubscribe(\"StartOfSimulation\")]",
    "        private void Init(object sender, EventArgs e)",
    "        {",
    "            // TODO: Error if Crops is empty.",
    "            cropCycle = cropsEnum().GetEnumerator();",
    "            // Set to first value.",
    "            cropCycle.MoveNext();",
    "        }",
    "",
    "        [EventSubscribe(\"PlantEnding\")]",
    "        private void OnEndCrop(object sender, EventArgs e)",
    "        {",
    "            // Currently assumes only one crop in the ground, so does not check if the  ",
    "            // harvested crop is this script's current crop.",
    "            var old = NextCrop;",
    "            cropCycle.MoveNext();",
    "            var _new = NextCrop;",
    "            Summary.WriteMessage(this, $\"Rotation finished with {old}, next up: {_new}.\", MessageType.Information);",
    "        }",
    "    }",
    "}"
  ],
  "Parameters": [
    {
      "Key": "Crops",
      "Value": "Maize"
    }
  ],
  "Name": "Simple Rotation",

}
sow_maize = {
  "$type": "Models.Manager, Models",
  "CodeArray": [
    "using System;",
    "using APSIM.Core;",
    "using APSIM.Numerics;",
    "using APSIM.Shared.Utilities;",
    "using APSIM.Shared.Documentation;",
    "using Models.Climate;",
    "using Models.Core;",
    "using Models.Interfaces;",
    "using Models.PMF;",
    "using Models.Soils;",
    "using Models.Utilities;",
    "",
    "namespace Models",
    "{",
    "    [Serializable]",
    "    public class Script : Model, IStructureDependency",
    "    {",
    "        [Link] private Clock Clock;",
    "        [Link] private Summary Summary;",
    "        [Link] private ISoilWater waterBalance;",
    "",
    "        private Accumulator accumulatedRain;",
    "",
    "        public IStructure Structure { get; set; }",
    "",
    "        [Description(\"Simple Rotation Manager\")]",
    "        public Manager Rotations { get; set; }",
    "",
    "        [Separator(\"Sowing Info\")]",
    "",
    "        [Description(\"Crop\")]",
    "        public IPlant Crop { get; set; }",
    "",
    "        [Description(\"Start of sowing window (d-mmm)\")]",
    "        public string StartDate { get; set; }",
    "",
    "        [Description(\"End of sowing window (d-mmm)\")]",
    "        public string EndDate { get; set; }",
    "",
    "        [Description(\"Minimum extractable soil water for sowing (mm)\")]",
    "        public double MinESW { get; set; }",
    "",
    "        [Description(\"Accumulated rainfall required for sowing (mm)\")]",
    "        public double MinRain { get; set; }",
    "",
    "        [Description(\"Duration of rainfall accumulation (d)\")]",
    "        public int RainDays { get; set; }",
    "",
    "        [Display(Type = DisplayType.CultivarName)]",
    "        [Description(\"Cultivar to be sown\")]",
    "        public string CultivarName { get; set; }",
    "",
    "        [Description(\"Sowing depth (mm)\")]",
    "        public double SowingDepth { get; set; }",
    "",
    "        [Description(\"Row spacing (mm)\")]",
    "        public double RowSpacing { get; set; }",
    "",
    "        [Description(\"Plant population (/m2)\")]",
    "        public double Population { get; set; }",
    "",
    "        [Description(\"Must sow by end date?\")]",
    "        public bool MustSow { get; set; }",
    "",
    "        [EventSubscribe(\"StartOfSimulation\")]",
    "        private void OnSimulationCommencing(object sender, EventArgs e)",
    "        {",
    "            accumulatedRain = new Accumulator(this, \"[Weather].Rain\", RainDays);",
    "        }",
    "",
    "        [EventSubscribe(\"DoManagement\")]",
    "        private void OnDoManagement(object sender, EventArgs e)",
    "        {",
    "            accumulatedRain.Update();",
    "",
    "            if (!Crop.IsAlive &&",
    "                DateUtilities.WithinDates(StartDate, Clock.Today, EndDate))",
    "            {",
    "                double rainSum = accumulatedRain.Sum;",
    "                double eswSum = MathUtilities.Sum(waterBalance.ESW);",
    "",
    "                if ((rainSum > MinRain && eswSum > MinESW) ||",
    "                    (DateUtilities.DatesEqual(EndDate, Clock.Today) && MustSow))",
    "                {",
    "                    string thisCrop = Crop.Name.ToLower();",
    "",
    "                    string nextCrop = Rotations.GetProperty(\"NextCrop\") as string;",
    "",
    "                    if (thisCrop == (nextCrop?.ToLower() ?? thisCrop))",
    "                    {",
    "                        Crop.Sow(",
    "                            population: Population,",
    "                            cultivar: CultivarName,",
    "                            depth: SowingDepth,",
    "                            rowSpacing: RowSpacing);",
    "                    }",
    "                }",
    "            }",
    "        }",
    "    }",
    "}",
    ""
  ],
  "Parameters": [
    {
      "Key": "Rotations",
      "Value": "[Simple Rotation]"
    },
    {
      "Key": "Crop",
      "Value": "[Maize]"
    },
    {
      "Key": "StartDate",
      "Value": "1-May"
    },
    {
      "Key": "EndDate",
      "Value": "15-May"
    },
    {
      "Key": "MinESW",
      "Value": "200"
    },
    {
      "Key": "MinRain",
      "Value": "30"
    },
    {
      "Key": "RainDays",
      "Value": "3"
    },
    {
      "Key": "CultivarName",
      "Value": "B_110"
    },
    {
      "Key": "SowingDepth",
      "Value": "50"
    },
    {
      "Key": "RowSpacing",
      "Value": "750"
    },
    {
      "Key": "Population",
      "Value": "8.65"
    },
    {
      "Key": "MustSow",
      "Value": "True"
    }
  ],
  "Name": "SowMaize",

}