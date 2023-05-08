from typing import Tuple

import threading
import time

from datetime import datetime as dt, timedelta
import pytz
import requests
import constants

from ns import stations


UTC_TZ = pytz.utc
LOCAL_TZ = pytz.timezone('Europe/Amsterdam')
STOCK_TRAIN = {
    'cancelled': False,

    'time': '',
    'delay': 0,

    'platform_changed': False,
    'platform': '',

    'destination_changed': False,
    'service': '',

    'rolling_stock': '',
}


class Departures:
    trains = []

    def __init__(self, station_code: str, limit: int = 10, destination_filter: list[str] = []) -> None:
        self.station_code = station_code.upper()
        self.limit = limit
        self.destination_filter = [stations.full_station_name(x).lower() for x in destination_filter]
        self.update_thread = threading.Thread(target=self._schedule)
        self.update_thread.start()

    def get_trains(self):
        return self.trains.copy()

    def _log(self, message: str):
        print(f'[{dt.now(tz=LOCAL_TZ).strftime("%H:%M:%S")}] {message}')

    def _schedule(self):
        while True:
            self._update_departures()
            time.sleep(60)

    def _update_departures(self):
        try:
            url = f'{constants.gotrain_api_base_url}/v2/departures/station/{self.station_code.upper()}'
            response = requests.get(url=url)
            trains = response.json()['departures']
        except Exception as e:
            self._log(f'API Exception: {e}')
            return

        now = dt.now(tz=UTC_TZ)
        parsed_trains = []
        for t in trains:
            try:
                new_train = STOCK_TRAIN.copy()

                '''
                Time processing
                '''
                # Parse scheduled departure time
                time = dt.strptime(t['departure_time'], '%Y-%m-%dT%H:%M:%SZ')
                time = UTC_TZ.localize(time)
                # Convert for frontend
                new_train['time'] = time.astimezone(LOCAL_TZ).strftime("%H:%M")

                # Delay in seconds
                secs = t['delay']
                # Int + floor division to convert to whole minutes
                new_train['delay'] = secs // 60

                # add delay to actual departure time
                actual_time = time + timedelta(seconds=secs)

                # Do not return this train if (time+delay) is in the past
                if now > actual_time:
                    continue

                '''
                Platform processing
                '''
                # Actual departure platform
                new_train['platform'] = t['platform_actual']
                # Whether platform has been changed
                new_train['platform_changed'] = t['platform_changed']

                '''
                Service name processing
                '''
                # Define a service prefix: Either line number or service type
                service_prefix = 'UNK'
                if t['line_number'] != None:
                    service_prefix = t['line_number']
                else:
                    service_prefix = t['type_code']

                # Get actual destination
                destination = t['destination_actual']

                # Skip this train if it's in the destination filter
                if destination.lower() in self.destination_filter:
                    continue

                # Construct service label
                new_train['service'] = f'{service_prefix} {destination}'

                # Whether destination has been changed
                new_train['destination_changed'] = destination != t['destination_planned']

                '''
                Rolling stock processing
                '''
                new_train['rolling_stock'] = self._update_rolling_stock(
                    t['service_number'], t['service_date'])

                '''
                Cancelled state
                '''
                new_train['cancelled'] = t['cancelled']

                '''
                Finalise parsing
                '''
                # Append train, if limit is parsed stop parsing.
                parsed_trains.append(new_train)
                if len(parsed_trains) >= self.limit:
                    break
            except Exception as e:
                self._log(f'Failed to parse train: {e}\r\nJSON: {str(t)}')
        self.trains = parsed_trains
        self._log(
            f'Fetched departures for {self.station_code}, took {(dt.now(tz=UTC_TZ) - now).total_seconds()}s.')

    def _update_rolling_stock(self, service_number: str, service_date: str):
        try:
            url = f'{constants.gotrain_api_base_url}/v2/services/service/{service_number}/{service_date}'
            response = requests.get(url=url)
            if response == None:
                return ''

            stops = response.json()['service']['parts'][0]['stops']
            for stop in stops:
                if stop['station']['code'] == self.station_code:
                    departing_mats = []
                    for mat in stop['material']:
                        if not mat['remains_behind']:
                            departing_mats.append(mat['type'])
                    return self._parse_rolling_stock(departing_mats)
            return ''
        except Exception as e:
            print(f'Exception: {e}')
            return ''

    def _parse_rolling_stock(self, material: list[str]) -> str:
        type = None
        total_length = 0

        for m in material:
            if 'E-LOC' in m:
                continue
            if 'DB-BER9' in m:
                type = 'BER'
                total_length += 9
                continue

            for t in ['ICM', 'VIRM', 'DDZ', 'SLT', 'FLIRT', 'SNG', 'LINT']:
                if t in m and m[-1].isnumeric():
                    type = t
                    total_length += int(m[-1])
                    continue
        if (type is not None and total_length > 0):
            return f'{type}-{total_length}'
        else:
            return ''
