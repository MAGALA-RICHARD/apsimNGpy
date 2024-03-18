def _split_df(daf):
    """
    :param daf: a data frame to be split numerically along the reset index. we are split along axis 0
    :return: a list of dataframes with single rows
    """
    daf.reset_index(drop=True, inplace=True)
    return [daf.loc[i].to_frame().T.copy(deep=True) for i in range(daf.shape[0])]