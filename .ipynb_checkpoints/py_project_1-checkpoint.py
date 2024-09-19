import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def read_data(filepath):
    dataframe  = pd.read_csv(filepath);
    return dataframe

def mean_of_dataframe(dataframe):
    mean = np.mean(dataframe)
    return mean

def variance(dataframe):
    var = np.var(dataframe)
    return var

def ecart_type(dataframe):
    ect = np.std(dataframe)
    return ect


filepath_1 = "dataset/monthly-beer-production-in-austr.csv"
df = read_data(filepath_1)
mean_1 = mean_of_dataframe(df['Monthly beer production'])
var_1 = variance(df['Monthly beer production'])
ect_1 = ecart_type(df['Monthly beer production'])

plt.scatter(df['Month'], df['Monthly beer production'], s=10, c='b', label="Production serie")
plt.xlabel("time")
plt.ylabel("value")
plt.title("Temporal serie for prooduction")
plt.legend()
plt.show()

plt.plot()



print(f"{mean_1}\t{var_1}\t{ect_1}")