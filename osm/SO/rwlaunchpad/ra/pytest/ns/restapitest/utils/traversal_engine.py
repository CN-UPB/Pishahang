
from .imports import * # noqa


def populate_data(data_type, original=True, test_value={}, keys={}):
    """Generate data from schema depends its Data-type
    Args:
        data_type (string): data_type from the test IP json
        original (boolean): if it is True,
                            will generate normal JSON with randon
                            values
        test_value (dict): will be like this {'string': '-1'}, means, if
                           string data typr comes, data will be -1
        keys (dict): if this is present, value testing for this particular
                     key
    Returns:
        string_ (string): string value
    """

    if original:
        if (isinstance(data_type, dict)):
            if 'enumeration' in data_type:
                string_ = list(data_type['enumeration']['enum'])[0]
                return string_
            if 'leafref' in data_type:
                data_type = 'leafref'
            if 'union' in data_type:
                data_type = 'union'

        if data_type == 'string':
            string_ = ''.join(choice(ascii_lowercase) for i in range(12))
        elif data_type == 'uint64':
            string_ = uuid.uuid4().int & (1 << 64) - 1
        elif data_type == 'uint8':
            string_ = uuid.uuid4().int & (1 << 8) - 1
        elif data_type == 'uint32':
            string_ = uuid.uuid4().int & (1 << 32) - 1
        elif data_type == 'uint16':
            string_ = uuid.uuid4().int & (1 << 16) - 1
        elif data_type == 'decimal64':
            string_ = float(decimal.Decimal('%d.%d'
                                            % (random.randint(0, 2134342),
                                               random.randint(0, 999))))
        elif data_type == 'int64':
            string_ = random.randint(0, 1000000000000)
        elif data_type == 'int32':
            string_ = random.randint(0, 1000000000)
        elif data_type == 'int16':
            string_ = random.randint(0, 10000)
        elif data_type == 'leafref':
            string_ = 'leafref_data-type'
        elif data_type == 'union':
            string_ = socket.inet_ntoa(
                struct.pack('>I', random.randint(1, 0xffffffff)))
        elif data_type == 'boolean':
            string_ = True
        else:
            string_ = data_type

        return string_
    else:
        if (isinstance(data_type, dict)):
            if 'enumeration' in data_type:
                string_ = list(data_type['enumeration']['enum'])[0]
                return string_
            if 'leafref' in data_type:
                data_type = 'leafref'
            if 'union' in data_type:
                data_type = 'union'

        # print(data_type, test_value)
        if not (isinstance(data_type, dict)):
            if keys and keys[list(keys)[0]]:
                if list(keys.values())[0] in keys:
                    if data_type in test_value:
                        return test_value[data_type]
            else:
                if data_type in test_value:
                    return test_value[data_type]

        if data_type == 'string':
            string_ = ''.join(choice(ascii_lowercase) for i in range(12))
        elif data_type == 'uint64':
            string_ = uuid.uuid4().int & (1 << 64) - 1
        elif data_type == 'uint8':
            string_ = uuid.uuid4().int & (1 << 8) - 1
        elif data_type == 'uint32':
            string_ = uuid.uuid4().int & (1 << 32) - 1
        elif data_type == 'uint16':
            string_ = uuid.uuid4().int & (1 << 16) - 1
        elif data_type == 'decimal64':
            string_ = float(decimal.Decimal('%d.%d'
                                            % (random.randint(0, 99999999),
                                               random.randint(0, 999))))
        elif data_type == 'int64':
            string_ = random.randint(0, 99999999)
        elif data_type == 'int32':
            string_ = random.randint(0, 999999)
        elif data_type == 'int16':
            string_ = random.randint(0, 999999)
        elif data_type == 'leafref':
            string_ = 'leafref_data-type'
        elif data_type == 'union':
            string_ = socket.inet_ntoa(
                struct.pack('>I', random.randint(1, 0xffffffff)))
        elif data_type == 'boolean':
            string_ = True
        else:
            string_ = data_type

        return string_


def traverse_it(it, path='', data_json={}, original=True, test_value={},
                test_key=None, avoid=[], depth=0, max_depth=0):
    """Main recursicve traversel method, which will go through the schema
    and generate data JSON

    Args:
        it (json): schema
        data_json (dict): used to generate the data for particular key which is
                          present in this dict
        original (boolean): used to generate original(complete) data JSON
        test_value (dict): data type and the corresponding value which is
                           getting replaced generated
        test_key (string): the key which is gonna get tested
        avoid (list): these keys will get avoided while JSON is getting
                      created
        depth (int): depth of the JSON
        max_depth (int: will be the max depth of the JSON)

    Returns:
        Json data
    """

    if (isinstance(it, list)):
        temp = {}
        depth += 1
        if depth == max_depth:
            return []
        for item in it:
            # print(path)

            x = traverse_it(item, path=path, data_json=data_json,
                            original=original,
                            test_value=test_value, test_key=test_key,
                            avoid=avoid,
                            depth=depth,
                            max_depth=max_depth)
            temp.update(x)
        return temp
    elif (isinstance(it, dict)):
        if 'name' in it.keys():
            if it['name'] == 'disabled':
                temp = [{it['name']: ''}, {}]
                return random.choice(temp)
            path = path + '/' + it['name']
        if 'type' in it.keys():

            if it['type'] == 'container':
                depth += 1
                if depth == max_depth:
                    return {}
                data_json = {
                    it['name']: traverse_it(it['properties'],
                                            path=path, data_json=data_json,
                                            original=original,
                                            test_value=test_value,
                                            test_key=test_key,
                                            avoid=avoid,
                                            depth=depth,
                                            max_depth=max_depth)
                }
                return data_json
            elif it['type'] == 'list':
                for item_check in it['properties']:

                    if 'data-type' in item_check:
                        if (isinstance(item_check['data-type'], dict)):
                            if 'leafref' in item_check['data-type']:
                                temp = {it['name']: []}
                                return temp
                depth += 1

                if depth == max_depth:
                    return {}

                temp = {
                    it['name']:
                    [traverse_it(it['properties'], path=path,
                                 data_json=data_json,
                                 original=original,
                                 test_value=test_value, test_key=test_key,
                                 avoid=avoid,
                                 depth=depth,
                                 max_depth=max_depth)]
                }
                return temp
            elif it['type'] == 'case':
                for item_check in it['properties']:
                    if 'data-type' in item_check:
                        if (isinstance(item_check['data-type'], dict)):
                            if 'leafref' in item_check['data-type']:
                                return {}
                depth += 1
                if depth == max_depth:
                    return {}

                return traverse_it(it['properties'][0], path=path,
                                   data_json=data_json,
                                   original=original,
                                   test_value=test_value, test_key=test_key,
                                   avoid=avoid,
                                   depth=depth,
                                   max_depth=max_depth)
            elif it['type'] == 'choice':
                depth += 1

                if depth == max_depth:
                    return {}

                return traverse_it(it['properties'][0], path=path,
                                   data_json=data_json,
                                   original=original,
                                   test_value=test_value, test_key=test_key,
                                   avoid=avoid,
                                   depth=depth,
                                   max_depth=max_depth)
            elif it['type'] == 'leaf':
                # print(data_json)
                if it['name'] in avoid:
                    return {}
                if 'data-type' in it:
                    if 'subnet-address' == it['name']:
                        data = '255.255.255.0/24'
                    elif 'numa-unaware' == it['name']:
                        data = ''
                    elif 'ephemeral' == it['name']:
                        data = ''
                    else:
                        data = populate_data(it['data-type'],
                                             original=original,
                                             test_value=test_value,
                                             keys={it['name']: test_key})
                return {it['name']: data}
            else:
                if 'subnet-address' == it['name']:
                    data = '255.255.255.0/24'
                elif 'numa-unaware' == it['name']:
                    data = ''
                elif 'ephemeral' == it['name']:
                    data = ''
                else:
                    data = populate_data(it['data-type'],
                                         original=original,
                                         test_value=test_value,
                                         keys={it['name']: test_key})
            return {it['name']: data}

        else:
            print('Error in the JSON!')
            exit(1)
