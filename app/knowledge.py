knowledge_base = {}

def update_knowledge(data):
    node_id = data.node_id
    if node_id not in knowledge_base:
        knowledge_base[node_id] = []
    knowledge_base[node_id].append(data)
    print(f"Updated knowledge base: {knowledge_base}")

def get_knowledge():
    return knowledge_base
