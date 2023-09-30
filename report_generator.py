from datetime import datetime
import json
import logging
import os
from pathlib import Path
import requests

logger = logging.getLogger('__name__')


class ReportGenerator:

    def __init__(self):
        """
        Инициализация директории, содержащей отчёты
        и словаря со сводными данными
        """
        self.tasks_dir = Path(__file__).cwd() / "tasks"
        self.summary_data = {}

    def check_tasks_dir(self):
        """
        Создание директории для отчётов
        """
        if not self.tasks_dir.exists():
            self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def create_summary_data(self, tasks):
        """
        Создаёт словарь со сводными данными о юзере и его задачах
        :param tasks: список словарей с информацией о задачах
        :return:
        """
        for task in tasks:
            userid = task.get('userId', None)
            if userid:
                is_completed = task['completed']
                if userid not in self.summary_data:
                    self.summary_data.setdefault(userid, {
                        'total_count': 0,
                        'count_completed': 0,
                        'count_active': 0,
                        'completed_list': [],
                        'active_list': []
                    })
                self.summary_data[userid]['total_count'] += 1
                if is_completed:
                    self.summary_data[userid]['completed_list'].append(task['title'])
                    self.summary_data[userid]['count_completed'] += 1
                else:
                    self.summary_data[userid]['active_list'].append(task['title'])
                    self.summary_data[userid]['count_active'] += 1

    def generate_reports(self, users):
        """
        Создаёт отчёты для юзеров
        :param users: список словарей с информацией о юзерах
        :return:
        """
        current_time = datetime.strftime(datetime.now(), "%d.%m.%YT%H:%M")
        for user in users:
            user_data = self.summary_data[user['id']]
            username = user['username']
            user_report = self.tasks_dir / f"{username}.txt"
            if user_report.exists():
                user_report.rename(self.tasks_dir / f'old_{user["username"]}_{current_time}.txt')

            active_list = '\n- '.join(
                task if len(task) <= 46 else f'{task[:46]}...' for task in user_data['active_list']
            )
            completed_list = '\n- '.join(
                task if len(task) <= 46 else f'{task[:46]}...' for task in user_data['completed_list']
            )

            text = (
                f"Отчёт для {user['company']['name']}.\n",
                f"{user['name']} <{user['email']}> {current_time}\n",
                f"Всего задач: {user_data['total_count']}\n\n",
                f"## Актуальные задачи: ({user_data['count_active']})\n",
                f"- {active_list}\n\n",
                f"## Завершённые задачи: ({user_data['count_completed']})\n",
                f"- {completed_list}\n",
            )
            try:
                with open(f'{user_report}', 'w', encoding="UTF-8") as file:
                    file.writelines(text)
            except Exception:
                logger.error(f"Отчёт '{username}.txt' не сформирован")
                os.remove(file.name)


def main():
    instance = ReportGenerator()
    instance.check_tasks_dir()
    try:
        users = json.loads(requests.get("https://json.medrocket.ru/users").text)
        tasks = json.loads(requests.get("https://json.medrocket.ru/todos").text)
    except requests.exceptions.ConnectionError:
        logger.error("Не удалось получить данные из API")
        return

    instance.create_summary_data(tasks)
    instance.generate_reports(users)


main()
