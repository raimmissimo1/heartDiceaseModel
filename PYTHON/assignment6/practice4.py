import pandas as pd
import os
import json
import sys

file_path = '/home/raim/Downloads/global_university_students_performance_habits_10000.csv'

print('=' * 50)

try:
    print('Checking file...')

    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding='utf-8')
        print('File found and loaded successfully')
    else:
        print('File does not exist, load from LMS')
        sys.exit()

except Exception as e:
    print('Error:', e)
    sys.exit()

folder = "output"

try:
    print("Checking output folder...")

    if os.path.exists(folder):
        print("Output folder found")
    else:
        print("Output folder not found, creating...")
        os.makedirs(folder)
        print("Output folder created successfully")
except Exception as e:
    print("Error:", e)
    sys.exit()

dict_df = df.to_dict(orient='records')

students = []

for student in dict_df:
    students.append(student)

print(f"Total number of students: {len(students)}")
print()
print("First 5 rows:")
print("-" * 30)

for student in dict_df[:5]:
    print(f"{student['student_id']} | {student['age']} | {student['gender']} | {student['country']} | GPA: {student['GPA']}")

print("-" * 30)

gpas = []
greater_than_3_5 = []

for student in students:
    gpas.append(float(student['GPA']))

gpas_avg = sum(gpas) / len(gpas)
max_gpa = max(gpas)
min_gpa = min(gpas)

for gpa in gpas:
    if gpa > 3.5:
        greater_than_3_5.append(gpa)

print('-' * 30)
print()
print("GPA Analysis")
print()
print('-' * 30)
print(f"Total number of students: {len(students)}")
print(f"Average GPA: {gpas_avg}")
print(f"Greatest GPA: {max_gpa}")
print(f"Lowest GPA: {min_gpa}")
print(f"Number of students with GPA greater than 3.5: {len(greater_than_3_5)}")

result = {
    "analysis": "GPA Statistics",
    "total_students": len(students),
    "average_gpa": round(gpas_avg, 2),
    "max_gpa": max_gpa,
    "min_gpa": min_gpa,
    "high_performers": len(greater_than_3_5)
}

with open("output/result.json", "w") as f:
    json.dump(result, f, indent=4)

print('=' * 30)
print()
print("ANALYSIS RESULT")
print()
print('=' * 30)
print(f"Total number of students: {len(students)}")
print(f"Average GPA: {gpas_avg}")
print(f"Greatest GPA: {max_gpa}")
print(f"Lowest GPA: {min_gpa}")
print(f"Number of students with GPA greater than 3.5: {len(greater_than_3_5)}")
print('=' * 30)
print()
print("Result saved to output/result.json")
print('=' * 50)
