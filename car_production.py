import time
import json
import random

from osbrain import run_agent
from osbrain import run_nameserver


JASON_FILE = None


def messaging(agent, part, units):
    agent.log_info('Provide {}. Remains {}'.format(part, units))


def reply_units(agent, message):
    with open('resources.json', 'r') as file:
        data = json.load(file)

    if message == "engine":
        data['current_stocks']['engine'] -= 1
        messaging(agent, message, data['current_stocks']['engine'])
        if data['current_stocks']['engine'] == 12:
            agent.log_info("Sent engine refill request")
            agent.send('company_a', 'engine_refill')
    elif message == "chassis":
        data['current_stocks']['chassis'] -= 1
        messaging(agent, message, data['current_stocks']['chassis'])
        if data['current_stocks']['chassis'] == 12:
            agent.log_info("Sent chassis refill request")
            agent.send('company_a', 'chassis_refill')
    elif message == "cabin":
        data['current_stocks']['cabin'] -= 1
        # messaging(agent, message, data['current_stocks']['cabin'])
        if data['current_stocks']['cabin'] == 10:
            # agent.log_info("Sent cabin refill request")
            agent.send('company_b', 'refill')
    else:
        agent.log_warning("No parts registered: {}".format(message))

    with open('resources.json', 'w') as output_file:
        json.dump(data, output_file)
    return 1


def reply_inspection(agent, message):
    result = random.choice(['good', 'moderate', 'considerable', 'bad'])
    agent.log_info("Test results : {}".format(result))
    if result in ['good', 'moderate']:
        return 1
    return 0


def refill_main_parts_late(agent, message):
    if message == "engine_refill":
        agent.log_info("Order request to fill engine. Will take 10 hours...")
        time.sleep(10)
    elif message == "chassis_refill":
        agent.log_info("Order request to fill chassis. Will take 4 hours...")
        time.sleep(4)


def process_refill_engine(agent, message):
    with open('resources.json', 'r') as file:
        data = json.load(file)

    agent.log_info("Receiving Order as {}".format(message))

    data['current_stocks']['engine'] = data['stocks']['engine']
    agent.log_info("Engine Process completed with {}".format(data['current_stocks']['cabin']))
    with open('resources.json', 'w') as output_file:
        json.dump(data, output_file)


def process_refill_chassis(agent, message):
    with open('resources.json', 'r') as file:
        data = json.load(file)

    agent.log_info("Receiving Order as {}".format(message))

    data['current_stocks']['chassis'] = data['stocks']['chassis']
    agent.log_info("Chassis Process completed with {}".format(data['current_stocks']['chassis']))
    with open('resources.json', 'w') as output_file:
        json.dump(data, output_file)


def refill_cabins_late(agent, message):
    agent.log_info("Order request to do {}".format(message))
    time.sleep(2)
    return message


def process_refill_cabin(agent, message):
    with open('resources.json', 'r') as file:
        data = json.load(file)

    agent.log_info("Receiving Order as {}".format(message))

    data['current_stocks']['cabin'] = data['stocks']['cabin']
    agent.log_info("Cabin Process completed with {}".format(data['current_stocks']['cabin']))
    with open('resources.json', 'w') as output_file:
        json.dump(data, output_file)


if __name__ == '__main__':

    # System deployment
    ns = run_nameserver()

    product_line = run_agent('Production_Line')
    engine = run_agent('Toyota_Engine')
    chassis = run_agent('Toyota_Chassis')
    cabin = run_agent('Toyota_Cabin')
    inspector = run_agent('Authorised_Inspector')
    company_a = run_agent('Company_Denso')
    company_b = run_agent('Company_Yusawa')

    # Create Reply-Request agents
    address_engine = engine.bind('REP', alias='engine', handler=reply_units)
    address_chassis = chassis.bind('REP', alias='chassis', handler=reply_units)
    address_cabin = cabin.bind('REP', alias='cabin', handler=reply_units)
    address_inspector = cabin.bind('REP', alias='inspector', handler=reply_inspection)
    product_line.connect(address_engine, alias='engine')
    product_line.connect(address_chassis, alias='chassis')
    product_line.connect(address_cabin, alias='cabin')
    product_line.connect(address_inspector, alias='inspector')

    # Create Async Reply-Request agents
    address_company_a = company_a.bind('ASYNC_REP', handler=refill_main_parts_late)
    engine.connect(address_company_a, alias='company_a', handler=process_refill_engine)
    chassis.connect(address_company_a, alias='company_a', handler=process_refill_chassis)
    address_company_b = company_b.bind('ASYNC_REP', handler=refill_cabins_late)
    cabin.connect(address_company_b, alias='company_b', handler=process_refill_cabin)

    REQ_UNITS = 10
    current_units = 0
    while current_units < REQ_UNITS:
        product_line.send('engine', 'engine')
        reply_by_engine = product_line.recv('engine')
        time.sleep(1)

        product_line.send('chassis', 'chassis')
        reply_by_chassis = product_line.recv('chassis')
        time.sleep(1)

        product_line.send('cabin', 'cabin')
        reply_by_cabin = product_line.recv('cabin')
        time.sleep(1)

        product_line.send('inspector', '')
        reply_by_inspector = product_line.recv('inspector')
        time.sleep(1)

        total_units = reply_by_engine + reply_by_chassis + reply_by_cabin + reply_by_inspector
        if total_units == 4:
            current_units += 1

    ns.shutdown()
