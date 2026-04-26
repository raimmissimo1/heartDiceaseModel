import csv
import json
import os


class FileManager:
    def __init__(self, filename):
        self.filename = filename

    def check_file(self):
        print('Checking file...')
        if os.path.exists(self.filename):
            print(f'File found: {self.filename}')
            return True

        print(f'File not found: {self.filename}')
        return False

    def create_output_folder(self, folder='output'):
        print('Checking output folder...')
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f'Output folder created: {folder}/')
        else:
            print(f'Output folder already exists: {folder}/')


class DataLoader:
    def __init__(self, filename):
        self.filename = filename
        self.students = []

    def load(self):
        print('Loading data...')
        try:
            with open(self.filename, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.students = list(reader)
            print(f'Data loaded successfully: {len(self.students)} students')
        except FileNotFoundError:
            self.students = []
            print(f'Error: file not found - {self.filename}')
        return self.students

    def preview(self, n=5):
        print(f'First {n} rows:')
        print('-' * 30)
        for student in self.students[:n]:
            print(
                f"{student.get('student_id', '')} | "
                f"{student.get('age', '')} | "
                f"{student.get('gender', '')} | "
                f"{student.get('country', '')} | "
                f"GPA: {student.get('GPA', '')}"
            )
        print('-' * 30)


class DataAnalyser:
    def __init__(self, students):
        self.students = students
        self.result = {}

    def analyse(self):
        gpas = []
        for student in self.students:
            try:
                gpas.append(float(student.get('GPA', 0)))
            except (TypeError, ValueError):
                continue

        if gpas:
            self.result = {
                'avg_gpa': sum(gpas) / len(gpas),
                'max_gpa': max(gpas),
                'min_gpa': min(gpas),
                'high_gpa_count': sum(1 for gpa in gpas if gpa > 3.5),
            }
        else:
            self.result = {
                'avg_gpa': 0,
                'max_gpa': 0,
                'min_gpa': 0,
                'high_gpa_count': 0,
            }

        return self.result

    def print_results(self):
        print('-' * 30)
        print('GPA Analysis')
        print('-' * 30)
        print('Total students :', len(self.students))
        print('Average GPA :', round(self.result.get('avg_gpa', 0), 2))
        print('Highest GPA :', self.result.get('max_gpa', 0))
        print('Lowest GPA :', self.result.get('min_gpa', 0))
        print('Students GPA>3.5 :', self.result.get('high_gpa_count', 0))
        print('-' * 30)


class ResultSaver:
    def __init__(self, result, output_path):
        self.result = result
        self.output_path = output_path

    def save_json(self):
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(self.result, f, indent=4)
            print(f'Result saved to {self.output_path}')
        except OSError as exc:
            print(f'Error saving result: {exc}')


def main():
    filename = 'global_university_students_performance_habits_10000.csv'
    fm = FileManager(filename)
    if not fm.check_file():
        print('Stopping program.')
        return

    fm.create_output_folder()

    dl = DataLoader(filename)
    dl.load()
    dl.preview()

    analyser = DataAnalyser(dl.students)
    analyser.analyse()
    analyser.print_results()

    saver = ResultSaver(analyser.result, os.path.join('output', 'result.json'))
    saver.save_json()


if __name__ == '__main__':
    main()
