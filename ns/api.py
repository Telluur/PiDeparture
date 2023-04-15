from datetime import datetime as dt
import requests
import constants


def fetch_trains(station='esk'):
    try:
        url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures?station={}".format(
            station)

        hdr = {
            # Request headers
            'Cache-Control': 'no-cache',
            'Ocp-Apim-Subscription-Key': constants.ns_api_key,
        }

        response = requests.get(url=url, headers=hdr)
        trains = response.json()['payload']['departures']

        parsed_trains = []

        for t in trains:
            if 'plannedDateTime' in t and 'actualDateTime' in t:
                planned_time = dt.strptime(
                    t['plannedDateTime'], '%Y-%m-%dT%H:%M:%S%z')
                actual_time = dt.strptime(
                    t['actualDateTime'], '%Y-%m-%dT%H:%M:%S%z')
                delay_in_minutes = int(
                    (actual_time - planned_time).total_seconds() // 60)
                planned_time = planned_time.strftime("%H:%M")
            else:
                planned_time = '-'
                delay_in_minutes = '-'

            if 'trainCategory' in t and 'direction' in t:
                service = '{} {}'.format(t['trainCategory'], t['direction'])
            else:
                service = ''

            planned_track = t['plannedTrack'] if 'plannedTrack' in t else '-'
            actual_track = t['actualTrack'] if 'actualTrack' in t else 'Bus'
            track_changed = actual_track != planned_track

            departure_status = t['departureStatus'].capitalize().replace(
                "_", " ") if 'departureStatus' in t else '-'

            cancelled = t['cancelled'] if 'cancelled' in t else '-'

            entry = {
                'time': planned_time,
                'delay': delay_in_minutes,
                'track': actual_track,
                'track_changed': track_changed,
                'service': service,
                'departure_status': departure_status,
                'cancelled': cancelled
            }

            #print(entry)
            parsed_trains.append(entry)
        print('[{}] API fetch complete'.format(dt.now().strftime("%H:%M:%S")))
        return parsed_trains
    except Exception as e:
        print(e)
        return []


empty_entry = {
    'time': '-',
    'delay': 0,
    'track': '-',
    'track_changed': False,
    'service': '-',
    'departure_status': '-',
    'cancelled': False,
}

night_entry = empty_entry | {'service': 'Suspended NS API calls till 5:00...'}
