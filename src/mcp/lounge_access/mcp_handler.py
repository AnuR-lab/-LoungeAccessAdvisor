"""
This module defines tools that interact with an external API client.
"""

def tool_example_1(api_client):
    """
    Example tool that interacts with the API client to retrieve a list of domains.
    """
    domains = api_client.get_tool_example_1()
    if domains:
        return [{"name": domain['name'], "id": domain['id']} for domain in domains]
    return []


def tool_example_2(parameter_1, parameter_2, api_client):
    """
    Example tool that takes two parameters and interacts with the API client.
    """
    #assets = datazone_client.get_assets(domain_id=domain_id, project_id=project_id)
    tool_response = api_client.get_tool_example_2(parameter_1, parameter_2)
    
    if tool_response:
        return {"parameter_1": parameter_1, "parameter_2": parameter_2, "tool_response": tool_response}
    return {"parameter_1": parameter_1, "parameter_2": parameter_2, "tool_response": None}

