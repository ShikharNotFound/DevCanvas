# graph_orchestrator.py
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. Import your refactored agent functions
from pm_agent import run_pm_agent
from architect_agent import run_architect_agent
from developer_agent import run_developer_agent
from output_store import slugify



# 2. Define the Shared State
class DevCanvasState(TypedDict):
    project_slug: str
    description: str
    prd_path: str
    sdd_path: str
    code_path: str



# 3. Define the Nodes (The Wrappers)
async def pm_node(state: DevCanvasState):
    print("--- Running PM Agent ---")
    prd_path = await run_pm_agent(state["project_slug"], state["description"])
    return {"prd_path": prd_path} # Return only the update

async def architect_node(state: DevCanvasState):
    print("--- Running Architect Agent ---")
    sdd_path = await run_architect_agent(state["project_slug"])
    return {"sdd_path": sdd_path}

async def developer_node(state: DevCanvasState):
    print("--- Running Developer Agent ---")
    code_path = await run_developer_agent(state["project_slug"])
    return {"code_path": code_path}

# 4. Build the Graph
workflow = StateGraph(DevCanvasState)

# Add the nodes
workflow.add_node("pm", pm_node)
workflow.add_node("architect", architect_node)
workflow.add_node("developer", developer_node)

# Connect the nodes in a straight line
workflow.add_edge(START, "pm")
workflow.add_edge("pm", "architect")
workflow.add_edge("architect", "developer")
workflow.add_edge("developer", END)

# Compile the graph into a runnable app
app = workflow.compile()

# 5. The Entry Point
if __name__ == "__main__":
    print("🚀 Starting DevCanvas Pipeline")
    
    # Get initial input from the user
    project_name = input("Project name (e.g. 'My App'): ")
    project_slug = slugify(project_name)
    description = input("Describe your software: ")
    
    # Define the initial state
    initial_state = {
        "project_slug": project_slug,
        "description": description,
        "prd_path": "",
        "sdd_path": "",
        "code_path": ""
    }
    
    # Run the graph
    final_state = asyncio.run(app.ainvoke(initial_state))
    
    print("\n✅ Pipeline Complete!")
    print(f"Final code is in: {final_state['code_path']}")