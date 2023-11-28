from datetime import datetime

# Mock Data and Constants
DAY_TRANSLATION = {
    'Monday': 'Måndag', 'Tuesday': 'Tisdag', 'Wednesday': 'Onsdag',
    'Thursday': 'Torsdag', 'Friday': 'Fredag', 'Saturday': 'Lördag', 'Sunday': 'Söndag'
}
SMS_MESSAGE = "Alarm:"

phone_book = [
    {
        "Name": "Roberts Balulis",
        "phone_number": "0707349518",
        "Active": "Yes",
        "timeSettings": [
            {
                "days": [
                    "Måndag",
                    "Tisdag"
                ],
                "startTime": "01:00",
                "endTime": "23:00",
                "lowestSeverity": "234",
                "highestSeverity": "1",
                "wordFilter": "Hög.Låg.\"Um01 motor hög temp\".-tryck"
            },
            {
                "days": [
                    "Söndag"
                ],
                "startTime": "00:00",
                "endTime": "23:59",
                "lowestSeverity": "500",
                "highestSeverity": "12",
                "wordFilter": "Motor"
            }
        ]
    }

]


async def user_notification(opcua_alarm_message:str, severity:int):
    current_time = datetime.now().time()
    current_day = datetime.now().strftime('%A')
    translated_day = DAY_TRANSLATION[current_day]

    for user in phone_book:
        if user.get('Active') == 'Yes':
            user_settings = user.get('timeSettings', [])

            for setting in user_settings:
                if translated_day in setting.get('days', []):
                    start_time = datetime.strptime(setting.get('startTime', '00:00'), '%H:%M').time()
                    end_time = datetime.strptime(setting.get('endTime', '00:00'), '%H:%M').time()
                    print("Day matched")

                    if start_time <= current_time <= end_time:
                        lowest_severity = int(setting.get('lowestSeverity', 0))
                        highest_severity = int(setting.get('highestSeverity', 100))
                        print("Time matched")

                        if lowest_severity >= severity >= highest_severity:
                            phone_number = user.get('phone_number')
                            name = user.get('Name')
                            message = f"{SMS_MESSAGE} {opcua_alarm_message}, allvarlighetsgrad: {severity}"
                            print("Severity matched")

                            word_filter = setting.get('wordFilter', '')

                            if word_filter:
                                include_words, exclude_words = parse_filter(word_filter)
                                alarm_message_lower = opcua_alarm_message.lower()

                                if (any(word in alarm_message_lower for word in include_words) and
                                    not any(word in alarm_message_lower for word in exclude_words)):

                                    print("Word filter matched")
                                    print(f"Sent SMS to {name}, {message}")
                            else:
                                print("User didn't have a word filter")
                                print(f"Sent SMS to {name}, {message}")


def parse_filter(filter_str):
    parts = filter_str.split('.')
    include_words = []
    exclude_words = []

    for part in parts:
        if part.startswith('"') and part.endswith('"'):
            include_words.append(part[1:-1].lower())
        elif part.startswith('-'):
            exclude_words.append(part[1:].lower())
        else:
            include_words.append(part.lower())

    return include_words, exclude_words


import asyncio
asyncio.run(user_notification("hej", 50))
