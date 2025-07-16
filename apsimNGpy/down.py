import pypistats
data = pypistats.overall("apsimNgpy", total='daily', format="pandas")
data = data.groupby("category").get_group("without_mirrors").sort_values("date")

chart = data.plot(x="date", y="downloads", figsize=(10, 2))
chart.figure.show()

chart.figure.savefig("overall.png")