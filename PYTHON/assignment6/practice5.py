import os
import csv
import json


FILE_NAME = "/home/raim/Downloads/global_university_students_performance_habits_10000.csv"
OUTPUT_FOLDER = "output"


def check_files():
    print("Checking file...")

    if os.path.exists(FILE_NAME):
        print(f"File found: {FILE_NAME}")
        file_exists = True
    else:
        print(f"File not found: {FILE_NAME}")
        file_exists = False

    print("Checking output folder...")

    if os.path.exists(OUTPUT_FOLDER):
        print(f"Output folder already exists: {OUTPUT_FOLDER}/")
    else:
        os.makedirs(OUTPUT_FOLDER)
        print(f"Output folder created: {OUTPUT_FOLDER}/")

    return file_exists


def load_data(filename):
    print("Loading data...")

    try:
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            students = list(reader)

        print(f"Data loaded successfully: {len(students)} students")
        return students

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found. Please check the filename.")
        return []

    except Exception as e:
        print("Error:", e)
        return []


def preview_data(students, n=5):
    print("First 5 rows:" if n == 5 else f"First {n} rows:")
    print("-" * 30)

    for student in students[:n]:
        print(
            f"{student['student_id']} | "
            f"{student['age']} | "
            f"{student['gender']} | "
            f"{student['country']} | "
            f"GPA: {student['GPA']}"
        )

    print("-" * 30)


def analyse_gpa(students):
    gpas = []
    high_performers = 0

    for student in students:
        try:
            gpa = float(student["GPA"])
            gpas.append(gpa)

            if gpa > 3.5:
                high_performers += 1

        except ValueError:
            print(f"Warning: could not convert value for student {student['student_id']} — skipping row.")
            continue

    if len(gpas) == 0:
        return {
            "total_students": 0,
            "average_gpa": 0,
            "max_gpa": 0,
            "min_gpa": 0,
            "high_performers": 0
        }

    result = {
        "total_students": len(students),
        "average_gpa": round(sum(gpas) / len(gpas), 2),
        "max_gpa": max(gpas),
        "min_gpa": min(gpas),
        "high_performers": high_performers
    }

    return result


def lambda_map_filter_part(students):
    print("-" * 30)
    print("Lambda / Map / Filter")
    print("-" * 30)

    high_gpa = list(filter(lambda s: float(s["GPA"]) > 3.8, students))
    print(f"Students with GPA > 3.8 : {len(high_gpa)}")

    gpa_values = list(map(lambda s: float(s["GPA"]), students))
    print(f"GPA values (first 5) : {gpa_values[:5]}")

    hard_workers = list(filter(lambda s: float(s["study_hours_per_day"]) > 4, students))
    print(f"Students studying > 4 hrs : {len(hard_workers)}")

    print("-" * 30)


def save_result(result):
    with open("output/result.json", "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    print("Result saved to output/result.json")


def main():
    print("=" * 50)

    if not check_files():
        return

    students = load_data(FILE_NAME)

    if not students:
        return

    preview_data(students)

    result = analyse_gpa(students)

    print("-" * 30)
    print("GPA Analysis")
    print("-" * 30)
    print(f"Total students : {result['total_students']}")
    print(f"Average GPA : {result['average_gpa']}")
    print(f"Highest GPA : {result['max_gpa']}")
    print(f"Lowest GPA : {result['min_gpa']}")
    print(f"Students GPA>3.5 : {result['high_performers']}")
    print("-" * 30)

    lambda_map_filter_part(students)

    save_result(result)

    print("Testing error handling:")
    load_data("wrong_file.csv")

    print("=" * 50)


if __name__ == "__main__":
    main()
