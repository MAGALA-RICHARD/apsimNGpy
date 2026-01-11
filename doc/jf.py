{
  "$type": "Models.PMF.Organs.ReproductiveOrgan, Models",
  "GrowthRespiration": 0.0,
  "MaintenanceRespiration": 0.0,
  "DMDemand": null,
  "NDemand": null,
  "DMSupply": null,
  "NSupply": null,
  "RipeStage": null,
  "potentialDMAllocation": null,
  "Live": {
    "$type": "Models.PMF.Biomass, Models",
    "Name": "Biomass",
    "ResourceName": null,
    "Children": [],
    "Enabled": true,
    "ReadOnly": false
  },
  "Dead": {
    "$type": "Models.PMF.Biomass, Models",
    "Name": "Biomass",
    "ResourceName": null,
    "Children": [],
    "Enabled": true,
    "ReadOnly": false
  },
  "Name": "Grain",
  "ResourceName": null,
  "Children": [
    {
      "$type": "Models.Functions.Constant, Models",
      "FixedValue": 1.0,
      "Units": null,
      "Name": "DMConversionEfficiency",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.Constant, Models",
      "FixedValue": 0.0,
      "Units": null,
      "Name": "RemobilisationCost",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.Constant, Models",
      "FixedValue": 0.05,
      "Units": null,
      "Name": "InitialGrainProportion",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.Constant, Models",
      "FixedValue": 0.3,
      "Units": "g",
      "Name": "MaximumPotentialGrainSize",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.Constant, Models",
      "FixedValue": 700.0,
      "Units": "number",
      "Name": "MaximumGrainsPerCob",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.PhaseLookup, Models",
      "Name": "DMDemandFunction",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.PhaseLookupValue, Models",
          "Start": "Flowering",
          "End": "StartGrainFill",
          "Name": "InitialPhase",
          "ResourceName": null,
          "Children": [
            {
              "$type": "Models.Functions.DemandFunctions.FillingRateFunction, Models",
              "Name": "FillingRateFunction",
              "ResourceName": null,
              "Children": [
                {
                  "$type": "Models.Functions.VariableReference, Models",
                  "VariableName": "[Grain].NumberFunction",
                  "Name": "NumberFunction",
                  "ResourceName": null,
                  "Children": [],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.VariableReference, Models",
                  "VariableName": "[Phenology].FloweringToGrainFilling.Target",
                  "Name": "FillingDuration",
                  "ResourceName": null,
                  "Children": [],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.VariableReference, Models",
                  "VariableName": "[Phenology].ThermalTime",
                  "Name": "ThermalTime",
                  "ResourceName": null,
                  "Children": [],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.MultiplyFunction, Models",
                  "Name": "PotentialSizeIncrement",
                  "ResourceName": null,
                  "Children": [
                    {
                      "$type": "Models.Functions.VariableReference, Models",
                      "VariableName": "[Grain].InitialGrainProportion",
                      "Name": "InitialProportion",
                      "ResourceName": null,
                      "Children": [],
                      "Enabled": true,
                      "ReadOnly": false
                    },
                    {
                      "$type": "Models.Functions.VariableReference, Models",
                      "VariableName": "[Grain].MaximumPotentialGrainSize",
                      "Name": "MaximumSize",
                      "ResourceName": null,
                      "Children": [],
                      "Enabled": true,
                      "ReadOnly": false
                    }
                  ],
                  "Enabled": true,
                  "ReadOnly": false
                }
              ],
              "Enabled": true,
              "ReadOnly": false
            }
          ],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.PhaseLookupValue, Models",
          "Start": "StartGrainFill",
          "End": "EndGrainFill",
          "Name": "LinearPhase",
          "ResourceName": null,
          "Children": [
            {
              "$type": "Models.Functions.DemandFunctions.FillingRateFunction, Models",
              "Name": "FillingRateFunction",
              "ResourceName": null,
              "Children": [
                {
                  "$type": "Models.Functions.VariableReference, Models",
                  "VariableName": "[Grain].NumberFunction",
                  "Name": "NumberFunction",
                  "ResourceName": null,
                  "Children": [],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.VariableReference, Models",
                  "VariableName": "[Phenology].GrainFilling.Target",
                  "Name": "FillingDuration",
                  "ResourceName": null,
                  "Children": [],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.VariableReference, Models",
                  "VariableName": "[Phenology].ThermalTime",
                  "Name": "ThermalTime",
                  "ResourceName": null,
                  "Children": [],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.MultiplyFunction, Models",
                  "Name": "PotentialSizeIncrement",
                  "ResourceName": null,
                  "Children": [
                    {
                      "$type": "Models.Functions.SubtractFunction, Models",
                      "Name": "ProportionLinearPhase",
                      "ResourceName": null,
                      "Children": [
                        {
                          "$type": "Models.Functions.Constant, Models",
                          "FixedValue": 1.0,
                          "Units": null,
                          "Name": "One",
                          "ResourceName": null,
                          "Children": [],
                          "Enabled": true,
                          "ReadOnly": false
                        },
                        {
                          "$type": "Models.Functions.VariableReference, Models",
                          "VariableName": "[Grain].InitialGrainProportion",
                          "Name": "InitialProportion",
                          "ResourceName": null,
                          "Children": [],
                          "Enabled": true,
                          "ReadOnly": false
                        }
                      ],
                      "Enabled": true,
                      "ReadOnly": false
                    },
                    {
                      "$type": "Models.Functions.VariableReference, Models",
                      "VariableName": "[Grain].MaximumPotentialGrainSize",
                      "Name": "MaximumSize",
                      "ResourceName": null,
                      "Children": [],
                      "Enabled": true,
                      "ReadOnly": false
                    }
                  ],
                  "Enabled": true,
                  "ReadOnly": false
                }
              ],
              "Enabled": true,
              "ReadOnly": false
            }
          ],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.Constant, Models",
      "FixedValue": 0.008,
      "Units": "g/g",
      "Name": "MinimumNConc",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.PhaseLookup, Models",
      "Name": "MaximumNConc",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.PhaseLookupValue, Models",
          "Start": "Flowering",
          "End": "StartGrainFill",
          "Name": "InitialPhase",
          "ResourceName": null,
          "Children": [
            {
              "$type": "Models.Functions.Constant, Models",
              "FixedValue": 0.05,
              "Units": null,
              "Name": "InitialNconc",
              "ResourceName": null,
              "Children": [],
              "Enabled": true,
              "ReadOnly": false
            }
          ],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.PhaseLookupValue, Models",
          "Start": "StartGrainFill",
          "End": "EndGrainFill",
          "Name": "LinearPhase",
          "ResourceName": null,
          "Children": [
            {
              "$type": "Models.Functions.Constant, Models",
              "FixedValue": 0.013,
              "Units": null,
              "Name": "FinalNconc",
              "ResourceName": null,
              "Children": [],
              "Enabled": true,
              "ReadOnly": false
            }
          ],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.Constant, Models",
      "FixedValue": 0.12,
      "Units": "g/g",
      "Name": "WaterContent",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.PhaseLookup, Models",
      "Name": "NFillingRate",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.PhaseLookupValue, Models",
          "Start": "Flowering",
          "End": "EndGrainFill",
          "Name": "GrainFilling",
          "ResourceName": null,
          "Children": [
            {
              "$type": "Models.Functions.DemandFunctions.FillingRateFunction, Models",
              "Name": "FillingRateFunction",
              "ResourceName": null,
              "Children": [
                {
                  "$type": "Models.Functions.VariableReference, Models",
                  "VariableName": "[Grain].NumberFunction",
                  "Name": "NumberFunction",
                  "ResourceName": null,
                  "Children": [],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.AddFunction, Models",
                  "Name": "FillingDuration",
                  "ResourceName": null,
                  "Children": [
                    {
                      "$type": "Models.Functions.VariableReference, Models",
                      "VariableName": "[Phenology].FloweringToGrainFilling.Target",
                      "Name": "FloweringToGrainFilling",
                      "ResourceName": null,
                      "Children": [],
                      "Enabled": true,
                      "ReadOnly": false
                    },
                    {
                      "$type": "Models.Functions.VariableReference, Models",
                      "VariableName": "[Phenology].GrainFilling.Target",
                      "Name": "GrainFilling",
                      "ResourceName": null,
                      "Children": [],
                      "Enabled": true,
                      "ReadOnly": false
                    }
                  ],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.VariableReference, Models",
                  "VariableName": "[Phenology].ThermalTime",
                  "Name": "ThermalTime",
                  "ResourceName": null,
                  "Children": [],
                  "Enabled": true,
                  "ReadOnly": false
                },
                {
                  "$type": "Models.Functions.MultiplyFunction, Models",
                  "Name": "PotentialSizeIncrement",
                  "ResourceName": null,
                  "Children": [
                    {
                      "$type": "Models.Functions.VariableReference, Models",
                      "VariableName": "[Grain].MaximumNConc.LinearPhase.FinalNconc",
                      "Name": "MaximumFinalNConc",
                      "ResourceName": null,
                      "Children": [],
                      "Enabled": true,
                      "ReadOnly": false
                    },
                    {
                      "$type": "Models.Functions.VariableReference, Models",
                      "VariableName": "[Grain].MaximumPotentialGrainSize",
                      "Name": "MaximumSize",
                      "ResourceName": null,
                      "Children": [],
                      "Enabled": true,
                      "ReadOnly": false
                    }
                  ],
                  "Enabled": true,
                  "ReadOnly": false
                }
              ],
              "Enabled": true,
              "ReadOnly": false
            }
          ],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.MultiplyFunction, Models",
      "Name": "NumberFunction",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.VariableReference, Models",
          "VariableName": "[MaximumGrainsPerCob]",
          "Name": "PotentialGrainNumber",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.LinearInterpolationFunction, Models",
          "Name": "GrowthRateFactor",
          "ResourceName": null,
          "Children": [
            {
              "$type": "Models.Functions.XYPairs, Models",
              "X": [
                0.55,
                3.3,
                6.6,
                10.0
              ],
              "Y": [
                0.0,
                0.6,
                1.0,
                1.0
              ],
              "XVariableName": null,
              "Name": "XYPairs",
              "ResourceName": null,
              "Children": [],
              "Enabled": true,
              "ReadOnly": false
            },
            {
              "$type": "Models.Functions.VariableReference, Models",
              "VariableName": "[GrowthRateGrainDevelopment]",
              "Name": "XValue",
              "ResourceName": null,
              "Children": [],
              "Enabled": true,
              "ReadOnly": false
            }
          ],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.VariableReference, Models",
          "VariableName": "[Maize].Population",
          "Name": "Population",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.ExpressionFunction, Models",
      "Expression": "[Grain].Live.Wt * 10 * 56 * 0.4536 * 2.471",
      "Name": "YieldBuPerAcre",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.AccumulateFunction, Models",
      "StartStageName": "FlagLeaf",
      "EndStageName": "StartGrainFill",
      "ResetStageName": null,
      "FractionRemovedOnCut": 0.0,
      "FractionRemovedOnHarvest": 0.0,
      "FractionRemovedOnGraze": 0.0,
      "FractionRemovedOnPrune": 0.0,
      "Name": "GrowthGrainDevelopment",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.VariableReference, Models",
          "VariableName": "[Arbitrator].DM.TotalFixationSupply",
          "Name": "DailyBiomassProduction",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.AccumulateFunction, Models",
      "StartStageName": "FlagLeaf",
      "EndStageName": "StartGrainFill",
      "ResetStageName": null,
      "FractionRemovedOnCut": 0.0,
      "FractionRemovedOnHarvest": 0.0,
      "FractionRemovedOnGraze": 0.0,
      "FractionRemovedOnPrune": 0.0,
      "Name": "DaysGrainDevelopment",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.Constant, Models",
          "FixedValue": 1.0,
          "Units": "days/day",
          "Name": "LenthOfADay",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.DivideFunction, Models",
      "Name": "GrowthRateGrainDevelopment",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.VariableReference, Models",
          "VariableName": "[GrowthGrainDevelopment]",
          "Name": "AccumulatedGrowth",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.VariableReference, Models",
          "VariableName": "[DaysGrainDevelopment]",
          "Name": "GrowthDuration",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.VariableReference, Models",
          "VariableName": "[Maize].Population",
          "Name": "Population",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.PMF.Library.BiomassRemoval, Models",
      "HarvestFractionLiveToRemove": 1.0,
      "HarvestFractionDeadToRemove": 0.0,
      "HarvestFractionLiveToResidue": 0.0,
      "HarvestFractionDeadToResidue": 0.0,
      "Name": "BiomassRemovalDefaults",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.Functions.Constant, Models",
      "FixedValue": 0.4,
      "Units": null,
      "Name": "CarbonConcentration",
      "ResourceName": null,
      "Children": [],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.PMF.NutrientPoolFunctions, Models",
      "Name": "DMDemandPriorityFactors",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.Constant, Models",
          "FixedValue": 1.0,
          "Units": null,
          "Name": "Structural",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.Constant, Models",
          "FixedValue": 1.0,
          "Units": null,
          "Name": "Metabolic",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.Constant, Models",
          "FixedValue": 1.0,
          "Units": null,
          "Name": "Storage",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    },
    {
      "$type": "Models.PMF.NutrientPoolFunctions, Models",
      "Name": "NDemandPriorityFactors",
      "ResourceName": null,
      "Children": [
        {
          "$type": "Models.Functions.Constant, Models",
          "FixedValue": 1.0,
          "Units": null,
          "Name": "Structural",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.Constant, Models",
          "FixedValue": 1.0,
          "Units": null,
          "Name": "Metabolic",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        },
        {
          "$type": "Models.Functions.Constant, Models",
          "FixedValue": 1.0,
          "Units": null,
          "Name": "Storage",
          "ResourceName": null,
          "Children": [],
          "Enabled": true,
          "ReadOnly": false
        }
      ],
      "Enabled": true,
      "ReadOnly": false
    }
  ],
  "Enabled": true,
  "ReadOnly": false
}