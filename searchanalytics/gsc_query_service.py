#!/usr/bin/env python3
# 234567890123456789012345678901234567890123456789012345678901234567890123456789
"""Download google search console data and augment for easy storage in a
relational schema.

To use:
1) Install the Google Python client library, as shown at
   https://developers.google.com/webmaster-tools/v3/libraries.
2) Sign up for a new project in the Google APIs console at
   https://code.google.com/apis/console.
3) Register the project to use OAuth2.0 for installed applications.
4) Copy your client ID, client secret, and redirect URL into the
   client_secrets.json file included in this package.
5) Run the app in the command-line as shown below.

Sample usage:

  $ python3 gsc_query_service.py 'sc-domain:intrepiduniverse.com' '2017-01-01'
  '2075-01-01'

Notes:
  https://support.google.com/webmasters/answer/7576553

  You can't group by search type
  search appearance can only be grouped on its own
  =>
  Full aggregate data for search type,date,country,device
  Partial breakdown data for search type,date,country,device,page,query
  Search appearance is its own thing
"""
import argparse
import sys
import time
import itertools
from googleapiclient import sample_tools


# Constants
CLICKS = 'clicks'
CTR = 'ctr'
DATE = 'date'
IMPRESSIONS = 'impressions'
KEYS = 'keys'
POSITION = 'position'
ROWS = 'rows'
SECONDARY_RESULT = 'secondary_result'


def debug(aggregate, query_breakdown, query_page_breakdown, page_breakdown, page_query_breakdown):
    """ Output debug information """
    print('A', aggregate)
    if query_breakdown:
        for row in query_breakdown:
            print('Q', row)
    if query_page_breakdown:
        for row in query_page_breakdown:
            print('q', row)
    if page_breakdown:
        for row in page_breakdown:
            print('P', row)
    if page_query_breakdown:
        for row in page_query_breakdown:
            print('p', row)


def register_command_line(argument_parser):
    """ Register command line flags """
    argument_parser.add_argument('property_uri', type=str,
                                 help=('Site or app URI to query data for (excluding '
                                       'trailing slash) e.g. sc-domain:example.com'))
    argument_parser.add_argument('start_date', type=str,
                                 help=('ISO Start date of the requested date range in '
                                       'YYYY-MM-DD format.'))
    argument_parser.add_argument('end_date', type=str,
                                 help=('ISO End date of the requested date range in '
                                       'YYYY-MM-DD format.'))


def anonymous_row(aggregate_keys, row_keys, clicks, impressions, position):
    """ Create an anonymous row under the given aggregate. """
    keys = []
    keys.extend(aggregate_keys)
    keys.extend(row_keys)
    new_row = {KEYS: keys,
               SECONDARY_RESULT: False,
               CLICKS: clicks,
               IMPRESSIONS: impressions,
               CTR: clicks / (impressions or 1),
               POSITION: position}
    return new_row


class GSCQueryService:
    """ Class to acquire Google Search Console data and interpolate omitted
    values """

    def __init__(self, argument_parser):
        """  Connect to data source taking arguments from command line """
        self.service, self.options = sample_tools.init(
            sys.argv, 'webmasters', 'v3', __doc__, __file__, parents=[argument_parser],
            scope='https://www.googleapis.com/auth/webmasters.readonly')

    def query_grand_total(self, search_type):
        """ Run a query to get grand total """
        request = {
            'startDate': self.options.start_date,
            'endDate': self.options.end_date,
            'searchType': search_type,
        }
        grand_total = self.execute_request(self.options.property_uri, request)
        return grand_total

    def query_daily_aggregates(self, search_type):
        """ Run a query to learn which dates we have data for """
        request = {
            'startDate': self.options.start_date,
            'endDate': self.options.end_date,
            'dimensions': ['date'],
            'searchType': search_type,
        }
        available_dates = self.execute_request(
            self.options.property_uri, request)

        return available_dates

    def query_device_country_aggregates(self, search_type, date):
        """ Return device and country totals for given search type and date """
        request = {
            'startDate': date,
            'endDate': date,
            'dimensions': ['date', 'device', 'country'],
            'searchType': search_type,
        }
        device_country_totals = self.execute_request(
            self.options.property_uri, request)
        return device_country_totals

    def query_breakdown(self, search_type, date, device_country_aggregates):
        """ Download data for given search type and date """
        request = {
            'startDate': date,
            'endDate': date,
            'searchType': search_type,
        }

        # Requests with omitted data
        request['dimensions'] = ['date', 'device', 'country', 'page']
        page_aggregates = self.execute_request(
            self.options.property_uri, request)

        request['dimensions'] = ['date', 'device', 'country', 'query']
        query_aggregates = self.execute_request(
            self.options.property_uri, request)

        request['dimensions'] = ['date', 'device', 'country', 'page', 'query']
        page_query_aggregates = self.execute_request(
            self.options.property_uri, request)

        request['dimensions'] = ['date', 'device', 'country', 'query', 'page']
        query_page_aggregates = self.execute_request(
            self.options.property_uri, request)

        assert_keyed_aggregate('vs. PageQuery Total ' + search_type,
                               page_aggregates,
                               page_query_aggregates,
                               4,
                               True)

        # Infer secondary data
        #
        # When grouping by query, data is aggregated by property. This means
        # there can be a mismatch between query_aggregates vs
        # query_page_aggregates.
        #
        # GOOGLE: For impressions, if a property appears twice on a search
        # results page when aggregating by property, it counts as a single
        # impression.
        query_page_secondary_rows = infer_secondary_rows(query_aggregates,
                                                         query_page_aggregates,
                                                         4)

        # Add SECONDARY_RESULT property so page_query_aggregates sum to
        # page_aggregates
        if ROWS in page_query_aggregates:
            for row in page_query_aggregates[ROWS]:
                row[SECONDARY_RESULT] = False
                keys = row[KEYS]
                key = (keys[0], keys[1], keys[2], keys[4], keys[3])
                if key in query_page_secondary_rows:
                    row[SECONDARY_RESULT] = True
                    assert_keyed_aggregate('vs. Augmented PageQuery Total ' + search_type,
                                           page_aggregates,
                                           page_query_aggregates,
                                           4,
                                           True)

        # Add SECONDARY_RESULT property so query_page_aggregates sum to
        # query_aggregates
        if ROWS in query_page_aggregates:
            for row in query_page_aggregates[ROWS]:
                row[SECONDARY_RESULT] = False
                key = tuple(row[KEYS])
                if key in query_page_secondary_rows:
                    row[SECONDARY_RESULT] = True

        # Add omitted (anonymised) rows so page_query_aggregates sum to
        # device_country_aggregates
        for aggregate in device_country_aggregates[ROWS]:
            aggregate_keys = aggregate[KEYS]

            page_breakdown = []
            if ROWS in page_aggregates:
                page_breakdown = [row for row in page_aggregates[ROWS]
                                  if row[KEYS][0:3] == aggregate_keys[0:3]]
            sum_page_clicks = sum([row[CLICKS] for row in page_breakdown])
            sum_page_impressions = sum([row[IMPRESSIONS]
                                        for row in page_breakdown])

            query_breakdown = []
            if ROWS in query_aggregates:
                query_breakdown = [row for row in query_aggregates[ROWS]
                                   if row[KEYS][0:3] == aggregate_keys[0:3]]
            sum_query_clicks = sum([row[CLICKS] for row in query_breakdown])
            sum_query_impressions = sum([row[IMPRESSIONS]
                                         for row in query_breakdown])

            page_query_breakdown = []
            if ROWS in page_query_aggregates:
                page_query_breakdown = [row for row in page_query_aggregates[ROWS]
                                        if row[KEYS][0:3] == aggregate_keys[0:3]]
            sum_secondary_clicks = sum([row[CLICKS]
                                        for row in page_query_breakdown if row[SECONDARY_RESULT]])
            sum_secondary_impressions = sum(
                [row[IMPRESSIONS] for row in page_query_breakdown if row[SECONDARY_RESULT]])

            query_page_breakdown = []
            if ROWS in query_page_aggregates:
                query_page_breakdown = [row for row in query_page_aggregates[ROWS]
                                        if row[KEYS][0:3] == aggregate_keys[0:3]]

            omitted_page_clicks = aggregate[CLICKS] + \
                sum_secondary_clicks - sum_page_clicks
            omitted_page_impressions = aggregate[IMPRESSIONS] + \
                sum_secondary_impressions - sum_page_impressions
            omitted_query_clicks = aggregate[CLICKS] - \
                sum_query_clicks
            omitted_query_impressions = aggregate[IMPRESSIONS] - \
                sum_query_impressions

            omitted_page = omitted_page_clicks != 0 or \
                omitted_page_impressions != 0
            omitted_query = omitted_query_clicks != 0 or \
                omitted_query_impressions != 0

            if omitted_page and omitted_query:
                if omitted_page_clicks == omitted_query_clicks and \
                        omitted_page_impressions == omitted_query_impressions:
                    row_pos_imp = sum([row[POSITION] * row[IMPRESSIONS]
                                       for row in query_breakdown])
                    implied_position = (
                        aggregate[POSITION] * aggregate[IMPRESSIONS] - row_pos_imp) \
                        / omitted_query_impressions
                    new_row = anonymous_row(aggregate_keys,
                                            ('*OMITTED*', '*OMITTED*'),
                                            omitted_query_clicks,
                                            omitted_query_impressions,
                                            implied_position)
                    if ROWS in page_query_aggregates:
                        page_query_aggregates[ROWS].append(new_row)
                    else:
                        page_query_aggregates[ROWS] = [new_row]
                elif omitted_page_clicks == omitted_query_clicks:
                    raise Exception("Omitted impressions mismatch page : %d vs query : %d" % (
                        omitted_page_impressions, omitted_query_impressions))
                else:
                    raise Exception("Omitted clicks mismatch page : %d vs query : %d" % (
                        omitted_page_clicks, omitted_query_clicks))
            elif omitted_page:
                if aggregate[IMPRESSIONS] != sum_page_impressions:
                    # discrepancy is explained by secondary results
                    if aggregate[IMPRESSIONS] + sum_secondary_impressions == sum_page_impressions \
                            and aggregate[CLICKS] == sum_page_clicks:
                        continue
                debug(aggregate, query_breakdown, query_page_breakdown,
                      page_breakdown, page_query_breakdown)
                raise Exception("Unexplained omitted page detected: clicks: %d impressions %d" % (
                    omitted_page_clicks, omitted_page_impressions))
            elif omitted_query:
                raise Exception("Unexplained omitted query detected: clicks: %d impressions %d" % (
                    omitted_query_clicks, omitted_query_impressions))

        # Add SECONDARY_RESULT property to page_aggregates to check
        # all secondary_impressions are accounted for
        if ROWS in page_aggregates:
            for row in page_aggregates[ROWS]:
                row[SECONDARY_RESULT] = False
                key = tuple(row[KEYS])
                second_rows = []
                for key_value in query_page_secondary_rows.items():
                    key2, row2 = key_value
                    key_tuple = (key2[0], key2[1], key2[2], key2[4])
                    if key == key_tuple:
                        second_rows.append(row2)
                if second_rows:
                    second_sum = sum([r[IMPRESSIONS] for r in second_rows])
                    if row[IMPRESSIONS] == second_sum:
                        row[SECONDARY_RESULT] = True
                    else:
                        if row[IMPRESSIONS] < second_sum:
                            debug(
                                row, None, query_page_secondary_rows.items(), None, None)
                            raise Exception(
                                'Impression mismatch during secondary processing')
                        else:
                            omitted_query_clicks = row[CLICKS] - \
                                sum([r[CLICKS] for r in second_rows])
                            omitted_query_impressions = row[IMPRESSIONS] - sum(
                                [r[IMPRESSIONS] for r in second_rows])
                            row_pos_imp = sum([row[POSITION] * row[IMPRESSIONS]
                                               for row in second_rows])
                            implied_position = (
                                row[POSITION] * row[IMPRESSIONS] - row_pos_imp) \
                                / omitted_query_impressions
                            keyword = '*OMITTED*'
                            for breakdown in page_query_breakdown:
                                if breakdown[KEYS][0] == row[KEYS][0] and \
                                        breakdown[KEYS][1] == row[KEYS][1] and \
                                        breakdown[KEYS][2] == row[KEYS][2] and \
                                        breakdown[KEYS][3] == row[KEYS][3] and \
                                        breakdown[POSITION] == implied_position and \
                                        breakdown[IMPRESSIONS] == omitted_query_impressions and \
                                        breakdown[CLICKS] == omitted_query_clicks:
                                    keyword = breakdown[KEYS][4]
                                    break
                            if keyword == '*OMITTED*':
                                raise Exception('Unable to infer keyword')
                            new_row = anonymous_row(row[KEYS][:3],
                                                    (keyword,
                                                     row[KEYS][3]),
                                                    omitted_query_clicks,
                                                    omitted_query_impressions,
                                                    implied_position)
                            query_page_secondary_rows[tuple(
                                new_row[KEYS])] = new_row

        assert_keyed_aggregate('vs. Augmented QueryPage Total ' + search_type,
                               query_aggregates,
                               query_page_aggregates,
                               4,
                               False)

        assert_keyed_aggregate('vs. Breakdown Total ' + search_type,
                               device_country_aggregates,
                               page_query_aggregates,
                               3,
                               False)

        return page_query_aggregates

    def query_search_appearance(self, search_type, date):
        """ Get search appearance data """
        request = {
            'startDate': date,
            'endDate': date,
            'dimensions': ['searchAppearance'],
            'searchType': search_type,
        }
        response = self.execute_request(self.options.property_uri, request)

        # Add the date so SQL code can be more generic
        response[DATE] = date
        return response

    def execute_request(self, property_uri, request):
        """Executes a searchAnalytics.query request.

        Args:
        service: The webmasters service to use when executing the query.
        property_uri: The site or app URI to request data for.
        request: The request to be executed.

        Returns:
        An array of response rows.
        """
        if 'rowLimit' in request:
            raise Exception('rowLimit is managed by execute_request')
        request['rowLimit'] = 25000
        response = self.service.searchanalytics().query(
            siteUrl=property_uri, body=request).execute()
        if ROWS in response:
            if len(response[ROWS]) == 25000:
                raise Exception(
                    'rowLimit reached - fix code to handle this case by adding startRow to request')
        del request['rowLimit']
        return response


def infer_secondary_rows(property_aggregates, breakdown_rows, key_length):
    """ When aggregated by property results that appear more than once on a
    SERP are given a single aggregate impression but the breakdown contains
    all. This function identifies the secondary rows."""
    if ROWS in property_aggregates and ROWS in breakdown_rows:
        secondary_rows = []
        for aggregate in property_aggregates[ROWS]:
            aggregate_keys = aggregate[KEYS]
            breakdown = []
            for breakdown_row in breakdown_rows[ROWS]:
                keys = breakdown_row[KEYS]
                if keys[0:key_length] == aggregate_keys[0:key_length]:
                    breakdown.append(breakdown_row)
            if len(breakdown) > 1:
                new_prim, new_sec = partition_rows(aggregate, breakdown)
                assert_aggregate('Secondary Inference',
                                 aggregate, new_prim)
                secondary_rows.extend(new_sec)
        return {key: row for key, row in
                zip([tuple(r[KEYS]) for r in secondary_rows], secondary_rows)}
    elif ROWS not in property_aggregates and ROWS not in breakdown_rows:
        pass
    elif ROWS not in property_aggregates:
        raise Exception('Missing property_aggregates')
    else:
        raise Exception('Missing property breakdown_rows')


def partition_rows(aggregate, details_list):
    """ Partition details_list into (primary, secondary) rows that would
    produce the aggregate. """
    for primary_length in range(1, len(details_list)):
        for candidate in itertools.combinations(details_list, primary_length):
            if check_aggregate(aggregate, candidate):
                secondaries = [x for x in details_list if x not in candidate]
                return (candidate, secondaries)
    raise Exception('Unable to partition rows')


def assert_keyed_aggregate(title, keyed_aggregates, breakdown_rows, key_length, include_secondary):
    """ Check totals for each key in keyed_aggregates against key filtered
    breakdown

    Args:
    title: displayed on failure
    keyed_aggregate: aggregate rows
    breakdown_rows: breakdown rows
    key_length: how many fields in the key to consider
    include_secondary: include secondary breakdown rows """
    if ROWS in keyed_aggregates and ROWS in breakdown_rows:
        for total in keyed_aggregates[ROWS]:
            total_keys = total[KEYS]
            breakdown = []
            for breakdown_row in breakdown_rows[ROWS]:
                keys = breakdown_row[KEYS]
                if keys[0:key_length] == total_keys[0:key_length]:
                    if include_secondary:
                        breakdown.append(breakdown_row)
                    elif not breakdown_row[SECONDARY_RESULT]:
                        breakdown.append(breakdown_row)
            assert_aggregate(str(total_keys) + ' ' + title, total, breakdown)
    elif ROWS not in keyed_aggregates and ROWS not in breakdown_rows:
        pass
    elif ROWS not in keyed_aggregates:
        raise Exception('Missing keyed_aggregates')
    else:
        raise Exception('Missing breakdown_rows')


def check_aggregate(aggregate, breakdown):
    """ Check the integrity of an aggregate row against its breakdown """
    if not check_equal(aggregate[CLICKS],
                       sum([row[CLICKS] for row in breakdown])):
        return False

    sum_impressions = sum([row[IMPRESSIONS] for row in breakdown])

    if not check_equal(aggregate[IMPRESSIONS],
                       sum_impressions):
        return False

    if not check_equal(aggregate[CTR],
                       sum([row[CLICKS] for row in breakdown]) / (sum_impressions or 1)):
        return False

    if not check_equal(aggregate[POSITION],
                       sum([row[POSITION] * row[IMPRESSIONS]
                            for row in breakdown])
                       / (sum_impressions or 1)):
        return False

    if not check_equal(aggregate[CTR], aggregate[CLICKS] / (aggregate[IMPRESSIONS] or 1)):
        return False

    for row in breakdown:
        if not check_equal(row[CTR], row[CLICKS] / (row[IMPRESSIONS] or 1)):
            return False

    return True


def assert_aggregate(title, aggregate, breakdown):
    """ Assert the integrity of an aggregate row against its breakdown """
    assert_equal(title + '. Clicks',
                 aggregate[CLICKS],
                 sum([row[CLICKS] for row in breakdown]))

    sum_impressions = sum([row[IMPRESSIONS] for row in breakdown])

    assert_equal(title + '. Impressions',
                 aggregate[IMPRESSIONS],
                 sum_impressions)

    assert_equal(title + '. CTR',
                 aggregate[CTR],
                 sum([row[CLICKS] for row in breakdown]) / (sum_impressions or 1))

    assert_equal(title + '. Position',
                 aggregate[POSITION],
                 sum([row[POSITION] * row[IMPRESSIONS] for row in breakdown])
                 / (sum_impressions or 1))

    assert_equal(title + '. Aggregate CTR',
                 aggregate[CTR], aggregate[CLICKS] / (aggregate[IMPRESSIONS] or 1))
    for row in breakdown:
        assert_equal(title + '. Breakdown CTR',
                     row[CTR], row[CLICKS] / (row[IMPRESSIONS] or 1))


def assert_equal(title, val1, val2):
    """ Check two values are equal and exit with message if not

    Args:
    title: a title for the assertion on failure
    val1: the first value to compare
    val2: the second value to compare
    """
    if abs(val1 - val2) > 0.0000000001:
        print('assert_equal FAILED: %s: %f <> %f' % (title, val1, val2))
        exit(-1)
    if val1 < 0:
        print('assert_equal FAILED: %s: %f < 0' % (title, val1))
        exit(-1)
    if val2 < 0:
        print('assert_equal FAILED: %s: %f < 0' % (title, val2))
        exit(-1)


def check_equal(val1, val2):
    """ Check two values are equal and exit with message if not

    Args:
    val1: the first value to compare
    val2: the second value to compare
    """
    return abs(val1 - val2) < 0.0000000001


def print_table(search_type, response, title):
    """Prints out a response table.

    Each row contains key(s), clicks, impressions, CTR, and average position.

    Args:
    search_type: The search type
    response: The server response to be printed as a table.
    title: The title of the table.
    """
    print('\n --' + title + ':')

    if ROWS not in response:
        print('Empty response')
        return

    rows = response[ROWS]
    row_format = '{:<10} {:<120} {:>10} {:>10} {:>10} {:>20}'
    print(row_format.format('SearchType', 'Keys',
                            'Clicks', 'Impressions', 'CTR', 'Average Position'))
    for row in rows:
        keys = ''
        # Keys are returned only if one or more dimensions are requested.
        if KEYS in row:
            keys = ','.join(row[KEYS])
        print(row_format.format(
            search_type, keys, row[CLICKS], row[IMPRESSIONS], row[CTR], row[POSITION]))


def get_data(argument_parser, process_result_function):
    """ Main data acquisition algorithm.

    Args:
    argument_parser: provides command line arguments
    process_result_function: receives the query results for further processing
    """
    source = GSCQueryService(argument_parser)

    for search_type in ['web', 'image', 'video']:
        grand_total = source.query_grand_total(search_type)
        if ROWS in grand_total:
            daily_aggregates = source.query_daily_aggregates(search_type)
            device_country_aggregates = []
            for row in daily_aggregates[ROWS]:
                date = row[KEYS][0]
                print('%s : %s' % (search_type, date))
                device_country_rows = source.query_device_country_aggregates(
                    search_type, date)
                if ROWS in device_country_rows:
                    device_country_aggregates.extend(device_country_rows[ROWS])
                    breakdown_rows = source.query_breakdown(
                        search_type, date, device_country_rows)
                    search_appearance_rows = source.query_search_appearance(
                        search_type, date)

                    process_result_function(
                        search_type, device_country_rows, 'Aggregate')
                    process_result_function(
                        search_type, breakdown_rows, 'Breakdown')
                    process_result_function(search_type, search_appearance_rows,
                                            'Search Appearance')

                # Crude API call throttle
                time.sleep(1.1)

            assert_aggregate('Grand Total vs. Device and Country Aggregate ' + search_type,
                             grand_total[ROWS][0], device_country_aggregates)
            assert_aggregate(search_type + ' Grand Total vs. Daily Aggregate ' + search_type,
                             grand_total[ROWS][0], daily_aggregates[ROWS])


if __name__ == '__main__':
    ARGUMENT_PARSER = argparse.ArgumentParser(add_help=False)
    register_command_line(ARGUMENT_PARSER)

    get_data(ARGUMENT_PARSER, print_table)
