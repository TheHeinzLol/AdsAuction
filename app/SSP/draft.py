from pycountry import countries
from random import choice
import random
print(choice(list(countries)).alpha_3)

from datetime import datetime, timezone, timedelta
tz = timezone(timedelta(hours=random.randint(-12, 12)))
print(datetime.now(tz).isoformat())
