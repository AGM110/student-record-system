class StatisticsManager:
    def __init__(self, data):
        self.data = data  

    def total_students(self):
        return len(self.data)

    def count_by_field(self, field):
        result = {}
        for student in self.data:
            key = student[field]
            result[key] = result.get(key, 0) + 1
        return result

    def students_by_program(self):
        return self.count_by_field("program")

    def students_by_year(self):
        return self.count_by_field("year")




