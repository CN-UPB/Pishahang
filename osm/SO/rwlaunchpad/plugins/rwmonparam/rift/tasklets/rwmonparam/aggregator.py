"""
# 
#   Copyright 2016 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

@file aggregator.py
@author Varun Prasad (varun.prasad@riftio.com)
@date 09-Jul-2016

"""
import abc
import functools


class IncompatibleAggregationType(Exception):
    pass

class InvalidAggregationType(Exception):
    pass

class InvalidAggregationOperation(Exception):
    pass

class InvalidAggregationValues(Exception):
    pass


def make_aggregator(field_types):
    """A factory method to create the aggregator based on the field type
    [value_interger, value_string or value_decimal] 
    
    Args:
        field_types (list): list of field types to aggregate
        values (list): List of values
        aggregation_type (str): Type of aggregation.
    
    Returns:
        subclass of ValueAggregator
    
    Raises:
        InvalidAggregationType: If Unknown aggregation type is provided
        InvalidAggregationValues: Raised if a mix of field types are provided.
    """
    if len(set(field_types)) != 1:
        raise InvalidAggregationValues(
            "Multiple value types provided for aggrgation {}".format(field_types))

    field_type = field_types[0]

    if field_type == IntValueAggregator.field_name():
        return IntValueAggregator()
    elif field_type == DecimalValueAggregator.field_name():
        return DecimalValueAggregator()
    elif field_type == StringValueAggregator.field_name():
        return StringValueAggregator()

    raise InvalidAggregationType("Invalid aggregation type")


class ValueAggregator():
    """Base class that defines all the basic operations.
    
    Attributes:
        aggregation_type (str): Aggregation type to be used to select the
                appropriate method.
        values (list): List of values to aggregate.
    """
    @classmethod
    @abc.abstractmethod
    def field_name(self):
        pass

    def average(self, values):
        raise InvalidAggregationOperation(
                "Invalid operation AVERAGE for {}".format(self.values))

    def sum(self, values):
        raise InvalidAggregationOperation(
                "Invalid operation SUM for {}".format(self.values))

    def maximum(self, values):
        raise InvalidAggregationOperation(
                "Invalid operation MAXIMUM for {}".format(self.values))

    def minimum(self, values):
        raise InvalidAggregationOperation(
                "Invalid operation MINIMUM for {}".format(self.values))

    def count(self, values):
        raise InvalidAggregationOperation(
                "Invalid operation COUNT for {}".format(self.values))

    def aggregate(self, aggregation_type, values):
        OP_MAP = {
                "AVERAGE": self.average,
                "SUM": self.sum,
                "MAXIMUM": self.maximum,
                "MINIMUM": self.minimum,
                "COUNT": self.count
            }

        op_func = OP_MAP.get(aggregation_type, None)

        if op_func is None:
            raise InvalidAggregationType("Unknown Aggregation type provided.")

        return self.field_name(), op_func(values)


class StringValueAggregator(ValueAggregator):

    @classmethod
    def field_name(self):
        return "value_string"


class DecimalValueAggregator(ValueAggregator):

    @classmethod
    def field_name(self):
        return "value_decimal"

    def average(self, values):
        avg = functools.reduce(lambda x, y: x + y, values) / len(values)
        return avg

    def sum(self, values):
        return functools.reduce(lambda x, y: x + y, values)

    def maximum(self, values):
        return max(values)

    def minimum(self, values):
        return min(values)

    def count(self, values):
        return len(values)


class IntValueAggregator(DecimalValueAggregator):

    @classmethod
    def field_name(self):
        return "value_integer"

    def average(self, values):
        avg = functools.reduce(lambda x, y: x + y, values) / len(values)
        return int(avg)
