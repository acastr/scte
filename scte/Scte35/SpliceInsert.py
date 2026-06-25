import copy
import bitstring
from scte.Scte35._logging import resolve_logger

class SpliceInsert:
    def __init__(self, bitarray_data, init_dict=None, logger=None):
        self._log = resolve_logger(logger)

        if init_dict:
            self.splice_insert = init_dict
            return

        self.splice_insert = {}

        self.splice_insert['splice_event_id'] = bitarray_data.read("uint:32")
        self.splice_insert['splice_event_cancel_indicator'] = bitarray_data.read("bool")

        bitarray_data.pos += 7

        if not self.splice_insert['splice_event_cancel_indicator']:
            self.splice_insert['out_of_network_indicator'] = bitarray_data.read("bool")
            self.splice_insert['program_splice_flag'] = bitarray_data.read("bool")
            self.splice_insert['duration_flag'] = bitarray_data.read("bool")
            self.splice_insert['splice_immediate_flag'] = bitarray_data.read("bool")

            bitarray_data.pos += 4

            if self.splice_insert['program_splice_flag'] and not self.splice_insert['splice_immediate_flag']:
                self.splice_insert['splice_time'] = self.splice_time(bitarray_data)

            if not self.splice_insert['program_splice_flag']:
                self.splice_insert['component_count'] = bitarray_data.read("uint:8")
                self.splice_insert['components'] = []

                for _ in range(self.splice_insert['component_count']):
                    component = {}
                    component['component_tag'] = bitarray_data.read("uint:8")

                    if not self.splice_insert['splice_immediate_flag']:
                        component['splice_time'] = self.splice_time(bitarray_data)

                    self.splice_insert['components'].append(component)

            if self.splice_insert['duration_flag']:
                self.splice_insert['break_duration'] = self.break_duration(bitarray_data)

            self.splice_insert['unique_program_id'] = bitarray_data.read("uint:16")
            self.splice_insert['avail_num'] = bitarray_data.read("uint:8")
            self.splice_insert['avails_expected'] = bitarray_data.read("uint:8")

    def break_duration(self, bitarray_data):
        break_duration = {}
        break_duration["auto_return"] = bitarray_data.read("bool")

        bitarray_data.pos += 6

        break_duration["duration"] = bitarray_data.read("uint:33")

        return break_duration

    def splice_time(self, bitarray_data):
        splice_time = {}
        splice_time["time_specified_flag"] = bitarray_data.read("bool")

        if splice_time["time_specified_flag"]:
            bitarray_data.pos += 6
            splice_time["pts_time"] = bitarray_data.read("uint:33")
        else:
            bitarray_data.pos += 7

        return splice_time

    @staticmethod
    def splice_time_serialize(splice_time):
        """Serialize a splice_time() structure. Reserved bits are set to 1."""
        if splice_time["time_specified_flag"]:
            return bitstring.pack(
                'bool, uint:6, uint:33',
                True, 1, splice_time["pts_time"])
        return bitstring.pack('bool, uint:7', False, 1)

    @staticmethod
    def break_duration_serialize(break_duration):
        """Serialize a break_duration() structure. Reserved bits are set to 1."""
        return bitstring.pack(
            'bool, uint:6, uint:33',
            break_duration["auto_return"], 1, break_duration["duration"])

    def serialize(self):
        """Serialize this splice_insert() command back into a bitstring.

        Mirrors the parsing performed in __init__ branch for branch. Reserved
        bits are emitted with a value of 1, matching the other serializers in
        this library.
        """
        result = bitstring.pack(
            'uint:32, bool, uint:7',
            self.splice_insert['splice_event_id'],
            self.splice_insert['splice_event_cancel_indicator'],
            1)

        if self.splice_insert['splice_event_cancel_indicator']:
            return result

        result += bitstring.pack(
            'bool, bool, bool, bool, uint:4',
            self.splice_insert['out_of_network_indicator'],
            self.splice_insert['program_splice_flag'],
            self.splice_insert['duration_flag'],
            self.splice_insert['splice_immediate_flag'],
            1)

        if self.splice_insert['program_splice_flag'] and not self.splice_insert['splice_immediate_flag']:
            result += self.splice_time_serialize(self.splice_insert['splice_time'])

        if not self.splice_insert['program_splice_flag']:
            result += bitstring.pack('uint:8', self.splice_insert['component_count'])
            for component in self.splice_insert['components']:
                result += bitstring.pack('uint:8', component['component_tag'])
                if not self.splice_insert['splice_immediate_flag']:
                    result += self.splice_time_serialize(component['splice_time'])

        if self.splice_insert['duration_flag']:
            result += self.break_duration_serialize(self.splice_insert['break_duration'])

        result += bitstring.pack(
            'uint:16, uint:8, uint:8',
            self.splice_insert['unique_program_id'],
            self.splice_insert['avail_num'],
            self.splice_insert['avails_expected'])

        return result

    @property
    def as_dict(self):
        return copy.deepcopy(self.splice_insert)

    def __str__(self):
        return str(self.splice_insert)

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_dict(cls, input_dict):
        # Need to do input checking here
        return cls(bitarray_data=None, init_dict=input_dict)
