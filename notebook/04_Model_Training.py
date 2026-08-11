import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

X_final = pd.read_csv("../data/X_final.csv")
Y_encoded = pd.read_csv(
    "../data/Y_encoded.csv"
).values.ravel()

# Create the model
decision_tree = DecisionTreeClassifier(
    random_state=42
)

# Train the model
decision_tree.fit(
    X_train,
    Y_train
)

# Make predictions
Y_pred = decision_tree.predict(
    X_test
)

# Calculate accuracy
accuracy = accuracy_score(
    Y_test,
    Y_pred
)

print("=" * 50)
print("Decision Tree Model")
print("=" * 50)

print(f"Training Samples : {X_train.shape[0]}")
print(f"Testing Samples  : {X_test.shape[0]}")
print(f"Accuracy         : {accuracy:.4f}")

print("=" * 50)


# RANDOM FOREST
random_forest = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

# Train model
random_forest.fit(
    X_train,
    Y_train
)

# Make prediction
rf_predictions = random_forest.predict(
    X_test
)

# Calculate accuracy
rf_accuracy = accuracy_score(
    Y_test,
    rf_predictions
)

print(f"Random Forest Accuracy: {rf_accuracy:.4f}")

print("=" * 50)
print("Random Forest Model")
print("=" * 50)

print(f"Number of Trees : {random_forest.n_estimators}")
print(f"Training Samples: {X_train.shape[0]}")
print(f"Testing Samples : {X_test.shape[0]}")
print(f"Accuracy        : {rf_accuracy:.4f}")

print("=" * 50)

import pandas as pd
comparison = pd.DataFrame({
    "Model": [
        "Decision Tree",
        "Random Forest"
    ],
    "Accuracy": [
        accuracy,
        rf_accuracy
    ]
})

comparison
logistic_model = LogisticRegression(
    max_iter=1000,
    random_state=42
)

logistic_model.fit(
    X_train,
    Y_train
)

lr_predictions = logistic_model.predict(
    X_test
)

lr_accuracy = accuracy_score(
    Y_test,
    lr_predictions
)
print("=" * 10)
print("Logistic Regression Model")
print(f"Logistic Regression Accuracy: {lr_accuracy:.4f}")

#UPDATE COMPARISON TABLE
comparison = pd.concat(
    [
        comparison,
        pd.DataFrame({
            "Model": ["Logistic Regression"],
            "Accuracy": [lr_accuracy]
        })
    ],
    ignore_index=True
)
comparison
svm_model = SVC(
    kernel="linear",
    random_state=42
)

# Train model
svm_model.fit(
    X_train,
    Y_train
)

svm_predictions = svm_model.predict(
    X_test
)

svm_accuracy = accuracy_score(
    Y_test,
    svm_predictions
)

print(f"SVM Accuracy: {svm_accuracy:.4f}")

comparison.loc[len(comparison)] = [
    "Support Vector Machine",
    svm_accuracy
]

comparison
