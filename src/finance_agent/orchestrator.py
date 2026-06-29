import operator

from langchain.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from typing import Annotated, Literal

from langchain.tools import tool
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from src.finance_agent.llm import llm

PLANNER_PROMPT = """You are an expert workflow orchestrator. It is your job to
receive a request from the user and delegate the task to the most appropriate
worker. You should not under any circumstances try to resolve the users request
yourself as you most likely will not have access to the necessary tools to do
so. You should just respond simply with a suggestion of which sub agent the
task will be delegated to.

The current list of available workers is the following:
1. The Query Agent: A specialist agent that is purpose built for generating 
   Read-Only analytic queries in order to answer user questions.
2. The Data Ingestion Agent: A specialist agent that is designed to automate the
   ingestion of user supplied data.

If uncertain about how to proceed, you should favour using the `request_info`
tool instead of guessing."""

ROUTER_PROMPT = """You now have all of the necessary available information to
make a decision about which worker (sub-graph) you will delegate the task to.
Please select the most appropriate worker and provide a meaningful justification.
"""


class SubGraphs(BaseModel):
    """The list of subgraphs that represent the different workers"""

    graph_type: Literal["QUERY", "INGESTION"] = Field(
        ..., description="Must be one of: QUERY, or INGESTION"
    )


class GraphState(BaseModel):
    user_input: HumanMessage
    sub_graph: SubGraphs | None = None
    path_taken: list[str] = ["start"]
    llm_calls: int = 0
    messages: Annotated[list[AnyMessage], operator.add]


class SubGraphSelection(BaseModel):
    worker: SubGraphs = Field(
        ...,
        description="The most appropriate sub-graph (worker) for the users request",
    )
    justification: str = Field(
        ..., description="Why this worker is the best suited for the users request"
    )


# TODO: Make this an interrupt that requires user input
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
structured_llm = llm.with_structured_output(SubGraphSelection)


def llm_planner(state: GraphState):
    return {
        "messages": [
            llm_with_tools.invoke(
                [SystemMessage(content=PLANNER_PROMPT)] + state.messages
            )
        ],
        "path_taken": state.path_taken + ["planner"],
        "llm_calls": state.llm_calls + 1,
    }


def llm_router(state: GraphState):
    llm_output = structured_llm.invoke(
        [SystemMessage(content=ROUTER_PROMPT)] + state.messages
    )
    print(llm_output)
    return {
        "sub_graph": llm_output.worker,
        "messages": [
            AIMessage(
                content=f"I believe the appropriate sub-graph is {llm_output.worker.graph_type} because {llm_output.justification}"
            )
        ],
        "path_taken": state.path_taken + ["router"],
        "llm_calls": state.llm_calls + 1,
    }


def tool_node(state: GraphState):
    """Performs the tool call"""

    result = []
    for tool_call in state.messages[-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))

    return {"messages": result}


def continue_planning(state: GraphState) -> Literal["tool_node", END]:  # type: ignore
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state.messages
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"

    return "llm_router"


agent_builder = StateGraph(GraphState)

agent_builder.add_node("llm_planner", llm_planner)
agent_builder.add_node("llm_router", llm_router)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_planner")
agent_builder.add_conditional_edges(
    "llm_planner", continue_planning, ["tool_node", "llm_router"]
)
agent_builder.add_edge("tool_node", "llm_planner")
agent_builder.add_edge("llm_router", END)

orchestrator = agent_builder.compile()

if __name__ == "__main__":
    print(orchestrator.get_graph(xray=True).draw_mermaid())
