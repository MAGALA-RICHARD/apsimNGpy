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


#simple_rotation_code = update_manager_code(simple_rotation_code, 'rotation', typeof='String')
