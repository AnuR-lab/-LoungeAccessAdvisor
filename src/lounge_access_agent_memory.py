"""
This module provides a function to set up memory tools for the Lounge Access Agent.
"""
import boto3
import uuid
from typing import Optional
from strands_tools.agent_core_memory import AgentCoreMemoryToolProvider
from bedrock_agentcore.memory import MemoryClient


def find_memory_by_name(memory_name_prefix, region: str = "us-east-1"):
    client = boto3.client("bedrock-agentcore-control", region_name="us-east-1")
    paginator = client.get_paginator("list_memories")
    memory = None
    for page in paginator.paginate():
        memory = next((obj for obj in page["memories"] if obj.get("id", "").startswith(memory_name_prefix)), None)
    return memory

def get_agent_memory_tools(session_id: Optional[str] = str(uuid.uuid4()), region: str = "us-east-1"):
    memory_client = MemoryClient(region_name=region)

    memory_name_prefix = "LoungeAccessAgentMemory"
    actorId = "loungeacccess-agent-1"
    sessionId = session_id or "default_session"

    memories = memory_client.list_memories()

    agent_memory = find_memory_by_name(memory_name_prefix, region)

    # look for your named memory
    if agent_memory is None:
        # short-term memory
        agent_memory = memory_client.create_memory(
            name=memory_name_prefix,
            description="Memory for customer conversations",
        )

        # long-term memory
        memory_client.add_summary_strategy(
            memory_id=agent_memory.get("id"),
            name="SessionSummarizer",
            description="Summarizes conversation sessions",
            namespaces=["/summaries/{actorId}/{sessionId}"])

    provider = AgentCoreMemoryToolProvider(
        memory_id=agent_memory.get("id"),
        actor_id=actorId,
        session_id=session_id,
        namespace="/users/{actorId}",  # only needed for long-term memory strategies
        region=region
    )

    return provider.tools