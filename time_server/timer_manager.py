import datetime

import pytz


class TimeManager:
    def __init__(self, local_timezone=None):
        if local_timezone:
            try:
                self.local_timezone = pytz.timezone(local_timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                self.local_timezone = (
                    datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
                )
        else:
            self.local_timezone = (
                datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
            )

    def _generate_word_phrase(self, h: int, minute: int) -> str:
        nums = {
            0: "o'clock",
            1: "one",
            2: "two",
            3: "three",
            4: "four",
            5: "five",
            6: "six",
            7: "seven",
            8: "eight",
            9: "nine",
            10: "ten",
            11: "eleven",
            12: "twelve",
            13: "thirteen",
            14: "fourteen",
            15: "quarter",
            16: "sixteen",
            17: "seventeen",
            18: "eighteen",
            19: "nineteen",
            20: "twenty",
            25: "twenty-five",
            30: "half",
        }

        if minute == 0:
            return f"{nums[h]} o'clock"
        elif minute == 15:
            return f"quarter past {nums[h]}"
        elif minute == 30:
            return f"half past {nums[h]}"
        elif minute == 45:
            next_h = (h % 12) + 1
            return f"quarter to {nums[next_h]}"
        elif minute < 30:
            return f"{nums.get(minute, str(minute))} past {nums[h]}"
        else:
            mins_to = 60 - minute
            next_h = (h % 12) + 1
            return f"{nums.get(mins_to, str(mins_to))} to {nums[next_h]}"

    def word_clock_for_time(
        self, timezone: str, datetime_obj: datetime.datetime
    ) -> dict:
        try:
            tz = pytz.timezone(timezone)
            local_time = datetime_obj.astimezone(tz)

            h = local_time.hour % 12 or 12
            minute = local_time.minute

            phrase = self._generate_word_phrase(h, minute)

            return {
                "timezone": timezone,
                "datetime": local_time.replace(
                    minute=minute, second=0, microsecond=0
                ).isoformat(),
                "words": phrase,
            }
        except Exception as e:
            return {
                "error": f"Error generating word clock: {e}",
                "timezone": timezone,
            }

    def word_clock(self, timezone: str, precision_minutes: int = 1) -> dict:
        try:
            tz = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            return {
                "error": f"Unknown timezone: {timezone}",
                "supported_timezones": pytz.all_timezones,
            }

        now = datetime.datetime.now(tz)
        m = now.minute
        rounded = int(round(m / precision_minutes) * precision_minutes)

        if rounded == 60:
            now += datetime.timedelta(hours=1)
            rounded = 0

        h = now.hour % 12 or 12
        minute = rounded

        phrase = self._generate_word_phrase(h, minute)

        return {
            "timezone": timezone,
            "datetime": now.replace(minute=minute, second=0, microsecond=0).isoformat(),
            "words": phrase,
        }

    def get_current_time(self, timezone: str) -> dict:
        try:
            tz = pytz.timezone(timezone)
            current_time = datetime.datetime.now(tz)

            word_time = self.word_clock(timezone)

            response = {
                "timezone": timezone,
                "datetime": current_time.isoformat(),
                "is_dst": current_time.tzinfo.dst(current_time)
                != datetime.timedelta(0),
                **word_time,
            }

            return response

        except pytz.exceptions.UnknownTimeZoneError:
            return {
                "error": f"Unknown timezone: {timezone}",
                "supported_timezones": pytz.all_timezones,
            }

    def convert_time(
        self, source_timezone: str, time_str: str, target_timezone: str
    ) -> dict:
        try:
            source_tz = pytz.timezone(source_timezone)
            target_tz = pytz.timezone(target_timezone)

            hours, minutes = map(int, time_str.split(":"))

            now = datetime.datetime.now(source_tz)
            source_datetime = now.replace(
                hour=hours, minute=minutes, second=0, microsecond=0
            )

            target_datetime = source_datetime.astimezone(target_tz)

            time_diff = target_datetime.utcoffset() - source_datetime.utcoffset()
            hours_diff = time_diff.total_seconds() / 3600

            source_word_time = self.word_clock_for_time(
                source_timezone, source_datetime
            )
            target_word_time = self.word_clock_for_time(
                target_timezone, target_datetime
            )

            response = {
                "source": {
                    "timezone": source_timezone,
                    "datetime": source_datetime.isoformat(),
                    "is_dst": source_datetime.tzinfo.dst(source_datetime)
                    != datetime.timedelta(0),
                    **source_word_time,
                },
                "target": {
                    "timezone": target_timezone,
                    "datetime": target_datetime.isoformat(),
                    "is_dst": target_datetime.tzinfo.dst(target_datetime)
                    != datetime.timedelta(0),
                    **target_word_time,
                },
                "time_difference": f"{'+' if hours_diff >= 0 else ''}{hours_diff:.1f}h",
            }

            return response

        except (pytz.exceptions.UnknownTimeZoneError, ValueError) as e:
            return {"error": str(e), "supported_timezones": pytz.all_timezones}

    @staticmethod
    def list_timezones() -> list:
        return pytz.all_timezones

    @staticmethod
    def validate_timezone(timezone: str) -> dict:
        try:
            pytz.timezone(timezone)
            return {"valid": True, "timezone": timezone}
        except pytz.exceptions.UnknownTimeZoneError:
            return {"valid": False, "timezone": timezone, "error": "Unknown timezone"}
