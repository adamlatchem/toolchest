""" Code to convert incoming buffer to table """
import utils


class FixedKeyColumn():
    """ Metadata for a single key at static position. """

    def __init__(self):
        super().__init__()

        # Defaults
        self.key = 0

        self.get_metadata = lambda rows: {'key': self.key}


class DelimitedTextRecordParser():
    """ A tabulator config mixin to read input as series of textual 'lines' """

    def __init__(self):
        super().__init__()

        # Defaults
        self.encoding = 'utf-8'
        self.record_delimiter = '\n'

        self.read_available_bytes = utils.read_available_bytes
        self.parse_records = lambda buffer: utils.bytes_to_unicode_records(
            buffer, self.record_delimiter, self.encoding)


class DelimitedTextFieldParser(DelimitedTextRecordParser, FixedKeyColumn):
    """ A tabulator config mixin to read input as series of textual 'lines' """

    def __init__(self):
        super().__init__()

        # Defaults
        self.field_delimiter = '\t'
        self.key = 0

        self.parse_fields = lambda record: record.split(self.field_delimiter)


class SyslogConfig(DelimitedTextRecordParser, FixedKeyColumn):
    """ A canned config when reporting from tcpdump """

    def __init__(self):
        super().__init__()

        self.encoding = 'utf-8'
        self.record_delimiter = '\n'
        self.key = 2

        def field_parser(record):
            tmp = record.split(':')
            if len(tmp) > 3:
                shs = tmp[2].split(' ')
                if len(shs) == 3:
                    second, host, system = shs
                    date = ' '.join(tmp[0:2]) + ' ' + second
                    date = date[:9] + ':' + date[10:12] + ':' + date[13:]
                    system = system.split('[')[0]
                    return [date, host, system, ':'.join(tmp[3:])]
            print('Failed to parse: ', record)
        self.parse_fields = field_parser


class TcpDumpConfig(DelimitedTextRecordParser, FixedKeyColumn):
    """ A canned config when reporting from tcpdump """

    def __init__(self):
        super().__init__()

        self.encoding = 'utf-8'
        self.record_delimiter = '\n'
        self.key = 2

        def field_parser(record):
            tmp = record.split('>')
            if len(tmp) == 2:
                leader = tmp[0].split(' ')
                leader2 = tmp[1].split(':')
                return [leader[0], leader[1], leader[2], leader2[0], ':'.join(leader2[1:])]
            else:
                # ARP
                tmp = record.split(' ')
                return [tmp[0], tmp[1], tmp[2], tmp[3], ' '.join(tmp[4:])]
        self.parse_fields = field_parser


class WeblogConfig(DelimitedTextRecordParser, FixedKeyColumn):
    """ A canned config when reporting from web logfile """

    def __init__(self):
        super().__init__()

        self.encoding = 'utf-8'
        self.record_delimiter = '\n'
        self.key = 5

        def field_parser(record):
            tmp = record.split(' ')
            date = ' '.join(tmp[3:5])
            return [tmp[0], tmp[1], tmp[2], date, tmp[5], tmp[6], tmp[7],
                    tmp[8], tmp[9], tmp[10], tmp[11], ' '.join(tmp[12:])]
        self.parse_fields = field_parser


class Tabulator():
    """ The tabulator has a dynamic config that supplies records split into
    fields that are then converted to tables. """

    def __init__(self):
        super().__init__()

        # Defaults
        self.replay_bytes = []
        self.bytes_history = []
        self.partial_record = b''
        self.config = DelimitedTextFieldParser()

    def replay(self):
        """ Replay buffer history - useful when changing config. """
        self.replay_bytes = self.bytes_history
        self.bytes_history = []
        self.partial_record = b''

    def read_or_replay_records(self):
        """ Read or replay records - handles partial records """
        if self.replay_bytes:
            byte_string = self.replay_bytes.pop(0)
        else:
            byte_string = self.config.read_available_bytes()

        if byte_string:
            self.bytes_history.append(byte_string)
            records, self.partial_record = self.config.parse_records(
                self.partial_record + byte_string)
            return records
        else:
            return None

    def update(self):
        """ Read available data and convert to a table """
        rows = []
        records = self.read_or_replay_records()
        if records:
            metadata = self.config.get_metadata(records)
            for record in records:
                fields = self.config.parse_fields(record)
                if fields:
                    rows.append(fields)
        else:
            metadata = {}
        return {'metadata': metadata, 'rows': rows}
