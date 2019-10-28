#!/usr/bin/env python3
#
# Must run with python 3 so unicode string works
#
# python3 ./search_analytics.py sc-domain:example.com YYYY-MM-DD YYYY-MM-DD
#
"""Download google search data and store in local database"""
import argparse
from datetime import datetime
import functools
import future
from sqlalchemy import create_engine
from gsc_query_service import CLICKS, CTR, DATE, IMPRESSIONS, KEYS, POSITION
from gsc_query_service import ROWS, SECONDARY_RESULT
import gsc_query_service
import sql_model


def register_command_line(argument_parser):
    """Register command line flags"""
    argument_parser.add_argument('--engine', type=str, default='sqlite:///./search_analytics.sqlite3',
                                 help=('Database Engine connection string e.g. '
                                       'sqlite:///./search_analytics.sqlite3'))
    argument_parser.add_argument('-v', '--verbose', action='store_true',
                                 help=('show verbose output'))


def connect_to_database(engine_connection_string, debug):
    """Connect to the database to store results

    engine_connection_string specifies the type of db e.g.
    debug is a flag to make SQL echo to screen.
    """
    engine = create_engine(engine_connection_string, echo=debug)
    sql_model.metadata.create_all(engine)
    connection = engine.connect()
    return connection


def store_data(connection, search_type, response, title):
    """Store gsc data in database

    Each row contains key(s), clicks, impressions, CTR, and average position.

    Args:
    database: The sqlalchemy database to write to
    search_type: The search type being performed
    response: The server response to be printed as a table.
    title: The title of the table.
    """
    if ROWS not in response:
        return

    table_name = title.lower().replace(' ', '_')
    table = sql_model.metadata.tables[table_name]
    rows = response[ROWS]

    for row in rows:
        if table_name == sql_model.t_search_appearance.name:
            the_date = datetime.strptime(response[DATE], '%Y-%m-%d')
            appearance = row[KEYS][0]
            statement = table.insert().values(
                search_type=search_type,
                date=the_date,
                appearance=appearance,
                clicks=row[CLICKS],
                impressions=row[IMPRESSIONS],
                ctr=row[CTR],
                average_position=row[POSITION]
            )
        else:
            statement = table.insert().values(
                search_type=search_type,
            )
            if KEYS in row:
                keys = row[KEYS]
                keys[0] = datetime.strptime(keys[0], '%Y-%m-%d')
                keys = {key: value for (key, value) in zip(
                    ['date', 'device', 'country', 'url', 'query'], keys)}
                statement = statement.values(**keys)
                if len(keys) == 5:
                    secondary_result = row[SECONDARY_RESULT]
                    statement = statement.values(
                        secondary_result=secondary_result
                    )
            statement = statement.values(
                clicks=row[CLICKS],
                impressions=row[IMPRESSIONS],
                ctr=row[CTR],
                average_position=row[POSITION]
            )

        try:
            connection.execute(statement)
        except Exception as ex:
            k = [search_type]
            k.extend(keys.values())
            if len(keys) == 5:
                k.append(row[SECONDARY_RESULT])
            k = ",".join([str(x) for x in k])
            if 'sqlite3.IntegrityError' in str(ex):
                print('Skip duplicate row %s' % (k))
            else:
                print('Row %s Exception %s' % (k, str(ex)))
                exit(1)


def main(argument_parser):
    """main program"""
    args = argument_parser.parse_args()
    debug = args.verbose
    connection = connect_to_database(args.engine, debug)
    gsc_query_service.get_data(
        argument_parser, functools.partial(store_data, connection))


if __name__ == '__main__':
    ARGUMENT_PARSER = argparse.ArgumentParser(add_help=False)
    register_command_line(ARGUMENT_PARSER)
    gsc_query_service.register_command_line(ARGUMENT_PARSER)

    main(ARGUMENT_PARSER)
