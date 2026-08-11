import pandas as pd
import joblib
final_model = joblib.load("../models/final_model.pkl")
education_encoder = joblib.load("../models/education_encoder.pkl")
skills_encoder = joblib.load("../models/skills_encoder.pkl")
label_encoder = joblib.load("../models/label_encoder.pkl")

print("=" * 50)
print("Models Loaded Successfully")
print("=" * 50)

print(type(final_model))
print(type(education_encoder))
print(type(skills_encoder))
print(type(label_encoder))

# Taking User Input
# Sample User Information

education = "Bachelor's"
experience = 3
skills = [
    "Python",
    "SQL",
    "Machine Learning"
]

print("=" * 50)
print("User Information")
print("=" * 50)

print("Education :", education)
print("Experience:", experience)
print("Skills     :", skills)

education_input = pd.DataFrame(
    {
        "Education": [education]
    }
)
education_encoded = education_encoder.transform(
    education_input
)
education_df = pd.DataFrame(
    education_encoded,
    columns=education_encoder.get_feature_names_out(["Education"])
)

skills_encoded = skills_encoder.transform([skills])
skills_df = pd.DataFrame(
    skills_encoded,
    columns=skills_encoder.classes_
)

experience_df = pd.DataFrame(
    {
        "Experience Years": [experience]
    }
)

user_input = pd.concat(
    [
        education_df,
        experience_df,
        skills_df
    ],
    axis=1
)

print(user_input.shape)
predicted_label = final_model.predict(user_input)
print("Encoded Prediction:", predicted_label)

# Decode prediction
predicted_job = label_encoder.inverse_transform(predicted_label)
print("Predicted Job Role:", predicted_job[0])

print("=" * 50)
print("AI Career Advisor")
print("=" * 50)

print("Education :", education)
print("Experience:", experience)
print("Skills     :", ", ".join(skills))

print("-" * 50)

print("Recommended Job Role:")
print(predicted_job[0])

print("=" * 50)
def predict_job_role(education, experience, skills):

    # Education
    education_input = pd.DataFrame({
        "Education": [education]
    })

    education_encoded = education_encoder.transform(education_input)
    education_df = pd.DataFrame(
        education_encoded,
        columns=education_encoder.get_feature_names_out(["Education"])
    )

    # Skills
    skills_encoded = skills_encoder.transform([skills])
    skills_df = pd.DataFrame(
        skills_encoded,
        columns=skills_encoder.classes_
    )

    # Experience
    experience_df = pd.DataFrame({
        "Experience Years": [experience]
    })
    # Combine features
    user_input = pd.concat(
        [
            education_df,
            experience_df,
            skills_df
        ],
        axis=1
    )

    # Predict
    predicted_label = final_model.predict(user_input)
    predicted_job = label_encoder.inverse_transform(predicted_label)
    return predicted_job[0]
job = predict_job_role(
    education="Bachelor's",
    experience=3,
    skills=[
        "Python",
        "SQL",
        "Machine Learning"
    ]
)
print("Recommended Job:", job)
job = predict_job_role(
    education="Master's",
    experience=6,
    skills=[
        "Java",
        "Spring Boot",
        "SQL"
    ]
)

print(job)
#Take user input
print("=" * 50)
print("AI Career Advisor")
print("=" * 50)

education = input("Enter Education: ")

experience = int(input("Enter Experience (Years): "))

skills = input("Enter Skills (comma separated): ")
skill_map = {
    "python": "Python",
    "java": "Java",
    "sql": "SQL",
    "machine learning": "Machine Learning"
}

skills = [
    skill_map.get(skill.strip().lower(), skill.strip())
    for skill in skills.split(",")
]

print(skills)

job = predict_job_role(
    education,
    experience,
    skills
)
print("\n" + "=" * 50)
print("Prediction Result")
print("=" * 50)
print(f"Education : {education}")
print(f"Experience: {experience}")
print(f"Skills    : {', '.join(skills)}")
print("-" * 50)
print("Recommended Job Role:")
print(job)

print("=" * 50)
