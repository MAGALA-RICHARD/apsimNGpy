if __name__ == "__main__":
    model = ApsimModel('Maize')
    prob = Problem(model, "Simulation", cache_size=200, cache=True)
    prob.add_control('Manager', "Sow using a variable rule", 'Population', 'population')
    prob.add_control('Manager', "Fertilise at sowing", 'Amount', 'Nitrogen')
    ans = prob.minimize_problem(x0=[1, 0], method='Powell', bounds=[(1, 12), (0, 208)])
    print(ans)
