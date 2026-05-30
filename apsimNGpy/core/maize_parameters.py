maize_params = {
    "Phenology": {
        "[Maize].Phenology.Germinating.MinSoilTemperature": 0.0,
        "[Maize].Phenology.Emerging.Target.ShootLag": 55.0,
        "[Maize].Phenology.Emerging.Target.DepthxRate.ShootRate": 0.6,
        "[Maize].Phenology.Juvenile.Target": 200.0,
        "[Maize].Phenology.FlagLeafToFlowering.Target": 50.0,
        "[Maize].Phenology.FloweringToGrainFilling.Target": 120.0,
        "[Maize].Phenology.GrainFilling.Target": 550.0,
        "[Maize].Phenology.Maturing.Target": 10.0,
        "[Maize].Phenology.MaturityToHarvestRipe.Target": 10.0,
    },

    "Structure": {
        "[Maize].Structure.zFinalLeafNumber": 15.0,
        "[Maize].Structure.FinalLeafNumber.ValueToHold.PrimordiaAtEmergence": 6.0,
        "[Maize].Structure.FinalLeafNumber.ValueToHold.PrimordiaDuringJuvenilePhase.MeanPlastochron.PreEmerg.Constant": 15.0,
        "[Maize].Structure.FinalLeafNumber.ValueToHold.PrimordiaDuringJuvenilePhase.MeanPlastochron.PostEmerg.MeanPlastochron.AccumulatedPlastochron.Plastochron.LeafTipsPerPrimordia": 0.5,
        "[Maize].Structure.FinalLeafNumber.ValueToHold.PrimordiaDuringJuvenilePhase.MeanPlastochron.PostEmerg.MeanPlastochron.Days.Constant": 1.0,
    },

    "Grain": {
        "[Maize].Grain.DMConversionEfficiency": 1.0,
        "[Maize].Grain.InitialGrainProportion": 0.05,
        "[Maize].Grain.MaximumPotentialGrainSize": 0.3,
        "[Maize].Grain.MaximumGrainsPerCob": 700.0,
        "[Maize].Grain.MinimumNConc": 0.008,
        "[Maize].Grain.MaximumNConc.InitialPhase.InitialNconc": 0.05,
        "[Maize].Grain.MaximumNConc.LinearPhase.FinalNconc": 0.013,
        "[Maize].Grain.WaterContent": 0.12,
        "[Maize].Grain.DaysGrainDevelopment.LenthOfADay": 1.0,
        "[Maize].Grain.CarbonConcentration": 0.4,
    },

    "Root": {
        "[Maize].Root.DMConversionEfficiency": 1.0,
        "[Maize].Root.SoilWaterEffect": 1.0,
        "[Maize].Root.MaxDailyNUptake": 20.0,
        "[Maize].Root.SenescenceRate": 0.005,
        "[Maize].Root.MaximumRootDepth": 1000000.0,
        "[Maize].Root.MaximumNConc": 0.01,
        "[Maize].Root.MinimumNConc": 0.01,
        "[Maize].Root.RootFrontVelocity.PotentialRootFrontVelocity.PreFlowering.RootFrontVelocity": 25.0,
        "[Maize].Root.RootFrontVelocity.RootDepthStressFactor": 1.0,
        "[Maize].Root.NitrogenDemandSwitch.Constant": 1.0,
        "[Maize].Root.SpecificRootLength": 40.0,
        "[Maize].Root.KNO3": 0.03,
        "[Maize].Root.KNH4": 0.02,
        "[Maize].Root.CarbonConcentration": 0.4,
    },

    "Leaf": {
        "[Maize].Leaf.Photosynthesis.RUE": 2.0,
        "[Maize].Leaf.StructuralFraction": 0.7,
        "[Maize].Leaf.DMConversionEfficiency": 1.0,
        "[Maize].Leaf.CarbonConcentration": 0.4,

        "CohortParameters": {
            "[Maize].Leaf.CohortParameters.DMReallocationFactor": 1.0,
            "[Maize].Leaf.CohortParameters.LeafSizeShapeParameter": 0.01,
            "[Maize].Leaf.CohortParameters.SenessingLeafRelativeSize": 1.0,
            "[Maize].Leaf.CohortParameters.MaxArea.LargestLeafPosition.RelativePositionOfLargestLeaf": 0.67,
            "[Maize].Leaf.CohortParameters.MaxArea.Skewness": 0.00025,
            "[Maize].Leaf.CohortParameters.NReallocationFactor": 1.0,
            "[Maize].Leaf.CohortParameters.DMRetranslocationFactor": 0.5,
            "[Maize].Leaf.CohortParameters.DetachmentLagDuration": 1000000.0,
            "[Maize].Leaf.CohortParameters.DetachmentDuration": 1000000.0,
            "[Maize].Leaf.CohortParameters.CriticalNConc": 0.01,
            "[Maize].Leaf.CohortParameters.MinimumNConc": 0.005,
            "[Maize].Leaf.CohortParameters.LagAcceleration.One": 1.0,
            "[Maize].Leaf.CohortParameters.LagAcceleration.Stress.StressResponseCoefficient": 2.0,
            "[Maize].Leaf.CohortParameters.SenescenceAcceleration.One": 1.0,
            "[Maize].Leaf.CohortParameters.StructuralFraction": 0.3,
            "[Maize].Leaf.CohortParameters.StorageFraction": 0.1,
        }
    }
}