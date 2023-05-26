import random
import json
import re

class Node:

    def __init__(self, id, is_traitor=False, is_commander=False):
        self.id = id
        self.is_traitor = is_traitor
        self.is_commander = is_commander
        
        self.orders = []
        self.prev_orders = []
        self.curr_orders = []

        self.logs = dict()
        self.attack_count = 0
        self.retreat_count = 0
        self.conclusion = "RETREAT"

    def send(self, target, order, round, step):
        msg = f"{self.id},{order}"

        expended_order = "ATTACK" if order[-1] == "A" else "RETREAT"
        
        if self.is_traitor and round == 1:
            msg = msg.replace(order[-1], "R" if order[-1] == "A" else "A")
            expended_order = "RETREAT" if order[-1] == "A" else "ATTACK"

        self.write_log(f"Sending {expended_order} to Node {target.id}", round, step)
        target.receive(msg, self.id, round, step, expended_order)

    def cmd_send(self, target, order):
        msg = f"{self.id},{order}"

        expended_order = "ATTACK" if order[-1] == "A" else "RETREAT"

        if self.is_traitor:
            msg = msg.replace(order, "R" if random.choice([0,1]) == 0 else "A")
            expended_order = "ATTACK" if msg[-1] == "A" else "RETREAT"
        
        self.write_log(f"Sending {expended_order} to Node {target.id}", 0, 0)
        target.receive(msg, self.id, 0, 0, expended_order)

    def receive(self, msg, sender, round, step, expended_order):
        self.orders.append(msg)
        self.curr_orders.append(msg)

        if msg[-1] == "A":
            self.attack_count += 1
        else:
            self.retreat_count += 1

        sender_node = "Commander" if sender == 0 else f"Node {sender}"
        self.write_log(f"Received {expended_order} from {sender_node}", round, step)

    def flush_orders(self):
        self.prev_orders.extend(self.curr_orders)
        self.curr_orders = []

    def write_log(self, msg, round, step):
        # self.logs.append(f"[Node {self.id}] {msg}")
        if round not in self.logs:
            self.logs[round] = dict()

        if step not in self.logs[round]:
            self.logs[round][step] = []

        self.logs[round][step].append(msg)

    def to_json(self):
        return {
            "id": self.id,
            "is_traitor": self.is_traitor,
            "is_commander": self.is_commander,
            "conclusion": self.conclusion,
            "logs": self.logs
        }
    
    def conclude(self, initial_order):       
        if self.is_commander:
            self.conclusion = "ATTACK" if initial_order == "A" else "RETREAT"
        elif self.attack_count > self.retreat_count:
            self.conclusion = "ATTACK"
            self.write_log(f"Received {self.attack_count} ATTACK and {self.retreat_count} RETREAT", "C", "C")

        if self.is_traitor:
            self.conclusion = "is a Byzantine Node"
        
        self.write_log(f"{self.conclusion}", "C", "C")



def initialize(is_traitor_status):
    nodes = []
    for i, status in enumerate(is_traitor_status):
        nodes.append(Node(i, status, i == 0))
    return nodes

def om(is_traitor_status, initial_order):
    nodes = initialize(is_traitor_status)
    m = sum(is_traitor_status)

    # Initial order from Commander
    commander = nodes[0]
    for node in nodes[1:]:
        commander.cmd_send(node, initial_order)
        node.flush_orders()    

    # Do m rounds
    for round in range(m):
        for step, sender in enumerate(nodes[1:]):

            # Rebroadcast orders from previous round
            for order in sender.prev_orders:
                for target in nodes[1:]:

                     # Skip if target is self or already received current order
                    if target == sender or f"{target.id}" in order:
                        continue

                    sender.send(target, order, round+1, step+1)
        
        for node in nodes:
            node.flush_orders()
    
    # Conclude Actions
    for node in nodes:
        node.conclude(initial_order)

    return nodes


def test(test_status=None, print_logs=False):
    initial = "A"

    status_4_1 = [False, False, False, True]
    status_4_1c = [True, False, False, False]
    status_4_2 = [False, False, True, True]
    status_6_2 = [False, False, False, True, False, False, True]
    status_4_0 = [False, False, False, False]

    if test_status is not None:
        testing_statuses = [test_status]
    else:
        testing_statuses = [status_4_1, status_4_2, status_6_2, status_4_1c, status_4_0]

    print("==========================================\n")
    for status in testing_statuses:
        nodes = om(status, initial)

        attack, retreat, byz = 0, 0, 0
        for node in nodes:
            if node.conclusion == "ATTACK":
                attack += 1
            elif node.conclusion == "RETREAT":
                retreat += 1
            else:
                byz += 1

            if print_logs:
                print(f"Node {node.id} | {node.conclusion}")
                for round in node.logs:
                    for step in node.logs[round]:
                        for log in node.logs[round][step]:
                            print(log)
                print("\n")

        consensus = "Not reached"
        if attack > retreat:
            consensus = "ATTACK"
        elif retreat > attack:
            consensus = "RETREAT"

        print(f"Initial Order: {initial}")
        print(f"Number of Nodes: {len(nodes)} | Number of Traitors: {sum(status)}")
        print(f"Traitor commander: {status[0]}")

        print("\nResult:")
        print(f"Attack: {attack} | Retreat: {retreat} | Byzantine: {byz}")
        print(f"Consensus = {consensus}")

        print("\n==========================================\n")

def serialize(nodes):
    serialized = {
        "nodes": {}
    }

    a_counter = 0
    r_counter = 0
    for node in nodes:
        serialized["nodes"][node.id] = node.to_json()
        if node.conclusion == "ATTACK":
            a_counter += 1
        elif node.conclusion == "RETREAT":
            r_counter += 1

    conclusion = "Tidak Tercapai"
    if a_counter > r_counter:
        conclusion = "Tercapai | ATTACK"
    elif r_counter > a_counter:
        conclusion = "Tercapai | RETREAT"

    serialized["conclusion"] = conclusion
    return json.dumps(serialized, indent=4)


def serialized_om(is_traitor_status, initial_order):
    nodes = om(is_traitor_status, initial_order)
    return serialize(nodes)


if __name__ == "__main__":
    test_input = [False, False, False, True]
    nodes = om(test_input, "A")
    
    serialized = serialize(nodes)
    print(serialized)