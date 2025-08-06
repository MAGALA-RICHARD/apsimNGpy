import os
from pathlib import Path
import re

# Define the path to the config file using pathlib for better cross-platform support
DLL_DIR = str(Path(__file__).parent.parent / 'dll')


def start_pythonnet():
    import pythonnet
    try:
        if pythonnet.get_runtime_info() is None:
            return pythonnet.load("coreclr")
    except:
        print("dotnet not found, trying alternate runtime")
        return pythonnet.load()


start_pythonnet()
import clr

clr.AddReference(os.path.join(DLL_DIR, 'CastBridge'))
from CastBridge import CastHelper


# a more pythonic version

def cast_as(model, model_class):
    return CastHelper.CastAs[model_class](model)


simple_rotation_code = """
using Models.Soils;
using System.Collections.Generic;
using APSIM.Shared.Utilities;
using Models.PMF;
using Models.Interfaces;
using Models.Core;
using System;

namespace Models
{
    [Serializable]
    public class Script : Model
    {
        [Link] IClock Clock;
        [Link] ISummary Summary;
        
        [Description("Rotation Sequence (comma separated crop names)")]
        public string[] Crops { get; set; }
        
        // Repeating cycle of input crops. Don't loop on this, loop on Crops
        private IEnumerable<string> cropsEnum()
        {
            var counter = 0;
            while (true)
            {
                yield return Crops[counter];
                ++counter;
                if (counter >= Crops.Length)
                    counter = 0;
            }
        }
        
        private IEnumerator<string> cropCycle;
        
        [Description("Next crop to sow in the simple rotation.")]
        public string NextCrop
        { get => cropCycle.Current; }
        
        [EventSubscribe("StartOfSimulation")]
        private void Init(object sender, EventArgs e)
        {
            // TODO: Error if Crops is empty.
            cropCycle = cropsEnum().GetEnumerator();
            // Set to first value.
            cropCycle.MoveNext();
        }

        [EventSubscribe("PlantEnding")]
        private void OnEndCrop(object sender, EventArgs e)
        {
            // Currently assumes only one crop in the ground, so does not check if the  
            // harvested crop is this script's current crop.
            var old = NextCrop;
            cropCycle.MoveNext();
            var _new = NextCrop;
            Summary.WriteMessage(this, $"Rotation finished with {old}, next up: {_new}.", MessageType.Information);
        }
    }
}
"""

sow_on_fixed_date = """
using APSIM.Shared.Utilities;
using Models.Utilities;
using Models.Soils;
using Models.PMF;
using Models.Core;
using System;
using System.Linq;

namespace Models
{
    [Serializable]
    public class Script : Model
    {
        [Link] Clock Clock;
        [Link] Fertiliser Fertiliser;
        [Link] Summary Summary;
        [Link] Soil Soil;
        
        [Description("Rotation manager name")]
        public Manager RotationManager { get; set; }
        [Separator("Sowing Info")]
        
        [Description("Crop")]
        public IPlant Crop { get; set; }

        [Description("Sowing date (d-mmm)")]
        public string SowDate { get; set; }

        [Display(Type = DisplayType.CultivarName)]
        [Description("Cultivar to be sown")]
        public string CultivarName { get; set; }

        [Description("Sowing depth (mm)")]
        public double SowingDepth { get; set; }

        [Description("Row spacing (mm)")]
        public double RowSpacing { get; set; }

        [Description("Plant population (/m2)")]
        public double Population { get; set; }

        [EventSubscribe("DoManagement")]
        private void OnDoManagement(object sender, EventArgs e)
        {
            if (DateUtilities.WithinDates(SowDate, Clock.Today, SowDate))
            {
                Crop.Sow(population: Population, cultivar: CultivarName, depth: SowingDepth, rowSpacing: RowSpacing);    
            }
        }
    }
}
"""

sow_using_variable_rule = """
    using Models.Interfaces;
    using APSIM.Shared.Utilities;
    using Models.Utilities;
    using Models.Soils;
    using Models.PMF;
    using Models.Core;
    using System;
    using System.Linq;
    using Models.Climate;
    
    namespace Models
    {
        [Serializable]
        public class Script : Model
        {
            [Link] private Clock Clock;
            [Link] private Fertiliser Fertiliser;
            [Link] private Summary Summary;
            [Link] private Soil Soil;
            private Accumulator accumulatedRain;
            [Link]
            private ISoilWater waterBalance;
            
            [Description("Rotation manager name")]
            public Manager RotationManager { get; set; }
            [Separator("Sowing Info")]
            
            [Description("Crop")]
            public IPlant Crop { get; set; }
    
            [Description("Start of sowing window (d-mmm)")]
            public string StartDate { get; set; }
    
            [Description("End of sowing window (d-mmm)")]
            public string EndDate { get; set; }
    
            [Description("Minimum extractable soil water for sowing (mm)")]
            public double MinESW { get; set; }
    
            [Description("Accumulated rainfall required for sowing (mm)")]
            public double MinRain { get; set; }
    
            [Description("Duration of rainfall accumulation (d)")]
            public int RainDays { get; set; }
    
            [Display(Type = DisplayType.CultivarName)]
            [Description("Cultivar to be sown")]
            public string CultivarName { get; set; }
    
            [Description("Sowing depth (mm)")]
            public double SowingDepth { get; set; }
    
            [Description("Row spacing (mm)")]
            public double RowSpacing { get; set; }
    
            [Description("Plant population (/m2)")]
            public double Population { get; set; }
            
            
            [EventSubscribe("StartOfSimulation")]
            private void OnSimulationCommencing(object sender, EventArgs e)
            {
                accumulatedRain = new Accumulator(this, "[Weather].Rain", RainDays);
            }
    
            [EventSubscribe("DoManagement")]
            private void OnDoManagement(object sender, EventArgs e)
            {
                accumulatedRain.Update();
                
                if (DateUtilities.WithinDates(StartDate, Clock.Today, EndDate) &&
                    !Crop.IsAlive &&
                    MathUtilities.Sum(waterBalance.ESW) > MinESW &&
                    accumulatedRain.Sum > MinRain)
                {
                    Crop.Sow(population: Population, cultivar: CultivarName, depth: SowingDepth, rowSpacing: RowSpacing);    
                }
            }
        }
    }
"""

harvest = """using APSIM.Shared.Utilities;
        using Models.Utilities;
        using Models.Soils;
        using Models.PMF;
        using Models.Core;
        using System;
        using System.Linq;
        
        namespace Models
        {
            [Serializable] 
            public class Script : Model
            {
                [Description("Crop")]
                public IPlant Crop { get; set; }
                
                [EventSubscribe("DoManagement")]
                private void OnDoManagement(object sender, EventArgs e)
                {
                    if (Crop.IsReadyForHarvesting)
                    {
                        Crop.Harvest();
                        Crop.EndCrop();
                    }
                }
            }
        }
       """

fertilizer_at_sow = """
    using Models.Soils;
using System;
using System.Linq;
using Models.Core;
using Models.PMF;
namespace Models
{
    [Serializable]
    public class Script : Model
    {
        [Link] Clock Clock;
        [Link] Fertiliser Fertiliser;
        
        [Description("Crop to be fertilised")]
        public IPlant Crop { get; set; }

        [Description("Type of fertiliser to apply? ")] 
        [Display(Type = DisplayType.FertiliserType)]public string FertiliserType { get; set; }
    
        [Description("Amount of fertiliser to be applied (kg/ha)")]
        public double Amount { get; set; }
        
        [Description("Fertilise depth (mm)")]
        public double FertiliseDepth { get; set; }
        
        [EventSubscribe("Sowing")]
        private void OnSowing(object sender, EventArgs e)
        {
            Model crop = sender as Model;
            if (Crop != null && crop.Name.ToLower() == (Crop as IModel).Name.ToLower())
                Fertiliser.Apply(amount: Amount, type: FertiliserType, depth: FertiliseDepth);
        }
    }
}
"""
new_property = '\n        public int RotationIndex { get; set; }\n'

import re


def update_manager_code(old_code, description, typeof, var_name):
    getter = '{ get; set; }'
    new_variable = [
        f'        [Description("{description}")]',
        f'        public {typeof} {var_name}  {getter}',
        ''
    ]

    lines = old_code.splitlines()

    for i in range(1, len(lines)):
        # Match line with [Description(...)]
        if re.match(r'\s*\[Description\(".*?"\)\]', lines[i - 1]) and \
                re.match(r'\s*public\s+[\w<>\[\]]+\s+\w+\s*\{\s*get;\s*set;\s*\}', lines[i]):
            insert_at = i + 2  # skip one line after the property
            lines[insert_at:insert_at] = new_variable
            break  # insert only once

    # Join and print or store
    updated_code = '\n'.join(lines)
    return updated_code

# simple_rotation_code = update_manager_code(simple_rotation_code, 'rotation', typeof='String')
