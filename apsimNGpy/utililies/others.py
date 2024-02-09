def remove_missing_tables(sp):
    print(len(sp))
    before = len(sp)
    for counter, i in enumerate(sp):
        if df_has_nan(i[0]) or df_has_nan(i[1]) or df_has_nan(i[2]):
            sp.pop(counter)
    after = len(sp)
    print(before - after, "had empty columns")
    return sp


