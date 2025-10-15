"""
Main chat interface with Streamlit, including custom handoff_to_user tool that works with Streamlit UI
"""

import asyncio
import streamlit as st

from strands import Agent, tool

#from mcp_client import McpClient
from strands.models import BedrockModel

from src.mcp_client import McpClient
from src.system_prompts import SystemPrompts

def get_agent(mcp_client):
    mcp_tools = mcp_client.list_tools_sync() if mcp_client else []

    agent_model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="us-east-1",
    )

    agent = Agent(
        tools=[handoff_to_user, mcp_tools],
        model=agent_model,
        system_prompt= SystemPrompts.workflow_orchestrator()
    )

    return agent


def init_state():
    if "agent" not in st.session_state:

        mcp_client = None
        # mcp_client = McpClient(
        #     mcp_gateway_url="https://gateway-quick-start-0e31fb-asclyv6trk.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
        #     client_id="37m4g3smkv8gvmr63142i1fqge",
        #     client_secret="d623h492ngp5up91c6f07699h8rsi8bvppn3cou7vbfv1edvvpo",
        #     token_url="https://my-domain-3y2hxkiv.auth.us-east-1.amazoncognito.com/oauth2/token"
        # ).get_mcp_client()


        # Keep a single Agent instance so conversation history persists
        st.session_state.mcp_context = mcp_client.__enter__() if mcp_client else None
        st.session_state.agent = get_agent(mcp_client) #Agent(tools=[handoff_to_user])

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []  # [{"role": "user"|"assistant", "content": "..."}]
    if "pending_handoff" not in st.session_state:
        st.session_state.pending_handoff = None  # {"message": str, "breakout": bool}
    if "handoff_triggered_this_run" not in st.session_state:
        st.session_state.handoff_triggered_this_run = False

@tool
def handoff_to_user(message: str, breakout_of_loop: bool = False):
    """
    Custom handoff tool that works with Streamlit UI instead of console input.
    This replaces the built-in handoff_to_user to prevent console prompts.

    Args:
        message: The message to show to the user
        breakout_of_loop: Whether to break out of the conversation loop

    Returns:
        str: The user's response from the Streamlit UI
    """

    # Force set the session state
    st.session_state.pending_handoff = {
        "message": message,
        "breakout": breakout_of_loop
    }
    st.session_state.handoff_triggered_this_run = True
    append_user(message)

    return f"Handoff initiated: {message}. Waiting for user response..."

# ----- UI Helpers -----
def render_transcript():
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

def append_user(text: str):
    if not text or not text.strip():
        return

    st.session_state.chat_messages.append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.markdown(text)

def append_assistant(text: str):
    if not text or not text.strip():
        return

    st.session_state.chat_messages.append({"role": "assistant", "content": text})
    with st.chat_message("assistant"):
        st.markdown(text)


def _format_colons_for_markdown_streaming(text: str) -> str:
    """Format colons for proper Markdown display with line breaks"""
    import re

    # Replace ': ' (colon + space) with ':\n\n' for line breaks
    formatted = re.sub(r':\s+', ':\n\n', text)
    formatted = re.sub(r':$', ':\n\n', formatted, flags=re.MULTILINE)

    return formatted

def filter_empty_messages(messages):
    """Filter out empty or whitespace-only messages"""
    return [msg for msg in messages if msg.get("content") and msg["content"].strip()]

# ----- Async streaming (Option B) -----
async def run_stream_async(prompt: str):
    """
    Streams the agent's response for `prompt`, detects handoff_to_user in-flight,
    and updates Streamlit UI incrementally.
    """

    # Temporarily replace messages with filtered version
    original_messages = st.session_state.chat_messages
    st.session_state.chat_messages = filter_empty_messages(original_messages)

    agent = st.session_state.agent
    # Live placeholder to show token-by-token text
    with st.chat_message("assistant"):
        spot = st.empty()
        collected = []

        try:
            # Use async streaming to get real-time updates
            async for event in agent.stream_async(prompt):

                etype = event.get("type") if isinstance(event, dict) else None

                # CHECK FOR HANDOFF STATE DURING STREAMING
                if st.session_state.pending_handoff and not st.session_state.handoff_triggered_this_run:
                    st.session_state.handoff_triggered_this_run = True
                    st.rerun()

                # Handle text streaming
                if "data" in event and isinstance(event["data"], str):
                    new_text = event["data"]
                    collected.append(new_text)

                    # Check if the accumulated text ends with a colon
                    full_text = "".join(collected)

                    # Add proper Markdown line breaks after sentences ending with ':'
                    if full_text.endswith(':'):
                        lines = full_text.split('\n')
                        current_line = lines[-1].strip()

                        # If current line ends with ':', add double newlines for Markdown
                        if current_line.endswith(':') and not full_text.endswith(':\n\n'):
                            collected[-1] = collected[-1].rstrip(':') + ' '
                            collected.append('\n\n')  # Double newline for Markdown line break

                    display_text = "".join(collected)
                    spot.markdown(display_text)
                    continue

                # Handle final result - check for handoff tool in metrics
                if etype == "result" or ("result" in event and hasattr(event["result"], "metrics")):
                    result = event.get("result")

                    # Only handle the response text, ignore handoff in metrics
                    if result and hasattr(result, "message"):
                        message_content = result.message.get("content", [])
                        for content_item in message_content:
                            if isinstance(content_item, dict) and "text" in content_item:
                                text = content_item["text"]
                                collected = [text]
                                spot.markdown(text)

                    # Log but don't process handoff in final result
                    if result and hasattr(result, "metrics"):
                        tool_metrics = result.metrics.tool_metrics
                        if "handoff_to_user" in tool_metrics:
                            print("HANDOFF FOUND in final result metrics - IGNORING (already handled)")
                    continue

                # Existing streaming logic for other event types...

        except Exception as e:
            st.error(f"Streaming error: {e}")


        # End of streaming loop — persist whatever we rendered
        final_text = "".join(collected).strip()
        if final_text:
            # We already displayed it live; just store in transcript
            st.session_state.chat_messages.append({"role": "assistant", "content": final_text})

    if st.session_state.handoff_triggered_this_run:
        st.session_state.handoff_triggered_this_run = False
        st.rerun()


def start_chat_session():
    init_state()

    # ----- Render transcript first -----
    render_transcript()


    # ----- HANDOFF GATE (must be before chat_input) -----
    if st.session_state.pending_handoff:
        # Show the agent’s request and a form for the human to answer
        with st.chat_message("assistant"):
            st.markdown(f"**Agent handoff:** {st.session_state.pending_handoff['message']}")

        with st.form("handoff_form", clear_on_submit=True):
            user_reply = st.text_area("Your input", placeholder="Type your answer…", height=120)
            submitted = st.form_submit_button("Send")

        if submitted and user_reply.strip():
            # Show the user reply and continue the SAME conversation
            append_user(user_reply)

            # Clear the pending handoff
            breakout = bool(st.session_state.pending_handoff.get("breakout"))

            st.session_state.pending_handoff = None  # Clear handoff state immediately
            st.session_state.handoff_triggered_this_run = False  # Reset trigger flag

            # If breakout==True, stop here and return to normal chat
            if breakout:
                st.rerun()  # This will show the regular chat input
            else:
                # For soft handoff, continue the conversation
                asyncio.run(run_stream_async(user_reply))

        st.stop()  # Don’t fall through to chat_input on this run


    # ----- NORMAL CHAT INPUT -----
    if prompt := st.chat_input("Ask me anything…"):
        append_user(prompt)
        asyncio.run(run_stream_async(prompt))

