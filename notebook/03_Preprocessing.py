import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import MultiLabelBinarizer
import joblib

# Load Training Dataset
df = pd.read_csv("../data/training_data.csv")
df.head()

# Select Input Features
X = df[
    [
        "Education",
        "Experience Years",
        "Skills"
    ]
]

# Select Target
Y = df["Job Role"]
print("Feature Shape :", X.shape)
print("Target Shape :", Y.shape)
label_encoder = LabelEncoder()

# Encode Target Variable
Y_encoded = label_encoder.fit_transform(Y)
print("Total Job Roles :", len(label_encoder.classes_))
print("\nFirst 10 Job Roles")
print(label_encoder.classes_[:10])

education_encoder = OneHotEncoder(
    sparse_output=False,
    handle_unknown="ignore"
)

education_encoded = education_encoder.fit_transform(
    X[["Education"]]
)

education_df = pd.DataFrame(
    education_encoded,
    columns=education_encoder.get_feature_names_out(
        ["Education"]
    ),
    index=X.index
)

print(education_df.shape)
education_df.head()
X_final = pd.concat(
    [
        education_df,
        experience_df,
        skills_df
    ],
    axis=1
)

print("Final Shape:", X_final.shape)
X_final.head()
skills_list = X["Skills"].str.split("|")
skills_encoder = MultiLabelBinarizer()
skills_encoded = skills_encoder.fit_transform(
    skills_list
)
skills_df = pd.DataFrame(
    skills_encoded,
    columns=skills_encoder.classes_,
    index=X.index
)
print(skills_df.shape)
skills_df.head()
experience_df = X[
    [
        "Experience Years"
    ]
]

experience_df.head()

## 3.5 Combine All Features
X_final = pd.concat(
    [
        education_df,
        experience_df,
        skills_df
    ],
    axis=1
)

print("=" * 50)
print("Final Feature Matrix")
print("=" * 50)

print("Rows :", X_final.shape[0])
print("Columns :", X_final.shape[1])

print("=" * 50)

X_final.head()

print(X_final.dtypes.unique())

joblib.dump(
    label_encoder,
    "../models/label_encoder.pkl"
)

joblib.dump(
    education_encoder,
    "../models/education_encoder.pkl"
)

joblib.dump(
    skills_encoder,
    "../models/skills_encoder.pkl"
)

print("Encoders Saved Successfully")

# Save processed features
X_final.to_csv("../data/X_final.csv", index=False)

# Save encoded target

pd.DataFrame(Y_encoded, columns=["Job Role"]).to_csv(
    "../data/Y_encoded.csv",
    index=False
)
print("Number of Job Roles:", len(label_encoder.classes_))
print(pd.Series(Y_encoded).value_counts())
print(df["Job Role"].value_counts().describe())
print(df["Job Role"].value_counts().head(10))
duplicates = X_final.duplicated().sum()
print("Duplicate Feature Rows:", duplicates)
