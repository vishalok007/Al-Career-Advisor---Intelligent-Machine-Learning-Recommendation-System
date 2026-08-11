import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("../Data/training_data.csv")

df.columns

df.dtypes

df.info()

df.isnull().sum()
df.duplicated().sum()

# Numerical summary
print(df.describe())

# Categorical summary
print(df.describe(include="object"))

# Education analysis
print(df["Education"].unique())
print(df["Education"].nunique())
print(df["Education"].value_counts())

# Job Role analysis
print(df["Job Role"].value_counts())

# Category analysis
print(df["Category"].value_counts())

education_counts = df["Education"].value_counts().head(10)

education_counts.plot(kind="bar", figsize=(10,5))

plt.title("Top 10 Education Levels")
plt.xlabel("Education")
plt.ylabel("Number of Candidates")
plt.xticks(rotation=90)

plt.show()

# Histogram
df["Experience Years"].plot(kind="hist", bins=10)
plt.title("Experience Distribution")
plt.xlabel("Years of Experience")
plt.ylabel("Number of Candidates")
plt.show()

#Pie Chart
education_counts = df["Education"].value_counts().head(8)
education_counts.plot(
    kind="pie",
    autopct="%1.1f%%",
    figsize=(8,8)
)
plt.title("Top 8 Education Levels")
plt.ylabel("")
plt.show()

plt.boxplot(df["Experience Years"])
plt.title("Experience Box Plot")
plt.show()

# Correlation matrix
numeric_df = df.select_dtypes(include="number")
corr_matrix = numeric_df.corr()
print(corr_matrix)

#Visualizing Correlation
plt.figure(figsize=(6,5))
plt.imshow(corr_matrix, cmap="coolwarm")
plt.colorbar()
plt.xticks(range(len(corr_matrix.columns)),
           corr_matrix.columns,
           rotation=0)
plt.yticks(range(len(corr_matrix.columns)),
           corr_matrix.columns)
plt.title("Correlation Heatmap")
plt.show()

numeric_df = df.select_dtypes(include="number")

print(numeric_df.columns)

print(numeric_df.corr())

# Input Features
X = df[[
    "Education",
    "Experience Years",
    "Skills"
]]

# Target Variable
Y = df["Job Role"]

X.head()

Y.head()

X = df[[
    "Resume Text",
    "Education",
    "Experience Years",
    "Skills"
]]

Y = df["Job Role"]

print(X.head())

print(Y.head())

print(X.shape)

print(Y.shape)
