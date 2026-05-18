from datetime import datetime
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
import requests


class CurrencyConverterApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("620x520")
        self.root.resizable(False, False)

        # Конфигурация файлов
        self.config_file = "config.json"
        self.history_file = "history.json"

        # Загрузка ключа и истории
        self.api_key = self.load_api_key()
        self.history_data = self.load_history()

        # Список валют
        self.currencies = [
            "USD",
            "EUR",
            "RUB",
            "KZT",
            "GBP",
            "JPY",
            "CNY",
            "AED",
        ]

        # Настройка стиля элементов
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Создание интерфейса
        self.create_widgets()

        # Первоначальный вывод истории
        self.update_history_table()

    def load_api_key(self):
        """Безопасная загрузка API ключа из файла конфигурации."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    return config.get("api_key", "")
            except json.JSONDecodeError:
                return ""
        return ""

    def load_history(self):
        """Загрузка истории из файла JSON."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_history(self):
        """Сохранение обновленной истории в JSON."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history_data, f, ensure_ascii=False, indent=4)

    def create_widgets(self):
        """Создание графических элементов GUI."""
        # Главный контейнер с отступами
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Секция выбора валют и ввода суммы
        input_frame = ttk.LabelFrame(
            main_frame, text=" Параметры конвертации ", padding="10"
        )
        input_frame.pack(fill=tk.X, pady=(0, 15))

        # Валюта "Из"
        ttk.Label(input_frame, text="Из валюты:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.combo_from = ttk.Combobox(
            input_frame, values=self.currencies, width=10, state="readonly"
        )
        self.combo_from.grid(row=1, column=0, padx=5, pady=5)
        self.combo_from.set("USD")

        # Валюта "В"
        ttk.Label(input_frame, text="В валюту:").grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        self.combo_to = ttk.Combobox(
            input_frame, values=self.currencies, width=10, state="readonly"
        )
        self.combo_to.grid(row=1, column=1, padx=5, pady=5)
        self.combo_to.set("EUR")

        # Поле ввода суммы
        ttk.Label(input_frame, text="Сумма:").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.entry_amount = ttk.Entry(input_frame, width=15)
        self.entry_amount.grid(row=1, column=2, padx=5, pady=5)
        self.entry_amount.insert(0, "100")

        # Кнопка Конвертировать
        self.btn_convert = ttk.Button(
            input_frame, text="Конвертировать", command=self.convert_currency
        )
        self.btn_convert.grid(row=1, column=3, padx=15, pady=5)

        # 2. Поле вывода результата
        self.label_result = ttk.Label(
            main_frame, text="", font=("Helvetica", 14, "bold"), foreground="blue"
        )
        self.label_result.pack(pady=10)

        # 3. Таблица истории (Treeview)
        history_frame = ttk.LabelFrame(
            main_frame, text=" История запросов ", padding="10"
        )
        history_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("date", "from_val", "to_val", "result")
        self.table = ttk.Treeview(
            history_frame, columns=columns, show="headings", height=8
        )

        # Определение заголовков колонок
        self.table.heading("date", text="Дата и время")
        self.table.heading("from_val", text="Исходная сумма")
        self.table.heading("to_val", text="Результат")
        self.table.heading("result", text="Курс")

        # Настройка ширины колонок
        self.table.column("date", width=140, anchor="center")
        self.table.column("from_val", width=120, anchor="center")
        self.table.column("to_val", width=120, anchor="center")
        self.table.column("result", width=100, anchor="center")

        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(
            history_frame, orient=tk.VERTICAL, command=self.table.yview
        )
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def update_history_table(self):
        """Очищает и заново заполняет таблицу из массива сохраненной истории."""
        # Очистка таблицы
        for row in self.table.get_children():
            self.table.delete(row)

        # Заполнение данными в обратном порядке (новые записи вверху)
        for item in reversed(self.history_data):
            self.table.insert(
                "",
                tk.END,
                values=(
                    item["date"],
                    f"{item['amount_from']} {item['currency_from']}",
                    f"{item['amount_to']} {item['currency_to']}",
                    f"{item['rate']}",
                ),
            )

    def convert_currency(self):
        """Проводит валидацию, отправляет запрос к API и сохраняет результат."""
        # 1. Валидация ввода суммы
        amount_str = self.entry_amount.get().replace(",", ".").strip()

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Ошибка ввода", "Сумма должна быть положительным числом!"
            )
            return

        from_curr = self.combo_from.get()
        to_curr = self.combo_to.get()

        # Проверка на одинаковые валюты
        if from_curr == to_curr:
            messagebox.showwarning(
                "Внимание", "Выберите разные валюты для конвертации!"
            )
            return

        # 2. Проверка наличия API-ключа
        if not self.api_key:
            messagebox.showerror(
                "Ошибка конфигурации",
                "API-ключ не найден в файле config.json.\nПожалуйста, создайте файл и добавьте ключ.",
            )
            return

        # 3. Запрос к внешнему API
        url = f"https://exchangerate-api.com{self.api_key}/pair/{from_curr}/{to_curr}"

        try:
            response = requests.get(url, timeout=5)
            data = response.json()

            if response.status_code == 200 and data.get("result") == "success":
                rate = data.get("conversion_rate")
                result_amount = round(amount * rate, 2)

                # Вывод результата на экран
                self.label_result.configure(
                    text=f"{amount} {from_curr} = {result_amount} {to_curr}",
                    foreground="green",
                )

                # 4. Сохранение записи в историю
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                history_entry = {
                    "date": now,
                    "currency_from": from_curr,
                    "currency_to": to_curr,
                    "amount_from": amount,
                    "amount_to": result_amount,
                    "rate": rate,
                }

                self.history_data.append(history_entry)
                self.save_history()

                # Обновление графической таблицы
                self.update_history_table()

            else:
                error_msg = data.get("error-type", "Неизвестная ошибка")
                messagebox.showerror(
                    "Ошибка API", f"Сервер вернул ошибку: {error_msg}"
                )

        except requests.exceptions.RequestException:
            messagebox.showerror(
                "Ошибка сети",
                "Не удалось связаться с сервером. Проверьте интернет-соединение.",
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()
