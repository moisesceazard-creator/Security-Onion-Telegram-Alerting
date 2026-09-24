from elastalert.enhancements import BaseEnhancement
from datetime import timedelta
from dateutil import parser as dateparser


class PHTimeEnhancement(BaseEnhancement):
    def process(self, match):
        ts = match.get('@timestamp')
        if not ts:
            return
        try:
            dt = dateparser.isoparse(ts) if hasattr(dateparser, 'isoparse') else dateparser.parse(ts)
            ph_dt = dt + timedelta(hours=8)
            match['time_ph'] = ph_dt.strftime('%Y-%m-%d %I:%M %p PHT')
        except Exception:
            match['time_ph'] = ts
