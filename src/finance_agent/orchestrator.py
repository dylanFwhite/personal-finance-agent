from langchain.messages import AnyMessage, SystemMessage, ToolMessage
import operator
from typing import Annotated, Literal, TypedDict

from langchain.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from src.finance_agent.llm import llm

SYSTEM_PROMPT = """You are an expert workflow orchestrator. It is your job to
receive a request from the user and delegate the task to the most appropriate
worker. You should not under any circumstances try to resolve the users request
yourself as you most likely will not have access to the necessary tools to do
so. You should just respond simply with a suggestion of which sub agent the
task will be delegated to.

The current list of available workers is the following:
1. The Q&A Agent: A specialist agent that is purpose built for responding to 
   user questions by providing meaningful answers.
2. The Data Ingestion Agent: A specialist agent that is designed to automate the
   ingestion of user supplied data.
"""


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


checkpointer = InMemorySaver()


@tool
def request_info() -> str:
    """
    Request additional information from the user.

    This tool should be used when the existing context is not sufficient to make
    an informed decision about what the appropriate course of action is for
    their request.
    """
    return "I think that you should delegate my request to the Q&A Agent"


tools = [request_info]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)
# TODO: Make model return structured output e.g.
# structured_llm = llm.with_structured_output(EmailClassification)


def llm_call(state: dict):
    return {
        "messages": [
            llm_with_tools.invoke(
                [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))

    return {"messages": result}


def should_continue(state: MessagesState) -> Literal["tool_node", END]:  # type: ignore
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"

    return END


agent_builder = StateGraph(MessagesState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

orchestrator = agent_builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    print(orchestrator.get_graph(xray=True).draw_mermaid())
