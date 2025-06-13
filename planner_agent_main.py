from agent import PlannerAgent

if __name__ == "__main__":
    agent = PlannerAgent()
    while True:
        query = input("Human: ")
        response = agent.response(query)
        print("AI:", response)
        print()