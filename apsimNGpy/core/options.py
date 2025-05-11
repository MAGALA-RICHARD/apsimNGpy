def nc(crop_area:float, nitrate_reduced:float):
    fixedFraction = (1-0.14) * crop_area
    print(fixedFraction)
    return (fixedFraction/6000) * nitrate_reduced