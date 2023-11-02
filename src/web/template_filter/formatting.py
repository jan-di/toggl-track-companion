from datetime import datetime


class Formatting:
    @staticmethod
    def format_number(number: int):
        if number == 0:
            return f'<span class="text-muted">{number}</span>'
        else:
            return f"<span>{number}</span>"

    @staticmethod
    def format_percentage(number: float, precision: int = 2):
        if number is None:
            return "---%"
        return f"{round(float(number) * 100, precision)}%"

    @staticmethod
    def format_time(total_seconds: int):
        minutes, seconds = divmod(abs(total_seconds), 60)
        hours, minutes = divmod(minutes, 60)

        result = f"{hours:02}:{minutes:02}:{seconds:02}"
        muted_length = len(result) - len(result.lstrip(":0"))
        if muted_length > 0:
            result = f'<span class="text-muted">{result[:muted_length]}</span>{result[muted_length:]}'
        return f'{"-" if total_seconds < 0 else "&nbsp;"}{result}'

    @staticmethod
    def format_datetime(input_dt: datetime):
        return input_dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def format_weekday(weekday: int, length: int = None):
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        return weekdays[weekday][:length]
