# chốc nữa cho viết cái api theo flow này
from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END

try:
    from .agent_ocr import agent_ocrs
    from .agent_rag import agent_rags
    from .agent_route import agent_routes
except ImportError:
    from agent_ocr import agent_ocrs
    from agent_rag import agent_rags
    from agent_route import agent_routes

class DictSys(TypedDict):
    inp: Any
    check: str
    # go: str
    rag_rs : str
    ocr_rs: str


def _extract_rag_input(inp: Any) -> str:
    if isinstance(inp, dict):
        return (inp.get("text") or inp.get("prompt") or "").strip()
    return str(inp)

def node_check(state: DictSys):
    rs = agent_routes(state['inp'])
    return {
        "check": rs
    }

def route_node(state: DictSys):
    print("AT ROUTE: ", state)
    route_result = state.get("check") or {}
    route_type = route_result.get("classifi") or route_result.get("result")

    if route_type == "OCR":
        return 'o'
    return 'r'

def node_rag(state: DictSys):
    rag = agent_rags(_extract_rag_input(state['inp']))
    return {
        'rag_rs': rag
    }

def node_ocr(state: DictSys):
    # path_img = state['inp']
    result = agent_ocrs(state['inp'])
    return {
        'ocr_rs': result
    }



graph = StateGraph(DictSys)
graph.add_node('c', node_check)
# graph.add_node('rou', route_node)
graph.add_node('o', node_ocr)
graph.add_node('r', node_rag)

graph.set_entry_point('c')
# graph.add_edge('c', 'rou')
graph.add_conditional_edges(
    'c',
    route_node,
    {
        "r": 'r',
        "o": 'o'
    }
)
graph.add_edge('r', END)
graph.add_edge('o', END)

app = graph.compile()

# D:/ttsVin/DVX-OCR/fastAPI/dataset/images/a_lot_of_noise/menu_01.png

if __name__ == "__main__":
    while True:
        inp = input("Bạn: ")

        if inp =='bye':
            print("AI: bye nhaaa!")
            break;

        rs = app.invoke({"inp": inp})
        if 'rag_rs' in rs.keys():
            print("AI: ", rs['rag_rs'])
        if 'ocr_rs' in rs.keys():
            print("AI: ", rs['ocr_rs'])
            inp = input("Bạn có muốn thêm menu này?")
